"""Monitoring REST endpoints + SSE realtime stream."""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from ..db import db
from ..auth import require_user, get_current_user
from ..utils import new_id, now_iso, serialize_doc, serialize_list
from ..changelog import log_change
from ..monitoring import pubsub, engine
from ..monitoring.notifiers import test_channel as _test_channel

router = APIRouter(prefix='/monitoring', tags=['Monitoring'])


# ============ MONITORS ============
class MonitorCreate(BaseModel):
    name: str
    type: str = 'icmp'  # icmp | tcp | http | https | dns | snmp
    target: Optional[str] = None
    url: Optional[str] = None
    port: Optional[int] = 80
    http_method: Optional[str] = 'GET'
    expected_status: Optional[int] = 200
    expected_text: Optional[str] = None
    verify_ssl: Optional[bool] = True
    oid: Optional[str] = '1.3.6.1.2.1.1.3.0'
    community: Optional[str] = 'public'
    record_type: Optional[str] = 'A'
    interval_seconds: int = 60
    timeout_seconds: int = 5
    icmp_count: int = 3
    retry: int = 1
    enabled: bool = True
    device_id: Optional[str] = None
    interface_id: Optional[str] = None
    circuit_id: Optional[str] = None
    site_id: Optional[str] = None
    thresholds: Optional[Dict[str, Any]] = {}
    description: Optional[str] = ''
    tags: Optional[List[str]] = []


@router.get('/monitors')
async def list_monitors(limit: int = 500, offset: int = 0, q: Optional[str] = None):
    f: Dict[str, Any] = {}
    if q:
        f['$or'] = [{'name': {'$regex': q, '$options': 'i'}}, {'target': {'$regex': q, '$options': 'i'}}, {'tags': {'$regex': q, '$options': 'i'}}]
    total = await db.monitors.count_documents(f)
    items = await db.monitors.find(f, {'_id': 0}).sort('created', -1).skip(offset).limit(limit).to_list(length=limit)
    return {'total': total, 'limit': limit, 'offset': offset, 'results': serialize_list(items)}


@router.get('/monitors/{id}')
async def get_monitor(id: str):
    doc = await db.monitors.find_one({'id': id}, {'_id': 0})
    if not doc:
        raise HTTPException(404, 'Not found')
    return serialize_doc(doc)


@router.post('/monitors')
async def create_monitor(payload: MonitorCreate, user=Depends(require_user)):
    doc = {**payload.model_dump(), 'id': new_id(), 'current_status': 'unknown',
           'last_check_at': None, 'last_latency_ms': None, 'last_loss_pct': None, 'last_error': None,
           'created': now_iso(), 'last_updated': now_iso()}
    await db.monitors.insert_one(doc)
    doc.pop('_id', None)
    await log_change('create', 'monitor', doc['id'], doc['name'], user, None, doc)
    return serialize_doc(doc)


@router.patch('/monitors/{id}')
async def update_monitor(id: str, payload: Dict[str, Any], user=Depends(require_user)):
    existing = await db.monitors.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    update = {**{k: v for k, v in payload.items() if v is not None}, 'last_updated': now_iso()}
    await db.monitors.update_one({'id': id}, {'$set': update})
    fresh = await db.monitors.find_one({'id': id}, {'_id': 0})
    await log_change('update', 'monitor', id, fresh.get('name'), user, existing, fresh)
    return serialize_doc(fresh)


@router.delete('/monitors/{id}')
async def delete_monitor(id: str, user=Depends(require_user)):
    existing = await db.monitors.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    await db.monitors.delete_one({'id': id})
    await db.metric_samples.delete_many({'monitor_id': id})
    await log_change('delete', 'monitor', id, existing.get('name'), user, existing, None)
    return {'deleted': id}


@router.post('/monitors/{id}/run')
async def run_monitor(id: str, user=Depends(require_user)):
    m = await engine.trigger_now(id)
    if not m:
        raise HTTPException(404, 'Monitor not found')
    return serialize_doc(m)


@router.get('/monitors/{id}/metrics')
async def monitor_metrics(id: str, hours: float = 1.0, limit: int = 500):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    docs = await db.metric_samples.find({'monitor_id': id, 'time': {'$gte': cutoff}}, {'_id': 0}).sort('time', 1).limit(limit).to_list(length=limit)
    return {'count': len(docs), 'results': serialize_list(docs)}


# ============ ALERT RULES ============
class RuleCreate(BaseModel):
    name: str
    monitor_id: Optional[str] = None  # None = applies to all
    condition: str = 'down'  # down | warning_or_worse | status_change | latency_above | loss_above
    threshold: Optional[float] = None
    duration_seconds: int = 0
    severity: str = 'critical'  # info | warning | critical
    channels: Optional[List[str]] = []  # channel ids
    enabled: bool = True
    description: Optional[str] = ''


@router.get('/rules')
async def list_rules():
    docs = await db.alert_rules.find({}, {'_id': 0}).sort('created', -1).to_list(length=1000)
    return {'total': len(docs), 'results': serialize_list(docs)}


@router.post('/rules')
async def create_rule(payload: RuleCreate, user=Depends(require_user)):
    doc = {**payload.model_dump(), 'id': new_id(), 'created': now_iso(), 'last_updated': now_iso()}
    await db.alert_rules.insert_one(doc)
    doc.pop('_id', None)
    await log_change('create', 'alert-rule', doc['id'], doc['name'], user, None, doc)
    return serialize_doc(doc)


@router.patch('/rules/{id}')
async def update_rule(id: str, payload: Dict[str, Any], user=Depends(require_user)):
    existing = await db.alert_rules.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    update = {**{k: v for k, v in payload.items()}, 'last_updated': now_iso()}
    await db.alert_rules.update_one({'id': id}, {'$set': update})
    fresh = await db.alert_rules.find_one({'id': id}, {'_id': 0})
    return serialize_doc(fresh)


@router.delete('/rules/{id}')
async def delete_rule(id: str, user=Depends(require_user)):
    await db.alert_rules.delete_one({'id': id})
    return {'deleted': id}


# ============ ALERTS ============
@router.get('/alerts')
async def list_alerts(state: Optional[str] = None, limit: int = 200, offset: int = 0):
    f: Dict[str, Any] = {}
    if state:
        f['state'] = state
    total = await db.alerts.count_documents(f)
    docs = await db.alerts.find(f, {'_id': 0}).sort('started_at', -1).skip(offset).limit(limit).to_list(length=limit)
    return {'total': total, 'limit': limit, 'offset': offset, 'results': serialize_list(docs)}


@router.post('/alerts/{id}/acknowledge')
async def ack_alert(id: str, user=Depends(require_user)):
    existing = await db.alerts.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    await db.alerts.update_one({'id': id}, {'$set': {
        'acknowledged_at': now_iso(),
        'acknowledged_by': user.get('username'),
        'last_updated': now_iso(),
    }})
    fresh = await db.alerts.find_one({'id': id}, {'_id': 0})
    await pubsub.publish({'type': 'alert_acknowledged', 'alert': serialize_doc(fresh)})
    return serialize_doc(fresh)


@router.post('/alerts/{id}/resolve')
async def resolve_alert(id: str, user=Depends(require_user)):
    existing = await db.alerts.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    await db.alerts.update_one({'id': id}, {'$set': {
        'state': 'resolved', 'resolved_at': now_iso(), 'last_updated': now_iso(),
    }})
    fresh = await db.alerts.find_one({'id': id}, {'_id': 0})
    await pubsub.publish({'type': 'alert_resolved', 'alert': serialize_doc(fresh)})
    return serialize_doc(fresh)


@router.delete('/alerts/{id}')
async def delete_alert(id: str, user=Depends(require_user)):
    await db.alerts.delete_one({'id': id})
    return {'deleted': id}


# ============ CHANNELS ============
class ChannelCreate(BaseModel):
    name: str
    type: str  # email | webhook | slack | teams | inapp
    enabled: bool = True
    config: Dict[str, Any] = {}
    description: Optional[str] = ''


@router.get('/channels')
async def list_channels():
    docs = await db.notification_channels.find({}, {'_id': 0}).to_list(length=500)
    # mask secrets
    out = []
    for d in docs:
        d2 = dict(d)
        cfg = dict(d2.get('config') or {})
        if 'password' in cfg and cfg['password']:
            cfg['password'] = '***'
        d2['config'] = cfg
        out.append(d2)
    return {'total': len(out), 'results': serialize_list(out)}


@router.post('/channels')
async def create_channel(payload: ChannelCreate, user=Depends(require_user)):
    doc = {**payload.model_dump(), 'id': new_id(), 'created': now_iso(), 'last_updated': now_iso()}
    await db.notification_channels.insert_one(doc)
    doc.pop('_id', None)
    await log_change('create', 'notification-channel', doc['id'], doc['name'], user, None, doc)
    return serialize_doc(doc)


@router.patch('/channels/{id}')
async def update_channel(id: str, payload: Dict[str, Any], user=Depends(require_user)):
    existing = await db.notification_channels.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    await db.notification_channels.update_one({'id': id}, {'$set': {**payload, 'last_updated': now_iso()}})
    fresh = await db.notification_channels.find_one({'id': id}, {'_id': 0})
    return serialize_doc(fresh)


@router.delete('/channels/{id}')
async def delete_channel(id: str, user=Depends(require_user)):
    await db.notification_channels.delete_one({'id': id})
    return {'deleted': id}


@router.post('/channels/{id}/test')
async def test_channel_endpoint(id: str, user=Depends(require_user)):
    ch = await db.notification_channels.find_one({'id': id}, {'_id': 0})
    if not ch:
        raise HTTPException(404, 'Not found')
    res = await _test_channel(ch)
    return res


# ============ NOTIFICATIONS / LOGS ============
@router.get('/notifications')
async def list_notifications(limit: int = 100):
    docs = await db.notification_logs.find({}, {'_id': 0}).sort('sent_at', -1).limit(limit).to_list(length=limit)
    return {'total': len(docs), 'results': serialize_list(docs)}


# ============ STATS ============
@router.get('/stats')
async def monitoring_stats():
    total = await db.monitors.count_documents({})
    ok = await db.monitors.count_documents({'current_status': 'ok'})
    warn = await db.monitors.count_documents({'current_status': 'warning'})
    crit = await db.monitors.count_documents({'current_status': 'critical'})
    unknown = await db.monitors.count_documents({'$or': [{'current_status': 'unknown'}, {'current_status': None}, {'current_status': {'$exists': False}}]})
    active_alerts = await db.alerts.count_documents({'state': 'firing'})
    critical_alerts = await db.alerts.count_documents({'state': 'firing', 'severity': 'critical'})
    return {
        'monitors_total': total,
        'monitors_ok': ok,
        'monitors_warning': warn,
        'monitors_critical': crit,
        'monitors_unknown': unknown,
        'alerts_firing': active_alerts,
        'alerts_critical': critical_alerts,
        'channels': await db.notification_channels.count_documents({}),
        'rules': await db.alert_rules.count_documents({}),
        'engine': engine.status(),
    }


# ============ SSE REALTIME ============
@router.get('/stream')
async def stream(request: Request, token: Optional[str] = None):
    # SSE auth: EventSource cannot set headers, so we accept token via query param too.
    if token:
        from ..auth import SECRET_KEY, ALGORITHM
        import jwt
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            raise HTTPException(401, 'invalid token')
    queue = await pubsub.subscribe()

    async def gen():
        try:
            # initial hello + a snapshot of stats
            yield f"event: hello\ndata: {json.dumps({'msg': 'connected'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    payload = json.dumps(event, default=str)
                    yield f"event: {event.get('type', 'message')}\ndata: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            await pubsub.unsubscribe(queue)

    return StreamingResponse(gen(), media_type='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
    })


# ============ WEBSOCKET REALTIME ============
@router.websocket('/ws')
async def ws_stream(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket variant of the live event stream.

    Auth via query token; same JWT as REST. Emits JSON events with shape
    {type, ...}. Client can send {"type":"ping"} to keep the link warm.
    """
    if token:
        from ..auth import SECRET_KEY, ALGORITHM
        import jwt as _jwt
        try:
            _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            await websocket.close(code=4401)
            return
    await websocket.accept()
    queue = await pubsub.subscribe()
    await websocket.send_text(json.dumps({'type': 'hello', 'msg': 'connected'}))

    async def reader():
        try:
            while True:
                msg = await websocket.receive_text()
                # Just echo pings for liveness; no other client commands today.
                try:
                    data = json.loads(msg)
                    if data.get('type') == 'ping':
                        await websocket.send_text(json.dumps({'type': 'pong'}))
                except Exception:
                    pass
        except WebSocketDisconnect:
            return
        except Exception:
            return

    reader_task = asyncio.create_task(reader())
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_text(json.dumps(event, default=str))
            except asyncio.TimeoutError:
                # Keep-alive
                try:
                    await websocket.send_text(json.dumps({'type': 'ping'}))
                except Exception:
                    break
            except WebSocketDisconnect:
                break
    finally:
        reader_task.cancel()
        await pubsub.unsubscribe(queue)
        try:
            await websocket.close()
        except Exception:
            pass
