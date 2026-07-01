from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import uuid
import time
import os
from datetime import datetime
from contextlib import asynccontextmanager
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bvenpvqygtmykrnssary.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title="AgentLens API v2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth helpers ─────────────────────────────────────────────────────────────

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.replace("Bearer ", "")
    try:
        sb = get_sb()
        result = sb.auth.get_user(token)
        if not result or not result.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return result.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

def get_project_by_apikey(api_key: str):
    sb = get_sb()
    result = sb.table("projects").select("*").eq("api_key", api_key).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return result.data[0]

# ── Models ────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str

class LogRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: str
    agent_response: str
    metadata: Optional[dict] = {}

class AnalyzeRequest(BaseModel):
    limit: Optional[int] = 50

# ── Auth routes ───────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.post("/auth/signup")
async def signup(body: dict):
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    try:
        sb = get_sb()
        result = sb.auth.sign_up({"email": email, "password": password})
        if result.user:
            # auto-create first project
            project = {
                "id": str(uuid.uuid4()),
                "user_id": result.user.id,
                "name": "My AI Agent",
                "api_key": f"ak_{uuid.uuid4().hex[:20]}",
                "created_at": datetime.utcnow().isoformat()
            }
            sb.table("projects").insert(project).execute()
            return {"user": {"id": result.user.id, "email": result.user.email}, "project": project}
        raise HTTPException(status_code=400, detail="Signup failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(body: dict):
    email = body.get("email")
    password = body.get("password")
    try:
        sb = get_sb()
        result = sb.auth.sign_in_with_password({"email": email, "password": password})
        if result.user and result.session:
            return {
                "access_token": result.session.access_token,
                "user": {"id": result.user.id, "email": result.user.email}
            }
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# ── Project routes ────────────────────────────────────────────────────────────

@app.get("/projects")
async def list_projects(user=Depends(get_current_user)):
    sb = get_sb()
    result = sb.table("projects").select("*").eq("user_id", user.id).execute()
    return result.data or []

@app.post("/projects")
async def create_project(body: ProjectCreate, user=Depends(get_current_user)):
    sb = get_sb()
    project = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "name": body.name,
        "api_key": f"ak_{uuid.uuid4().hex[:20]}",
        "created_at": datetime.utcnow().isoformat()
    }
    sb.table("projects").insert(project).execute()
    return project

# ── Logging ───────────────────────────────────────────────────────────────────

@app.post("/log")
async def log_conversation(body: LogRequest, x_api_key: str = Header(...)):
    project = get_project_by_apikey(x_api_key)
    sb = get_sb()
    conv = {
        "id": str(uuid.uuid4()),
        "project_id": project["id"],
        "session_id": body.session_id or str(uuid.uuid4()),
        "user_message": body.user_message,
        "agent_response": body.agent_response,
        "metadata": json.dumps(body.metadata or {}),
        "analyzed": False,
        "is_failure": False,
        "created_at": datetime.utcnow().isoformat()
    }
    sb.table("conversations").insert(conv).execute()
    return {"id": conv["id"], "status": "logged"}

# ── Analysis ──────────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze(body: AnalyzeRequest, x_api_key: str = Header(...)):
    project = get_project_by_apikey(x_api_key)
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
            "analyzed": True
        }).eq("id", r["id"]).execute()

    return {"analyzed": len(results), "results": results}

# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard")
async def dashboard(x_api_key: str = Header(...)):
    project = get_project_by_apikey(x_api_key)
    sb = get_sb()
    pid = project["id"]

    all_convs = sb.table("conversations").select("*").eq("project_id", pid).execute()
    convs = all_convs.data or []

    total = len(convs)
    analyzed = sum(1 for c in convs if c.get("analyzed"))
    failures = sum(1 for c in convs if c.get("is_failure"))

    # intents
    intent_counts = {}
    for c in convs:
        if c.get("intent"):
            intent_counts[c["intent"]] = intent_counts.get(c["intent"], 0) + 1
    top_intents = sorted([{"intent": k, "count": v} for k, v in intent_counts.items()], key=lambda x: -x["count"])[:10]

    # sentiments
    sent_counts = {}
    for c in convs:
        if c.get("sentiment"):
            sent_counts[c["sentiment"]] = sent_counts.get(c["sentiment"], 0) + 1
    sentiments = [{"sentiment": k, "count": v} for k, v in sent_counts.items()]

    # recent
    recent = sorted(convs, key=lambda x: x.get("created_at", ""), reverse=True)[:20]

    # daily volume
    daily_counts = {}
    for c in convs:
        day = c.get("created_at", "")[:10]
        if day:
            daily_counts[day] = daily_counts.get(day, 0) + 1
    daily = sorted([{"day": k, "count": v} for k, v in daily_counts.items()])[-7:]

    return {
        "project": project,
        "stats": {
            "total": total,
            "analyzed": analyzed,
            "failures": failures,
            "failure_rate": round(failures / total * 100, 1) if total else 0
        },
        "top_intents": top_intents,
        "sentiments": sentiments,
        "recent_conversations": recent,
        "daily_volume": daily
    }

@app.get("/conversations")
async def list_conversations(
    page: int = 1,
    limit: int = 20,
    intent: Optional[str] = None,
    sentiment: Optional[str] = None,
    failures_only: bool = False,
    x_api_key: str = Header(...)
):
    project = get_project_by_apikey(x_api_key)
    sb = get_sb()
    query = sb.table("conversations").select("*").eq("project_id", project["id"])
    if intent:
        query = query.eq("intent", intent)
    if sentiment:
        query = query.eq("sentiment", sentiment)
    if failures_only:
        query = query.eq("is_failure", True)

    result = query.order("created_at", desc=True).range((page-1)*limit, page*limit-1).execute()
    total_result = sb.table("conversations").select("id", count="exact").eq("project_id", project["id"]).execute()

    return {
        "total": total_result.count or 0,
        "page": page,
        "conversations": result.data or []
    }

@app.post("/suggest-prompt")
async def suggest_prompt(body: dict, x_api_key: str = Header(...)):
    project = get_project_by_apikey(x_api_key)
    sb = get_sb()

    failures = sb.table("conversations").select("user_message,agent_response,failure_reason")\
        .eq("project_id", project["id"]).eq("is_failure", True).limit(20).execute()
    top_intents = []
    all_convs = sb.table("conversations").select("intent")\
        .eq("project_id", project["id"]).not_.is_("intent", "null").execute()

    intent_counts = {}
    for c in (all_convs.data or []):
        if c.get("intent"):
            intent_counts[c["intent"]] = intent_counts.get(c["intent"], 0) + 1
    top_intents = [{"intent": k, "cnt": v} for k, v in sorted(intent_counts.items(), key=lambda x: -x[1])[:5]]

    from analyzer import suggest_improved_prompt
    suggestion = await suggest_improved_prompt(
        body.get("current_prompt", ""),
        failures.data or [],
        top_intents
    )
    return suggestion

@app.post("/test-alert")
async def test_alert(x_api_key: str = Header(...)):
    project = get_project_by_apikey(x_api_key)
    from alerts import send_failure_alert
    sb = get_sb()
    user = sb.auth.admin.get_user_by_id(project["user_id"])
    email = user.user.email if user and user.user else "shraman.foruppo@gmail.com"
    await send_failure_alert(
        to_email=email,
        project_name=project["name"],
        failure_rate=30.0,
        total=20,
        failures=6,
        top_failures=[
            {"user_message": "Can you book a flight for me?", "failure_reason": "Out of scope request"},
            {"user_message": "I want a refund", "failure_reason": "Agent cannot process refunds"},
            {"user_message": "This is broken!", "failure_reason": "User frustration detected"},
        ]
    )
    return {"status": "alert sent", "to": email}
