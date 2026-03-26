import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/client.js'

/**
 * Login page — authenticates the user and stores JWT in localStorage.
 */
export default function Login() {
  const navigate = useNavigate()
  const [form, setForm]       = useState({ username: '', password: '' })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/auth/login', form)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Errore di connessione al server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <i className="bi bi-server" style={{ color: 'white' }} />
        </div>

        <h1>Accedi al Portale</h1>
        <p className="auth-subtitle">Proxmox Self-Service Portal</p>

        {error && (
          <div className="alert-portal alert-danger-portal mb-3">
            <i className="bi bi-exclamation-triangle-fill" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="login-username" className="form-label">Username</label>
            <input
              id="login-username"
              type="text"
              name="username"
              className="form-control"
              placeholder="il tuo username"
              value={form.username}
              onChange={handleChange}
              required
              autoFocus
            />
          </div>

          <div className="mb-4">
            <label htmlFor="login-password" className="form-label">Password</label>
            <input
              id="login-password"
              type="password"
              name="password"
              className="form-control"
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="btn-primary-portal w-100 justify-content-center"
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner-portal" /> Accesso…</>
            ) : (
              <><i className="bi bi-box-arrow-in-right" /> Accedi</>
            )}
          </button>
        </form>

        <p className="text-center mt-4" style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Non hai un account?{' '}
          <Link to="/register" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: 600 }}>
            Registrati
          </Link>
        </p>
      </div>
    </div>
  )
}
