/**
 * src/pages/Register.jsx
 * ──────────────────────
 * Registration page (old frontend/pages/register.html).
 */

import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { API, Auth } from '../lib/api.js';
import { useToast } from '../components/ToastProvider.jsx';
import { useTimeouts } from '../lib/hooks.js';
import PageShell from '../components/PageShell.jsx';

export default function Register() {
  const navigate = useNavigate();
  const toast = useToast();
  const schedule = useTimeouts();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    document.title = 'Create account — BlogAI';
  }, []);

  if (Auth.isLoggedIn()) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    if (password !== confirm) {
      toast.error('Passwords do not match');
      return;
    }
    setSubmitting(true);
    try {
      await API.register({
        name: name.trim(),
        email: email.trim(),
        password,
      });
      toast.success('Account created. Signing you in…');
      const tokens = await API.login({ email: email.trim(), password });
      Auth.save(tokens);
      schedule(() => navigate('/dashboard'), 700);
    } catch (err) {
      toast.error(err.message);
      setSubmitting(false);
    }
  }

  return (
    <PageShell skipHref="#register-form" skipLabel="Skip to sign up">
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <div className="logo-icon" aria-hidden="true">
              <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth="2" strokeLinecap="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z" /></svg>
            </div>
            <h2>Create account</h2>
            <p style={{ color: 'var(--clay-muted)', marginTop: '6px' }}>Start generating blogs in minutes.</p>
          </div>
          <form id="register-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">Name</label>
              <input
                type="text"
                id="name"
                placeholder="Jane Doe"
                required
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
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
              <label htmlFor="password">Password (min 8 characters)</label>
              <input
                type="password"
                id="password"
                placeholder="••••••••"
                required
                minLength={8}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirm">Confirm password</label>
              <input
                type="password"
                id="confirm"
                placeholder="••••••••"
                required
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary btn-lg"
              style={{ width: '100%', justifyContent: 'center', marginTop: '6px' }}
              id="submit-btn"
              disabled={submitting}
            >
              {submitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>
          <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '.92rem' }}>
            Have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </PageShell>
  );
}
