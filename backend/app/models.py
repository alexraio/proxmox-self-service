"""SQLAlchemy ORM models: User and Machine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ── Enum definitions ─────────────────────────────────────────────────────────

class ResourceType(str, PyEnum):
    """Type of Proxmox resource to provision."""

    VM = "vm"
    CT = "ct"


class ResourceSize(str, PyEnum):
    """Predefined hardware size tier."""

    TINY = "tiny"
    MEDIUM = "medium"
    HIGH = "high"


class MachineStatus(str, PyEnum):
    """Lifecycle status for a provisioning job."""

    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    DELETED = "deleted"


def _utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


# ── ORM Models ────────────────────────────────────────────────────────────────

class User(Base):
    """Portal user account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    machines = relationship("Machine", back_populates="owner", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


class Machine(Base):
    """A VM or Container provisioning job tracked by the portal."""

    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # User-supplied configuration
    name = Column(String(100), nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False)
    size = Column(Enum(ResourceSize), nullable=False)
    bridge = Column(String(50), nullable=False)
    storage = Column(String(100), nullable=False)

    # Lifecycle
    status = Column(
        Enum(MachineStatus),
        default=MachineStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Populated after successful provisioning
    proxmox_vmid = Column(Integer, nullable=True)
    proxmox_node = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    owner = relationship("User", back_populates="machines")

    def __repr__(self) -> str:
        return (
            f"<Machine id={self.id} name={self.name!r} "
            f"status={self.status} vmid={self.proxmox_vmid}>"
        )
