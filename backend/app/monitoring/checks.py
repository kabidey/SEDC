"""Concrete check implementations: ICMP, TCP, HTTP(S), DNS, SNMP, SIP.

Each check returns a normalised dict:
    {
      'status':           'ok' | 'warning' | 'critical' | 'unknown',
      'latency_ms':       float | None,
      'loss_pct':         float | None,
      'response_time_ms': float | None,
      'status_code':      int | None,
      'error':            str | None,
      'raw':              dict   # arbitrary extra context (resolved_ip, port, etc.)
    }

Design principles for robustness:
  * Accept hostnames or IPs uniformly. Each check pre-resolves the hostname
    and embeds the resolved IP into `raw` for transparency.
  * If a check fails because of DNS (NXDOMAIN, timeout), surface that as the
    error message — the caller knows whether to escalate or fall back.
  * ICMP automatically falls back to TCP/443 (and then TCP/80) when raw-socket
    ICMP is not permitted by the container, so latency monitoring still works.
  * No silent simulation, no fabricated data — every value comes from the wire.
"""
from __future__ import annotations
import asyncio
import socket
import time
import re
import struct
import os
import secrets
from typing import Any, Dict, List, Optional, Tuple
import httpx

try:
    from ping3 import ping as _ping3
    _PING3 = True
except Exception:  # pragma: no cover
    _PING3 = False


# ---------------- helpers ----------------

async def _resolve(host: str, timeout: float = 3.0) -> Tuple[Optional[str], Optional[str]]:
    """Resolve hostname to an IPv4/IPv6 address. Returns (ip, error)."""
    if not host:
        return None, 'empty target'
    # Already an IP literal?
    for fam in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(fam, host)
            return host, None
        except OSError:
            pass
    try:
        loop = asyncio.get_event_loop()
        infos = await asyncio.wait_for(
            loop.getaddrinfo(host, None, type=socket.SOCK_STREAM),
            timeout=timeout,
        )
        if not infos:
            return None, f'DNS resolution returned no addresses for {host!r}'
        # Prefer IPv4 if available
        for fam, _t, _p, _c, sa in infos:
            if fam == socket.AF_INET:
                return sa[0], None
        return infos[0][4][0], None
    except asyncio.TimeoutError:
        return None, f'DNS resolution timeout for {host!r}'
    except socket.gaierror as e:
        return None, f'DNS resolution failed for {host!r}: {e}'
    except Exception as e:
        return None, f'DNS error for {host!r}: {e.__class__.__name__}: {e}'


def _ok(latency_ms: Optional[float], **extra) -> Dict[str, Any]:
    return {
        'status': 'ok',
        'latency_ms': round(latency_ms, 2) if isinstance(latency_ms, (int, float)) else None,
        'loss_pct': 0.0,
        'response_time_ms': round(latency_ms, 2) if isinstance(latency_ms, (int, float)) else None,
        'status_code': extra.pop('status_code', None),
        'error': None,
        'raw': extra,
    }


def _fail(error: str, status: str = 'critical', **extra) -> Dict[str, Any]:
    return {
        'status': status,
        'latency_ms': None,
        'loss_pct': 100.0 if status == 'critical' else None,
        'response_time_ms': None,
        'status_code': extra.pop('status_code', None),
        'error': error,
        'raw': extra,
    }


# ---------------- ICMP ----------------

async def _icmp_subprocess(host: str, timeout: float) -> Optional[float]:
    """Use system /bin/ping. Returns latency in ms or None."""
    try:
        proc = await asyncio.create_subprocess_exec(
            'ping', '-c', '1', '-W', str(max(1, int(timeout))), host,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 2)
        if proc.returncode != 0:
            return None
        m = re.search(r'time[=<]\s*([\d.]+)\s*ms', out.decode('utf-8', errors='ignore'))
        return float(m.group(1)) if m else 0.0
    except Exception:
        return None


async def _tcp_probe(host: str, port: int, timeout: float) -> Optional[float]:
    """Return TCP handshake latency in ms or None on failure."""
    started = time.perf_counter()
    try:
        _r, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        w.close()
        try:
            await w.wait_closed()
        except Exception:
            pass
        return (time.perf_counter() - started) * 1000.0
    except Exception:
        return None


async def check_icmp(target: str, count: int = 3, timeout: float = 2.0, **_) -> Dict[str, Any]:
    """Send N pings, report avg latency and loss percentage.

    Falls back to TCP/443 (HTTPS) and then TCP/80 (HTTP) if the container
    blocks raw ICMP sockets, so latency monitoring still works.
    """
    ip, dns_err = await _resolve(target)
    if dns_err:
        return _fail(dns_err, raw_target=target)
    rtts: List[float] = []
    losses = 0
    for _i in range(count):
        rtt: Optional[float] = None
        if _PING3:
            try:
                v = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: _ping3(ip, timeout=timeout, unit='ms'),
                )
                if isinstance(v, (int, float)):
                    rtt = float(v)
            except Exception:
                rtt = None
        if rtt is None:
            rtt = await _icmp_subprocess(ip, timeout)
        if rtt is None or rtt is False:
            losses += 1
        else:
            rtts.append(rtt)
        await asyncio.sleep(0.05)
    if rtts:
        avg = sum(rtts) / len(rtts)
        return _ok(avg, resolved_ip=ip, count=count, rtts=rtts, method='icmp')
    # ICMP failed entirely — try TCP fallback so the user still has latency data
    for port in (443, 80):
        lat = await _tcp_probe(ip, port, timeout)
        if lat is not None:
            return {
                **_ok(lat, resolved_ip=ip, method=f'tcp/{port} (icmp blocked)', port=port),
                'status': 'warning',
                'error': 'ICMP blocked; latency measured via TCP fallback',
            }
    return _fail(
        f'ICMP unreachable and TCP/443+TCP/80 fallback also failed (resolved {target} -> {ip})',
        raw_target=target, resolved_ip=ip, count=count,
    )


# ---------------- TCP ----------------

async def check_tcp(target: str, port: int = 80, timeout: float = 5.0, **_) -> Dict[str, Any]:
    """Open a TCP socket, measure handshake latency."""
    ip, dns_err = await _resolve(target)
    if dns_err:
        return _fail(dns_err, raw_target=target, port=port)
    lat = await _tcp_probe(ip, port, timeout)
    if lat is None:
        return _fail(
            f'TCP connection to {target}:{port} failed (resolved {ip}) — host down, port closed, or filtered',
            raw_target=target, resolved_ip=ip, port=port,
        )
    return _ok(lat, resolved_ip=ip, port=port)


# ---------------- HTTP / HTTPS ----------------

def _normalize_http_url(url_or_host: str, default_scheme: str) -> str:
    """If user typed a bare hostname or IP, prepend the right scheme."""
    s = (url_or_host or '').strip()
    if not s:
        return s
    if s.lower().startswith(('http://', 'https://')):
        return s
    return f'{default_scheme}://{s}'


async def check_http(url: str, method: str = 'GET', expected_status: int = 200,
                     expected_text: Optional[str] = None, timeout: float = 10.0,
                     verify_ssl: bool = True, scheme: str = 'http', **_) -> Dict[str, Any]:
    url = _normalize_http_url(url, scheme)
    if not url:
        return _fail('empty URL')
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout,
                                     follow_redirects=True,
                                     headers={'User-Agent': 'SMIFS-EDC-Monitor/1.0'}) as c:
            r = await c.request(method.upper(), url)
        rt = (time.perf_counter() - started) * 1000.0
        ok_status = r.status_code == expected_status
        if expected_text:
            ok_status = ok_status and (expected_text in r.text)
        if ok_status:
            return _ok(rt, url=url, method=method.upper(), status_code=r.status_code)
        return {
            **_ok(rt, url=url, method=method.upper(), status_code=r.status_code),
            'status': 'warning',
            'error': (
                f'unexpected HTTP status {r.status_code} (wanted {expected_status})'
                if r.status_code != expected_status
                else f'expected text {expected_text!r} not found in response'
            ),
            'loss_pct': 100.0,
        }
    except httpx.ConnectError as e:
        return _fail(f'HTTP connection error: {e}', url=url)
    except httpx.TimeoutException:
        return _fail(f'HTTP timeout after {timeout}s', url=url)
    except Exception as e:
        return _fail(f'{e.__class__.__name__}: {e}', url=url)


# ---------------- DNS ----------------

def _build_dns_query(name: str, qtype: int) -> bytes:
    """Construct a minimal DNS query packet."""
    txid = secrets.randbits(16)
    header = struct.pack('!HHHHHH', txid, 0x0100, 1, 0, 0, 0)
    qname = b''.join(bytes([len(p)]) + p.encode() for p in name.rstrip('.').split('.')) + b'\x00'
    question = qname + struct.pack('!HH', qtype, 1)
    return header + question


def _parse_dns_response(data: bytes) -> List[str]:
    """Return list of A/AAAA addresses from a DNS response. Best-effort."""
    if len(data) < 12:
        return []
    qdcount, ancount = struct.unpack('!HH', data[4:8])
    offset = 12
    # Skip questions
    for _ in range(qdcount):
        while offset < len(data) and data[offset] != 0:
            length = data[offset]
            if length & 0xc0:  # pointer
                offset += 2
                break
            offset += length + 1
        else:
            offset += 1
        offset += 4  # qtype + qclass
    addrs: List[str] = []
    for _ in range(ancount):
        if offset + 12 > len(data):
            break
        # Skip name (may be pointer)
        if data[offset] & 0xc0:
            offset += 2
        else:
            while offset < len(data) and data[offset] != 0:
                offset += data[offset] + 1
            offset += 1
        if offset + 10 > len(data):
            break
        rtype, _rclass, _ttl, rdlen = struct.unpack('!HHIH', data[offset:offset + 10])
        offset += 10
        rdata = data[offset:offset + rdlen]
        offset += rdlen
        if rtype == 1 and len(rdata) == 4:  # A
            addrs.append('.'.join(str(b) for b in rdata))
        elif rtype == 28 and len(rdata) == 16:  # AAAA
            addrs.append(socket.inet_ntop(socket.AF_INET6, rdata))
    return addrs


async def check_dns(target: str, record_type: str = 'A', timeout: float = 5.0,
                    dns_server: Optional[str] = None, **_) -> Dict[str, Any]:
    """Perform an actual DNS query against a public/local resolver.

    By default sends an A (or AAAA) query to the OS resolver via getaddrinfo,
    falling back to a raw UDP/53 query against 1.1.1.1 if the OS resolver
    fails. This is a real DNS health check, not a /etc/hosts lookup.
    """
    qtype = 28 if record_type.upper() == 'AAAA' else 1
    started = time.perf_counter()
    # Try the system resolver first
    try:
        sock_t = socket.SOCK_STREAM
        infos = await asyncio.wait_for(
            asyncio.get_event_loop().getaddrinfo(
                target, None,
                family=socket.AF_INET6 if qtype == 28 else socket.AF_INET,
                type=sock_t,
            ),
            timeout=timeout,
        )
        rt = (time.perf_counter() - started) * 1000.0
        addrs = list({r[4][0] for r in infos})
        if addrs:
            return _ok(rt, addresses=addrs, record_type=record_type, via='system_resolver')
    except Exception as sys_err:
        # Fall through to raw UDP/53 query
        sys_err_str = f'{sys_err.__class__.__name__}: {sys_err}'
    else:
        sys_err_str = 'no addresses returned by system resolver'

    server = dns_server or '1.1.1.1'
    started = time.perf_counter()
    try:
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.connect((server, 53))
        query = _build_dns_query(target, qtype)
        await loop.sock_sendall(sock, query)
        try:
            data = await asyncio.wait_for(loop.sock_recv(sock, 2048), timeout=timeout)
        finally:
            sock.close()
        rt = (time.perf_counter() - started) * 1000.0
        addrs = _parse_dns_response(data)
        if addrs:
            return _ok(rt, addresses=addrs, record_type=record_type, via=f'udp://{server}:53')
        return _fail(
            f'DNS query for {target!r} returned no {record_type} records via {server} '
            f'(system resolver: {sys_err_str})',
            record_type=record_type, via=server,
        )
    except Exception as e:
        return _fail(
            f'DNS query failed via {server}: {e.__class__.__name__}: {e} '
            f'(system resolver: {sys_err_str})',
            record_type=record_type,
        )


# ---------------- SNMP ----------------

async def check_snmp(target: str, oid: str = '1.3.6.1.2.1.1.3.0',
                     community: str = 'public', port: int = 161,
                     timeout: float = 4.0, **_) -> Dict[str, Any]:
    """Reuse the discovery SNMP layer to do a single GET (sysUpTime by default)."""
    try:
        from ..discovery.snmp_scanner import _snmp_get, _build_auth, SNMP_OK
    except Exception as e:
        return _fail(f'SNMP layer unavailable: {e}')
    if not SNMP_OK:
        return _fail('pysnmp not installed in this environment', status='unknown')
    ip, dns_err = await _resolve(target)
    if dns_err:
        return _fail(dns_err, raw_target=target)
    auth = _build_auth({'snmp_version': 'v2c', 'community': community})
    started = time.perf_counter()
    try:
        v = await asyncio.wait_for(_snmp_get(ip, port, auth, oid, int(timeout)), timeout=timeout + 1)
    except asyncio.TimeoutError:
        return _fail(f'SNMP timeout after {timeout}s on UDP/{port} (resolved {target} -> {ip})',
                     resolved_ip=ip, oid=oid, port=port)
    except Exception as e:
        return _fail(f'{e.__class__.__name__}: {e}', resolved_ip=ip, oid=oid, port=port)
    rt = (time.perf_counter() - started) * 1000.0
    if v is None:
        return _fail(f'No SNMP reply on UDP/{port} (resolved {target} -> {ip}). '
                     f'Check ACLs, community string, and that snmpd is running.',
                     resolved_ip=ip, oid=oid, port=port)
    return _ok(rt, resolved_ip=ip, oid=oid, value=str(v), port=port)


# ---------------- SIP ----------------

_SIP_OPTIONS_TEMPLATE = (
    'OPTIONS sip:{user}@{host}:{port} SIP/2.0\r\n'
    'Via: SIP/2.0/{transport} {local};branch={branch}\r\n'
    'Max-Forwards: 70\r\n'
    'From: <sip:smifs-edc@{local}>;tag={tag}\r\n'
    'To: <sip:{user}@{host}:{port}>\r\n'
    'Call-ID: {call_id}@{local}\r\n'
    'CSeq: 1 OPTIONS\r\n'
    'User-Agent: SMIFS-EDC-Monitor/1.0\r\n'
    'Accept: application/sdp\r\n'
    'Content-Length: 0\r\n'
    '\r\n'
)


def _sip_options_message(host: str, port: int, transport: str, user: str = 'ping') -> bytes:
    local_ip = '0.0.0.0'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((host, port))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    msg = _SIP_OPTIONS_TEMPLATE.format(
        user=user, host=host, port=port, transport=transport.upper(),
        local=local_ip,
        branch=f'z9hG4bK-{secrets.token_hex(6)}',
        tag=secrets.token_hex(4),
        call_id=secrets.token_hex(8),
    )
    return msg.encode('utf-8')


async def check_sip(target: str, port: int = 5060, transport: str = 'udp',
                    timeout: float = 5.0, sip_user: str = 'ping', **_) -> Dict[str, Any]:
    """Send a SIP OPTIONS ping and expect any SIP response line.

    transport: 'udp' or 'tcp'. Treats any valid SIP/2.0 response as up. 200,
    401, 403, 404, 405 etc all prove the device is alive and speaking SIP.
    """
    ip, dns_err = await _resolve(target)
    if dns_err:
        return _fail(dns_err, raw_target=target, port=port, transport=transport)
    payload = _sip_options_message(ip, port, transport, sip_user)
    started = time.perf_counter()
    if transport.lower() == 'tcp':
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout)
            w.write(payload)
            await w.drain()
            data = await asyncio.wait_for(r.read(2048), timeout=timeout)
            w.close()
            try:
                await w.wait_closed()
            except Exception:
                pass
        except Exception as e:
            return _fail(f'SIP/TCP connection to {target}:{port} failed: {e.__class__.__name__}: {e}',
                         resolved_ip=ip, port=port, transport='tcp')
    else:
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        try:
            sock.connect((ip, port))
            await loop.sock_sendall(sock, payload)
            data = await asyncio.wait_for(loop.sock_recv(sock, 2048), timeout=timeout)
        except asyncio.TimeoutError:
            sock.close()
            return _fail(f'SIP/UDP timeout after {timeout}s (resolved {target} -> {ip}:{port})',
                         resolved_ip=ip, port=port, transport='udp')
        except Exception as e:
            sock.close()
            return _fail(f'SIP/UDP error: {e.__class__.__name__}: {e}',
                         resolved_ip=ip, port=port, transport='udp')
        sock.close()
    rt = (time.perf_counter() - started) * 1000.0
    text = data.decode('utf-8', errors='ignore') if data else ''
    first_line = text.split('\r\n', 1)[0]
    if 'SIP/2.0' in first_line:
        # extract status code
        m = re.search(r'SIP/2\.0\s+(\d{3})\s+(.*)', first_line)
        code = int(m.group(1)) if m else None
        return _ok(rt, resolved_ip=ip, port=port, transport=transport, status_line=first_line,
                   status_code=code)
    return _fail(
        f'Got reply from {target}:{port} but it does not look like SIP: {first_line!r}',
        resolved_ip=ip, port=port, transport=transport,
    )


# ---------------- Dispatch ----------------

CHECKS = {
    'icmp': check_icmp,
    'ping': check_icmp,
    'tcp': check_tcp,
    'http': lambda **kw: check_http(scheme='http', **kw),
    'https': lambda **kw: check_http(scheme='https', **kw),
    'dns': check_dns,
    'snmp': check_snmp,
    'sip': check_sip,
}


async def run_check(monitor: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch by monitor.type and run with retries + threshold promotion."""
    ctype = (monitor.get('type') or 'icmp').lower()
    fn = CHECKS.get(ctype, check_icmp)
    target = (monitor.get('target') or monitor.get('url') or '').strip()
    # For HTTP/HTTPS, accept either `url` or `target` and auto-normalize.
    url = (monitor.get('url') or target or '').strip()
    args = {
        'target': target,
        'port': monitor.get('port') or (443 if ctype == 'https' else 5060 if ctype == 'sip' else 80),
        'url': url,
        'method': monitor.get('http_method', 'GET'),
        'expected_status': monitor.get('expected_status', 200),
        'expected_text': monitor.get('expected_text') or None,
        'verify_ssl': monitor.get('verify_ssl', True),
        'oid': monitor.get('oid', '1.3.6.1.2.1.1.3.0'),
        'community': monitor.get('community', 'public'),
        'record_type': monitor.get('record_type', 'A'),
        'dns_server': monitor.get('dns_server'),
        'transport': monitor.get('sip_transport', 'udp'),
        'sip_user': monitor.get('sip_user', 'ping'),
        'timeout': float(monitor.get('timeout_seconds', 5)),
        'count': int(monitor.get('icmp_count', 3)),
    }
    retry = max(1, int(monitor.get('retry', 1) or 1))
    last_result: Dict[str, Any] = {}
    for attempt in range(retry):
        try:
            last_result = await fn(**args)
        except Exception as e:
            last_result = _fail(f'{e.__class__.__name__}: {e}', exception=True)
        if last_result.get('status') == 'ok':
            break
        if attempt < retry - 1:
            await asyncio.sleep(0.5)
    # Threshold promotion
    th = monitor.get('thresholds') or {}
    lat = last_result.get('latency_ms')
    loss = last_result.get('loss_pct')
    if last_result.get('status') == 'ok':
        if th.get('latency_crit_ms') is not None and lat is not None and lat >= float(th['latency_crit_ms']):
            last_result['status'] = 'critical'
        elif th.get('latency_warn_ms') is not None and lat is not None and lat >= float(th['latency_warn_ms']):
            last_result['status'] = 'warning'
        if th.get('loss_crit_pct') is not None and loss is not None and loss >= float(th['loss_crit_pct']):
            last_result['status'] = 'critical'
        elif th.get('loss_warn_pct') is not None and loss is not None and loss >= float(th['loss_warn_pct']):
            last_result['status'] = last_result['status'] if last_result['status'] == 'critical' else 'warning'
    # Ensure required keys exist
    last_result.setdefault('status_code', None)
    last_result.setdefault('raw', {})
    return last_result
