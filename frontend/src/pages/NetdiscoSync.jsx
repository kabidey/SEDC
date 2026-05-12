import React, { useEffect, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';

export default function NetdiscoSync() {
  const [settings, setSettings] = useState({ base_url: '', username: '', password: '', verify_ssl: true });
  const [testing, setTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [syncResult, setSyncResult] = useState(null);

  useEffect(() => { (async () => {
    try { const { data } = await api.get('/discovery/netdisco/settings'); if (data?.base_url) setSettings((s) => ({ ...s, ...data, password: '' })); } catch {}
  })(); }, []);

  const save = async () => {
    try { await api.post('/discovery/netdisco/settings', settings); toast.success('Saved'); } catch (e) { toast.error('Save failed'); }
  };
  const test = async () => {
    setTesting(true); setTestResult(null);
    try { const { data } = await api.post('/discovery/netdisco/test', settings); setTestResult(data); } catch (e) { setTestResult({ error: e.message }); }
    setTesting(false);
  };
  const sync = async () => {
    setSyncing(true); setSyncResult(null);
    try { const { data } = await api.post('/discovery/netdisco/sync', settings); setSyncResult(data); toast.success(`Pulled ${data.devices_pulled} devices, staged ${data.staged}`); } catch (e) { toast.error('Sync failed: ' + (e?.response?.data?.detail || e.message)); }
    setSyncing(false);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">External Netdisco Sync</h1>
      <p className="text-sm text-muted-foreground mb-4">Connect to a running Netdisco instance and pull discovered devices via its REST API.</p>
      <Card>
        <CardHeader><CardTitle className="text-base">Connection Settings</CardTitle><CardDescription>Use your Netdisco admin credentials. Devices are staged as Discovered Devices and can then be imported into SMIFS.</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <div><Label>Base URL</Label><Input value={settings.base_url} onChange={(e) => setSettings({ ...settings, base_url: e.target.value })} placeholder="https://netdisco.example.com" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label>Username</Label><Input value={settings.username} onChange={(e) => setSettings({ ...settings, username: e.target.value })} /></div>
            <div><Label>Password</Label><Input type="password" value={settings.password} onChange={(e) => setSettings({ ...settings, password: e.target.value })} /></div>
          </div>
          <div className="flex items-center gap-3"><Switch checked={settings.verify_ssl} onCheckedChange={(v) => setSettings({ ...settings, verify_ssl: v })} /><Label>Verify SSL</Label></div>
          <div className="flex gap-2 pt-2">
            <Button variant="outline" onClick={test} disabled={testing || !settings.base_url}>{testing ? 'Testing…' : 'Test Connection'}</Button>
            <Button variant="outline" onClick={save} disabled={!settings.base_url}>Save Settings</Button>
            <Button onClick={sync} disabled={syncing || !settings.base_url}>{syncing ? 'Syncing…' : 'Pull Devices Now'}</Button>
          </div>
          {testResult && (
            <div className="p-3 border rounded text-sm bg-muted/30">
              <Badge variant={testResult.reachable ? 'default' : 'destructive'}>{testResult.reachable ? 'reachable' : 'unreachable'}</Badge>
              <pre className="mt-2 text-xs">{JSON.stringify(testResult, null, 2)}</pre>
            </div>
          )}
          {syncResult && (
            <div className="p-3 border rounded text-sm bg-emerald-50">
              <p>Pulled <strong>{syncResult.devices_pulled}</strong> devices, staged <strong>{syncResult.staged}</strong> for review.</p>
              <p className="text-xs text-muted-foreground mt-1">Open Discovered Devices to inspect and import.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
