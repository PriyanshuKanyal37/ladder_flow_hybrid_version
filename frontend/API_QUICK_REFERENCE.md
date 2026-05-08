# API Quick Reference (Path B)

## Backend Base URL
- `BACKEND_URL` environment variable (frontend server-side routes)

## Health
- `GET /api/agent/health` -> backend `/ready`
- Success when response status is `200` and payload status is `ready`.

## Voice Session
- `POST /api/agent/config` -> create interview + LiveKit join token
- `POST /api/agent/dispatch` -> dispatch worker after room join

## Interview Persistence
- `GET /api/interviews`
- `GET /api/interviews/[id]`
- `PATCH /api/interviews/[id]`

## Post-Call Processing
- `POST /api/content/linkedin`
- `POST /api/content/twitter`
- `POST /api/content/newsletter`
- `POST /api/agent/extract`

## Runtime Truth
Use these docs for architecture and behavior:
- `frontend/README.md`
- `voice-agent/backend/README.md`
