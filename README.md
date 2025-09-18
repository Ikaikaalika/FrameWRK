# AI Ops Runbook Hub

Turn ops tribal knowledge into a durable, AI-assisted workflow. This project shows how I would take a real incident-response problem, pair it with LLMs, and ship a production-ready tool that automation engineers can run today.

## Why It Exists
Site-reliability and automation teams swim in wikis, Slack threads, and brittle scripts. During an incident you need:
- answers grounded in the latest runbooks (not hallucinations)
- the ability to classify & summarize noisy alerts
- an auditable trail for compliance and continuous improvement

This hub tackles that end-to-end: ingest docs → embed → search → reason → log. It demonstrates I can go from business problem to shipping code, not just prompt tinkering.

## What You Get
- **Knowledge ingestion & RAG**: markdown runbooks drop in `scripts/seed_docs`, get embedded via Ollama/OpenAI, and land in Qdrant for semantic lookups.
- **Ops-ready chat**: `/chat` UI (Next.js) gives responders contextual answers plus citations.
- **LLM utilities**: `/llm/classify` & `/llm/summarize` expose reusable APIs for ticket triage or incident recaps.
- **Request telemetry**: every call is stored in Postgres; `/admin` visualizes route volume so we can spot drift or abuse.
- **Provider resilience**: FastAPI adapters speak OpenAI, Anthropic, **and local Ollama**. If the network dies, we fall back to deterministic heuristics instead of 500s.
- **Nuvia Ops Command Center**: `/ops` aggregates surgeries, sedation load, inventory alerts, and lets coordinators auto-generate pre-op checklists tailored to each case.

## Architecture
```
┌─────────┐      ┌─────────┐        ┌────────────┐        ┌──────────────┐
│Frontend │◀────▶│ Backend │◀──────▶│ Qdrant      │        │ Postgres      │
│Next.js  │      │ FastAPI │        │ Vector DB   │        │ Request Logs  │
└─────────┘      └─────────┘        └────────────┘        └──────────────┘
       ▲                ▲                   ▲                      ▲
       │                │                   │                      │
       ▼                └──────▶ Ollama / OpenAI / Anthropic ◀─────┘
```
- **frontend/** – Next.js 14 app with Chat, Upload/Ingest, and Admin pages.
- **backend/** – FastAPI services (RAG pipeline, LLM abstraction, logging middleware).
- **qdrant** – stores embeddings + source text.
- **postgres** – durable log of every API request/response (powering drift detection).
- **docker-compose.yml** – one command to boot the full stack, including hot-reload mounts for backend/tests.

## Quickstart (Local)
```bash
# 0) Prereqs: Docker Desktop + Ollama (for local inference)
brew install ollama
ollama serve >/tmp/ollama.log 2>&1 &
ollama pull llama3.2:3b
ollama pull nomic-embed-text

# 1) Configure env (points backend + frontend at the right services)
cp .env.example .env
# edit if you want OpenAI/Anthropic keys; defaults work with Ollama
# note: frontend uses `NEXT_PUBLIC_API_URL` in the browser (defaults to http://localhost:8000) and `API_INTERNAL_URL` on the server (defaults to http://backend:8000 for Docker)

# 2) Start the platform
docker compose up --build
# UI:  http://localhost:3000
# API: http://localhost:8000/docs

# 3) Seed the knowledge base with sample runbooks
docker compose exec backend bash -lc "python scripts/ingest.py /app/scripts/seed_docs"

# 4) Run backend tests
docker compose exec backend pytest -q
```

## Key Workflows
| Task | How | Notes |
|------|-----|-------|
| Ask grounded questions | Visit `/chat` or `POST /rag/query` | Answers include the top-matched runbook chunks. |
| Monitor Nuvia operations | `/ops` | Live view of surgeries, tasks, inventory, and checklist generator. |
| Upload new runbooks | `/upload` UI | Accepts `.md`, `.txt`, or `.json` text; triggers embed + Qdrant upsert. |
| Classify alerts | `POST /llm/classify` | Provider-agnostic; falls back to rule-based scores if LLM unavailable. |
| Summarize incidents | `POST /llm/summarize` | Great for daily incident digests or PR columns. |
| Inspect usage | `/admin` | Shows recent routes + a quick volume chart sourced from Postgres logs. |

## Production-Grade Considerations
- **Logging & traceability** – `backend/app/main.py` middleware stores URL + payload (JSON-safe) per call.
- **Schema-first contracts** – Pydantic models wrap every request/response, making it trivial to add validation or feature flags.
- **Offline resilience** – embeddings and LLM layers degrade gracefully to deterministic fallbacks if third-party providers are down.
- **Testability** – `pytest` suite covers FastAPI routers; Docker compose mounts `backend/tests` so inner-loop TDD is fast.

## Roadmap / Next Iterations
1. **Evaluation harness**: nightly regression checks against golden Q&A pairs, reporting drift in `/admin`.
2. **Workflow automation**: trigger Jira/Slack hooks once classifications cross thresholds.
3. **Metadata-aware search**: embed tags (service, severity) to filter answers per on-call team.
4. **Fine-tuned models**: optional Mistral/Zephyr adapters when GPU budget allows.

## Hiring Narrative
This repo is more than a demo. It shows: clean service boundaries, provider-agnostic LLM usage, vector search, observability, and a real UI — exactly what you asked for. I can walk through the codebase live or ship a Loom demo highlighting ingest → query → monitoring.

Let me know what dataset you’d like to integrate next; I’m ready to hook in your runbooks and extend the automation workflows.
