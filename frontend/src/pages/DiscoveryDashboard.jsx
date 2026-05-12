import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Radar, ScanSearch, Network, Settings2, Plus, Play, Download } from 'lucide-react';

export default function DiscoveryDashboard() {
  const [stats, setStats] = useState({});
  const [credentials, setCredentials] = useState([]);
  const [adhoc, setAdhoc] = useState({ target: '', credential_id: '__none__' });
  const [scanning, setScanning] = useState(false);
  const [adhocResult, setAdhocResult] = useState(null);

  const load = async () => {
    try {
      const [s, c] = await Promise.all([
        api.get('/discovery/stats'),
        api.get('/discovery/credentials'),
      ]);
      setStats(s.data);
      setCredentials(c.data.results || []);
    } catch (e) {}
  };
  useEffect(() => { load(); }, []);

  const runAdhoc = async () => {
    if (!adhoc.target) return;
    setScanning(true);
    setAdhocResult(null);
    try {
      const body = { target: adhoc.target, timeout: 3 };
      if (adhoc.credential_id && adhoc.credential_id !== '__none__') body.credential_id = adhoc.credential_id;
      const { data } = await api.post('/discovery/scan', body);
      setAdhocResult(data);
      toast.success(`Scanned ${data.target} — ${data.simulated ? 'simulated' : 'live'} result`);
      load();
    } catch (e) { toast.error('Scan failed'); }
    setScanning(false);
  };

  const importIt = async () => {
    if (!adhocResult?.id) return;
    try {
      const { data } = await api.post(`/discovery/devices/${adhocResult.id}/import`, {});
      toast.success(`Imported — created ${data.interfaces_created} interfaces, ${data.ips_created} IPs, ${data.cables_created} cables`);
      load();
    } catch (e) { toast.error('Import failed'); }
  };

  const STAT_CARDS = [
    { key: 'credentials', label: 'Credentials', icon: Settings2, link: '/discovery/credentials' },
    { key: 'jobs', label: 'Discovery Jobs', icon: ScanSearch, link: '/discovery/jobs' },
    { key: 'jobs_running', label: 'Running Now', icon: Radar, link: '/discovery/jobs' },
    { key: 'jobs_completed', label: 'Completed Jobs', icon: ScanSearch, link: '/discovery/jobs' },
    { key: 'discovered_devices', label: 'Discovered Devices', icon: Network, link: '/discovery/devices' },
    { key: 'imported_devices', label: 'Imported to SMIFS', icon: Network, link: '/devices' },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2"><Radar size={22} className="text-emerald-600" />Discovery</h1>
          <p className="text-sm text-muted-foreground mt-1">SNMP-based autodiscovery (Netdisco compatible) — scan, discover, map.</p>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {STAT_CARDS.map((s) => {
          const Icon = s.icon;
          return (
            <Link key={s.key} to={s.link}>
              <Card className="hover:border-emerald-500 transition-all">
                <CardContent className="p-4">
                  <div className="w-9 h-9 mb-2 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center"><Icon size={16} /></div>
                  <div className="text-xs uppercase tracking-wider text-muted-foreground">{s.label}</div>
                  <div className="text-2xl font-semibold tabular-nums">{stats[s.key] ?? '…'}</div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Ad-hoc Scan</CardTitle>
          <CardDescription>Probe a single target by IP/hostname using SNMP. Falls back to simulated results if unreachable.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 items-end mb-4">
            <div className="flex-1">
              <Label className="text-xs uppercase">Target IP / Hostname</Label>
              <Input value={adhoc.target} onChange={(e) => setAdhoc({ ...adhoc, target: e.target.value })} placeholder="e.g. 10.0.0.1 or core-sw-01" />
            </div>
            <div className="w-64">
              <Label className="text-xs uppercase">Credential</Label>
              <Select value={adhoc.credential_id} onValueChange={(v) => setAdhoc({ ...adhoc, credential_id: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">Default (public v2c)</SelectItem>
                  {credentials.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={runAdhoc} disabled={scanning || !adhoc.target} data-testid="adhoc-scan-btn"><Play size={14} className="mr-1" />{scanning ? 'Scanning…' : 'Scan'}</Button>
          </div>
          {adhocResult && (
            <div className="border rounded p-4 bg-muted/30 space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <Badge variant={adhocResult.simulated ? 'secondary' : 'default'}>{adhocResult.simulated ? 'simulated' : 'live SNMP'}</Badge>
                <span className="font-semibold">{adhocResult.sysname || adhocResult.target}</span>
                <Badge variant="outline">{adhocResult.vendor}</Badge>
                <Badge variant="outline">{adhocResult.model}</Badge>
                <span className="flex-1" />
                <Button size="sm" onClick={importIt}><Download size={14} className="mr-1" />Import to SMIFS</Button>
              </div>
              <div><span className="text-muted-foreground">Description:</span> {adhocResult.sysdescr}</div>
              <div><span className="text-muted-foreground">Location:</span> {adhocResult.syslocation || '—'}</div>
              <div><span className="text-muted-foreground">Interfaces:</span> {(adhocResult.interfaces || []).length}, <span className="text-muted-foreground">IPs:</span> {(adhocResult.ip_addresses || []).length}, <span className="text-muted-foreground">Neighbors:</span> {(adhocResult.neighbors || []).length}</div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Quick Links</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Link to="/discovery/credentials" className="block p-3 border rounded hover:border-emerald-500"><Settings2 size={14} className="inline mr-2" />Manage Credentials (SNMP v1 / v2c / v3)</Link>
            <Link to="/discovery/jobs" className="block p-3 border rounded hover:border-emerald-500"><ScanSearch size={14} className="inline mr-2" />Scheduled / On-Demand Jobs</Link>
            <Link to="/discovery/devices" className="block p-3 border rounded hover:border-emerald-500"><Network size={14} className="inline mr-2" />Discovered Devices Inbox</Link>
            <Link to="/discovery/topology" className="block p-3 border rounded hover:border-emerald-500"><Network size={14} className="inline mr-2" />Network Topology Graph</Link>
            <Link to="/discovery/netdisco" className="block p-3 border rounded hover:border-emerald-500"><Radar size={14} className="inline mr-2" />External Netdisco Sync</Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">How it works</CardTitle></CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p><strong className="text-foreground">SNMP scanning</strong> uses pysnmp to poll <code>sysDescr</code>, <code>sysName</code>, <code>ifTable</code>, <code>ipAddrTable</code>, and LLDP/CDP neighbour tables on each target.</p>
            <p><strong className="text-foreground">Auto-mapping</strong> creates SMIFS Manufacturer / DeviceType / DeviceRole / Device / Interface / IPAddress records and infers Cables from LLDP neighbours.</p>
            <p><strong className="text-foreground">Netdisco bridge</strong> pulls already-discovered devices from a running Netdisco instance via its REST API.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
