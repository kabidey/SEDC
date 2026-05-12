import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Bell, Check, X, RotateCw, AlertCircle, Trash2 } from 'lucide-react';

const SEV_BG = {
  critical: 'bg-rose-600 text-white',
  warning: 'bg-amber-500 text-white',
  info: 'bg-emerald-600 text-white',
};
const STATE_BG = {
  firing: 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
  resolved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
};

export default function AlertHistory() {
  const [alerts, setAlerts] = useState([]);
  const [stateFilter, setStateFilter] = useState('all');

  const load = async () => {
    try {
      const url = stateFilter === 'all' ? '/monitoring/alerts?limit=500' : `/monitoring/alerts?state=${stateFilter}&limit=500`;
      const { data } = await api.get(url);
      setAlerts(data.results || []);
    } catch (e) { toast.error('Failed to load alerts'); }
  };

  useEffect(() => { load(); }, [stateFilter]);
  useEffect(() => { const t = setInterval(load, 10000); return () => clearInterval(t); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [stateFilter]);

  const ack = async (id) => { try { await api.post(`/monitoring/alerts/${id}/acknowledge`); toast.success('Acknowledged'); load(); } catch { toast.error('Failed'); } };
  const resolve = async (id) => { try { await api.post(`/monitoring/alerts/${id}/resolve`); toast.success('Resolved'); load(); } catch { toast.error('Failed'); } };
  const remove = async (id) => { if (!window.confirm('Delete alert?')) return; try { await api.delete(`/monitoring/alerts/${id}`); toast.success('Deleted'); load(); } catch { toast.error('Failed'); } };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2"><AlertCircle size={22} className="text-emerald-600" />Alert History</h1>
          <p className="text-sm text-muted-foreground mt-1">Firing, acknowledged, and resolved alerts.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={stateFilter} onValueChange={setStateFilter}>
            <SelectTrigger className="w-36" data-testid="alert-state-filter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="firing">Firing</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={load}><RotateCw size={14} className="mr-1" />Refresh</Button>
        </div>
      </div>
      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr className="text-left">
                <th className="px-3 py-2 font-medium">State</th>
                <th className="px-3 py-2 font-medium">Severity</th>
                <th className="px-3 py-2 font-medium">Title</th>
                <th className="px-3 py-2 font-medium">Monitor</th>
                <th className="px-3 py-2 font-medium">Started</th>
                <th className="px-3 py-2 font-medium">Resolved</th>
                <th className="px-3 py-2 font-medium">Ack</th>
                <th className="px-3 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody data-testid="alerts-table">
              {alerts.length === 0 ? <tr><td colSpan={8} className="text-center py-10 text-muted-foreground"><Bell className="mx-auto mb-2 text-emerald-500" size={28} />No alerts.</td></tr> : alerts.map((a) => (
                <tr key={a.id} className="border-t border-border hover:bg-muted/40">
                  <td className="px-3 py-2"><Badge className={`${STATE_BG[a.state] || 'bg-slate-100'} uppercase text-[10px]`}>{a.state}</Badge></td>
                  <td className="px-3 py-2"><Badge className={`${SEV_BG[a.severity]} text-[10px] uppercase`}>{a.severity}</Badge></td>
                  <td className="px-3 py-2 font-medium max-w-[360px] truncate" title={a.title}>{a.title}</td>
                  <td className="px-3 py-2">{a.monitor_name}</td>
                  <td className="px-3 py-2 text-xs">{a.started_at ? new Date(a.started_at).toLocaleString() : '—'}</td>
                  <td className="px-3 py-2 text-xs">{a.resolved_at ? new Date(a.resolved_at).toLocaleString() : '—'}</td>
                  <td className="px-3 py-2 text-xs">{a.acknowledged_by ? `${a.acknowledged_by} @ ${new Date(a.acknowledged_at).toLocaleString()}` : '—'}</td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1 justify-end">
                      {a.state === 'firing' && !a.acknowledged_at && <Button variant="ghost" size="sm" onClick={() => ack(a.id)} data-testid={`history-ack-${a.id}`}><Check size={14} /></Button>}
                      {a.state === 'firing' && <Button variant="ghost" size="sm" onClick={() => resolve(a.id)} data-testid={`history-resolve-${a.id}`}><X size={14} /></Button>}
                      <Button variant="ghost" size="sm" onClick={() => remove(a.id)} data-testid={`history-delete-${a.id}`}><Trash2 size={14} className="text-rose-600" /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
