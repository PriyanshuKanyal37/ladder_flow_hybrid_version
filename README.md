# LadderFlow — AI Voice Interview Prep

LadderFlow is a full-stack AI-powered interview and podcast preparation platform. It conducts live voice interviews using a real-time voice agent, generates research-backed content angles, and builds a persistent knowledge graph of each session.

---

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 16, React 19, Tailwind CSS v4, TypeScript |
| Backend | FastAPI, Python 3.12, SQLAlchemy (async) |
| Voice Agent | LiveKit Cloud, Deepgram STT, ElevenLabs / Cartesia / Inworld TTS |
| Database | Neon PostgreSQL (asyncpg), Neo4j AuraDB, Upstash Redis |
| Auth | fastapi-users, JWT |
| AI | OpenAI, Anthropic, Perplexity |

---

## Project Structure

```
ladder_flow_ui_hybrid_approach/
├── frontend/          # Next.js app
├── voice-agent/
│   └── backend/       # FastAPI + voice agent process
├── docs/              # Deployment guide
├── ui_theme/          # Design references
└── package.json       # npm workspace root
```

---

## Local Development

### Prerequisites
- Node 20
- Python 3.12
- npm 10+

### Frontend

```bash
# From project root
npm install

cd frontend
cp .env.local.example .env.local   # fill in BACKEND_URL
npm run dev
```

### Backend

```bash
cd voice-agent/backend
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # fill in all keys
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables

### Backend (`voice-agent/backend/.env`)

| Variable | Source |
|----------|--------|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `INTERNAL_SECRET` | Same command, different value |
| `DATABASE_URL` | Neon → Connection Details (asyncpg format) |
| `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` | Neo4j AuraDB |
| `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | LiveKit Cloud |
| `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` | Upstash |
| `OPENAI_API_KEY` | platform.openai.com |
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `PERPLEXITY_API_KEY` | perplexity.ai |
| `DEEPGRAM_API_KEY` | console.deepgram.com |
| `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` | elevenlabs.io |
| `CARTESIA_API_KEY` | cartesia.ai |
| `INWORLD_API_KEY` | inworld.ai |

### Frontend (`frontend/.env.local`)

| Variable | Value |
|----------|-------|
| `BACKEND_URL` | `http://localhost:8000` (local) or internal server URL |

---

## Deployment

See [docs/DIGITALOCEAN_DEPLOYMENT.md](docs/DIGITALOCEAN_DEPLOYMENT.md) for the complete guide — covers Droplet setup, nginx, SSL, systemd, PM2, GitHub Actions CI/CD, and full pricing breakdown (~$0.60–$1.00 per 30-min interview session).

---

## Notes

- Backend must run with `--workers 1`. The voice agent is spawned as a child process on startup — multiple workers cause conflicts.
- `npm install` / `npm ci` must be run from the **project root** (not `frontend/`) due to npm workspace hoisting.
