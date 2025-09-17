'use client';
import { useState } from 'react';
import { ragChat } from '../../lib/api';

type Turn = { role:'user'|'assistant', content:string };

export default function Chat(){
  const [history, setHistory] = useState<Turn[]>([]);
  const [q, setQ] = useState('What does this project include?');
  const [thinking, setThinking] = useState(false);

  async function send(){
    setThinking(true);
    const res = await ragChat(history, q);
    setHistory([...history, {role:'user', content:q}, {role:'assistant', content:res.answer}]);
    setQ('');
    setThinking(false);
  }

  return (
    <main>
      <div className="card">
        <h2>Chat (RAG)</h2>
        <div style={{display:'grid', gap:8}}>
          {history.map((t,i)=>(
            <div key={i} className="card">
              <div className="label">{t.role}</div>
              <div>{t.content}</div>
            </div>
          ))}
        </div>
        <div className="grid two" style={{marginTop:12}}>
          <input className="input" value={q} onChange={e=>setQ(e.target.value)} placeholder="Ask a question..." />
          <button className="btn" onClick={send} disabled={thinking || !q.trim()}>{thinking?'Thinking...':'Send'}</button>
        </div>
      </div>
    </main>
  );
}
