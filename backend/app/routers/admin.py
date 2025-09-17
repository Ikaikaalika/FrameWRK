from fastapi import APIRouter, Query
from ..storage.db import get_conn

router = APIRouter(prefix="/admin")

@router.get("/logs")
def get_logs(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, route, created_at FROM api_logs ORDER BY id DESC LIMIT %s OFFSET %s", (limit, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"items": [{"id": r[0], "route": r[1], "created_at": r[2].isoformat()} for r in rows], "limit": limit, "offset": offset}
