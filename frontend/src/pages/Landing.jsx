/**
 * src/pages/Landing.jsx
 * ─────────────────────
 * Marketing/landing page (old frontend/index.html).
 * Logged-in users skip the landing page entirely.
 */

import { useEffect } from 'react';
import { Link, Navigate } from 'react-router-dom';

import { Auth } from '../lib/api.js';
import PageShell from '../components/PageShell.jsx';

export default function Landing() {
  useEffect(() => {
    document.title = 'BlogAI — AI Blog Generator';
  }, []);

  if (Auth.isLoggedIn()) return <Navigate to="/dashboard" replace />;

  return (
    <PageShell skipHref="#main" skipLabel="Skip to content">
      <header className="masthead">
        <div className="masthead-inner">
          <Link className="masthead-brand" to="/">BlogAI</Link>
          <nav className="masthead-nav" aria-label="Primary">
            <Link to="/login" id="nav-auth">Sign in</Link>
          </nav>
        </div>
      </header>

      <main className="main-content" id="main">
        <div className="container">
          <section className="hero">
            <div className="hero-card">
              <div className="orb-row" aria-hidden="true">
                <span className="orb orb-violet"></span>
                <span className="orb orb-pink"></span>
                <span className="orb orb-sky"></span>
              </div>
              <h1>Blogs that <span className="clay-gradient-text">write themselves.</span><br />You approve every word.</h1>
              <p className="lead" style={{ marginTop: '16px' }}>Describe a topic. Review the AI-drafted outline. Get a finished, editable blog.</p>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '28px' }}>
                <Link to="/register" className="btn btn-primary" id="cta-primary">Get started</Link>
                <Link to="/login" className="btn btn-secondary" id="cta-secondary">Sign in</Link>
              </div>
            </div>
          </section>

          <section className="section-pad">
            <div className="how-steps">
              <div className="how-step"><span className="step-num">1</span><span><strong>Describe</strong> your topic and preferences.</span></div>
              <div className="how-step"><span className="step-num">2</span><span><strong>Approve</strong> the AI-generated outline.</span></div>
              <div className="how-step"><span className="step-num">3</span><span><strong>Read & edit</strong> each section.</span></div>
            </div>
          </section>
        </div>
      </main>
    </PageShell>
  );
}
