"""Discovery REST endpoints: credentials, jobs, discovered devices, topology, Netdisco sync."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import asyncio
from ..db import db
from ..auth import require_user
from ..utils import new_id, now_iso, serialize_doc, serialize_list
from ..changelog import log_change
from ..discovery.snmp_scanner import scan_target, scan_range, expand_targets
from ..discovery.netdisco_client import NetdiscoClient
from ..discovery.mapper import import_discovered_device

router = APIRouter(prefix='/discovery', tags=['Discovery'])


# -------------------- CREDENTIALS --------------------
class CredentialCreate(BaseModel):
    name: str
    snmp_version: str = 'v2c'  # v1, v2c, v3
    community: Optional[str] = 'public'
    username: Optional[str] = ''
    auth_key: Optional[str] = ''
    priv_key: Optional[str] = ''
    port: int = 161
    description: Optional[str] = ''


@router.get('/credentials')
async def list_credentials():
    docs = await db.discovery_credentials.find({}, {'_id': 0}).to_list(length=500)
    return {'total': len(docs), 'results': serialize_list(docs)}


@router.post('/credentials')
async def create_credential(payload: CredentialCreate, user=Depends(require_user)):
    doc = {**payload.model_dump(), 'id': new_id(), 'created': now_iso(), 'last_updated': now_iso()}
    await db.discovery_credentials.insert_one(doc)
    doc.pop('_id', None)
    await log_change('create', 'discovery-credential', doc['id'], doc['name'], user, None, doc)
    return serialize_doc(doc)


@router.patch('/credentials/{id}')
async def update_credential(id: str, payload: CredentialCreate, user=Depends(require_user)):
    existing = await db.discovery_credentials.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    update = {**payload.model_dump(exclude_unset=True), 'last_updated': now_iso()}
    await db.discovery_credentials.update_one({'id': id}, {'$set': update})
    fresh = await db.discovery_credentials.find_one({'id': id}, {'_id': 0})
    await log_change('update', 'discovery-credential', id, fresh['name'], user, existing, fresh)
    return serialize_doc(fresh)


@router.delete('/credentials/{id}')
async def delete_credential(id: str, user=Depends(require_user)):
    existing = await db.discovery_credentials.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    await db.discovery_credentials.delete_one({'id': id})
    await log_change('delete', 'discovery-credential', id, existing.get('name', id), user, existing, None)
    return {'deleted': id}


# -------------------- JOBS --------------------
class JobCreate(BaseModel):
    name: str
    target_spec: str  # CIDR, range, comma-list
    credential_id: Optional[str] = None
    description: Optional[str] = ''
    auto_import: bool = False  # auto-create SMIFS Devices from results
    site_id: Optional[str] = None


@router.get('/jobs')
async def list_jobs():
    docs = await db.discovery_jobs.find({}, {'_id': 0}).sort('created', -1).to_list(length=500)
    return {'total': len(docs), 'results': serialize_list(docs)}


@router.get('/jobs/{id}')
async def get_job(id: str):
    doc = await db.discovery_jobs.find_one({'id': id}, {'_id': 0})
    if not doc:
        raise HTTPException(404, 'Not found')
    return serialize_doc(doc)


@router.post('/jobs')
async def create_job(payload: JobCreate, user=Depends(require_user)):
    doc = {
        **payload.model_dump(),
        'id': new_id(),
        'status': 'pending',
        'last_run': None,
        'stats': {'scanned': 0, 'discovered': 0, 'imported': 0},
        'created': now_iso(),
        'last_updated': now_iso(),
    }
    await db.discovery_jobs.insert_one(doc)
    doc.pop('_id', None)
    await log_change('create', 'discovery-job', doc['id'], doc['name'], user, None, doc)
    return serialize_doc(doc)


@router.delete('/jobs/{id}')
async def delete_job(id: str, user=Depends(require_user)):
    existing = await db.discovery_jobs.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Not found')
    await db.discovery_jobs.delete_one({'id': id})
    await log_change('delete', 'discovery-job', id, existing.get('name', id), user, existing, None)
    return {'deleted': id}


async def _execute_job(job_id: str, user: Dict[str, Any]):
    job = await db.discovery_jobs.find_one({'id': job_id}, {'_id': 0})
    if not job:
        return
    await db.discovery_jobs.update_one({'id': job_id}, {'$set': {'status': 'running', 'last_run': now_iso(), 'last_updated': now_iso()}})
    cred = {}
    if job.get('credential_id'):
        cred = await db.discovery_credentials.find_one({'id': job['credential_id']}, {'_id': 0}) or {}
    cred = {k: v for k, v in cred.items() if k not in ('_id',)}
    targets = expand_targets(job['target_spec'])
    results = await scan_range(targets, cred or {'snmp_version': 'v2c', 'community': 'public', 'port': 161}, concurrency=16, timeout=3)
    discovered = 0
    imported = 0
    for r in results:
        # Persist discovered device snapshot
        doc = {
            'id': new_id(),
            'job_id': job_id,
            **r,
            'discovered_at': now_iso(),
        }
        await db.discovered_devices.insert_one(doc)
        discovered += 1
        if job.get('auto_import') and (r.get('reachable') or r.get('simulated')):
            try:
                await import_discovered_device(r, job.get('site_id'), user)
                imported += 1
            except Exception:
                pass
    await db.discovery_jobs.update_one({'id': job_id}, {'$set': {
        'status': 'completed',
        'stats': {'scanned': len(results), 'discovered': discovered, 'imported': imported},
        'last_updated': now_iso(),
    }})


@router.post('/jobs/{id}/run')
async def run_job(id: str, bg: BackgroundTasks, user=Depends(require_user)):
    job = await db.discovery_jobs.find_one({'id': id}, {'_id': 0})
    if not job:
        raise HTTPException(404, 'Not found')
    bg.add_task(_execute_job, id, user)
    return {'status': 'queued', 'job_id': id}


# -------------------- ON-DEMAND SCAN (no persistent job) --------------------
class AdhocScanRequest(BaseModel):
    target: str
    credential_id: Optional[str] = None
    timeout: int = 4


@router.post('/scan')
async def adhoc_scan(payload: AdhocScanRequest, user=Depends(require_user)):
    cred = {}
    if payload.credential_id:
        cred = await db.discovery_credentials.find_one({'id': payload.credential_id}, {'_id': 0}) or {}
    result = await scan_target(payload.target, cred or {'snmp_version': 'v2c', 'community': 'public', 'port': 161}, timeout=payload.timeout)
    # Save snapshot
    doc = {**result, 'id': new_id(), 'discovered_at': now_iso(), 'job_id': None}
    await db.discovered_devices.insert_one(doc)
    doc.pop('_id', None)
    return serialize_doc(doc)


# -------------------- DISCOVERED DEVICES --------------------
@router.get('/devices')
async def list_discovered(limit: int = 200, offset: int = 0, job_id: Optional[str] = None, q: Optional[str] = None):
    f: Dict[str, Any] = {}
    if job_id:
        f['job_id'] = job_id
    if q:
        f['$or'] = [{'sysname': {'$regex': q, '$options': 'i'}}, {'target': {'$regex': q, '$options': 'i'}}, {'vendor': {'$regex': q, '$options': 'i'}}]
    total = await db.discovered_devices.count_documents(f)
    docs = await db.discovered_devices.find(f, {'_id': 0}).sort('discovered_at', -1).skip(offset).limit(limit).to_list(length=limit)
    return {'total': total, 'limit': limit, 'offset': offset, 'results': serialize_list(docs)}


@router.get('/devices/{id}')
async def get_discovered(id: str):
    doc = await db.discovered_devices.find_one({'id': id}, {'_id': 0})
    if not doc:
        raise HTTPException(404, 'Not found')
    return serialize_doc(doc)


@router.post('/devices/{id}/import')
async def import_discovered(id: str, site_id: Optional[str] = Body(None, embed=True), user=Depends(require_user)):
    doc = await db.discovered_devices.find_one({'id': id}, {'_id': 0})
    if not doc:
        raise HTTPException(404, 'Not found')
    result = await import_discovered_device(doc, site_id, user)
    return result


@router.delete('/devices/{id}')
async def delete_discovered(id: str, user=Depends(require_user)):
    await db.discovered_devices.delete_one({'id': id})
    return {'deleted': id}


# -------------------- TOPOLOGY --------------------
@router.get('/topology')
async def topology():
    """Return graph data: nodes (devices) and edges (LLDP neighbors / cables)."""
    nodes_devices = await db.devices.find({}, {'_id': 0}).to_list(length=5000)
    nodes = [{'id': d['id'], 'label': d.get('name') or d['id'], 'type': 'device', 'role_id': d.get('role_id'), 'site_id': d.get('site_id')} for d in nodes_devices]
    iface_index = {}
    cur = db.interfaces.find({}, {'_id': 0, 'id': 1, 'device_id': 1, 'name': 1})
    async for i in cur:
        iface_index[i['id']] = i
    edges = []
    cables = await db.cables.find({}, {'_id': 0}).to_list(length=5000)
    for c in cables:
        a = (c.get('a_terminations') or [])
        b = (c.get('b_terminations') or [])
        if not (a and b):
            continue
        a0, b0 = a[0], b[0]
        if a0.get('object_type') == 'interface' and b0.get('object_type') == 'interface':
            ai = iface_index.get(a0['object_id'])
            bi = iface_index.get(b0['object_id'])
            if not (ai and bi):
                continue
            edges.append({
                'id': c['id'],
                'source': ai['device_id'],
                'target': bi['device_id'],
                'source_port': ai['name'],
                'target_port': bi['name'],
                'cable_type': c.get('type'),
                'status': c.get('status'),
            })
    return {'nodes': nodes, 'edges': edges}


# -------------------- NETDISCO INTEGRATION --------------------
class NetdiscoSettings(BaseModel):
    base_url: str
    username: str
    password: str
    verify_ssl: bool = True


@router.post('/netdisco/test')
async def netdisco_test(settings: NetdiscoSettings, user=Depends(require_user)):
    client = NetdiscoClient(settings.base_url, settings.username, settings.password, settings.verify_ssl)
    try:
        res = await client.check()
        return res
    finally:
        await client.close()


@router.post('/netdisco/sync')
async def netdisco_sync(settings: NetdiscoSettings, user=Depends(require_user)):
    """Pull devices + neighbors from a Netdisco instance and stage them as DiscoveredDevices."""
    client = NetdiscoClient(settings.base_url, settings.username, settings.password, settings.verify_ssl)
    try:
        devices = await client.list_devices()
        inserted = 0
        for d in devices or []:
            ip = d.get('ip') or d.get('management_ip')
            if not ip:
                continue
            ports = await client.list_device_ports(ip)
            neighbors = await client.list_neighbors(ip)
            doc = {
                'id': new_id(),
                'target': ip,
                'reachable': True,
                'simulated': False,
                'sysname': d.get('name') or d.get('dns'),
                'sysdescr': d.get('description') or d.get('os'),
                'vendor': d.get('vendor') or d.get('mfg'),
                'model': d.get('model'),
                'role': '',
                'syslocation': d.get('location') or '',
                'interfaces': [{'name': p.get('port'), 'descr': p.get('name'), 'mac': p.get('mac'), 'speed': p.get('speed_actual'), 'oper_status': p.get('up')} for p in (ports or [])],
                'ip_addresses': [],
                'neighbors': [{'local_port': n.get('port'), 'remote_system_name': n.get('remote_name'), 'remote_port': n.get('remote_port')} for n in (neighbors or [])],
                'job_id': None,
                'discovered_at': now_iso(),
                'source': 'netdisco',
            }
            await db.discovered_devices.insert_one(doc)
            inserted += 1
        return {'devices_pulled': len(devices or []), 'staged': inserted}
    finally:
        await client.close()


@router.get('/netdisco/settings')
async def get_netdisco_settings():
    doc = await db.discovery_netdisco.find_one({'id': 'global'}, {'_id': 0}) or {'id': 'global'}
    if 'password' in doc:
        doc = {**doc, 'password': '***' if doc['password'] else ''}
    return serialize_doc(doc)


@router.post('/netdisco/settings')
async def save_netdisco_settings(settings: NetdiscoSettings, user=Depends(require_user)):
    doc = settings.model_dump()
    doc['id'] = 'global'
    doc['last_updated'] = now_iso()
    await db.discovery_netdisco.update_one({'id': 'global'}, {'$set': doc}, upsert=True)
    return {'saved': True}


# -------------------- STATS --------------------
@router.get('/stats')
async def discovery_stats():
    return {
        'credentials': await db.discovery_credentials.count_documents({}),
        'jobs': await db.discovery_jobs.count_documents({}),
        'jobs_running': await db.discovery_jobs.count_documents({'status': 'running'}),
        'jobs_completed': await db.discovery_jobs.count_documents({'status': 'completed'}),
        'discovered_devices': await db.discovered_devices.count_documents({}),
        'imported_devices': await db.devices.count_documents({'tags': 'auto-discovered'}),
    }
