"""Pydantic v2 schemas for request validation and API response serialization."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import MachineStatus, ResourceSize, ResourceType


# ── Auth schemas ──────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """Payload to register a new user account."""

    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLoginRequest(BaseModel):
    """Payload to authenticate with username and password."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Public user record — never includes the password hash."""

    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token returned on successful login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Machine schemas ───────────────────────────────────────────────────────────

class MachineCreateRequest(BaseModel):
    """Payload to submit a new provisioning request."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-zA-Z0-9\-]+$",
        description="Alphanumeric hostname (hyphens allowed)",
    )
    resource_type: ResourceType
    size: ResourceSize
    bridge: str = Field(..., min_length=2, max_length=50)
    storage: str = Field(..., min_length=2, max_length=100)


class MachineResponse(BaseModel):
    """Full machine representation for API responses."""

    id: int
    name: str
    resource_type: ResourceType
    size: ResourceSize
    bridge: str
    storage: str
    status: MachineStatus
    proxmox_vmid: Optional[int] = None
    proxmox_node: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    owner: UserResponse

    model_config = {"from_attributes": True}
