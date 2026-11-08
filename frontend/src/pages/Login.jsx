/**
 * src/pages/Login.jsx
 * ───────────────────
 * Sign-in page (old frontend/pages/login.html).
 */

import { useEffect, useRef, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { API, Auth } from '../lib/api.js';
import { useToast } from '../components/ToastProvider.jsx';
import { useTimeouts } from '../lib/hooks.js';
import PageShell from '../components/PageShell.jsx';

export default function Login() {
  const navigate = useNavigate();
  const toast = useToast();
  const schedule = useTimeouts();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    document.title = 'Sign in — BlogAI';
  }, []);

  if (Auth.isLoggedIn()) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const tokens = await API.login({
        email: email.trim(),
        password,
      });
      Auth.save(tokens);
      toast.success('Welcome back.');
      schedule(() => navigate('/dashboard'), 500);
    } catch (err) {
      toast.error(err.message);
      setSubmitting(false);
    }
  }

  return (
    <PageShell skipHref="#login-form" skipLabel="Skip to sign in">
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <div className="logo-icon" aria-hidden="true">
              <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth="2" strokeLinecap="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z" /></svg>
            </div>
            <h2>Welcome back</h2>
            <p style={{ color: 'var(--clay-muted)', marginTop: '6px' }}>Sign in to continue.</p>
          </div>
          <form id="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                placeholder="you@example.com"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                placeholder="••••••••"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary btn-lg"
              style={{ width: '100%', justifyContent: 'center', marginTop: '6px' }}
              id="submit-btn"
              disabled={submitting}
            >
              {submitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
          <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '.92rem' }}>
            No account? <Link to="/register">Create one</Link>
          </p>
        </div>
      </div>
    </PageShell>
  );
}
