import React from 'react'
import { StatusBadge, BridgeBadge, StorageBadge, SizeBadge, TypeBadge } from './StatusBadge.jsx'

/**
 * MachineCard — displays a single provisioned or pending machine.
 *
 * @param {object}   props
 * @param {object}   props.machine    - Machine data from the API
 * @param {function} props.onDelete   - Called with the machine ID to trigger deletion
 * @param {boolean}  props.isAdmin    - Whether the current user is an admin
 */
export default function MachineCard({ machine, onDelete, isAdmin }) {
  const isVM = machine.resource_type === 'vm'
  const canDelete = machine.status === 'pending' || machine.status === 'active'

  const formattedDate = new Date(machine.created_at).toLocaleString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

  return (
    <div className="machine-card animate-in">
      {/* Icon */}
      <div className={`card-icon ${isVM ? 'vm-icon' : 'ct-icon'}`}>
        <i className={`bi ${isVM ? 'bi-cpu' : 'bi-box'}`} />
      </div>

      {/* Name */}
      <div className="card-name">{machine.name}</div>

      {/* Badges row */}
      <div className="card-meta">
        <TypeBadge type={machine.resource_type} />
        <SizeBadge size={machine.size} />
        <BridgeBadge bridge={machine.bridge} />
        <StorageBadge storage={machine.storage} />
        {machine.proxmox_vmid && (
          <span className="badge-portal badge-vmid">
            <i className="bi bi-hash" />
            {machine.proxmox_vmid}
          </span>
        )}
      </div>

      {/* Node info */}
      {machine.proxmox_node && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
          <i className="bi bi-diagram-2 me-1" />
          Nodo: <strong style={{ color: 'var(--text-secondary)' }}>{machine.proxmox_node}</strong>
        </div>
      )}

      {/* Error message */}
      {machine.status === 'failed' && machine.error_message && (
        <div className="alert-portal alert-danger-portal mb-2" style={{ fontSize: '0.73rem' }}>
          <i className="bi bi-exclamation-triangle-fill" />
          {machine.error_message}
        </div>
      )}

      {/* Admin: show owner */}
      {isAdmin && machine.owner && (
        <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
          <i className="bi bi-person me-1" />
          {machine.owner.username}
        </div>
      )}

      {/* Footer */}
      <div className="card-footer-row">
        <div>
          <StatusBadge status={machine.status} />
          <div className="card-date mt-1">{formattedDate}</div>
        </div>
        {canDelete && (
          <button
            id={`delete-machine-${machine.id}`}
            className="btn-danger-portal"
            onClick={() => onDelete(machine)}
            title="Elimina macchina"
          >
            <i className="bi bi-trash3" />
            Elimina
          </button>
        )}
      </div>
    </div>
  )
}
