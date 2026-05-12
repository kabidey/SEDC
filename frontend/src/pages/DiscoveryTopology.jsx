import React, { useEffect, useRef, useState } from 'react';
import api from '../lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';

export default function DiscoveryTopology() {
  const [data, setData] = useState({ nodes: [], edges: [] });
  const canvasRef = useRef(null);

  useEffect(() => { (async () => {
    const { data } = await api.get('/discovery/topology');
    setData(data);
  })(); }, []);

  useEffect(() => {
    if (!canvasRef.current || !data.nodes.length) return;
    const ctx = canvasRef.current.getContext('2d');
    const w = canvasRef.current.width;
    const h = canvasRef.current.height;
    ctx.clearRect(0, 0, w, h);
    // Simple force-free layout: arrange nodes in a circle
    const cx = w / 2, cy = h / 2;
    const radius = Math.min(w, h) * 0.36;
    const positions = {};
    data.nodes.forEach((n, i) => {
      const angle = (i / Math.max(data.nodes.length, 1)) * Math.PI * 2;
      positions[n.id] = { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) };
    });
    // Draw edges
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1.5;
    data.edges.forEach((e) => {
      const a = positions[e.source]; const b = positions[e.target];
      if (!a || !b) return;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    });
    // Draw nodes
    data.nodes.forEach((n) => {
      const p = positions[n.id];
      ctx.beginPath();
      ctx.fillStyle = '#047857';
      ctx.arc(p.x, p.y, 11, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(n.label?.slice(0, 2).toUpperCase() || '?', p.x, p.y + 3);
      ctx.fillStyle = '#0f172a';
      ctx.font = '10px sans-serif';
      ctx.fillText((n.label || '').slice(0, 22), p.x, p.y + 26);
    });
  }, [data]);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Network Topology</h1>
      <p className="text-sm text-muted-foreground mb-4">Graph of {data.nodes.length} devices and {data.edges.length} discovered links (LLDP/CDP neighbours rendered as cables).</p>
      <Card><CardContent className="p-4">
        {data.nodes.length === 0 ? (
          <p className="text-sm text-muted-foreground p-8 text-center">No devices yet. Run a discovery scan to populate the topology.</p>
        ) : (
          <div className="flex flex-col md:flex-row gap-4">
            <canvas ref={canvasRef} width={720} height={520} className="bg-muted/20 rounded border w-full md:w-2/3" />
            <div className="w-full md:w-1/3">
              <h3 className="text-sm font-semibold mb-2">Links</h3>
              <ul className="space-y-1 text-xs max-h-96 overflow-y-auto">
                {data.edges.map((e) => (
                  <li key={e.id} className="p-2 border rounded">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px]">{e.cable_type || 'cable'}</Badge>
                      <Badge variant="secondary" className="text-[10px]">{e.status}</Badge>
                    </div>
                    <div className="mt-1">
                      <Link to={`/devices/${e.source}`} className="text-emerald-700 hover:underline">{data.nodes.find((n) => n.id === e.source)?.label}</Link>
                      <span className="text-muted-foreground">:{e.source_port} ↔ </span>
                      <Link to={`/devices/${e.target}`} className="text-emerald-700 hover:underline">{data.nodes.find((n) => n.id === e.target)?.label}</Link>
                      <span className="text-muted-foreground">:{e.target_port}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </CardContent></Card>
    </div>
  );
}
