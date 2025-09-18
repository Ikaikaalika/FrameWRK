const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function ragQuery(question: string){
  const r = await fetch(`${API_BASE}/rag/query`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({question, k: 5})
  });
  return await r.json();
}

export async function ragChat(history: {role:'user'|'assistant', content:string}[], question: string){
  const r = await fetch(`${API_BASE}/rag/chat`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({history, question, k:5})
  });
  return await r.json();
}

export async function summarize(text: string){
  const r = await fetch(`${API_BASE}/llm/summarize`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text, max_tokens:150})
  });
  return await r.json();
}

export async function classify(text: string, labels: string[]){
  const r = await fetch(`${API_BASE}/llm/classify`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text, labels})
  });
  return await r.json();
}

export async function getLogs(limit=50, offset=0){
  const r = await fetch(`${API_BASE}/admin/logs?limit=${limit}&offset=${offset}`);
  return await r.json();
}

export async function ingestDocs(texts: string[]){
  const r = await fetch(`${API_BASE}/rag/ingest`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({texts})
  });
  return await r.json();
}

export type OpsDashboard = {
  meta: {
    total_surgeries: number;
    total_sedation_cases: number;
    at_risk_centers: number;
    open_tasks: number;
  };
  locations: Array<{
    location: string;
    surgeries_today: number;
    sedation_cases: number;
    risk_patients: number;
    team_lead: string;
    status: string;
  }>;
  schedule: Array<{
    patient: string;
    procedure: string;
    start: string;
    location: string;
    surgeon: string;
    stage: string;
    notes: string;
  }>;
  tasks: Array<{
    title: string;
    owner: string;
    due: string;
    priority: string;
  }>;
  inventory_alerts: Array<{
    item: string;
    location: string;
    status: string;
    on_hand: number;
    par_level: number;
  }>;
};

export async function getOpsDashboard(){
  const r = await fetch(`${API_BASE}/ops/dashboard`);
  if (!r.ok) throw new Error('Failed to load ops dashboard');
  return (await r.json()) as OpsDashboard;
}

export type ChecklistPayload = {
  patient_name: string;
  procedure: string;
  location: string;
  sedation: string;
  notes?: string;
};

export type ChecklistResponse = {
  title: string;
  checklist: string[];
  follow_up: string[];
};

export async function createChecklist(payload: ChecklistPayload){
  const r = await fetch(`${API_BASE}/ops/checklist`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  if (!r.ok) throw new Error('Failed to generate checklist');
  return (await r.json()) as ChecklistResponse;
}
