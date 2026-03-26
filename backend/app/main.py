"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.config import load_portal_config, settings
from app.database import create_db_and_tables
from app.machines.router import router as machines_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler: create DB tables on startup."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="Proxmox Self-Service Portal",
    version="1.1.0",
    description=(
        "Self-service portal for provisioning VMs and Containers on Proxmox VE. "
        "Jobs are queued in a local database and processed asynchronously by a background worker."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(machines_router, prefix="/machines", tags=["Machines"])


# ── System endpoints ──────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Return API health status and version."""
    return {"status": "ok", "version": "1.1.0"}


@app.get("/config/options", tags=["System"])
def get_config_options() -> dict:
    """Return the configurable UI options sourced from templates.yaml.

    Used by the frontend to populate the dropdowns for bridge, storage, and size.

    Returns:
        dict: Keys ``bridges``, ``storages``, and ``sizes`` for the new request form.
    """
    cfg = load_portal_config()
    proxmox_cfg = cfg.get("proxmox", {})
    sizes_cfg = cfg.get("sizes", {})
    return {
        "bridges": proxmox_cfg.get("bridges", []),
        "storages": proxmox_cfg.get("storages", []),
        "sizes": [
            {
                "id": k,
                "label": k.capitalize(),
                "vcpu": v["vcpu"],
                "memory_mb": v["memory_mb"],
                "disk_gb": v["disk_gb"],
            }
            for k, v in sizes_cfg.items()
        ],
    }
