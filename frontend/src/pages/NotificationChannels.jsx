import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Plus, Trash2, Pencil, Mail, Send, Slack, MessageSquare, Inbox, RotateCw } from 'lucide-react';

const TYPES = [
  { value: 'email', label: 'Email (SMTP)', icon: Mail },
  { value: 'webhook', label: 'Generic Webhook', icon: Send },
  { value: 'slack', label: 'Slack', icon: Slack },
  { value: 'teams', label: 'Microsoft Teams', icon: MessageSquare },
  { value: 'inapp', label: 'In-app Only', icon: Inbox },
];

const defaultForm = () => ({
  name: '', type: 'email', enabled: true, description: '',
  config: {
    smtp_host: '', smtp_port: 587, username: '', password: '', from: '', to: '', use_tls: true, use_ssl: false,
    url: '', method: 'POST', headers: '', verify_ssl: true,
    webhook_url: '',
  },
});

export default function NotificationChannels() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(defaultForm());

  const load = async () => {
    try { const { data } = await api.get('/monitoring/channels'); setItems(data.results || []); }
    catch (e) { toast.error('Failed to load channels'); }
  };
  useEffect(() => { load(); }, []);

  const openCreate = () => { setEditing(null); setForm(defaultForm()); setOpen(true); };
  const openEdit = (c) => {
    setEditing(c);
    setForm({ ...defaultForm(), ...c, config: { ...defaultForm().config, ...(c.config || {}) } });
    setOpen(true);
  };

  const save = async () => {
    try {
      const payload = { ...form };
      // For webhook, store headers as object
      if (payload.type === 'webhook' && typeof payload.config.headers === 'string' && payload.config.headers.trim()) {
        try { payload.config = { ...payload.config, headers: JSON.parse(payload.config.headers) }; }
        catch { toast.error('Headers must be valid JSON'); return; }
      }
      if (editing) await api.patch(`/monitoring/channels/${editing.id}`, payload);
      else await api.post('/monitoring/channels', payload);
      toast.success(`Channel ${editing ? 'updated' : 'created'}`);
      setOpen(false); load();
    } catch (e) { toast.error('Save failed: ' + (e?.response?.data?.detail || e.message)); }
  };

  const remove = async (id) => {
    if (!window.confirm('Delete channel?')) return;
    try { await api.delete(`/monitoring/channels/${id}`); toast.success('Deleted'); load(); }
    catch { toast.error('Delete failed'); }
  };

  const testCh = async (id) => {
    try {
      const { data } = await api.post(`/monitoring/channels/${id}/test`);
      if (data.ok) toast.success('Test sent successfully');
      else toast.error(`Test failed: ${data.error || JSON.stringify(data).slice(0, 120)}`);
    } catch (e) { toast.error('Test failed: ' + (e?.response?.data?.detail || e.message)); }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2"><Send size={22} className="text-emerald-600" />Notification Channels</h1>
          <p className="text-sm text-muted-foreground mt-1">Where alerts should be sent: Email, Webhook, Slack, Teams, or in-app.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={load}><RotateCw size={14} className="mr-1" />Refresh</Button>
          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={openCreate} data-testid="channel-create-button"><Plus size={14} className="mr-1" />New Channel</Button>
        </div>
      </div>
      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr className="text-left">
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Type</th>
                <th className="px-3 py-2 font-medium">Target / Config</th>
                <th className="px-3 py-2 font-medium">Enabled</th>
                <th className="px-3 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody data-testid="channel-table">
              {items.length === 0 ? <tr><td colSpan={5} className="text-center py-10 text-muted-foreground">No channels yet.</td></tr> : items.map((c) => (
                <tr key={c.id} className="border-t border-border hover:bg-muted/40">
                  <td className="px-3 py-2 font-medium">{c.name}</td>
                  <td className="px-3 py-2"><Badge variant="outline" className="uppercase text-[10px]">{c.type}</Badge></td>
                  <td className="px-3 py-2 text-xs text-muted-foreground truncate max-w-[400px]">
                    {c.type === 'email' && `${c.config?.smtp_host}:${c.config?.smtp_port} → ${c.config?.to}`}
                    {c.type === 'webhook' && c.config?.url}
                    {(c.type === 'slack' || c.type === 'teams') && c.config?.webhook_url}
                    {c.type === 'inapp' && 'In-app notifications only'}
                  </td>
                  <td className="px-3 py-2"><Badge variant={c.enabled ? 'default' : 'outline'} className={c.enabled ? 'bg-emerald-600' : ''}>{c.enabled ? 'On' : 'Off'}</Badge></td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1 justify-end">
                      <Button variant="ghost" size="sm" onClick={() => testCh(c.id)} data-testid={`channel-test-${c.id}`}>Test</Button>
                      <Button variant="ghost" size="sm" onClick={() => openEdit(c)} data-testid={`channel-edit-${c.id}`}><Pencil size={14} /></Button>
                      <Button variant="ghost" size="sm" onClick={() => remove(c.id)} data-testid={`channel-delete-${c.id}`}><Trash2 size={14} className="text-rose-600" /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Channel' : 'New Channel'}</DialogTitle>
            <DialogDescription>Where do you want alerts delivered?</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Name</Label>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="channel-form-name" />
              </div>
              <div>
                <Label>Type</Label>
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                  <SelectTrigger data-testid="channel-form-type"><SelectValue /></SelectTrigger>
                  <SelectContent>{TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            {form.type === 'email' && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div><Label>SMTP host</Label><Input value={form.config.smtp_host} onChange={(e) => setForm({ ...form, config: { ...form.config, smtp_host: e.target.value } })} placeholder="smtp.smifs.com" /></div>
                  <div><Label>Port</Label><Input type="number" value={form.config.smtp_port} onChange={(e) => setForm({ ...form, config: { ...form.config, smtp_port: Number(e.target.value) } })} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><Label>Username</Label><Input value={form.config.username} onChange={(e) => setForm({ ...form, config: { ...form.config, username: e.target.value } })} /></div>
                  <div><Label>Password</Label><Input type="password" value={form.config.password || ''} onChange={(e) => setForm({ ...form, config: { ...form.config, password: e.target.value } })} /></div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><Label>From address</Label><Input value={form.config.from} onChange={(e) => setForm({ ...form, config: { ...form.config, from: e.target.value } })} placeholder="noc@smifs.com" /></div>
                  <div><Label>To (comma separated)</Label><Input value={form.config.to} onChange={(e) => setForm({ ...form, config: { ...form.config, to: e.target.value } })} placeholder="oncall@smifs.com,backup@smifs.com" /></div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2"><Switch checked={form.config.use_tls} onCheckedChange={(v) => setForm({ ...form, config: { ...form.config, use_tls: v } })} /><Label>STARTTLS</Label></div>
                  <div className="flex items-center gap-2"><Switch checked={form.config.use_ssl} onCheckedChange={(v) => setForm({ ...form, config: { ...form.config, use_ssl: v } })} /><Label>SSL/TLS</Label></div>
                </div>
              </>
            )}
            {form.type === 'webhook' && (
              <>
                <div><Label>Webhook URL</Label><Input value={form.config.url} onChange={(e) => setForm({ ...form, config: { ...form.config, url: e.target.value } })} placeholder="https://example.com/hook" /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>HTTP Method</Label>
                    <Select value={form.config.method} onValueChange={(v) => setForm({ ...form, config: { ...form.config, method: v } })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>{['POST', 'PUT', 'PATCH'].map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-end gap-2"><Switch checked={form.config.verify_ssl} onCheckedChange={(v) => setForm({ ...form, config: { ...form.config, verify_ssl: v } })} id="wb-vssl" /><Label htmlFor="wb-vssl" className="pb-2 cursor-pointer">Verify SSL</Label></div>
                </div>
                <div><Label>Headers (JSON, optional)</Label><Textarea rows={3} value={typeof form.config.headers === 'string' ? form.config.headers : JSON.stringify(form.config.headers || {}, null, 2)} onChange={(e) => setForm({ ...form, config: { ...form.config, headers: e.target.value } })} placeholder='{"Authorization":"Bearer ..."}' /></div>
              </>
            )}
            {(form.type === 'slack' || form.type === 'teams') && (
              <div><Label>{form.type === 'slack' ? 'Slack Incoming Webhook URL' : 'Teams Incoming Webhook URL'}</Label><Input value={form.config.webhook_url} onChange={(e) => setForm({ ...form, config: { ...form.config, webhook_url: e.target.value } })} /></div>
            )}
            {form.type === 'inapp' && (
              <div className="text-sm text-muted-foreground p-3 border border-dashed border-emerald-500/40 rounded">In-app channels only need a name. Alerts will appear on the NOC dashboard.</div>
            )}
            <div className="flex items-center gap-3">
              <Switch checked={form.enabled} onCheckedChange={(v) => setForm({ ...form, enabled: v })} id="ch-enabled" />
              <Label htmlFor="ch-enabled" className="cursor-pointer">Enabled</Label>
            </div>
            <div><Label>Description</Label><Textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={save} data-testid="channel-save">{editing ? 'Save' : 'Create'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
