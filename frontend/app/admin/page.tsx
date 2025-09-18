'use client';
import { useEffect, useMemo, useState } from 'react';
import { getLogs } from '../../lib/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';

type LogItem = { id: number; route: string; created_at: string };

export default function Admin() {
  const [items, setItems] = useState<LogItem[]>([]);

  useEffect(() => {
    (async () => {
      const data = await getLogs(400, 0);
      setItems(data.items || []);
    })();
  }, []);

  const analytics = useMemo(() => {
    const counts: Record<string, number> = {};
    let last = '';
    items.forEach((item) => {
      const route = new URL(item.route).pathname;
      counts[route] = (counts[route] || 0) + 1;
      if (!last || new Date(item.created_at) > new Date(last)) {
        last = item.created_at;
      }
    });

    const chartData = Object.keys(counts).map((route) => ({ route, count: counts[route] }));
    const topRoute = Object.entries(counts).sort(([, a], [, b]) => b - a)[0]?.[0] ?? '—';

    return {
      chartData,
      topRoute,
      totalCalls: items.length,
      uniqueRoutes: Object.keys(counts).length,
      lastCall: last,
    };
  }, [items]);

  return (
    <section>
      <header className="card">
        <h2>Operational telemetry</h2>
        <p className="form-helper">Monitor API volume, popular endpoints, and freshness of your RAG pipeline.</p>
      </header>

      <div className="stat-grid">
        <div className="stat">
          <span>Total calls</span>
          <strong>{analytics.totalCalls}</strong>
          <small className="form-helper">Captured in Postgres</small>
        </div>
        <div className="stat">
          <span>Unique routes</span>
          <strong>{analytics.uniqueRoutes}</strong>
          <small className="form-helper">Across recent activity</small>
        </div>
        <div className="stat">
          <span>Most active route</span>
          <strong>{analytics.topRoute}</strong>
        </div>
        <div className="stat">
          <span>Last request</span>
          <strong>{analytics.lastCall ? new Date(analytics.lastCall).toLocaleString() : '—'}</strong>
        </div>
      </div>

      <div className="card">
        <h3>Route volume</h3>
        {analytics.chartData.length ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={analytics.chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.2)" />
              <XAxis dataKey="route" hide />
              <YAxis allowDecimals={false} stroke="rgba(148, 163, 184, 0.4)" />
              <Tooltip contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', borderRadius: 12, border: '1px solid rgba(99,102,241,0.4)' }} />
              <Line type="monotone" dataKey="count" stroke="#818cf8" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">Hit the API to populate usage metrics.</div>
        )}
      </div>

      <div className="card">
        <h3>Request log</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Route</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{new URL(item.route).pathname}</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
