"""Proxmox API client factory and low-level helpers."""

from __future__ import annotations

import time
import urllib3
from functools import lru_cache

from proxmoxer import ProxmoxAPI

from app.config import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@lru_cache(maxsize=1)
def get_proxmox_client() -> ProxmoxAPI:
    """Create and cache a ProxmoxAPI client using API token authentication.

    The client is instantiated once per process and reused for all calls.
    Restart the application if credentials change.

    Returns:
        ProxmoxAPI: Authenticated proxmoxer client.
    """
    return ProxmoxAPI(
        settings.proxmox_host,
        user=settings.proxmox_user,
        token_name=settings.proxmox_token_name,
        token_value=settings.proxmox_token_value,
        verify_ssl=settings.proxmox_verify_ssl,
        timeout=60,
    )


def next_vmid(proxmox: ProxmoxAPI) -> int:
    """Return the next available VMID across the entire cluster.

    Args:
        proxmox: Authenticated ProxmoxAPI client.

    Returns:
        int: The next free VMID as reported by ``/cluster/nextid``.
    """
    return int(proxmox.cluster.nextid.get())


def wait_task(proxmox: ProxmoxAPI, node: str, upid: str, interval: int = 3) -> dict:
    """Poll a Proxmox async task (UPID) until it completes.

    Args:
        proxmox: Authenticated ProxmoxAPI client.
        node: Name of the Proxmox node running the task.
        upid: Task UPID string returned by the async Proxmox call.
        interval: Polling interval in seconds (default 3).

    Returns:
        dict: Final task status dict from Proxmox.

    Raises:
        RuntimeError: If the task finishes with a non-OK exit status.
    """
    while True:
        task_status = proxmox.nodes(node).tasks(upid).status.get()
        if task_status["status"] == "stopped":
            exit_status = task_status.get("exitstatus", "")
            if exit_status != "OK":
                raise RuntimeError(f"Task Proxmox fallito (UPID={upid}): {exit_status}")
            return task_status
        time.sleep(interval)
