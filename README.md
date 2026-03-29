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

## Production Deployment

This section describes how to deploy the application to a remote Docker server (e.g., via Portainer) using images built on your local machine.

### 1. Build and Prepare Images (Cross-Platform)

If you are building your images on a Mac (ARM/Apple Silicon) but your server is on an Intel/AMD (x86_64) machine, you **must** specify the target platform to avoid the `exec format error`.

```bash
# Sostituisci USERNAME con il tuo nome utente Docker Hub
# Build for AMD64 (Standard Intel/AMD Servers)
docker build --platform linux/amd64 -t USERNAME/proxmox-backend ./backend
docker build --platform linux/amd64 -t USERNAME/proxmox-frontend ./frontend

# Push to Docker Hub
docker push USERNAME/proxmox-backend
docker push USERNAME/proxmox-frontend
```

### 2. Portainer Deployment (Stacks)

When deploying using Portainer Stacks, follow these best practices to avoid volume and environment file errors:

#### A. Environment Variables
Instead of using an external `.env` file (which Portainer won't find on the server filesystem), use the **Environment variables** section in the Portainer UI:
1.  Copy the contents of your local `backend/.env`.
2.  In Portainer, enable **Advanced mode** under Environment variables.
3.  Paste the variables directly.
4.  Remove the `env_file: .env` line from your Compose YAML.

#### B. Configuration Files (YAML)
Docker Compose relative paths (like `./config/templates.yaml`) often fail in Portainer. Use an **absolute path** on the server:
1.  Create a directory on your server: `mkdir -p /opt/proxmox-portal/config/`.
2.  Upload your `templates.yaml` there (e.g., using SFTP or a text editor via SSH).
3.  Update the volume mount in your YAML to use that absolute path:
    ```yaml
    volumes:
      - /opt/proxmox-portal/config/templates.yaml:/app/config/templates.yaml:ro
    ```

### 3. Production Compose Example (`docker-compose.prod.yml`)

Use this optimized configuration for your remote server. Ensure you have already pushed your images as described in step 1.

```yaml
services:
  backend:
    image: USERNAME/proxmox-backend:latest
    container_name: proxmox-portal-backend
    restart: unless-stopped
    volumes:
      - db-data:/app/data
      - /opt/proxmox-portal/config/templates.yaml:/app/config/templates.yaml:ro
    ports:
      - "8000:8000"

  worker:
    image: USERNAME/proxmox-backend:latest
    container_name: proxmox-portal-worker
    restart: unless-stopped
    command: ["python", "-m", "cronjob.worker"]
    volumes:
      - db-data:/app/data
      - /opt/proxmox-portal/config/templates.yaml:/app/config/templates.yaml:ro
    depends_on:
      - backend

  frontend:
    image: USERNAME/proxmox-frontend:latest
    container_name: proxmox-portal-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  db-data:
```

