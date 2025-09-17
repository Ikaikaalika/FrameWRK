'use client';
import { useState } from 'react';

export default function Upload(){
  const [files, setFiles] = useState<FileList|null>(null);
  const [status, setStatus] = useState('');

  async function ingest(){
    if(!files || files.length===0){ setStatus('Pick at least one .md file'); return; }
    const texts: string[] = [];
    for(const f of Array.from(files)){
      const txt = await f.text();
      texts.push(txt);
    }
    const r = await fetch('http://localhost:8000/rag/ingest', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({texts})
    });
    const data = await r.json();
    setStatus(`Ingested: ${data.ingested}`);
  }

  return (
    <main>
      <div className="card">
        <h2>Upload & Ingest</h2>
        <p>Select one or more <b>.md</b> files to ingest into the vector DB.</p>
        <input type="file" multiple accept=".md,text/markdown" onChange={e=>setFiles(e.target.files)} />
        <div style={{marginTop:12}}>
          <button className="btn" onClick={ingest}>Ingest</button>
        </div>
        <p>{status}</p>
      </div>
    </main>
  );
}
