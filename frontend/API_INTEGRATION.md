# API Integration Guide (Path B)

This project now runs on a LiveKit-first voice pipeline (Path B).

## Source Of Truth
- `frontend/README.md`
- `voice-agent/backend/README.md`

## Active Frontend API Routes
- `POST /api/agent/config` -> backend `/agent-config`
- `POST /api/agent/dispatch` -> backend `/agent-dispatch`
- `GET /api/agent/health` -> backend `/ready`
- `POST /api/agent/extract` -> backend `/extract`
- `GET /api/interviews`
- `GET /api/interviews/[id]`
- `PATCH /api/interviews/[id]`
- `POST /api/content/linkedin`
- `POST /api/content/twitter`
- `POST /api/content/newsletter`

## Path B Session Order
1. Create session via `/api/agent/config`.
2. Join LiveKit room from frontend with returned token.
3. Dispatch worker via `/api/agent/dispatch` after room connect.
4. Stream transcripts via LiveKit events/data channel.
5. End call, persist transcript/content to interview row.
6. Trigger `/api/agent/extract` for background memory extraction.

## Notes
- Legacy Deepgram WebSocket flow is removed from runtime.
- Do not use old `deepgramConfig` docs for current implementation.
