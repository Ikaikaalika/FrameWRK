# Filling the RAG Database with Mock Data & Prompt Tuning Tips

## 1. Loading Mock Operational Content

You have two quick options for populating Qdrant with sample documents:

### Option A — Use the provided script (recommended)
```bash
# Make sure docker stack + ollama are running
ollama serve >/tmp/ollama.log 2>&1 &
docker compose up -d

# Seed the repo’s sample docs
docker compose exec backend bash -lc "python scripts/ingest.py /app/scripts/seed_docs"

# Inject the richer clinic mock docs (pre-op checklist, emergency protocol, inventory guide, recovery protocol, sedation log)
docker compose exec backend bash -lc "python scripts/ingest.py /app/scripts/mock_docs"
```
The script now accepts `.md`, `.txt`, and `.json` files and logs the number of items uploaded.

### Option B — Manual upload via UI
1. Zip or copy any clinic SOPs / mock docs into `scripts/mock_docs` (or create your own directory).
2. Open http://localhost:3000/upload
3. Drag files (supported types: `.md`, `.txt`, `.json`) and click **Ingest**.
4. Check `/admin` to confirm the call was logged, and `/chat` to test retrieval.

You can create additional mock files by following the structure of the existing ones (pre-op, sedation, post-op). Each ingestion overwrites duplicates by vector similarity, so feel free to tweak text and rerun.

## 2. Improving the System Prompt

The default prompt lives in `backend/app/services/rag_pipeline.py`:
```python
prompt = "You are a helpful assistant. Use the context to answer. If unknown, say you don't know.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
```

### Prompt Enhancement Ideas
- **Role-specific guidance**: Tell the model it’s the Nuvia Ops coordinator, emphasising clinical safety.
- **Formatting**: Ask for numbered checklists or structured JSON summaries.
- **Citation hints**: Instruct it to reference bullet numbers or include source quotes.

Example upgrade:
```python
prompt = (
    "You are Nuvia Smiles' operations co-pilot. Answer using only the provided context. "
    "If the context is insufficient, respond with 'I don't know'."
    "\n\nRespond as a numbered checklist when appropriate, and call out sedation or inventory risks explicitly."
    "\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
)
```

After editing the prompt, restart the backend:
```bash
docker compose restart backend
```

### Keep Prompts Testable
- Add regression questions to a notebook or script (e.g., `scripts/query_examples.py`) so you can compare answers before/after prompt tweaks.
- Use `/admin` logs to monitor latency and ensure the new prompt doesn’t exceed token limits.

## 3. Automating Bulk Ingests
- Drop any additional folders into `scripts/` and call the ingest script with the path.
- For larger datasets, build a CSV/JSON pipeline that reads rows and batches them into the `{ "texts": [...] }` payload.
- Consider tagging payloads with metadata (extend `vectorstore.upsert_texts`) to support faceted retrieval later.

Once the mock data and prompt improvements are in place, your demo can show:
- Ops Command Center summarising the synthetic surgical schedule.
- Chat answering domain-specific questions with the new prompt behaviour.
- Checklist generator leveraging the same documents.
