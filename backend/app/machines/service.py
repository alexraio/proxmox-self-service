"""Business logic for machine provisioning request lifecycle."""

from __future__ import annotations

import logging
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Machine, MachineStatus, User
from app.proxmox.provisioner import destroy_machine
from app.schemas import MachineCreateRequest

logger = logging.getLogger(__name__)


def create_machine_request(
    payload: MachineCreateRequest,
    current_user: User,
    db: Session,
) -> Machine:
    """Create a new provisioning job with PENDING status.

    Args:
        payload: Validated request data from the API.
        current_user: The authenticated user submitting the request.
        db: Database session.

    Returns:
        Machine: The newly created Machine ORM instance.
    """
    machine = Machine(
        user_id=current_user.id,
        name=payload.name,
        resource_type=payload.resource_type,
        size=payload.size,
        bridge=payload.bridge,
        storage=payload.storage,
        status=MachineStatus.PENDING,
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    logger.info(
        "New machine request #%d by user='%s': %s/%s name='%s'",
        machine.id,
        current_user.username,
        payload.resource_type,
        payload.size,
        payload.name,
    )
    return machine


def list_machines(current_user: User, db: Session) -> List[Machine]:
    """Return machines visible to the current user (admins see all).

    Deleted machines are always excluded from the listing.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        List[Machine]: Non-deleted machines ordered by creation date DESC.
    """
    query = db.query(Machine).filter(Machine.status != MachineStatus.DELETED)
    if not current_user.is_admin:
        query = query.filter(Machine.user_id == current_user.id)
    return query.order_by(Machine.created_at.desc()).all()


def get_machine_or_404(machine_id: int, current_user: User, db: Session) -> Machine:
    """Retrieve a machine by ID, enforcing ownership or admin access.

    Args:
        machine_id: Primary key of the machine.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        Machine: The requested ORM instance.

    Raises:
        HTTPException 404: Machine not found, deleted, or inaccessible.
    """
    machine = db.get(Machine, machine_id)
    if not machine or machine.status == MachineStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Macchina non trovata.",
        )
    if not current_user.is_admin and machine.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Macchina non trovata.",
        )
    return machine


def delete_machine(machine_id: int, current_user: User, db: Session) -> Machine:
    """Delete a machine: stop/destroy on Proxmox then mark as DELETED in DB.

    If the machine is still PENDING (not yet provisioned), it is simply
    cancelled without any Proxmox call.

    Args:
        machine_id: Primary key of the machine to delete.
        current_user: The authenticated user requesting deletion.
        db: Database session.

    Returns:
        Machine: Updated Machine with DELETED status.

    Raises:
        HTTPException 404: Machine not found or inaccessible.
        HTTPException 500: Proxmox destroy call failed.
    """
    machine = get_machine_or_404(machine_id, current_user, db)

    if machine.status == MachineStatus.PENDING:
        # Cancel pending job without calling Proxmox
        machine.status = MachineStatus.DELETED
        db.commit()
        db.refresh(machine)
        logger.info("Cancelled pending machine #%d", machine_id)
        return machine

    if machine.status == MachineStatus.ACTIVE and machine.proxmox_vmid:
        try:
            destroy_machine(
                resource_type=machine.resource_type.value,
                vmid=machine.proxmox_vmid,
                node=machine.proxmox_node,
            )
        except Exception as exc:
            logger.error(
                "Failed to destroy machine #%d (vmid=%d) on Proxmox: %s",
                machine_id,
                machine.proxmox_vmid,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Errore durante l'eliminazione su Proxmox: {exc}",
            )

    machine.status = MachineStatus.DELETED
    db.commit()
    db.refresh(machine)
    logger.info(
        "Deleted machine #%d (vmid=%s, node=%s)",
        machine_id,
        machine.proxmox_vmid,
        machine.proxmox_node,
    )
    return machine
