import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/client.js'

/**
 * Register page — creates a new user account and redirects to login.
 */
export default function Register() {
  const navigate = useNavigate()
  const [form, setForm]       = useState({ username: '', email: '', password: '', confirm: '' })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (form.password !== form.confirm) {
      setError('Le password non coincidono.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.post('/auth/register', {
        username: form.username,
        email: form.email,
        password: form.password,
      })
      navigate('/login')
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail[0]?.msg : (detail ?? 'Errore durante la registrazione.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <i className="bi bi-person-plus" style={{ color: 'white' }} />
        </div>

        <h1>Crea Account</h1>
        <p className="auth-subtitle">Registrati al Proxmox Self-Service Portal</p>

        {error && (
          <div className="alert-portal alert-danger-portal mb-3">
            <i className="bi bi-exclamation-triangle-fill" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="reg-username" className="form-label">Username</label>
            <input
              id="reg-username"
              type="text"
              name="username"
              className="form-control"
              placeholder="min. 3 caratteri"
              value={form.username}
              onChange={handleChange}
              required
              minLength={3}
              autoFocus
            />
          </div>

          <div className="mb-3">
            <label htmlFor="reg-email" className="form-label">Email</label>
            <input
              id="reg-email"
              type="email"
              name="email"
              className="form-control"
              placeholder="nome@esempio.it"
              value={form.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="mb-3">
            <label htmlFor="reg-password" className="form-label">Password</label>
            <input
              id="reg-password"
              type="password"
              name="password"
              className="form-control"
              placeholder="min. 8 caratteri"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
            />
          </div>

          <div className="mb-4">
            <label htmlFor="reg-confirm" className="form-label">Conferma Password</label>
            <input
              id="reg-confirm"
              type="password"
              name="confirm"
              className="form-control"
              placeholder="••••••••"
              value={form.confirm}
              onChange={handleChange}
              required
            />
          </div>

          <button
            id="register-submit-btn"
            type="submit"
            className="btn-primary-portal w-100 justify-content-center"
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner-portal" /> Registrazione…</>
            ) : (
              <><i className="bi bi-person-check" /> Crea Account</>
            )}
          </button>
        </form>

        <p className="text-center mt-4" style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Hai già un account?{' '}
          <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>
            Accedi
          </Link>
        </p>
      </div>
    </div>
  )
}
