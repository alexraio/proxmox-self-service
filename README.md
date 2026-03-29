# Proxmox Self-Service Portal

Self-service web portal for provisioning VMs and LXC Containers on Proxmox VE.

## Architecture

```
┌─────────────────┐     HTTP      ┌──────────────────┐
│  React Frontend │ ────────────► │  FastAPI Backend  │
│  (Bootstrap 5)  │               │  + SQLite DB      │
└─────────────────┘               └────────┬─────────┘
                                           │
                                   ┌───────▼──────────┐
                                   │  Background Worker│
                                   │  (APScheduler)    │
                                   └───────┬──────────┘
                                           │ proxmoxer
                                   ┌───────▼──────────┐
                                   │   Proxmox VE API  │
                                   └──────────────────┘
```

## Quick Start

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your Proxmox credentials
```

### 2. Configure templates

Edit `backend/config/templates.yaml`:
- Replace template VMIDs (100–202) with your actual Proxmox template VMIDs
- Add/remove storage and bridge entries as needed

### 3. Run with Docker Compose

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Run locally for development

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in your credentials
uvicorn app.main:app --reload
```

**Worker (separate terminal):**
```bash
cd backend
source .venv/bin/activate
python -m cronjob.worker
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev               # http://localhost:5173
```

### 5. Troubleshooting: Restarting local services

If you need to kill stuck processes to cleanly restart the application locally, you can forcefully free the used ports:

```bash
# Kill the FastAPI Backend (port 8000)
lsof -ti :8000 | xargs kill -9

# Kill the React Frontend (port 5173)
lsof -ti :5173 | xargs kill -9
```

## Configuration (`backend/config/templates.yaml`)

| Section | Description |
|---|---|
| `sizes` | vCPU, RAM, disk for Tiny/Medium/High tiers |
| `templates.vm` | Template VMID to clone for VM sizes |
| `templates.ct` | Template VMID to clone for CT sizes |
| `proxmox.default_node` | Target Proxmox node name |
| `proxmox.storages` | List of storage options shown in the form |
| `proxmox.bridges` | List of network bridges shown in the form |

## Environment Variables (`backend/.env`)

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key (long random string) |
| `DATABASE_URL` | SQLite or PostgreSQL URL |
| `PROXMOX_HOST` | Proxmox VE hostname / IP |
| `PROXMOX_USER` | Proxmox user (e.g. `root@pam`) |
| `PROXMOX_TOKEN_NAME` | API Token name |
| `PROXMOX_TOKEN_VALUE` | API Token UUID |
| `PROXMOX_VERIFY_SSL` | Set `false` for self-signed certificates |
| `WORKER_INTERVAL_SECONDS` | Polling interval for the worker (default: 60) |

## Proxmox Permissions Required

The API token user needs at least:
- `VM.Clone` on the template VMs/CTs
- `VM.Config.Network` to set the bridge
- `VM.PowerMgmt` to start resources
- `Datastore.AllocateSpace` on the target storage

## Features

- 🔐 JWT Authentication (register / login)
- 🖥️ VM & LXC Container provisioning via template cloning
- 📏 Three size tiers: Tiny, Medium, High
- 🌐 Per-request network bridge selection
- 💾 Per-request storage selection
- ⏱️ Async job queue: UI stays responsive while Proxmox provisions
- 📊 Dashboard with auto-refresh (30s) and status badges
- 🗑️ Delete with confirmation (stops + destroys on Proxmox)
- 👑 Admin view: see all users' machines
