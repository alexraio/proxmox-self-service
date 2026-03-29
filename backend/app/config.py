"""Application configuration loaded from environment variables / .env file."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All runtime settings, populated from env vars or .env file."""

    # ── JWT / Security ────────────────────────────────────────────────────────
    secret_key: str = Field(..., description="JWT signing secret — keep it long and random")
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./proxmox_portal.db"

    # ── Proxmox ───────────────────────────────────────────────────────────────
    proxmox_host: str = Field(..., description="Proxmox VE hostname or IP address")
    proxmox_user: str = Field("root@pam", description="Proxmox user, e.g. root@pam")
    proxmox_token_name: str = Field(..., description="API Token name")
    proxmox_token_value: str = Field(..., description="API Token UUID value")
    proxmox_verify_ssl: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Worker ────────────────────────────────────────────────────────────────
    worker_interval_seconds: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


def load_portal_config() -> dict:
    """Load and return the YAML portal configuration (templates, bridges, storages).

    The config file is resolved relative to this module's location so it works
    regardless of the current working directory.

    Re-reads the file on every call so that edits to ``config/templates.yaml``
    (bridges, storages, sizes, template VMIDs, default_node) are reflected
    immediately without restarting the backend.

    Returns:
        dict: Parsed YAML with keys: ``sizes``, ``templates``, ``proxmox``.

    Raises:
        FileNotFoundError: If ``config/templates.yaml`` does not exist.
    """
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "templates.yaml"
    )
    with open(os.path.normpath(config_path), "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# settings is a singleton — env vars don't change at runtime
settings: Settings = get_settings()

