"""SNMP-based device discovery (Netdisco-compatible).

Collects sysName, sysDescr, ifTable, ipAddrTable, and LLDP neighbours from
real SNMP-speaking devices. Targets that are unreachable or that fail SNMP
auth return an *honest* unreachable result with an error message — there
is **no simulation, no fake data, no fallback**. If you see results in
the UI, they came from real wire traffic.
"""
from __future__ import annotations
import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    from pysnmp.hlapi.asyncio import (
        SnmpEngine, CommunityData, UsmUserData, UdpTransportTarget,
        ContextData, ObjectType, ObjectIdentity, getCmd, walkCmd,
        usmHMACSHAAuthProtocol, usmAesCfb128Protocol, usmNoAuthProtocol,
        usmNoPrivProtocol,
    )
    SNMP_OK = True
    SNMP_IMPORT_ERROR: Optional[str] = None
except Exception as _e:  # pragma: no cover
    SNMP_OK = False
    SNMP_IMPORT_ERROR = str(_e)

OID_SYSDESCR = '1.3.6.1.2.1.1.1.0'
OID_SYSOBJECTID = '1.3.6.1.2.1.1.2.0'
OID_SYSUPTIME = '1.3.6.1.2.1.1.3.0'
OID_SYSCONTACT = '1.3.6.1.2.1.1.4.0'
OID_SYSNAME = '1.3.6.1.2.1.1.5.0'
OID_SYSLOCATION = '1.3.6.1.2.1.1.6.0'
OID_IFDESCR = '1.3.6.1.2.1.2.2.1.2'
OID_IFTYPE = '1.3.6.1.2.1.2.2.1.3'
OID_IFMTU = '1.3.6.1.2.1.2.2.1.4'
OID_IFSPEED = '1.3.6.1.2.1.2.2.1.5'
OID_IFPHYS = '1.3.6.1.2.1.2.2.1.6'
OID_IFOPER = '1.3.6.1.2.1.2.2.1.8'
OID_IFNAME = '1.3.6.1.2.1.31.1.1.1.1'
OID_IFALIAS = '1.3.6.1.2.1.31.1.1.1.18'
OID_IPADDRENT = '1.3.6.1.2.1.4.20.1'
OID_LLDP_REMTABLE = '1.0.8802.1.1.2.1.4.1.1'

# Heuristic vendor detection by sysDescr regex
VENDORS = [
    (r'cisco|ios', 'Cisco'),
    (r'juniper|junos', 'Juniper'),
    (r'arista|eos', 'Arista'),
    (r'mikrotik|routeros', 'MikroTik'),
    (r'huawei|vrp', 'Huawei'),
    (r'fortinet|fortigate', 'Fortinet'),
    (r'palo alto|panos', 'Palo Alto Networks'),
    (r'ubiquiti|edgeos|unifi', 'Ubiquiti'),
    (r'dell|os10|force10', 'Dell'),
    (r'hp|hpe|procurve|aruba', 'HPE'),
    (r'extreme|exos', 'Extreme Networks'),
    (r'linux', 'Linux'),
    (r'windows', 'Microsoft'),
    (r'freebsd|openbsd|netbsd', 'BSD'),
]


def _vendor_from_desc(desc: str) -> str:
    s = (desc or '').lower()
    for pat, vendor in VENDORS:
        if re.search(pat, s):
            return vendor
    return 'Unknown'


def _model_from_desc(desc: str) -> str:
    if not desc:
        return ''
    m = re.search(r'\b([A-Z][A-Z0-9\-]{2,})\b', desc)
    return m.group(1) if m else desc.split()[0][:40]


def _detail(varbinds) -> Optional[str]:
    for _name, val in varbinds:
        try:
            return val.prettyPrint()
        except Exception:
            return str(val)
    return None


async def _snmp_get(target: str, port: int, auth, oid: str, timeout: int) -> Optional[str]:
    iterator = getCmd(
        SnmpEngine(),
        auth,
        UdpTransportTarget((target, port), timeout=timeout, retries=0),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    err_ind, err_status, _, varbinds = await iterator
    if err_ind or err_status:
        return None
    return _detail(varbinds)


async def _snmp_walk(target: str, port: int, auth, base_oid: str, timeout: int, max_rows: int = 500) -> List[Tuple[str, str]]:
    """Walk a sub-tree. Returns list of (oid, value) pairs.

    Uses pysnmp 6.x `walkCmd` (async generator).
    """
    out: List[Tuple[str, str]] = []
    g = walkCmd(
        SnmpEngine(), auth,
        UdpTransportTarget((target, port), timeout=timeout, retries=0),
        ContextData(),
        ObjectType(ObjectIdentity(base_oid)),
        lexicographicMode=False,
    )
    async for err_ind, err_status, _, varbinds in g:  # type: ignore
        if err_ind or err_status:
            break
        for name, val in varbinds:
            try:
                out.append((name.prettyPrint(), val.prettyPrint()))
            except Exception:
                out.append((str(name), str(val)))
        if len(out) >= max_rows:
            break
    return out


def _build_auth(credential: Dict[str, Any]):
    """Convert a Credential dict into a pysnmp auth object."""
    version = credential.get('snmp_version', 'v2c')
    if version in ('v1', 'v2c'):
        return CommunityData(credential.get('community', 'public'),
                             mpModel=0 if version == 'v1' else 1)
    # v3
    return UsmUserData(
        credential.get('username', ''),
        authKey=credential.get('auth_key') or None,
        privKey=credential.get('priv_key') or None,
        authProtocol=usmHMACSHAAuthProtocol if credential.get('auth_key') else usmNoAuthProtocol,
        privProtocol=usmAesCfb128Protocol if credential.get('priv_key') else usmNoPrivProtocol,
    )


def _empty_result(target: str, error: str) -> Dict[str, Any]:
    """Return an honest 'unreachable' record. No fabricated fields."""
    return {
        'target': target,
        'reachable': False,
        'error': error,
        'sysname': '',
        'sysdescr': '',
        'syscontact': '',
        'syslocation': '',
        'sysobjectid': '',
        'vendor': '',
        'model': '',
        'role': '',
        'interfaces': [],
        'ip_addresses': [],
        'neighbors': [],
    }


async def scan_target(target: str, credential: Dict[str, Any], timeout: int = 4) -> Dict[str, Any]:
    """Scan a single host with SNMP. Returns a normalised dict.

    On any failure (pysnmp missing, no reply, auth error, exception) returns
    an *honest* unreachable record with the error message. No simulation.
    """
    port = credential.get('port', 161)
    if not SNMP_OK:
        return _empty_result(target, f'SNMP library not available: {SNMP_IMPORT_ERROR}')
    try:
        auth = _build_auth(credential)
        # Probe sysDescr first to confirm reachability
        try:
            sys_descr = await asyncio.wait_for(
                _snmp_get(target, port, auth, OID_SYSDESCR, timeout),
                timeout=timeout + 1,
            )
        except asyncio.TimeoutError:
            return _empty_result(target, f'SNMP timeout after {timeout}s on UDP/{port}')
        if sys_descr is None:
            return _empty_result(
                target,
                f'No SNMP reply on UDP/{port} (check reachability, community/credential, ACLs and firewall)',
            )
        sys_name = await _snmp_get(target, port, auth, OID_SYSNAME, timeout)
        sys_contact = await _snmp_get(target, port, auth, OID_SYSCONTACT, timeout)
        sys_location = await _snmp_get(target, port, auth, OID_SYSLOCATION, timeout)
        sys_oid = await _snmp_get(target, port, auth, OID_SYSOBJECTID, timeout)
        # Walks
        ifdescr_rows = await _snmp_walk(target, port, auth, OID_IFDESCR, timeout)
        ifname_rows = await _snmp_walk(target, port, auth, OID_IFNAME, timeout)
        iftype_rows = await _snmp_walk(target, port, auth, OID_IFTYPE, timeout)
        ifspeed_rows = await _snmp_walk(target, port, auth, OID_IFSPEED, timeout)
        ifmac_rows = await _snmp_walk(target, port, auth, OID_IFPHYS, timeout)
        ifoper_rows = await _snmp_walk(target, port, auth, OID_IFOPER, timeout)
        ifalias_rows = await _snmp_walk(target, port, auth, OID_IFALIAS, timeout)
        ipaddr_rows = await _snmp_walk(target, port, auth, OID_IPADDRENT, timeout)

        def _index(rows):
            d = {}
            for oid, val in rows:
                d[oid.rsplit('.', 1)[-1]] = val
            return d
        descrs = _index(ifdescr_rows)
        names = _index(ifname_rows)
        types = _index(iftype_rows)
        speeds = _index(ifspeed_rows)
        macs = _index(ifmac_rows)
        opers = _index(ifoper_rows)
        aliases = _index(ifalias_rows)
        all_idx = sorted(set(list(descrs.keys()) + list(names.keys())), key=lambda x: int(x) if x.isdigit() else 0)
        interfaces = []
        for idx in all_idx:
            interfaces.append({
                'ifindex': int(idx) if idx.isdigit() else idx,
                'name': names.get(idx) or descrs.get(idx) or f'if{idx}',
                'descr': descrs.get(idx) or '',
                'alias': aliases.get(idx) or '',
                'type': types.get(idx) or '',
                'speed': int(speeds.get(idx)) if (speeds.get(idx) or '').isdigit() else None,
                'mac': macs.get(idx) or '',
                'oper_status': 'up' if opers.get(idx) in ('1', 'up') else 'down',
            })
        # IP addresses
        ip_addresses = []
        for oid, val in ipaddr_rows:
            if '.4.20.1.1.' in oid:
                ip_addresses.append(val + '/32')
        # LLDP neighbours
        try:
            lldp_rows = await _snmp_walk(target, port, auth, OID_LLDP_REMTABLE, timeout)
        except Exception:
            lldp_rows = []
        nb_map: Dict[str, Dict[str, Any]] = {}
        for oid, val in lldp_rows:
            parts = oid.split('.')
            try:
                remote_idx = parts[-2]
            except Exception:
                continue
            nb = nb_map.setdefault(remote_idx, {})
            if '.5.' in oid:
                nb['remote_chassis_id'] = val
            if '.7.' in oid:
                nb['remote_port'] = val
            if '.9.' in oid:
                nb['remote_system_name'] = val
        neighbors = [nb for nb in nb_map.values() if nb]

        vendor = _vendor_from_desc(sys_descr)
        return {
            'target': target,
            'reachable': True,
            'error': None,
            'sysname': sys_name or '',
            'sysdescr': sys_descr or '',
            'syscontact': sys_contact or '',
            'syslocation': sys_location or '',
            'sysobjectid': sys_oid or '',
            'vendor': vendor,
            'model': _model_from_desc(sys_descr or ''),
            'role': '',
            'interfaces': interfaces,
            'ip_addresses': ip_addresses,
            'neighbors': neighbors,
        }
    except Exception as e:
        return _empty_result(target, f'SNMP error: {e.__class__.__name__}: {e}')


async def scan_range(targets: List[str], credential: Dict[str, Any], concurrency: int = 16, timeout: int = 4) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)

    async def _one(t: str) -> Dict[str, Any]:
        async with sem:
            try:
                return await scan_target(t, credential, timeout=timeout)
            except Exception as e:
                return _empty_result(t, f'{e.__class__.__name__}: {e}')
    return await asyncio.gather(*[_one(t) for t in targets])


def expand_targets(spec: str) -> List[str]:
    """Expand a target spec: comma-separated list of IPs, ranges (10.0.0.1-10), or CIDR."""
    import ipaddress
    out: List[str] = []
    for chunk in (spec or '').split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            if '/' in chunk:
                net = ipaddress.ip_network(chunk, strict=False)
                for h in net.hosts():
                    out.append(str(h))
                    if len(out) > 1024:
                        return out
            elif '-' in chunk:
                base, end = chunk.split('-', 1)
                base_ip = ipaddress.ip_address(base.strip())
                if '.' in end:
                    end_ip = ipaddress.ip_address(end.strip())
                else:
                    parts = str(base_ip).split('.')
                    parts[-1] = end.strip()
                    end_ip = ipaddress.ip_address('.'.join(parts))
                cur = int(base_ip)
                while cur <= int(end_ip) and len(out) <= 1024:
                    out.append(str(ipaddress.ip_address(cur)))
                    cur += 1
            else:
                out.append(chunk)
        except Exception:
            out.append(chunk)
    return out
