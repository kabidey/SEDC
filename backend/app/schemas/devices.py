from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from .org_racks import BaseSchema, BaseUpdateSchema


# ============= DEVICES =============
class ManufacturerCreate(BaseSchema):
    name: str
    slug: Optional[str] = None


class ManufacturerUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None


class DeviceTypeCreate(BaseSchema):
    manufacturer_id: str
    model: str
    slug: Optional[str] = None
    default_platform_id: Optional[str] = None
    part_number: Optional[str] = ''
    u_height: float = 1.0
    is_full_depth: bool = True
    subdevice_role: Optional[str] = None  # parent, child
    airflow: Optional[str] = None  # front-to-rear, rear-to-front, etc.
    weight: Optional[float] = None
    weight_unit: Optional[str] = 'kg'
    front_image: Optional[str] = None
    rear_image: Optional[str] = None


class DeviceTypeUpdate(BaseUpdateSchema):
    manufacturer_id: Optional[str] = None
    model: Optional[str] = None
    slug: Optional[str] = None
    default_platform_id: Optional[str] = None
    part_number: Optional[str] = None
    u_height: Optional[float] = None
    is_full_depth: Optional[bool] = None
    subdevice_role: Optional[str] = None
    airflow: Optional[str] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    front_image: Optional[str] = None
    rear_image: Optional[str] = None


class ModuleTypeCreate(BaseSchema):
    manufacturer_id: str
    model: str
    part_number: Optional[str] = ''
    weight: Optional[float] = None
    weight_unit: Optional[str] = 'kg'


class ModuleTypeUpdate(BaseUpdateSchema):
    manufacturer_id: Optional[str] = None
    model: Optional[str] = None
    part_number: Optional[str] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None


class DeviceRoleCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    color: Optional[str] = '10b981'
    vm_role: bool = True


class DeviceRoleUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = None
    vm_role: Optional[bool] = None


class PlatformCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    manufacturer_id: Optional[str] = None
    napalm_driver: Optional[str] = ''
    napalm_args: Optional[Dict[str, Any]] = {}


class PlatformUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    manufacturer_id: Optional[str] = None
    napalm_driver: Optional[str] = None
    napalm_args: Optional[Dict[str, Any]] = None


class DeviceCreate(BaseSchema):
    name: Optional[str] = None
    device_type_id: str
    role_id: str
    tenant_id: Optional[str] = None
    platform_id: Optional[str] = None
    serial: Optional[str] = ''
    asset_tag: Optional[str] = ''
    site_id: str
    location_id: Optional[str] = None
    rack_id: Optional[str] = None
    position: Optional[float] = None
    face: Optional[str] = None  # front, rear
    parent_device_id: Optional[str] = None
    status: str = 'active'
    airflow: Optional[str] = None
    primary_ip4_id: Optional[str] = None
    primary_ip6_id: Optional[str] = None
    cluster_id: Optional[str] = None
    virtual_chassis_id: Optional[str] = None
    vc_position: Optional[int] = None
    vc_priority: Optional[int] = None
    config_template_id: Optional[str] = None
    oob_ip_id: Optional[str] = None
    config_context_data: Optional[Dict[str, Any]] = None
    local_context_data: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DeviceUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    device_type_id: Optional[str] = None
    role_id: Optional[str] = None
    tenant_id: Optional[str] = None
    platform_id: Optional[str] = None
    serial: Optional[str] = None
    asset_tag: Optional[str] = None
    site_id: Optional[str] = None
    location_id: Optional[str] = None
    rack_id: Optional[str] = None
    position: Optional[float] = None
    face: Optional[str] = None
    parent_device_id: Optional[str] = None
    status: Optional[str] = None
    airflow: Optional[str] = None
    primary_ip4_id: Optional[str] = None
    primary_ip6_id: Optional[str] = None
    cluster_id: Optional[str] = None
    virtual_chassis_id: Optional[str] = None
    vc_position: Optional[int] = None
    vc_priority: Optional[int] = None
    config_template_id: Optional[str] = None
    oob_ip_id: Optional[str] = None
    local_context_data: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ModuleCreate(BaseSchema):
    device_id: str
    module_bay_id: Optional[str] = None
    module_type_id: str
    status: str = 'active'
    serial: Optional[str] = ''
    asset_tag: Optional[str] = ''


class ModuleUpdate(BaseUpdateSchema):
    device_id: Optional[str] = None
    module_bay_id: Optional[str] = None
    module_type_id: Optional[str] = None
    status: Optional[str] = None
    serial: Optional[str] = None
    asset_tag: Optional[str] = None


class VirtualChassisCreate(BaseSchema):
    name: str
    domain: Optional[str] = ''
    master_id: Optional[str] = None


class VirtualChassisUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    domain: Optional[str] = None
    master_id: Optional[str] = None


class VirtualDeviceContextCreate(BaseSchema):
    name: str
    device_id: str
    identifier: Optional[str] = None
    tenant_id: Optional[str] = None
    primary_ip4_id: Optional[str] = None
    primary_ip6_id: Optional[str] = None
    status: str = 'active'


class VirtualDeviceContextUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    device_id: Optional[str] = None
    identifier: Optional[str] = None
    tenant_id: Optional[str] = None
    primary_ip4_id: Optional[str] = None
    primary_ip6_id: Optional[str] = None
    status: Optional[str] = None


class InventoryItemRoleCreate(BaseSchema):
    name: str
    slug: Optional[str] = None
    color: Optional[str] = '10b981'


class InventoryItemRoleUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = None


class InventoryItemCreate(BaseSchema):
    device_id: str
    parent_id: Optional[str] = None
    name: str
    label: Optional[str] = ''
    role_id: Optional[str] = None
    manufacturer_id: Optional[str] = None
    part_id: Optional[str] = ''
    serial: Optional[str] = ''
    asset_tag: Optional[str] = ''
    discovered: bool = False
    component_type: Optional[str] = None
    component_id: Optional[str] = None


class InventoryItemUpdate(BaseUpdateSchema):
    device_id: Optional[str] = None
    parent_id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    role_id: Optional[str] = None
    manufacturer_id: Optional[str] = None
    part_id: Optional[str] = None
    serial: Optional[str] = None
    asset_tag: Optional[str] = None
    discovered: Optional[bool] = None
    component_type: Optional[str] = None
    component_id: Optional[str] = None


# ============= COMPONENTS (Interfaces, Ports, Bays, etc.) =============
class InterfaceCreate(BaseSchema):
    device_id: Optional[str] = None
    virtual_machine_id: Optional[str] = None
    module_id: Optional[str] = None
    name: str
    label: Optional[str] = ''
    type: str = '1000base-t'  # 1000base-t, 10gbase-t, 10gbase-x-sfpp, 25gbase-x-sfp28, 40gbase-x-qsfpp, 100gbase-x-qsfp28, virtual, lag, etc.
    enabled: bool = True
    parent_id: Optional[str] = None
    bridge_id: Optional[str] = None
    lag_id: Optional[str] = None
    mtu: Optional[int] = None
    mac_address: Optional[str] = None
    speed: Optional[int] = None
    duplex: Optional[str] = None
    wwn: Optional[str] = None
    mgmt_only: bool = False
    mode: Optional[str] = None  # access, tagged, tagged-all
    rf_role: Optional[str] = None
    rf_channel: Optional[str] = None
    poe_mode: Optional[str] = None
    poe_type: Optional[str] = None
    tx_power: Optional[int] = None
    untagged_vlan_id: Optional[str] = None
    tagged_vlans: Optional[List[str]] = []
    vrf_id: Optional[str] = None
    primary_mac_address: Optional[str] = None


class InterfaceUpdate(BaseUpdateSchema):
    device_id: Optional[str] = None
    virtual_machine_id: Optional[str] = None
    module_id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    enabled: Optional[bool] = None
    parent_id: Optional[str] = None
    bridge_id: Optional[str] = None
    lag_id: Optional[str] = None
    mtu: Optional[int] = None
    mac_address: Optional[str] = None
    speed: Optional[int] = None
    duplex: Optional[str] = None
    wwn: Optional[str] = None
    mgmt_only: Optional[bool] = None
    mode: Optional[str] = None
    rf_role: Optional[str] = None
    rf_channel: Optional[str] = None
    poe_mode: Optional[str] = None
    poe_type: Optional[str] = None
    tx_power: Optional[int] = None
    untagged_vlan_id: Optional[str] = None
    tagged_vlans: Optional[List[str]] = None
    vrf_id: Optional[str] = None


class PortCreate(BaseSchema):
    """Generic schema for console-port, console-server-port, power-port, power-outlet, front-port, rear-port."""
    device_id: str
    module_id: Optional[str] = None
    name: str
    label: Optional[str] = ''
    type: Optional[str] = None
    # power
    maximum_draw: Optional[int] = None
    allocated_draw: Optional[int] = None
    feed_leg: Optional[str] = None
    power_port_id: Optional[str] = None  # for outlets
    # front/rear ports
    rear_port_id: Optional[str] = None
    rear_port_position: Optional[int] = 1
    positions: Optional[int] = 1
    color: Optional[str] = None
    speed: Optional[int] = None


class PortUpdate(BaseUpdateSchema):
    device_id: Optional[str] = None
    module_id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    maximum_draw: Optional[int] = None
    allocated_draw: Optional[int] = None
    feed_leg: Optional[str] = None
    power_port_id: Optional[str] = None
    rear_port_id: Optional[str] = None
    rear_port_position: Optional[int] = None
    positions: Optional[int] = None
    color: Optional[str] = None
    speed: Optional[int] = None


class BayCreate(BaseSchema):
    """Module bay or device bay."""
    device_id: str
    name: str
    label: Optional[str] = ''
    position: Optional[str] = ''
    installed_device_id: Optional[str] = None
    installed_module_id: Optional[str] = None


class BayUpdate(BaseUpdateSchema):
    device_id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    position: Optional[str] = None
    installed_device_id: Optional[str] = None
    installed_module_id: Optional[str] = None


# ============= TEMPLATES (on DeviceType / ModuleType) =============
class ComponentTemplateCreate(BaseSchema):
    device_type_id: Optional[str] = None
    module_type_id: Optional[str] = None
    name: str
    label: Optional[str] = ''
    type: Optional[str] = None
    enabled: Optional[bool] = True
    mgmt_only: Optional[bool] = False
    maximum_draw: Optional[int] = None
    allocated_draw: Optional[int] = None
    feed_leg: Optional[str] = None
    poe_mode: Optional[str] = None
    poe_type: Optional[str] = None
    rear_port_id: Optional[str] = None
    rear_port_position: Optional[int] = 1
    positions: Optional[int] = 1
    color: Optional[str] = None
    role_id: Optional[str] = None


class ComponentTemplateUpdate(BaseUpdateSchema):
    device_type_id: Optional[str] = None
    module_type_id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    enabled: Optional[bool] = None
    mgmt_only: Optional[bool] = None
    maximum_draw: Optional[int] = None
    allocated_draw: Optional[int] = None
    feed_leg: Optional[str] = None
    poe_mode: Optional[str] = None
    poe_type: Optional[str] = None
    rear_port_id: Optional[str] = None
    rear_port_position: Optional[int] = None
    positions: Optional[int] = None
    color: Optional[str] = None
    role_id: Optional[str] = None


# ============= CABLES =============
class CableTermination(BaseModel):
    object_type: str  # 'interface', 'console-port', 'power-port', 'power-outlet', 'front-port', 'rear-port', 'circuit-termination', 'power-feed'
    object_id: str


class CableCreate(BaseSchema):
    a_terminations: List[CableTermination]
    b_terminations: List[CableTermination]
    type: Optional[str] = None  # cat3, cat5, cat5e, cat6, cat6a, cat7, cat7a, cat8, dac-active, dac-passive, mrj21-trunk, coaxial, mmf-om1..om5, smf-os1, smf-os2, aoc, power
    status: str = 'connected'
    label: Optional[str] = ''
    color: Optional[str] = None
    length: Optional[float] = None
    length_unit: Optional[str] = 'm'
    tenant_id: Optional[str] = None


class CableUpdate(BaseUpdateSchema):
    a_terminations: Optional[List[CableTermination]] = None
    b_terminations: Optional[List[CableTermination]] = None
    type: Optional[str] = None
    status: Optional[str] = None
    label: Optional[str] = None
    color: Optional[str] = None
    length: Optional[float] = None
    length_unit: Optional[str] = None
    tenant_id: Optional[str] = None
