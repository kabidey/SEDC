# plan.md — SMIFS Enterprise Data Centre (NetBox clone)

## 1) Objectives
- Deliver a full-stack NetBox clone named **SMIFS Enterprise Data Centre** (React + FastAPI + MongoDB) with **all major NetBox modules**, REST + **GraphQL**, **JWT auth**, tags/custom-fields, audit log, CSV import/export, bulk actions, global search, and green (SMIFS) branding.
- Build in phases with a **core-flow POC first** (hardest parts: polymorphic terminations, hierarchy, bulk ops, audit log, GraphQL), then expand to full module coverage.

## 2) Implementation Steps

### Phase 1 — Core-flow POC (isolation) (must pass before full build)
**Goal:** prove the “NetBox core mechanics” in a thin slice without UI polish.
1. Websearch best practices for:
   - MongoDB modeling for hierarchical objects (materialized path) + fast prefix containment queries
   - Polymorphic relationships (cables/terminations) + content-type pattern
   - Strawberry GraphQL with FastAPI + auth context
2. Backend POC (single FastAPI service):
   - Base patterns: UUID ids, created/updated timestamps, slug fields, pagination, filtering, text search
   - Tags + Custom Fields (applied to arbitrary content-types)
   - Change log middleware: record before/after snapshots for create/update/delete
   - Polymorphic attachments: `assigned_object_type` + `assigned_object_id`
3. Minimal domain slice (enough to validate core):
   - Organization: Site → Location (hierarchy)
   - Racks: Rack + rack units occupancy
   - Devices: Manufacturer, DeviceType, DeviceRole, Device, Interface
   - Connections: Cable connecting Interface ↔ Interface with path trace
   - IPAM: VRF, Prefix, IPAddress assigned to Interface
4. APIs:
   - REST CRUD for above + bulk create/update/delete endpoints
   - CSV import/export for at least 2 models (prove pattern)
   - GraphQL read queries for above models
5. POC validation script(s):
   - Create site/location/rack/device/type/interface → cable interfaces → create prefix/IP → assign IP → verify audit log + GraphQL query works

**User stories (Phase 1)**
1. As a user, I can create a Site and nested Locations so I can model physical hierarchy.
2. As a user, I can place a Device in a Rack at a specific U position so rack occupancy is correct.
3. As a user, I can cable two Interfaces together and view the cable path so I can trace connectivity.
4. As a user, I can create a Prefix and assign an IP to an Interface so IPAM matches physical connectivity.
5. As an admin, I can view an object’s change history so I can audit who changed what.

---

### Phase 2 — V1 App Development (MVP UI + broad CRUD coverage, minimal calls)
**Goal:** stand up the full app shell + consistent CRUD UX across modules, wired to REST.
1. Repo structure + shared utilities:
   - Backend: modular routers/services/schemas, shared query builder (filter/sort/search), consistent error model
   - Frontend: app shell (sidebar/topbar/breadcrumbs), API client, form + table primitives
2. Frontend V1 UX baseline (green theme):
   - Login-free mode for dev (feature flag) to speed testing; keep auth endpoints ready
   - Lists: table w/ search, filters, sort, pagination, bulk select, CSV export/import
   - Details: overview, related objects tabs, change log tab, journal/notes tab, attachments tab
   - Create/Edit: validated forms, tag picker, custom field rendering
3. Implement module coverage (CRUD + relations) to match NetBox navigation:
   - Organization (all core objects + contacts/assignments)
   - Racks (roles/reservations/elevation view v1)
   - Devices + inventory/components/templates (v1 forms + relations)
   - Connections (cables, terminations, cable trace viewer v1)
   - IPAM (VRFs, RIRs, aggregates, prefixes, IP ranges, IP addresses, VLANs, ASNs)
   - Virtualization (clusters, VMs, VM interfaces)
   - Circuits (providers, circuits, terminations)
   - Power (panels, feeds)
   - Wireless (WLAN groups/WLANs/links)
   - VPN/Overlay (L2VPN/tunnels/terminations)
4. One round of end-to-end testing (UI + API) and fix blockers.

**User stories (Phase 2)**
1. As a user, I can navigate all NetBox modules from a consistent sidebar so I can manage DC data end-to-end.
2. As a user, I can use one consistent list/table experience across all objects so I can work quickly.
3. As a user, I can view related objects (tabs) from a detail page so I can understand dependencies.
4. As a user, I can perform bulk edit/delete so large-scale updates are manageable.
5. As a user, I can import/export CSV for supported objects so I can move data in/out.

---

### Phase 3 — Advanced platform features (complete parity items)
**Goal:** finish “NetBox platform” capabilities across all models.
1. Authentication + authorization (JWT):
   - Users, groups, permissions/roles; object-level access checks
   - Note in docs: auth designed to be swapped for Orglens directory playbook later
2. Customization:
   - Custom Links, Custom Validators, Config Contexts, Config Templates (Jinja2)
   - Saved Filters; per-user preferences
3. Automation/integration:
   - Webhooks (create/update/delete) with retries + signing secret
   - API tokens for service access
4. GraphQL: expand schema to cover all models (read-first, then mutations if required)
5. Search: global search across all major objects with faceted results
6. Second end-to-end testing round and fix regressions.

**User stories (Phase 3)**
1. As an admin, I can manage users/groups/permissions so access is controlled per role.
2. As an admin, I can add custom fields and see them appear in forms and APIs so the system adapts.
3. As a user, I can save filters so I can return to common views instantly.
4. As an integrator, I can use webhooks and API tokens so external systems stay in sync.
5. As a user, I can query GraphQL for cross-object data so reporting is easier.

---

### Phase 4 — Polish, performance, completeness checks
1. Rack elevation (drag/drop, conflict detection), prefix tree visualization, topology/cable graph refinements
2. Performance: MongoDB indexes, query tuning, caching where safe
3. Hardening: validation rules, referential integrity checks, delete protections
4. Final comprehensive testing (critical flows + edge cases) and UI consistency pass.

**User stories (Phase 4)**
1. As a user, I can visually manage rack layouts without accidental overlaps.
2. As a user, I can explore prefixes as a tree so I can understand utilization.
3. As a user, I can trace connectivity across multiple hops so troubleshooting is faster.
4. As an admin, I can rely on fast searches and lists even with large datasets.
5. As an auditor, I can export change logs and object data so compliance is supported.

## 3) Next Actions
1. Implement Phase 1 POC backend slice + validation scripts.
2. Run POC tests; do not proceed until cable polymorphism + prefix containment + audit log + GraphQL queries pass.
3. After POC pass: build Phase 2 app shell + reusable table/form components, then expand modules.

## 4) Success Criteria
- Phase 1: POC script succeeds (create hierarchy, rack/device placement, cable connect/trace, prefix/IP assign) + audit log entries + GraphQL query results correct.
- Phase 2: UI supports CRUD for all major modules with consistent list/detail/forms + working CSV import/export + bulk actions.
- Phase 3: JWT auth + permissions working; custom fields/tags everywhere; webhooks/tokens; GraphQL expanded.
- Phase 4: No critical bugs in end-to-end tests; acceptable performance; green-themed enterprise UI consistency.