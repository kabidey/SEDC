import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';

export default function PrefixTree() {
  const [vrfs, setVrfs] = useState([]);
  const [vrfId, setVrfId] = useState('');
  const [tree, setTree] = useState([]);

  useEffect(() => { (async () => {
    const { data } = await api.get('/vrfs?limit=500');
    setVrfs(data.results || []);
  })(); }, []);
  useEffect(() => { (async () => {
    const url = vrfId ? `/prefix-tools/tree?vrf_id=${vrfId}` : '/prefix-tools/tree';
    const { data } = await api.get(url);
    setTree(data.results || []);
  })(); }, [vrfId]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Prefix Tree</h1>
      <div className="flex items-center gap-3 mb-4">
        <Label className="text-sm">VRF:</Label>
        <Select value={vrfId || '__all__'} onValueChange={(v) => setVrfId(v === '__all__' ? '' : v)}>
          <SelectTrigger className="w-72"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">All VRFs (Global)</SelectItem>
            {vrfs.map((v) => <SelectItem key={v.id} value={v.id}>{v.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <Card>
        <CardContent className="p-4">
          {tree.length === 0 ? <p className="text-sm text-muted-foreground">No prefixes.</p> : (
            <ul className="font-mono text-sm space-y-0.5">
              {tree.map((p) => (
                <li key={p.id} style={{ paddingLeft: (p.depth || 0) * 20 }} className="py-1 hover:bg-muted/30 rounded px-2 flex items-center gap-2">
                  <Link to={`/prefixes/${p.id}`} className="text-emerald-700 hover:underline font-medium">{p.prefix}</Link>
                  <Badge variant="outline" className="text-xs">{p.status}</Badge>
                  {p.is_pool && <Badge variant="secondary" className="text-xs">pool</Badge>}
                  <span className="text-muted-foreground text-xs">{p.description}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
