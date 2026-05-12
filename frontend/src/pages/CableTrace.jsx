import React, { useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

const TERM_TYPES = ['interface', 'console-port', 'console-server-port', 'power-port', 'power-outlet', 'front-port', 'rear-port', 'circuit-termination', 'power-feed'];

export default function CableTrace() {
  const [type, setType] = useState('interface');
  const [id, setId] = useState('');
  const [path, setPath] = useState([]);
  const trace = async () => {
    if (!id) return;
    const { data } = await api.get(`/cables/trace/${type}/${id}`);
    setPath(data.path || []);
  };
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Cable Trace</h1>
      <Card><CardContent className="p-4 space-y-3">
        <div className="flex gap-2 items-end">
          <div>
            <Label className="text-xs uppercase">From Object Type</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger className="w-56"><SelectValue /></SelectTrigger>
              <SelectContent>{TERM_TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="flex-1">
            <Label className="text-xs uppercase">Object ID</Label>
            <Input value={id} onChange={(e) => setId(e.target.value)} placeholder="UUID" />
          </div>
          <Button onClick={trace}>Trace</Button>
        </div>
        {path.length > 0 && (
          <div className="mt-4 space-y-2">
            {path.map((hop, i) => (
              <div key={i} className="p-3 border rounded">
                <div className="flex items-center gap-2 text-sm font-mono">
                  <Badge variant="outline">{hop.from.type}</Badge>
                  <span className="text-emerald-700">{hop.from.id}</span>
                  <span className="text-muted-foreground">via cable</span>
                  <Badge>{hop.cable.type || 'unknown'}</Badge>
                  <span className="text-muted-foreground">→</span>
                  <Badge variant="outline">{hop.to.type}</Badge>
                  <span className="text-emerald-700">{hop.to.id}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent></Card>
    </div>
  );
}
