"""Background scheduler: periodically runs due monitors and dispatches results."""
from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Dict
from ..db import db
from ..utils import new_id, now_iso
from . import pubsub
from .checks import run_check
from .alerts import evaluate_for_monitor

log = logging.getLogger(__name__)

_TASK: asyncio.Task | None = None
_running = False
_concurrency = 16
_sem: asyncio.Semaphore | None = None
# in-process counter for retention pruning
_loop_counter = 0


async def _check_monitor(monitor: Dict[str, Any]):
    global _sem
    try:
        async with _sem:
            sample = await run_check(monitor)
    except Exception as e:
        sample = {'status': 'unknown', 'error': str(e), 'latency_ms': None, 'loss_pct': None, 'response_time_ms': None, 'raw': {}}
    sample_doc = {
        'id': new_id(),
        'monitor_id': monitor['id'],
        'monitor_name': monitor.get('name'),
        'time': now_iso(),
        **sample,
    }
    try:
        await db.metric_samples.insert_one(sample_doc)
        sample_doc.pop('_id', None)
    except Exception:
        pass
    # Update monitor's last-known state
    try:
        await db.monitors.update_one({'id': monitor['id']}, {'$set': {
            'current_status': sample.get('status'),
            'last_check_at': sample_doc['time'],
            'last_latency_ms': sample.get('latency_ms'),
            'last_loss_pct': sample.get('loss_pct'),
            'last_error': sample.get('error'),
            'last_updated': now_iso(),
        }})
    except Exception:
        pass
    # Publish live event
    try:
        await pubsub.publish({'type': 'metric', 'monitor_id': monitor['id'], 'monitor_name': monitor.get('name'), 'sample': sample_doc})
    except Exception:
        pass
    # Evaluate alert rules
    try:
        await evaluate_for_monitor(monitor, sample)
    except Exception as e:
        log.exception('alert eval failed: %s', e)


async def _scheduler_loop():
    """Tick every 5 seconds; pick up monitors due for a check."""
    global _running, _loop_counter
    while _running:
        try:
            now = time.time()
            cursor = db.monitors.find({'enabled': {'$ne': False}}, {'_id': 0})
            tasks = []
            async for m in cursor:
                interval = max(int(m.get('interval_seconds') or 60), 5)
                last = m.get('last_check_at')
                # parse ISO -> epoch
                last_t = 0.0
                if last:
                    try:
                        from datetime import datetime
                        last_t = datetime.fromisoformat(last.replace('Z', '+00:00')).timestamp()
                    except Exception:
                        last_t = 0.0
                if now - last_t >= interval:
                    tasks.append(asyncio.create_task(_check_monitor(m)))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            _loop_counter += 1
            # Every ~5 minutes prune metric_samples older than 24h
            if _loop_counter % 60 == 0:
                try:
                    from datetime import datetime, timezone, timedelta
                    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
                    await db.metric_samples.delete_many({'time': {'$lt': cutoff}})
                except Exception:
                    pass
        except Exception as e:
            log.exception('scheduler tick failed: %s', e)
        await asyncio.sleep(5)


async def start():
    global _TASK, _running, _sem
    if _TASK and not _TASK.done():
        return
    _running = True
    _sem = asyncio.Semaphore(_concurrency)
    _TASK = asyncio.create_task(_scheduler_loop())
    log.info('Monitoring scheduler started')


async def stop():
    global _running, _TASK
    _running = False
    if _TASK:
        _TASK.cancel()
        try:
            await _TASK
        except Exception:
            pass
        _TASK = None


def status() -> Dict[str, Any]:
    return {'running': _running, 'subscribers': pubsub.subscriber_count()}


async def trigger_now(monitor_id: str):
    """Run a single monitor check immediately, out of band."""
    m = await db.monitors.find_one({'id': monitor_id}, {'_id': 0})
    if not m:
        return None
    await _check_monitor(m)
    return await db.monitors.find_one({'id': monitor_id}, {'_id': 0})
