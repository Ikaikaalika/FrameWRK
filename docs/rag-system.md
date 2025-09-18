# Retrieval-Augmented Generation (RAG) System Overview

This document describes how the FrameWRK Ops Hub implements retrieval-augmented generation to deliver grounded answers for operations teams.

## Goals
- **Ground LLM responses** in the latest procedures, runbooks, and operational notes.
- **Keep knowledge fresh** by letting teams ingest markdown docs on demand.
- **Log every interaction** for auditing and continuous improvement.

## High-Level Flow
1. **Ingest** – Runbooks and notes (`.md`, `.txt`, `.json`) are uploaded via `/upload` (UI) or `POST /rag/ingest`.
2. **Embed** – Text chunks are converted to vectors using the configured embeddings provider (OpenAI or local Ollama).
3. **Store** – Vectors plus payload metadata are written to the Qdrant collection `docs`.
4. **Query** – When a user asks a question, we embed it, search Qdrant for top-k matches, and feed those snippets into the LLM.
5. **Respond** – The LLM returns an answer anchored to the retrieved context; responses and payloads are logged in Postgres.

```
Markdown Doc ─▶ Embed ─▶ Qdrant
     ▲                            ▼
Upload UI/Script              Query Embedding
                               ▼
                        LLM Prompt (context)
                               ▼
                         Grounded Answer
```

## Key Components

### Embeddings (`backend/app/services/embeddings.py`)
- Supports `OPENAI` or `OLLAMA` providers via config.
- Falls back to a deterministic hash embedding if remote APIs are unavailable (keeps the system usable offline).

### Vector Store (`backend/app/services/vectorstore.py`)
- Wraps the Qdrant client for `ensure_collection`, `upsert_texts`, and `search`.
- Gracefully handles missing collections (returns an empty result instead of 500), enabling cold starts before any ingestion.

### RAG Pipeline (`backend/app/services/rag_pipeline.py`)
- `ensure_collection()` bootstraps the Qdrant collection with the correct embedding dimension.
- `ingest_texts()` embeds incoming texts and writes them to Qdrant.
- `query(question)` embeds the question, retrieves top-k vectors, and crafts a prompt instructing the LLM to respond only with grounded info.

### API Surface
- `POST /rag/ingest` – Accepts `{ "texts": [...] }`. Pipelines through `ensure_collection()` → `ingest_texts()`.
- `POST /rag/query` – Full RAG call returning `answer` + `chunks`.
- `POST /rag/chat` – Chat wrapper that keeps short history and feeds `query()`.

### Frontend Hooks (`frontend/lib/api.ts`)
- `ragChat(history, question)` wires the chat page to `POST /rag/chat`.
- `ingestDocs(texts)` powers the Upload page.

## Logging & Observability
- Middleware in `backend/app/main.py` logs every request to Postgres (`api_logs` table) using `psycopg2.extras.Json`. The Admin UI reflects this log stream.
- Qdrant operations surface errors in the backend logs; the vector store catches 404 collection errors to avoid crashing the user experience.

## Deployment Considerations
- **Collection lifecycle**: In production you may wish to initialize `docs` with `ensure_collection()` during startup rather than the first ingestion.
- **Chunking**: Current ingest treats each markdown file as a single chunk. For large documents, add splitter logic (e.g., `textwrap` or `langchain` chunkers) before embedding.
- **Metadata**: Attach payload metadata (location, procedure stage, author) to `PointStruct.payload` for faceted search later.
- **Evaluation**: Store golden Q&A pairs and periodically validate responses to catch drift as new documents are ingested.

## Quick Demo Script
1. `docker compose up -d` and ensure `ollama serve` is running (or set `OPENAI_API_KEY`).
2. Upload docs via `/upload` UI or the seed script: `docker compose exec backend bash -lc "python scripts/ingest.py /app/scripts/seed_docs"`.
3. Visit `/chat` and ask "What does Nuvia Smiles do?" – answer should cite the newly ingested text.
4. Open `/admin` to confirm the ingest + chat calls appear in the request log.

This RAG backbone keeps the Ops Hub responsive to knowledge updates while maintaining provenance for every answer delivered to the field.
