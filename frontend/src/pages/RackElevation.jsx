import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';
import { Server } from 'lucide-react';

export default function RackElevation() {
  const [racks, setRacks] = useState([]);
  const [rackId, setRackId] = useState('');
  const [data, setData] = useState(null);

  useEffect(() => { (async () => {
    const { data } = await api.get('/racks?limit=500');
    setRacks(data.results || []);
    if (data.results?.[0]) setRackId(data.results[0].id);
  })(); }, []);
  useEffect(() => { if (!rackId) return; (async () => {
    const { data } = await api.get(`/rack-tools/${rackId}/elevation`);
    setData(data);
  })(); }, [rackId]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Rack Elevation</h1>
      <div className="flex items-center gap-3 mb-6">
        <Label className="text-sm">Rack:</Label>
        <Select value={rackId} onValueChange={setRackId}>
          <SelectTrigger className="w-72"><SelectValue placeholder="Select a rack" /></SelectTrigger>
          <SelectContent>
            {racks.map((r) => <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>)}
          </SelectContent>
        </Select>
        {data && <Badge variant="secondary">Util: {data.utilization?.toFixed(0)}%</Badge>}
      </div>
      {data && (
        <Card>
          <CardContent className="p-6">
            <div className="flex gap-6">
              <div className="flex-1 max-w-sm">
                <div className="text-xs uppercase text-muted-foreground mb-2 text-center font-semibold">{data.rack.name} ({data.rack.u_height}U)</div>
                <div className="border-2 border-emerald-900 rounded overflow-hidden">
                  {[...data.units].reverse().map((u) => (
                    <div key={u.unit} className={`flex items-center text-xs border-b last:border-0 ${u.occupant ? 'bg-emerald-100 border-emerald-300' : 'bg-muted/30'}`} style={{ height: 28 }}>
                      <div className="w-10 text-center text-muted-foreground border-r border-border bg-background h-full flex items-center justify-center font-mono">{u.unit}</div>
                      <div className="flex-1 px-2 truncate">
                        {u.occupant ? (
                          <Link to={`/devices/${u.occupant.device.id}`} className="flex items-center gap-1 font-medium text-emerald-800 hover:underline">
                            <Server size={11} /> {u.occupant.device.name || u.occupant.device.id}
                          </Link>
                        ) : <span className="text-muted-foreground">empty</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium mb-2">Devices in this rack ({data.devices.length})</div>
                <ul className="space-y-1">
                  {data.devices.map((d) => (
                    <li key={d.id} className="p-2 border rounded text-sm flex items-center justify-between">
                      <Link to={`/devices/${d.id}`} className="font-medium text-emerald-700 hover:underline">{d.name || d.id}</Link>
                      <Badge variant="outline">U{d.position} / {d.face}</Badge>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
