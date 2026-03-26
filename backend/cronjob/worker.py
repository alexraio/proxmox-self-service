"""Background worker: processes PENDING machine jobs and provisions them on Proxmox.

Run this script directly to start the scheduler:

    cd backend
    python -m cronjob.worker

The scheduler polls the database every 60 seconds (configurable via
WORKER_INTERVAL_SECONDS env var) and processes all PENDING jobs sequentially.
"""

from __future__ import annotations

import logging
import os
import sys
import time

# ---------------------------------------------------------------------------
# Ensure the backend/ directory is on sys.path so that ``app.*`` imports work
# regardless of how this script is invoked.
# ---------------------------------------------------------------------------
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: E402

from app.database import SessionLocal, create_db_and_tables  # noqa: E402
from app.models import Machine, MachineStatus  # noqa: E402
from app.proxmox.provisioner import provision_machine  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("proxmox.worker")

WORKER_INTERVAL_SECONDS: int = int(os.getenv("WORKER_INTERVAL_SECONDS", "60"))


def process_pending_jobs() -> None:
    """Query all PENDING machine jobs and attempt to provision each one.

    For every pending job:
    - Calls ``provision_machine`` which clones the Proxmox template,
      applies size overrides, sets the requested bridge, and starts the resource.
    - On success: updates status to ACTIVE and stores the VMID + node.
    - On failure: updates status to FAILED and stores the error message.

    This function is designed to be called repeatedly by the scheduler.
    It opens and closes its own database session to be safe for use outside
    the FastAPI request lifecycle.
    """
    db = SessionLocal()
    try:
        pending: list[Machine] = (
            db.query(Machine)
            .filter(Machine.status == MachineStatus.PENDING)
            .order_by(Machine.created_at.asc())
            .all()
        )

        if not pending:
            logger.debug("No pending jobs found.")
            return

        logger.info("Found %d pending job(s) to process.", len(pending))

        for machine in pending:
            logger.info(
                "Processing job #%d: %s '%s' size=%s bridge=%s storage=%s",
                machine.id,
                machine.resource_type.value,
                machine.name,
                machine.size.value,
                machine.bridge,
                machine.storage,
            )
            try:
                vmid, node = provision_machine(
                    resource_type=machine.resource_type.value,
                    size=machine.size.value,
                    bridge=machine.bridge,
                    storage=machine.storage,
                    name=machine.name,
                )
                machine.status = MachineStatus.ACTIVE
                machine.proxmox_vmid = vmid
                machine.proxmox_node = node
                machine.error_message = None
                db.commit()
                logger.info(
                    "Job #%d succeeded: vmid=%d node=%s", machine.id, vmid, node
                )

            except Exception as exc:
                logger.error(
                    "Job #%d failed: %s", machine.id, exc, exc_info=True
                )
                machine.status = MachineStatus.FAILED
                machine.error_message = str(exc)
                db.commit()

    finally:
        db.close()


def main() -> None:
    """Entry point: initialise the database and start the APScheduler loop."""
    logger.info("Proxmox Self-Service — background worker starting.")
    create_db_and_tables()

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        process_pending_jobs,
        trigger="interval",
        seconds=WORKER_INTERVAL_SECONDS,
        id="process_pending_jobs",
        next_run_time=__import__("datetime").datetime.utcnow(),  # run immediately on start
    )

    logger.info(
        "Scheduler started. Processing pending jobs every %ds.",
        WORKER_INTERVAL_SECONDS,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker stopped.")


if __name__ == "__main__":
    main()
