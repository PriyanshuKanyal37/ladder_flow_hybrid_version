# LadderFlow DigitalOcean Deployment Guide

Last updated: 2026-05-08

This guide is written for a beginner deploying this exact repository:

- Frontend: `frontend` - Next.js 16, React 19
- Backend: `voice-agent/backend` - FastAPI, SQLAlchemy, LiveKit worker child process
- Voice: LiveKit Cloud room + LiveKit Agents worker, Deepgram STT, Anthropic LLM, ElevenLabs TTS
- Data: PostgreSQL with pgvector, Neo4j Aura, Upstash Redis REST

The recommended beginner path is:

1. Deploy the backend as one DigitalOcean App Platform app.
2. Deploy the frontend as a second DigitalOcean App Platform app.
3. Use DigitalOcean Managed PostgreSQL / Vector Database for Postgres.
4. Keep Neo4j on Neo4j Aura because DigitalOcean Managed Databases do not include Neo4j.
5. Keep Upstash Redis because the current backend uses the Upstash REST client, not raw Redis/Valkey TCP.

Do not deploy production traffic until the security checklist in this guide is complete.

## What DigitalOcean Pieces Mean

DigitalOcean App Platform is a managed platform. You connect a GitHub repo, choose a folder, set build/run commands and environment variables, and DigitalOcean builds and runs containers for you.

For this project:

- A "service" is a web app that receives HTTP traffic.
- The backend service runs FastAPI and starts `agent_worker.py` automatically during startup.
- The frontend service runs `next start`.
- A "managed database" is a database DigitalOcean operates for you.
- App Platform local disk is not persistent. Do not store uploads or user data on local files.
- Environment variables are where you put secrets and URLs.

## Current Project Findings

The repo currently has:

- No Dockerfiles.
- No DigitalOcean app spec.
- No GitHub remote configured in this local checkout.
- A root Git branch named `master`.
- Next.js dependencies under `frontend/package.json`.
- Python dependencies under `voice-agent/backend/requirements.txt`.
- Backend env template at `voice-agent/backend/.env.example`.
- Additive migration scripts, but no one-file baseline migration for a brand new database.

That last point matters. If you already have the existing Neon Postgres database from development, the fastest deployment is to keep using it first. If you want a fresh DigitalOcean Postgres database, use the "Fresh DigitalOcean Postgres" section below.

## Source Docs Checked

DigitalOcean docs used for this guide:

- App Platform overview: https://docs.digitalocean.com/products/app-platform/
- Create apps: https://docs.digitalocean.com/products/app-platform/how-to/create-apps/
- Monorepos: https://docs.digitalocean.com/products/app-platform/how-to/deploy-from-monorepo/
- Environment variables and bindable variables: https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/
- Python buildpack: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/python/
- Node.js buildpack: https://docs.digitalocean.com/products/app-platform/reference/buildpacks/nodejs/
- App spec reference: https://docs.digitalocean.com/products/app-platform/reference/app-spec/
- App Platform limits: https://docs.digitalocean.com/products/app-platform/details/limits/
- App Platform availability: https://docs.digitalocean.com/products/app-platform/details/availability/
- App Platform logs: https://docs.digitalocean.com/products/app-platform/how-to/view-logs/
- App Platform console: https://docs.digitalocean.com/products/app-platform/how-to/console/
- App Platform health checks: https://docs.digitalocean.com/products/app-platform/how-to/manage-health-checks/
- Managed Databases: https://docs.digitalocean.com/products/databases/
- PostgreSQL vector database / pgvector: https://docs.digitalocean.com/products/vector-databases/postgresql/
- Domains: https://docs.digitalocean.com/products/app-platform/how-to/manage-domains/

Other official docs:

- Next.js Node requirement: https://nextjs.org/docs/pages/getting-started/installation
- Neo4j Aura connection: https://neo4j.com/docs/aura/getting-started/connect-instance/
- Upstash Redis REST: https://upstash.com/docs/redis/howto/connectwithupstashredis
- Deepgram API keys: https://developers.deepgram.com/docs/create-additional-api-keys
- ElevenLabs API authentication: https://elevenlabs.io/docs/api-reference/authentication

## Production Blockers First

Before pushing this to GitHub or DigitalOcean:

1. Rotate every API key that has ever been committed, pasted into chat, or stored in a repo file.
2. Ensure `.env` files are not committed.
3. Keep the GitHub repo private.
4. Use a strong `SECRET_KEY`, not the hardcoded fallback in `auth_config.py`.
5. Use a strong `INTERNAL_SECRET`.
6. Fix or knowingly accept the audit blockers in `docs/audits/2026-05-08-full-project-audit.md`.
7. Decide whether this is staging or production. For first deployment, treat it as staging.

Generate secrets locally:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Run it twice:

- one value for `SECRET_KEY`
- one value for `INTERNAL_SECRET`

## Accounts You Need

Create or log into:

1. GitHub - to host this repo.
2. DigitalOcean - to run backend/frontend and Postgres.
3. Neo4j Aura - to host Neo4j.
4. LiveKit Cloud - to host realtime voice rooms.
5. OpenAI - for embeddings and content generation.
6. Anthropic - for voice-agent LLM and memory extraction.
7. Deepgram - for speech-to-text.
8. ElevenLabs - for text-to-speech.
9. Perplexity - for research/trending topics.
10. Upstash - for Redis REST rate limiter.

## Recommended Architecture

Use two App Platform apps:

```text
Browser
  -> frontend App Platform app
       source_dir: frontend
       env: BACKEND_URL, NEXT_PUBLIC_API_BASE_URL, TRENDING_API_URL

  -> backend App Platform app
       source_dir: voice-agent/backend
       run: uvicorn app.main:app
       starts child LiveKit worker automatically

Backend
  -> DigitalOcean Managed PostgreSQL with pgvector
  -> Neo4j Aura
  -> LiveKit Cloud
  -> OpenAI, Anthropic, Perplexity, Deepgram, ElevenLabs, Upstash
```

Why not one App Platform app with multiple route prefixes? The frontend has Next.js API routes under `/api`, and the backend also has some `/api/*` routes. Two separate apps avoid route conflicts and are easier for a beginner.

## Region Choice

DigitalOcean App Platform currently lists these regions for dynamic apps: NYC, AMS, SFO, SGP, LON, FRA, TOR, BLR, SYD, ATL, RIC.

For you in India:

- First choice: `BLR` if available in the UI for App Platform and Managed PostgreSQL.
- Second choice: `SGP`.
- Third choice: `FRA`.

Use the same region for backend, frontend, and Postgres when possible.

## Cost-Minimum Starting Size

For staging:

- Backend: 1 shared CPU / 1 GiB if available, or the nearest 1 GiB option.
- Frontend: smallest paid service that can run Next.js SSR.
- Postgres: smallest Managed PostgreSQL / Vector Database plan.
- Neo4j Aura: free/smallest tier for staging if it fits.
- Upstash: free/smallest REST Redis.

Do not use App Platform scale-to-zero for the backend. The LiveKit worker needs to remain connected and ready.

For production:

- Backend: 1 vCPU / 2 GiB or larger.
- Frontend: 1 GiB is usually enough to start.
- Backend instance count: start with 1 because the backend spawns a LiveKit worker child process. Scale only after testing dispatch behavior with multiple workers.
- Postgres: managed production database, not a dev database.

## Step 1: Push This Project To GitHub

DigitalOcean App Platform needs a Git provider.

1. Go to GitHub.
2. Click New repository.
3. Name it something like `ladderflow`.
4. Set it to Private.
5. Do not add a README from GitHub.
6. From your local terminal in this repo, first inspect what will be committed:

```powershell
git status
```

7. Confirm this list does not include `.env`, `node_modules`, `.next`, `graphify-out`, `output`, `.playwright-cli`, or old session transcript `.txt` files.
8. Add only the project files:

```powershell
git add .gitignore ANTIGRAVITY.md CLAUDE.md docs frontend ui_theme UI_reference voice-agent
git commit -m "Prepare LadderFlow for DigitalOcean deployment"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/ladderflow.git
git push -u origin master
```

If Git says files are too large, remove generated output folders first:

- `graphify-out`
- `output`
- `.playwright-cli`
- old session text files if not needed

Do not push `.env`.

## Step 2: Get External Service Values

You need these values before the backend deploy can work.

### LiveKit Cloud

Create a LiveKit Cloud project and copy:

- `LIVEKIT_URL`, starts with `wss://`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

### Neo4j Aura

Create a Neo4j Aura database and copy:

- `NEO4J_URI`, usually starts with `neo4j+s://`
- `NEO4J_USERNAME`, usually `neo4j`
- `NEO4J_PASSWORD`

### OpenAI

Create an API key:

- `OPENAI_API_KEY`

### Anthropic

Create an API key:

- `ANTHROPIC_API_KEY`

This backend uses `claude-sonnet-4-6` in `agent_worker.py` and `memory_extractor.py`. Confirm that your Anthropic account has access to that model, or change the model in code before deployment.

### Deepgram

Create a Deepgram API key:

- `DEEPGRAM_API_KEY`

### ElevenLabs

Create/copy:

- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`

If you do not know the voice ID yet, use the current default in code:

```text
ljX1ZrXuDIIRVcmiVSyR
```

### Perplexity

Create:

- `PERPLEXITY_API_KEY`

### Upstash

Create a Redis database and copy the REST values:

- `UPSTASH_REDIS_REST_URL`, must be HTTPS
- `UPSTASH_REDIS_REST_TOKEN`

Do not use DigitalOcean Valkey unless you change backend code. The current code imports `upstash_redis` and expects REST URL/token, not a Redis socket URL.

## Step 3: Create PostgreSQL

You have two paths.

### Path A: Fastest Staging Path - Keep Existing Neon

If your existing development database is already Neon and contains the current schema:

1. Keep `DATABASE_URL` pointing to Neon for the first DigitalOcean staging deploy.
2. Use the same connection string format:

```text
postgresql+asyncpg://USER:PASSWORD@HOST/DATABASE?ssl=require
```

3. Deploy the app.
4. Later migrate from Neon to DigitalOcean Managed PostgreSQL.

This avoids the repo's missing baseline migration problem.

### Path B: Fresh DigitalOcean Postgres / Vector Database

Use this if you want all data on DigitalOcean.

1. In DigitalOcean, click Create.
2. Click Database or Vector Database.
3. Choose PostgreSQL.
4. Choose the same region as the backend.
5. Choose the smallest production plan for staging, not App Platform dev database.
6. Create the cluster.
7. Open the database cluster.
8. Go to Users & Databases.
9. Create or note:
   - database name
   - username
   - password
10. Go to Connection Details.
11. Copy the public connection string.
12. Convert it to SQLAlchemy async format:

```text
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE?ssl=require
```

Enable pgvector after the backend app exists. You can do this from local `psql`, DigitalOcean's SQL console if available, or a one-off backend console.

Minimum SQL needed:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

Because this repo does not currently include a complete baseline migration, create tables from SQLAlchemy once:

```powershell
cd voice-agent/backend
$env:DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE?ssl=require"
@'
import asyncio
from app.db.database import engine, Base
import app.db.models

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(main())
'@ | python -
```

Then add vector columns that SQLAlchemy does not map:

```sql
ALTER TABLE memory_items ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE topic_registry ADD COLUMN IF NOT EXISTS embedding vector(1536);
```

Then run additive migrations:

```powershell
cd voice-agent/backend
$env:DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE?ssl=require"
python migrate_user_profiles_frontend_schema.py
python migrate_posts_and_draft.py
python migrate_content_outputs.py
python migrate_add_fk_indexes.py
```

If you already have data in Neon, export/import separately before running the app for real users.

## Step 4: Create Backend App On DigitalOcean

1. Open DigitalOcean Control Panel.
2. Click Create.
3. Click App Platform.
4. Choose GitHub as source.
5. Authorize DigitalOcean to access your GitHub if asked.
6. Pick your private repo.
7. Branch: `master`.
8. Source Directory: `voice-agent/backend`.
9. Autodeploy: on for staging, optional for production.
10. Click Next.

On the Resources screen, edit the detected backend component:

- Component type: Service
- Name: `ladderflow-api`
- Environment: Python
- Build command: leave blank
- Run command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- HTTP port: `8000`
- Instance count: `1`
- Size: start with at least 1 GiB RAM
- Health check path: `/health` for first deploy

Use `/health` first because it returns a response even if the LiveKit worker is degraded. After env vars are correct and worker is healthy, switch the health check to `/ready`.

Click Next.

## Step 5: Backend Environment Variables

In the backend app's Environment screen, add these. Mark all secrets as encrypted/secret.

Required:

```text
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE?ssl=require
SECRET_KEY=GENERATED_LONG_RANDOM_VALUE
INTERNAL_SECRET=GENERATED_LONG_RANDOM_VALUE
FRONTEND_URL=https://TEMP-FRONTEND-URL.ondigitalocean.app
BACKEND_INTERNAL_URL=https://TEMP-BACKEND-URL.ondigitalocean.app

OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
PERPLEXITY_API_KEY=...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

NEO4J_URI=neo4j+s://...
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...

UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
```

Optional if you use those TTS providers:

```text
CARTESIA_API_KEY=...
INWORLD_API_KEY=...
```

Temporary URL problem:

- You do not know the backend and frontend DigitalOcean URLs before creating apps.
- Use placeholders for first deploy if the UI requires values.
- After both apps exist, come back and replace:
  - backend `FRONTEND_URL`
  - backend `BACKEND_INTERNAL_URL`
  - frontend `BACKEND_URL`
  - frontend `NEXT_PUBLIC_API_BASE_URL`
  - frontend `TRENDING_API_URL`

Click Create Resources.

## Step 6: Verify Backend

After deploy:

1. Open the backend app in DigitalOcean.
2. Go to Overview.
3. Copy the live URL. It looks like:

```text
https://ladderflow-api-xxxxx.ondigitalocean.app
```

4. Open:

```text
https://BACKEND_URL/health
```

Expected healthy shape:

```json
{
  "status": "ok",
  "voice_agent": "ladderflow-host",
  "voice_worker_alive": true
}
```

If status is degraded:

1. Go to Runtime Logs.
2. Look for missing env vars or LiveKit worker errors.
3. Fix env vars.
4. Click Actions or Settings, then redeploy/restart.

Also test:

```text
https://BACKEND_URL/ready
```

Expected:

```json
{
  "status": "ready",
  "voice_worker_alive": true
}
```

## Step 7: Update Backend URLs After Backend Exists

In backend app:

1. Go to Settings.
2. Click the backend component.
3. Edit Environment Variables.
4. Set:

```text
BACKEND_INTERNAL_URL=https://BACKEND_URL
```

For now, leave `FRONTEND_URL` placeholder until frontend exists.

Save and redeploy.

## Step 8: Create Frontend App On DigitalOcean

1. Open DigitalOcean Control Panel.
2. Click Create.
3. Click App Platform.
4. Choose GitHub.
5. Pick the same repo.
6. Branch: `master`.
7. Source Directory: `frontend`.
8. Autodeploy: on for staging.
9. Click Next.

On Resources, edit the detected component:

- Component type: Service, not Static Site
- Name: `ladderflow-web`
- Environment: Node.js
- Build command:

```bash
npm run build
```

- Run command:

```bash
npm run start
```

- HTTP port: `3000`
- Instance count: `1`
- Size: smallest 1 GiB option if available

Why service, not static site: this frontend uses Next.js server-side API routes under `frontend/app/api/*`, so it needs a running Node server.

## Step 9: Frontend Environment Variables

Add:

```text
BACKEND_URL=https://YOUR-BACKEND-APP.ondigitalocean.app
NEXT_PUBLIC_API_BASE_URL=https://YOUR-BACKEND-APP.ondigitalocean.app
TRENDING_API_URL=https://YOUR-BACKEND-APP.ondigitalocean.app/api/research
NODE_ENV=production
```

Set `BACKEND_URL` and `TRENDING_API_URL` as runtime variables.

`NEXT_PUBLIC_API_BASE_URL` is used by browser code, so it is intentionally public. Do not put secrets in any `NEXT_PUBLIC_*` variable.

Click Create Resources.

## Step 10: Update Backend CORS After Frontend Exists

After the frontend deploys:

1. Copy the frontend URL:

```text
https://ladderflow-web-xxxxx.ondigitalocean.app
```

2. Go back to the backend app.
3. Settings.
4. Environment Variables.
5. Set:

```text
FRONTEND_URL=https://YOUR-FRONTEND-APP.ondigitalocean.app
```

If you also use a custom domain later, comma-separate both:

```text
FRONTEND_URL=https://YOUR-FRONTEND-APP.ondigitalocean.app,https://app.yourdomain.com
```

6. Save.
7. Redeploy backend.

## Step 11: Test The App

Open the frontend URL.

Test in this order:

1. Signup.
2. Login.
3. Onboarding/profile save.
4. Discover/trending topic.
5. Start interview.
6. Browser joins LiveKit room.
7. Backend `/agent-config` creates an interview row and token.
8. Frontend calls `/agent-dispatch`.
9. Agent joins and speaks.
10. End interview.
11. Review/generated content.
12. Digital Brain/memory extraction.

If login fails:

- Check frontend `NEXT_PUBLIC_API_BASE_URL`.
- Check backend `/auth/login`.
- Check backend CORS `FRONTEND_URL`.

If interview fails:

- Check backend `/health`.
- Check LiveKit URL/key/secret.
- Check Deepgram key.
- Check Anthropic key/model access.
- Check ElevenLabs key/voice ID.
- Check backend runtime logs.

If memory/brain fails:

- Check Postgres `vector` extension.
- Check `memory_items.embedding` and `topic_registry.embedding`.
- Check Neo4j Aura env vars.
- Check OpenAI key.
- Check Anthropic key.

## Step 12: Logs In DigitalOcean UI

For either app:

1. Open DigitalOcean.
2. Click Apps.
3. Click your app.
4. Click Activity for build/deploy logs.
5. Click Runtime Logs for live app logs.
6. Click a failed deployment to see build logs.

Backend logs are the most important. The backend starts the LiveKit worker as a child process, so worker crashes show in backend runtime logs.

## Step 13: App Console

DigitalOcean App Platform has an in-browser console for components.

Use it for safe checks:

```bash
printenv | sort
python -V
python -c "import app.main; print('backend import ok')"
```

Do not print secret values in shared screen recordings.

## Step 14: Health Checks

Start with backend health check:

```text
/health
```

After the worker is stable, use:

```text
/ready
```

`/ready` returns `503` when the LiveKit worker is not alive. That is better for production, but it can block first deployment while you are still fixing env vars.

## Step 15: Custom Domain

Recommended:

- Frontend: `app.yourdomain.com`
- Backend: `api.yourdomain.com`

DigitalOcean UI:

1. Open the frontend app.
2. Go to Settings or Networking.
3. Domains.
4. Add `app.yourdomain.com`.
5. Choose whether DigitalOcean manages DNS.
6. Follow the DNS records shown.
7. Wait for SSL certificate.
8. Open backend app.
9. Add `api.yourdomain.com`.
10. Update frontend env:

```text
BACKEND_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
TRENDING_API_URL=https://api.yourdomain.com/api/research
```

11. Update backend env:

```text
FRONTEND_URL=https://app.yourdomain.com
BACKEND_INTERNAL_URL=https://api.yourdomain.com
```

12. Redeploy both apps.

## Step 16: Database Security

For first staging deploy, public SSL database connection is acceptable if your password is strong.

For production:

1. Put backend and Postgres in the same DigitalOcean region.
2. Enable App Platform VPC if using DigitalOcean Managed PostgreSQL.
3. Prefer private database URLs where available.
4. Use trusted sources once the app is stable.

Note: App Platform cannot connect to a trusted-source database during build. This project only needs DB at runtime, so that is fine, but avoid build commands that touch the database.

## Step 17: Production Hardening Checklist

Before real users:

- Rotate all external API keys.
- Confirm `.env` is not in GitHub.
- Make GitHub repo private.
- Set strong `SECRET_KEY`.
- Set strong `INTERNAL_SECRET`.
- Confirm backend `/ready` returns 200.
- Confirm frontend signup/login works.
- Confirm CORS only allows your frontend domain.
- Enable DigitalOcean deployment failure alerts.
- Add external uptime monitoring for frontend and backend.
- Run the four backend migration scripts.
- Run `sync_onboarding_profiles_to_neo4j.py` if migrating old users.
- Test one complete voice interview.
- Check OpenAI, Anthropic, Deepgram, ElevenLabs billing limits.
- Keep backend instance count at 1 until multi-worker LiveKit behavior is tested.
- Add backups for Postgres.

## Step 18: Common Errors

### Backend deploys but `/ready` returns 503

The LiveKit worker is not alive.

Check:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `DEEPGRAM_API_KEY`
- `ANTHROPIC_API_KEY`
- `ELEVENLABS_API_KEY`
- backend runtime logs

### Frontend build fails on Node

Next.js 16 requires Node 20.9 or newer. DigitalOcean Node buildpack defaults to Node 22 as of the checked docs. If build still fails, add this to `frontend/package.json`:

```json
"engines": {
  "node": "22.x"
}
```

Then commit and push.

### Python version problems

DigitalOcean Python buildpack defaults to Python 3.13.x. If a dependency fails, add `voice-agent/backend/runtime.txt`:

```text
python-3.12.12
```

Then commit and push.

### Database vector errors

If you see errors like `type "vector" does not exist`, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE memory_items ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE topic_registry ADD COLUMN IF NOT EXISTS embedding vector(1536);
```

### CORS errors in browser

Set backend:

```text
FRONTEND_URL=https://YOUR-FRONTEND-DOMAIN
```

Redeploy backend.

### Login works locally but not in production

Check frontend:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR-BACKEND-DOMAIN
```

This variable is used by `frontend/app/login/page.tsx`, `signup/page.tsx`, and `onboarding/page.tsx`.

### Trending topics timeout

The frontend proxy has a 2 minute timeout. Check:

```text
PERPLEXITY_API_KEY
TRENDING_API_URL=https://YOUR-BACKEND-DOMAIN/api/research
```

### Worker joins LiveKit but no voice

Check:

- Deepgram balance/key
- Anthropic key/model access
- ElevenLabs key/voice ID
- LiveKit room dispatch logs
- backend runtime logs

## Step 19: Updating The App Later

Normal workflow:

```powershell
git status
git add frontend voice-agent docs
git commit -m "Describe change"
git push
```

If autodeploy is enabled, DigitalOcean redeploys automatically.

To manually redeploy:

1. Open DigitalOcean.
2. Apps.
3. Click app.
4. Deployments or Activity.
5. Click Deploy / Force rebuild and deploy.

## Step 20: What I Would Improve Before Production

These are not required for first staging deploy, but they matter:

1. Add a real migration system: Alembic.
2. Add a baseline migration for a fresh database.
3. Add Dockerfiles or an App Platform app spec for reproducible deploys.
4. Move browser direct auth calls behind Next.js API proxy to simplify CORS.
5. Add GitHub Actions for lint/build checks.
6. Add backend tests for auth, ownership, interviews, and memory endpoints.
7. Add rate limiting to auth endpoints.
8. Decide if backend and worker should be separate components instead of parent/child processes.

## Minimal Environment Variable Checklist

Backend:

```text
DATABASE_URL
SECRET_KEY
INTERNAL_SECRET
FRONTEND_URL
BACKEND_INTERNAL_URL
OPENAI_API_KEY
ANTHROPIC_API_KEY
PERPLEXITY_API_KEY
DEEPGRAM_API_KEY
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
LIVEKIT_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
```

Frontend:

```text
BACKEND_URL
NEXT_PUBLIC_API_BASE_URL
TRENDING_API_URL
NODE_ENV
```

## Final Recommended First Deployment Order

1. Rotate secrets.
2. Push private repo to GitHub.
3. Create or reuse Postgres.
4. Create Neo4j Aura.
5. Create LiveKit Cloud project.
6. Create API keys for OpenAI, Anthropic, Deepgram, ElevenLabs, Perplexity, Upstash.
7. Deploy backend App Platform app.
8. Verify `/health`.
9. Deploy frontend App Platform app.
10. Update backend `FRONTEND_URL`.
11. Update frontend backend URLs.
12. Verify signup/login.
13. Verify full voice interview.
14. Add custom domains.
15. Switch backend health check to `/ready`.
16. Only then invite users.
