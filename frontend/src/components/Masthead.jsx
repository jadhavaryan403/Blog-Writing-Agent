/**
 * src/components/Masthead.jsx
 * ───────────────────────────
 * App header: brand, primary nav with active state, user chip, logout.
 * Port of the shared <header class="masthead"> markup plus the old
 * setActiveNav()/renderSidebarUser()/logout() helpers.
 */

import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { API, Auth } from '../lib/api.js';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/create',    label: 'New blog' },
  { to: '/settings',  label: 'Settings' },
];

export default function Masthead() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  // Fill the user chip once /auth/me resolves (old renderSidebarUser).
  useEffect(() => {
    let alive = true;
    API.me()
      .then((u) => { if (alive) setUser(u); })
      .catch(() => {});
    return () => { alive = false; };
  }, []);

  // Masthead date fill for any [data-masthead-date] element (old renderMastheadDate).
  useEffect(() => {
    const els = document.querySelectorAll('[data-masthead-date]');
    if (!els.length) return;
    const s = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
    els.forEach((el) => { el.textContent = s; });
  }, []);

  function handleLogout(e) {
    e.preventDefault();
    Auth.clear();
    navigate('/login');
  }

  const initial = user ? (user.name || 'E')[0].toUpperCase() : '·';
  const name = user ? user.name : '—';
  const email = user ? user.email : '—';

  return (
    <header className="masthead">
      <div className="masthead-inner">
        <Link className="masthead-brand" to="/">BlogAI</Link>
        <nav className="masthead-nav" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={pathname === item.to ? 'nav-item active' : 'nav-item'}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="masthead-user" id="sidebar-user">
          <span className="user-chip">
            <span className="avatar" id="user-avatar">{initial}</span>
            <span>
              <span className="user-name">{name}</span>
              <span className="user-email">{email}</span>
            </span>
          </span>
          <a className="link-logout" href="#" onClick={handleLogout}>Log out</a>
        </div>
      </div>
    </header>
  );
}
