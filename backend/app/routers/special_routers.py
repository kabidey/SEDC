"""Specialized routers for cables (polymorphic), prefix tree, rack elevation, change log, search."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import ipaddress as ipa
from ..db import db
from ..auth import require_user, get_current_user
from ..utils import new_id, now_iso, serialize_doc, serialize_list
from ..changelog import log_change
from ..schemas.devices import CableCreate, CableUpdate


# ============= CABLES =============
cables_router = APIRouter(prefix='/cables', tags=['Connections'])


@cables_router.get('')
async def list_cables(limit: int = 100, offset: int = 0, q: Optional[str] = None):
    f: Dict[str, Any] = {}
    if q:
        f['$or'] = [{'label': {'$regex': q, '$options': 'i'}}, {'type': {'$regex': q, '$options': 'i'}}]
    total = await db.cables.count_documents(f)
    items = await db.cables.find(f, {'_id': 0}).sort('created', -1).skip(offset).limit(limit).to_list(length=limit)
    return {'total': total, 'limit': limit, 'offset': offset, 'results': serialize_list(items)}


@cables_router.get('/{id}')
async def get_cable(id: str):
    doc = await db.cables.find_one({'id': id}, {'_id': 0})
    if not doc:
        raise HTTPException(404, 'Cable not found')
    return serialize_doc(doc)


@cables_router.post('')
async def create_cable(payload: CableCreate, user: Dict[str, Any] = Depends(require_user)):
    data = payload.model_dump()
    data['id'] = new_id()
    data['created'] = now_iso()
    data['last_updated'] = now_iso()
    await db.cables.insert_one(data)
    # Update terminations: mark connected
    for term in (data['a_terminations'] + data['b_terminations']):
        collection_map = {
            'interface': 'interfaces', 'console-port': 'console_ports', 'console-server-port': 'console_server_ports',
            'power-port': 'power_ports', 'power-outlet': 'power_outlets', 'front-port': 'front_ports',
            'rear-port': 'rear_ports', 'circuit-termination': 'circuit_terminations', 'power-feed': 'power_feeds',
        }
        col = collection_map.get(term['object_type'])
        if col:
            await db[col].update_one({'id': term['object_id']}, {'$set': {'cable_id': data['id'], 'connected': True}})
    await log_change('create', 'cable', data['id'], data.get('label') or data['id'], user, None, data)
    return serialize_doc(data)


@cables_router.patch('/{id}')
async def update_cable(id: str, payload: CableUpdate, user: Dict[str, Any] = Depends(require_user)):
    existing = await db.cables.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Cable not found')
    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    update['last_updated'] = now_iso()
    await db.cables.update_one({'id': id}, {'$set': update})
    fresh = await db.cables.find_one({'id': id}, {'_id': 0})
    await log_change('update', 'cable', id, fresh.get('label') or id, user, existing, fresh)
    return serialize_doc(fresh)


@cables_router.delete('/{id}')
async def delete_cable(id: str, user: Dict[str, Any] = Depends(require_user)):
    existing = await db.cables.find_one({'id': id}, {'_id': 0})
    if not existing:
        raise HTTPException(404, 'Cable not found')
    collection_map = {
        'interface': 'interfaces', 'console-port': 'console_ports', 'console-server-port': 'console_server_ports',
        'power-port': 'power_ports', 'power-outlet': 'power_outlets', 'front-port': 'front_ports',
        'rear-port': 'rear_ports', 'circuit-termination': 'circuit_terminations', 'power-feed': 'power_feeds',
    }
    for term in (existing.get('a_terminations', []) + existing.get('b_terminations', [])):
        col = collection_map.get(term['object_type'])
        if col:
            await db[col].update_one({'id': term['object_id']}, {'$unset': {'cable_id': '', 'connected': ''}})
    await db.cables.delete_one({'id': id})
    await log_change('delete', 'cable', id, existing.get('label') or id, user, existing, None)
    return {'deleted': id}


@cables_router.get('/trace/{object_type}/{object_id}')
async def trace_cable(object_type: str, object_id: str):
    """Trace a path starting from the given termination."""
    path = []
    visited = set()
    current_type, current_id = object_type, object_id
    for _ in range(50):  # cap depth
        key = f'{current_type}:{current_id}'
        if key in visited:
            break
        visited.add(key)
        # Find a cable with this termination
        cable = await db.cables.find_one({
            '$or': [
                {'a_terminations': {'$elemMatch': {'object_type': current_type, 'object_id': current_id}}},
                {'b_terminations': {'$elemMatch': {'object_type': current_type, 'object_id': current_id}}},
            ]
        }, {'_id': 0})
        if not cable:
            break
        path.append({'cable': serialize_doc(cable), 'from': {'type': current_type, 'id': current_id}})
        # Determine the other side
        a_terms = cable.get('a_terminations', [])
        b_terms = cable.get('b_terminations', [])
        if any(t['object_type'] == current_type and t['object_id'] == current_id for t in a_terms):
            others = b_terms
        else:
            others = a_terms
        if not others:
            break
        # Take first other side as next hop (for now do single trace)
        nxt = others[0]
        path[-1]['to'] = {'type': nxt['object_type'], 'id': nxt['object_id']}
        current_type, current_id = nxt['object_type'], nxt['object_id']
        # Stop if not a port that could pass through (e.g., interface terminates)
        if current_type in ('interface', 'console-port', 'console-server-port', 'power-outlet', 'power-feed'):
            break
    return {'path': path}


# ============= PREFIX TREE =============
prefix_router = APIRouter(prefix='/prefix-tools', tags=['IPAM'])


@prefix_router.get('/tree')
async def prefix_tree(vrf_id: Optional[str] = None):
    f = {'vrf_id': vrf_id} if vrf_id else {}
    items = await db.prefixes.find(f, {'_id': 0}).to_list(length=10000)
    nodes = []
    for it in items:
        try:
            net = ipa.ip_network(it['prefix'], strict=False)
            nodes.append({**serialize_doc(it), '_net': net})
        except Exception:
            continue
    nodes.sort(key=lambda n: (n['_net'].prefixlen, int(n['_net'].network_address)))
    # Build parent-child
    roots = []
    for n in nodes:
        parent = None
        for p in nodes:
            if p is n:
                continue
            if n['_net'].subnet_of(p['_net']) and p['_net'].prefixlen < n['_net'].prefixlen:
                if parent is None or p['_net'].prefixlen > parent['_net'].prefixlen:
                    parent = p
        n['parent'] = parent['id'] if parent else None
        n['depth'] = 0
    # Compute depth
    by_id = {n['id']: n for n in nodes}
    for n in nodes:
        d = 0
        p = n['parent']
        while p:
            d += 1
            p = by_id[p]['parent'] if p in by_id else None
        n['depth'] = d
    # Remove _net before returning
    for n in nodes:
        n.pop('_net', None)
    return {'results': nodes}


@prefix_router.get('/available-ips/{prefix_id}')
async def available_ips(prefix_id: str, limit: int = 50):
    p = await db.prefixes.find_one({'id': prefix_id}, {'_id': 0})
    if not p:
        raise HTTPException(404, 'Prefix not found')
    try:
        net = ipa.ip_network(p['prefix'], strict=False)
    except Exception:
        raise HTTPException(400, 'Invalid prefix')
    used = set()
    cur = db.ip_addresses.find({}, {'_id': 0})
    async for ip in cur:
        try:
            iface = ipa.ip_interface(ip['address']).ip
            if iface in net:
                used.add(int(iface))
        except Exception:
            continue
    available = []
    hosts_iter = net.hosts() if net.prefixlen < (32 if net.version == 4 else 128) else [net.network_address]
    for host in hosts_iter:
        if int(host) not in used:
            available.append(f'{host}/{net.prefixlen}')
            if len(available) >= limit:
                break
    return {'available': available, 'count': len(available)}


# ============= RACK ELEVATION =============
rack_tools_router = APIRouter(prefix='/rack-tools', tags=['Racks'])


@rack_tools_router.get('/{rack_id}/elevation')
async def rack_elevation(rack_id: str):
    rack = await db.racks.find_one({'id': rack_id}, {'_id': 0})
    if not rack:
        raise HTTPException(404, 'Rack not found')
    devices = await db.devices.find({'rack_id': rack_id}, {'_id': 0}).to_list(length=1000)
    device_types = {}
    for d in devices:
        if d.get('device_type_id') and d['device_type_id'] not in device_types:
            dt = await db.device_types.find_one({'id': d['device_type_id']}, {'_id': 0})
            if dt:
                device_types[d['device_type_id']] = serialize_doc(dt)
    # build elevation: position from 1..u_height (or reverse if desc_units)
    u_height = rack.get('u_height', 42)
    units = []
    for u in range(1, u_height + 1):
        occupant = None
        for d in devices:
            pos = d.get('position')
            if pos is None:
                continue
            dt = device_types.get(d.get('device_type_id'))
            uh = (dt.get('u_height') if dt else 1) or 1
            if pos <= u < pos + uh:
                occupant = {'device': serialize_doc(d), 'device_type': dt, 'is_top': u == pos + uh - 1}
                break
        units.append({'unit': u, 'occupant': occupant})
    return {
        'rack': serialize_doc(rack),
        'units': units,
        'devices': serialize_list(devices),
        'utilization': sum(1 for u in units if u['occupant']) / max(u_height, 1) * 100,
    }


# ============= CHANGE LOG =============
changelog_router = APIRouter(prefix='/changelog', tags=['Customization'])


@changelog_router.get('')
async def list_changes(
    limit: int = 100, offset: int = 0,
    object_type: Optional[str] = None,
    object_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
):
    f: Dict[str, Any] = {}
    if object_type: f['object_type'] = object_type
    if object_id: f['object_id'] = object_id
    if user_id: f['user_id'] = user_id
    if action: f['action'] = action
    total = await db.object_changes.count_documents(f)
    items = await db.object_changes.find(f, {'_id': 0}).sort('time', -1).skip(offset).limit(limit).to_list(length=limit)
    return {'total': total, 'results': serialize_list(items)}


# ============= GLOBAL SEARCH =============
search_router = APIRouter(prefix='/search', tags=['Search'])

SEARCHABLE_COLLECTIONS = [
    ('sites', 'site', ['name', 'slug', 'facility']),
    ('locations', 'location', ['name', 'slug']),
    ('tenants', 'tenant', ['name', 'slug']),
    ('racks', 'rack', ['name', 'serial', 'asset_tag', 'facility_id']),
    ('devices', 'device', ['name', 'serial', 'asset_tag']),
    ('device_types', 'device-type', ['model', 'slug', 'part_number']),
    ('manufacturers', 'manufacturer', ['name', 'slug']),
    ('interfaces', 'interface', ['name', 'mac_address']),
    ('ip_addresses', 'ip-address', ['address', 'dns_name']),
    ('prefixes', 'prefix', ['prefix']),
    ('vlans', 'vlan', ['name']),
    ('vrfs', 'vrf', ['name', 'rd']),
    ('virtual_machines', 'virtual-machine', ['name']),
    ('clusters', 'cluster', ['name']),
    ('circuits', 'circuit', ['cid']),
    ('providers', 'provider', ['name', 'slug']),
    ('cables', 'cable', ['label']),
    ('contacts', 'contact', ['name', 'email', 'phone']),
]


@search_router.get('')
async def global_search(q: str = Query(..., min_length=1), limit: int = 25):
    if not q:
        return {'results': []}
    out = []
    for col, otype, fields in SEARCHABLE_COLLECTIONS:
        regex = {'$regex': q, '$options': 'i'}
        or_clauses = [{f: regex} for f in fields]
        docs = await db[col].find({'$or': or_clauses}, {'_id': 0}).limit(limit).to_list(length=limit)
        for d in docs:
            out.append({'object_type': otype, 'object': serialize_doc(d)})
        if len(out) >= 100:
            break
    return {'query': q, 'count': len(out), 'results': out[:100]}


# ============= STATS / DASHBOARD =============
stats_router = APIRouter(prefix='/stats', tags=['Stats'])


@stats_router.get('')
async def stats():
    counters = {}
    for col in ['sites', 'locations', 'racks', 'devices', 'device_types', 'manufacturers',
                'interfaces', 'cables', 'prefixes', 'ip_addresses', 'vlans', 'vrfs', 'aggregates',
                'virtual_machines', 'clusters', 'circuits', 'providers', 'tenants',
                'wireless_lans', 'tunnels', 'l2vpns', 'power_panels', 'power_feeds',
                'contacts', 'tags', 'custom_fields', 'webhooks']:
        counters[col] = await db[col].count_documents({})
    counters['users'] = await db.users.count_documents({})
    recent_changes = await db.object_changes.find({}, {'_id': 0}).sort('time', -1).limit(10).to_list(length=10)
    return {'counters': counters, 'recent_changes': serialize_list(recent_changes)}
