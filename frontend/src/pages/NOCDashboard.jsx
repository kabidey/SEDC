import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import { openMonitoringStream } from '../lib/monitoring-sse';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Activity, AlertTriangle, CheckCircle2, AlertCircle, HelpCircle, Radio, Bell, BellOff, Server, ArrowUpRight, Wifi, WifiOff, Gauge } from 'lucide-react';
import { toast } from 'sonner';

const STATUS_COLORS = {
  ok: { bg: 'bg-emerald-50 dark:bg-emerald-950/40', text: 'text-emerald-700 dark:text-emerald-300', border: 'border-emerald-500/40', icon: CheckCircle2 },
  warning: { bg: 'bg-amber-50 dark:bg-amber-950/40', text: 'text-amber-700 dark:text-amber-300', border: 'border-amber-500/40', icon: AlertTriangle },
  critical: { bg: 'bg-rose-50 dark:bg-rose-950/40', text: 'text-rose-700 dark:text-rose-300', border: 'border-rose-500/40', icon: AlertCircle },
  unknown: { bg: 'bg-slate-50 dark:bg-slate-900/60', text: 'text-slate-700 dark:text-slate-300', border: 'border-slate-500/40', icon: HelpCircle },
};

function Tile({ label, value, hint, status, to, icon: Icon }) {
  const sty = STATUS_COLORS[status] || STATUS_COLORS.unknown;
  const body = (
    <Card className={`border ${sty.border} ${sty.bg} hover:shadow-md transition-shadow`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">{label}</div>
            <div className={`text-3xl font-bold mt-1 ${sty.text}`} data-testid={`noc-tile-${label.toLowerCase().replace(/\s+/g, '-')}`}>{value ?? '—'}</div>
            {hint && <div className="text-xs text-muted-foreground mt-1">{hint}</div>}
          </div>
          {Icon && <Icon size={22} className={sty.text} />}
        </div>
      </CardContent>
    </Card>
  );
  return to ? <Link to={to}>{body}</Link> : body;
}

function SeverityBadge({ severity }) {
  const map = {
    critical: 'bg-rose-600 text-white',
    warning: 'bg-amber-500 text-white',
    info: 'bg-emerald-600 text-white',
  };
  return <Badge className={`${map[severity] || 'bg-slate-500 text-white'} text-[10px] uppercase tracking-wider`}>{severity}</Badge>;
}

function MonitorTypeBadge({ type }) {
  return <Badge variant="outline" className="text-[10px] uppercase border-emerald-500/40 text-emerald-700 dark:text-emerald-300">{type}</Badge>;
}

export default function NOCDashboard() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [monitors, setMonitors] = useState([]);
  const [connected, setConnected] = useState(false);
  const [muted, setMuted] = useState(false);
  const [feed, setFeed] = useState([]); // live event feed (last 100)
  const streamRef = useRef(null);

  const loadAll = async () => {
    try {
      const [s, a, m] = await Promise.all([
        api.get('/monitoring/stats'),
        api.get('/monitoring/alerts?state=firing&limit=50'),
        api.get('/monitoring/monitors?limit=500'),
      ]);
      setStats(s.data);
      setAlerts(a.data.results || []);
      setMonitors(m.data.results || []);
    } catch (e) {
      // surfaced via toast on demand only
    }
  };

  useEffect(() => {
    loadAll();
    const t = setInterval(loadAll, 15000);
    return () => clearInterval(t);
  }, []);

  // Live event stream (SSE)
  useEffect(() => {
    streamRef.current = openMonitoringStream({
      onEvent: (ev) => {
        if (ev.type === 'hello') { setConnected(true); return; }
        setFeed((prev) => [{ ...ev, t: Date.now() }, ...prev].slice(0, 100));
        if (ev.type === 'metric' && ev.sample) {
          setMonitors((prev) => prev.map((m) => m.id === ev.monitor_id ? { ...m, current_status: ev.sample.status, last_latency_ms: ev.sample.latency_ms, last_check_at: ev.sample.time, last_error: ev.sample.error } : m));
        }
        if (ev.type === 'alert_firing' && ev.alert) {
          setAlerts((prev) => [ev.alert, ...prev.filter((a) => a.id !== ev.alert.id)]);
          if (!muted) {
            toast.error(ev.alert.title || 'New alert firing', { description: ev.alert.message });
          }
          loadAll();
        }
        if (ev.type === 'alert_resolved' && ev.alert) {
          setAlerts((prev) => prev.filter((a) => a.id !== ev.alert.id));
          if (!muted) {
            toast.success(`Resolved: ${ev.alert.monitor_name}`);
          }
          loadAll();
        }
        if (ev.type === 'alert_acknowledged' && ev.alert) {
          setAlerts((prev) => prev.map((a) => a.id === ev.alert.id ? ev.alert : a));
        }
      },
      onError: () => setConnected(false),
    });
    return () => { try { streamRef.current && streamRef.current.close(); } catch { /* noop */ } };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [muted]);

  const counts = useMemo(() => ({
    total: stats?.monitors_total ?? monitors.length,
    ok: stats?.monitors_ok ?? monitors.filter(m => m.current_status === 'ok').length,
    warning: stats?.monitors_warning ?? monitors.filter(m => m.current_status === 'warning').length,
    critical: stats?.monitors_critical ?? monitors.filter(m => m.current_status === 'critical').length,
    unknown: stats?.monitors_unknown ?? monitors.filter(m => !m.current_status || m.current_status === 'unknown').length,
    firing: stats?.alerts_firing ?? alerts.length,
    criticalAlerts: stats?.alerts_critical ?? alerts.filter(a => a.severity === 'critical').length,
  }), [stats, monitors, alerts]);

  const ackAlert = async (id) => {
    try { await api.post(`/monitoring/alerts/${id}/acknowledge`); toast.success('Acknowledged'); loadAll(); }
    catch (e) { toast.error('Failed to acknowledge'); }
  };
  const resolveAlert = async (id) => {
    try { await api.post(`/monitoring/alerts/${id}/resolve`); toast.success('Resolved'); loadAll(); }
    catch (e) { toast.error('Failed to resolve'); }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2"><Activity size={22} className="text-emerald-600" />NOC Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time analytics, monitoring, and mission-critical alerting.</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={connected ? 'border-emerald-500 text-emerald-600' : 'border-rose-500 text-rose-600'} data-testid="noc-stream-status">
            {connected ? <Wifi size={12} className="mr-1" /> : <WifiOff size={12} className="mr-1" />}
            {connected ? 'Live' : 'Reconnecting'}
          </Badge>
          <Button variant="outline" size="sm" onClick={() => setMuted(!muted)} data-testid="noc-mute-toggle">
            {muted ? <BellOff size={14} className="mr-1" /> : <Bell size={14} className="mr-1" />}
            {muted ? 'Muted' : 'Sound on'}
          </Button>
          <Link to="/monitoring/monitors"><Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" data-testid="noc-manage-monitors"><Server size={14} className="mr-1" />Monitors</Button></Link>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
        <Tile label="Monitors" value={counts.total} status="ok" icon={Radio} to="/monitoring/monitors" />
        <Tile label="Up" value={counts.ok} status="ok" icon={CheckCircle2} />
        <Tile label="Warning" value={counts.warning} status="warning" icon={AlertTriangle} />
        <Tile label="Critical" value={counts.critical} status="critical" icon={AlertCircle} />
        <Tile label="Unknown" value={counts.unknown} status="unknown" icon={HelpCircle} />
        <Tile label="Alerts Firing" value={counts.firing} status={counts.firing > 0 ? 'critical' : 'ok'} icon={Bell} to="/monitoring/alerts" />
        <Tile label="Critical Alerts" value={counts.criticalAlerts} status={counts.criticalAlerts > 0 ? 'critical' : 'ok'} icon={AlertCircle} to="/monitoring/alerts" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Firing alerts */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="flex items-center gap-2"><AlertTriangle size={16} className="text-rose-600" />Active Alerts</CardTitle>
              <CardDescription>Firing alerts that need attention.</CardDescription>
            </div>
            <Link to="/monitoring/alerts"><Button variant="ghost" size="sm">View all <ArrowUpRight size={14} className="ml-1" /></Button></Link>
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground" data-testid="noc-no-alerts">
                <CheckCircle2 size={28} className="mx-auto mb-2 text-emerald-600" />
                All systems green — no firing alerts.
              </div>
            ) : (
              <ScrollArea className="max-h-[420px] pr-2">
                <div className="space-y-2" data-testid="noc-alerts-list">
                  {alerts.map((a) => (
                    <div key={a.id} className="flex items-start gap-3 p-3 rounded border border-rose-200/60 dark:border-rose-900/60 bg-rose-50/60 dark:bg-rose-950/30">
                      <AlertCircle size={18} className="text-rose-600 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <SeverityBadge severity={a.severity} />
                          <span className="font-medium truncate">{a.title}</span>
                          {a.acknowledged_at && <Badge variant="outline" className="text-[10px]">ACK by {a.acknowledged_by}</Badge>}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{a.message}</div>
                        <div className="text-[11px] text-muted-foreground mt-1">Started {new Date(a.started_at).toLocaleString()}</div>
                      </div>
                      <div className="flex flex-col gap-1">
                        {!a.acknowledged_at && <Button size="sm" variant="outline" onClick={() => ackAlert(a.id)} data-testid={`alert-ack-${a.id}`}>Ack</Button>}
                        <Button size="sm" variant="outline" onClick={() => resolveAlert(a.id)} data-testid={`alert-resolve-${a.id}`}>Resolve</Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Live event feed */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2"><Radio size={16} className="text-emerald-600" />Live Event Feed</CardTitle>
            <CardDescription>Streaming check results &amp; alert state changes.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[420px] pr-2">
              {feed.length === 0 ? (
                <div className="py-10 text-center text-sm text-muted-foreground">Waiting for events...</div>
              ) : (
                <div className="space-y-1.5 text-xs font-mono" data-testid="noc-feed">
                  {feed.map((e, i) => {
                    if (e.type === 'metric') {
                      const s = e.sample || {};
                      const sty = STATUS_COLORS[s.status] || STATUS_COLORS.unknown;
                      return (
                        <div key={i} className="flex items-center gap-2 py-1 border-b border-border/40">
                          <span className={`w-1.5 h-1.5 rounded-full ${s.status === 'ok' ? 'bg-emerald-500' : s.status === 'warning' ? 'bg-amber-500' : s.status === 'critical' ? 'bg-rose-500' : 'bg-slate-400'}`} />
                          <span className="text-muted-foreground">{new Date(e.t).toLocaleTimeString()}</span>
                          <span className={`font-medium ${sty.text} truncate`}>{e.monitor_name}</span>
                          <span className="ml-auto text-muted-foreground">{s.latency_ms != null ? `${s.latency_ms}ms` : '—'}</span>
                        </div>
                      );
                    }
                    if (e.type === 'alert_firing' || e.type === 'alert_resolved' || e.type === 'alert_acknowledged') {
                      const a = e.alert || {};
                      const colour = e.type === 'alert_firing' ? 'text-rose-600' : e.type === 'alert_resolved' ? 'text-emerald-600' : 'text-amber-600';
                      return (
                        <div key={i} className={`py-1 border-b border-border/40 ${colour}`}>
                          <span className="font-bold">{e.type.replace('alert_', '').toUpperCase()}</span> · <span className="text-foreground">{a.title}</span>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Monitor grid */}
      <Card className="mt-4">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="flex items-center gap-2"><Gauge size={16} className="text-emerald-600" />Monitor Status</CardTitle>
            <CardDescription>All registered checks and their current state.</CardDescription>
          </div>
          <Link to="/monitoring/monitors"><Button variant="outline" size="sm">Manage</Button></Link>
        </CardHeader>
        <CardContent>
          {monitors.length === 0 ? (
            <div className="py-10 text-center text-sm text-muted-foreground" data-testid="noc-no-monitors">
              No monitors configured yet. <Link to="/monitoring/monitors" className="text-emerald-600 underline">Create one</Link> to start monitoring servers, circuits, or services.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2" data-testid="noc-monitors-grid">
              {monitors.map((m) => {
                const sty = STATUS_COLORS[m.current_status] || STATUS_COLORS.unknown;
                const Icon = sty.icon;
                return (
                  <Link to={`/monitoring/monitors`} key={m.id} className="block">
                    <div className={`p-3 rounded border ${sty.border} ${sty.bg} hover:shadow-sm transition-shadow`}>
                      <div className="flex items-center gap-2">
                        <Icon size={16} className={sty.text} />
                        <span className="font-medium truncate flex-1">{m.name}</span>
                        <MonitorTypeBadge type={m.type} />
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-1 truncate">{m.target || m.url || '—'}</div>
                      <div className="flex items-center gap-3 text-[11px] text-muted-foreground mt-1">
                        <span>Latency: <span className={sty.text}>{m.last_latency_ms ?? '—'}{m.last_latency_ms != null ? ' ms' : ''}</span></span>
                        <span>Loss: {m.last_loss_pct ?? '—'}{m.last_loss_pct != null ? '%' : ''}</span>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
