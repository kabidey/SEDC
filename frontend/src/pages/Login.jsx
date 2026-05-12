import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function Login() {
  const { login, register } = useAuth();
  const nav = useNavigate();
  const [u, setU] = useState('');
  const [p, setP] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setErr('');
    setLoading(true);
    try {
      await login(u, p);
      nav('/');
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReg = async (e) => {
    e.preventDefault();
    setErr('');
    setLoading(true);
    try {
      await register({ username: u, password: p });
      nav('/');
    } catch (e) {
      setErr(e?.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'linear-gradient(135deg, #064e3b 0%, #065f46 40%, #047857 100%)' }}>
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 rounded-xl items-center justify-center font-bold text-2xl text-white mb-4" style={{ background: 'linear-gradient(135deg, #10b981, #047857)' }}>S</div>
          <h1 className="text-3xl font-bold text-white">SMIFS</h1>
          <p className="text-emerald-200/80 mt-1">Enterprise Data Centre</p>
        </div>
        <Card className="shadow-2xl">
          <CardHeader>
            <CardTitle>Sign in</CardTitle>
            <CardDescription>Network &amp; data-centre infrastructure management</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login">
              <TabsList className="grid grid-cols-2 mb-4">
                <TabsTrigger value="login" data-testid="login-tab">Sign in</TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab">Create account</TabsTrigger>
              </TabsList>
              <TabsContent value="login">
                <form onSubmit={handle} className="space-y-4">
                  <div>
                    <Label htmlFor="u">Username</Label>
                    <Input id="u" data-testid="login-username" value={u} onChange={(e) => setU(e.target.value)} required autoFocus />
                  </div>
                  <div>
                    <Label htmlFor="p">Password</Label>
                    <Input id="p" data-testid="login-password" type="password" value={p} onChange={(e) => setP(e.target.value)} required />
                  </div>
                  {err && <Alert variant="destructive"><AlertDescription>{err}</AlertDescription></Alert>}
                  <Button type="submit" disabled={loading} className="w-full" data-testid="login-submit">{loading ? 'Signing in...' : 'Sign in'}</Button>
                  <p className="text-xs text-muted-foreground text-center mt-2">Default: <code className="text-emerald-700">admin / admin</code></p>
                </form>
              </TabsContent>
              <TabsContent value="register">
                <form onSubmit={handleReg} className="space-y-4">
                  <div>
                    <Label htmlFor="r-u">Username</Label>
                    <Input id="r-u" data-testid="register-username" value={u} onChange={(e) => setU(e.target.value)} required />
                  </div>
                  <div>
                    <Label htmlFor="r-p">Password</Label>
                    <Input id="r-p" data-testid="register-password" type="password" value={p} onChange={(e) => setP(e.target.value)} required />
                  </div>
                  {err && <Alert variant="destructive"><AlertDescription>{err}</AlertDescription></Alert>}
                  <Button type="submit" disabled={loading} className="w-full" data-testid="register-submit">{loading ? 'Creating...' : 'Create account'}</Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        <p className="text-center text-emerald-200/60 text-xs mt-6">Auth bridge to Orglens employee directory will be enabled when integration playbook is provided.</p>
      </div>
    </div>
  );
}
