'use client';
import { useEffect, useState } from 'react';
import { getLogs } from '../../lib/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

type LogItem = {id:number, route:string, created_at:string};

export default function Admin(){
  const [items, setItems] = useState<LogItem[]>([]);
  useEffect(()=>{ (async()=>{
    const data = await getLogs(200,0);
    setItems(data.items || []);
  })(); }, []);

  const counts: Record<string, number> = {};
  items.forEach(i=>{
    const rt = new URL(i.route).pathname;
    counts[rt] = (counts[rt]||0)+1;
  });
  const chartData = Object.keys(counts).map(k=>({route:k, count:counts[k]}));

  return (
    <main>
      <div className="card">
        <h2>Admin</h2>
        <p>Recent API routes (last {items.length} calls)</p>
        <div style={{overflowX:'auto'}}>
          <LineChart width={600} height={280} data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="route" hide />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="count" strokeWidth={2} />
          </LineChart>
        </div>
      </div>
      <div className="card">
        <h3>Logs</h3>
        <table>
          <thead><tr><th>ID</th><th>Route</th><th>Time</th></tr></thead>
          <tbody>
            {items.map(it=>(
              <tr key={it.id}><td>{it.id}</td><td>{new URL(it.route).pathname}</td><td>{it.created_at}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
