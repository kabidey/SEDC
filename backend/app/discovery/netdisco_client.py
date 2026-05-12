"""REST client for an external Netdisco instance.

Netdisco exposes a JSON/REST API typically protected by basic-auth + session cookie
(see https://github.com/netdisco/netdisco). The class below targets common endpoints
(login, devices, device-port-neighbours). If the user's Netdisco deployment
uses a different prefix it is configurable via base_url.
"""
import httpx
from typing import Any, Dict, List, Optional


class NetdiscoClient:
    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure(self):
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, verify=self.verify_ssl, timeout=15.0)
            # Try to login: Netdisco 2.x uses POST /login form-encoded
            try:
                await self._client.post('/login', data={'username': self.username, 'password': self.password})
            except Exception:
                pass
        return self._client

    async def list_devices(self, limit: int = 500) -> List[Dict[str, Any]]:
        c = await self._ensure()
        try:
            r = await c.get('/api/v1/search/device', params={'name': '%', 'count': limit}, auth=(self.username, self.password))
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and 'results' in data:
                    return data['results']
        except Exception:
            pass
        return []

    async def get_device(self, ip: str) -> Optional[Dict[str, Any]]:
        c = await self._ensure()
        try:
            r = await c.get(f'/api/v1/object/device/{ip}', auth=(self.username, self.password))
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    async def list_device_ports(self, ip: str) -> List[Dict[str, Any]]:
        c = await self._ensure()
        try:
            r = await c.get(f'/api/v1/object/device/{ip}/ports', auth=(self.username, self.password))
            if r.status_code == 200:
                d = r.json()
                return d if isinstance(d, list) else d.get('results', [])
        except Exception:
            pass
        return []

    async def list_neighbors(self, ip: str) -> List[Dict[str, Any]]:
        c = await self._ensure()
        try:
            r = await c.get(f'/api/v1/object/device/{ip}/neighbors', auth=(self.username, self.password))
            if r.status_code == 200:
                d = r.json()
                return d if isinstance(d, list) else d.get('results', [])
        except Exception:
            pass
        return []

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check(self) -> Dict[str, Any]:
        """Probe the endpoint and return health info."""
        c = await self._ensure()
        try:
            r = await c.get('/', auth=(self.username, self.password))
            return {'reachable': r.status_code < 500, 'status_code': r.status_code}
        except Exception as e:
            return {'reachable': False, 'error': str(e)}
