import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Trash2, Plus } from 'lucide-react';

export function UsersAdmin() {
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', email: '', first_name: '', last_name: '', is_admin: false, is_active: true });
  const load = async () => { const { data } = await api.get('/users'); setUsers(data.results || []); };
  useEffect(() => { load(); }, []);
  const create = async () => {
    try { await api.post('/users', form); toast.success('User created'); setOpen(false); setForm({ username: '', password: '', email: '', first_name: '', last_name: '', is_admin: false, is_active: true }); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
  };
  const del = async (id) => { try { await api.delete(`/users/${id}`); load(); } catch {} };
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Users</h1>
        <Button onClick={() => setOpen(true)}><Plus size={14} className="mr-1" />Add User</Button>
      </div>
      <Card><CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b"><tr><th className="p-3 text-left">Username</th><th className="p-3 text-left">Name</th><th className="p-3 text-left">Email</th><th className="p-3 text-left">Admin</th><th className="p-3 text-left">Active</th><th className="p-3"></th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b last:border-0">
                <td className="p-3 font-medium">{u.username}</td>
                <td className="p-3">{u.first_name} {u.last_name}</td>
                <td className="p-3">{u.email}</td>
                <td className="p-3">{u.is_admin && <Badge>admin</Badge>}</td>
                <td className="p-3">{u.is_active ? <Badge variant="secondary">active</Badge> : <Badge variant="destructive">inactive</Badge>}</td>
                <td className="p-3 text-right"><Button size="icon" variant="ghost" onClick={() => del(u.id)}><Trash2 size={14} className="text-destructive" /></Button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent></Card>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Create User</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label>Username</Label><Input value={form.username} onChange={(e) => setForm({...form, username: e.target.value})} /></div>
            <div><Label>Password</Label><Input type="password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} /></div>
            <div><Label>Email</Label><Input value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><Label>First Name</Label><Input value={form.first_name} onChange={(e) => setForm({...form, first_name: e.target.value})} /></div>
              <div><Label>Last Name</Label><Input value={form.last_name} onChange={(e) => setForm({...form, last_name: e.target.value})} /></div>
            </div>
            <div className="flex items-center gap-3"><Switch checked={form.is_admin} onCheckedChange={(v) => setForm({...form, is_admin: v})} /><Label>Admin</Label></div>
            <div className="flex items-center gap-3"><Switch checked={form.is_active} onCheckedChange={(v) => setForm({...form, is_active: v})} /><Label>Active</Label></div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={create}>Create</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function GroupsAdmin() {
  const [groups, setGroups] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });
  const load = async () => { const { data } = await api.get('/groups'); setGroups(data.results || []); };
  useEffect(() => { load(); }, []);
  const create = async () => { try { await api.post('/groups', form); toast.success('Created'); setOpen(false); setForm({ name: '', description: '' }); load(); } catch (e) { toast.error('Failed'); } };
  const del = async (id) => { await api.delete(`/groups/${id}`); load(); };
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4"><h1 className="text-2xl font-bold">Groups</h1><Button onClick={() => setOpen(true)}><Plus size={14} className="mr-1" />Add Group</Button></div>
      <Card><CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b"><tr><th className="p-3 text-left">Name</th><th className="p-3 text-left">Description</th><th className="p-3"></th></tr></thead>
          <tbody>{groups.map((g) => <tr key={g.id} className="border-b last:border-0"><td className="p-3 font-medium">{g.name}</td><td className="p-3">{g.description}</td><td className="p-3 text-right"><Button size="icon" variant="ghost" onClick={() => del(g.id)}><Trash2 size={14} className="text-destructive" /></Button></td></tr>)}</tbody>
        </table>
      </CardContent></Card>
      <Dialog open={open} onOpenChange={setOpen}><DialogContent><DialogHeader><DialogTitle>Create Group</DialogTitle></DialogHeader><div className="space-y-3"><div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} /></div><div><Label>Description</Label><Input value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} /></div></div><DialogFooter><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={create}>Create</Button></DialogFooter></DialogContent></Dialog>
    </div>
  );
}

export function ApiTokensAdmin() {
  const [tokens, setTokens] = useState([]);
  const [open, setOpen] = useState(false);
  const [desc, setDesc] = useState('');
  const load = async () => { const { data } = await api.get('/api-tokens'); setTokens(data.results || []); };
  useEffect(() => { load(); }, []);
  const create = async () => { try { const { data } = await api.post('/api-tokens', { description: desc, write_enabled: true }); toast.success('Token created'); setOpen(false); setDesc(''); load(); } catch (e) { toast.error('Failed'); } };
  const del = async (id) => { await api.delete(`/api-tokens/${id}`); load(); };
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4"><h1 className="text-2xl font-bold">API Tokens</h1><Button onClick={() => setOpen(true)}><Plus size={14} className="mr-1" />Add Token</Button></div>
      <Card><CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b"><tr><th className="p-3 text-left">Key</th><th className="p-3 text-left">Description</th><th className="p-3 text-left">Created</th><th className="p-3"></th></tr></thead>
          <tbody>{tokens.map((t) => <tr key={t.id} className="border-b last:border-0"><td className="p-3 font-mono text-xs">{t.key}</td><td className="p-3">{t.description}</td><td className="p-3 text-xs text-muted-foreground">{t.created?.slice(0, 19)}</td><td className="p-3 text-right"><Button size="icon" variant="ghost" onClick={() => del(t.id)}><Trash2 size={14} className="text-destructive" /></Button></td></tr>)}</tbody>
        </table>
      </CardContent></Card>
      <Dialog open={open} onOpenChange={setOpen}><DialogContent><DialogHeader><DialogTitle>Create API Token</DialogTitle></DialogHeader><div><Label>Description</Label><Input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="e.g. CI/CD" /></div><DialogFooter><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={create}>Create</Button></DialogFooter></DialogContent></Dialog>
    </div>
  );
}
