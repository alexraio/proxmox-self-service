import React from 'react'

/**
 * StatusBadge — coloured pill badge for a machine's lifecycle status.
 *
 * @param {object} props
 * @param {'pending'|'active'|'failed'|'deleted'} props.status
 */
export function StatusBadge({ status }) {
  const cfg = {
    pending: { cls: 'badge-pending', icon: 'bi-clock-history', label: 'In attesa' },
    active:  { cls: 'badge-active',  icon: 'bi-check-circle-fill', label: 'Attiva' },
    failed:  { cls: 'badge-failed',  icon: 'bi-exclamation-circle-fill', label: 'Errore' },
    deleted: { cls: 'badge-deleted', icon: 'bi-trash3-fill', label: 'Eliminata' },
  }
  const { cls, icon, label } = cfg[status] ?? cfg.deleted
  return (
    <span className={`badge-portal ${cls}`}>
      <i className={`bi ${icon}`} />
      {label}
    </span>
  )
}

/**
 * BridgeBadge — coloured badge showing the network bridge.
 *
 * @param {object} props
 * @param {string} props.bridge  e.g. "vmbr0" or "vmbr0.50"
 */
export function BridgeBadge({ bridge }) {
  const isVlan = bridge.includes('.')
  return (
    <span className={`badge-portal ${isVlan ? 'badge-bridge-vlan' : 'badge-bridge-standard'}`}>
      <i className="bi bi-diagram-3" />
      {bridge}
    </span>
  )
}

/**
 * StorageBadge — purple badge showing the Proxmox storage ID.
 *
 * @param {object} props
 * @param {string} props.storage  e.g. "local-lvm"
 */
export function StorageBadge({ storage }) {
  return (
    <span className="badge-portal badge-storage">
      <i className="bi bi-hdd-stack" />
      {storage}
    </span>
  )
}

/**
 * SizeBadge — cyan badge showing the size tier.
 *
 * @param {object} props
 * @param {'tiny'|'medium'|'high'} props.size
 */
export function SizeBadge({ size }) {
  const icons = { tiny: 'bi-phone', medium: 'bi-laptop', high: 'bi-server' }
  return (
    <span className="badge-portal badge-size">
      <i className={`bi ${icons[size] ?? 'bi-server'}`} />
      {size}
    </span>
  )
}

/**
 * TypeBadge — pink badge showing VM or CT.
 *
 * @param {object} props
 * @param {'vm'|'ct'} props.type
 */
export function TypeBadge({ type }) {
  return (
    <span className="badge-portal badge-type">
      <i className={`bi ${type === 'vm' ? 'bi-cpu' : 'bi-box'}`} />
      {type.toUpperCase()}
    </span>
  )
}
