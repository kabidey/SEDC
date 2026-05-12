"""Simple GraphQL endpoint exposing read access to all major models."""
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional
from .db import db
from .utils import serialize_doc
import json


@strawberry.type
class GenericObject:
    id: str
    data: str  # JSON serialized

    @staticmethod
    def from_doc(doc: dict) -> 'GenericObject':
        d = serialize_doc(doc) or {}
        return GenericObject(id=str(d.get('id', '')), data=json.dumps(d))


COLLECTIONS = {
    'sites': 'sites', 'site_groups': 'site_groups', 'regions': 'regions',
    'locations': 'locations', 'tenants': 'tenants', 'tenant_groups': 'tenant_groups',
    'contacts': 'contacts', 'contact_groups': 'contact_groups', 'contact_roles': 'contact_roles',
    'racks': 'racks', 'rack_roles': 'rack_roles',
    'manufacturers': 'manufacturers', 'device_types': 'device_types',
    'module_types': 'module_types', 'device_roles': 'device_roles',
    'platforms': 'platforms', 'devices': 'devices', 'modules': 'modules',
    'interfaces': 'interfaces', 'cables': 'cables',
    'rirs': 'rirs', 'aggregates': 'aggregates', 'prefixes': 'prefixes',
    'ip_addresses': 'ip_addresses', 'ip_ranges': 'ip_ranges', 'vrfs': 'vrfs',
    'vlans': 'vlans', 'vlan_groups': 'vlan_groups', 'asns': 'asns',
    'providers': 'providers', 'circuits': 'circuits', 'circuit_types': 'circuit_types',
    'power_panels': 'power_panels', 'power_feeds': 'power_feeds',
    'clusters': 'clusters', 'cluster_types': 'cluster_types',
    'virtual_machines': 'virtual_machines', 'vm_interfaces': 'vm_interfaces',
    'wireless_lans': 'wireless_lans', 'wireless_links': 'wireless_links',
    'l2vpns': 'l2vpns', 'tunnels': 'tunnels',
    'tags': 'tags', 'custom_fields': 'custom_fields',
    'webhooks': 'webhooks', 'config_contexts': 'config_contexts',
}


@strawberry.type
class Query:
    @strawberry.field
    async def collection(self, name: str, limit: int = 100, q: Optional[str] = None) -> List[GenericObject]:
        col = COLLECTIONS.get(name)
        if not col:
            return []
        filt = {}
        if q:
            filt = {'$or': [{'name': {'$regex': q, '$options': 'i'}}, {'slug': {'$regex': q, '$options': 'i'}}]}
        docs = await db[col].find(filt, {'_id': 0}).limit(limit).to_list(length=limit)
        return [GenericObject.from_doc(d) for d in docs]

    @strawberry.field
    async def object(self, name: str, id: str) -> Optional[GenericObject]:
        col = COLLECTIONS.get(name)
        if not col:
            return None
        doc = await db[col].find_one({'id': id}, {'_id': 0})
        if not doc:
            return None
        return GenericObject.from_doc(doc)

    @strawberry.field
    async def collections(self) -> List[str]:
        return list(COLLECTIONS.keys())


schema = strawberry.Schema(query=Query)
graphql_router = GraphQLRouter(schema)
