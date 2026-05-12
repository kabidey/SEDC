import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { Plus, Trash2, Pencil, Bell, RotateCw } from 'lucide-react';

const CONDITIONS = [
  { value: 'down', label: 'Monitor is down (critical/unknown)' },
  { value: 'warning_or_worse', label: 'Status is warning or worse' },
  { value: 'status_change', label: 'Status moves off OK' },
  { value: 'latency_above', label: 'Latency above threshold (ms)' },
  { value: 'loss_above', label: 'Packet loss above threshold (%)' },
];
const SEVERITY = ['info', 'warning', 'critical'];

const SEV_BG = {
  critical: 'bg-rose-600 text-white',
  warning: 'bg-amber-500 text-white',
  info: 'bg-emerald-600 text-white',
};

const defaultForm = () => ({
  name: '', monitor_id: '', condition: 'down', threshold: '', duration_seconds: 0,
  severity: 'critical', channels: [], enabled: true, description: '',
});

export default function AlertRules() {
  const [rules, setRules] = useState([]);
  const [monitors, setMonitors] = useState([]);
  const [channels, setChannels] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(defaultForm());

  const load = async () => {
    try {
      const [r, m, c] = await Promise.all([
        api.get('/monitoring/rules'),
        api.get('/monitoring/monitors?limit=500'),
        api.get('/monitoring/channels'),
      ]);
      setRules(r.data.results || []);
      setMonitors(m.data.results || []);
      setChannels(c.data.results || []);
    } catch (e) { toast.error('Failed to load rules'); }
  };
  useEffect(() => { load(); }, []);

  const openCreate = () => { setEditing(null); setForm(defaultForm()); setOpen(true); };
  const openEdit = (r) => { setEditing(r); setForm({ ...defaultForm(), ...r, threshold: r.threshold ?? '' }); setOpen(true); };

  const save = async () => {
    const payload = {
      ...form,
      monitor_id: form.monitor_id || null,
      threshold: form.threshold === '' || form.threshold == null ? null : Number(form.threshold),
      duration_seconds: Number(form.duration_seconds) || 0,
    };
    try {
      if (editing) await api.patch(`/monitoring/rules/${editing.id}`, payload);
      else await api.post('/monitoring/rules', payload);
      toast.success(`Rule ${editing ? 'updated' : 'created'}`);
      setOpen(false); load();
    } catch (e) { toast.error('Save failed: ' + (e?.response?.data?.detail || e.message)); }
  };
  const remove = async (id) => { if (!window.confirm('Delete rule?')) return; try { await api.delete(`/monitoring/rules/${id}`); toast.success('Deleted'); load(); } catch { toast.error('Delete failed'); } };

  const monName = (id) => id ? (monitors.find((m) => m.id === id)?.name || id) : 'All monitors';
  const chanName = (id) => channels.find((c) => c.id === id)?.name || id;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2"><Bell size={22} className="text-emerald-600" />Alert Rules</h1>
          <p className="text-sm text-muted-foreground mt-1">Define when a monitor result should fire an alert.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={load}><RotateCw size={14} className="mr-1" />Refresh</Button>
          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={openCreate} data-testid="rule-create-button"><Plus size={14} className="mr-1" />New Rule</Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr className="text-left">
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Severity</th>
                <th className="px-3 py-2 font-medium">Monitor</th>
                <th className="px-3 py-2 font-medium">Condition</th>
                <th className="px-3 py-2 font-medium">Threshold</th>
                <th className="px-3 py-2 font-medium">Duration</th>
                <th className="px-3 py-2 font-medium">Channels</th>
                <th className="px-3 py-2 font-medium">Enabled</th>
                <th className="px-3 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody data-testid="rule-table">
              {rules.length === 0 ? <tr><td colSpan={9} className="text-center py-10 text-muted-foreground">No alert rules yet.</td></tr> : rules.map((r) => (
                <tr key={r.id} className="border-t border-border hover:bg-muted/40">
                  <td className="px-3 py-2 font-medium">{r.name}</td>
                  <td className="px-3 py-2"><Badge className={`${SEV_BG[r.severity]} text-[10px] uppercase`}>{r.severity}</Badge></td>
                  <td className="px-3 py-2">{monName(r.monitor_id)}</td>
                  <td className="px-3 py-2 text-xs">{r.condition}</td>
                  <td className="px-3 py-2">{r.threshold ?? '—'}</td>
                  <td className="px-3 py-2">{r.duration_seconds ? `${r.duration_seconds}s` : '—'}</td>
                  <td className="px-3 py-2 text-xs">{(r.channels || []).map(chanName).join(', ') || 'in-app'}</td>
                  <td className="px-3 py-2"><Badge variant={r.enabled ? 'default' : 'outline'} className={r.enabled ? 'bg-emerald-600' : ''}>{r.enabled ? 'On' : 'Off'}</Badge></td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1 justify-end">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(r)} data-testid={`rule-edit-${r.id}`}><Pencil size={14} /></Button>
                      <Button variant="ghost" size="sm" onClick={() => remove(r.id)} data-testid={`rule-delete-${r.id}`}><Trash2 size={14} className="text-rose-600" /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Rule' : 'New Rule'}</DialogTitle>
            <DialogDescription>Rules turn check results into actionable alerts.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>Name</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="rule-form-name" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Monitor scope</Label>
                <Select value={form.monitor_id || '__all__'} onValueChange={(v) => setForm({ ...form, monitor_id: v === '__all__' ? '' : v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">All monitors</SelectItem>
                    {monitors.map((m) => <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Severity</Label>
                <Select value={form.severity} onValueChange={(v) => setForm({ ...form, severity: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{SEVERITY.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>Condition</Label>
              <Select value={form.condition} onValueChange={(v) => setForm({ ...form, condition: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{CONDITIONS.map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Threshold (for latency/loss conditions)</Label>
                <Input type="number" value={form.threshold} onChange={(e) => setForm({ ...form, threshold: e.target.value })} />
              </div>
              <div>
                <Label>Min. duration (sec)</Label>
                <Input type="number" value={form.duration_seconds} onChange={(e) => setForm({ ...form, duration_seconds: e.target.value })} />
              </div>
            </div>
            <div>
              <Label>Notification channels</Label>
              <div className="border border-border rounded p-2 max-h-40 overflow-y-auto space-y-1">
                {channels.length === 0 ? <div className="text-xs text-muted-foreground p-2">No channels yet — create some on the Channels page. Without channels, alerts will still be visible in-app.</div> : channels.map((c) => (
                  <label key={c.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/40 px-1 py-1 rounded">
                    <Checkbox checked={form.channels.includes(c.id)} onCheckedChange={(checked) => {
                      const next = checked ? [...form.channels, c.id] : form.channels.filter((x) => x !== c.id);
                      setForm({ ...form, channels: next });
                    }} />
                    <span className="font-medium">{c.name}</span>
                    <Badge variant="outline" className="text-[10px] uppercase">{c.type}</Badge>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Switch checked={form.enabled} onCheckedChange={(v) => setForm({ ...form, enabled: v })} id="rule-enabled" />
              <Label htmlFor="rule-enabled" className="cursor-pointer">Enabled</Label>
            </div>
            <div>
              <Label>Description</Label>
              <Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={save} data-testid="rule-save">{editing ? 'Save' : 'Create'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
