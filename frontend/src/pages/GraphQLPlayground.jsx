import React, { useState } from 'react';
import api, { API_BASE } from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import axios from 'axios';

const SAMPLES = [
  `{ collections }`,
  `{ collection(name: "sites", limit: 5) { id data } }`,
  `{ collection(name: "devices", limit: 10, q: "router") { id data } }`,
];

export default function GraphQLPlayground() {
  const [q, setQ] = useState(SAMPLES[1]);
  const [out, setOut] = useState('');
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API_BASE}/graphql`, { query: q }, { headers: { Authorization: `Bearer ${localStorage.getItem('smifs_token')}` } });
      setOut(JSON.stringify(data, null, 2));
    } catch (e) { setOut(JSON.stringify(e?.response?.data || { error: e.message }, null, 2)); }
    setLoading(false);
  };
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">GraphQL Playground</h1>
      <p className="text-sm text-muted-foreground mb-4">Endpoint: <code className="bg-muted px-2 py-0.5 rounded">{API_BASE}/graphql</code></p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card><CardContent className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <Label>Query</Label>
            <div className="flex gap-1">{SAMPLES.map((s, i) => <Button key={i} variant="outline" size="sm" onClick={() => setQ(s)}>Sample {i + 1}</Button>)}</div>
          </div>
          <Textarea value={q} onChange={(e) => setQ(e.target.value)} rows={14} className="font-mono text-xs" />
          <Button onClick={run} disabled={loading}>{loading ? 'Running...' : 'Run Query'}</Button>
        </CardContent></Card>
        <Card><CardContent className="p-4">
          <Label className="mb-2 block">Response</Label>
          <pre className="font-mono text-xs whitespace-pre-wrap break-all bg-muted/40 p-3 rounded h-[440px] overflow-auto">{out || '— run a query —'}</pre>
        </CardContent></Card>
      </div>
    </div>
  );
}
