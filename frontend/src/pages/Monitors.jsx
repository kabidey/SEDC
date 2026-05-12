import React, { useEffect, useMemo, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { Plus, Play, Trash2, Pencil, Radio, Activity, RotateCw, ExternalLink } from 'lucide-react';

const TYPES = [
  { value: 'icmp', label: 'ICMP (Ping)' },
  { value: 'tcp', label: 'TCP Port' },
  { value: 'http', label: 'HTTP' },
  { value: 'https', label: 'HTTPS' },
  { value: 'dns', label: 'DNS' },
  { value: 'snmp', label: 'SNMP' },
];

const STATUS_STYLES = {
  ok: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  warning: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  critical: 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
  unknown: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
};

const defaultForm = () => ({
  name: '',
  type: 'icmp',
  target: '',
  url: '',
  port: 80,
  http_method: 'GET',
  expected_status: 200,
  expected_text: '',
  verify_ssl: true,
  oid: '1.3.6.1.2.1.1.3.0',
  community: 'public',
  record_type: 'A',
  interval_seconds: 30,
  timeout_seconds: 5,
  icmp_count: 3,
  retry: 1,
  enabled: true,
  description: '',
  thresholds: { latency_warn_ms: '', latency_crit_ms: '', loss_warn_pct: '', loss_crit_pct: '' },
});

export default function Monitors() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(defaultForm());
  const [metricsFor, setMetricsFor] = useState(null);
  const [metrics, setMetrics] = useState([]);

  const load = async () => {
    try {
      const { data } = await api.get(`/monitoring/monitors?q=${encodeURIComponent(q)}&limit=500`);
      setItems(data.results || []);
    } catch (e) { toast.error('Failed to load monitors'); }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { const t = setInterval(load, 10000); return () => clearInterval(t); }, []);

  const filtered = useMemo(() => {
    if (!q) return items;
    const k = q.toLowerCase();
    return items.filter((m) => (m.name || '').toLowerCase().includes(k) || (m.target || '').toLowerCase().includes(k) || (m.url || '').toLowerCase().includes(k));
  }, [items, q]);

  const openCreate = () => { setEditing(null); setForm(defaultForm()); setOpen(true); };
  const openEdit = (m) => {
    setEditing(m);
    setForm({
      ...defaultForm(),
      ...m,
      thresholds: { ...defaultForm().thresholds, ...(m.thresholds || {}) },
    });
    setOpen(true);
  };

  const save = async () => {
    try {
      const payload = {
        ...form,
        port: Number(form.port) || 80,
        interval_seconds: Math.max(5, Number(form.interval_seconds) || 30),
        timeout_seconds: Math.max(1, Number(form.timeout_seconds) || 5),
        icmp_count: Math.max(1, Number(form.icmp_count) || 3),
        retry: Math.max(1, Number(form.retry) || 1),
        thresholds: Object.fromEntries(Object.entries(form.thresholds || {}).map(([k, v]) => [k, v === '' || v == null ? null : Number(v)])),
      };
      if (editing) await api.patch(`/monitoring/monitors/${editing.id}`, payload);
      else await api.post('/monitoring/monitors', payload);
      toast.success(`Monitor ${editing ? 'updated' : 'created'}`);
      setOpen(false);
      load();
    } catch (e) { toast.error('Save failed: ' + (e?.response?.data?.detail || e.message)); }
  };

  const remove = async (id) => {
    if (!window.confirm('Delete this monitor?')) return;
    try { await api.delete(`/monitoring/monitors/${id}`); toast.success('Deleted'); load(); }
    catch (e) { toast.error('Delete failed'); }
  };

  const runNow = async (id) => {
    try { await api.post(`/monitoring/monitors/${id}/run`); toast.success('Run triggered'); load(); }
    catch (e) { toast.error('Run failed'); }
  };

  const showMetrics = async (m) => {
    setMetricsFor(m);
    try {
      const { data } = await api.get(`/monitoring/monitors/${m.id}/metrics?hours=2&limit=200`);
      setMetrics(data.results || []);
    } catch (e) { setMetrics([]); }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2"><Radio size={22} className="text-emerald-600" />Monitors</h1>
          <p className="text-sm text-muted-foreground mt-1">Define what to monitor: hosts, ports, URLs, SNMP, and DNS.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={load}><RotateCw size={14} className="mr-1" />Refresh</Button>
          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={openCreate} data-testid="monitor-create-button"><Plus size={14} className="mr-1" />New Monitor</Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-3">
          <Input placeholder="Search by name or target..." value={q} onChange={(e) => setQ(e.target.value)} className="max-w-sm" data-testid="monitor-search" />
        </CardContent>
      </Card>

      <Card className="mt-3">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr className="text-left">
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Name</th>
                  <th className="px-3 py-2 font-medium">Type</th>
                  <th className="px-3 py-2 font-medium">Target</th>
                  <th className="px-3 py-2 font-medium">Latency</th>
                  <th className="px-3 py-2 font-medium">Loss</th>
                  <th className="px-3 py-2 font-medium">Interval</th>
                  <th className="px-3 py-2 font-medium">Last check</th>
                  <th className="px-3 py-2 font-medium">Enabled</th>
                  <th className="px-3 py-2 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody data-testid="monitor-table">
                {filtered.length === 0 ? (
                  <tr><td colSpan={10} className="text-center py-10 text-muted-foreground">No monitors. Click <strong>New Monitor</strong> to add one.</td></tr>
                ) : filtered.map((m) => (
                  <tr key={m.id} className="border-t border-border hover:bg-muted/40">
                    <td className="px-3 py-2"><Badge className={`${STATUS_STYLES[m.current_status] || STATUS_STYLES.unknown} uppercase text-[10px]`}>{m.current_status || 'unknown'}</Badge></td>
                    <td className="px-3 py-2 font-medium">{m.name}</td>
                    <td className="px-3 py-2"><Badge variant="outline" className="uppercase text-[10px]">{m.type}</Badge></td>
                    <td className="px-3 py-2 truncate max-w-[260px]" title={m.target || m.url}>{m.target || m.url || '—'}{m.type === 'tcp' ? `:${m.port}` : ''}</td>
                    <td className="px-3 py-2">{m.last_latency_ms != null ? `${m.last_latency_ms} ms` : '—'}</td>
                    <td className="px-3 py-2">{m.last_loss_pct != null ? `${m.last_loss_pct}%` : '—'}</td>
                    <td className="px-3 py-2">{m.interval_seconds}s</td>
                    <td className="px-3 py-2 text-xs">{m.last_check_at ? new Date(m.last_check_at).toLocaleTimeString() : 'never'}</td>
                    <td className="px-3 py-2"><Badge variant={m.enabled ? 'default' : 'outline'} className={m.enabled ? 'bg-emerald-600' : ''}>{m.enabled ? 'On' : 'Off'}</Badge></td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1 justify-end">
                        <Button variant="ghost" size="sm" onClick={() => runNow(m.id)} data-testid={`monitor-run-${m.id}`}><Play size={14} /></Button>
                        <Button variant="ghost" size="sm" onClick={() => showMetrics(m)} data-testid={`monitor-metrics-${m.id}`}><Activity size={14} /></Button>
                        <Button variant="ghost" size="sm" onClick={() => openEdit(m)} data-testid={`monitor-edit-${m.id}`}><Pencil size={14} /></Button>
                        <Button variant="ghost" size="sm" onClick={() => remove(m.id)} data-testid={`monitor-delete-${m.id}`}><Trash2 size={14} className="text-rose-600" /></Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Create / edit dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Monitor' : 'New Monitor'}</DialogTitle>
            <DialogDescription>Configure check type, target, and thresholds.</DialogDescription>
          </DialogHeader>
          <Tabs defaultValue="basics">
            <TabsList>
              <TabsTrigger value="basics">Basics</TabsTrigger>
              <TabsTrigger value="target">Target</TabsTrigger>
              <TabsTrigger value="thresholds">Thresholds</TabsTrigger>
            </TabsList>
            <TabsContent value="basics" className="space-y-3 pt-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Name</Label>
                  <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. core-router-01" data-testid="monitor-form-name" />
                </div>
                <div>
                  <Label>Type</Label>
                  <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                    <SelectTrigger data-testid="monitor-form-type"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label>Interval (sec)</Label>
                  <Input type="number" value={form.interval_seconds} onChange={(e) => setForm({ ...form, interval_seconds: e.target.value })} />
                </div>
                <div>
                  <Label>Timeout (sec)</Label>
                  <Input type="number" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: e.target.value })} />
                </div>
                <div>
                  <Label>Retries</Label>
                  <Input type="number" value={form.retry} onChange={(e) => setForm({ ...form, retry: e.target.value })} />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Switch checked={form.enabled} onCheckedChange={(v) => setForm({ ...form, enabled: v })} id="mon-enabled" />
                <Label htmlFor="mon-enabled" className="cursor-pointer">Enabled</Label>
              </div>
              <div>
                <Label>Description</Label>
                <Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
            </TabsContent>
            <TabsContent value="target" className="space-y-3 pt-3">
              {form.type === 'http' || form.type === 'https' ? (
                <>
                  <div>
                    <Label>URL</Label>
                    <Input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} placeholder="https://example.com/health" />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <Label>Method</Label>
                      <Select value={form.http_method} onValueChange={(v) => setForm({ ...form, http_method: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {['GET', 'HEAD', 'POST', 'PUT'].map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Expected status</Label>
                      <Input type="number" value={form.expected_status} onChange={(e) => setForm({ ...form, expected_status: e.target.value })} />
                    </div>
                    <div className="flex items-end gap-2">
                      <Switch checked={form.verify_ssl} onCheckedChange={(v) => setForm({ ...form, verify_ssl: v })} id="verify-ssl" />
                      <Label htmlFor="verify-ssl" className="cursor-pointer pb-2">Verify SSL</Label>
                    </div>
                  </div>
                  <div>
                    <Label>Expected text (optional substring)</Label>
                    <Input value={form.expected_text || ''} onChange={(e) => setForm({ ...form, expected_text: e.target.value })} />
                  </div>
                </>
              ) : (
                <div>
                  <Label>Target (host or IP)</Label>
                  <Input value={form.target} onChange={(e) => setForm({ ...form, target: e.target.value })} placeholder="e.g. 10.0.0.1 or core-sw.smifs.local" />
                </div>
              )}
              {form.type === 'tcp' && (
                <div>
                  <Label>Port</Label>
                  <Input type="number" value={form.port} onChange={(e) => setForm({ ...form, port: e.target.value })} />
                </div>
              )}
              {form.type === 'icmp' && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>ICMP count (per check)</Label>
                    <Input type="number" value={form.icmp_count} onChange={(e) => setForm({ ...form, icmp_count: e.target.value })} />
                  </div>
                  <div className="text-xs text-muted-foreground pt-6">
                    ICMP requires raw sockets; if blocked, set up a TCP monitor for the same host.
                  </div>
                </div>
              )}
              {form.type === 'snmp' && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Community (v2c)</Label>
                    <Input value={form.community} onChange={(e) => setForm({ ...form, community: e.target.value })} />
                  </div>
                  <div>
                    <Label>OID</Label>
                    <Input value={form.oid} onChange={(e) => setForm({ ...form, oid: e.target.value })} />
                  </div>
                </div>
              )}
              {form.type === 'dns' && (
                <div>
                  <Label>Record type</Label>
                  <Select value={form.record_type} onValueChange={(v) => setForm({ ...form, record_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {['A', 'AAAA'].map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </TabsContent>
            <TabsContent value="thresholds" className="space-y-3 pt-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Latency warning (ms)</Label>
                  <Input type="number" value={form.thresholds.latency_warn_ms ?? ''} onChange={(e) => setForm({ ...form, thresholds: { ...form.thresholds, latency_warn_ms: e.target.value } })} />
                </div>
                <div>
                  <Label>Latency critical (ms)</Label>
                  <Input type="number" value={form.thresholds.latency_crit_ms ?? ''} onChange={(e) => setForm({ ...form, thresholds: { ...form.thresholds, latency_crit_ms: e.target.value } })} />
                </div>
                <div>
                  <Label>Loss warning (%)</Label>
                  <Input type="number" value={form.thresholds.loss_warn_pct ?? ''} onChange={(e) => setForm({ ...form, thresholds: { ...form.thresholds, loss_warn_pct: e.target.value } })} />
                </div>
                <div>
                  <Label>Loss critical (%)</Label>
                  <Input type="number" value={form.thresholds.loss_crit_pct ?? ''} onChange={(e) => setForm({ ...form, thresholds: { ...form.thresholds, loss_crit_pct: e.target.value } })} />
                </div>
              </div>
              <div className="text-xs text-muted-foreground">
                Thresholds promote an OK check to warning or critical when latency or loss exceed the configured value. Leave blank to ignore.
              </div>
            </TabsContent>
          </Tabs>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={save} data-testid="monitor-save">{editing ? 'Save' : 'Create'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Metrics dialog */}
      <Dialog open={!!metricsFor} onOpenChange={(o) => !o && setMetricsFor(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Activity size={18} className="text-emerald-600" />{metricsFor?.name} — Recent Metrics</DialogTitle>
            <DialogDescription>Last {metrics.length} samples (up to 2 hours)</DialogDescription>
          </DialogHeader>
          <div className="max-h-[60vh] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr className="text-left">
                  <th className="px-3 py-2">Time</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Latency</th>
                  <th className="px-3 py-2">Loss</th>
                  <th className="px-3 py-2">Error</th>
                </tr>
              </thead>
              <tbody>
                {metrics.length === 0 ? <tr><td colSpan={5} className="text-center py-6 text-muted-foreground">No samples yet</td></tr> : metrics.slice().reverse().map((s) => (
                  <tr key={s.id} className="border-t border-border">
                    <td className="px-3 py-2 font-mono text-xs">{new Date(s.time).toLocaleString()}</td>
                    <td className="px-3 py-2"><Badge className={`${STATUS_STYLES[s.status] || STATUS_STYLES.unknown} uppercase text-[10px]`}>{s.status}</Badge></td>
                    <td className="px-3 py-2">{s.latency_ms ?? '—'}</td>
                    <td className="px-3 py-2">{s.loss_pct ?? '—'}</td>
                    <td className="px-3 py-2 text-rose-600 text-xs">{s.error || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
