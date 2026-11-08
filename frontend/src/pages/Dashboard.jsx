/**
 * src/pages/Dashboard.jsx
 * ───────────────────────
 * Stats + recent blogs table (old frontend/pages/dashboard.html).
 */

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { API } from '../lib/api.js';
import { formatCost, formatDate, formatTokens } from '../lib/utils.js';
import { useToast } from '../components/ToastProvider.jsx';
import Masthead from '../components/Masthead.jsx';
import PageShell from '../components/PageShell.jsx';
import StatusBadge from '../components/StatusBadge.jsx';

export default function Dashboard() {
  const toast = useToast();

  const [usage, setUsage] = useState(null);
  const [blogList, setBlogList] = useState(null); // null = loading
  const [listError, setListError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    document.title = 'Dashboard — BlogAI';
  }, []);

  const load = useCallback(async () => {
    try {
      const u = await API.usage();
      setUsage(u);
    } catch {}

    try {
      const data = await API.listBlogs();
      setBlogList(data);
      setListError(null);
    } catch (err) {
      setListError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function deleteBlog(id) {
    if (!window.confirm('Delete this blog? This cannot be undone.')) return;
    setDeletingId(id);
    try {
      await API.deleteBlog(id);
      toast.success('Blog deleted.');
      load();
    } catch (err) {
      toast.error(err.message);
      setDeletingId(null);
    }
  }

  const blogs = blogList ? blogList.items : [];

  return (
    <PageShell skipHref="#main" skipLabel="Skip to content">
      <Masthead />

      <main className="main-content" id="main">
        <div className="container">
          <section className="hero">
            <div className="hero-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '20px', flexWrap: 'wrap' }}>
              <div>
                <p className="eyebrow">Your blogs</p>
                <h1>Dashboard</h1>
              </div>
              <Link to="/create" className="btn btn-primary">+ New blog</Link>
            </div>
          </section>

          <section>
            <div className="stats-grid">
              <div className="stat-card"><div className="stat-orb">B</div><div className="stat-value" id="stat-blogs">{blogList ? blogList.total : '—'}</div><div className="stat-label">Total blogs</div></div>
              <div className="stat-card"><div className="stat-orb" style={{ background: 'linear-gradient(135deg,#7DD3FC,#0EA5E9)' }}>T</div><div className="stat-value" id="stat-tokens">{usage ? formatTokens(usage.total_tokens) : '—'}</div><div className="stat-label">Tokens used</div></div>
              <div className="stat-card"><div className="stat-orb" style={{ background: 'linear-gradient(135deg,#6EE7B7,#10B981)' }}>C</div><div className="stat-value" id="stat-cost">{usage ? formatCost(usage.total_cost) : '—'}</div><div className="stat-label">Total cost</div></div>
              <div className="stat-card"><div className="stat-orb" style={{ background: 'linear-gradient(135deg,#F9A8D4,#DB2777)' }}>S</div><div className="stat-value" id="stat-latency">{usage ? (usage.average_latency ? `${usage.average_latency.toFixed(1)}s` : '—') : '—'}</div><div className="stat-label">Avg. generation time</div></div>
            </div>
          </section>

          <section>
            <div className="card lift" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="card-header" style={{ padding: '28px 28px 0' }}>
                <h2>Recent blogs</h2>
              </div>
              <div id="blogs-container" style={{ padding: '0 28px 28px' }}>
                {listError ? (
                  <p style={{ padding: '20px' }}>{listError}</p>
                ) : !blogList ? (
                  <div style={{ textAlign: 'center', padding: '48px' }}>
                    <span className="spinner" aria-hidden="true"></span>
                    <p className="eyebrow" style={{ marginTop: '12px' }}>Loading…</p>
                  </div>
                ) : blogs.length === 0 ? (
                  <div className="empty-state">
                    <h3 style={{ marginBottom: '8px' }}>No blogs yet</h3>
                    <p style={{ marginBottom: '20px' }}>Create your first AI-generated blog.</p>
                    <Link to="/create" className="btn btn-primary">Get started</Link>
                  </div>
                ) : (
                  <div className="table-wrap" style={{ boxShadow: 'none' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Title / Topic</th>
                          <th>Status</th>
                          <th>Created</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {blogs.map((b) => (
                          <tr key={b.id}>
                            <td>
                              <div className="blog-title">{b.title || '(Untitled)'}</div>
                              <div className="blog-topic">{b.topic}</div>
                            </td>
                            <td><StatusBadge status={b.status} /></td>
                            <td style={{ fontSize: '.85rem', color: 'var(--clay-muted)' }}>{formatDate(b.created_at)}</td>
                            <td>
                              <div className="row-actions">
                                {b.status === 'completed'
                                  ? <Link to={`/viewer?id=${b.id}`} className="btn btn-secondary btn-sm">View</Link>
                                  : b.status === 'awaiting_approval'
                                    ? <Link to={`/approval?blog_id=${b.id}`} className="btn btn-primary btn-sm">Review</Link>
                                    : b.status === 'running'
                                      ? <Link to={`/approval?blog_id=${b.id}`} className="btn btn-secondary btn-sm">Track</Link>
                                      : null}
                                <button
                                  onClick={() => deleteBlog(b.id)}
                                  className="btn btn-danger btn-sm"
                                  disabled={deletingId === b.id}
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    </PageShell>
  );
}
