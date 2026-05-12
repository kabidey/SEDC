import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Trash2, Plus, Play } from 'lucide-react';
import { toast } from 'sonner';

export function CredentialsPage() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', snmp_version: 'v2c', community: 'public', username: '', auth_key: '', priv_key: '', port: 161, description: '' });
  const load = async () => { const { data } = await api.get('/discovery/credentials'); setItems(data.results || []); };
  useEffect(() => { load(); }, []);
  const create = async () => {
    try {
      await api.post('/discovery/credentials', form);
      toast.success('Credential created');
      setOpen(false);
      setForm({ name: '', snmp_version: 'v2c', community: 'public', username: '', auth_key: '', priv_key: '', port: 161, description: '' });
      load();
    } catch (e) { toast.error('Failed'); }
  };
  const del = async (id) => { try { await api.delete(`/discovery/credentials/${id}`); load(); } catch {} };
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div><h1 className="text-2xl font-bold">Discovery Credentials</h1><p className="text-sm text-muted-foreground">SNMP v1 / v2c / v3 credentials used by discovery jobs.</p></div>
        <Button onClick={() => setOpen(true)} data-testid="add-credential-btn"><Plus size={14} className="mr-1" />Add Credential</Button>
      </div>
      <Card><CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b"><tr><th className="p-3 text-left">Name</th><th className="p-3 text-left">Version</th><th className="p-3 text-left">Community / User</th><th className="p-3 text-left">Port</th><th className="p-3 text-left">Description</th><th className="p-3"></th></tr></thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id} className="border-b last:border-0">
                <td className="p-3 font-medium">{c.name}</td>
                <td className="p-3"><Badge variant="outline">{c.snmp_version}</Badge></td>
                <td className="p-3">{c.snmp_version === 'v3' ? c.username : c.community}</td>
                <td className="p-3">{c.port}</td>
                <td className="p-3">{c.description}</td>
                <td className="p-3 text-right"><Button size="icon" variant="ghost" onClick={() => del(c.id)}><Trash2 size={14} className="text-destructive" /></Button></td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No credentials yet</td></tr>}
          </tbody>
        </table>
      </CardContent></Card>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create Credential</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
            <div><Label>SNMP Version</Label>
              <Select value={form.snmp_version} onValueChange={(v) => setForm({ ...form, snmp_version: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="v1">v1</SelectItem><SelectItem value="v2c">v2c</SelectItem><SelectItem value="v3">v3</SelectItem></SelectContent>
              </Select>
            </div>
            {form.snmp_version !== 'v3' ? (
              <div><Label>Community</Label><Input value={form.community} onChange={(e) => setForm({ ...form, community: e.target.value })} /></div>
            ) : (
              <>
                <div><Label>Username</Label><Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></div>
                <div><Label>Auth Key</Label><Input type="password" value={form.auth_key} onChange={(e) => setForm({ ...form, auth_key: e.target.value })} /></div>
                <div><Label>Priv Key</Label><Input type="password" value={form.priv_key} onChange={(e) => setForm({ ...form, priv_key: e.target.value })} /></div>
              </>
            )}
            <div><Label>Port</Label><Input type="number" value={form.port} onChange={(e) => setForm({ ...form, port: Number(e.target.value) })} /></div>
            <div><Label>Description</Label><Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={create}>Create</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [creds, setCreds] = useState([]);
  const [sites, setSites] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', target_spec: '', credential_id: '__none__', site_id: '__none__', auto_import: true, description: '' });

  const load = async () => {
    const [j, c, s] = await Promise.all([api.get('/discovery/jobs'), api.get('/discovery/credentials'), api.get('/sites?limit=200')]);
    setJobs(j.data.results || []);
    setCreds(c.data.results || []);
    setSites(s.data.results || []);
  };
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, []);

  const create = async () => {
    try {
      const payload = { ...form };
      if (payload.credential_id === '__none__') delete payload.credential_id;
      if (payload.site_id === '__none__') delete payload.site_id;
      await api.post('/discovery/jobs', payload);
      toast.success('Job created');
      setOpen(false);
      setForm({ name: '', target_spec: '', credential_id: '__none__', site_id: '__none__', auto_import: true, description: '' });
      load();
    } catch (e) { toast.error('Failed'); }
  };
  const run = async (id) => {
    try { await api.post(`/discovery/jobs/${id}/run`); toast.success('Job queued'); load(); } catch (e) { toast.error('Failed'); }
  };
  const del = async (id) => { await api.delete(`/discovery/jobs/${id}`); load(); };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div><h1 className="text-2xl font-bold">Discovery Jobs</h1><p className="text-sm text-muted-foreground">Define target ranges + run SNMP scans.</p></div>
        <Button onClick={() => setOpen(true)} data-testid="add-job-btn"><Plus size={14} className="mr-1" />Add Job</Button>
      </div>
      <Card><CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b"><tr><th className="p-3 text-left">Name</th><th className="p-3 text-left">Target</th><th className="p-3 text-left">Status</th><th className="p-3 text-left">Last Run</th><th className="p-3 text-left">Stats</th><th className="p-3"></th></tr></thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id} className="border-b last:border-0">
                <td className="p-3 font-medium">{j.name}</td>
                <td className="p-3 font-mono text-xs">{j.target_spec}</td>
                <td className="p-3"><Badge variant={j.status === 'running' ? 'default' : j.status === 'completed' ? 'secondary' : 'outline'} className="capitalize">{j.status}</Badge></td>
                <td className="p-3 text-xs text-muted-foreground">{j.last_run?.slice(0, 19).replace('T', ' ') || '—'}</td>
                <td className="p-3 text-xs">scanned: {j.stats?.scanned || 0} · disc: {j.stats?.discovered || 0} · imp: {j.stats?.imported || 0}</td>
                <td className="p-3 text-right">
                  <div className="flex gap-1 justify-end">
                    <Button size="sm" variant="outline" onClick={() => run(j.id)} data-testid={`run-job-${j.id}`}><Play size={12} className="mr-1" />Run</Button>
                    <Button size="icon" variant="ghost" onClick={() => del(j.id)}><Trash2 size={14} className="text-destructive" /></Button>
                  </div>
                </td>
              </tr>
            ))}
            {jobs.length === 0 && <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No discovery jobs. Click "Add Job" to create one.</td></tr>}
          </tbody>
        </table>
      </CardContent></Card>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader><DialogTitle>Create Discovery Job</DialogTitle><DialogDescription>Provide a target spec (CIDR, range, or comma list) and an SNMP credential.</DialogDescription></DialogHeader>
          <div className="space-y-3">
            <div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="DC1 Subnet" /></div>
            <div><Label>Target Spec</Label><Input value={form.target_spec} onChange={(e) => setForm({ ...form, target_spec: e.target.value })} placeholder="10.0.0.0/24 or 10.0.0.1-10 or comma list" /></div>
            <div><Label>Credential</Label>
              <Select value={form.credential_id} onValueChange={(v) => setForm({ ...form, credential_id: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">Default (public v2c)</SelectItem>
                  {creds.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div><Label>Target Site (for auto-import)</Label>
              <Select value={form.site_id} onValueChange={(v) => setForm({ ...form, site_id: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">Auto-Discovered (default)</SelectItem>
                  {sites.map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-3"><Switch checked={form.auto_import} onCheckedChange={(v) => setForm({ ...form, auto_import: v })} /><Label>Auto-import discovered devices to SMIFS</Label></div>
            <div><Label>Description</Label><Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={create}>Create</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function DiscoveredDevicesPage() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState(null);

  const load = async () => { const { data } = await api.get(`/discovery/devices?limit=200${q ? `&q=${q}` : ''}`); setItems(data.results || []); };
  useEffect(() => { load(); }, [q]);
  const importIt = async (id) => { try { const { data } = await api.post(`/discovery/devices/${id}/import`, {}); toast.success(`Imported ${data.device_name} — ${data.interfaces_created} ifs, ${data.ips_created} IPs, ${data.cables_created} cables`); load(); } catch (e) { toast.error('Import failed'); } };
  const del = async (id) => { await api.delete(`/discovery/devices/${id}`); load(); };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div><h1 className="text-2xl font-bold">Discovered Devices</h1><p className="text-sm text-muted-foreground">Raw snapshots from scans — import into SMIFS to create Devices.</p></div>
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search target / vendor / name" className="w-64" />
      </div>
      <Card><CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b"><tr><th className="p-3 text-left">Target</th><th className="p-3 text-left">SysName</th><th className="p-3 text-left">Vendor</th><th className="p-3 text-left">Model</th><th className="p-3 text-left">Reachable</th><th className="p-3 text-left">Ports</th><th className="p-3 text-left">Discovered</th><th className="p-3"></th></tr></thead>
          <tbody>
            {items.map((d) => (
              <tr key={d.id} className="border-b last:border-0 hover:bg-muted/30">
                <td className="p-3 font-mono">{d.target}</td>
                <td className="p-3 font-medium">{d.sysname || '—'}</td>
                <td className="p-3">{d.vendor}</td>
                <td className="p-3">{d.model}</td>
                <td className="p-3">{d.simulated ? <Badge variant="secondary">simulated</Badge> : d.reachable ? <Badge>live</Badge> : <Badge variant="destructive">unreachable</Badge>}</td>
                <td className="p-3 tabular-nums">{(d.interfaces || []).length}</td>
                <td className="p-3 text-xs text-muted-foreground">{d.discovered_at?.slice(0, 19).replace('T', ' ')}</td>
                <td className="p-3 text-right">
                  <div className="flex gap-1 justify-end">
                    <Button size="sm" variant="outline" onClick={() => setSelected(d)}>Details</Button>
                    <Button size="sm" onClick={() => importIt(d.id)} data-testid={`import-${d.id}`}>Import</Button>
                    <Button size="icon" variant="ghost" onClick={() => del(d.id)}><Trash2 size={14} className="text-destructive" /></Button>
                  </div>
                </td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={8} className="p-8 text-center text-muted-foreground">No discovered devices yet. Run an ad-hoc scan or a job.</td></tr>}
          </tbody>
        </table>
      </CardContent></Card>
      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>{selected?.sysname || selected?.target}</DialogTitle><DialogDescription>{selected?.sysdescr}</DialogDescription></DialogHeader>
          {selected && (
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div><Label className="text-xs uppercase">Vendor</Label><div>{selected.vendor}</div></div>
                <div><Label className="text-xs uppercase">Model</Label><div>{selected.model}</div></div>
                <div><Label className="text-xs uppercase">Role</Label><div>{selected.role || '—'}</div></div>
                <div><Label className="text-xs uppercase">Location</Label><div>{selected.syslocation || '—'}</div></div>
              </div>
              <div><Label className="text-xs uppercase">Interfaces ({(selected.interfaces || []).length})</Label>
                <div className="border rounded mt-1 max-h-60 overflow-y-auto">
                  <table className="w-full text-xs"><thead className="bg-muted"><tr><th className="p-2 text-left">Name</th><th className="p-2 text-left">MAC</th><th className="p-2 text-left">Speed</th><th className="p-2 text-left">Status</th></tr></thead>
                    <tbody>{(selected.interfaces || []).map((i, idx) => <tr key={idx} className="border-t"><td className="p-2 font-mono">{i.name}</td><td className="p-2 font-mono">{i.mac}</td><td className="p-2">{i.speed}</td><td className="p-2">{i.oper_status}</td></tr>)}</tbody>
                  </table>
                </div>
              </div>
              <div><Label className="text-xs uppercase">Neighbors ({(selected.neighbors || []).length})</Label>
                <ul className="text-xs mt-1">{(selected.neighbors || []).map((n, i) => <li key={i} className="p-2 border rounded mb-1">{n.local_port} ↔ <strong>{n.remote_system_name}</strong>:{n.remote_port}</li>)}</ul>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
