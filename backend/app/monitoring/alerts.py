"""Alert rule evaluation + state machine.

Rules apply to monitors. After every check, we re-evaluate the rules that
apply (rule.monitor_id == monitor.id, or rule.monitor_id is None meaning 'all').
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..db import db
from ..utils import new_id, now_iso
from . import pubsub
from .notifiers import dispatch_alert


def _condition_holds(rule: Dict[str, Any], sample: Dict[str, Any]) -> bool:
    cond = rule.get('condition') or 'status_change'
    s = (sample.get('status') or 'unknown').lower()
    if cond == 'down':
        return s in ('critical', 'unknown')
    if cond == 'warning_or_worse':
        return s in ('warning', 'critical', 'unknown')
    if cond == 'status_change':
        # Triggers any non-ok state — used for any change away from healthy.
        return s != 'ok'
    if cond == 'latency_above':
        thr = float(rule.get('threshold') or 0)
        lat = sample.get('latency_ms')
        return lat is not None and lat >= thr
    if cond == 'loss_above':
        thr = float(rule.get('threshold') or 0)
        loss = sample.get('loss_pct')
        return loss is not None and loss >= thr
    return False


async def get_rules_for_monitor(monitor: Dict[str, Any]) -> List[Dict[str, Any]]:
    docs = await db.alert_rules.find({
        '$or': [{'monitor_id': monitor['id']}, {'monitor_id': None}, {'monitor_id': ''}],
        'enabled': {'$ne': False},
    }, {'_id': 0}).to_list(length=500)
    return docs


async def evaluate_for_monitor(monitor: Dict[str, Any], sample: Dict[str, Any]):
    """Evaluate every applicable rule and update alert state."""
    rules = await get_rules_for_monitor(monitor)
    for rule in rules:
        holds = _condition_holds(rule, sample)
        # Find currently firing alert for (rule, monitor)
        existing = await db.alerts.find_one({
            'rule_id': rule['id'], 'monitor_id': monitor['id'], 'state': 'firing',
        }, {'_id': 0})
        if holds:
            # Check duration — must have been bad for >= duration_seconds
            duration = int(rule.get('duration_seconds') or 0)
            if duration > 0 and not existing:
                # Walk back metric_samples to see if condition has been continuously true
                since = await db.metric_samples.find({'monitor_id': monitor['id']}, {'_id': 0}).sort('time', -1).limit(200).to_list(length=200)
                cont = 0
                first_time = None
                for s in since:
                    if _condition_holds(rule, s):
                        cont += 1
                        first_time = s.get('time')
                    else:
                        break
                # crude time math: assume monitor interval; if duration not reached, skip
                interval = max(int(monitor.get('interval_seconds') or 60), 5)
                if cont * interval < duration:
                    continue
            if existing:
                # Update last_sample on the existing alert and publish
                await db.alerts.update_one({'id': existing['id']}, {'$set': {'last_sample': sample, 'last_updated': now_iso()}})
                continue
            # New alert!
            alert = {
                'id': new_id(),
                'rule_id': rule['id'],
                'rule_name': rule.get('name'),
                'monitor_id': monitor['id'],
                'monitor_name': monitor.get('name'),
                'state': 'firing',
                'severity': rule.get('severity', 'warning'),
                'title': f"{(rule.get('severity') or 'warning').upper()}: {monitor.get('name')} — {rule.get('name')}",
                'message': (
                    f"Monitor '{monitor.get('name')}' on target '{monitor.get('target') or monitor.get('url')}' "
                    f"triggered '{rule.get('name')}' (condition={rule.get('condition')}). "
                    f"Latest status={sample.get('status')} latency={sample.get('latency_ms')}ms loss={sample.get('loss_pct')}% "
                    f"error={sample.get('error') or 'none'}."
                ),
                'started_at': now_iso(),
                'resolved_at': None,
                'acknowledged_at': None,
                'acknowledged_by': None,
                'last_sample': sample,
                'created': now_iso(),
                'last_updated': now_iso(),
            }
            await db.alerts.insert_one(alert)
            alert.pop('_id', None)
            await pubsub.publish({'type': 'alert_firing', 'alert': alert})
            try:
                await dispatch_alert(alert, rule.get('channels') or [])
            except Exception:
                pass
        else:
            # Condition does not hold — auto-resolve a firing alert.
            if existing:
                resolved = {
                    **existing,
                    'state': 'resolved',
                    'resolved_at': now_iso(),
                    'last_sample': sample,
                    'last_updated': now_iso(),
                }
                await db.alerts.update_one({'id': existing['id']}, {'$set': resolved})
                await pubsub.publish({'type': 'alert_resolved', 'alert': resolved})
                resolved['title'] = f"RECOVERED: {monitor.get('name')} — {rule.get('name')}"
                resolved['message'] = f"Monitor '{monitor.get('name')}' is healthy again."
                try:
                    await dispatch_alert(resolved, rule.get('channels') or [])
                except Exception:
                    pass
