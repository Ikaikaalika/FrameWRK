from fastapi import FastAPI, Request
from .routers import health, llm, rag, admin, rag_chat
from .storage.db import get_conn

app = FastAPI(title="AI App Starter", version="0.2.0")

@app.on_event("startup")
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(open("/app/app/storage/migrations.sql","r").read())
    conn.commit()
    cur.close()
    conn.close()

app.include_router(health.router)
app.include_router(llm.router)
app.include_router(rag.router)
app.include_router(admin.router)
app.include_router(rag_chat.router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import json, time
    body = await request.body()
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO api_logs(route, request_json, response_json) VALUES (%s,%s,%s)",
            (str(request.url), json.loads(body.decode('utf-8') or "{}"), {})
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass
    response.headers["x-runtime"] = f"{elapsed:.3f}s"
    return response
