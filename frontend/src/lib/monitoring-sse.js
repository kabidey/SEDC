// Helper to open a live event stream (SSE primary, WebSocket fallback) against /api/monitoring.
// Returns a handle with .close().
import { API_BASE } from './api';

export function openMonitoringStream({ onEvent, onError, transport = 'sse' } = {}) {
  const token = localStorage.getItem('smifs_token') || '';
  let closed = false;
  let es = null;
  let ws = null;
  let reconnectTimer = null;

  const connectSSE = () => {
    if (closed) return;
    try {
      const url = `${API_BASE}/monitoring/stream?token=${encodeURIComponent(token)}`;
      es = new EventSource(url);
      const handle = (type) => (e) => {
        try {
          const data = e.data ? JSON.parse(e.data) : {};
          onEvent && onEvent({ type, ...data });
        } catch {
          /* ignore */
        }
      };
      es.addEventListener('hello', handle('hello'));
      es.addEventListener('metric', handle('metric'));
      es.addEventListener('alert_firing', handle('alert_firing'));
      es.addEventListener('alert_resolved', handle('alert_resolved'));
      es.addEventListener('alert_acknowledged', handle('alert_acknowledged'));
      es.addEventListener('message', handle('message'));
      es.onerror = () => {
        onError && onError(new Error('SSE error'));
        try { es && es.close(); } catch { /* noop */ }
        if (!closed) {
          reconnectTimer = setTimeout(connectSSE, 4000);
        }
      };
    } catch (e) {
      onError && onError(e);
    }
  };

  const connectWS = () => {
    if (closed) return;
    try {
      const base = API_BASE.replace(/^http/, 'ws');
      const url = `${base}/monitoring/ws?token=${encodeURIComponent(token)}`;
      ws = new WebSocket(url);
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          onEvent && onEvent(data);
        } catch { /* ignore */ }
      };
      ws.onerror = (err) => onError && onError(err);
      ws.onclose = () => {
        if (!closed) reconnectTimer = setTimeout(connectWS, 4000);
      };
      const keepalive = setInterval(() => {
        if (ws && ws.readyState === 1) {
          try { ws.send(JSON.stringify({ type: 'ping' })); } catch { /* noop */ }
        } else {
          clearInterval(keepalive);
        }
      }, 25000);
    } catch (e) {
      onError && onError(e);
    }
  };

  if (transport === 'ws') connectWS(); else connectSSE();

  return {
    close: () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      try { es && es.close(); } catch { /* noop */ }
      try { ws && ws.close(); } catch { /* noop */ }
    },
  };
}
