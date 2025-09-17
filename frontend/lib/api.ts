export async function ragQuery(question: string){
  const r = await fetch('http://localhost:8000/rag/query', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({question, k: 5})
  });
  return await r.json();
}

export async function ragChat(history: {role:'user'|'assistant', content:string}[], question: string){
  const r = await fetch('http://localhost:8000/rag/chat', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({history, question, k:5})
  });
  return await r.json();
}

export async function summarize(text: string){
  const r = await fetch('http://localhost:8000/llm/summarize', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text, max_tokens:150})
  });
  return await r.json();
}

export async function classify(text: string, labels: string[]){
  const r = await fetch('http://localhost:8000/llm/classify', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text, labels})
  });
  return await r.json();
}

export async function getLogs(limit=50, offset=0){
  const r = await fetch(`http://localhost:8000/admin/logs?limit=${limit}&offset=${offset}`);
  return await r.json();
}
