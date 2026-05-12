import React, { useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate, useParams, useLocation } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from '@/lib/auth';
import Layout from '@/components/Layout';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import { ListView, DetailView } from '@/components/ResourcePage';
import RackElevation from '@/pages/RackElevation';
import PrefixTree from '@/pages/PrefixTree';
import CableTrace from '@/pages/CableTrace';
import ChangeLog from '@/pages/ChangeLog';
import { UsersAdmin, GroupsAdmin, ApiTokensAdmin } from '@/pages/Admin';
import GraphQLPlayground from '@/pages/GraphQLPlayground';
import { RESOURCES } from '@/lib/resources';

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="p-6 text-center text-muted-foreground">Loading...</div>;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}

function ResourceListRoute() {
  const { resource } = useParams();
  if (!RESOURCES[resource]) return <div className="p-6">Unknown resource: <code>{resource}</code></div>;
  return <ListView resource={resource} />;
}
function ResourceDetailRoute() {
  const { resource } = useParams();
  if (!RESOURCES[resource]) return <div className="p-6">Unknown resource: <code>{resource}</code></div>;
  return <DetailView resource={resource} />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={
        <RequireAuth>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/rack-elevation" element={<RackElevation />} />
              <Route path="/prefix-tree" element={<PrefixTree />} />
              <Route path="/cable-trace" element={<CableTrace />} />
              <Route path="/changelog" element={<ChangeLog />} />
              <Route path="/graphql" element={<GraphQLPlayground />} />
              <Route path="/admin/users" element={<UsersAdmin />} />
              <Route path="/admin/groups" element={<GroupsAdmin />} />
              <Route path="/admin/api-tokens" element={<ApiTokensAdmin />} />
              <Route path="/:resource/:id" element={<ResourceDetailRoute />} />
              <Route path="/:resource" element={<ResourceListRoute />} />
              <Route path="*" element={<div className="p-6">Page not found.</div>} />
            </Routes>
          </Layout>
        </RequireAuth>
      } />
    </Routes>
  );
}

export default function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
          <Toaster richColors position="top-right" />
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}
