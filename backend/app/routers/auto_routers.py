"""Auto-build CRUD routers for all simple models using the generic builder."""
from fastapi import APIRouter
from ..generic_router import build_router
from ..schemas.org_racks import (
    RegionCreate, RegionUpdate, SiteGroupCreate, SiteGroupUpdate,
    SiteCreate, SiteUpdate, LocationCreate, LocationUpdate,
    TenantGroupCreate, TenantGroupUpdate, TenantCreate, TenantUpdate,
    ContactGroupCreate, ContactGroupUpdate, ContactRoleCreate, ContactRoleUpdate,
    ContactCreate, ContactUpdate, ContactAssignmentCreate, ContactAssignmentUpdate,
    RackRoleCreate, RackRoleUpdate, RackCreate, RackUpdate,
    RackReservationCreate, RackReservationUpdate,
)
from ..schemas.devices import (
    ManufacturerCreate, ManufacturerUpdate, DeviceTypeCreate, DeviceTypeUpdate,
    ModuleTypeCreate, ModuleTypeUpdate, DeviceRoleCreate, DeviceRoleUpdate,
    PlatformCreate, PlatformUpdate, DeviceCreate, DeviceUpdate, ModuleCreate, ModuleUpdate,
    VirtualChassisCreate, VirtualChassisUpdate,
    VirtualDeviceContextCreate, VirtualDeviceContextUpdate,
    InventoryItemRoleCreate, InventoryItemRoleUpdate, InventoryItemCreate, InventoryItemUpdate,
    InterfaceCreate, InterfaceUpdate, PortCreate, PortUpdate, BayCreate, BayUpdate,
    ComponentTemplateCreate, ComponentTemplateUpdate,
)
from ..schemas.ipam import (
    RIRCreate, RIRUpdate, ASNRangeCreate, ASNRangeUpdate, ASNCreate, ASNUpdate,
    AggregateCreate, AggregateUpdate, RoleCreate, RoleUpdate,
    PrefixCreate, PrefixUpdate, IPRangeCreate, IPRangeUpdate,
    IPAddressCreate, IPAddressUpdate, VRFCreate, VRFUpdate,
    RouteTargetCreate, RouteTargetUpdate, VLANGroupCreate, VLANGroupUpdate,
    VLANCreate, VLANUpdate, ServiceTemplateCreate, ServiceTemplateUpdate,
    ServiceCreate, ServiceUpdate, FHRPGroupCreate, FHRPGroupUpdate,
    FHRPGroupAssignmentCreate, FHRPGroupAssignmentUpdate,
)
from ..schemas.extra import (
    ProviderCreate, ProviderUpdate, ProviderAccountCreate, ProviderAccountUpdate,
    ProviderNetworkCreate, ProviderNetworkUpdate, CircuitTypeCreate, CircuitTypeUpdate,
    CircuitCreate, CircuitUpdate, CircuitTerminationCreate, CircuitTerminationUpdate,
    PowerPanelCreate, PowerPanelUpdate, PowerFeedCreate, PowerFeedUpdate,
    ClusterTypeCreate, ClusterTypeUpdate, ClusterGroupCreate, ClusterGroupUpdate,
    ClusterCreate, ClusterUpdate, VirtualMachineCreate, VirtualMachineUpdate,
    VMInterfaceCreate, VMInterfaceUpdate, VirtualDiskCreate, VirtualDiskUpdate,
    WirelessLANGroupCreate, WirelessLANGroupUpdate, WirelessLANCreate, WirelessLANUpdate,
    WirelessLinkCreate, WirelessLinkUpdate,
    L2VPNCreate, L2VPNUpdate, L2VPNTerminationCreate, L2VPNTerminationUpdate,
    TunnelGroupCreate, TunnelGroupUpdate, TunnelCreate, TunnelUpdate,
    TunnelTerminationCreate, TunnelTerminationUpdate,
    IKEProposalCreate, IKEProposalUpdate, IKEPolicyCreate, IKEPolicyUpdate,
    IPSecProposalCreate, IPSecProposalUpdate, IPSecPolicyCreate, IPSecPolicyUpdate,
    IPSecProfileCreate, IPSecProfileUpdate,
    TagCreate, TagUpdate, CustomFieldCreate, CustomFieldUpdate,
    CustomLinkCreate, CustomLinkUpdate, ConfigContextCreate, ConfigContextUpdate,
    ConfigTemplateCreate, ConfigTemplateUpdate, WebhookCreate, WebhookUpdate,
    SavedFilterCreate, SavedFilterUpdate, JournalEntryCreate, JournalEntryUpdate,
    ImageAttachmentCreate, ImageAttachmentUpdate,
)


MODEL_DEFS = [
    # Organization
    ('/regions', ['Organization'], 'regions', 'region', RegionCreate, RegionUpdate),
    ('/site-groups', ['Organization'], 'site_groups', 'site-group', SiteGroupCreate, SiteGroupUpdate),
    ('/sites', ['Organization'], 'sites', 'site', SiteCreate, SiteUpdate),
    ('/locations', ['Organization'], 'locations', 'location', LocationCreate, LocationUpdate),
    ('/tenant-groups', ['Organization'], 'tenant_groups', 'tenant-group', TenantGroupCreate, TenantGroupUpdate),
    ('/tenants', ['Organization'], 'tenants', 'tenant', TenantCreate, TenantUpdate),
    ('/contact-groups', ['Organization'], 'contact_groups', 'contact-group', ContactGroupCreate, ContactGroupUpdate),
    ('/contact-roles', ['Organization'], 'contact_roles', 'contact-role', ContactRoleCreate, ContactRoleUpdate),
    ('/contacts', ['Organization'], 'contacts', 'contact', ContactCreate, ContactUpdate),
    ('/contact-assignments', ['Organization'], 'contact_assignments', 'contact-assignment', ContactAssignmentCreate, ContactAssignmentUpdate),
    # Racks
    ('/rack-roles', ['Racks'], 'rack_roles', 'rack-role', RackRoleCreate, RackRoleUpdate),
    ('/racks', ['Racks'], 'racks', 'rack', RackCreate, RackUpdate),
    ('/rack-reservations', ['Racks'], 'rack_reservations', 'rack-reservation', RackReservationCreate, RackReservationUpdate),
    # Devices
    ('/manufacturers', ['Devices'], 'manufacturers', 'manufacturer', ManufacturerCreate, ManufacturerUpdate),
    ('/device-types', ['Devices'], 'device_types', 'device-type', DeviceTypeCreate, DeviceTypeUpdate),
    ('/module-types', ['Devices'], 'module_types', 'module-type', ModuleTypeCreate, ModuleTypeUpdate),
    ('/device-roles', ['Devices'], 'device_roles', 'device-role', DeviceRoleCreate, DeviceRoleUpdate),
    ('/platforms', ['Devices'], 'platforms', 'platform', PlatformCreate, PlatformUpdate),
    ('/devices', ['Devices'], 'devices', 'device', DeviceCreate, DeviceUpdate),
    ('/modules', ['Devices'], 'modules', 'module', ModuleCreate, ModuleUpdate),
    ('/virtual-chassis', ['Devices'], 'virtual_chassis', 'virtual-chassis', VirtualChassisCreate, VirtualChassisUpdate),
    ('/virtual-device-contexts', ['Devices'], 'virtual_device_contexts', 'vdc', VirtualDeviceContextCreate, VirtualDeviceContextUpdate),
    ('/inventory-item-roles', ['Devices'], 'inventory_item_roles', 'inventory-item-role', InventoryItemRoleCreate, InventoryItemRoleUpdate),
    ('/inventory-items', ['Devices'], 'inventory_items', 'inventory-item', InventoryItemCreate, InventoryItemUpdate),
    # Components
    ('/interfaces', ['Connections'], 'interfaces', 'interface', InterfaceCreate, InterfaceUpdate),
    ('/console-ports', ['Connections'], 'console_ports', 'console-port', PortCreate, PortUpdate),
    ('/console-server-ports', ['Connections'], 'console_server_ports', 'console-server-port', PortCreate, PortUpdate),
    ('/power-ports', ['Connections'], 'power_ports', 'power-port', PortCreate, PortUpdate),
    ('/power-outlets', ['Connections'], 'power_outlets', 'power-outlet', PortCreate, PortUpdate),
    ('/front-ports', ['Connections'], 'front_ports', 'front-port', PortCreate, PortUpdate),
    ('/rear-ports', ['Connections'], 'rear_ports', 'rear-port', PortCreate, PortUpdate),
    ('/module-bays', ['Connections'], 'module_bays', 'module-bay', BayCreate, BayUpdate),
    ('/device-bays', ['Connections'], 'device_bays', 'device-bay', BayCreate, BayUpdate),
    # Component templates
    ('/interface-templates', ['Devices'], 'interface_templates', 'interface-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/console-port-templates', ['Devices'], 'console_port_templates', 'console-port-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/console-server-port-templates', ['Devices'], 'console_server_port_templates', 'console-server-port-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/power-port-templates', ['Devices'], 'power_port_templates', 'power-port-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/power-outlet-templates', ['Devices'], 'power_outlet_templates', 'power-outlet-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/front-port-templates', ['Devices'], 'front_port_templates', 'front-port-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/rear-port-templates', ['Devices'], 'rear_port_templates', 'rear-port-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/module-bay-templates', ['Devices'], 'module_bay_templates', 'module-bay-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/device-bay-templates', ['Devices'], 'device_bay_templates', 'device-bay-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    ('/inventory-item-templates', ['Devices'], 'inventory_item_templates', 'inventory-item-template', ComponentTemplateCreate, ComponentTemplateUpdate),
    # IPAM
    ('/rirs', ['IPAM'], 'rirs', 'rir', RIRCreate, RIRUpdate),
    ('/asn-ranges', ['IPAM'], 'asn_ranges', 'asn-range', ASNRangeCreate, ASNRangeUpdate),
    ('/asns', ['IPAM'], 'asns', 'asn', ASNCreate, ASNUpdate),
    ('/aggregates', ['IPAM'], 'aggregates', 'aggregate', AggregateCreate, AggregateUpdate),
    ('/roles', ['IPAM'], 'roles', 'role', RoleCreate, RoleUpdate),
    ('/prefixes', ['IPAM'], 'prefixes', 'prefix', PrefixCreate, PrefixUpdate),
    ('/ip-ranges', ['IPAM'], 'ip_ranges', 'ip-range', IPRangeCreate, IPRangeUpdate),
    ('/ip-addresses', ['IPAM'], 'ip_addresses', 'ip-address', IPAddressCreate, IPAddressUpdate),
    ('/vrfs', ['IPAM'], 'vrfs', 'vrf', VRFCreate, VRFUpdate),
    ('/route-targets', ['IPAM'], 'route_targets', 'route-target', RouteTargetCreate, RouteTargetUpdate),
    ('/vlan-groups', ['IPAM'], 'vlan_groups', 'vlan-group', VLANGroupCreate, VLANGroupUpdate),
    ('/vlans', ['IPAM'], 'vlans', 'vlan', VLANCreate, VLANUpdate),
    ('/service-templates', ['IPAM'], 'service_templates', 'service-template', ServiceTemplateCreate, ServiceTemplateUpdate),
    ('/services', ['IPAM'], 'services', 'service', ServiceCreate, ServiceUpdate),
    ('/fhrp-groups', ['IPAM'], 'fhrp_groups', 'fhrp-group', FHRPGroupCreate, FHRPGroupUpdate),
    ('/fhrp-group-assignments', ['IPAM'], 'fhrp_group_assignments', 'fhrp-assignment', FHRPGroupAssignmentCreate, FHRPGroupAssignmentUpdate),
    # Circuits
    ('/providers', ['Circuits'], 'providers', 'provider', ProviderCreate, ProviderUpdate),
    ('/provider-accounts', ['Circuits'], 'provider_accounts', 'provider-account', ProviderAccountCreate, ProviderAccountUpdate),
    ('/provider-networks', ['Circuits'], 'provider_networks', 'provider-network', ProviderNetworkCreate, ProviderNetworkUpdate),
    ('/circuit-types', ['Circuits'], 'circuit_types', 'circuit-type', CircuitTypeCreate, CircuitTypeUpdate),
    ('/circuits', ['Circuits'], 'circuits', 'circuit', CircuitCreate, CircuitUpdate),
    ('/circuit-terminations', ['Circuits'], 'circuit_terminations', 'circuit-termination', CircuitTerminationCreate, CircuitTerminationUpdate),
    # Power
    ('/power-panels', ['Power'], 'power_panels', 'power-panel', PowerPanelCreate, PowerPanelUpdate),
    ('/power-feeds', ['Power'], 'power_feeds', 'power-feed', PowerFeedCreate, PowerFeedUpdate),
    # Virtualization
    ('/cluster-types', ['Virtualization'], 'cluster_types', 'cluster-type', ClusterTypeCreate, ClusterTypeUpdate),
    ('/cluster-groups', ['Virtualization'], 'cluster_groups', 'cluster-group', ClusterGroupCreate, ClusterGroupUpdate),
    ('/clusters', ['Virtualization'], 'clusters', 'cluster', ClusterCreate, ClusterUpdate),
    ('/virtual-machines', ['Virtualization'], 'virtual_machines', 'virtual-machine', VirtualMachineCreate, VirtualMachineUpdate),
    ('/vm-interfaces', ['Virtualization'], 'vm_interfaces', 'vm-interface', VMInterfaceCreate, VMInterfaceUpdate),
    ('/virtual-disks', ['Virtualization'], 'virtual_disks', 'virtual-disk', VirtualDiskCreate, VirtualDiskUpdate),
    # Wireless
    ('/wireless-lan-groups', ['Wireless'], 'wireless_lan_groups', 'wireless-lan-group', WirelessLANGroupCreate, WirelessLANGroupUpdate),
    ('/wireless-lans', ['Wireless'], 'wireless_lans', 'wireless-lan', WirelessLANCreate, WirelessLANUpdate),
    ('/wireless-links', ['Wireless'], 'wireless_links', 'wireless-link', WirelessLinkCreate, WirelessLinkUpdate),
    # VPN/Overlay
    ('/l2vpns', ['VPN'], 'l2vpns', 'l2vpn', L2VPNCreate, L2VPNUpdate),
    ('/l2vpn-terminations', ['VPN'], 'l2vpn_terminations', 'l2vpn-termination', L2VPNTerminationCreate, L2VPNTerminationUpdate),
    ('/tunnel-groups', ['VPN'], 'tunnel_groups', 'tunnel-group', TunnelGroupCreate, TunnelGroupUpdate),
    ('/tunnels', ['VPN'], 'tunnels', 'tunnel', TunnelCreate, TunnelUpdate),
    ('/tunnel-terminations', ['VPN'], 'tunnel_terminations', 'tunnel-termination', TunnelTerminationCreate, TunnelTerminationUpdate),
    ('/ike-proposals', ['VPN'], 'ike_proposals', 'ike-proposal', IKEProposalCreate, IKEProposalUpdate),
    ('/ike-policies', ['VPN'], 'ike_policies', 'ike-policy', IKEPolicyCreate, IKEPolicyUpdate),
    ('/ipsec-proposals', ['VPN'], 'ipsec_proposals', 'ipsec-proposal', IPSecProposalCreate, IPSecProposalUpdate),
    ('/ipsec-policies', ['VPN'], 'ipsec_policies', 'ipsec-policy', IPSecPolicyCreate, IPSecPolicyUpdate),
    ('/ipsec-profiles', ['VPN'], 'ipsec_profiles', 'ipsec-profile', IPSecProfileCreate, IPSecProfileUpdate),
    # Customization
    ('/tags', ['Customization'], 'tags', 'tag', TagCreate, TagUpdate),
    ('/custom-fields', ['Customization'], 'custom_fields', 'custom-field', CustomFieldCreate, CustomFieldUpdate),
    ('/custom-links', ['Customization'], 'custom_links', 'custom-link', CustomLinkCreate, CustomLinkUpdate),
    ('/config-contexts', ['Customization'], 'config_contexts', 'config-context', ConfigContextCreate, ConfigContextUpdate),
    ('/config-templates', ['Customization'], 'config_templates', 'config-template', ConfigTemplateCreate, ConfigTemplateUpdate),
    ('/webhooks', ['Customization'], 'webhooks', 'webhook', WebhookCreate, WebhookUpdate),
    ('/saved-filters', ['Customization'], 'saved_filters', 'saved-filter', SavedFilterCreate, SavedFilterUpdate),
    ('/journal-entries', ['Customization'], 'journal_entries', 'journal-entry', JournalEntryCreate, JournalEntryUpdate),
    ('/image-attachments', ['Customization'], 'image_attachments', 'image-attachment', ImageAttachmentCreate, ImageAttachmentUpdate),
]


def build_all_routers():
    routers = []
    for prefix, tags, collection, object_type, create_schema, update_schema in MODEL_DEFS:
        slug_field = None if object_type in ('contact-assignment', 'cable', 'ip-address', 'prefix', 'aggregate', 'rack-reservation', 'circuit-termination', 'l2vpn-termination', 'tunnel-termination', 'fhrp-assignment', 'journal-entry', 'image-attachment') else 'name'
        r = build_router(prefix, tags, collection, object_type, create_schema, update_schema, slug_field=slug_field)
        routers.append(r)
    return routers
