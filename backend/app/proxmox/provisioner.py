"""Proxmox provisioning logic: clone template, configure network, start machine."""

from __future__ import annotations

import logging
from typing import Tuple

from proxmoxer import ProxmoxAPI

from app.config import load_portal_config
from app.proxmox.client import get_proxmox_client, next_vmid, wait_task

logger = logging.getLogger(__name__)


# ── Internal helpers ─────────────────────────────────────────────────────────

def _get_template_vmid(resource_type: str, size: str) -> int:
    """Retrieve the template VMID from YAML config.

    Args:
        resource_type: ``'vm'`` or ``'ct'``.
        size: ``'tiny'``, ``'medium'``, or ``'high'``.

    Returns:
        int: Template VMID to clone from.

    Raises:
        KeyError: If resource_type or size is not defined in config.
    """
    return int(load_portal_config()["templates"][resource_type][size])


def _get_size_config(size: str) -> dict:
    """Return hardware spec dict for a size tier.

    Args:
        size: Size key (``'tiny'``, ``'medium'``, ``'high'``).

    Returns:
        dict: Keys: ``vcpu`` (int), ``memory_mb`` (int), ``disk_gb`` (int).
    """
    return load_portal_config()["sizes"][size]


def _parse_bridge_vlan(bridge_input: str) -> tuple[str, str | None]:
    """Split a bridge string like ``'vmbr0.50'`` into ``('vmbr0', '50')``.

    If there is no VLAN suffix the second element is ``None``.

    Args:
        bridge_input: Bridge identifier from the portal config, e.g. ``'vmbr0'``
            or ``'vmbr0.50'``.

    Returns:
        tuple[str, str | None]: ``(bridge_name, vlan_tag_or_None)``.
    """
    if "." in bridge_input:
        bridge, tag = bridge_input.split(".", 1)
        return bridge, tag
    return bridge_input, None


def _update_bridge_in_config_string(raw: str, bridge_input: str) -> str:
    """Replace bridge (and optional VLAN tag) in a Proxmox net config string.

    Proxmox stores network config as a comma-separated string, e.g.
    ``virtio,bridge=vmbr0,firewall=1``.  This function replaces the
    ``bridge=`` and ``tag=`` segments in place without touching other
    parameters.

    Args:
        raw: Existing net config string from Proxmox.
        bridge_input: Bridge identifier, optionally with VLAN suffix
            (e.g. ``'vmbr0'`` or ``'vmbr0.50'``).

    Returns:
        str: Updated net config string with the correct bridge and tag.
    """
    bridge, tag = _parse_bridge_vlan(bridge_input)
    parts = raw.split(",")
    new_parts = []
    bridge_set = False
    tag_removed = False
    for part in parts:
        if part.startswith("bridge="):
            new_parts.append(f"bridge={bridge}")
            bridge_set = True
        elif part.startswith("tag="):
            # Will re-add below if needed; skip old value
            tag_removed = True
        else:
            new_parts.append(part)
    if not bridge_set:
        new_parts.append(f"bridge={bridge}")
    if tag:
        new_parts.append(f"tag={tag}")
    return ",".join(new_parts)


# ── Clone operations ──────────────────────────────────────────────────────────

def _clone_vm(
    proxmox: ProxmoxAPI,
    node: str,
    template_vmid: int,
    new_vmid: int,
    name: str,
    storage: str,
) -> None:
    """Perform a full clone of a QEMU VM template.

    Args:
        proxmox: Authenticated ProxmoxAPI client.
        node: Target Proxmox node.
        template_vmid: Source template VMID.
        new_vmid: VMID for the new VM.
        name: Name for the new VM.
        storage: Proxmox storage ID for the clone disks.
    """
    logger.info(
        "Cloning VM template %d → vmid=%d on node=%s (storage=%s)",
        template_vmid, new_vmid, node, storage,
    )
    upid = proxmox.nodes(node).qemu(template_vmid).clone.post(
        newid=new_vmid, name=name, full=1, storage=storage
    )
    wait_task(proxmox, node, upid)
    logger.info("VM clone complete: vmid=%d", new_vmid)


def _clone_ct(
    proxmox: ProxmoxAPI,
    node: str,
    template_vmid: int,
    new_vmid: int,
    name: str,
    storage: str,
) -> None:
    """Perform a full clone of an LXC container template.

    Args:
        proxmox: Authenticated ProxmoxAPI client.
        node: Target Proxmox node.
        template_vmid: Source template VMID.
        new_vmid: VMID for the new container.
        name: Hostname for the new container.
        storage: Proxmox storage ID for the clone rootfs.
    """
    logger.info(
        "Cloning CT template %d → vmid=%d on node=%s (storage=%s)",
        template_vmid, new_vmid, node, storage,
    )
    upid = proxmox.nodes(node).lxc(template_vmid).clone.post(
        newid=new_vmid, hostname=name, full=1, storage=storage
    )
    wait_task(proxmox, node, upid)
    logger.info("CT clone complete: vmid=%d", new_vmid)


# ── Post-clone configuration ──────────────────────────────────────────────────

def _configure_vm_network(
    proxmox: ProxmoxAPI, node: str, vmid: int, bridge: str
) -> None:
    """Set the net0 bridge on a QEMU VM.

    Args:
        proxmox: Authenticated ProxmoxAPI client.
        node: Proxmox node name.
        vmid: Target VM VMID.
        bridge: Bridge name to apply (e.g. ``'vmbr0.50'``).
    """
    config = proxmox.nodes(node).qemu(vmid).config.get()
    raw = config.get("net0", "virtio,bridge=vmbr0")
    new_net0 = _update_bridge_in_config_string(raw, bridge)
    logger.info("VM %d — setting net0 bridge to %s", vmid, bridge)
    proxmox.nodes(node).qemu(vmid).config.put(net0=new_net0)


def _configure_ct_network(
    proxmox: ProxmoxAPI, node: str, vmid: int, bridge: str
) -> None:
    """Set the net0 bridge on an LXC container.

    Args:
        proxmox: Authenticated ProxmoxAPI client.
        node: Proxmox node name.
        vmid: Target container VMID.
        bridge: Bridge name to apply (e.g. ``'vmbr0.50'``).
    """
    config = proxmox.nodes(node).lxc(vmid).config.get()
    raw = config.get("net0", "name=eth0,bridge=vmbr0,ip=dhcp")
    new_net0 = _update_bridge_in_config_string(raw, bridge)
    logger.info("CT %d — setting net0 bridge to %s", vmid, bridge)
    proxmox.nodes(node).lxc(vmid).config.put(net0=new_net0)


def _apply_size_vm(
    proxmox: ProxmoxAPI, node: str, vmid: int, size_cfg: dict
) -> None:
    """Apply CPU and RAM configuration to a QEMU VM.

    Args:
        proxmox: Authenticated ProxmoxAPI client.
        node: Proxmox node name.
        vmid: Target VM VMID.
        size_cfg: Size dict with ``vcpu`` and ``memory_mb`` keys.
    """
    proxmox.nodes(node).qemu(vmid).config.put(
        cores=size_cfg["vcpu"], memory=size_cfg["memory_mb"]
    )


def _apply_size_ct(
    proxmox: ProxmoxAPI, node: str, vmid: int, size_cfg: dict
) -> None:
    """Apply CPU and RAM configuration to an LXC container.

    Args:
        proxmox: Authenticated ProxmoxAPI client.
        node: Proxmox node name.
        vmid: Target container VMID.
        size_cfg: Size dict with ``vcpu`` and ``memory_mb`` keys.
    """
    proxmox.nodes(node).lxc(vmid).config.put(
        cores=size_cfg["vcpu"], memory=size_cfg["memory_mb"]
    )


# ── Public API ────────────────────────────────────────────────────────────────

def provision_machine(
    resource_type: str,
    size: str,
    bridge: str,
    storage: str,
    name: str,
    node: str | None = None,
) -> Tuple[int, str]:
    """Full provisioning pipeline: clone → configure → start.

    Steps:
        1. Resolve template VMID and size spec from YAML config.
        2. Acquire the next free VMID from the cluster.
        3. Clone the template (full clone) to the new VMID.
        4. Apply size overrides (CPU / RAM).
        5. Reconfigure net0 to the requested bridge.
        6. Start the VM/CT.

    Args:
        resource_type: ``'vm'`` or ``'ct'``.
        size: ``'tiny'``, ``'medium'``, or ``'high'``.
        bridge: Target network bridge (e.g. ``'vmbr0.50'``).
        storage: Target Proxmox storage (e.g. ``'local-lvm'``).
        name: Hostname / VM name for the new resource.
        node: Proxmox node name; falls back to ``default_node`` from config.

    Returns:
        Tuple[int, str]: ``(new_vmid, node_name)`` on success.

    Raises:
        RuntimeError: If any Proxmox task fails.
        KeyError: If resource_type/size/template is not found in config.
        ValueError: If resource_type is not ``'vm'`` or ``'ct'``.
    """
    proxmox = get_proxmox_client()
    target_node = node or load_portal_config()["proxmox"]["default_node"]
    template_vmid = _get_template_vmid(resource_type, size)
    size_cfg = _get_size_config(size)
    new_vmid = next_vmid(proxmox)

    logger.info(
        "Provisioning %s '%s' size=%s bridge=%s storage=%s node=%s vmid=%d",
        resource_type, name, size, bridge, storage, target_node, new_vmid,
    )

    if resource_type == "vm":
        _clone_vm(proxmox, target_node, template_vmid, new_vmid, name, storage)
        _apply_size_vm(proxmox, target_node, new_vmid, size_cfg)
        _configure_vm_network(proxmox, target_node, new_vmid, bridge)
        upid = proxmox.nodes(target_node).qemu(new_vmid).status.start.post()
        wait_task(proxmox, target_node, upid)

    elif resource_type == "ct":
        _clone_ct(proxmox, target_node, template_vmid, new_vmid, name, storage)
        _apply_size_ct(proxmox, target_node, new_vmid, size_cfg)
        _configure_ct_network(proxmox, target_node, new_vmid, bridge)
        upid = proxmox.nodes(target_node).lxc(new_vmid).status.start.post()
        wait_task(proxmox, target_node, upid)

    else:
        raise ValueError(f"Tipo risorsa non supportato: {resource_type!r}")

    logger.info("Provisioning completato: vmid=%d node=%s", new_vmid, target_node)
    return new_vmid, target_node


def destroy_machine(resource_type: str, vmid: int, node: str) -> None:
    """Stop and permanently delete a VM or container from Proxmox.

    The machine is first forced-stopped (errors are swallowed, as it may
    already be stopped), then deleted via the Proxmox API.

    Args:
        resource_type: ``'vm'`` or ``'ct'``.
        vmid: VMID of the resource to destroy.
        node: Proxmox node where the resource lives.

    Raises:
        RuntimeError: If the delete task fails.
        ValueError: If resource_type is not ``'vm'`` or ``'ct'``.
    """
    proxmox = get_proxmox_client()
    logger.info("Destroying %s vmid=%d on node=%s", resource_type, vmid, node)

    if resource_type == "vm":
        try:
            upid = proxmox.nodes(node).qemu(vmid).status.stop.post()
            wait_task(proxmox, node, upid)
        except Exception as exc:
            logger.warning("Stop VM %d failed (possibly already stopped): %s", vmid, exc)
        upid = proxmox.nodes(node).qemu(vmid).delete()
        wait_task(proxmox, node, upid)

    elif resource_type == "ct":
        try:
            upid = proxmox.nodes(node).lxc(vmid).status.stop.post()
            wait_task(proxmox, node, upid)
        except Exception as exc:
            logger.warning("Stop CT %d failed (possibly already stopped): %s", vmid, exc)
        upid = proxmox.nodes(node).lxc(vmid).delete()
        wait_task(proxmox, node, upid)

    else:
        raise ValueError(f"Tipo risorsa non supportato: {resource_type!r}")

    logger.info("Destroy completato: vmid=%d", vmid)
