import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Building2, Server, Columns3, Cable, Globe, Box, Route, Zap, Wifi, Shield, Users, FileText, Tag as TagIcon, Webhook } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';

const STATS_CARDS = [
  { key: 'sites', label: 'Sites', icon: Building2, color: 'emerald', link: '/sites' },
  { key: 'racks', label: 'Racks', icon: Columns3, color: 'green', link: '/racks' },
  { key: 'devices', label: 'Devices', icon: Server, color: 'teal', link: '/devices' },
  { key: 'interfaces', label: 'Interfaces', icon: Cable, color: 'cyan', link: '/interfaces' },
  { key: 'ip_addresses', label: 'IP Addresses', icon: Globe, color: 'sky', link: '/ip-addresses' },
  { key: 'prefixes', label: 'Prefixes', icon: Globe, color: 'blue', link: '/prefixes' },
  { key: 'vlans', label: 'VLANs', icon: Cable, color: 'indigo', link: '/vlans' },
  { key: 'virtual_machines', label: 'Virtual Machines', icon: Box, color: 'violet', link: '/virtual-machines' },
  { key: 'clusters', label: 'Clusters', icon: Box, color: 'fuchsia', link: '/clusters' },
  { key: 'circuits', label: 'Circuits', icon: Route, color: 'amber', link: '/circuits' },
  { key: 'power_panels', label: 'Power Panels', icon: Zap, color: 'orange', link: '/power-panels' },
  { key: 'wireless_lans', label: 'Wireless LANs', icon: Wifi, color: 'rose', link: '/wireless-lans' },
  { key: 'tunnels', label: 'Tunnels', icon: Shield, color: 'pink', link: '/tunnels' },
  { key: 'tenants', label: 'Tenants', icon: Users, color: 'lime', link: '/tenants' },
  { key: 'cables', label: 'Cables', icon: Cable, color: 'yellow', link: '/cables' },
  { key: 'l2vpns', label: 'L2VPNs', icon: Shield, color: 'red', link: '/l2vpns' },
];

export default function Dashboard() {
  const [stats, setStats] = useState({ counters: {}, recent_changes: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/stats');
        setStats(data);
      } catch {}
      setLoading(false);
    })();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">Overview of your network and data-centre infrastructure</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
        {STATS_CARDS.map((s) => {
          const Icon = s.icon;
          const count = stats.counters?.[s.key] ?? 0;
          return (
            <Link key={s.key} to={s.link} className="group">
              <Card className="hover:border-emerald-500 hover:shadow-md transition-all">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center group-hover:bg-emerald-100">
                    <Icon size={18} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">{s.label}</div>
                    <div className="text-2xl font-semibold tabular-nums">{loading ? '…' : count}</div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Changes</CardTitle>
          <CardDescription>Last 10 changes recorded across the system</CardDescription>
        </CardHeader>
        <CardContent>
          {!stats.recent_changes?.length ? (
            <p className="text-sm text-muted-foreground">No changes yet.</p>
          ) : (
            <ul className="divide-y divide-border">
              {stats.recent_changes.map((c) => (
                <li key={c.id} className="py-2 flex items-center gap-3 text-sm">
                  <Badge variant={c.action === 'delete' ? 'destructive' : c.action === 'create' ? 'default' : 'secondary'} className="capitalize">{c.action}</Badge>
                  <span className="font-medium">{c.object_type}</span>
                  <span className="text-muted-foreground truncate flex-1">{c.object_repr || c.object_id}</span>
                  <span className="text-xs text-muted-foreground">{c.username}</span>
                  <span className="text-xs text-muted-foreground">{c.time?.slice(0, 19).replace('T', ' ')}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
