from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .org_racks import BaseSchema, BaseUpdateSchema


# ============= CIRCUITS =============
class ProviderCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    asns: Optional[List[str]] = []
    accounts: Optional[List[str]] = []


class ProviderUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    asns: Optional[List[str]] = None
    accounts: Optional[List[str]] = None


class ProviderAccountCreate(BaseSchema):
    name: str
    account: str
    provider_id: str


class ProviderAccountUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    account: Optional[str] = None
    provider_id: Optional[str] = None


class ProviderNetworkCreate(BaseSchema):
    name: str
    provider_id: str
    service_id: Optional[str] = ''


class ProviderNetworkUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    provider_id: Optional[str] = None
    service_id: Optional[str] = None


class CircuitTypeCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    color: Optional[str] = '10b981'


class CircuitTypeUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = None


class CircuitCreate(BaseSchema):
    cid: str
    provider_id: str
    provider_account_id: Optional[str] = None
    type_id: str
    status: str = 'active'
    tenant_id: Optional[str] = None
    install_date: Optional[str] = None
    termination_date: Optional[str] = None
    commit_rate: Optional[int] = None


class CircuitUpdate(BaseUpdateSchema):
    cid: Optional[str] = None
    provider_id: Optional[str] = None
    provider_account_id: Optional[str] = None
    type_id: Optional[str] = None
    status: Optional[str] = None
    tenant_id: Optional[str] = None
    install_date: Optional[str] = None
    termination_date: Optional[str] = None
    commit_rate: Optional[int] = None


class CircuitTerminationCreate(BaseSchema):
    circuit_id: str
    term_side: str  # 'A' or 'Z'
    site_id: Optional[str] = None
    provider_network_id: Optional[str] = None
    port_speed: Optional[int] = None
    upstream_speed: Optional[int] = None
    xconnect_id: Optional[str] = ''
    pp_info: Optional[str] = ''


class CircuitTerminationUpdate(BaseUpdateSchema):
    circuit_id: Optional[str] = None
    term_side: Optional[str] = None
    site_id: Optional[str] = None
    provider_network_id: Optional[str] = None
    port_speed: Optional[int] = None
    upstream_speed: Optional[int] = None
    xconnect_id: Optional[str] = None
    pp_info: Optional[str] = None


# ============= POWER =============
class PowerPanelCreate(BaseSchema):
    name: str
    site_id: str
    location_id: Optional[str] = None


class PowerPanelUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    site_id: Optional[str] = None
    location_id: Optional[str] = None


class PowerFeedCreate(BaseSchema):
    name: str
    power_panel_id: str
    rack_id: Optional[str] = None
    status: str = 'active'
    type: str = 'primary'  # primary, redundant
    supply: str = 'ac'  # ac, dc
    phase: str = 'single-phase'
    voltage: int = 230
    amperage: int = 32
    max_utilization: int = 80


class PowerFeedUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    power_panel_id: Optional[str] = None
    rack_id: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    supply: Optional[str] = None
    phase: Optional[str] = None
    voltage: Optional[int] = None
    amperage: Optional[int] = None
    max_utilization: Optional[int] = None


# ============= VIRTUALIZATION =============
class ClusterTypeCreate(BaseSchema):
    name: str
    slug: Optional[str] = None


class ClusterTypeUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None


class ClusterGroupCreate(BaseSchema):
    name: str
    slug: Optional[str] = None


class ClusterGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None


class ClusterCreate(BaseSchema):
    name: str
    type_id: str
    group_id: Optional[str] = None
    status: str = 'active'
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None


class ClusterUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    type_id: Optional[str] = None
    group_id: Optional[str] = None
    status: Optional[str] = None
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None


class VirtualMachineCreate(BaseSchema):
    name: str
    status: str = 'active'
    cluster_id: Optional[str] = None
    device_id: Optional[str] = None
    role_id: Optional[str] = None
    tenant_id: Optional[str] = None
    platform_id: Optional[str] = None
    primary_ip4_id: Optional[str] = None
    primary_ip6_id: Optional[str] = None
    vcpus: Optional[float] = None
    memory: Optional[int] = None  # MB
    disk: Optional[int] = None  # GB
    serial: Optional[str] = ''
    site_id: Optional[str] = None


class VirtualMachineUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    status: Optional[str] = None
    cluster_id: Optional[str] = None
    device_id: Optional[str] = None
    role_id: Optional[str] = None
    tenant_id: Optional[str] = None
    platform_id: Optional[str] = None
    primary_ip4_id: Optional[str] = None
    primary_ip6_id: Optional[str] = None
    vcpus: Optional[float] = None
    memory: Optional[int] = None
    disk: Optional[int] = None
    serial: Optional[str] = None
    site_id: Optional[str] = None


class VMInterfaceCreate(BaseSchema):
    virtual_machine_id: str
    name: str
    enabled: bool = True
    mtu: Optional[int] = None
    mac_address: Optional[str] = None
    description: Optional[str] = ''
    mode: Optional[str] = None
    untagged_vlan_id: Optional[str] = None
    tagged_vlans: Optional[List[str]] = []
    vrf_id: Optional[str] = None
    parent_id: Optional[str] = None
    bridge_id: Optional[str] = None


class VMInterfaceUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    mtu: Optional[int] = None
    mac_address: Optional[str] = None
    mode: Optional[str] = None
    untagged_vlan_id: Optional[str] = None
    tagged_vlans: Optional[List[str]] = None
    vrf_id: Optional[str] = None
    parent_id: Optional[str] = None
    bridge_id: Optional[str] = None
    virtual_machine_id: Optional[str] = None


class VirtualDiskCreate(BaseSchema):
    virtual_machine_id: str
    name: str
    size: int  # MB


class VirtualDiskUpdate(BaseUpdateSchema):
    virtual_machine_id: Optional[str] = None
    name: Optional[str] = None
    size: Optional[int] = None


# ============= WIRELESS =============
class WirelessLANGroupCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class WirelessLANGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class WirelessLANCreate(BaseSchema):
    ssid: str
    group_id: Optional[str] = None
    status: str = 'active'
    vlan_id: Optional[str] = None
    tenant_id: Optional[str] = None
    auth_type: Optional[str] = 'open'
    auth_cipher: Optional[str] = 'auto'
    auth_psk: Optional[str] = ''


class WirelessLANUpdate(BaseUpdateSchema):
    ssid: Optional[str] = None
    group_id: Optional[str] = None
    status: Optional[str] = None
    vlan_id: Optional[str] = None
    tenant_id: Optional[str] = None
    auth_type: Optional[str] = None
    auth_cipher: Optional[str] = None
    auth_psk: Optional[str] = None


class WirelessLinkCreate(BaseSchema):
    interface_a_id: str
    interface_b_id: str
    ssid: Optional[str] = ''
    status: str = 'connected'
    tenant_id: Optional[str] = None
    auth_type: Optional[str] = 'open'
    auth_cipher: Optional[str] = 'auto'
    auth_psk: Optional[str] = ''
    distance: Optional[float] = None
    distance_unit: Optional[str] = 'm'


class WirelessLinkUpdate(BaseUpdateSchema):
    interface_a_id: Optional[str] = None
    interface_b_id: Optional[str] = None
    ssid: Optional[str] = None
    status: Optional[str] = None
    tenant_id: Optional[str] = None
    auth_type: Optional[str] = None
    auth_cipher: Optional[str] = None
    auth_psk: Optional[str] = None
    distance: Optional[float] = None
    distance_unit: Optional[str] = None


# ============= VPN / OVERLAY =============
class L2VPNCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    identifier: Optional[int] = None
    type: str = 'vxlan'  # vxlan, vpls, mpls-evpn, etc.
    tenant_id: Optional[str] = None
    import_targets: Optional[List[str]] = []
    export_targets: Optional[List[str]] = []


class L2VPNUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    identifier: Optional[int] = None
    type: Optional[str] = None
    tenant_id: Optional[str] = None
    import_targets: Optional[List[str]] = None
    export_targets: Optional[List[str]] = None


class L2VPNTerminationCreate(BaseSchema):
    l2vpn_id: str
    assigned_object_type: str  # 'vlan', 'interface', 'vminterface'
    assigned_object_id: str


class L2VPNTerminationUpdate(BaseUpdateSchema):
    l2vpn_id: Optional[str] = None
    assigned_object_type: Optional[str] = None
    assigned_object_id: Optional[str] = None


class TunnelGroupCreate(BaseSchema):
    name: str
    slug: Optional[str] = None


class TunnelGroupUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None


class TunnelCreate(BaseSchema):
    name: str
    group_id: Optional[str] = None
    status: str = 'active'
    encapsulation: str = 'gre'  # gre, ip-ip, ipsec-transport, ipsec-tunnel, wireguard, openvpn
    ipsec_profile_id: Optional[str] = None
    tenant_id: Optional[str] = None
    tunnel_id: Optional[int] = None


class TunnelUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    group_id: Optional[str] = None
    status: Optional[str] = None
    encapsulation: Optional[str] = None
    ipsec_profile_id: Optional[str] = None
    tenant_id: Optional[str] = None
    tunnel_id: Optional[int] = None


class TunnelTerminationCreate(BaseSchema):
    tunnel_id: str
    role: str  # 'peer', 'hub', 'spoke'
    termination_type: str  # 'interface', 'vminterface'
    termination_id: str
    outside_ip_id: Optional[str] = None


class TunnelTerminationUpdate(BaseUpdateSchema):
    tunnel_id: Optional[str] = None
    role: Optional[str] = None
    termination_type: Optional[str] = None
    termination_id: Optional[str] = None
    outside_ip_id: Optional[str] = None


class IKEProposalCreate(BaseSchema):
    name: str
    authentication_method: str = 'preshared-keys'
    encryption_algorithm: str = 'aes-256-cbc'
    authentication_algorithm: str = 'sha256'
    group: int = 14
    sa_lifetime: Optional[int] = None


class IKEProposalUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    authentication_method: Optional[str] = None
    encryption_algorithm: Optional[str] = None
    authentication_algorithm: Optional[str] = None
    group: Optional[int] = None
    sa_lifetime: Optional[int] = None


class IKEPolicyCreate(BaseSchema):
    name: str
    version: int = 2
    mode: Optional[str] = None
    proposals: List[str] = []
    preshared_key: Optional[str] = ''


class IKEPolicyUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    version: Optional[int] = None
    mode: Optional[str] = None
    proposals: Optional[List[str]] = None
    preshared_key: Optional[str] = None


class IPSecProposalCreate(BaseSchema):
    name: str
    encryption_algorithm: str = 'aes-256-cbc'
    authentication_algorithm: str = 'sha256'
    sa_lifetime_seconds: Optional[int] = None
    sa_lifetime_data: Optional[int] = None


class IPSecProposalUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    encryption_algorithm: Optional[str] = None
    authentication_algorithm: Optional[str] = None
    sa_lifetime_seconds: Optional[int] = None
    sa_lifetime_data: Optional[int] = None


class IPSecPolicyCreate(BaseSchema):
    name: str
    proposals: List[str] = []
    pfs_group: Optional[int] = None


class IPSecPolicyUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    proposals: Optional[List[str]] = None
    pfs_group: Optional[int] = None


class IPSecProfileCreate(BaseSchema):
    name: str
    mode: str = 'esp'
    ike_policy_id: str
    ipsec_policy_id: str


class IPSecProfileUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    mode: Optional[str] = None
    ike_policy_id: Optional[str] = None
    ipsec_policy_id: Optional[str] = None


# ============= CUSTOMIZATION =============
class TagCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    color: Optional[str] = '10b981'
    object_types: Optional[List[str]] = []


class TagUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = None
    object_types: Optional[List[str]] = None


class CustomFieldCreate(BaseSchema):
    name: str
    label: Optional[str] = ''
    type: str  # text, longtext, integer, decimal, boolean, date, datetime, url, json, select, multiselect, object, multiobject
    object_types: List[str]  # which models this applies to
    required: bool = False
    default: Optional[Any] = None
    choices: Optional[List[str]] = []
    weight: int = 100
    filter_logic: Optional[str] = 'loose'
    ui_visible: Optional[str] = 'always'
    ui_editable: Optional[str] = 'yes'


class CustomFieldUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    object_types: Optional[List[str]] = None
    required: Optional[bool] = None
    default: Optional[Any] = None
    choices: Optional[List[str]] = None
    weight: Optional[int] = None
    filter_logic: Optional[str] = None
    ui_visible: Optional[str] = None
    ui_editable: Optional[str] = None


class CustomLinkCreate(BaseSchema):
    name: str
    object_types: List[str]
    link_text: str
    link_url: str
    weight: int = 100
    group_name: Optional[str] = ''
    button_class: Optional[str] = 'default'
    new_window: bool = False
    enabled: bool = True


class CustomLinkUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    object_types: Optional[List[str]] = None
    link_text: Optional[str] = None
    link_url: Optional[str] = None
    weight: Optional[int] = None
    group_name: Optional[str] = None
    button_class: Optional[str] = None
    new_window: Optional[bool] = None
    enabled: Optional[bool] = None


class ConfigContextCreate(BaseSchema):
    name: str
    weight: int = 1000
    data: Dict[str, Any]
    is_active: bool = True
    sites: Optional[List[str]] = []
    locations: Optional[List[str]] = []
    roles: Optional[List[str]] = []
    platforms: Optional[List[str]] = []
    cluster_groups: Optional[List[str]] = []
    clusters: Optional[List[str]] = []
    tenant_groups: Optional[List[str]] = []
    tenants: Optional[List[str]] = []
    tags_match: Optional[List[str]] = []


class ConfigContextUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    weight: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    sites: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    cluster_groups: Optional[List[str]] = None
    clusters: Optional[List[str]] = None
    tenant_groups: Optional[List[str]] = None
    tenants: Optional[List[str]] = None
    tags_match: Optional[List[str]] = None


class ConfigTemplateCreate(BaseSchema):
    name: str
    template_code: str  # Jinja2 template
    environment_params: Optional[Dict[str, Any]] = {}


class ConfigTemplateUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    template_code: Optional[str] = None
    environment_params: Optional[Dict[str, Any]] = None


class WebhookCreate(BaseSchema):
    name: str
    object_types: List[str]
    type_create: bool = False
    type_update: bool = False
    type_delete: bool = False
    payload_url: str
    enabled: bool = True
    http_method: str = 'POST'
    http_content_type: str = 'application/json'
    additional_headers: Optional[str] = ''
    body_template: Optional[str] = ''
    secret: Optional[str] = ''
    ssl_verification: bool = True


class WebhookUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    object_types: Optional[List[str]] = None
    type_create: Optional[bool] = None
    type_update: Optional[bool] = None
    type_delete: Optional[bool] = None
    payload_url: Optional[str] = None
    enabled: Optional[bool] = None
    http_method: Optional[str] = None
    http_content_type: Optional[str] = None
    additional_headers: Optional[str] = None
    body_template: Optional[str] = None
    secret: Optional[str] = None
    ssl_verification: Optional[bool] = None


class SavedFilterCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    object_types: List[str]
    parameters: Dict[str, Any]
    weight: int = 100
    enabled: bool = True
    shared: bool = False


class SavedFilterUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    object_types: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    weight: Optional[int] = None
    enabled: Optional[bool] = None
    shared: Optional[bool] = None


class JournalEntryCreate(BaseSchema):
    assigned_object_type: str
    assigned_object_id: str
    kind: str = 'info'  # info, success, warning, danger
    comments: str


class JournalEntryUpdate(BaseUpdateSchema):
    kind: Optional[str] = None
    comments: Optional[str] = None


class ImageAttachmentCreate(BaseSchema):
    object_type: str
    object_id: str
    name: Optional[str] = ''
    image: str  # base64 or URL


class ImageAttachmentUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    image: Optional[str] = None
