import React, { useEffect, useRef, useState } from 'react'
import { Modal } from 'bootstrap'
import api from '../api/client.js'

/**
 * NewRequestModal — Bootstrap modal form for submitting a new VM/CT request.
 *
 * Fetches available options (bridges, storages, sizes) from /config/options
 * on first open, then presents:
 *  - Type selector (VM / CT)
 *  - Size card selector (Tiny / Medium / High)
 *  - Bridge dropdown
 *  - Storage dropdown
 *  - Name input
 *
 * @param {object}   props
 * @param {function} props.onCreated  Called after a successful submission
 */
export default function NewRequestModal({ onCreated }) {
  const modalRef = useRef(null)
  const bsModal = useRef(null)

  const [options, setOptions]   = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  const [form, setForm] = useState({
    name: '',
    resource_type: 'vm',
    size: 'tiny',
    bridge: '',
    storage: '',
  })

  // Initialise Bootstrap modal once
  useEffect(() => {
    bsModal.current = new Modal(modalRef.current, { backdrop: 'static' })
  }, [])

  // Load config options once
  useEffect(() => {
    api.get('/config/options')
      .then(({ data }) => {
        setOptions(data)
        setForm((f) => ({
          ...f,
          bridge:  data.bridges?.[0]?.id  ?? '',
          storage: data.storages?.[0]?.id ?? '',
        }))
      })
      .catch(() => setError('Impossibile caricare le opzioni di configurazione.'))
  }, [])

  function open() {
    setError('')
    bsModal.current.show()
  }

  function close() {
    bsModal.current.hide()
  }

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  function selectSize(sizeId) {
    setForm((f) => ({ ...f, size: sizeId }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api.post('/machines/', form)
      close()
      onCreated()
      // Reset form
      setForm((f) => ({
        ...f,
        name: '',
        resource_type: 'vm',
        size: 'tiny',
        bridge:  options?.bridges?.[0]?.id  ?? '',
        storage: options?.storages?.[0]?.id ?? '',
      }))
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail[0]?.msg : (detail ?? 'Errore durante la richiesta.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Trigger button */}
      <button
        id="new-request-btn"
        className="btn-primary-portal"
        onClick={open}
      >
        <i className="bi bi-plus-lg" />
        Nuova Richiesta
      </button>

      {/* Modal */}
      <div className="modal fade" ref={modalRef} tabIndex="-1" aria-labelledby="newRequestModalLabel" aria-hidden="true">
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">

            <div className="modal-header">
              <h5 className="modal-title" id="newRequestModalLabel">
                <i className="bi bi-plus-circle me-2" style={{ color: 'var(--accent)' }} />
                Nuova Richiesta Lab
              </h5>
              <button type="button" className="btn-close" onClick={close} aria-label="Chiudi" />
            </div>

            <form onSubmit={handleSubmit}>
              <div className="modal-body p-4">
                {error && (
                  <div className="alert-portal alert-danger-portal mb-3">
                    <i className="bi bi-exclamation-triangle-fill" />
                    {error}
                  </div>
                )}

                {/* Name */}
                <div className="mb-3">
                  <label className="form-label">Nome (hostname)</label>
                  <input
                    id="machine-name-input"
                    type="text"
                    name="name"
                    className="form-control"
                    placeholder="es. my-lab-01"
                    value={form.name}
                    onChange={handleChange}
                    required
                    pattern="^[a-zA-Z0-9\-]+$"
                    title="Solo lettere, numeri e trattini"
                  />
                </div>

                {/* Type */}
                <div className="mb-3">
                  <label className="form-label">Tipo di risorsa</label>
                  <div className="d-flex gap-2">
                    {[
                      { id: 'vm', label: 'Virtual Machine', icon: 'bi-cpu' },
                      { id: 'ct', label: 'Container LXC',   icon: 'bi-box' },
                    ].map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        id={`type-${t.id}-btn`}
                        className={`size-option flex-fill ${form.resource_type === t.id ? 'selected' : ''}`}
                        onClick={() => setForm((f) => ({ ...f, resource_type: t.id }))}
                      >
                        <i className={`bi ${t.icon} fs-5`} style={{ color: t.id === 'vm' ? 'var(--accent)' : 'var(--success)' }} />
                        <span className="size-name" style={{ fontSize: '0.8rem' }}>{t.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Size */}
                <div className="mb-3">
                  <label className="form-label">Taglia</label>
                  {options ? (
                    <div className="row g-2">
                      {options.sizes.map((s) => (
                        <div key={s.id} className="col-4">
                          <button
                            type="button"
                            id={`size-${s.id}-btn`}
                            className={`size-option w-100 ${form.size === s.id ? 'selected' : ''}`}
                            onClick={() => selectSize(s.id)}
                          >
                            <span className="size-name">{s.label}</span>
                            <span className="size-spec">{s.vcpu} vCPU · {s.memory_mb / 1024}GB RAM</span>
                            <span className="size-spec">{s.disk_gb}GB Disk</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="skeleton" style={{ height: '70px' }} />
                  )}
                </div>

                {/* Bridge */}
                <div className="mb-3">
                  <label htmlFor="bridge-select" className="form-label">Bridge di rete</label>
                  {options ? (
                    <select
                      id="bridge-select"
                      name="bridge"
                      className="form-select"
                      value={form.bridge}
                      onChange={handleChange}
                      required
                    >
                      {options.bridges.map((b) => (
                        <option key={b.id} value={b.id}>{b.label}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="skeleton" style={{ height: '40px' }} />
                  )}
                </div>

                {/* Storage */}
                <div className="mb-1">
                  <label htmlFor="storage-select" className="form-label">Storage</label>
                  {options ? (
                    <select
                      id="storage-select"
                      name="storage"
                      className="form-select"
                      value={form.storage}
                      onChange={handleChange}
                      required
                    >
                      {options.storages.map((s) => (
                        <option key={s.id} value={s.id}>{s.label}</option>
                      ))}
                    </select>
                  ) : (
                    <div className="skeleton" style={{ height: '40px' }} />
                  )}
                </div>

                <div className="alert-portal alert-info-portal mt-3">
                  <i className="bi bi-info-circle-fill" />
                  La risorsa sarà pronta al prossimo ciclo di automazione (max 60 s).
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-danger-portal" onClick={close} disabled={loading}>
                  Annulla
                </button>
                <button
                  id="submit-request-btn"
                  type="submit"
                  className="btn-primary-portal"
                  disabled={loading || !options}
                >
                  {loading ? (
                    <><div className="spinner-portal" /> Invio in corso…</>
                  ) : (
                    <><i className="bi bi-send" /> Invia richiesta</>
                  )}
                </button>
              </div>
            </form>

          </div>
        </div>
      </div>
    </>
  )
}
