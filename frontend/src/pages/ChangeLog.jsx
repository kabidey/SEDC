import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

export default function ChangeLog() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState('');
  const load = async () => {
    const { data } = await api.get(`/changelog?limit=200`);
    setItems(data.results || []);
  };
  useEffect(() => { load(); }, []);
  const filtered = items.filter((i) => !q || (i.object_type + ' ' + (i.object_repr || '') + ' ' + i.username).toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Change Log</h1>
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter" className="w-64" />
      </div>
      <Card><CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 border-b">
            <tr>
              <th className="p-3 text-left">Action</th>
              <th className="p-3 text-left">Type</th>
              <th className="p-3 text-left">Object</th>
              <th className="p-3 text-left">User</th>
              <th className="p-3 text-left">Time</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.id} className="border-b last:border-0">
                <td className="p-3"><Badge variant={c.action === 'delete' ? 'destructive' : c.action === 'create' ? 'default' : 'secondary'} className="capitalize">{c.action}</Badge></td>
                <td className="p-3 font-mono text-xs">{c.object_type}</td>
                <td className="p-3">{c.object_repr || c.object_id}</td>
                <td className="p-3">{c.username}</td>
                <td className="p-3 text-xs text-muted-foreground">{c.time?.slice(0, 19).replace('T', ' ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent></Card>
    </div>
  );
}
