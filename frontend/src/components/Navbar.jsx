import React from 'react'
import { Link, useNavigate } from 'react-router-dom'

/**
 * Navbar persists across all authenticated pages.
 * Shows the portal brand, the logged-in username, and a logout button.
 *
 * @param {object} props
 * @param {object} props.user  - User object from localStorage
 */
export default function Navbar({ user }) {
  const navigate = useNavigate()

  function handleLogout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <nav className="portal-navbar navbar navbar-expand-lg">
      <div className="container-fluid px-0">
        {/* Brand */}
        <Link className="navbar-brand" to="/">
          <div className="brand-icon">
            <i className="bi bi-server" />
          </div>
          Proxmox Portal
        </Link>

        {/* Right side */}
        <div className="d-flex align-items-center gap-3 ms-auto">
          {user && (
            <span className="nav-link d-none d-md-flex align-items-center gap-2">
              <i className="bi bi-person-circle" style={{ color: 'var(--accent)' }} />
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                {user.username}
              </span>
              {user.is_admin && (
                <span className="badge-portal badge-active" style={{ fontSize: '0.65rem', padding: '0.15rem 0.45rem' }}>
                  Admin
                </span>
              )}
            </span>
          )}
          <button
            id="logout-btn"
            className="btn-danger-portal"
            onClick={handleLogout}
            title="Esci"
          >
            <i className="bi bi-box-arrow-right" />
            <span className="d-none d-sm-inline">Esci</span>
          </button>
        </div>
      </div>
    </nav>
  )
}
