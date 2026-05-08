# Frontend Migration Audit - ElevenLabs Frontend Into Hybrid

Date: 2026-05-04

## Scope

Source frontend copied from:

`C:\Users\priya\Desktop\Ladder\ladderflow_version\ladder_flow_Elevenlabs_Approach\frontend`

Target frontend updated in:

`C:\Users\priya\Desktop\Ladder\ladderflow_version\ladder_flow_ui_hybrid_approach\frontend`

Only Hybrid project files were changed. The ElevenLabs project was used as a read-only source. Hybrid backend and `voice-agent` files were not modified.

## What Was Changed

The Hybrid `frontend` was mechanically updated to match the ElevenLabs `frontend` source files, excluding ignored/generated directories:

- Excluded: `node_modules`
- Excluded: `.next`
- Excluded: `graphify-out`
- Excluded: `tsconfig.tsbuildinfo`

Primary migrated areas:

- `frontend/app`
- `frontend/components`
- `frontend/hooks`
- `frontend/lib`
- `frontend/public`
- `frontend/package.json`
- `frontend/package-lock.json`
- frontend config/docs files such as `next.config.ts`, `tsconfig.json`, `README.md`, and API docs

## Important Runtime Differences Now Present In Hybrid Frontend

The migrated frontend expects the ElevenLabs-style voice client:

- `@elevenlabs/react`
- `frontend/hooks/useElevenLabsAgent.ts`
- `frontend/app/(dashboard)/interview/page.tsx`
- `provider: "elevenlabs"` session responses
- one of `agentId`, `conversationToken`, or `signedUrl`

The migrated frontend also includes LiveKit fallback typing in `frontend/lib/types/agent.ts`, but the active interview page imported from ElevenLabs uses `useElevenLabsAgent`.

## Backend/API Endpoints Expected By Migrated Frontend

These frontend routes proxy to backend endpoints and must exist in whichever backend you connect:

- `POST /content-pack/analyze`
- `POST /content-pack/generate`
- `GET /content-pack/{interview_id}`
- `PATCH /content-outputs/{output_id}`
- `DELETE /content-outputs/{output_id}`
- `POST /content-outputs/{output_id}/regenerate`

Existing voice/session endpoints still referenced:

- `GET /ready`
- `POST /agent-config`
- `POST /agent-config/resume`
- `POST /agent-dispatch`
- `POST /extract`
- `GET /interviews`
- `POST /interviews`
- `GET /interviews/{id}`
- `PATCH /interviews/{id}`
- `POST /interviews/{id}/autosave`
- `POST /interviews/{id}/finalize-draft`
- `GET /posts`
- `PATCH /posts/{interview_id}/{platform}`
- `DELETE /posts/{interview_id}/{platform}`

## Backend Work Not Done Here

Per instruction, no backend files were changed.

If Hybrid backend is not already compatible with this frontend, likely backend work is:

- Add or wire content-pack routes.
- Add or wire content-output routes.
- Ensure `/agent-config` returns the session shape expected by the active frontend voice page.
- Ensure auth headers pass through for all proxied API routes.
- Ensure content pack generation returns `ContentPackResponse` with `summary`, `signals`, `theme_clusters`, `outputs`, and `interview`.
- Ensure posts returned by `/posts` may include optional `output_id` for newer content-output editing/regeneration paths.

## DB Notes

No DB changes were made by this migration.

The migrated frontend assumes backend support for saved content outputs. If the Hybrid backend database is not already migrated, expected backend schema support includes:

- `interviews.content_pack_summary`
- `content_outputs` table
- `content_outputs.interview_id`
- `content_outputs.user_id`
- `content_outputs.platform`
- `content_outputs.content_type`
- `content_outputs.raw_content`
- `content_outputs.edited_content`
- `content_outputs.status`
- `content_outputs.signal_snapshot`
- `content_outputs.generation_metadata`

## Validation Performed

Frontend source-to-target file comparison was run after copy:

`All copied source frontend files match target.`

Dependency install was run from Hybrid `frontend`:

```powershell
npm install
```

Result:

- Install completed.
- npm reported 9 audit vulnerabilities: 5 moderate, 4 high.
- No audit fix was applied.

Lint was run from Hybrid `frontend`:

```powershell
npm run lint
```

Result:

- Exit code 0.
- 0 errors.
- 8 warnings.

Build was run from Hybrid `frontend`:

```powershell
npm run build
```

Result:

- Exit code 0.
- Next.js production build completed.
- 38 app pages generated.
- Build warning: Next.js inferred workspace root from `C:\Users\priya\package-lock.json`; set `turbopack.root` in `next.config.ts` if this warning should be silenced.

Dev server was started from Hybrid `frontend`:

```powershell
npm run dev -- --port 3000
```

Result:

- Local URL: `http://localhost:3000`
- Probe result: `HTTP 200 OK`
- Logs: `frontend/.codex-dev/next-dev.out.log` and `frontend/.codex-dev/next-dev.err.log`

## Suggested Validation Next

From Hybrid `frontend`:

```powershell
npm install
npm run lint
npm run build
npm run dev
```

Manual app checks:

- Login/signup render.
- Dashboard shell renders.
- Discover/trending flow stores research context.
- Interview setup calls `/api/agent/config`.
- Interview page handles returned session shape.
- Debrief calls `/api/content-pack/analyze`.
- Generate pack calls `/api/content-pack/generate`.
- Review page loads `/api/content-pack/{interview_id}`.
- Posts page can edit/archive legacy posts and newer `content_outputs`.

## Risk Summary

The main risk is backend contract mismatch, not frontend copy integrity. The active migrated interview page is ElevenLabs-oriented. If Hybrid backend still returns LiveKit-only sessions, the interview page will show session setup/loading errors until backend/session contract is adjusted or the page is adapted back to LiveKit.
