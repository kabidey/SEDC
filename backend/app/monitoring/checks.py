"""Concrete check implementations: ICMP, TCP, HTTP, SNMP, DNS.

Each check returns a normalized dict:
    {
      'status': 'ok' | 'warning' | 'critical' | 'unknown',
      'latency_ms': float | None,
      'loss_pct': float | None,
      'response_time_ms': float | None,
      'status_code': int | None,
      'error': str | None,
      'raw': dict (arbitrary extra context),
    }
"""
from __future__ import annotations
import asyncio
import socket
import time
import subprocess
import re
from typing import Any, Dict, Optional
import httpx

try:
    from ping3 import ping as _ping3
    _PING3 = True
except Exception:  # pragma: no cover
    _PING3 = False


async def _icmp_subprocess(host: str, timeout: float) -> Optional[float]:
    """Use system /bin/ping. Returns latency in ms or None."""
    try:
        proc = await asyncio.create_subprocess_exec(
            'ping', '-c', '1', '-W', str(int(max(1, timeout))), host,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 2)
        if proc.returncode != 0:
            return None
        m = re.search(r'time[=<]\s*([\d.]+)\s*ms', out.decode('utf-8', errors='ignore'))
        return float(m.group(1)) if m else 0.0
    except Exception:
        return None


async def check_icmp(target: str, count: int = 3, timeout: float = 2.0, **_) -> Dict[str, Any]:
    """Send N pings, report avg latency and loss percentage."""
    rtts = []
    losses = 0
    for _i in range(count):
        rtt = None
        # Prefer ping3 (no subprocess overhead), fall back to /bin/ping
        if _PING3:
            try:
                v = await asyncio.get_event_loop().run_in_executor(None, lambda: _ping3(target, timeout=timeout, unit='ms'))
                if isinstance(v, (int, float)):
                    rtt = float(v)
            except Exception:
                rtt = None
        if rtt is None:
            rtt = await _icmp_subprocess(target, timeout)
        if rtt is None or rtt is False:
            losses += 1
        else:
            rtts.append(rtt)
        await asyncio.sleep(0.05)
    if not rtts:
        return {'status': 'critical', 'latency_ms': None, 'loss_pct': 100.0, 'error': 'no reply', 'raw': {'count': count}}
    avg = sum(rtts) / len(rtts)
    loss_pct = (losses / count) * 100.0
    return {
        'status': 'ok',
        'latency_ms': round(avg, 2),
        'loss_pct': round(loss_pct, 1),
        'response_time_ms': round(avg, 2),
        'error': None,
        'raw': {'rtts': rtts, 'count': count},
    }


async def check_tcp(target: str, port: int = 80, timeout: float = 5.0, **_) -> Dict[str, Any]:
    """Open a TCP socket, measure handshake latency."""
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(target, port), timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        latency = (time.perf_counter() - started) * 1000.0
        return {'status': 'ok', 'latency_ms': round(latency, 2), 'loss_pct': 0.0, 'response_time_ms': round(latency, 2), 'error': None, 'raw': {'port': port}}
    except (asyncio.TimeoutError, OSError, ConnectionRefusedError) as e:
        return {'status': 'critical', 'latency_ms': None, 'loss_pct': 100.0, 'response_time_ms': None, 'error': str(e) or 'timeout', 'raw': {'port': port}}


async def check_http(url: str, method: str = 'GET', expected_status: int = 200, expected_text: Optional[str] = None, timeout: float = 10.0, verify_ssl: bool = True, **_) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout, follow_redirects=True) as c:
            r = await c.request(method.upper(), url)
        rt = (time.perf_counter() - started) * 1000.0
        ok = r.status_code == expected_status
        if ok and expected_text:
            ok = expected_text in r.text
        return {
            'status': 'ok' if ok else 'warning',
            'latency_ms': round(rt, 2),
            'loss_pct': 0.0 if ok else 100.0,
            'response_time_ms': round(rt, 2),
            'status_code': r.status_code,
            'error': None if ok else f'unexpected status {r.status_code} or missing text',
            'raw': {'url': url, 'method': method.upper()},
        }
    except Exception as e:
        rt = (time.perf_counter() - started) * 1000.0
        return {'status': 'critical', 'latency_ms': None, 'loss_pct': 100.0, 'response_time_ms': round(rt, 2), 'status_code': None, 'error': str(e), 'raw': {'url': url}}


async def check_dns(target: str, record_type: str = 'A', timeout: float = 5.0, **_) -> Dict[str, Any]:
    """Resolve a hostname. record_type ignored for now (A/AAAA)."""
    started = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().getaddrinfo(target, None, type=socket.SOCK_STREAM),
            timeout=timeout,
        )
        rt = (time.perf_counter() - started) * 1000.0
        addrs = list({r[4][0] for r in result})
        return {'status': 'ok', 'latency_ms': round(rt, 2), 'loss_pct': 0.0, 'response_time_ms': round(rt, 2), 'error': None, 'raw': {'addresses': addrs}}
    except Exception as e:
        return {'status': 'critical', 'latency_ms': None, 'loss_pct': 100.0, 'response_time_ms': None, 'error': str(e), 'raw': {}}


async def check_snmp(target: str, oid: str = '1.3.6.1.2.1.1.3.0', community: str = 'public', timeout: float = 4.0, **_) -> Dict[str, Any]:
    """Reuse the discovery SNMP layer to do a single GET (sysUpTime by default)."""
    try:
        from ..discovery.snmp_scanner import _snmp_get, _build_auth, SNMP_OK
        if not SNMP_OK:
            return {'status': 'unknown', 'error': 'pysnmp not available', 'raw': {}, 'latency_ms': None, 'loss_pct': None, 'response_time_ms': None}
        auth = _build_auth({'snmp_version': 'v2c', 'community': community})
        started = time.perf_counter()
        v = await asyncio.wait_for(_snmp_get(target, 161, auth, oid, int(timeout)), timeout=timeout + 1)
        rt = (time.perf_counter() - started) * 1000.0
        if v is None:
            return {'status': 'critical', 'latency_ms': None, 'loss_pct': 100.0, 'response_time_ms': round(rt, 2), 'error': 'no reply', 'raw': {'oid': oid}}
        return {'status': 'ok', 'latency_ms': round(rt, 2), 'loss_pct': 0.0, 'response_time_ms': round(rt, 2), 'error': None, 'raw': {'oid': oid, 'value': str(v)}}
    except Exception as e:
        return {'status': 'critical', 'latency_ms': None, 'loss_pct': 100.0, 'response_time_ms': None, 'error': str(e), 'raw': {'oid': oid}}


CHECKS = {
    'icmp': check_icmp,
    'tcp': check_tcp,
    'http': check_http,
    'https': check_http,
    'dns': check_dns,
    'snmp': check_snmp,
}


async def run_check(monitor: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch by monitor.type and run with retries."""
    ctype = (monitor.get('type') or 'icmp').lower()
    fn = CHECKS.get(ctype, check_icmp)
    target = monitor.get('target') or monitor.get('url') or ''
    args = {
        'target': target,
        'port': monitor.get('port', 80),
        'url': monitor.get('url') or target,
        'method': monitor.get('http_method', 'GET'),
        'expected_status': monitor.get('expected_status', 200),
        'expected_text': monitor.get('expected_text'),
        'verify_ssl': monitor.get('verify_ssl', True),
        'oid': monitor.get('oid', '1.3.6.1.2.1.1.3.0'),
        'community': monitor.get('community', 'public'),
        'record_type': monitor.get('record_type', 'A'),
        'timeout': float(monitor.get('timeout_seconds', 5)),
        'count': int(monitor.get('icmp_count', 3)),
    }
    retry = int(monitor.get('retry', 1)) or 1
    last_result = None
    for attempt in range(retry):
        try:
            last_result = await fn(**args)
        except Exception as e:
            last_result = {'status': 'unknown', 'error': str(e), 'latency_ms': None, 'loss_pct': None, 'response_time_ms': None, 'raw': {}}
        if last_result.get('status') == 'ok':
            break
        if attempt < retry - 1:
            await asyncio.sleep(0.5)
    # Apply thresholds
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
    return last_result
