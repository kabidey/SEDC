import React, { useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { NAV_GROUPS } from '../lib/resources';
import {
  Building2, Server, Columns3, Cable, Globe, Route, Zap, Box, Wifi, Shield,
  Settings2, ShieldCheck, ChevronDown, ChevronRight, LogOut, Search, LayoutDashboard,
  User as UserIcon, Menu as MenuIcon, X, Radar, BookOpen, Activity,
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import api from '../lib/api';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

const ICON_MAP = { 'building-2': Building2, server: Server, 'columns-3': Columns3, cable: Cable, globe: Globe, route: Route, zap: Zap, box: Box, wifi: Wifi, shield: Shield, 'settings-2': Settings2, 'shield-check': ShieldCheck, radar: Radar, activity: Activity };

function SidebarGroup({ group, openGroups, toggleGroup, onItemClick }) {
  const Icon = ICON_MAP[group.icon] || Server;
  const open = openGroups[group.label] ?? false;
  return (
    <div className="mb-1">
      <button onClick={() => toggleGroup(group.label)} className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-emerald-100/80 hover:text-white transition-colors">
        <Icon size={16} className="text-emerald-400" />
        <span className="flex-1 text-left">{group.label}</span>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {open && (
        <div className="ml-7 mt-1 space-y-0.5 border-l border-emerald-800/40 pl-2">
          {group.items.map((item) => (
            <NavLink
              key={item.path}
              to={`/${item.path}`}
              onClick={onItemClick}
              className={({ isActive }) =>
                `block px-3 py-1.5 text-sm rounded text-emerald-100/70 hover:text-white hover:bg-emerald-800/40 transition-colors ${isActive ? 'bg-emerald-700/60 text-white font-medium' : ''}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

function Sidebar({ onItemClick }) {
  const [openGroups, setOpenGroups] = useState(() => {
    const init = {};
    NAV_GROUPS.forEach((g) => { init[g.label] = false; });
    init['Organization'] = true;
    return init;
  });
  const toggleGroup = (label) => setOpenGroups((p) => ({ ...p, [label]: !p[label] }));

  return (
    <aside className="w-72 h-full flex flex-col" style={{ background: 'hsl(158 50% 9%)' }}>
      <div className="px-5 py-4 border-b border-emerald-800/40">
        <Link to="/" className="flex items-center gap-2 text-white">
          <div className="w-9 h-9 rounded-md flex items-center justify-center font-bold text-white" style={{ background: 'linear-gradient(135deg, #10b981, #047857)' }}>S</div>
          <div>
            <div className="font-bold text-base leading-tight">SMIFS</div>
            <div className="text-[11px] text-emerald-300/80 leading-tight">Enterprise Data Centre</div>
          </div>
        </Link>
      </div>
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        <NavLink to="/" onClick={onItemClick} className={({ isActive }) => `flex items-center gap-2 px-3 py-2 text-sm font-medium rounded mb-1 ${isActive ? 'bg-emerald-700/60 text-white' : 'text-emerald-100/80 hover:bg-emerald-800/40 hover:text-white'}`}>
          <LayoutDashboard size={16} />
          Dashboard
        </NavLink>
        <NavLink to="/help" onClick={onItemClick} className={({ isActive }) => `flex items-center gap-2 px-3 py-2 text-sm font-medium rounded mb-2 ${isActive ? 'bg-emerald-700/60 text-white' : 'text-emerald-100/80 hover:bg-emerald-800/40 hover:text-white'}`}>
          <BookOpen size={16} />
          Help &amp; Tutorial
        </NavLink>
        {NAV_GROUPS.map((g) => (
          <SidebarGroup key={g.label} group={g} openGroups={openGroups} toggleGroup={toggleGroup} onItemClick={onItemClick} />
        ))}
      </nav>
      <div className="p-3 border-t border-emerald-800/40 text-[11px] text-emerald-300/60">
        v1.0.0 · {new Date().getFullYear()}
      </div>
    </aside>
  );
}

function GlobalSearch() {
  const [q, setQ] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const nav = useNavigate();

  const doSearch = async (val) => {
    setQ(val);
    if (!val || val.length < 2) { setResults([]); setOpen(false); return; }
    try {
      const { data } = await api.get(`/search?q=${encodeURIComponent(val)}`);
      setResults(data.results || []);
      setOpen(true);
    } catch (e) {
      setResults([]);
    }
  };

  return (
    <div className="relative w-full max-w-xl">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={q}
          onChange={(e) => doSearch(e.target.value)}
          onFocus={() => results.length && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder="Search sites, devices, IPs, prefixes, VLANs, ..."
          className="pl-10"
          data-testid="global-search-input"
        />
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-40 mt-1 w-full bg-popover border border-border rounded-md shadow-lg max-h-96 overflow-y-auto">
          {results.slice(0, 30).map((r, i) => (
            <button
              key={i}
              onClick={() => { nav(`/${r.object_type.replace('_', '-')}s/${r.object.id}`); setQ(''); setOpen(false); }}
              className="w-full text-left px-3 py-2 hover:bg-accent text-sm border-b border-border last:border-0"
            >
              <span className="text-xs text-emerald-700 font-medium uppercase">{r.object_type}</span>
              <span className="ml-2 font-medium">{r.object.name || r.object.address || r.object.prefix || r.object.cid || r.object.ssid || r.object.id}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="hidden lg:flex"><Sidebar /></div>
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-72" style={{ background: 'hsl(158 50% 9%)' }}>
          <Sidebar onItemClick={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-border bg-card flex items-center px-4 gap-3">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileOpen(true)}><MenuIcon size={20} /></Button>
          <GlobalSearch />
          <div className="flex-1" />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-2" data-testid="user-menu-trigger">
                <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-semibold">
                  {(user?.first_name?.[0] || user?.username?.[0] || 'U').toUpperCase()}
                </div>
                <span className="text-sm font-medium hidden sm:inline">{user?.username || 'User'}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div>
                  <div className="font-medium">{user?.first_name} {user?.last_name}</div>
                  <div className="text-xs text-muted-foreground">{user?.email}</div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => nav('/admin/api-tokens')}><Settings2 size={14} className="mr-2" />API Tokens</DropdownMenuItem>
              {user?.is_admin && <DropdownMenuItem onSelect={() => nav('/admin/users')}><ShieldCheck size={14} className="mr-2" />Admin</DropdownMenuItem>}
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => { logout(); nav('/login'); }} data-testid="logout-button"><LogOut size={14} className="mr-2" />Sign Out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
