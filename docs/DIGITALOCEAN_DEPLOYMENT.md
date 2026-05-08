# LadderFlow — DigitalOcean Deployment Guide

> **Updated:** May 2026 | **Time:** ~2 hrs first deploy, ~10 min after

---

## Stack Overview

| Process | Port | Runtime |
|---------|------|---------|
| Next.js frontend | 3000 | Node 20 |
| FastAPI backend | 8000 | Python 3.12 |
| LiveKit voice agent | outbound only | Python 3.12 (subprocess of backend) |

**External services:** Neon (DB) · Neo4j (graph) · LiveKit Cloud (voice) · Upstash Redis (rate limit) · OpenAI · Anthropic · Perplexity · ElevenLabs · Deepgram · Cartesia · Inworld

---

## Pricing Breakdown

### DigitalOcean Server

| Plan | vCPU | RAM | Cost | Use |
|------|------|-----|------|-----|
| Basic 2 vCPU / 4 GiB | 2 | 4 GiB | **$24/mo** | Dev / low traffic |
| **Basic 4 vCPU / 8 GiB** | **4** | **8 GiB** | **$48/mo** | **Production (recommended)** |
| + Backups | — | — | +$4.80/mo | Optional but worth it |

> **Why 4 vCPU?** Voice agent spawns a child process per room. Under load, 2 vCPU saturates fast.

### Databases & Infrastructure

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Neon** (PostgreSQL) | 10 GiB storage, 5 projects | Launch $19/mo · Scale $69/mo |
| **Neo4j AuraDB** (graph) | 200K nodes / 400K rels | Professional ~$65/mo |
| **Upstash Redis** (rate limit) | 10K cmds/day | Pay-as-you-go $0.20/100K cmds · Starter $10/mo |
| **LiveKit Cloud** (voice infra) | 100K audio-minutes/mo | Startup $100/mo (500K min) · $0.006/min after |

### AI & Voice APIs

| Service | Free Tier | Paid Tiers |
|---------|-----------|------------|
| **OpenAI** | $5 credit | GPT-4o: $2.50/1M in · $10/1M out |
| **Anthropic** | $5 credit | Sonnet 4.6: $3/1M in · $15/1M out |
| **Perplexity** | — | ~$0.005/req (Sonar) · API sub $20/mo |
| **ElevenLabs** (TTS) | 10K chars/mo | Creator $22/mo (100K) · Pro $99/mo (500K) |
| **Deepgram** (STT) | $200 credit | Nova-2: $0.0059/min · Aura-2 TTS: $0.0095/min |
| **Cartesia** (TTS) | Free tier | Sonic: $0.05/1K chars |
| **Inworld** (TTS) | Free tier | Usage-based |

### Cost Per Interview Session (30 min estimate)

| Service | Usage | ~Cost |
|---------|-------|-------|
| Deepgram STT | 30 min × $0.0059 | $0.18 |
| ElevenLabs TTS | ~5K chars of AI speech | $0.11 (Pro plan) |
| OpenAI (content gen) | ~50K tokens | $0.15 |
| LiveKit audio | 30 min × $0.006 | $0.18 |
| **Total per session** | | **~$0.60 – $1.00** |

### Monthly Total (Production)

| Scenario | Cost |
|----------|------|
| Just starting (free tiers + DO Droplet) | **~$53/mo** |
| 100 interviews/mo | **~$150–200/mo** |
| 500 interviews/mo | **~$500–700/mo** |

---

## Pre-Flight Checklist

Gather these before touching DigitalOcean:

```
API Keys needed:
□ OPENAI_API_KEY          → platform.openai.com → API Keys
□ ANTHROPIC_API_KEY       → console.anthropic.com → API Keys
□ PERPLEXITY_API_KEY      → perplexity.ai → Settings → API
□ DEEPGRAM_API_KEY        → console.deepgram.com → API Keys
□ ELEVENLABS_API_KEY      → elevenlabs.io → Profile → API Key
□ ELEVENLABS_VOICE_ID     → elevenlabs.io → Voices → copy ID
□ CARTESIA_API_KEY        → cartesia.ai → Dashboard → API Keys
□ INWORLD_API_KEY         → inworld.ai → API Keys

Database:
□ DATABASE_URL            → Neon → Connection Details → Connection string
                            format: postgresql+asyncpg://user:pass@ep-xxx.neon.tech/db?ssl=require

Neo4j:
□ NEO4J_URI               → AuraDB → Connection URI (starts with neo4j+s://)
□ NEO4J_USERNAME          → usually: neo4j
□ NEO4J_PASSWORD          → from AuraDB credentials

LiveKit:
□ LIVEKIT_URL             → LiveKit Cloud → Settings (starts with wss://)
□ LIVEKIT_API_KEY         → LiveKit Cloud → API Keys
□ LIVEKIT_API_SECRET      → same place

Upstash:
□ UPSTASH_REDIS_REST_URL   → Upstash → Database → REST URL
□ UPSTASH_REDIS_REST_TOKEN → same place

Generate these yourself — run in terminal:
□ SECRET_KEY              → python -c "import secrets; print(secrets.token_hex(32))"
□ INTERNAL_SECRET         → run same command again (different value each time)

Domain (optional but recommended):
□ yourdomain.com          → Namecheap / GoDaddy / Squarespace (~$10/yr)
```

---

## Phase 1 — Push Code to GitHub

```bash
# In your project root
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ladderflow.git
git push -u origin main
```

Make sure `.gitignore` contains:
```
.env
*.env
.env.*
.next/
__pycache__/
node_modules/
venv/
*.log
```

---

## Phase 2 — Create DigitalOcean Account

1. Go to **digitalocean.com** → Sign Up
2. Add payment method (credit card or PayPal)
3. New accounts get **$200 free credit for 60 days**

---

## Phase 3 — Create a Droplet

1. Dashboard → **Create** → **Droplets**
2. **Region:** choose closest to your users (NYC3 for US East, BLR1 for India, SGP1 for SE Asia)
3. **Image:** Ubuntu **24.04 (LTS) x64**
4. **Plan:** Basic → Regular SSD → **$48/mo (4 vCPU / 8 GiB)**
5. **Auth:** Password (set a strong one) or SSH Key (see note below)
6. **Hostname:** `ladderflow-prod`
7. **Backups:** check the box (+$4.80/mo) — worth it
8. Click **Create Droplet**

Write down the IP address shown after creation.

> **SSH Key (recommended):** In PowerShell: `ssh-keygen -t ed25519`. Then `cat $env:USERPROFILE\.ssh\id_ed25519.pub` → paste in DO's "Add SSH Key" dialog.

---

## Phase 4 — Connect to Server

```powershell
ssh root@YOUR_IP_ADDRESS
# First connection: type "yes" when asked about fingerprint
```

Create a deploy user:
```bash
adduser deploy
usermod -aG sudo deploy

# If using SSH keys:
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

Switch to deploy user:
```bash
su - deploy
```

---

## Phase 5 — Install Software

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
  git curl wget build-essential \
  nginx certbot python3-certbot-nginx \
  python3 python3-pip python3-venv \
  ffmpeg

# Install Node 20
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 20 && nvm use 20 && nvm alias default 20

# Install PM2
npm install -g pm2
```

---

## Phase 6 — Deploy Backend

```bash
# Create directories
sudo mkdir -p /srv/ladderflow && sudo chown deploy:deploy /srv/ladderflow

# Clone repo
cd /srv/ladderflow
git clone https://github.com/YOUR_USERNAME/ladderflow.git app

# Create Python venv
cd /srv/ladderflow/app/voice-agent/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create the env file:
```bash
nano /srv/ladderflow/app/voice-agent/backend/.env
```

```env
# ── AI Providers ──────────────────────────────────────────────────────────────
# OpenAI → platform.openai.com → API Keys
OPENAI_API_KEY=sk-proj-...

# Anthropic → console.anthropic.com → API Keys
ANTHROPIC_API_KEY=sk-ant-...

# Perplexity → perplexity.ai → Settings → API
PERPLEXITY_API_KEY=pplx-...

# ── STT / TTS ─────────────────────────────────────────────────────────────────
# Deepgram → console.deepgram.com → API Keys
DEEPGRAM_API_KEY=...
VITE_DEEPGRAM_API_KEY=...        # same value as DEEPGRAM_API_KEY

# ElevenLabs → elevenlabs.io → Profile → API Key
ELEVENLABS_API_KEY=...
# ElevenLabs → Voices → click voice → copy ID from URL
ELEVENLABS_VOICE_ID=...

# Cartesia → cartesia.ai → Dashboard → API Keys
CARTESIA_API_KEY=...

# Inworld → inworld.ai → API Keys
INWORLD_API_KEY=...

# ── Database ──────────────────────────────────────────────────────────────────
# Neon → Dashboard → your project → Connection Details
# Click "Connection string" → select "asyncpg" driver
# Format MUST be: postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/dbname?ssl=require
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?ssl=require

# ── Neo4j (Digital Brain) ─────────────────────────────────────────────────────
# AuraDB → console.neo4j.io → your instance → Connection URI
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...

# ── LiveKit Cloud ─────────────────────────────────────────────────────────────
# LiveKit Cloud → cloud.livekit.io → your project → Settings
LIVEKIT_URL=wss://your-project-name.livekit.cloud
# LiveKit Cloud → API Keys → Create Key
LIVEKIT_API_KEY=APIxxxxxxxxxx
LIVEKIT_API_SECRET=...

# ── Upstash Redis ─────────────────────────────────────────────────────────────
# Upstash → console.upstash.com → your database → REST API tab
UPSTASH_REDIS_REST_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=...

# ── App Secrets (generate fresh for production) ───────────────────────────────
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
# Use a DIFFERENT value for each key — never reuse
SECRET_KEY=<64-char-hex>
INTERNAL_SECRET=<64-char-hex>

# ── URLs ──────────────────────────────────────────────────────────────────────
# Set to your actual domain once DNS is pointed
FRONTEND_URL=https://yourdomain.com
# Leave as-is — backend talks to itself on the same server
BACKEND_INTERNAL_URL=http://127.0.0.1:8000
```

**Generate `SECRET_KEY` and `INTERNAL_SECRET` on the server:**
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('INTERNAL_SECRET=' + secrets.token_hex(32))"
```
Copy each output line directly into the `.env` file.

```bash
chmod 600 /srv/ladderflow/app/voice-agent/backend/.env
```

Create systemd service:
```bash
sudo nano /etc/systemd/system/ladderflow-backend.service
```

```ini
[Unit]
Description=LadderFlow FastAPI Backend
After=network.target

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/srv/ladderflow/app/voice-agent/backend
Environment="PATH=/srv/ladderflow/app/voice-agent/backend/venv/bin"
EnvironmentFile=/srv/ladderflow/app/voice-agent/backend/.env
ExecStart=/srv/ladderflow/app/voice-agent/backend/venv/bin/uvicorn \
    app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --no-access-log
Restart=always
RestartSec=5
KillSignal=SIGTERM
TimeoutStopSec=60
StandardOutput=append:/var/log/ladderflow-backend.log
StandardError=append:/var/log/ladderflow-backend.log

[Install]
WantedBy=multi-user.target
```

> **`--workers 1` is critical.** Backend spawns the voice agent as a child process on startup. Multiple workers = multiple voice agents fighting over the same rooms.

```bash
sudo touch /var/log/ladderflow-backend.log
sudo chown deploy:deploy /var/log/ladderflow-backend.log
sudo systemctl daemon-reload
sudo systemctl enable ladderflow-backend
sudo systemctl start ladderflow-backend

# Verify
curl http://localhost:8000/health
# Expected: {"status":"ok","voice_agent":"ladderflow-host","voice_worker_alive":true}
```

---

## Phase 7 — Deploy Frontend

```bash
cd /srv/ladderflow/app

# Create env
nano frontend/.env.local
```

```env
BACKEND_URL=http://localhost:8000
```

```bash
# Run from project root — installs workspace root + frontend deps together
npm ci
cd frontend
npm run build
pm2 start npm --name "ladderflow-frontend" -- start
pm2 startup    # copy the command it prints and run it
pm2 save

# Verify
curl http://localhost:3000   # should return HTML
```

---

## Phase 8 — Nginx Config

```bash
sudo rm /etc/nginx/sites-enabled/default
sudo nano /etc/nginx/sites-available/ladderflow
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 50M;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        location /_next/static/ {
            proxy_pass http://127.0.0.1:3000;
            add_header Cache-Control "public, max-age=31536000, immutable";
        }
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ladderflow /etc/nginx/sites-enabled/
sudo nginx -t      # must say "syntax is ok"
sudo systemctl restart nginx
sudo systemctl enable nginx

# Firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable     # type y when prompted
```

---

## Phase 9 — Domain + HTTPS

**At your domain registrar, create two DNS A records:**

| Type | Host | Value |
|------|------|-------|
| A | `@` | `YOUR_SERVER_IP` |
| A | `www` | `YOUR_SERVER_IP` |

Wait for DNS to propagate (5 min – 2 hrs). Test: `nslookup yourdomain.com` → shows your IP.

Then:
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
# Answer prompts: email → A (agree) → 2 (redirect HTTP→HTTPS)
```

Update backend `.env`:
```bash
nano /srv/ladderflow/app/voice-agent/backend/.env
# Set: FRONTEND_URL=https://yourdomain.com
sudo systemctl restart ladderflow-backend
```

---

## Phase 10 — CI/CD (Auto-Deploy from GitHub)

Create `/srv/ladderflow/deploy.sh`:
```bash
nano /srv/ladderflow/deploy.sh
```

```bash
#!/bin/bash
set -e
cd /srv/ladderflow/app
git pull origin main

# Backend
cd voice-agent/backend
source venv/bin/activate
pip install -q -r requirements.txt
sudo systemctl restart ladderflow-backend
sleep 3
systemctl is-active --quiet ladderflow-backend || { echo "Backend failed"; exit 1; }

# Frontend — npm ci must run from project root (workspace setup)
cd /srv/ladderflow/app
npm ci
cd frontend
npm run build
pm2 restart ladderflow-frontend && pm2 save

echo "Deploy complete"
```

```bash
chmod +x /srv/ladderflow/deploy.sh

# Allow passwordless restart
sudo visudo
```

Add at bottom of visudo:
```
deploy ALL=(ALL) NOPASSWD: /bin/systemctl restart ladderflow-backend, /bin/systemctl status ladderflow-backend
```

In your local repo, create `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_IP }}
          username: deploy
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: /srv/ladderflow/deploy.sh
```

**Add GitHub Secrets** (repo → Settings → Secrets → Actions → New secret):
- `SERVER_IP` → your Droplet IP
- `SERVER_SSH_KEY` → contents of `cat $env:USERPROFILE\.ssh\id_ed25519` (the private key, not `.pub`)

Push the workflow file — every push to `main` now auto-deploys.

---

## Monitoring & Logs

```bash
# All service statuses
sudo systemctl status ladderflow-backend
pm2 status
sudo systemctl status nginx

# Live logs
tail -f /var/log/ladderflow-backend.log     # backend + voice agent
pm2 logs ladderflow-frontend                # frontend
sudo tail -f /var/log/nginx/error.log       # nginx

# Server resources
htop                # CPU/memory — press q to quit
df -h               # disk space

# Restart all
sudo systemctl restart ladderflow-backend && pm2 restart ladderflow-frontend

# Check health
curl https://yourdomain.com/health
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `502 Bad Gateway` | Backend or frontend down | `sudo systemctl restart ladderflow-backend` or `pm2 restart ladderflow-frontend` |
| `voice_worker_alive: false` | LiveKit agent crashed | Check `LIVEKIT_URL/KEY/SECRET` in `.env`, restart backend |
| Module not found (Python) | venv not set up | `source venv/bin/activate && pip install -r requirements.txt` |
| `npm run build` fails | TypeScript errors or missing env | Run locally first, fix errors, then push |
| SSL cert expired | Certbot not running | `sudo certbot renew --dry-run` |
| GitHub Actions SSH fails | Wrong key in secret | Paste private key (`id_ed25519` not `id_ed25519.pub`) |

---

## Cost Summary

| Scenario | Monthly Cost |
|----------|-------------|
| **Minimum** (free tiers, dev use) | ~$53/mo |
| **Production** (paid Neon + Neo4j + ~100 sessions) | ~$200/mo |
| **Growth** (~500 sessions/mo) | ~$500–700/mo |

| Fixed Costs | |
|-------------|--|
| DO Droplet 4 vCPU / 8 GiB | $48/mo |
| Neon Launch (when free tier fills) | $19/mo |
| Neo4j AuraDB Professional | $65/mo |

| Variable Costs (per 30-min interview) | |
|---------------------------------------|--|
| Deepgram STT | ~$0.18 |
| ElevenLabs TTS | ~$0.11 |
| OpenAI content gen | ~$0.15 |
| LiveKit audio | ~$0.18 |
| **Total** | **~$0.60–$1.00** |
