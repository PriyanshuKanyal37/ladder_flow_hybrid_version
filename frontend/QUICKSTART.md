# Quick Start (Path B)

## 1. Install
```bash
cd frontend
npm install
```

## 2. Configure Frontend Env
Set in `frontend/.env.local`:
```env
BACKEND_URL=http://localhost:8000
```

## 3. Start Backend
From `voice-agent/backend`:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 4. Start Frontend
From `frontend`:
```bash
npm run dev
```

## 5. Validate
- `GET /api/agent/health` returns `{ "status": "ready" }`
- Start interview flow from `/discover/trending`

## Runtime Notes
- Path B (LiveKit-first) is the only supported voice runtime.
- Legacy Deepgram-only frontend flow is not used.
