import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Modal } from 'bootstrap'
import Navbar from '../components/Navbar.jsx'
import MachineCard from '../components/MachineCard.jsx'
import NewRequestModal from '../components/NewRequestModal.jsx'
import api from '../api/client.js'

/**
 * Dashboard — "I miei Lab"
 *
 * Lists all machines for the current user (admins see all).
 * Provides:
 *  - Auto-refresh every 30 seconds
 *  - Manual refresh button
 *  - New request modal
 *  - Delete confirmation modal
 */
export default function Dashboard() {
  const user = JSON.parse(localStorage.getItem('user') ?? '{}')

  const [machines, setMachines] = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [deleting, setDeleting] = useState(false)
  const [machineToDelete, setMachineToDelete] = useState(null)

  const confirmModalRef = useRef(null)
  const bsConfirmModal  = useRef(null)

  // Init confirmation modal
  useEffect(() => {
    bsConfirmModal.current = new Modal(confirmModalRef.current, { backdrop: 'static' })
  }, [])

  const fetchMachines = useCallback(async () => {
    try {
      const { data } = await api.get('/machines/')
      setMachines(data)
      setError('')
    } catch {
      setError('Impossibile caricare le macchine. Riprova.')
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load + auto-refresh every 30s
  useEffect(() => {
    fetchMachines()
    const interval = setInterval(fetchMachines, 30_000)
    return () => clearInterval(interval)
  }, [fetchMachines])

  function openDeleteConfirm(machine) {
    setMachineToDelete(machine)
    bsConfirmModal.current.show()
  }

  function closeDeleteConfirm() {
    bsConfirmModal.current.hide()
    setMachineToDelete(null)
  }

  async function confirmDelete() {
    if (!machineToDelete) return
    setDeleting(true)
    try {
      await api.delete(`/machines/${machineToDelete.id}`)
      closeDeleteConfirm()
      await fetchMachines()
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Errore durante l\'eliminazione.')
      closeDeleteConfirm()
    } finally {
      setDeleting(false)
    }
  }

  // Separate by status for better UX
  const active  = machines.filter((m) => m.status === 'active')
  const pending = machines.filter((m) => m.status === 'pending')
  const failed  = machines.filter((m) => m.status === 'failed')

  function MachineGrid({ items }) {
    if (!items.length) return null
    return (
      <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-3">
        {items.map((m) => (
          <div key={m.id} className="col">
            <MachineCard
              machine={m}
              onDelete={openDeleteConfirm}
              isAdmin={user.is_admin}
            />
          </div>
        ))}
      </div>
    )
  }

  function SectionHeader({ icon, title, count, color }) {
    if (!count) return null
    return (
      <div className="d-flex align-items-center gap-2 mb-3">
        <i className={`bi ${icon}`} style={{ color, fontSize: '1.1rem' }} />
        <h2 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>{title}</h2>
        <span className="badge-portal badge-vmid">{count}</span>
      </div>
    )
  }

  return (
    <>
      <Navbar user={user} />

      <div className="dashboard-container">
        {/* Header */}
        <div className="dashboard-header">
          <h1>I miei Lab</h1>
          <div className="d-flex gap-2">
            <button
              id="refresh-btn"
              className="btn-danger-portal"
              onClick={fetchMachines}
              title="Aggiorna lista"
              style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}
            >
              <i className="bi bi-arrow-clockwise" />
              <span className="d-none d-sm-inline">Aggiorna</span>
            </button>
            <NewRequestModal onCreated={fetchMachines} />
          </div>
        </div>

        {/* Global error */}
        {error && (
          <div className="alert-portal alert-danger-portal mb-4">
            <i className="bi bi-exclamation-triangle-fill" />
            {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="col">
                <div className="machine-card">
                  <div className="skeleton mb-3" style={{ height: '40px', width: '40px', borderRadius: '8px' }} />
                  <div className="skeleton mb-2" style={{ height: '18px', width: '60%' }} />
                  <div className="skeleton mb-1" style={{ height: '14px', width: '80%' }} />
                  <div className="skeleton" style={{ height: '14px', width: '40%' }} />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Machine sections */}
        {!loading && (
          <>
            {machines.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon"><i className="bi bi-server" /></div>
                <h3>Nessuna risorsa ancora</h3>
                <p style={{ fontSize: '0.875rem' }}>
                  Clicca su <strong>Nuova Richiesta</strong> per richiedere la tua prima VM o Container.
                </p>
              </div>
            ) : (
              <>
                {/* Active */}
                {active.length > 0 && (
                  <div className="mb-5">
                    <SectionHeader icon="bi-check-circle-fill" title="Attive" count={active.length} color="var(--success)" />
                    <MachineGrid items={active} />
                  </div>
                )}

                {/* Pending */}
                {pending.length > 0 && (
                  <div className="mb-5">
                    <SectionHeader icon="bi-clock-history" title="In attesa" count={pending.length} color="var(--warning)" />
                    <MachineGrid items={pending} />
                  </div>
                )}

                {/* Failed */}
                {failed.length > 0 && (
                  <div className="mb-5">
                    <SectionHeader icon="bi-exclamation-circle-fill" title="Con errori" count={failed.length} color="var(--danger)" />
                    <MachineGrid items={failed} />
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>

      {/* Delete confirmation modal */}
      <div className="modal fade" ref={confirmModalRef} tabIndex="-1" aria-labelledby="confirmDeleteLabel" aria-hidden="true">
        <div className="modal-dialog modal-dialog-centered modal-sm">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title" id="confirmDeleteLabel">
                <i className="bi bi-exclamation-triangle-fill me-2" style={{ color: 'var(--danger)' }} />
                Conferma eliminazione
              </h5>
              <button type="button" className="btn-close" onClick={closeDeleteConfirm} aria-label="Chiudi" />
            </div>
            <div className="modal-body p-4" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              {machineToDelete && (
                <>
                  Stai per eliminare{' '}
                  <strong style={{ color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                    {machineToDelete.name}
                  </strong>.
                  <br /><br />
                  {machineToDelete.status === 'active'
                    ? 'La macchina verrà fermata e rimossa da Proxmox. Questa azione è irreversibile.'
                    : 'Il job in attesa verrà annullato.'}
                </>
              )}
            </div>
            <div className="modal-footer">
              <button
                id="cancel-delete-btn"
                type="button"
                className="btn-danger-portal"
                onClick={closeDeleteConfirm}
                disabled={deleting}
                style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}
              >
                Annulla
              </button>
              <button
                id="confirm-delete-btn"
                type="button"
                className="btn-primary-portal"
                onClick={confirmDelete}
                disabled={deleting}
                style={{ background: 'var(--danger)' }}
              >
                {deleting ? (
                  <><div className="spinner-portal" /> Eliminazione…</>
                ) : (
                  <><i className="bi bi-trash3" /> Elimina</>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
