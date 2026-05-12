from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .org_racks import BaseSchema, BaseUpdateSchema


# ============= IPAM =============
class RIRCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    is_private: bool = False


class RIRUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    is_private: Optional[bool] = None


class ASNRangeCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    rir_id: str
    start: int
    end: int
    tenant_id: Optional[str] = None


class ASNRangeUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    rir_id: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None
    tenant_id: Optional[str] = None


class ASNCreate(BaseSchema):
    asn: int
    rir_id: str
    tenant_id: Optional[str] = None


class ASNUpdate(BaseUpdateSchema):
    asn: Optional[int] = None
    rir_id: Optional[str] = None
    tenant_id: Optional[str] = None


class AggregateCreate(BaseSchema):
    prefix: str  # CIDR e.g., '10.0.0.0/8'
    rir_id: str
    tenant_id: Optional[str] = None
    date_added: Optional[str] = None


class AggregateUpdate(BaseUpdateSchema):
    prefix: Optional[str] = None
    rir_id: Optional[str] = None
    tenant_id: Optional[str] = None
    date_added: Optional[str] = None


class RoleCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    weight: int = 1000


class RoleUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    weight: Optional[int] = None


class PrefixCreate(BaseSchema):
    prefix: str  # CIDR
    site_id: Optional[str] = None
    vrf_id: Optional[str] = None
    tenant_id: Optional[str] = None
    vlan_id: Optional[str] = None
    status: str = 'active'  # container, active, reserved, deprecated
    role_id: Optional[str] = None
    is_pool: bool = False
    mark_utilized: bool = False
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None


class PrefixUpdate(BaseUpdateSchema):
    prefix: Optional[str] = None
    site_id: Optional[str] = None
    vrf_id: Optional[str] = None
    tenant_id: Optional[str] = None
    vlan_id: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[str] = None
    is_pool: Optional[bool] = None
    mark_utilized: Optional[bool] = None


class IPRangeCreate(BaseSchema):
    start_address: str
    end_address: str
    size: Optional[int] = None
    vrf_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: str = 'active'
    role_id: Optional[str] = None
    mark_utilized: bool = False


class IPRangeUpdate(BaseUpdateSchema):
    start_address: Optional[str] = None
    end_address: Optional[str] = None
    size: Optional[int] = None
    vrf_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[str] = None
    mark_utilized: Optional[bool] = None


class IPAddressCreate(BaseSchema):
    address: str  # e.g., '192.0.2.1/24'
    vrf_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: str = 'active'  # active, reserved, deprecated, dhcp, slaac
    role: Optional[str] = None  # loopback, secondary, anycast, vip, vrrp, hsrp, glbp, carp
    assigned_object_type: Optional[str] = None  # 'interface', 'vminterface', 'fhrpgroup'
    assigned_object_id: Optional[str] = None
    nat_inside_id: Optional[str] = None
    dns_name: Optional[str] = ''


class IPAddressUpdate(BaseUpdateSchema):
    address: Optional[str] = None
    vrf_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    assigned_object_type: Optional[str] = None
    assigned_object_id: Optional[str] = None
    nat_inside_id: Optional[str] = None
    dns_name: Optional[str] = None


class VRFCreate(BaseSchema):
    name: str
    rd: Optional[str] = None
    tenant_id: Optional[str] = None
    enforce_unique: bool = True
    import_targets: Optional[List[str]] = []
    export_targets: Optional[List[str]] = []


class VRFUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    rd: Optional[str] = None
    tenant_id: Optional[str] = None
    enforce_unique: Optional[bool] = None
    import_targets: Optional[List[str]] = None
    export_targets: Optional[List[str]] = None


class RouteTargetCreate(BaseSchema):
    name: str  # e.g., '65000:100'
    tenant_id: Optional[str] = None


class RouteTargetUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    tenant_id: Optional[str] = None


class VLANGroupCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    min_vid: int = 1
    max_vid: int = 4094


class VLANGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    min_vid: Optional[int] = None
    max_vid: Optional[int] = None


class VLANCreate(BaseSchema):
    vid: int
    name: str
    site_id: Optional[str] = None
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: str = 'active'
    role_id: Optional[str] = None
    qinq_role: Optional[str] = None
    qinq_svlan_id: Optional[str] = None


class VLANUpdate(BaseUpdateSchema):
    vid: Optional[int] = None
    name: Optional[str] = None
    site_id: Optional[str] = None
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[str] = None


class ServiceTemplateCreate(BaseSchema):
    name: str
    protocol: str  # tcp, udp, sctp
    ports: List[int]


class ServiceTemplateUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    protocol: Optional[str] = None
    ports: Optional[List[int]] = None


class ServiceCreate(BaseSchema):
    name: str
    protocol: str
    ports: List[int]
    device_id: Optional[str] = None
    virtual_machine_id: Optional[str] = None
    ipaddresses: Optional[List[str]] = []


class ServiceUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    protocol: Optional[str] = None
    ports: Optional[List[int]] = None
    device_id: Optional[str] = None
    virtual_machine_id: Optional[str] = None
    ipaddresses: Optional[List[str]] = None


class FHRPGroupCreate(BaseSchema):
    name: Optional[str] = ''
    group_id: int
    protocol: str  # vrrp2, vrrp3, hsrp, glbp, carp
    auth_type: Optional[str] = None
    auth_key: Optional[str] = ''


class FHRPGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    group_id: Optional[int] = None
    protocol: Optional[str] = None
    auth_type: Optional[str] = None
    auth_key: Optional[str] = None


class FHRPGroupAssignmentCreate(BaseSchema):
    group_id: str
    interface_type: str  # 'interface', 'vminterface'
    interface_id: str
    priority: int = 100


class FHRPGroupAssignmentUpdate(BaseUpdateSchema):
    group_id: Optional[str] = None
    interface_type: Optional[str] = None
    interface_id: Optional[str] = None
    priority: Optional[int] = None
