"""
AgentLens API v2 — industry-grade FastAPI backend
"""
from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import (
    Depends, FastAPI, Header, HTTPException, Query,
    Request, WebSocket, WebSocketDisconnect, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("agentlens")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ── WebSocket connection manager ──────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}  # project_id → sockets

    async def connect(self, ws: WebSocket, project_id: str):
        await ws.accept()
        self._connections.setdefault(project_id, []).append(ws)
        logger.info(f"WS connected: project={project_id}, total={len(self._connections[project_id])}")

    def disconnect(self, ws: WebSocket, project_id: str):
        conns = self._connections.get(project_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, project_id: str, event: dict):
        dead = []
        for ws in self._connections.get(project_id, []):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, project_id)


ws_manager = ConnectionManager()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    from scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    logger.info("AgentLens API started")
    yield
    stop_scheduler()
    logger.info("AgentLens API stopped")


# ── App setup ─────────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="AgentLens API",
    description="Production monitoring & analytics for AI agents",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    t0 = time.monotonic()
    response = await call_next(request)
    ms = int((time.monotonic() - t0) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{ms}ms"
    return response


# ── Auth helpers ──────────────────────────────────────────────────────────────

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authorization header")
    token = authorization.replace("Bearer ", "")
    try:
        sb = get_sb()
        result = sb.auth.get_user(token)
        if not result or not result.user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        return result.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))


def require_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    sb = get_sb()
    result = sb.table("projects").select("*").eq("api_key", x_api_key).execute()
    if not result.data:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    return result.data[0]


# ── Models ────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str


class LogRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: str
    agent_response: str
    latency_ms: Optional[int] = None
    model: Optional[str] = None
    metadata: Optional[dict] = {}


class AnalyzeRequest(BaseModel):
    limit: Optional[int] = 50


class AlertConfig(BaseModel):
    failure_rate_threshold: float = 20.0
    min_conversations: int = 10
    email_alerts: bool = True


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": "2.0.0", "time": datetime.utcnow().isoformat()}


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/auth/signup", tags=["auth"])
@limiter.limit("10/minute")
async def signup(body: dict, request: Request):
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        raise HTTPException(400, "Email and password required")
    try:
        sb = get_sb()
        result = sb.auth.sign_up({"email": email, "password": password})
        if result.user:
            project = {
                "id": str(uuid.uuid4()),
                "user_id": result.user.id,
                "name": "My AI Agent",
                "api_key": f"ak_{uuid.uuid4().hex[:20]}",
                "created_at": datetime.utcnow().isoformat(),
            }
            sb.table("projects").insert(project).execute()
            return {"user": {"id": result.user.id, "email": result.user.email}, "project": project}
        raise HTTPException(400, "Signup failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/auth/login", tags=["auth"])
@limiter.limit("20/minute")
async def login(body: dict, request: Request):
    try:
        sb = get_sb()
        result = sb.auth.sign_in_with_password({"email": body.get("email"), "password": body.get("password")})
        if result.user and result.session:
            return {"access_token": result.session.access_token, "user": {"id": result.user.id, "email": result.user.email}}
        raise HTTPException(401, "Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, str(e))


# ── Projects ──────────────────────────────────────────────────────────────────

@app.get("/projects", tags=["projects"])
async def list_projects(user=Depends(get_current_user)):
    sb = get_sb()
    result = sb.table("projects").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
    return result.data or []


@app.post("/projects", tags=["projects"], status_code=201)
async def create_project(body: ProjectCreate, user=Depends(get_current_user)):
    sb = get_sb()
    project = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "name": body.name,
        "api_key": f"ak_{uuid.uuid4().hex[:20]}",
        "created_at": datetime.utcnow().isoformat(),
    }
    sb.table("projects").insert(project).execute()
    return project


# ── Logging ───────────────────────────────────────────────────────────────────

@app.post("/log", tags=["logging"])
@limiter.limit("300/minute")
async def log_conversation(body: LogRequest, request: Request, project=Depends(require_api_key)):
    sb = get_sb()
    meta = body.metadata or {}
    if body.latency_ms is not None:
        meta["latency_ms"] = body.latency_ms
    if body.model:
        meta["model"] = body.model

    conv = {
        "id": str(uuid.uuid4()),
        "project_id": project["id"],
        "session_id": body.session_id or str(uuid.uuid4()),
        "user_message": body.user_message,
        "agent_response": body.agent_response,
        "metadata": json.dumps(meta),
        "analyzed": False,
        "is_failure": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    sb.table("conversations").insert(conv).execute()

    # push real-time event to dashboard watchers
    asyncio.create_task(ws_manager.broadcast(project["id"], {
        "type": "new_conversation",
        "id": conv["id"],
        "session_id": conv["session_id"],
        "user_message": body.user_message[:120],
        "created_at": conv["created_at"],
    }))

    return {"id": conv["id"], "status": "logged"}


# ── Analysis ──────────────────────────────────────────────────────────────────

@app.post("/analyze", tags=["analysis"])
@limiter.limit("10/minute")
async def analyze(body: AnalyzeRequest, request: Request, project=Depends(require_api_key)):
    sb = get_sb()
    result = sb.table("conversations").select("*")\
        .eq("project_id", project["id"])\
        .eq("analyzed", False)\
        .limit(body.limit).execute()

    conversations = result.data or []
    if not conversations:
        return {"message": "No unanalyzed conversations", "analyzed": 0}

    from analyzer import analyze_conversations_batch
    results = await analyze_conversations_batch(conversations)

    for r in results:
        sb.table("conversations").update({
            "intent": r.get("intent"),
            "sentiment": r.get("sentiment"),
            "is_failure": r.get("is_failure", False),
            "failure_reason": r.get("failure_reason"),
            "analyzed": True,
        }).eq("id", r["id"]).execute()

    # broadcast analysis-done event
    asyncio.create_task(ws_manager.broadcast(project["id"], {
        "type": "analysis_complete",
        "analyzed": len(results),
    }))

    return {"analyzed": len(results), "results": results}


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard", tags=["dashboard"])
async def dashboard(
    days: int = Query(7, ge=1, le=90),
    project=Depends(require_api_key),
):
    sb = get_sb()
    pid = project["id"]
    convs = (sb.table("conversations").select("*").eq("project_id", pid).execute().data or [])

    total = len(convs)
    analyzed = sum(1 for c in convs if c.get("analyzed"))
    failures = sum(1 for c in convs if c.get("is_failure"))

    intent_counts: dict[str, int] = {}
    sent_counts: dict[str, int] = {}
    daily_counts: dict[str, int] = {}
    latencies: list[int] = []

    for c in convs:
        if c.get("intent"):
            intent_counts[c["intent"]] = intent_counts.get(c["intent"], 0) + 1
        if c.get("sentiment"):
            sent_counts[c["sentiment"]] = sent_counts.get(c["sentiment"], 0) + 1
        day = (c.get("created_at") or "")[:10]
        if day:
            daily_counts[day] = daily_counts.get(day, 0) + 1
        try:
            meta = json.loads(c.get("metadata") or "{}")
            if "latency_ms" in meta:
                latencies.append(int(meta["latency_ms"]))
        except Exception:
            pass

    top_intents = sorted(
        [{"intent": k, "count": v} for k, v in intent_counts.items()],
        key=lambda x: -x["count"],
    )[:10]
    sentiments = [{"sentiment": k, "count": v} for k, v in sent_counts.items()]
    daily = sorted([{"day": k, "count": v} for k, v in daily_counts.items()])[-days:]
    recent = sorted(convs, key=lambda x: x.get("created_at", ""), reverse=True)[:20]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else None

    return {
        "project": project,
        "stats": {
            "total": total,
            "analyzed": analyzed,
            "failures": failures,
            "failure_rate": round(failures / total * 100, 1) if total else 0,
            "avg_latency_ms": avg_latency,
        },
        "top_intents": top_intents,
        "sentiments": sentiments,
        "recent_conversations": recent,
        "daily_volume": daily,
    }


# ── Conversations ─────────────────────────────────────────────────────────────

@app.get("/conversations", tags=["conversations"])
async def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    intent: Optional[str] = None,
    sentiment: Optional[str] = None,
    failures_only: bool = False,
    search: Optional[str] = None,
    project=Depends(require_api_key),
):
    sb = get_sb()
    query = sb.table("conversations").select("*").eq("project_id", project["id"])
    if intent:
        query = query.eq("intent", intent)
    if sentiment:
        query = query.eq("sentiment", sentiment)
    if failures_only:
        query = query.eq("is_failure", True)

    result = query.order("created_at", desc=True).range((page - 1) * limit, page * limit - 1).execute()
    count_result = sb.table("conversations").select("id", count="exact").eq("project_id", project["id"]).execute()

    rows = result.data or []
    if search:
        s = search.lower()
        rows = [r for r in rows if s in (r.get("user_message") or "").lower() or s in (r.get("agent_response") or "").lower()]

    return {"total": count_result.count or 0, "page": page, "limit": limit, "conversations": rows}


# ── Sessions ──────────────────────────────────────────────────────────────────

@app.get("/sessions", tags=["sessions"])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    project=Depends(require_api_key),
):
    """List unique sessions with turn count and last activity."""
    sb = get_sb()
    convs = (sb.table("conversations")
             .select("session_id,created_at,user_message,is_failure")
             .eq("project_id", project["id"])
             .order("created_at", desc=True)
             .execute().data or [])

    seen: dict[str, dict] = {}
    for c in convs:
        sid = c["session_id"]
        if sid not in seen:
            seen[sid] = {"session_id": sid, "turns": 0, "failures": 0, "last_active": c["created_at"], "first_message": c["user_message"]}
        seen[sid]["turns"] += 1
        if c.get("is_failure"):
            seen[sid]["failures"] += 1

    sessions = sorted(seen.values(), key=lambda x: x["last_active"], reverse=True)
    return {"sessions": sessions[:limit]}


@app.get("/sessions/{session_id}", tags=["sessions"])
async def get_session(session_id: str, project=Depends(require_api_key)):
    """Full session replay — all turns in order."""
    sb = get_sb()
    result = (sb.table("conversations")
              .select("*")
              .eq("project_id", project["id"])
              .eq("session_id", session_id)
              .order("created_at")
              .execute())
    turns = result.data or []
    if not turns:
        raise HTTPException(404, "Session not found")
    return {"session_id": session_id, "turns": turns, "total_turns": len(turns)}


# ── Prompt Lab ────────────────────────────────────────────────────────────────

@app.post("/suggest-prompt", tags=["prompt-lab"])
@limiter.limit("5/minute")
async def suggest_prompt(body: dict, request: Request, project=Depends(require_api_key)):
    sb = get_sb()
    failures = (sb.table("conversations")
                .select("user_message,agent_response,failure_reason")
                .eq("project_id", project["id"])
                .eq("is_failure", True)
                .limit(20).execute())
    all_convs = (sb.table("conversations")
                 .select("intent")
                 .eq("project_id", project["id"])
                 .not_.is_("intent", "null")
                 .execute())

    intent_counts: dict[str, int] = {}
    for c in (all_convs.data or []):
        if c.get("intent"):
            intent_counts[c["intent"]] = intent_counts.get(c["intent"], 0) + 1
    top_intents = [{"intent": k, "cnt": v} for k, v in sorted(intent_counts.items(), key=lambda x: -x[1])[:5]]

    from analyzer import suggest_improved_prompt
    return await suggest_improved_prompt(body.get("current_prompt", ""), failures.data or [], top_intents)


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.get("/alerts/config", tags=["alerts"])
async def get_alert_config(project=Depends(require_api_key)):
    sb = get_sb()
    result = sb.table("projects").select("alert_config").eq("id", project["id"]).execute()
    raw = (result.data or [{}])[0].get("alert_config") or {}
    cfg = raw if isinstance(raw, dict) else json.loads(raw or "{}")
    return {"failure_rate_threshold": cfg.get("failure_rate_threshold", 20.0), "min_conversations": cfg.get("min_conversations", 10), "email_alerts": cfg.get("email_alerts", True)}


@app.put("/alerts/config", tags=["alerts"])
async def update_alert_config(body: AlertConfig, project=Depends(require_api_key)):
    sb = get_sb()
    sb.table("projects").update({"alert_config": body.model_dump()}).eq("id", project["id"]).execute()
    return {"status": "updated", "config": body.model_dump()}


@app.post("/test-alert", tags=["alerts"])
async def test_alert(project=Depends(require_api_key)):
    from alerts import send_failure_alert
    sb = get_sb()
    user = sb.auth.admin.get_user_by_id(project["user_id"])
    email = user.user.email if user and user.user else "unknown@example.com"
    await send_failure_alert(email, project["name"], 30.0, 20, 6, [
        {"user_message": "Can you book a flight for me?", "failure_reason": "Out of scope"},
        {"user_message": "I want a refund", "failure_reason": "Cannot process refunds"},
    ])
    return {"status": "alert sent", "to": email}


# ── Export ────────────────────────────────────────────────────────────────────

@app.get("/export", tags=["export"])
async def export_csv(
    failures_only: bool = False,
    project=Depends(require_api_key),
):
    """Export conversations as CSV."""
    sb = get_sb()
    query = sb.table("conversations").select("*").eq("project_id", project["id"])
    if failures_only:
        query = query.eq("is_failure", True)
    rows = query.order("created_at", desc=True).limit(5000).execute().data or []

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "id", "session_id", "user_message", "agent_response",
        "intent", "sentiment", "is_failure", "failure_reason", "created_at", "metadata",
    ], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)

    filename = f"agentlens_{project['id'][:8]}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── WebSocket real-time feed ──────────────────────────────────────────────────

@app.websocket("/ws/{api_key}")
async def websocket_endpoint(websocket: WebSocket, api_key: str):
    try:
        sb = get_sb()
        result = sb.table("projects").select("id").eq("api_key", api_key).execute()
        if not result.data:
            await websocket.close(code=4001)
            return
        project_id = result.data[0]["id"]
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(websocket, project_id)
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, project_id)
    except Exception:
        ws_manager.disconnect(websocket, project_id)
