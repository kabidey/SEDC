"""Notification dispatchers: email (SMTP), webhook, Slack, Teams, in-app."""
from __future__ import annotations
import asyncio
import json
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Dict, Optional
import httpx
from ..db import db
from ..utils import new_id, now_iso


async def _send_email(cfg: Dict[str, Any], subject: str, body: str) -> Dict[str, Any]:
    def _do():
        host = cfg.get('smtp_host')
        port = int(cfg.get('smtp_port', 587))
        user = cfg.get('username') or ''
        pwd = cfg.get('password') or ''
        sender = cfg.get('from') or user
        to = cfg.get('to') or []
        if isinstance(to, str):
            to = [t.strip() for t in to.split(',') if t.strip()]
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(to)
        msg.set_content(body)
        ctx = ssl.create_default_context()
        use_tls = bool(cfg.get('use_tls', True))
        if cfg.get('use_ssl', False):
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=15) as s:
                if user:
                    s.login(user, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as s:
                if use_tls:
                    s.starttls(context=ctx)
                if user:
                    s.login(user, pwd)
                s.send_message(msg)
        return {'ok': True, 'recipients': to}
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _do)
    except Exception as e:
        return {'ok': False, 'error': str(e)}


async def _send_webhook(cfg: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        headers = cfg.get('headers') or {}
        if not isinstance(headers, dict):
            headers = {}
        headers.setdefault('Content-Type', 'application/json')
        async with httpx.AsyncClient(timeout=10, verify=cfg.get('verify_ssl', True)) as c:
            r = await c.request(cfg.get('method', 'POST'), cfg['url'], json=payload, headers=headers)
            return {'ok': r.status_code < 400, 'status': r.status_code, 'body': r.text[:500]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


async def _send_slack(cfg: Dict[str, Any], title: str, body: str, severity: str) -> Dict[str, Any]:
    color = {'critical': '#dc2626', 'warning': '#f59e0b', 'info': '#10b981'}.get(severity, '#10b981')
    payload = {
        'text': f'*{title}*',
        'attachments': [{'color': color, 'text': body, 'mrkdwn_in': ['text']}],
    }
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(cfg['webhook_url'], json=payload)
            return {'ok': r.status_code < 400, 'status': r.status_code}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


async def _send_teams(cfg: Dict[str, Any], title: str, body: str, severity: str) -> Dict[str, Any]:
    theme = {'critical': 'DC2626', 'warning': 'F59E0B', 'info': '10B981'}.get(severity, '10B981')
    payload = {
        '@type': 'MessageCard',
        '@context': 'https://schema.org/extensions',
        'themeColor': theme,
        'summary': title,
        'title': title,
        'text': body,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(cfg['webhook_url'], json=payload)
            return {'ok': r.status_code < 400, 'status': r.status_code}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


async def dispatch_alert(alert: Dict[str, Any], channel_ids: list) -> None:
    """Look up channels by id, send to each, and log results."""
    if not channel_ids:
        # default behaviour: only persist (in-app)
        return
    severity = alert.get('severity', 'warning')
    title = alert.get('title') or 'SMIFS EDC alert'
    body = alert.get('message') or ''
    for cid in channel_ids:
        ch = await db.notification_channels.find_one({'id': cid}, {'_id': 0})
        if not ch or not ch.get('enabled', True):
            continue
        cfg = ch.get('config') or {}
        kind = ch.get('type')
        result = {'ok': False, 'error': 'unknown channel type'}
        try:
            if kind == 'email':
                result = await _send_email(cfg, f'[{severity.upper()}] {title}', body)
            elif kind == 'webhook':
                result = await _send_webhook(cfg, {'alert': alert, 'severity': severity})
            elif kind == 'slack':
                result = await _send_slack(cfg, title, body, severity)
            elif kind == 'teams':
                result = await _send_teams(cfg, title, body, severity)
            elif kind == 'inapp':
                result = {'ok': True}
        except Exception as e:
            result = {'ok': False, 'error': str(e)}
        await db.notification_logs.insert_one({
            'id': new_id(), 'alert_id': alert.get('id'), 'channel_id': cid, 'type': kind,
            'sent_at': now_iso(), 'success': bool(result.get('ok')), 'error': result.get('error'),
            'response': str(result.get('body') or result.get('status') or ''),
        })


async def test_channel(channel: Dict[str, Any]) -> Dict[str, Any]:
    cfg = channel.get('config') or {}
    kind = channel.get('type')
    title = 'SMIFS EDC channel test'
    body = 'This is a test notification from SMIFS Enterprise Data Centre. If you can read this, the channel is configured correctly.'
    if kind == 'email':
        return await _send_email(cfg, title, body)
    if kind == 'webhook':
        return await _send_webhook(cfg, {'test': True, 'message': body})
    if kind == 'slack':
        return await _send_slack(cfg, title, body, 'info')
    if kind == 'teams':
        return await _send_teams(cfg, title, body, 'info')
    return {'ok': True, 'detail': 'in-app channels need no test'}
