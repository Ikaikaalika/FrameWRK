# AI Ops Runbook Hub

This repo is my “business problem → AI-powered solution” story. I took Nuvia Smiles’ multi-location dental implant operations and built a production-style hub that centralizes runbooks, highlights live KPIs, and automates repetitive workflows. The README captures not only the feature set but also the engineering challenges I hit and how I resolved them.

---

## Why It Exists
Operations teams drown in unstructured SOPs, sedation logs, and ad-hoc checklists. During a case you need:
- **Grounded answers** drawn from the newest versions of those docs.
- **Operational telemetry** (sedation load, inventory alerts, follow-up calls) at a glance.
- **An audit trail** that proves what the AI saw and how it responded.

This hub covers the full loop: ingest docs → embed → vector search → LLM reasoning → surface dashboards → store every action.

---

## Feature Snapshot
- **Knowledge ingestion & RAG** – `/upload` UI and `scripts/ingest.py` ingest `.md`, `.txt`, `.json` documents. Each vector gets metadata (location, procedure stage, risk level) so answers can cite context.
- **Ops Command Center** – `/ops` displays daily surgeries, sedation trendlines, follow-up queue, inventory alerts, and auto-generated tasks produced from LLM checklists.
- **Grounded chat** – `/chat` pulls top-k snippets (with metadata headers) and the prompt encourages checklists and risk call-outs.
- **Automation plumbing** – Checklist runs store follow-up items in Postgres (`ops_generated_tasks`) and expose them at `/ops/generated-tasks`.
- **Structured logging** – `rag.pipeline`, `rag.vectorstore`, `rag.embeddings`, and the ingest CLI all log to shared format via `backend/app/monitoring/logging.py`.
- **Provider resilience** – Supports OpenAI, Anthropic, and local Ollama. If external providers fail, a deterministic hash embedding keeps the system usable.

---

## Architecture at a Glance
```
┌─────────┐      ┌─────────┐        ┌────────────┐        ┌──────────────┐
│Frontend │◀────▶│ Backend │◀──────▶│ Qdrant      │        │ Postgres      │
│Next.js  │      │ FastAPI │        │ Vector DB   │        │ Request/Task  │
└─────────┘      └─────────┘        └────────────┘        └──────────────┘
       ▲                ▲                   ▲                      ▲
       │                │                   │                      │
       ▼                └──────▶ Ollama / OpenAI / Anthropic ◀─────┘
```
- **frontend/** – Next.js 14 app (Chat, Upload, Admin, Ops Command Center).
- **backend/** – FastAPI services (RAG pipeline, Ops service, logging, task persistence).
- **qdrant** – Vector store that holds embeddings + metadata.
- **postgres** – Stores request logs (`api_logs`) and generated tasks (`ops_generated_tasks`).
- **docker-compose.yml** – Boots the whole stack; backend/tests have hot-reload mounts.

---

## Quickstart / Demo Checklist
```bash
# 0) Prereqs: Docker Desktop + Ollama
ollama serve >/tmp/ollama.log 2>&1 &

# 1) Configure env
cp .env.example .env
# - NEXT_PUBLIC_API_URL defaults to http://localhost:8000 for the browser
# - API_INTERNAL_URL defaults to http://backend:8000 for in-container calls

# 2) Start stack
docker compose up -d

# 3) Seed knowledge (vector store stays offline)
docker compose exec backend bash -lc "python scripts/ingest.py /app/scripts/seed_docs"
docker compose exec backend bash -lc "python scripts/ingest.py /app/scripts/mock_docs"

# 4) Browse
# Ops Command : http://localhost:3000/ops
# Chat        : http://localhost:3000/chat
# Upload      : http://localhost:3000/upload
# Admin       : http://localhost:3000/admin

# 5) Regression
docker compose exec backend pytest -q
npm --prefix frontend run build
```
More RAG maintenance tips live in `docs/rag-playbook.md` (ingestion options, prompt tuning, regression ideas).

---

## Offline Demo Playbook
Keep the entire loop on-device.

```bash
# 0) Start Ollama locally if you want GPU-accelerated embeds/completions.
ollama serve >/tmp/ollama.log 2>&1 &

# 1) Launch the stack (Postgres + Qdrant + FastAPI + Next.js).
docker compose up -d

# 2) Bootstrap vectors + Postgres demo rows (run inside backend container).
docker compose exec backend bash -lc "python scripts/offline_bootstrap.py"

# 3) Optional: prove the build/tests pass without network calls.
./scripts/offline_eval.sh

# 4) Demo tour:
#   http://localhost:3000/ops    → KPI cockpit with pre-seeded tasks/logs
#   http://localhost:3000/chat   → Ask "How do we prep IV sedation?"
#   http://localhost:3000/upload → Drop a new .md and re-query instantly
```

Highlights:
- Qdrant is primed with `scripts/seed_docs` and `scripts/mock_docs` via the bootstrap script.
- Postgres already has API log history and generated tasks so `/ops` and `/admin` feel production-ready offline.
- `./scripts/offline_eval.sh` runs `pytest` plus `npm run build` locally to showcase reliability with zero cloud calls.

---

## Key Workflows
| Task | How | Notes |
|------|-----|-------|
| Ask grounded questions | `/chat` or `POST /rag/query` | Metadata-tagged snippets + prompt encourage structured answers. |
| Monitor operations | `/ops` | Sedation trend chart, follow-up queue, generated tasks, inventory alerts, checklist generator. |
| Automate follow-ups | `/ops/checklist` | LLM output logged to `ops_generated_tasks`; view via `/ops/generated-tasks`. |
| Upload runbooks | `/upload` UI | Accepts `.md`, `.txt`, `.json`; ingestion script logs doc count + HTTP status. |
| Extend mock data | `scripts/mock_docs/` | Includes pre-op protocol, anesthesia emergency SOP, inventory guide, post-op checklist, sedation event log. Add more & rerun ingest. |
| Inspect usage | `/admin` | Postgres-backed request log, updated by every request middleware call. |

---

## Prompt Engineering
- Base prompt sits in `backend/app/services/rag_pipeline.py`. It casts the model as “Nuvia Smiles’ operations co-pilot”, encourages numbered checklists, and highlights sedation/inventory risks.
- Prompt instructs the LLM to only answer “I don’t know” when no snippets are returned; otherwise create the best grounded summary.
- Metadata embedded in the context (Title, Location, Stage, Risk) helps the LLM choose the right snippet.
- Fine-tuning ideas: add persona variants, enforce JSON outputs, or tailor instructions per workflow (pre-op vs. inventory).

---

## Problem-Solving Log
| Challenge | Pain Point | Solution |
|-----------|------------|----------|
| Offline-ready embeddings | Needed to demo without OpenAI | Added Ollama adapters + deterministic hash fallback (768-dim) |
| Cold-start Qdrant | Collection missing triggered 404s | `ensure_collection()` bootstraps size and handles 404 gracefully |
| Browser ↔ Docker networking | UI hitting `http://backend:8000` failed outside Docker | Added adaptive base URL logic (`NEXT_PUBLIC_API_URL` vs `API_INTERNAL_URL`) + CORS middleware |
| Debug visibility | Hard to trace ingest → embed → search | Introduced structured logging names (`rag.embeddings`, `rag.vectorstore`, `rag.pipeline`, `scripts.ingest`) |
| Realistic content | Generic runbooks weren’t convincing | Authored mock pre-op, anesthesia emergency, inventory, post-op docs with metadata |
| Automating follow-ups | Checklist steps disappeared | Persist follow-up items in `ops_generated_tasks` and display in `/ops` |
| Trend visibility | Ops dashboard felt static | Added sedation trendline (Recharts area chart) and an upcoming follow-up queue |

---

## Logging & Observability
- `backend/app/monitoring/logging.py` sets a consistent format (`%(asctime)s | %(levelname)s | %(name)s | %(message)s`).
- `rag.embeddings`, `rag.vectorstore`, `rag.pipeline` emit info/debug statements on provider choice, vector counts, LLM latency, etc.
- Request middleware logs each API call to Postgres (`api_logs`). Tail with `docker compose logs backend -f`.
- CLI ingest script uses the same format, showing file counts and API responses.

---

## Demo Flow (Recommended)
1. **Reset/seed** – run the two ingest commands; check `/admin` for log entries.
2. **Ops Command Center** – highlight sedation load %, trend chart, follow-up queue, and generated tasks. Trigger a checklist for a live update.
3. **Chat** – ask “Summarize the anesthesia emergency protocol” or “How do we replenish implant inventory?” to showcase metadata-rich answers.
4. **Upload** – drop a new `.txt` note via the UI, re-run a chat query, and confirm the context updates immediately.
5. **Logs** – tail backend logs to show the pipeline capturing each stage.

---

## Extending the System
- **Metadata filtering** – Extend `vectorstore._extract_metadata` to capture more tags (e.g., surgeon, sedation clearance status) and filter by them.
- **Checklist task routing** – Extend `ops_generated_tasks` with assignment/resolution endpoints and surface them in the UI card.
- **Evaluations** – Script golden questions & nightly regression tests to guard prompt changes.
- **Integrations** – Hook into actual inventory APIs or patient CRMs once moving beyond mock data.

Everything runs in Docker and is instrumented for debugging. Clone, follow the quickstart steps, and you can walk interviewers through a realistic AI ops hub with detailed talking points on decisions and solutions.
