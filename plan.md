# plan.md — SMIFS Enterprise Data Centre (NetBox clone)

## Status: ✅ v1.0 DELIVERED (Phases 1–7 complete)

## 1) Objectives
- Full-stack NetBox clone named **SMIFS Enterprise Data Centre** (React + FastAPI + MongoDB)
- ALL major NetBox modules, REST + GraphQL, JWT auth, tags, custom fields, audit log, CSV import/export, bulk actions, global search
- Green (SMIFS) branding (forest/emerald)

## 2) Outcome by Phase

### Phase 1 — POC (skipped intentionally)
Skipped because the core mechanics are well-proven CRUD over MongoDB. Polymorphic terminations + hierarchy + change log were folded directly into the Phase 2 implementation and validated by the testing agent at the end (100% backend pass).

### Phase 2–5 — Backend (complete)
**95 fully-wired REST routers** with CRUD + bulk_delete + CSV import + CSV export, plus specialized endpoints:
- Auth (JWT, default admin/admin, register, /me)
- Users / Groups / API Tokens (admin)
- Organization: Region, SiteGroup, Site, Location, TenantGroup, Tenant, ContactGroup, ContactRole, Contact, ContactAssignment
- Racks: RackRole, Rack, RackReservation, rack-tools/elevation
- Devices: Manufacturer, DeviceType, ModuleType, DeviceRole, Platform, Device, Module, VirtualChassis, VirtualDeviceContext, InventoryItem(+Role) and all 10 component templates
- Connections: Interface, Console/ConsoleServer/Power/Power-outlet/Front/Rear Ports, Module/Device Bays, Cable (polymorphic terminations), cable trace
- IPAM: RIR, ASN, ASNRange, Aggregate, Role, Prefix, IPRange, IPAddress, VRF, RouteTarget, VLAN, VLANGroup, Service(+Template), FHRPGroup, prefix-tools tree + available-IPs
- Circuits: Provider, ProviderAccount, ProviderNetwork, CircuitType, Circuit, CircuitTermination
- Power: PowerPanel, PowerFeed
- Virtualization: ClusterType, ClusterGroup, Cluster, VM, VMInterface, VirtualDisk
- Wireless: WirelessLANGroup, WirelessLAN, WirelessLink
- VPN/Overlay: L2VPN(+Termination), TunnelGroup, Tunnel(+Termination), IKEProposal/Policy, IPSecProposal/Policy/Profile
- Customization: Tags, CustomFields, CustomLinks, ConfigContexts, ConfigTemplates, Webhooks, SavedFilters, JournalEntries, ImageAttachments, ChangeLog
- Cross-cutting: /api/search (global), /api/stats (dashboard), /api/graphql (Strawberry)

### Phase 6 — Frontend (complete)
- Green-themed enterprise UI (forest/emerald palette, dark sidebar) with collapsible nav for 11 module groups (100+ resource links)
- Login + Register (admin/admin default)
- Dashboard with 16 stat cards + Recent Changes feed
- Generic ResourcePage that drives list/detail/form for all 95 models, with search, pagination, bulk-select+delete, CSV export, CSV import, tags, FK pickers, color, JSON, boolean, select, textarea fields
- Detail view with Details / Raw / Change Log / Journal tabs
- Special pages: Rack Elevation, Prefix Tree, Cable Trace, Change Log, GraphQL Playground
- Admin: Users, Groups, API Tokens
- Global header search with autocomplete

### Phase 7 — Testing (complete)
Testing agent results: **Backend 46/46 (100%) · Frontend 15/16 passing**. Only minor dropdown click interception fixed (switched to onSelect). All critical flows verified.

## 3) Notes for next phases
- **Orglens employee directory auth**: Local JWT (admin/admin) is in place as a stand-in. When the Orglens integration playbook is provided, swap `/app/backend/app/auth.py::get_current_user` + the `/api/auth/login` endpoint to delegate to Orglens; frontend `lib/auth.jsx` will not need changes.
- **Test auth bypass**: Default admin/admin user is auto-seeded at startup. Remove the seeding in `auth.py::init_admin_user` before production deployment.

## 4) Success Criteria — Met
- ✅ All 95 NetBox-style models with REST CRUD
- ✅ GraphQL endpoint live at `/api/graphql`
- ✅ Tags, custom fields, change log on every model
- ✅ CSV import / export on every model
- ✅ Bulk delete on every model
- ✅ Polymorphic cables + cable trace
- ✅ Hierarchical prefix tree
- ✅ Rack elevation visualizer
- ✅ Global search across all major collections
- ✅ Dashboard with live counters
- ✅ Green enterprise theme
- ✅ JWT auth (Orglens-ready)
- ✅ End-to-end tested (100% backend, 94% frontend with 1 minor fix applied)
