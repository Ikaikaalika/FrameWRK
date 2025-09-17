# AI App Starter — FastAPI + Next.js + Qdrant + Postgres (+ Upgraded UI) 

A production-grade, modular starter that demonstrates how to go from **business problem → code → AI-powered solution**.

**What’s included**
- **FastAPI** backend with clean service layers and provider-agnostic **LLM adapters** (OpenAI, Anthropic, **Ollama**).
- **RAG** pipeline (ingest → embed → vector search → answer) with **Qdrant**.
- **Classification** and **Summarization** APIs.
- **Next.js (TS)** front end with **Chat (RAG)**, **Upload & Ingest**, and **Admin dashboard** (Recharts).
- **Postgres** for logs & traces; **Docker Compose** to run everything locally.
- **Terraform** or **one-liner bash** to deploy on **AWS EC2**.
- **Pytest** tests and **.env.example**/**.env.aws.example** for fast start.

## Quickstart (Local)

```bash
# 0) Prereq: Docker Desktop
# 1) Copy env and set keys / provider
cp .env.example .env
# 2) Start stack
docker compose up --build
# 3) Open
# UI : http://localhost:3000
# API: http://localhost:8000/docs
```

### GPU on Mac (use your local Ollama)
Install Ollama on macOS and point the backend at it:

```bash
brew install ollama
ollama serve &
ollama pull llama3.1
# optional embeddings
ollama pull nomic-embed-text

# .env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1
EMBEDDINGS_PROVIDER=ollama
```

### Seed RAG with sample docs
```bash
docker compose exec backend bash -lc "python scripts/ingest.py scripts/seed_docs"
```

---

## UI Pages
- **/** — overview
- **/chat** — chat-style RAG with history
- **/upload** — drag in .md text and ingest
- **/admin** — logs list + tiny route count chart

---

## Deploy on AWS

### Option A — Terraform (EC2 + Docker)
1. Zip this repo and upload to S3 (presigned URL).
2. In `deploy/aws/terraform`:
```bash
terraform init
terraform apply   -var key_name=YOUR_EC2_KEYPAIR   -var zip_url="https://YOUR-PRESIGNED-URL/ai-app-starter.zip"   -var env_contents="$(cat .env.aws.example)"
```
Outputs:
- UI  → `http://<EC2_PUBLIC_IP>`
- API → `http://<EC2_PUBLIC_IP>:8000/docs`

### Option B — Existing EC2 (one-liner)
On Ubuntu 22.04:
```bash
sudo bash deploy/aws/scripts/run_on_aws.sh   "https://YOUR-PRESIGNED-URL/ai-app-starter.zip"   "$(cat .env.aws.example)"
```

**Notes**
- On AWS, prefer **OpenAI/Anthropic** for inference (Ollama GPU is best on Mac).
- Lock down security groups and add HTTPS (ALB + ACM) for production.
