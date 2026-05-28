<div align="center">

```
 █████╗  ██████╗ ███████╗███╗   ██╗████████╗██╗     ███████╗███╗   ██╗███████╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██║     ██╔════╝████╗  ██║██╔════╝
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║     █████╗  ██╔██╗ ██║███████╗
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║     ██╔══╝  ██║╚██╗██║╚════██║
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████╗███████╗██║ ╚████║███████║
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝
```

**Know exactly what your AI agent is doing wrong.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-agent--lens--two.vercel.app-00ff88?style=for-the-badge&logo=vercel&logoColor=black)](https://agent-lens-two.vercel.app)
[![Backend](https://img.shields.io/badge/API-Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://shraman18-agentlens-backend.hf.space/docs)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Built with](https://img.shields.io/badge/Built_with-FastAPI_+_React-009688?style=for-the-badge)](https://fastapi.tiangolo.com)

</div>

---

## ⚡ What is AgentLens?

Most developers ship AI agents and have **no idea** what's happening inside them.

AgentLens fixes that. It logs every conversation, automatically extracts user intent and sentiment using AI, detects failures before users churn, and suggests exactly how to improve your system prompt — all in real time.

```
User asks → Agent responds → AgentLens logs it
                                    ↓
                          AI extracts intent
                          Detects failures
                          Tracks sentiment
                                    ↓
                          Dashboard shows patterns
                          Prompt Lab fixes them
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 📡 **Conversation Logging** | One line of Python to capture every chat |
| 🧠 **Intent Extraction** | AI auto-labels what every user was trying to do |
| 💥 **Failure Detection** | Catches where your agent failed or frustrated users |
| 😤 **Sentiment Analysis** | Positive / Neutral / Negative breakdown |
| ⚡ **Prompt Lab** | AI analyzes failures and rewrites your system prompt |
| 🔄 **Auto-Analysis** | Runs every hour — no manual clicks needed |
| 👥 **Multi-tenant** | Each user gets their own project and API key |
| 🔑 **Auth System** | Signup / login with Supabase |

---

## 🚀 Quick Start

### 1. Clone
```bash
git clone https://github.com/Shraman123/AgentLens.git
cd AgentLens
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt

# Set your keys
export GROQ_API_KEY=gsk_...
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_KEY=eyJ...

uvicorn app:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install

REACT_APP_API_URL=http://localhost:8000 npm start
```

### 4. Open
```
http://localhost:3000
```

---

## 📡 Integrate in 1 Line

```python
from agentlens import AgentLens

lens = AgentLens(api_key="ak_your_key", base_url="https://your-backend.hf.space")

# Decorator — auto-logs everything
@lens.watch
def my_agent(user_message: str) -> str:
    return call_your_llm(user_message)

# That's it. Every conversation is now logged and analyzed.
my_agent("How do I reset my password?")
```

### Async support
```python
@lens.watch_async
async def my_agent(user_message: str) -> str:
    return await call_your_llm(user_message)
```

### Direct HTTP
```bash
curl -X POST https://your-backend.hf.space/log \
  -H "x-api-key: ak_your_key" \
  -H "Content-Type: application/json" \
  -d '{"user_message": "Hello", "agent_response": "Hi there!"}'
```

---

## 📋 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | — | Health check |
| `POST` | `/auth/signup` | — | Create account |
| `POST` | `/auth/login` | — | Sign in |
| `GET` | `/projects` | Bearer | List your projects |
| `POST` | `/projects` | Bearer | Create project |
| `POST` | `/log` | API Key | Log a conversation |
| `POST` | `/analyze` | API Key | Analyze conversations |
| `GET` | `/dashboard` | API Key | Get dashboard stats |
| `GET` | `/conversations` | API Key | List conversations |
| `POST` | `/suggest-prompt` | API Key | Get prompt suggestion |

---

## 🏗 Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Your AI Agent  │────▶│  AgentLens API   │────▶│    Supabase     │
│                 │     │  (FastAPI + HF)   │     │   (Postgres)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                  │                        │
                                  ▼                        ▼
                         ┌──────────────────┐    ┌─────────────────┐
                         │   Groq / LLM     │    │  React Dashboard │
                         │ (Intent extract) │    │    (Vercel)      │
                         └──────────────────┘    └─────────────────┘
```

---

## 🚢 Deploy Free

| Service | What | Cost |
|---|---|---|
| **Hugging Face Spaces** | Backend API | Free |
| **Vercel** | Frontend dashboard | Free |
| **Supabase** | Database + Auth | Free |
| **Groq** | AI analysis | Free |

**Total: $0/month** for up to ~50k conversations analyzed.

### Deploy Backend (Hugging Face)
1. Fork this repo
2. Create a new Space → Docker
3. Add secrets: `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
4. Push `backend/` files to the Space

### Deploy Frontend (Vercel)
1. Import repo to Vercel
2. Set root directory: `frontend`
3. Add env vars: `REACT_APP_API_URL`, `REACT_APP_API_KEY`
4. Deploy

---

## 🗺 Roadmap

- [x] Conversation logging
- [x] AI intent extraction
- [x] Failure detection
- [x] Sentiment analysis
- [x] Prompt Lab
- [x] Auto-analysis scheduler
- [x] Multi-tenant auth
- [ ] Email alerts on failure spikes
- [ ] Slack / Discord notifications
- [ ] OpenTelemetry ingestion
- [ ] Prompt version history
- [ ] A/B testing for prompts
- [ ] CSV export

---

## 💰 Cost to Run

| Conversations analyzed | Monthly cost |
|---|---|
| 10,000 | ~$0 (Groq free tier) |
| 100,000 | ~$1-2 |
| 1,000,000 | ~$10-20 |

---

## 🛠 Stack

- **Backend** — FastAPI, Supabase, APScheduler
- **AI** — Groq (llama-3.3-70b), free tier
- **Frontend** — React, Recharts, React Query, TanStack
- **Auth** — Supabase Auth
- **Hosting** — Hugging Face Spaces + Vercel

---

## 📄 License

MIT — free to use, modify, and build on.

---

<div align="center">

Built in public · Star ⭐ if this helped you

**[Live Demo](https://agent-lens-two.vercel.app) · [API Docs](https://shraman18-agentlens-backend.hf.space/docs) · [Landing Page](https://agent-lens-1fgl.vercel.app)**

</div>
