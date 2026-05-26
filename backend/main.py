from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
import uuid
import time
import os
from datetime import datetime
from contextlib import asynccontextmanager
from analyzer import analyze_conversations_batch

DB_PATH = "data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT,
            user_message TEXT NOT NULL,
            agent_response TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            intent TEXT,
            sentiment TEXT,
            is_failure INTEGER DEFAULT 0,
            failure_reason TEXT,
            analyzed INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS insights (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prompt_suggestions (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            original_prompt TEXT,
            suggested_prompt TEXT NOT NULL,
            reasoning TEXT,
            applied INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        );

        -- seed a demo project
        INSERT OR IGNORE INTO projects (id, name, api_key, created_at)
        VALUES ('demo-project-1', 'My AI Agent', 'ak_demo_123456789', unixepoch());
    """)
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AgentLens API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth helper ──────────────────────────────────────────────────────────────

def get_project_by_key(api_key: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM projects WHERE api_key = ?", (api_key,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return dict(row)

# ── Models ───────────────────────────────────────────────────────────────────

class LogRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: str
    agent_response: str
    metadata: Optional[dict] = {}

class ProjectCreate(BaseModel):
    name: str

class AnalyzeRequest(BaseModel):
    limit: Optional[int] = 50

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/projects")
def create_project(body: ProjectCreate):
    conn = get_db()
    project = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "api_key": f"ak_{uuid.uuid4().hex[:20]}",
        "created_at": int(time.time())
    }
    conn.execute(
        "INSERT INTO projects VALUES (:id, :name, :api_key, :created_at)",
        project
    )
    conn.commit()
    conn.close()
    return project


@app.post("/log")
def log_conversation(body: LogRequest, x_api_key: str = Header(...)):
    project = get_project_by_key(x_api_key)
    conn = get_db()
    conv = {
        "id": str(uuid.uuid4()),
        "project_id": project["id"],
        "session_id": body.session_id or str(uuid.uuid4()),
        "user_message": body.user_message,
        "agent_response": body.agent_response,
        "metadata": json.dumps(body.metadata or {}),
        "created_at": int(time.time())
    }
    conn.execute("""
        INSERT INTO conversations
        (id, project_id, session_id, user_message, agent_response, metadata, created_at)
        VALUES (:id, :project_id, :session_id, :user_message, :agent_response, :metadata, :created_at)
    """, conv)
    conn.commit()
    conn.close()
    return {"id": conv["id"], "status": "logged"}


@app.post("/analyze")
async def trigger_analysis(body: AnalyzeRequest, x_api_key: str = Header(...)):
    project = get_project_by_key(x_api_key)
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM conversations
        WHERE project_id = ? AND analyzed = 0
        ORDER BY created_at DESC LIMIT ?
    """, (project["id"], body.limit)).fetchall()
    conn.close()

    if not rows:
        return {"message": "No unanalyzed conversations", "analyzed": 0}

    conversations = [dict(r) for r in rows]
    results = await analyze_conversations_batch(conversations)

    conn = get_db()
    for result in results:
        conn.execute("""
            UPDATE conversations
            SET intent=?, sentiment=?, is_failure=?, failure_reason=?, analyzed=1
            WHERE id=?
        """, (
            result.get("intent"),
            result.get("sentiment"),
            1 if result.get("is_failure") else 0,
            result.get("failure_reason"),
            result["id"]
        ))

    # store insights
    if results:
        insight_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO insights (id, project_id, type, title, description, count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            insight_id,
            project["id"],
            "analysis_run",
            f"Analysis completed",
            f"Analyzed {len(results)} conversations",
            len(results),
            int(time.time())
        ))

    conn.commit()
    conn.close()
    return {"analyzed": len(results), "results": results}


@app.get("/dashboard")
def get_dashboard(x_api_key: str = Header(...)):
    project = get_project_by_key(x_api_key)
    pid = project["id"]
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM conversations WHERE project_id=?", (pid,)).fetchone()[0]
    analyzed = conn.execute("SELECT COUNT(*) FROM conversations WHERE project_id=? AND analyzed=1", (pid,)).fetchone()[0]
    failures = conn.execute("SELECT COUNT(*) FROM conversations WHERE project_id=? AND is_failure=1", (pid,)).fetchone()[0]

    # top intents
    intents = conn.execute("""
        SELECT intent, COUNT(*) as count FROM conversations
        WHERE project_id=? AND intent IS NOT NULL
        GROUP BY intent ORDER BY count DESC LIMIT 10
    """, (pid,)).fetchall()

    # sentiment breakdown
    sentiments = conn.execute("""
        SELECT sentiment, COUNT(*) as count FROM conversations
        WHERE project_id=? AND sentiment IS NOT NULL
        GROUP BY sentiment
    """, (pid,)).fetchall()

    # recent conversations
    recent = conn.execute("""
        SELECT id, session_id, user_message, agent_response, intent, sentiment,
               is_failure, failure_reason, created_at
        FROM conversations WHERE project_id=?
        ORDER BY created_at DESC LIMIT 20
    """, (pid,)).fetchall()

    # daily volume last 7 days
    daily = conn.execute("""
        SELECT date(created_at, 'unixepoch') as day, COUNT(*) as count
        FROM conversations WHERE project_id=?
        GROUP BY day ORDER BY day DESC LIMIT 7
    """, (pid,)).fetchall()

    conn.close()

    return {
        "project": project,
        "stats": {
            "total": total,
            "analyzed": analyzed,
            "failures": failures,
            "failure_rate": round(failures / total * 100, 1) if total else 0
        },
        "top_intents": [dict(r) for r in intents],
        "sentiments": [dict(r) for r in sentiments],
        "recent_conversations": [dict(r) for r in recent],
        "daily_volume": [dict(r) for r in daily]
    }


@app.get("/conversations")
def list_conversations(
    page: int = 1,
    limit: int = 20,
    intent: Optional[str] = None,
    sentiment: Optional[str] = None,
    failures_only: bool = False,
    x_api_key: str = Header(...)
):
    project = get_project_by_key(x_api_key)
    pid = project["id"]
    offset = (page - 1) * limit

    where = ["project_id = ?"]
    params = [pid]
    if intent:
        where.append("intent = ?"); params.append(intent)
    if sentiment:
        where.append("sentiment = ?"); params.append(sentiment)
    if failures_only:
        where.append("is_failure = 1")

    where_sql = " AND ".join(where)
    conn = get_db()
    total = conn.execute(f"SELECT COUNT(*) FROM conversations WHERE {where_sql}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM conversations WHERE {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()

    return {
        "total": total,
        "page": page,
        "conversations": [dict(r) for r in rows]
    }


@app.post("/suggest-prompt")
async def suggest_prompt(
    body: dict,
    x_api_key: str = Header(...)
):
    project = get_project_by_key(x_api_key)
    current_prompt = body.get("current_prompt", "")

    conn = get_db()
    failures = conn.execute("""
        SELECT user_message, agent_response, failure_reason FROM conversations
        WHERE project_id=? AND is_failure=1
        ORDER BY created_at DESC LIMIT 20
    """, (project["id"],)).fetchall()
    top_intents = conn.execute("""
        SELECT intent, COUNT(*) as cnt FROM conversations
        WHERE project_id=? AND intent IS NOT NULL
        GROUP BY intent ORDER BY cnt DESC LIMIT 5
    """, (project["id"],)).fetchall()
    conn.close()

    from analyzer import suggest_improved_prompt
    suggestion = await suggest_improved_prompt(
        current_prompt,
        [dict(f) for f in failures],
        [dict(i) for i in top_intents]
    )

    conn = get_db()
    conn.execute("""
        INSERT INTO prompt_suggestions (id, project_id, original_prompt, suggested_prompt, reasoning, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), project["id"], current_prompt,
          suggestion["suggested_prompt"], suggestion["reasoning"], int(time.time())))
    conn.commit()
    conn.close()
    return suggestion
