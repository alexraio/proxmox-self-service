"""Machines CRUD endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.router import get_current_user
from app.database import get_db
from app.machines.service import (
    create_machine_request,
    delete_machine,
    get_machine_or_404,
    list_machines,
)
from app.models import User
from app.schemas import MachineCreateRequest, MachineResponse

router = APIRouter()


@router.get("/", response_model=List[MachineResponse])
def list_user_machines(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[MachineResponse]:
    """Return machines for the current user (admins see all non-deleted machines).

    Args:
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        List[MachineResponse]: Non-deleted machines, newest first.
    """
    return list_machines(current_user, db)


@router.post("/", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
def request_machine(
    payload: MachineCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MachineResponse:
    """Submit a new VM/CT provisioning request.

    The job enters the database with status PENDING and will be processed
    by the background worker at its next scheduled run.

    Args:
        payload: Validated request body.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        MachineResponse: The created machine in PENDING state.
    """
    return create_machine_request(payload, current_user, db)


@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MachineResponse:
    """Get details for a single machine.

    Args:
        machine_id: Machine primary key.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        MachineResponse: Machine detail.

    Raises:
        HTTPException 404: Machine not found or inaccessible.
    """
    return get_machine_or_404(machine_id, current_user, db)


@router.delete("/{machine_id}", response_model=MachineResponse)
def delete_machine_endpoint(
    machine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MachineResponse:
    """Stop and remove a machine from Proxmox, then mark it as DELETED.

    Args:
        machine_id: Machine primary key.
        current_user: Authenticated user from JWT.
        db: Database session.

    Returns:
        MachineResponse: Updated machine with DELETED status.

    Raises:
        HTTPException 404: Machine not found or inaccessible.
        HTTPException 500: Proxmox destroy operation failed.
    """
    return delete_machine(machine_id, current_user, db)
