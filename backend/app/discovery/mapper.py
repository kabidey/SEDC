"""Map raw discovery results into SMIFS Devices, Interfaces, IP addresses
and inferred Cables (from LLDP neighbours).
"""
from typing import Any, Dict, List, Optional, Tuple
from ..db import db
from ..utils import new_id, now_iso, slugify, serialize_doc
from ..changelog import log_change


async def _ensure(collection: str, query: Dict[str, Any], doc: Dict[str, Any], user) -> Dict[str, Any]:
    existing = await db[collection].find_one(query, {'_id': 0})
    if existing:
        return existing
    doc['id'] = doc.get('id') or new_id()
    doc['created'] = now_iso()
    doc['last_updated'] = now_iso()
    if 'name' in doc and not doc.get('slug'):
        doc['slug'] = slugify(doc['name'])
    await db[collection].insert_one(doc)
    doc.pop('_id', None)
    await log_change('create', collection.rstrip('s').replace('_', '-'), doc['id'], doc.get('name') or doc.get('model') or doc['id'], user, None, doc)
    return doc


async def import_discovered_device(disc: Dict[str, Any], site_id: Optional[str], user: Dict[str, Any]) -> Dict[str, Any]:
    """Create/Update SMIFS Device + components from a discovered-device dict.

    `disc` shape is what `snmp_scanner.scan_target` returns or what
    `DiscoveredDevice` documents store.
    """
    # Manufacturer
    vendor = (disc.get('vendor') or 'Unknown').strip() or 'Unknown'
    manuf = await _ensure('manufacturers',
                          {'name': vendor},
                          {'name': vendor},
                          user)
    # Device type (model)
    model = disc.get('model') or 'Auto-discovered'
    dt = await _ensure('device_types',
                       {'manufacturer_id': manuf['id'], 'model': model},
                       {'manufacturer_id': manuf['id'], 'model': model, 'u_height': 1.0, 'is_full_depth': True, 'part_number': ''},
                       user)
    # Role
    role_name = (disc.get('role') or 'Network Device').strip()
    role = await _ensure('device_roles', {'name': role_name}, {'name': role_name, 'color': '10b981', 'vm_role': True}, user)
    # Site (default if not provided): create or find 'Auto-Discovered' site
    if not site_id:
        site = await _ensure('sites', {'name': 'Auto-Discovered'}, {'name': 'Auto-Discovered', 'status': 'active', 'facility': 'auto'}, user)
        site_id = site['id']
    # Device upsert by sysname OR primary target IP
    name = disc.get('sysname') or disc.get('target')
    existing = await db.devices.find_one({'name': name}, {'_id': 0})
    if existing:
        device = existing
    else:
        device = {
            'id': new_id(),
            'name': name,
            'device_type_id': dt['id'],
            'role_id': role['id'],
            'site_id': site_id,
            'status': 'active',
            'serial': disc.get('serial', ''),
            'asset_tag': '',
            'description': disc.get('sysdescr', ''),
            'comments': f"Discovered via SNMP. Location: {disc.get('syslocation', '')}",
            'tags': ['auto-discovered'],
            'custom_fields': {},
            'created': now_iso(),
            'last_updated': now_iso(),
        }
        await db.devices.insert_one(device)
        device.pop('_id', None)
        await log_change('create', 'device', device['id'], name, user, None, device)
    # Interfaces
    created_ifs = 0
    for ifc in (disc.get('interfaces') or []):
        iface_q = {'device_id': device['id'], 'name': ifc['name']}
        existing_if = await db.interfaces.find_one(iface_q, {'_id': 0})
        if existing_if:
            continue
        doc = {
            'id': new_id(),
            'device_id': device['id'],
            'name': ifc['name'],
            'label': ifc.get('descr', '') or '',
            'type': '1000base-t',
            'enabled': ifc.get('oper_status') == 'up',
            'mtu': ifc.get('mtu'),
            'mac_address': ifc.get('mac', '') or None,
            'speed': ifc.get('speed'),
            'description': ifc.get('alias', '') or '',
            'tags': ['auto-discovered'],
            'custom_fields': {'ifindex': ifc.get('ifindex')},
            'created': now_iso(),
            'last_updated': now_iso(),
        }
        await db.interfaces.insert_one(doc)
        doc.pop('_id', None)
        await log_change('create', 'interface', doc['id'], doc['name'], user, None, doc)
        created_ifs += 1
    # IP addresses
    created_ips = 0
    for addr in (disc.get('ip_addresses') or []):
        existing_ip = await db.ip_addresses.find_one({'address': addr}, {'_id': 0})
        if existing_ip:
            continue
        doc = {
            'id': new_id(),
            'address': addr,
            'status': 'active',
            'tags': ['auto-discovered'],
            'custom_fields': {},
            'created': now_iso(),
            'last_updated': now_iso(),
        }
        await db.ip_addresses.insert_one(doc)
        doc.pop('_id', None)
        await log_change('create', 'ip-address', doc['id'], addr, user, None, doc)
        created_ips += 1
    # Neighbors -> cables (best-effort, if remote interface and local interface known)
    created_cables = 0
    for nb in (disc.get('neighbors') or []):
        local_port = nb.get('local_port')
        remote_name = nb.get('remote_system_name') or nb.get('remote_chassis_id')
        remote_port = nb.get('remote_port')
        if not (local_port and remote_name and remote_port):
            continue
        local_if = await db.interfaces.find_one({'device_id': device['id'], 'name': local_port}, {'_id': 0})
        remote_device = await db.devices.find_one({'name': remote_name}, {'_id': 0})
        if not (local_if and remote_device):
            continue
        remote_if = await db.interfaces.find_one({'device_id': remote_device['id'], 'name': remote_port}, {'_id': 0})
        if not remote_if:
            continue
        # Already cabled?
        already = await db.cables.find_one({
            '$or': [
                {'a_terminations.object_id': local_if['id']},
                {'b_terminations.object_id': local_if['id']},
            ]
        }, {'_id': 0})
        if already:
            continue
        cable = {
            'id': new_id(),
            'a_terminations': [{'object_type': 'interface', 'object_id': local_if['id']}],
            'b_terminations': [{'object_type': 'interface', 'object_id': remote_if['id']}],
            'status': 'connected',
            'type': 'cat6',
            'label': f"auto-discovered {local_port} ↔ {remote_port}",
            'tags': ['auto-discovered'],
            'custom_fields': {},
            'created': now_iso(),
            'last_updated': now_iso(),
        }
        await db.cables.insert_one(cable)
        cable.pop('_id', None)
        await log_change('create', 'cable', cable['id'], cable['label'], user, None, cable)
        created_cables += 1
    return {
        'device_id': device['id'],
        'device_name': name,
        'interfaces_created': created_ifs,
        'ips_created': created_ips,
        'cables_created': created_cables,
    }
