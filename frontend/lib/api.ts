const RAW_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || '';
const isServer = typeof window === 'undefined';

let API_BASE = RAW_BASE;
if (!API_BASE) {
  API_BASE = isServer ? 'http://backend:8000' : '';
} else if (!isServer && /backend:\d+/.test(API_BASE)) {
  // Inside the browser we can't resolve docker service names — fall back to same-origin paths
  API_BASE = '';
}

const buildUrl = (path: string) => (API_BASE ? `${API_BASE}${path}` : path);

export async function ragQuery(question: string){
  const r = await fetch(buildUrl('/rag/query'), {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({question, k: 5})
  });
  return await r.json();
}

export async function ragChat(history: {role:'user'|'assistant', content:string}[], question: string){
  const r = await fetch(buildUrl('/rag/chat'), {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({history, question, k:5})
  });
  return await r.json();
}

export async function summarize(text: string){
  const r = await fetch(buildUrl('/llm/summarize'), {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text, max_tokens:150})
  });
  return await r.json();
}

export async function classify(text: string, labels: string[]){
  const r = await fetch(buildUrl('/llm/classify'), {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text, labels})
  });
  return await r.json();
}

export async function getLogs(limit=50, offset=0){
  const r = await fetch(buildUrl(`/admin/logs?limit=${limit}&offset=${offset}`));
  return await r.json();
}

export async function ingestDocs(texts: string[]){
  const r = await fetch(buildUrl('/rag/ingest'), {
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
  const r = await fetch(buildUrl('/ops/dashboard'));
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
  const r = await fetch(buildUrl('/ops/checklist'), {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  if (!r.ok) throw new Error('Failed to generate checklist');
  return (await r.json()) as ChecklistResponse;
}
