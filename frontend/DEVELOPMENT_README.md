# Frontend Development Guide (Path B)

## Architecture
- Next.js App Router frontend
- LiveKit client room + audio transport
- Backend worker dispatch after room connect
- Transcript rendering from:
  - LiveKit data channel final transcript events
  - LiveKit transcription interim segments

## Key Files
- `frontend/hooks/useLiveKitAgent.ts`
- `frontend/app/(dashboard)/interview/page.tsx`
- `frontend/app/(dashboard)/review/[id]/page.tsx`
- `frontend/lib/api/agent.ts`
- `frontend/lib/types/agent.ts`

## Environment
- `BACKEND_URL` for server-side API proxy routes

## Pipeline
1. Discover topic
2. Create agent config
3. Connect room
4. Dispatch worker
5. Capture transcript/state in real time
6. End call and persist interview/content
7. Run memory extraction in background

## Deprecated
Previous Deepgram-first documentation is archived and no longer applies to runtime.
