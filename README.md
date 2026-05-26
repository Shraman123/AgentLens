# AgentLens — Self-Improving Layer for AI Agents

Your open-source alternative to Agnost AI. Logs every conversation, analyzes intent + sentiment, detects failures, and suggests prompt improvements.

---

## Stack
- **Backend**: FastAPI + SQLite + Anthropic API
- **Frontend**: React + Recharts + React Query
- **SDK**: Python (sync + async + decorator)
- **Infra**: Docker Compose

---

## 🚀 Quick Start (5 minutes)

### 1. Clone & setup env
```bash
git clone <your-repo>
cd agnost-clone
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Start everything
```bash
docker-compose up --build
```

Or run manually:

**Backend:**
```bash
cd backend
pip install -r requirements.txt
ANTHROPIC_API_KEY=sk-ant-... uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

### 3. Open dashboard
http://localhost:3000

---

## 📡 Logging Conversations

### Python SDK (simplest)
```python
from agentlens import AgentLens

lens = AgentLens(api_key="ak_demo_123456789", base_url="http://localhost:8000")

# Log manually
lens.log(
    user_message="How do I reset my password?",
    agent_response="Click Forgot Password on the login page.",
    session_id="user-123"
)

# Or use the decorator — auto-logs everything
@lens.watch
def my_agent(user_message: str) -> str:
    return call_your_llm(user_message)

my_agent("What's the pricing?")
```

### Async
```python
@lens.watch_async
async def my_agent(user_message: str) -> str:
    return await call_your_llm(user_message)
```

### Direct HTTP
```bash
curl -X POST http://localhost:8000/log \
  -H "x-api-key: ak_demo_123456789" \
  -H "Content-Type: application/json" \
  -d '{"user_message": "Hello", "agent_response": "Hi there!"}'
```

---

## 🔍 Running Analysis

Triggers AI analysis of all unanalyzed conversations:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "x-api-key: ak_demo_123456789" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

Or click **"Run Analysis"** in the dashboard.

---

## 🌱 Seed Demo Data

```bash
cd backend
pip install httpx
python seed.py
# Then run analysis from dashboard
```

---

## 📋 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/log` | Log a conversation |
| POST | `/analyze` | Analyze unanalyzed conversations |
| GET | `/dashboard` | Get all dashboard stats |
| GET | `/conversations` | List conversations (paginated, filterable) |
| POST | `/suggest-prompt` | Get AI prompt improvement suggestion |
| POST | `/projects` | Create a new project |

All endpoints require `x-api-key` header.

---

## 🔑 Creating More Projects / API Keys

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Second Agent"}'
# Returns: {"id": "...", "api_key": "ak_...", ...}
```

---

## 🚢 Deploy Free

**Backend → Railway:**
```bash
# Connect GitHub repo to Railway
# Set env var: ANTHROPIC_API_KEY=sk-ant-...
# Railway auto-detects Dockerfile
```

**Frontend → Vercel:**
```bash
cd frontend
npx vercel
# Set env: REACT_APP_API_URL=https://your-backend.railway.app
```

---

## 🗺 Roadmap (What to Build Next)

- [ ] Auto-run analysis on a schedule (APScheduler)
- [ ] Email/Slack alerts when failure rate spikes
- [ ] Multi-tenant auth (JWT)
- [ ] OpenTelemetry ingestion endpoint
- [ ] Prompt version history
- [ ] A/B testing for prompts
- [ ] Webhook notifications

---

## 💰 Cost Estimate

| Usage | Monthly Cost |
|-------|-------------|
| 1,000 conversations analyzed | ~$0.05 |
| 10,000 conversations analyzed | ~$0.50 |
| 100,000 conversations analyzed | ~$5.00 |

Analysis uses Claude Sonnet in batch mode — extremely cheap.
