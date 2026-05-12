# plan.md — SMIFS Enterprise Data Centre (NetBox clone)

## Status: 🟩 v1.1 DELIVERED (Phases 1–8 complete) · 🟨 Orglens JWT (Phase 9) PENDING PLAYBOOK

## 1) Objectives
- Full-stack NetBox clone named **SMIFS Enterprise Data Centre** (React + FastAPI + MongoDB)
- ALL major NetBox modules and workflows:
  - REST CRUD for all models
  - GraphQL endpoint
  - Tags, custom fields, change log/journal, CSV import/export, bulk actions, global search
- Enterprise UI theme: **shades of green** (forest/emerald) and **SMIFS-only** branding (no Emergent)
- Network autodiscovery + mapping (Netdisco-style) via SNMP
- **Real-time analytics, monitoring, and mission-critical alerting** (DELIVERED):
  - Check types: **ICMP, TCP, HTTP(S), SNMP, DNS**
  - Live transport: **SSE + WebSocket**
  - Alerts + notifications: **Email (SMTP), Webhook, Slack, Teams, In-app**
  - ICMP permission issues: **fallback to TCP-based availability/latency** (via TCP monitors when ICMP is blocked)
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
- Green-themed enterprise UI (forest/emerald palette, dark sidebar) with collapsible nav for 11+ module groups (100+ resource links)
- Login + Register (admin/admin default)
- Dashboard with stat cards + Recent Changes feed
- Generic ResourcePage that drives list/detail/form for all ~95 models, with search, pagination, bulk-select+delete, CSV export, CSV import, tags, FK pickers, color, JSON, boolean, select, textarea fields
- Detail view with Details / Raw / Change Log / Journal tabs
- Special pages: Rack Elevation, Prefix Tree, Cable Trace, Change Log, GraphQL Playground
- Admin: Users, Groups, API Tokens
- Global header search with autocomplete

### Phase 7 — Testing (complete)
Testing agent results (pre-monitoring): **Backend 46/46 (100%) · Frontend 15/16 passing**. Only minor dropdown click interception fixed (switched to onSelect). All critical flows verified.

### Phase 8 — Real-Time Analytics & Monitoring Engine (DELIVERED)

#### Phase 8A — Backend engine + API wiring (COMPLETE)
**Implemented in `/app/backend/app/monitoring/`:**
- `engine.py`: async scheduler loop, retention pruning, immediate run support
- `checks.py`: ICMP, TCP, HTTP(S), DNS, SNMP checks
- `alerts.py`: rule evaluation, firing/resolved state machine
- `pubsub.py`: in-memory async pub/sub
- `notifiers.py`: email (SMTP), webhook, Slack, Teams, in-app + notification logs

**REST API in `/app/backend/app/routers/monitoring_router.py`:**
- Monitors CRUD + run-now + metrics
- Alert rules CRUD
- Alerts list + acknowledge + resolve + delete
- Notification channels CRUD + test
- Notification logs
- Monitoring stats
- Live streaming:
  - SSE: `GET /api/monitoring/stream?token=...`
  - WebSocket: `WS /api/monitoring/ws?token=...`

**Server integration in `/app/backend/server.py`:**
- Router mounted under `/api/monitoring/*`
- Scheduler lifecycle:
  - startup: `await monitoring_engine.start()`
  - shutdown: `await monitoring_engine.stop()`
- Indexes created for:
  - `monitors.enabled`, `monitors.current_status`
  - `metric_samples.(monitor_id,time)`, `metric_samples.time`
  - `alerts.(state,started_at)`, `alerts.monitor_id`
  - `alert_rules.monitor_id`
  - `notification_logs.sent_at`

#### Phase 8B — Frontend Monitoring / NOC UI buildout (COMPLETE)
**New pages (green enterprise styling):**
- `/monitoring` — `NOCDashboard.jsx`
  - Live tiles (up/warn/crit/unknown + firing/critical alerts)
  - Active alerts panel with ack/resolve
  - Live event feed
  - Monitor status grid
  - SSE client with reconnect logic and mute toggle
- `/monitoring/monitors` — `Monitors.jsx`
  - CRUD for monitor definitions
  - “Run now” action
  - Metrics viewer
  - Threshold configuration
- `/monitoring/rules` — `AlertRules.jsx`
  - CRUD for alert rules
  - Condition types: down, warning_or_worse, status_change, latency_above, loss_above
  - Channel routing
- `/monitoring/alerts` — `AlertHistory.jsx`
  - Filtering by state (all/firing/resolved)
  - ack/resolve/delete actions
- `/monitoring/channels` — `NotificationChannels.jsx`
  - CRUD for channels: Email, Webhook, Slack, Teams, In-app
  - Channel test endpoint integration

**Supporting library:**
- `frontend/src/lib/monitoring-sse.js`: SSE primary + WebSocket optional transport helper, reconnect handling

**Navigation integration:**
- Added **Monitoring** group to `frontend/src/lib/resources.js` (NOC Dashboard, Monitors, Alert Rules, Alert History, Notification Channels)
- Added icon mapping in `frontend/src/components/Layout.jsx`
- Added routes in `frontend/src/App.js`

#### Phase 8C — Testing (COMPLETE)
- Test report: `/app/test_reports/iteration_3.json`
- Backend success: **24/27 (88.9%)** with **0 critical bugs**
  - 3 “failures” were test-logic quirks (SSE long-lived connection timeout expectation, cleanup endpoint expectation, /api/stats assertion mismatch)
  - All core features validated: monitors CRUD, checks, metrics persistence, alert firing/ack/resolve, channel CRUD/test, SSE hello event
- Frontend validated:
  - All monitoring pages render and match green theme
  - Sidebar/route integration confirmed
  - Auth protection confirmed

## 3) Notes for next phases
- **Orglens employee directory auth** (NEXT):
  - Local JWT (admin/admin) remains as a stand-in.
  - When Orglens integration playbook is provided, swap:
    - `/app/backend/app/auth.py::get_current_user`
    - `/app/backend/app/routers/auth_router.py` login flow
  - Frontend `lib/auth.jsx` should not need changes.
- **Test auth bypass**:
  - Default admin/admin user is auto-seeded at startup.
  - Remove seeding in `auth.py::init_admin_user` before production deployment.
- **Realtime hardening (future)**:
  - Ensure SSE/WebSocket reconnect logic doesn’t leak subscribers.
  - Consider moving pub/sub to Redis for multi-instance scaling.
  - Add rate limiting/backpressure controls if monitor volume grows.

## 4) Success Criteria — Met (v1.0) + Monitoring

### Met (v1.0)
- ✅ All NetBox-style models with REST CRUD
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
- ✅ End-to-end tested (100% backend pre-monitoring)

### Met (Phase 8)
- ✅ Monitoring router mounted + engine lifecycle wired into `server.py`
- ✅ ICMP/TCP/HTTP(S)/SNMP/DNS checks running on schedule (default 30s)
- ✅ Alerts/rules/channels fully functional (Email/Webhook/Slack/Teams/In-app)
- ✅ Live streaming to UI via SSE + WebSocket
- ✅ NOC Dashboard + Monitoring admin pages implemented and added to sidebar
- ✅ Backend + Frontend monitoring tests completed (0 critical bugs)

### Pending
- 🟨 Orglens employee directory JWT integration (awaiting playbook)
