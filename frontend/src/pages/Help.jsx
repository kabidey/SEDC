import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  BookOpen, Building2, Server, Columns3, Cable, Globe, Route, Zap, Box, Wifi,
  Shield, Settings2, ShieldCheck, Radar, Code2, Users, ArrowRight, ArrowLeft,
  Info, AlertTriangle, Lightbulb, CheckCircle2, Sparkles, Search, FileText,
  Tag as TagIcon, Webhook, Network, KeyRound, Database, Map as MapIcon,
} from 'lucide-react';

// ========================================================================
// CHAPTERS — content registry
// ========================================================================

const CHAPTERS = [
  { id: 'welcome', title: 'Welcome', icon: Sparkles, group: 'Intro' },
  { id: 'first-login', title: 'First Login', icon: KeyRound, group: 'Intro' },
  { id: 'mental-model', title: 'The Mental Model', icon: MapIcon, group: 'Intro' },
  { id: 'quick-start', title: '5-Minute Quick Start', icon: CheckCircle2, group: 'Intro' },

  { id: 'organization', title: 'Step 1 · Organization', icon: Building2, group: 'Build Your DC' },
  { id: 'racks', title: 'Step 2 · Racks', icon: Columns3, group: 'Build Your DC' },
  { id: 'devices', title: 'Step 3 · Devices', icon: Server, group: 'Build Your DC' },
  { id: 'connections', title: 'Step 4 · Cabling', icon: Cable, group: 'Build Your DC' },

  { id: 'ipam', title: 'Step 5 · IPAM', icon: Globe, group: 'Networking' },
  { id: 'circuits', title: 'Step 6 · Circuits', icon: Route, group: 'Networking' },
  { id: 'power', title: 'Step 7 · Power', icon: Zap, group: 'Networking' },
  { id: 'virt', title: 'Step 8 · Virtualization', icon: Box, group: 'Networking' },
  { id: 'wireless-vpn', title: 'Step 9 · Wireless & VPN', icon: Wifi, group: 'Networking' },

  { id: 'discovery', title: 'Step 10 · Autodiscovery', icon: Radar, group: 'Automation' },
  { id: 'customization', title: 'Customization', icon: Settings2, group: 'Automation' },
  { id: 'audit-search', title: 'Audit & Search', icon: Search, group: 'Automation' },
  { id: 'csv', title: 'CSV Import / Export', icon: FileText, group: 'Automation' },
  { id: 'api', title: 'REST API & GraphQL', icon: Code2, group: 'Automation' },

  { id: 'admin', title: 'Admin & Security', icon: ShieldCheck, group: 'Operations' },
  { id: 'patterns', title: 'Architecture Patterns', icon: Network, group: 'Operations' },
];

// ========================================================================
// Reusable bits
// ========================================================================

const H1 = ({ children, icon: Icon }) => (
  <div className="flex items-center gap-3 mb-3">
    {Icon && <div className="w-10 h-10 rounded-lg bg-emerald-600 text-white flex items-center justify-center"><Icon size={20} /></div>}
    <h1 className="text-3xl font-bold tracking-tight">{children}</h1>
  </div>
);
const H2 = ({ children }) => <h2 className="text-xl font-bold mt-8 mb-3 text-emerald-800 border-b border-emerald-100 pb-1">{children}</h2>;
const H3 = ({ children }) => <h3 className="text-base font-semibold mt-5 mb-2 text-foreground">{children}</h3>;
const P = ({ children }) => <p className="text-[15px] leading-relaxed text-foreground/90 mb-3">{children}</p>;
const Lead = ({ children }) => <p className="text-base leading-relaxed text-muted-foreground mb-4">{children}</p>;
const UL = ({ children }) => <ul className="list-disc pl-6 space-y-1 text-[15px] text-foreground/90 mb-3">{children}</ul>;
const OL = ({ children }) => <ol className="list-decimal pl-6 space-y-1.5 text-[15px] text-foreground/90 mb-3 marker:font-semibold marker:text-emerald-700">{children}</ol>;
const KBD = ({ children }) => <code className="px-1.5 py-0.5 rounded bg-muted text-emerald-800 text-[12px] font-mono">{children}</code>;
const Code = ({ children }) => <pre className="bg-slate-900 text-emerald-100 text-xs p-3 rounded-md overflow-x-auto my-3 font-mono leading-relaxed">{children}</pre>;
const Tip = ({ children, tone = 'info' }) => {
  const map = {
    info: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-900', Icon: Info, label: 'Tip' },
    warn: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-900', Icon: AlertTriangle, label: 'Heads up' },
    idea: { bg: 'bg-sky-50', border: 'border-sky-200', text: 'text-sky-900', Icon: Lightbulb, label: 'Good to know' },
    do: { bg: 'bg-violet-50', border: 'border-violet-200', text: 'text-violet-900', Icon: CheckCircle2, label: 'Do this' },
  }[tone];
  const Icon = map.Icon;
  return (
    <div className={`flex gap-3 p-3 rounded-md border ${map.bg} ${map.border} ${map.text} my-3`}>
      <Icon size={18} className="shrink-0 mt-0.5" />
      <div className="text-sm leading-relaxed"><strong className="font-semibold mr-1">{map.label}:</strong>{children}</div>
    </div>
  );
};
const Step = ({ n, children }) => (
  <div className="flex gap-3 mb-3">
    <div className="w-7 h-7 rounded-full bg-emerald-600 text-white text-sm font-bold flex items-center justify-center shrink-0">{n}</div>
    <div className="flex-1 pt-0.5 text-[15px] leading-relaxed">{children}</div>
  </div>
);
const GoTo = ({ to, label }) => (
  <Link to={to} className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-xs font-medium hover:bg-emerald-200">
    {label} <ArrowRight size={11} />
  </Link>
);
const DiagramBox = ({ children }) => (
  <pre className="bg-emerald-50 text-emerald-900 p-3 rounded border border-emerald-200 text-[11px] leading-snug overflow-x-auto font-mono my-3">{children}</pre>
);

// ========================================================================
// Chapter bodies
// ========================================================================

const Bodies = {
  welcome: () => (
    <div>
      <H1 icon={Sparkles}>Welcome to SMIFS Enterprise Data Centre</H1>
      <Lead>
        SMIFS EDC is a single source of truth for everything in your network and data‑centre:
        sites, racks, devices, cables, IP addresses, VLANs, circuits, power, virtual machines,
        wireless, VPNs, and more. Think of it as a giant filing cabinet where every drawer is
        labelled and connected to every other drawer.
      </Lead>
      <H2>Who this is for</H2>
      <UL>
        <li><strong>Network engineers</strong> who want to stop tracking infrastructure in spreadsheets.</li>
        <li><strong>Data‑centre operators</strong> who need to know what is in each rack and how it is cabled.</li>
        <li><strong>IT/Ops teams</strong> who want an automated, audited inventory.</li>
        <li><strong>Developers</strong> who need a REST or GraphQL API to programmatically read/write the inventory.</li>
      </UL>
      <H2>What you will learn in this tutorial</H2>
      <OL>
        <li>The “mental model” — how all the pieces fit together.</li>
        <li>How to build your first <em>Site</em>, <em>Rack</em> and <em>Device</em>, step by step.</li>
        <li>How to plan and assign IP addresses, VLANs, and VRFs.</li>
        <li>How to connect interfaces with cables and trace them.</li>
        <li>How to discover real devices automatically with SNMP / Netdisco.</li>
        <li>How to extend the schema (tags, custom fields, webhooks).</li>
        <li>How to talk to SMIFS programmatically via REST and GraphQL.</li>
      </OL>
      <Tip tone="do">Read the chapters in order the first time. Then come back to use this Help as a reference.</Tip>
      <H2>The golden rule</H2>
      <P>
        Always build from <em>big</em> to <em>small</em>: Region → Site → Location → Rack → Device → Interface → IP. If you try to create
        a Device before its Site exists, you will get an error. That is by design — it prevents orphan records.
      </P>
    </div>
  ),

  'first-login': () => (
    <div>
      <H1 icon={KeyRound}>First Login</H1>
      <Lead>This part takes 90 seconds.</Lead>
      <Step n={1}>Open the app and click <KBD>Sign in</KBD>.</Step>
      <Step n={2}>Use the default credentials — username <KBD>admin</KBD>, password <KBD>admin</KBD>.</Step>
      <Step n={3}>You land on the <strong>Dashboard</strong>. It will be empty (we did not seed demo data). That is correct.</Step>
      <Step n={4}>Click your avatar (top‑right) → <strong>Admin</strong> to open the User Management page. Create a personal admin account for yourself, then sign out and sign back in.</Step>
      <Step n={5}>(Optional but recommended) From the avatar menu, open <strong>API Tokens</strong> and generate one. Keep it safe — you will use it later for API calls.</Step>
      <Tip tone="warn">
        The default <KBD>admin / admin</KBD> account exists only to bootstrap. Disable it (or change its password)
        before exposing SMIFS to a wider audience. Admin → Users → set <em>is_active = false</em> for <code>admin</code>.
      </Tip>
      <H2>The layout you will use</H2>
      <UL>
        <li><strong>Left sidebar</strong> — collapsible groups for every module (Organization, Devices, Racks, Connections, IPAM, …).</li>
        <li><strong>Top bar</strong> — global search (try it: it searches across sites, devices, IPs, prefixes, VLANs, cables, contacts).</li>
        <li><strong>Content area</strong> — list / detail / form views, identical pattern for every resource.</li>
      </UL>
    </div>
  ),

  'mental-model': () => (
    <div>
      <H1 icon={MapIcon}>The Mental Model — how everything connects</H1>
      <Lead>
        Before you click anything, look at the picture below. Every box is a thing you can create
        in SMIFS, and every arrow is a relationship. Once you understand this, the rest is just data entry.
      </Lead>
      <H2>Physical world</H2>
      <DiagramBox>{`
Region (Asia)
  └── Site Group (DC East)
        └── Site (Kolkata DC)
              └── Location (Floor 3 / Cage A)
                    └── Rack (RACK‑01)
                          └── Device (core‑sw‑01)
                                ├── Interface (Ethernet1/1) ──┐
                                ├── Power Port (PSU1)         │ cable
                                ├── Console Port (CON0)       │
                                └── Module Bay → Module       │
                                                              │
                  Device (core‑sw‑02) ── Interface (Eth1/1) ──┘
`}</DiagramBox>
      <H2>Logical world (IPs, VLANs)</H2>
      <DiagramBox>{`
RIR (APNIC) ── Aggregate (10.0.0.0/8)
                  ├── Prefix container 10.0.0.0/16  (status=container)
                  │     ├── Prefix 10.0.10.0/24  (status=active, role=mgmt)
                  │     │     └── IP 10.0.10.5/24  ──▶  assigned to Interface (core‑sw‑01 / Eth1/1)
                  │     └── Prefix 10.0.20.0/24  (vlan=20, role=user)
                  └── VRF (CUSTOMER‑A)  +  Route Targets

VLAN Group (Kolkata DC) ── VLAN 10 (Mgmt), 20 (User), 30 (Voice)
`}</DiagramBox>
      <H2>People & ownership</H2>
      <DiagramBox>{`
Tenant Group (Enterprises) ── Tenant (SMIFS Securities)
                                  ▲       ▲
                                  │       │ tenant_id link
                                Site    Device    Prefix    VRF   Circuit
`}</DiagramBox>
      <H2>Three rules to remember</H2>
      <OL>
        <li><strong>Templates first, instances later.</strong> Create a <em>Device Type</em> (e.g., Cisco Catalyst 9300) <em>before</em> you instantiate a Device from it.</li>
        <li><strong>Roles and Statuses are everywhere.</strong> Almost every record has a <em>status</em> (planned / active / decommissioning) and a <em>role</em>. Use them — they unlock filtering.</li>
        <li><strong>IDs are stable, slugs are pretty.</strong> Every object has an opaque <KBD>id</KBD> (UUID) and most also have a <KBD>slug</KBD> (URL‑friendly name). Cross‑references always use the id.</li>
      </OL>
    </div>
  ),

  'quick-start': () => (
    <div>
      <H1 icon={CheckCircle2}>5‑Minute Quick Start</H1>
      <Lead>Click through these in order. At the end you will have one Site, one Rack, one Device, one Cable, one Prefix and one IP — a complete miniature inventory.</Lead>
      <Step n={1}>Open <GoTo to="/sites" label="Sites" /> → click <strong>Add Site</strong> → name <KBD>HQ</KBD>, status <em>active</em> → <strong>Save</strong>.</Step>
      <Step n={2}>Open <GoTo to="/locations" label="Locations" /> → <strong>Add Location</strong> → name <KBD>Server Room</KBD>, pick site <KBD>HQ</KBD> → <strong>Save</strong>.</Step>
      <Step n={3}>Open <GoTo to="/rack-roles" label="Rack Roles" /> → add <KBD>General</KBD>. Then <GoTo to="/racks" label="Racks" /> → <strong>Add Rack</strong> → name <KBD>R1</KBD>, site <KBD>HQ</KBD>, U height <KBD>42</KBD> → <strong>Save</strong>.</Step>
      <Step n={4}>Open <GoTo to="/manufacturers" label="Manufacturers" /> → add <KBD>Cisco</KBD>. Then <GoTo to="/device-types" label="Device Types" /> → add Manufacturer=Cisco, Model=<KBD>Catalyst‑9300</KBD>, U height=<KBD>1</KBD>.</Step>
      <Step n={5}>Open <GoTo to="/device-roles" label="Device Roles" /> → add <KBD>Switch</KBD>. Then <GoTo to="/devices" label="Devices" /> → <strong>Add Device</strong> → name <KBD>sw‑01</KBD>, device type <KBD>Catalyst‑9300</KBD>, role <KBD>Switch</KBD>, site <KBD>HQ</KBD>, rack <KBD>R1</KBD>, position <KBD>1</KBD>, face <KBD>front</KBD> → <strong>Save</strong>. Repeat for <KBD>sw‑02</KBD> at position 2.</Step>
      <Step n={6}>Open <GoTo to="/interfaces" label="Interfaces" /> → add two interfaces, one for <KBD>sw‑01</KBD> named <KBD>Eth1/1</KBD>, one for <KBD>sw‑02</KBD> named <KBD>Eth1/1</KBD>.</Step>
      <Step n={7}>Open <GoTo to="/cables" label="Cables" /> → <strong>Add Cable</strong> → paste this JSON in both terminations and adjust the two interface ids (copy them from the interface detail pages):
        <Code>{`a_terminations:
[{"object_type":"interface","object_id":"<sw-01 Eth1/1 id>"}]

b_terminations:
[{"object_type":"interface","object_id":"<sw-02 Eth1/1 id>"}]`}</Code>
      </Step>
      <Step n={8}>Open <GoTo to="/aggregates" label="Aggregates" /> after adding a <GoTo to="/rirs" label="RIR" /> (e.g., <KBD>APNIC</KBD>): create aggregate <KBD>10.0.0.0/8</KBD>.</Step>
      <Step n={9}>Open <GoTo to="/prefixes" label="Prefixes" /> → add <KBD>10.0.0.0/24</KBD>, status active.</Step>
      <Step n={10}>Open <GoTo to="/ip-addresses" label="IP Addresses" /> → add <KBD>10.0.0.1/24</KBD>, assigned_object_type <KBD>interface</KBD>, assigned_object_id = <KBD>sw‑01 Eth1/1 id</KBD>.</Step>
      <Step n={11}>Visit <GoTo to="/rack-elevation" label="Rack Elevation" />, pick <KBD>R1</KBD> — you should see sw‑01 and sw‑02. Visit <GoTo to="/prefix-tree" label="Prefix Tree" /> to see your prefix.</Step>
      <Tip tone="do">Congratulations — you just modelled your first piece of infrastructure. Everything else in this guide is just more of the same pattern: <em>template → instance → relate → visualise</em>.</Tip>
    </div>
  ),

  organization: () => (
    <div>
      <H1 icon={Building2}>Step 1 · Organization</H1>
      <Lead>This is the geographic / corporate hierarchy. Get it right once and never touch it again.</Lead>
      <H2>What each thing means</H2>
      <UL>
        <li><strong>Region</strong> — a geographic area, optionally nested (Asia → India → West‑Bengal). Used for filtering reports.</li>
        <li><strong>Site Group</strong> — a logical grouping (e.g., “Edge POPs”, “Cloud Regions”). Independent of geography.</li>
        <li><strong>Site</strong> — a physical location: a campus, building, or DC.</li>
        <li><strong>Location</strong> — a sub‑area inside a Site (a floor, a cage, a closet). Locations can nest.</li>
        <li><strong>Tenant Group / Tenant</strong> — “who owns this”. A bank, a customer, an internal BU. Tag anything with a Tenant for chargeback / multi‑tenant reporting.</li>
        <li><strong>Contact Group / Contact / Contact Role</strong> — humans (the NOC engineer, the landlord, the vendor SE). Assign them to <em>any</em> object via <em>Contact Assignment</em>.</li>
      </UL>
      <H2>Recommended build order</H2>
      <OL>
        <li>Create your <strong>Regions</strong> (top‑down).</li>
        <li>Create <strong>Site Groups</strong> if you want one (optional).</li>
        <li>Create your <strong>Sites</strong>. Each Site must have a <em>name</em> and <em>status</em>. <KBD>active</KBD> is the usual default.</li>
        <li>For each Site, create one or more <strong>Locations</strong> describing internal layout.</li>
        <li>Create your <strong>Tenants</strong> if you have customers/departments. You can also do this later.</li>
        <li>Add <strong>Contacts</strong> with their roles (e.g., “Smart‑hands”, “Account Manager”). You will assign them to devices/sites in later steps.</li>
      </OL>
      <H3>Example</H3>
      <Code>{`Region        : Asia
Site Group    : Production DCs
Site          : Kolkata-DC1   (status=active, region=Asia, group=Production DCs)
Locations     : Floor-3, Floor-3/Cage-A, Floor-3/Cage-B
Tenants       : SMIFS-Securities, SMIFS-Wealth, External-Hosting
Contact roles : NOC, On-call, Landlord
Contact       : "Anil Sharma"  role=NOC  phone=+91...`}</Code>
      <Tip tone="idea">
        Don't over‑model. If you only have one country, you don't need Regions. If you only have one company,
        you don't need Tenants. Add hierarchy only when it gives you filtering / reporting value.
      </Tip>
    </div>
  ),

  racks: () => (
    <div>
      <H1 icon={Columns3}>Step 2 · Racks</H1>
      <Lead>Racks live inside a Site (optionally inside a Location). Every Device that occupies a rack will reference one of these.</Lead>
      <H2>Build order</H2>
      <OL>
        <li>Create <strong>Rack Roles</strong> (e.g., <KBD>Network</KBD>, <KBD>Compute</KBD>, <KBD>Storage</KBD>) with distinct colours so the rack‑elevation view is easy to read.</li>
        <li>Create <strong>Racks</strong>. Required fields: <em>name</em>, <em>site</em>, <em>U height</em> (default 42). Recommended: type (<KBD>4‑post‑cabinet</KBD>), width (19″), serial, asset tag.</li>
        <li>(Optional) <strong>Rack Reservations</strong> — reserve units 10‑12 for "future expansion".</li>
      </OL>
      <H2>The rack elevation view</H2>
      <P>
        After adding devices (next chapter), open <GoTo to="/rack-elevation" label="Rack Elevation" /> and pick a rack from the dropdown.
        You will see units numbered top‑down with each device occupying its U positions. Click a device row to jump straight into it.
      </P>
      <Tip tone="warn">
        Set the rack's <em>U height</em> correctly the first time. Shrinking it later when devices already occupy higher
        units will throw those devices off the visualisation.
      </Tip>
      <H3>Naming convention that works</H3>
      <UL>
        <li>Racks: <KBD>&lt;site&gt;-&lt;row&gt;-&lt;num&gt;</KBD> → <KBD>KOL-A-01</KBD></li>
        <li>Use rack roles + tenants to colour‑code who owns what.</li>
      </UL>
    </div>
  ),

  devices: () => (
    <div>
      <H1 icon={Server}>Step 3 · Devices</H1>
      <Lead>This is where most of the work happens. There is a 4‑step template → instance pattern: <strong>Manufacturer → Device Type → Device Role → Device</strong>.</Lead>
      <H2>3a · Manufacturers</H2>
      <P>Just a name (Cisco, Juniper, Arista, Dell, HPE, …). Used to group device types.</P>

      <H2>3b · Device Types</H2>
      <P>A Device Type is a <em>model spec</em> (e.g., "Catalyst 9300‑48P"). It does NOT live in a rack — only Devices do. Required: <em>manufacturer</em>, <em>model</em>, <em>U height</em>.</P>
      <UL>
        <li><em>Sub‑device role</em> — only for chassis with line‑cards. Set to <KBD>parent</KBD> for a chassis, <KBD>child</KBD> for a line‑card.</li>
        <li><em>Airflow</em> — front‑to‑rear / rear‑to‑front. Useful for hot‑aisle/cold‑aisle planning.</li>
        <li><em>Is full depth</em> — false for half‑depth devices (some firewalls).</li>
      </UL>
      <Tip tone="idea">
        Build a <strong>library</strong> of Device Types once and reuse them. Adding ten Catalyst 9300s later is then just
        "duplicate the Device" not "fill in another 15 fields".
      </Tip>

      <H2>3c · Device Roles</H2>
      <P>A semantic label: Core Switch, Distribution Switch, Access Switch, Firewall, Router, Load Balancer, Server. Choose a colour — it tints the rack elevation.</P>

      <H2>3d · Platforms (optional)</H2>
      <P>The OS/firmware family: Cisco IOS, IOS‑XE, NX‑OS, Junos, EOS, Linux. Pair it with a NAPALM driver if you plan to automate config pulls.</P>

      <H2>3e · Devices (the instance)</H2>
      <OL>
        <li>Pick a unique <strong>name</strong> (e.g., <KBD>kol-core-sw-01</KBD>).</li>
        <li>Choose <strong>Device Type</strong>, <strong>Role</strong>, and optionally <strong>Platform</strong>.</li>
        <li>Place it: <strong>Site</strong> (required), <strong>Location</strong>, <strong>Rack</strong>, <strong>Position</strong>, <strong>Face</strong> (front/rear).</li>
        <li>Add <strong>serial</strong> and <strong>asset tag</strong> for finance/audit reasons.</li>
        <li>Set <strong>Status</strong> = <em>planned</em> while you build, flip to <em>active</em> once it's live.</li>
        <li>(Optional) Link it to a Tenant, Cluster (if it's a hypervisor), or Virtual Chassis (if stacked).</li>
      </OL>

      <H2>3f · Components</H2>
      <P>Once a Device exists, add its physical components. SMIFS treats each as a first‑class object so you can cable them up:</P>
      <UL>
        <li><GoTo to="/interfaces" label="Interfaces" /> — Ethernet, LAG, virtual, wireless.</li>
        <li><GoTo to="/console-ports" label="Console Ports" /> and <GoTo to="/console-server-ports" label="Console Server Ports" />.</li>
        <li><GoTo to="/power-ports" label="Power Ports" /> (on a device) and <GoTo to="/power-outlets" label="Power Outlets" /> (on a PDU).</li>
        <li><GoTo to="/front-ports" label="Front" /> & <GoTo to="/rear-ports" label="Rear Ports" /> — used for patch panels.</li>
        <li><GoTo to="/module-bays" label="Module Bays" /> / <GoTo to="/device-bays" label="Device Bays" /> — slots for line‑cards or sub‑devices.</li>
      </UL>
      <Tip tone="do">
        If you find yourself adding 48 identical interfaces by hand, build them once on the <em>Device Type</em> as
        <GoTo to="/interface-templates" label="Interface Templates" /> instead — they spawn automatically on every new device of that type (planned for future automation).
      </Tip>
    </div>
  ),

  connections: () => (
    <div>
      <H1 icon={Cable}>Step 4 · Cabling</H1>
      <Lead>A Cable connects two endpoints. The endpoints can be interfaces, console ports, power ports, front/rear ports, circuit terminations, or power feeds — anything pluggable.</Lead>
      <H2>How to add a cable</H2>
      <Step n={1}>Open <GoTo to="/cables" label="Cables" /> → <strong>Add Cable</strong>.</Step>
      <Step n={2}>In <em>A terminations</em>, paste a JSON array like <Code>{`[{"object_type":"interface","object_id":"<uuid>"}]`}</Code></Step>
      <Step n={3}>Do the same for <em>B terminations</em>.</Step>
      <Step n={4}>Pick a cable <strong>type</strong> (cat6, smf‑os2, dac‑passive, power, …) and a colour. Status defaults to <KBD>connected</KBD>.</Step>
      <Step n={5}>Save. SMIFS marks both terminations as connected and refuses a second cable on the same endpoint.</Step>
      <Tip tone="idea">
        The polymorphic <KBD>object_type</KBD> values are: <code>interface</code>, <code>console-port</code>, <code>console-server-port</code>,
        <code>power-port</code>, <code>power-outlet</code>, <code>front-port</code>, <code>rear-port</code>, <code>circuit-termination</code>, <code>power-feed</code>.
      </Tip>
      <H2>Cable tracing</H2>
      <P>
        Open <GoTo to="/cable-trace" label="Cable Trace" />, pick a starting object type and id, click <em>Trace</em>.
        SMIFS walks every cable and patch (front‑port ↔ rear‑port hops) up to a 50‑hop ceiling and shows you the full path.
        Great for figuring out "where does this fibre actually end up?"
      </P>
      <H2>Inferred cables from discovery</H2>
      <P>
        If you run an SNMP discovery (see Step 10), LLDP/CDP neighbour data is converted to cables automatically. Look for them tagged <KBD>auto-discovered</KBD>.
      </P>
    </div>
  ),

  ipam: () => (
    <div>
      <H1 icon={Globe}>Step 5 · IPAM</H1>
      <Lead>IP Address Management. The hierarchy is: <strong>RIR → Aggregate → Prefix (recursive) → IP Range → IP Address</strong>. Plus VRFs and VLANs cut across this.</Lead>

      <H2>5a · RIRs and ASNs</H2>
      <UL>
        <li><strong>RIR</strong> — the registry that allocated your space (APNIC, ARIN, RIPE, AFRINIC, LACNIC, or "RFC1918" for private).</li>
        <li><strong>ASN Range / ASN</strong> — your autonomous system numbers (16/32‑bit). Tag them with a tenant.</li>
      </UL>

      <H2>5b · Aggregates</H2>
      <P>An Aggregate is a top‑of‑pyramid CIDR you got from a RIR, e.g., <KBD>203.0.113.0/24</KBD>. Aggregates don't get assigned — they hold child Prefixes.</P>

      <H2>5c · Prefixes (the meat)</H2>
      <P>Prefixes are CIDR blocks. They are recursive — a /24 can contain /27s which contain /30s. SMIFS computes parent/child by looking at the actual subnet math, so you do not have to set parents manually.</P>
      <UL>
        <li><strong>Status</strong>: <KBD>container</KBD> (used only to hold other prefixes), <KBD>active</KBD>, <KBD>reserved</KBD>, <KBD>deprecated</KBD>.</li>
        <li><strong>Role</strong>: typically Mgmt, User, Voice, Loopback, Point‑to‑point.</li>
        <li><strong>Is pool</strong>: when true, "available IPs" includes the network and broadcast addresses (useful for /31 P2P links).</li>
        <li><strong>VRF</strong>: the routing instance. Same prefix in two VRFs = two different prefixes.</li>
      </UL>
      <P>
        Visit <GoTo to="/prefix-tree" label="Prefix Tree" /> for a hierarchical view (optionally filtered by VRF), and call
        <KBD>GET /api/prefix-tools/available-ips/&#123;prefix_id&#125;</KBD> to get the next free IPs.
      </P>

      <H2>5d · IP Addresses</H2>
      <OL>
        <li>Always store an IP in CIDR notation: <KBD>10.0.0.5/24</KBD> not just <KBD>10.0.0.5</KBD>.</li>
        <li>Assign it to a component by setting <em>assigned_object_type</em> (<KBD>interface</KBD> / <KBD>vminterface</KBD> / <KBD>fhrpgroup</KBD>) and <em>assigned_object_id</em>.</li>
        <li>(NAT) Set <em>nat_inside_id</em> to model 1:1 NAT — the outside IP points to the inside IP.</li>
        <li>Use <em>role</em> for <KBD>vip</KBD>, <KBD>vrrp</KBD>, <KBD>hsrp</KBD>, <KBD>anycast</KBD>, etc.</li>
        <li>Set the <strong>Primary IPv4/IPv6</strong> on the parent Device so reports know which address is its "front door".</li>
      </OL>

      <H2>5e · VRFs &amp; Route Targets</H2>
      <P>Create a VRF first (with optional Route Distinguisher), then tag prefixes / IPs with it. Import / Export Route Targets attach to the VRF for MPLS L3VPN modelling.</P>

      <H2>5f · VLANs</H2>
      <UL>
        <li>Create a <strong>VLAN Group</strong> per site or per fabric. It defines the allowed VID range (1‑4094 by default).</li>
        <li>Create <strong>VLANs</strong> inside the group with a VID and a name (e.g., <em>VID 10 — Management</em>).</li>
        <li>On each Interface, choose mode <KBD>access</KBD> + <em>untagged_vlan</em>, or <KBD>tagged</KBD> + <em>tagged_vlans</em>.</li>
        <li>Optionally link the VLAN to a Prefix so DHCP scope and L3 are obvious.</li>
      </UL>

      <H2>5g · Services and FHRP</H2>
      <UL>
        <li><strong>Service</strong> — "DNS on udp/53 on device kol‑dns‑01". Used by NetOps inventory.</li>
        <li><strong>FHRP Group</strong> — HSRP/VRRP/GLBP/CARP virtual gateway groups. Assign IPs with role <KBD>vrrp</KBD>/<KBD>hsrp</KBD>.</li>
      </UL>
    </div>
  ),

  circuits: () => (
    <div>
      <H1 icon={Route}>Step 6 · Circuits</H1>
      <Lead>Circuits model the wires that come into your data‑centre from telcos / ISPs.</Lead>
      <H2>Build order</H2>
      <OL>
        <li><strong>Provider</strong> — Tata, Airtel, Lumen, Cogent, …</li>
        <li>(Optional) <strong>Provider Account</strong> if you have many account numbers with one provider.</li>
        <li>(Optional) <strong>Provider Network</strong> — abstract clouds (MPLS, SD‑WAN backbone) when the far end is the provider, not another of your sites.</li>
        <li><strong>Circuit Type</strong> — IPL, MPLS, Internet Transit, Dark Fibre, Wave.</li>
        <li><strong>Circuit</strong> — the actual order. Requires Circuit ID (CID), Provider, Type. Add install / termination dates, commit rate.</li>
        <li><strong>Circuit Terminations</strong> — one per side. Side A is usually <em>your</em> side (set Site), side Z is the provider (set Provider Network or another Site).</li>
        <li>Once you have a termination, you can cable it to a Device's interface via the normal Cables flow (<KBD>object_type=circuit-termination</KBD>).</li>
      </OL>
      <Tip tone="info">When a circuit goes down, set its status to <KBD>offline</KBD> rather than deleting it. The change log and tenant chargeback reports rely on history.</Tip>
    </div>
  ),

  power: () => (
    <div>
      <H1 icon={Zap}>Step 7 · Power</H1>
      <Lead>Power Panels feed Power Feeds, which feed Rack PDUs, which feed Power Ports on devices.</Lead>
      <H2>Build order</H2>
      <OL>
        <li><GoTo to="/power-panels" label="Power Panel" /> — name + Site (and Location). Usually one per electrical room.</li>
        <li><GoTo to="/power-feeds" label="Power Feed" /> — comes from a Panel, feeds a Rack. Set supply (AC/DC), phase, voltage (e.g., 230V), amperage (e.g., 32A), max utilisation %.</li>
        <li>(Optional) Cable the Power Feed to a Power Port on a PDU device (<KBD>object_type=power-feed</KBD>).</li>
        <li>On the PDU device, define <GoTo to="/power-outlets" label="Power Outlets" />. Each outlet references a parent <em>power port</em>.</li>
        <li>On each server, cable its Power Port → the PDU's Power Outlet.</li>
      </OL>
      <Tip tone="idea">Once cabled, you can sum allocated_draw on outlets vs. feed amperage × voltage to compute true rack power utilisation.</Tip>
    </div>
  ),

  virt: () => (
    <div>
      <H1 icon={Box}>Step 8 · Virtualization</H1>
      <Lead>Same template → instance pattern as devices, but for VMs.</Lead>
      <OL>
        <li><GoTo to="/cluster-types" label="Cluster Types" /> — VMware vSphere, Proxmox, Hyper‑V, K8s, Nutanix AHV.</li>
        <li>(Optional) <GoTo to="/cluster-groups" label="Cluster Groups" /> if you have many clusters in regions.</li>
        <li><GoTo to="/clusters" label="Clusters" /> — name + type + (optionally) Site and Tenant.</li>
        <li>Attach <strong>physical hypervisor Devices</strong> by setting their <em>cluster_id</em>.</li>
        <li><GoTo to="/virtual-machines" label="Virtual Machines" /> — name, cluster, vCPUs, memory (MB), disk (GB), role.</li>
        <li><GoTo to="/vm-interfaces" label="VM Interfaces" /> — each VM has one or more virtual NICs. Assign IPs via the normal IP flow (assigned_object_type = <KBD>vminterface</KBD>).</li>
        <li><GoTo to="/virtual-disks" label="Virtual Disks" /> — additional disks beyond the boot disk.</li>
      </OL>
    </div>
  ),

  'wireless-vpn': () => (
    <div>
      <H1 icon={Wifi}>Step 9 · Wireless &amp; VPN</H1>
      <H2>Wireless</H2>
      <OL>
        <li><GoTo to="/wireless-lan-groups" label="Wireless LAN Group" /> — e.g., "Corporate", "Guest".</li>
        <li><GoTo to="/wireless-lans" label="Wireless LAN" /> — SSID, optional VLAN, auth type (open/WPA‑personal/WPA‑enterprise), PSK.</li>
        <li><GoTo to="/wireless-links" label="Wireless Link" /> — point‑to‑point radio links between two Interfaces (replace Cable for wireless backhauls).</li>
      </OL>
      <H2>VPN &amp; Overlay</H2>
      <UL>
        <li><GoTo to="/l2vpns" label="L2VPN" /> — VXLAN, VPLS, MPLS EVPN. Attach terminations to VLANs / interfaces.</li>
        <li><GoTo to="/tunnels" label="Tunnels" /> — GRE, IPsec, WireGuard, OpenVPN. Tunnel Terminations attach to interfaces with an outside IP.</li>
        <li><GoTo to="/ike-proposals" label="IKE Proposals/Policies" /> &amp; <GoTo to="/ipsec-proposals" label="IPSec Proposals/Policies/Profiles" /> — model your IPsec parameters reusably.</li>
      </UL>
    </div>
  ),

  discovery: () => (
    <div>
      <H1 icon={Radar}>Step 10 · Autodiscovery (Netdisco‑style)</H1>
      <Lead>The fastest way to populate SMIFS is to <em>not</em> type — let the network tell SMIFS what is on it.</Lead>
      <H2>What it does</H2>
      <UL>
        <li>Polls SNMP on a target IP/range/CIDR.</li>
        <li>Reads sysName, sysDescr, ifTable, ipAddrTable, LLDP/CDP neighbours.</li>
        <li>Stages each result as a <em>Discovered Device</em> (raw snapshot).</li>
        <li>One click → SMIFS creates Manufacturer, Device Type, Role, Site, Device, Interfaces, IP Addresses, and inferred Cables.</li>
      </UL>
      <H2>End‑to‑end</H2>
      <Step n={1}>Open <GoTo to="/discovery/credentials" label="Discovery → Credentials" />. Add one: name <KBD>Default</KBD>, SNMP v2c, community <KBD>public</KBD> (or v3 with username + auth/priv keys).</Step>
      <Step n={2}>Open <GoTo to="/discovery" label="Discovery → Dashboard" />. Try the <strong>Ad‑hoc Scan</strong> first: type an IP, pick the credential, click Scan. You will see vendor / model / interfaces. Click <strong>Import to SMIFS</strong>.</Step>
      <Step n={3}>For recurring or bulk scans, open <GoTo to="/discovery/jobs" label="Discovery Jobs" /> → <strong>Add Job</strong>. Target spec accepts:
        <UL>
          <li>A CIDR: <KBD>10.0.0.0/24</KBD></li>
          <li>A range: <KBD>10.0.0.1-50</KBD></li>
          <li>A comma list: <KBD>10.0.0.1, 10.0.0.5, 10.0.0.10</KBD></li>
        </UL>
        Tick <em>Auto‑import</em> and pick a target Site — SMIFS will create Devices automatically as it finds them.
      </Step>
      <Step n={4}>Click <strong>Run</strong>. The page polls every 5 seconds and the status moves <KBD>pending → running → completed</KBD> with stats (scanned / discovered / imported).</Step>
      <Step n={5}>Open <GoTo to="/discovery/devices" label="Discovered Devices" /> to review raw snapshots. Click any row for Details (interfaces, neighbours). Use <strong>Import</strong> to map manually.</Step>
      <Step n={6}>Open <GoTo to="/discovery/topology" label="Network Topology" /> to see the auto‑drawn graph — nodes are imported devices, edges are LLDP/CDP inferred cables.</Step>
      <H2>Bridging an existing Netdisco</H2>
      <P>
        If you already run Netdisco, open <GoTo to="/discovery/netdisco" label="Netdisco Sync" />. Fill in Base URL,
        Username, Password → <strong>Test Connection</strong>. If reachable, click <strong>Pull Devices Now</strong> —
        SMIFS pulls device + port + neighbour data via Netdisco's REST API and stages them as Discovered Devices ready
        for import.
      </P>
      <Tip tone="warn">
        Discovery uses real SNMP traffic. If a target is unreachable, behind a firewall, or has the wrong community/credential,
        SMIFS returns an honest <em>unreachable</em> result with the specific error (timeout, no reply, auth failure). There
        is no simulated data — what you see in the Discovered Devices list is what came back on the wire.
      </Tip>
    </div>
  ),

  customization: () => (
    <div>
      <H1 icon={Settings2}>Customization</H1>
      <Lead>Bend SMIFS to your business without forking it.</Lead>
      <H2>Tags</H2>
      <P>
        Add coloured tags to <em>any</em> object. Filter lists, dashboards and the global search by tag. Tip — use tags like
        <KBD>pci-zone</KBD>, <KBD>prod</KBD>, <KBD>edge</KBD>, <KBD>monitoring-critical</KBD>.
      </P>
      <H2>Custom Fields</H2>
      <OL>
        <li>Open <GoTo to="/custom-fields" label="Custom Fields" /> → Add.</li>
        <li>Pick the <em>type</em> (text, integer, boolean, date, url, select, multiselect, json, object).</li>
        <li>Pick <em>object types</em> — which models should grow this field (e.g., "devices", "racks", "sites").</li>
        <li>Optional: required, default, choices (for select), weight (ordering in forms).</li>
      </OL>
      <P>Custom field values live inside the object's <KBD>custom_fields</KBD> map and appear in the detail form just like built‑in fields.</P>
      <H2>Custom Links</H2>
      <P>Add buttons that point to external systems. Templates can use object fields (e.g., link to Grafana with the device name).</P>
      <H2>Config Contexts</H2>
      <P>JSON blobs that get merged onto devices based on filters (site / role / platform / tag). Used to feed automation tools like Ansible/Nornir.</P>
      <H2>Config Templates</H2>
      <P>Jinja2 templates you can render against a device's context to generate a config snippet.</P>
      <H2>Webhooks</H2>
      <OL>
        <li>Pick the object types you care about and the events (create / update / delete).</li>
        <li>Set the payload URL (e.g., a Slack / PagerDuty / your‑own webhook).</li>
        <li>Optional secret, custom headers, JSON body template.</li>
      </OL>
      <H2>Saved Filters &amp; Journal Entries</H2>
      <P>
        Save a complex list filter for one‑click recall. Add Journal Entries (timestamped notes with severity) to any object — they show up under the
        Journal tab on the detail page.
      </P>
    </div>
  ),

  'audit-search': () => (
    <div>
      <H1 icon={Search}>Audit &amp; Search</H1>
      <H2>Global search</H2>
      <P>The search box in the header looks across sites, locations, racks, devices, interfaces, IPs, prefixes, VLANs, VRFs, VMs, clusters, circuits, providers, cables, contacts, manufacturers and device‑types. Type two characters to trigger autocomplete.</P>
      <H2>Change Log</H2>
      <P>
        Every create / update / delete is recorded in the change log with a snapshot of the before and after state, plus the user who did it. Open
        <GoTo to="/changelog" label="Change Log" /> for the global feed, or click the <em>Change Log</em> tab on any detail page for just that object's history.
      </P>
      <H2>Search by tag</H2>
      <P>The generic search parameter <KBD>?q=</KBD> on every resource list also matches tags. Try <KBD>/devices?q=auto-discovered</KBD>.</P>
    </div>
  ),

  csv: () => (
    <div>
      <H1 icon={FileText}>CSV Import / Export</H1>
      <Lead>Every list view has Export and Import buttons.</Lead>
      <H2>Export</H2>
      <P>Click <strong>Export</strong> on any list page. You get a CSV with every column for every record (up to 10,000 rows). Use this for spreadsheets, backups, or to migrate to another system.</P>
      <H2>Import</H2>
      <OL>
        <li>Click <strong>Import</strong>. Upload a CSV.</li>
        <li>Headers in the CSV must match field names (e.g., <KBD>name,status,site_id</KBD>).</li>
        <li>SMIFS imports row by row; on success it returns a count, on failure a list of errors per row.</li>
      </OL>
      <Tip tone="do">
        The easiest workflow: <em>(a)</em> create one object by hand, <em>(b)</em> export the list, <em>(c)</em> append rows to the CSV in Excel, <em>(d)</em> re‑import. You never have to memorise headers.
      </Tip>
    </div>
  ),

  api: () => (
    <div>
      <H1 icon={Code2}>REST API &amp; GraphQL</H1>
      <Lead>Anything you can do in the UI you can do over the API. Use it for CI/CD, scripts, observability integrations.</Lead>
      <H2>Get a token</H2>
      <P>Open your avatar → <strong>API Tokens</strong> → Add. Copy the <KBD>key</KBD> shown — that is your bearer token.</P>
      <H2>REST examples</H2>
      <Code>{`# List sites
curl -H "Authorization: Bearer <TOKEN>" \\
  https://<your-host>/api/sites

# Create a site
curl -X POST -H "Authorization: Bearer <TOKEN>" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Mumbai-DC","status":"active"}' \\
  https://<your-host>/api/sites

# Run a discovery job
curl -X POST -H "Authorization: Bearer <TOKEN>" \\
  https://<your-host>/api/discovery/jobs/<job-id>/run`}</Code>
      <P>Every endpoint supports <KBD>?limit=</KBD>, <KBD>?offset=</KBD>, <KBD>?q=</KBD> and <KBD>?sort=field</KBD> (or <KBD>-field</KBD> for desc).</P>
      <H2>GraphQL</H2>
      <P>
        Open <GoTo to="/graphql" label="GraphQL Playground" />. Try:
      </P>
      <Code>{`{
  collections
}

{
  collection(name: "devices", limit: 5, q: "core") {
    id
    data
  }
}`}</Code>
      <H2>Schema introspection</H2>
      <P>Visit <KBD>/api/_schema</KBD> for a JSON list of every collection, path, tag, and special endpoint.</P>
    </div>
  ),

  admin: () => (
    <div>
      <H1 icon={ShieldCheck}>Admin &amp; Security</H1>
      <H2>Users</H2>
      <P>Open <GoTo to="/admin/users" label="Users" /> to add accounts. Toggle <em>is_admin</em> for full access. Set <em>is_active=false</em> to lock without deleting.</P>
      <H2>Groups</H2>
      <P>Group accounts for easier permissioning (planned: per‑group permissions; today they are descriptive).</P>
      <H2>API Tokens</H2>
      <P>Each user can mint multiple tokens. Tokens currently inherit the user's permissions. Rotate them every 90 days.</P>
      <H2>Auth bridge to Orglens (planned)</H2>
      <P>
        The auth layer is intentionally narrow: only <KBD>app/auth.py::get_current_user</KBD> and <KBD>POST /api/auth/login</KBD> talk to user storage.
        When the Orglens employee directory integration playbook lands, only those two functions need to delegate to Orglens — the UI does not change.
      </P>
      <Tip tone="warn">Remove or password‑rotate the default <KBD>admin / admin</KBD> account before sharing this instance with anyone outside your team.</Tip>
    </div>
  ),

  patterns: () => (
    <div>
      <H1 icon={Network}>Architecture Patterns</H1>
      <Lead>Three reference setups. Use whichever matches your reality, then adapt.</Lead>

      <H2>Pattern A · Single‑site enterprise</H2>
      <DiagramBox>{`Region: (skip)
Site:  HQ
Locations: Server-Room, IDF-1, IDF-2
Tenants: (skip)
Racks: HQ-A-01, HQ-A-02, ...
Roles: Core, Distribution, Access, Firewall, Server
Manufacturer/DeviceType library: 3-5 entries
VRFs: global only
VLANs: 10..50 in a single VLAN Group "HQ"
Prefixes: one /16 broken into per-VLAN /24s
Circuits: 2 internet feeds (primary + backup)`}</DiagramBox>

      <H2>Pattern B · Multi‑tenant ISP / Co‑lo</H2>
      <DiagramBox>{`Tenants: one per customer
Sites: one per POP/DC
Each customer gets:
  - dedicated VRF "CUST-<NAME>"
  - their Aggregates/Prefixes (mark tenant_id)
  - their Wireless LANs/VLAN Groups
  - Devices and Cables tagged with their tenant_id
Circuits modelled as "customer drops"
Use Webhooks to push customer-visible inventory to their portal`}</DiagramBox>

      <H2>Pattern C · Multi‑region cloud / SD‑WAN</H2>
      <DiagramBox>{`Regions: Asia, EU, NA (nested countries beneath)
Site Groups: Edge POPs, Core DCs
Sites: ~10-30 entries
Provider Networks: model the SD-WAN/MPLS clouds
Circuits terminate Site <-> Provider Network
Tunnels: site-to-site IPsec / WireGuard
L2VPNs: VXLAN identifiers across the fabric
Discovery jobs: one per region with a different SNMP credential`}</DiagramBox>

      <H2>Migrating from spreadsheets / Excel</H2>
      <OL>
        <li>Decide your hierarchy (Region / Site / Location). Build that first.</li>
        <li>Build the Device Type library — even if it is just 10 entries.</li>
        <li>Add a few <strong>Roles</strong> (Switch, Router, Firewall, Server, …).</li>
        <li>Add one Device by hand to <em>see</em> the field names.</li>
        <li><GoTo to="/devices" label="Export the Devices list" /> to CSV. Use the CSV as a template; fill it from your spreadsheet; re‑import.</li>
        <li>Repeat for Interfaces, IPs, Prefixes, VLANs.</li>
        <li>Run <strong>Discovery</strong> jobs to fill in everything else from the live network.</li>
      </OL>
      <Tip tone="do">The single biggest mistake is over‑modelling. Start with the smallest hierarchy that explains your real ops. You can always add tenants / locations / VRFs later — SMIFS is happy with shallow data.</Tip>
    </div>
  ),
};

// ========================================================================
// Page shell with sticky TOC, prev / next, search filter
// ========================================================================

export default function Help() {
  const [active, setActive] = useState('welcome');
  const [filter, setFilter] = useState('');
  const contentRef = useRef(null);

  const filtered = useMemo(() => {
    if (!filter) return CHAPTERS;
    const f = filter.toLowerCase();
    return CHAPTERS.filter((c) => c.title.toLowerCase().includes(f) || c.group.toLowerCase().includes(f));
  }, [filter]);

  const groups = useMemo(() => {
    const m = new Map();
    filtered.forEach((c) => { if (!m.has(c.group)) m.set(c.group, []); m.get(c.group).push(c); });
    return Array.from(m.entries());
  }, [filtered]);

  const currentIdx = CHAPTERS.findIndex((c) => c.id === active);
  const prev = currentIdx > 0 ? CHAPTERS[currentIdx - 1] : null;
  const next = currentIdx >= 0 && currentIdx < CHAPTERS.length - 1 ? CHAPTERS[currentIdx + 1] : null;
  const Chapter = Bodies[active] || Bodies.welcome;

  useEffect(() => { contentRef.current?.scrollTo({ top: 0, behavior: 'smooth' }); }, [active]);

  return (
    <div className="flex h-full">
      <aside className="w-72 border-r bg-muted/30 flex flex-col overflow-hidden">
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-md bg-emerald-600 text-white flex items-center justify-center"><BookOpen size={16} /></div>
            <div>
              <div className="font-semibold">Help & Tutorial</div>
              <div className="text-[11px] text-muted-foreground">A guided tour, end-to-end.</div>
            </div>
          </div>
          <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter chapters…" className="h-8 text-sm" />
        </div>
        <nav className="flex-1 overflow-y-auto p-2">
          {groups.map(([group, items]) => (
            <div key={group} className="mb-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground px-2 mb-1 font-semibold">{group}</div>
              {items.map((c) => {
                const Icon = c.icon;
                const isActive = active === c.id;
                return (
                  <button
                    key={c.id}
                    onClick={() => setActive(c.id)}
                    data-testid={`help-toc-${c.id}`}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm text-left transition-colors ${isActive ? 'bg-emerald-600 text-white' : 'text-foreground hover:bg-emerald-100'}`}
                  >
                    <Icon size={14} className={isActive ? 'text-white' : 'text-emerald-600'} />
                    <span className="truncate">{c.title}</span>
                  </button>
                );
              })}
            </div>
          ))}
          {groups.length === 0 && <div className="text-sm text-muted-foreground p-4 text-center">No chapters match "{filter}"</div>}
        </nav>
      </aside>

      <main ref={contentRef} className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto p-8">
          <div className="text-xs uppercase tracking-wider text-emerald-700 font-semibold mb-2">{CHAPTERS[currentIdx]?.group}</div>
          <Chapter />
          <div className="border-t mt-12 pt-6 flex items-center justify-between">
            {prev ? (
              <Button variant="outline" onClick={() => setActive(prev.id)} data-testid="help-prev">
                <ArrowLeft size={14} className="mr-1" /> {prev.title}
              </Button>
            ) : <span />}
            {next ? (
              <Button onClick={() => setActive(next.id)} data-testid="help-next">
                {next.title} <ArrowRight size={14} className="ml-1" />
              </Button>
            ) : (
              <Badge variant="secondary" className="px-3 py-1.5">End of tutorial — happy modelling!</Badge>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
