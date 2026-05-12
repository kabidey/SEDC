# plan.md — SMIFS Enterprise Data Centre (NetBox clone)

## Status: 🟩 v1.0 DELIVERED (Phases 1–7 complete) · 🟨 Monitoring Engine (Phase 8) IN PROGRESS

## 1) Objectives
- Full-stack NetBox clone named **SMIFS Enterprise Data Centre** (React + FastAPI + MongoDB)
- ALL major NetBox modules and workflows:
  - REST CRUD for all models
  - GraphQL endpoint
  - Tags, custom fields, change log/journal, CSV import/export, bulk actions, global search
- Enterprise UI theme: **shades of green** (forest/emerald) and **SMIFS-only** branding (no Emergent)
- Network autodiscovery + mapping (Netdisco-style) via SNMP
- **Real-time analytics, monitoring, and mission-critical alerting**:
  - Check types: **ICMP, TCP, HTTP(S), SNMP, DNS**
  - Live transport: **SSE + WebSocket**
  - Alerts + notifications: **Email (SMTP), Webhook, Slack, Teams, In-app**
  - ICMP permission issues: **fallback to TCP-based latency/availability**
  - Default poll interval: **30 seconds**
- Auth direction:
  - Current: local JWT (admin/admin seed)
  - Future: JWT backed by **Orglens employee directory** once playbook is provided

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

### Phase 8 — Real-Time Analytics & Monitoring Engine (IN PROGRESS)

#### Phase 8A — Backend engine + API wiring (PARTIALLY COMPLETE)
**Already implemented (code exists, not yet fully integrated):**
- Monitoring engine modules created in `/app/backend/app/monitoring/`:
  - `engine.py` (scheduler loop + immediate run)
  - `checks.py` (ICMP/TCP/HTTP(S)/SNMP/DNS)
  - `alerts.py` (rule evaluation + state machine)
  - `pubsub.py` (in-memory pub/sub)
  - `notifiers.py` (email/webhook/slack/teams/in-app + logs)
- REST router created: `/app/backend/app/routers/monitoring_router.py`
  - Monitors CRUD + run-now + metrics
  - Alert rules CRUD
  - Alerts list + ack + resolve
  - Notification channels CRUD + test
  - Notification logs
  - Stats + SSE stream endpoint

**Next backend steps (to complete Phase 8A):**
1. Wire the router:
   - Include `monitoring_router` into `/app/backend/server.py` under `/api/monitoring/*`.
2. Start/stop the monitoring scheduler:
   - Add startup hook to `await monitoring.engine.start()`.
   - Add shutdown hook to `await monitoring.engine.stop()`.
3. Ensure persistence collections exist and are indexed reasonably:
   - `monitors`, `metric_samples`, `alert_rules`, `alerts`, `notification_channels`, `notification_logs`.
   - Add indexes on: `metric_samples.monitor_id + time`, `alerts.state + started_at`, `monitors.enabled`.
4. ICMP reliability:
   - Keep ICMP implementation, but **fallback to TCP-based latency/availability** when ICMP is blocked.
5. Live streaming transport:
   - Keep **SSE** endpoint for EventSource clients (`/api/monitoring/stream?token=...`).
   - Add **WebSocket** endpoint (parallel to SSE) for richer clients and future enhancements.
6. Validate model/field alignment with the rest of the app:
   - Confirm serialization consistency (`id`, `created`, `last_updated`) and changelog hooks.

#### Phase 8B — Frontend Monitoring / NOC UI buildout (NOT STARTED)
**New pages to implement (green theme, enterprise styling):**
1. `NOCDashboard.jsx`
   - Live tiles: monitors up/warn/crit/unknown, firing/critical alerts
   - Recent alert feed
   - Basic latency chart(s) from `metric_samples`
   - Live updates via **SSE and WebSocket** (configurable, SSE default)
2. `Monitors.jsx`
   - Table + create/edit dialog for monitor definitions
   - “Run now” action
   - Detail view panel: recent metrics and status
3. `AlertRules.jsx`
   - CRUD for rule conditions, duration, severity, and channel routing
4. `AlertHistory.jsx`
   - Filter by state/severity/monitor/rule, ack/resolve actions
5. `NotificationChannels.jsx`
   - CRUD for channel definitions: Email (SMTP), Webhook, Slack, Teams, In-app
   - Test button calling `/api/monitoring/channels/{id}/test`

**Navigation updates:**
- Add a new **Monitoring** nav group in `frontend/src/lib/resources.js`:
  - NOC Dashboard
  - Monitors
  - Alert Rules
  - Alert History
  - Notification Channels

#### Phase 8C — Testing (PENDING)
- Backend:
  - curl/script tests for:
    - create monitor → run now → metrics present
    - create rule → force failure → alert firing
    - ack/resolve alert
    - SSE stream emits metric/alert events
    - channel create/test (where possible in environment)
- Frontend:
  - Verify NOC pages render and match theme
  - Verify live updates (SSE + WebSocket)
  - Verify CRUD flows for monitors/rules/channels

## 3) Notes for next phases
- **Orglens employee directory auth**: Local JWT (admin/admin) is in place as a stand-in. When the Orglens integration playbook is provided, swap `/app/backend/app/auth.py::get_current_user` + the `/api/auth/login` endpoint to delegate to Orglens; frontend `lib/auth.jsx` will not need changes.
- **Test auth bypass**: Default admin/admin user is auto-seeded at startup. Remove the seeding in `auth.py::init_admin_user` before production deployment.
- **Realtime client robustness** (future hardening):
  - Ensure SSE/WebSocket reconnect logic doesn’t leak subscriptions/queues.
  - Add backpressure/retention controls for high-frequency metrics.

## 4) Success Criteria — Met (v1.0) + Updated (Monitoring)

### Met (v1.0)
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

### In progress / Pending (Phase 8)
- 🟨 Monitoring router mounted + engine lifecycle wired into `server.py`
- 🟨 ICMP/TCP/HTTP(S)/SNMP/DNS checks running on schedule (default 30s)
- 🟨 Alerts/rules/channels fully functional (Email/Webhook/Slack/Teams/In-app)
- 🟨 Live streaming to UI via SSE + WebSocket
- 🟨 NOC Dashboard + Monitoring admin pages implemented and added to sidebar
- 🟨 Backend + Frontend monitoring tests completed
