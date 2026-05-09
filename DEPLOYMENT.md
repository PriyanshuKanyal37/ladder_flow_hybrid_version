# LadderFlow Deployment — DigitalOcean Droplet

Production server reference. Domain: **https://ladderflow.ai**

---

## 1. Server access

```bash
# DO Web Console (browser, no SSH key needed):
# DigitalOcean dashboard → Droplets → ladderflow-prod → Console

# SSH (if key set up): password is setuped
ssh root@168.144.66.43
```

**Droplet specs:** $12/mo · 2GB RAM · 1 vCPU · 50GB SSD · Ubuntu 24.04 · region NYC.

---

## 2. File structure on droplet

```
/srv/ladderflow/
└── app/                         # git repo (origin = GitHub master)
    ├── backend/
    │   ├── app/                 # FastAPI source code
    │   │   ├── main.py          # entry point — uvicorn loads this
    │   │   ├── api/             # REST routes
    │   │   ├── auth/            # fastapi-users + Google OAuth + reset-password
    │   │   └── services/        # neo4j, openai, deepgram, etc.
    │   ├── agent_worker.py      # LiveKit voice agent (subprocess)
    │   ├── requirements.txt
    │   ├── .env                 # backend secrets (DB, OpenAI, LiveKit, Resend, Google OAuth)
    │   └── venv/                # Python virtualenv
    │       └── bin/python       # use this Python, not system python
    └── frontend/
        ├── app/                 # Next.js 16 App Router pages
        ├── components/
        ├── lib/
        ├── package.json
        ├── .env.local           # NEXT_PUBLIC_* vars (built into bundle)
        └── .next/               # build output (created by `npm run build`)
```

Key system paths:
- `/etc/systemd/system/ladderflow-backend.service` — systemd unit for FastAPI
- `/etc/nginx/sites-available/ladderflow` — nginx reverse proxy config
- `/etc/letsencrypt/live/ladderflow.ai/` — SSL certs (auto-renew via certbot)
- `/root/.pm2/` — PM2 process manager state for frontend

---

## 3. How traffic flows

```
User browser
    ↓ HTTPS :443
nginx (ladderflow.ai)
    ├── /auth/google/*   →  127.0.0.1:8000  (FastAPI backend)
    ├── /auth/callback   →  127.0.0.1:3000  (Next.js — frontend page that consumes JWT)
    ├── /auth/*          →  127.0.0.1:8000  (FastAPI: login, register, forgot-password, etc.)
    ├── /users/*         →  127.0.0.1:8000  (FastAPI user routes)
    ├── /health          →  127.0.0.1:8000  (FastAPI health check)
    └── /                →  127.0.0.1:3000  (Next.js pages + Next API routes /api/*)
```

`certbot` issued the SSL cert and auto-renews. nginx config managed by certbot.

---

## 4. Common commands

### 4a. Deploy a code change (most common)

```bash
cd /srv/ladderflow/app
git pull

# If frontend changed:
cd frontend && npm run build && pm2 restart ladderflow-frontend

# If backend changed:
systemctl restart ladderflow-backend

# If both:
cd frontend && npm run build && pm2 restart ladderflow-frontend
systemctl restart ladderflow-backend
```

### 4b. Backend (systemd) — FastAPI + voice agent

```bash
systemctl status ladderflow-backend          # is it running?
systemctl restart ladderflow-backend         # restart
systemctl stop ladderflow-backend
systemctl start ladderflow-backend
journalctl -u ladderflow-backend -n 50 --no-pager   # last 50 log lines
journalctl -u ladderflow-backend -f                  # tail logs live
```

### 4c. Frontend (PM2) — Next.js

```bash
pm2 list                                     # show all processes
pm2 logs ladderflow-frontend --lines 50      # last 50 lines
pm2 logs ladderflow-frontend                 # tail live
pm2 restart ladderflow-frontend
pm2 stop ladderflow-frontend
pm2 start ladderflow-frontend
```

### 4d. Nginx

```bash
nginx -t                                     # test config syntax
systemctl reload nginx                       # apply config (no downtime)
systemctl restart nginx                      # full restart
tail -50 /var/log/nginx/access.log
tail -50 /var/log/nginx/error.log
nano /etc/nginx/sites-available/ladderflow   # edit config
```

### 4e. Python deps (after `requirements.txt` change)

```bash
cd /srv/ladderflow/app/backend
./venv/bin/pip install -r requirements.txt
systemctl restart ladderflow-backend
```

### 4f. Node deps (after `package.json` change)

```bash
cd /srv/ladderflow/app/frontend
npm ci
npm run build
pm2 restart ladderflow-frontend
```

### 4g. Inspect FastAPI routes

```bash
curl -s http://localhost:8000/openapi.json | python3 -c "import json,sys; [print(p) for p in json.load(sys.stdin)['paths']]"
```

### 4h. Disk / RAM / CPU

```bash
df -h                                        # disk space
free -h                                      # RAM
htop                                         # process viewer (q to quit)
```

---

## 5. Environment variables

### Backend — `/srv/ladderflow/app/backend/.env`

```
DATABASE_URL=postgresql+asyncpg://...
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
LIVEKIT_URL=wss://ladderflow-158azioj.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
NEO4J_URI=...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
JWT_SECRET=...
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
FRONTEND_URL=https://ladderflow.ai
BACKEND_PUBLIC_URL=https://ladderflow.ai
RESEND_API_KEY=re_...
FROM_EMAIL=noreply@ladderflow.ai
```

After editing: `systemctl restart ladderflow-backend`.

### Frontend — `/srv/ladderflow/app/frontend/.env.local`

```
NEXT_PUBLIC_API_BASE_URL=
NEXT_PUBLIC_LIVEKIT_URL=wss://ladderflow-158azioj.livekit.cloud
```

`NEXT_PUBLIC_API_BASE_URL` is **empty** — frontend uses relative URLs (`/auth/login` etc.), nginx routes them to backend. Avoids mixed-content errors.

After editing: must `npm run build` (env baked into bundle), then `pm2 restart ladderflow-frontend`.

---

## 6. External services

| Service | Purpose | Where configured |
|---|---|---|
| GitHub | Source repo | `github.com/PriyanshuKanyal37/ladder_flow_hybrid_version` |
| GoDaddy | DNS — A record `@` and `www` → 168.144.66.43 | godaddy.com DNS panel |
| Let's Encrypt | SSL cert (auto-renews via certbot timer) | `/etc/letsencrypt/` |
| LiveKit Cloud | WebRTC SFU for voice agent | livekit.io console |
| Google Cloud | OAuth client. Authorized redirect: `https://ladderflow.ai/auth/google/callback` | console.cloud.google.com |
| Resend | Password reset email delivery | resend.com — domain `theladder.ai` must be verified |
| Postgres | App DB (managed) | DigitalOcean Managed DB or external |
| Neo4j Aura | Knowledge graph DB | neo4j.com/cloud |

---

## 7. Common breakage / fixes

| Symptom | Cause | Fix |
|---|---|---|
| `502 Bad Gateway` | Backend crashed or not started | `systemctl restart ladderflow-backend`, check `journalctl` |
| `404 Not Found` on `/auth/google/authorize` | Backend running stale code in memory | `systemctl restart ladderflow-backend` |
| `404` on `/auth/callback?token=...` | nginx routing `/auth/callback` to backend instead of frontend | Confirm nginx has explicit `location /auth/callback { proxy_pass …:3000 }` block |
| Mixed content / blocked HTTP from HTTPS page | `NEXT_PUBLIC_API_BASE_URL` set to absolute `http://...` | Set it to empty string in `.env.local`, rebuild frontend |
| Frontend 500 on a page | Server-side render crashed | `pm2 logs ladderflow-frontend` |
| `npm ci` hangs / OOM | Droplet RAM too low | Resize droplet (≥2GB needed for Next.js builds) |
| SSL cert expired | certbot timer broken | `certbot renew --force-renewal && systemctl reload nginx` |
| Voice agent silent | LiveKit worker subprocess died | Check `/health` — `voice_worker_alive: true`? Restart backend. |

---

## 8. systemd unit (reference only — already installed)

`/etc/systemd/system/ladderflow-backend.service`:

```ini
[Unit]
Description=LadderFlow FastAPI Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=/srv/ladderflow/app/backend
EnvironmentFile=/srv/ladderflow/app/backend/.env
ExecStart=/srv/ladderflow/app/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

> `--workers 1` is **required** — the voice agent subprocess assumes a single parent. Multiple workers would spawn duplicate LiveKit workers.

---

## 9. nginx config (reference only — at `/etc/nginx/sites-available/ladderflow`)

```nginx
server {
    server_name ladderflow.ai www.ladderflow.ai;

    client_max_body_size 50M;
    proxy_read_timeout 120s;

    location /auth/callback {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /auth/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /users/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/ladderflow.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ladderflow.ai/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = www.ladderflow.ai) { return 301 https://$host$request_uri; }
    if ($host = ladderflow.ai)     { return 301 https://$host$request_uri; }
    listen 80;
    server_name ladderflow.ai www.ladderflow.ai;
    return 404;
}
```

---

## 10. Quick health check

```bash
curl https://ladderflow.ai/health
# expected: {"status":"ok","voice_agent":"ladderflow-host","voice_worker_alive":true}

curl -I https://ladderflow.ai/login
# expected: HTTP/2 200
```

If both pass: production is healthy.
