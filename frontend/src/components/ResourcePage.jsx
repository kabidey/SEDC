import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useNavigate, useParams, useLocation, Link } from 'react-router-dom';
import api, { API_BASE } from '../lib/api';
import { RESOURCES, getDefaultColumns } from '../lib/resources';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { Pencil, Trash2, Plus, Download, Upload, ArrowLeft, RefreshCw, Filter } from 'lucide-react';
import { toast } from 'sonner';

function FKField({ field, value, onChange }) {
  const [options, setOptions] = useState([]);
  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/${field.fk.resource}?limit=500`);
        setOptions(data.results || []);
      } catch (e) {}
    })();
  }, [field.fk.resource]);
  return (
    <Select value={value || '__none__'} onValueChange={(v) => onChange(v === '__none__' ? null : v)}>
      <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
      <SelectContent>
        <SelectItem value="__none__">— None —</SelectItem>
        {options.map((o) => (
          <SelectItem key={o.id} value={o.id}>{o[field.fk.displayField] || o.name || o.id}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function EntityField({ field, value, onChange }) {
  if (field.type === 'fk') return <FKField field={field} value={value} onChange={onChange} />;
  if (field.type === 'select') return (
    <Select value={value ?? '__none__'} onValueChange={(v) => onChange(v === '__none__' ? '' : v)}>
      <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
      <SelectContent>
        {(field.options || []).map((o) => (
          <SelectItem key={o || '__none__'} value={o || '__none__'}>{o || '— None —'}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
  if (field.type === 'textarea') return <Textarea value={value || ''} onChange={(e) => onChange(e.target.value)} rows={3} />;
  if (field.type === 'number') return <Input type="number" value={value ?? ''} onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))} />;
  if (field.type === 'boolean') return <div className="flex items-center gap-2 h-9"><Switch checked={!!value} onCheckedChange={onChange} /><span className="text-sm text-muted-foreground">{value ? 'Enabled' : 'Disabled'}</span></div>;
  if (field.type === 'color') return <div className="flex items-center gap-2"><input type="color" value={`#${value || '10b981'}`} onChange={(e) => onChange(e.target.value.replace('#', ''))} className="w-12 h-9 rounded border" /><Input value={value || ''} onChange={(e) => onChange(e.target.value.replace('#', ''))} placeholder="10b981" className="flex-1" /></div>;
  if (field.type === 'tags') {
    const arr = Array.isArray(value) ? value : [];
    return <Input value={arr.join(', ')} onChange={(e) => onChange(e.target.value.split(',').map((s) => s.trim()).filter(Boolean))} placeholder="tag1, tag2, ..." />;
  }
  if (field.type === 'json') {
    let str = '';
    if (value === null || value === undefined) str = '';
    else if (typeof value === 'string') str = value;
    else str = JSON.stringify(value, null, 2);
    return <Textarea value={str} onChange={(e) => { try { onChange(JSON.parse(e.target.value)); } catch { onChange(e.target.value); } }} rows={4} className="font-mono text-xs" />;
  }
  return <Input value={value ?? ''} onChange={(e) => onChange(e.target.value)} />;
}

function EntityForm({ schema, initial = {}, onSubmit, onCancel, submitting }) {
  const [data, setData] = useState(initial);
  useEffect(() => { setData(initial); }, [initial]);

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onSubmit(data); }}
      className="space-y-4"
      data-testid="entity-form"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {schema.fields.map((f) => (
          <div key={f.name} className={f.type === 'textarea' || f.type === 'json' ? 'md:col-span-2' : ''}>
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              {f.label || f.name}{f.required && <span className="text-destructive ml-1">*</span>}
            </Label>
            <div className="mt-1">
              <EntityField field={f} value={data[f.name]} onChange={(v) => setData({ ...data, [f.name]: v })} />
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-end gap-2 pt-4 border-t">
        {onCancel && <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>}
        <Button type="submit" disabled={submitting} data-testid="entity-form-submit">{submitting ? 'Saving...' : 'Save'}</Button>
      </div>
    </form>
  );
}

export function ListView({ resource }) {
  const schema = RESOURCES[resource];
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(0);
  const [limit] = useState(50);
  const [selected, setSelected] = useState(new Set());
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const columns = useMemo(() => getDefaultColumns(resource), [resource]);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
      if (q) params.set('q', q);
      const { data } = await api.get(`/${resource}?${params.toString()}`);
      setItems(data.results || []);
      setTotal(data.total || 0);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => d.msg || JSON.stringify(d)).join(', ') : e.message;
      toast.error(`Failed to load ${schema?.label || resource}: ${msg}`);
    }
    setLoading(false);
  }, [resource, q, page, limit, schema]);

  useEffect(() => { fetchItems(); }, [fetchItems]);
  useEffect(() => { setPage(0); setSelected(new Set()); }, [resource]);

  if (!schema) return <div className="p-6">Unknown resource: {resource}</div>;

  const handleCreate = async (formData) => {
    setCreating(true);
    try {
      await api.post(`/${resource}`, formData);
      toast.success(`${schema.label} created`);
      setCreateOpen(false);
      fetchItems();
    } catch (e) {
      toast.error(`Create failed: ${JSON.stringify(e?.response?.data?.detail || e.message)}`);
    }
    setCreating(false);
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/${resource}/${id}`);
      toast.success('Deleted');
      setConfirmDelete(null);
      fetchItems();
    } catch (e) { toast.error(`Delete failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const handleBulkDelete = async () => {
    if (!selected.size) return;
    try {
      await api.post(`/${resource}/bulk_delete`, { ids: Array.from(selected) });
      toast.success(`Deleted ${selected.size}`);
      setSelected(new Set());
      fetchItems();
    } catch (e) { toast.error(`Bulk delete failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const handleImport = async () => {
    if (!importFile) return;
    const fd = new FormData();
    fd.append('file', importFile);
    try {
      const { data } = await api.post(`/${resource}/import`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success(`Imported ${data.created} rows${data.errors?.length ? ` (${data.errors.length} errors)` : ''}`);
      setImportOpen(false);
      setImportFile(null);
      fetchItems();
    } catch (e) { toast.error(`Import failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const exportUrl = `${API_BASE}/${resource}/export`;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{schema.label}s</h1>
          <p className="text-sm text-muted-foreground">{total} {total === 1 ? schema.label.toLowerCase() : `${schema.label.toLowerCase()}s`} total</p>
        </div>
        <div className="flex items-center gap-2">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search" className="w-56" data-testid="list-search" />
          <Button variant="outline" size="sm" onClick={fetchItems}><RefreshCw size={14} /></Button>
          <Button variant="outline" size="sm" asChild>
            <a href={exportUrl} target="_blank" rel="noopener noreferrer"><Download size={14} className="mr-1" />Export</a>
          </Button>
          <Button variant="outline" size="sm" onClick={() => setImportOpen(true)}><Upload size={14} className="mr-1" />Import</Button>
          <Button size="sm" onClick={() => setCreateOpen(true)} data-testid="create-btn"><Plus size={14} className="mr-1" />Add {schema.label}</Button>
        </div>
      </div>

      {selected.size > 0 && (
        <div className="mb-3 p-3 bg-emerald-50 rounded-md border border-emerald-200 flex items-center gap-3">
          <span className="text-sm font-medium text-emerald-900">{selected.size} selected</span>
          <Button size="sm" variant="destructive" onClick={handleBulkDelete}><Trash2 size={14} className="mr-1" />Delete</Button>
          <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())}>Clear</Button>
        </div>
      )}

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 border-b">
              <tr>
                <th className="w-10 p-3 text-left">
                  <Checkbox
                    checked={items.length > 0 && selected.size === items.length}
                    onCheckedChange={(c) => setSelected(c ? new Set(items.map((i) => i.id)) : new Set())}
                  />
                </th>
                {columns.map((c) => (
                  <th key={c} className="p-3 text-left font-medium text-xs uppercase tracking-wider text-muted-foreground">{c.replace(/_/g, ' ').replace('id', 'ID')}</th>
                ))}
                <th className="p-3 text-right w-24">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={columns.length + 2} className="p-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={columns.length + 2} className="p-8 text-center text-muted-foreground">No {schema.label.toLowerCase()}s yet. Click "Add {schema.label}" to create one.</td></tr>
              ) : (
                items.map((it) => (
                  <tr key={it.id} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="p-3">
                      <Checkbox
                        checked={selected.has(it.id)}
                        onCheckedChange={(c) => {
                          const n = new Set(selected);
                          if (c) n.add(it.id); else n.delete(it.id);
                          setSelected(n);
                        }}
                      />
                    </td>
                    {columns.map((c) => (
                      <td key={c} className="p-3">
                        {c === columns[0] ? (
                          <Link to={`/${resource}/${it.id}`} className="font-medium text-emerald-700 hover:underline" data-testid={`detail-link-${it.id}`}>
                            {String(it[c] ?? '—')}
                          </Link>
                        ) : c === 'status' ? (
                          <Badge variant="secondary" className="capitalize">{it[c] || '—'}</Badge>
                        ) : c === 'tags' ? (
                          <div className="flex gap-1 flex-wrap">{(it[c] || []).map((t) => <Badge key={t} variant="outline" className="text-xs">{t}</Badge>)}</div>
                        ) : Array.isArray(it[c]) ? it[c].join(', ') : typeof it[c] === 'object' && it[c] !== null ? JSON.stringify(it[c]).slice(0, 40) : String(it[c] ?? '—').slice(0, 60)}
                      </td>
                    ))}
                    <td className="p-3 text-right">
                      <div className="flex justify-end gap-1">
                        <Button size="icon" variant="ghost" onClick={() => nav(`/${resource}/${it.id}`)}><Pencil size={14} /></Button>
                        <Button size="icon" variant="ghost" onClick={() => setConfirmDelete(it)}><Trash2 size={14} className="text-destructive" /></Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="p-3 border-t flex items-center justify-between">
            <div className="text-xs text-muted-foreground">Page {page + 1} of {totalPages}</div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>Previous</Button>
              <Button size="sm" variant="outline" disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</Button>
            </div>
          </div>
        )}
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create {schema.label}</DialogTitle>
            <DialogDescription>Fill in the fields below to add a new {schema.label.toLowerCase()}.</DialogDescription>
          </DialogHeader>
          <EntityForm schema={schema} initial={{}} onSubmit={handleCreate} onCancel={() => setCreateOpen(false)} submitting={creating} />
        </DialogContent>
      </Dialog>

      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Import {schema.label}s from CSV</DialogTitle>
            <DialogDescription>Upload a CSV file with headers matching {schema.label.toLowerCase()} fields.</DialogDescription>
          </DialogHeader>
          <Input type="file" accept=".csv" onChange={(e) => setImportFile(e.target.files?.[0])} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setImportOpen(false)}>Cancel</Button>
            <Button onClick={handleImport} disabled={!importFile}>Import</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!confirmDelete} onOpenChange={(o) => !o && setConfirmDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {schema.label}?</AlertDialogTitle>
            <AlertDialogDescription>This will permanently remove this item and record the change in the audit log.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => handleDelete(confirmDelete?.id)}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export function DetailView({ resource }) {
  const { id } = useParams();
  const nav = useNavigate();
  const schema = RESOURCES[resource];
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changes, setChanges] = useState([]);
  const [journal, setJournal] = useState([]);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/${resource}/${id}`);
        setItem(data);
      } catch (e) {
        toast.error('Item not found');
        nav(`/${resource}`);
      }
      setLoading(false);
    })();
    (async () => {
      try {
        const { data } = await api.get(`/changelog?object_id=${id}&limit=20`);
        setChanges(data.results || []);
      } catch {}
    })();
    (async () => {
      try {
        const { data } = await api.get(`/journal-entries?limit=100`);
        setJournal((data.results || []).filter((j) => j.assigned_object_id === id));
      } catch {}
    })();
  }, [resource, id]);

  if (!schema) return <div className="p-6">Unknown resource: {resource}</div>;
  if (loading) return <div className="p-6">Loading...</div>;
  if (!item) return null;

  const handleSave = async (formData) => {
    setSaving(true);
    try {
      const { data } = await api.patch(`/${resource}/${id}`, formData);
      setItem(data);
      toast.success('Saved');
    } catch (e) {
      toast.error(`Save failed: ${e?.response?.data?.detail || e.message}`);
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/${resource}/${id}`);
      toast.success('Deleted');
      nav(`/${resource}`);
    } catch (e) { toast.error(`Delete failed: ${e?.response?.data?.detail || e.message}`); }
  };

  const title = item[schema.titleField] || item.name || item.id;
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button size="icon" variant="ghost" onClick={() => nav(`/${resource}`)}><ArrowLeft size={16} /></Button>
          <div>
            <div className="text-xs text-muted-foreground uppercase tracking-wider">{schema.label}</div>
            <h1 className="text-2xl font-bold tracking-tight">{String(title)}</h1>
          </div>
        </div>
        <Button variant="destructive" size="sm" onClick={() => setConfirmDelete(true)}><Trash2 size={14} className="mr-1" />Delete</Button>
      </div>
      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="raw">Raw</TabsTrigger>
          <TabsTrigger value="changelog">Change Log ({changes.length})</TabsTrigger>
          <TabsTrigger value="journal">Journal ({journal.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="details" className="mt-4">
          <Card>
            <CardContent className="p-6">
              <EntityForm schema={schema} initial={item} onSubmit={handleSave} submitting={saving} />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="raw" className="mt-4">
          <Card><CardContent className="p-4"><pre className="text-xs overflow-x-auto whitespace-pre-wrap">{JSON.stringify(item, null, 2)}</pre></CardContent></Card>
        </TabsContent>
        <TabsContent value="changelog" className="mt-4">
          <Card>
            <CardContent className="p-4">
              {changes.length === 0 ? <p className="text-sm text-muted-foreground">No changes recorded.</p> : (
                <ul className="divide-y">
                  {changes.map((c) => (
                    <li key={c.id} className="py-2 flex items-center gap-3 text-sm">
                      <Badge variant={c.action === 'delete' ? 'destructive' : 'secondary'} className="capitalize">{c.action}</Badge>
                      <span className="text-muted-foreground">{c.username}</span>
                      <span className="flex-1" />
                      <span className="text-xs text-muted-foreground">{c.time?.slice(0, 19).replace('T', ' ')}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="journal" className="mt-4">
          <JournalSection objectType={schema.label.toLowerCase().replace(/\s/g, '-')} objectId={id} entries={journal} onAdded={async () => {
            const { data } = await api.get(`/journal-entries?limit=100`);
            setJournal((data.results || []).filter((j) => j.assigned_object_id === id));
          }} />
        </TabsContent>
      </Tabs>

      <AlertDialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this {schema.label}?</AlertDialogTitle>
            <AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function JournalSection({ objectType, objectId, entries, onAdded }) {
  const [comment, setComment] = useState('');
  const [kind, setKind] = useState('info');
  const submit = async () => {
    if (!comment.trim()) return;
    try {
      await api.post('/journal-entries', { assigned_object_type: objectType, assigned_object_id: objectId, kind, comments: comment });
      setComment('');
      toast.success('Journal entry added');
      onAdded?.();
    } catch (e) { toast.error('Add failed'); }
  };
  return (
    <Card><CardContent className="p-4 space-y-3">
      <div className="flex gap-2">
        <Select value={kind} onValueChange={setKind}>
          <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="info">Info</SelectItem>
            <SelectItem value="success">Success</SelectItem>
            <SelectItem value="warning">Warning</SelectItem>
            <SelectItem value="danger">Danger</SelectItem>
          </SelectContent>
        </Select>
        <Input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add a note…" className="flex-1" />
        <Button onClick={submit}>Add</Button>
      </div>
      {entries.length === 0 ? <p className="text-sm text-muted-foreground">No journal entries yet.</p> : (
        <ul className="space-y-2">
          {entries.map((j) => (
            <li key={j.id} className="p-3 border rounded text-sm">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className="capitalize">{j.kind}</Badge>
                <span className="text-xs text-muted-foreground">{j.created?.slice(0, 19).replace('T', ' ')}</span>
              </div>
              <p>{j.comments}</p>
            </li>
          ))}
        </ul>
      )}
    </CardContent></Card>
  );
}
