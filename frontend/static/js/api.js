/**
 * static/js/api.js
 * ─────────────────
 * Centralised API client for all backend calls.
 * Handles: auth headers, token refresh, error parsing, toast notifications.
 * Design: Minimalist Monochrome — sharp, instant, black & white only.
 * NOTE: All endpoint paths and function signatures are backend contracts.
 * Do not change paths without updating backend routers.
 */

const BASE = '/api/v1';

// ── Token management ──────────────────────────────────────────────────────────
const Auth = {
  getAccess:  () => localStorage.getItem('access_token'),
  getRefresh: () => localStorage.getItem('refresh_token'),
  save(tokens) {
    localStorage.setItem('access_token',  tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  isLoggedIn: () => !!localStorage.getItem('access_token'),
};

// ── Toast notifications (monochrome, instant) ─────────────────────────────────
const Toast = {
  container: null,
  init() {
    if (!this.container) {
      this.container = document.getElementById('toast-container') || (() => {
        const c = document.createElement('div');
        c.id = 'toast-container';
        document.body.appendChild(c);
        return c;
      })();
    }
  },
  show(message, type = 'info', duration = 4000) {
    this.init();
    const icons = { success: '✓', error: '✕', info: '§' };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.setAttribute('role', 'status');
    el.innerHTML = `<span aria-hidden="true">${icons[type] || icons.info}</span><span>${message}</span>`;
    this.container.appendChild(el);
    setTimeout(() => { el.remove(); }, duration);
  },
  success: (msg) => Toast.show(msg, 'success'),
  error:   (msg) => Toast.show(msg, 'error'),
  info:    (msg) => Toast.show(msg, 'info'),
};

// ── HTTP client ───────────────────────────────────────────────────────────────
async function request(method, path, body = null, retry = true) {
  const headers = { 'Content-Type': 'application/json' };
  const token = Auth.getAccess();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  let res = await fetch(BASE + path, opts);

  // Auto-refresh on 401
  if (res.status === 401 && retry && Auth.getRefresh()) {
    const refreshRes = await fetch(BASE + '/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: Auth.getRefresh() }),
    });
    if (refreshRes.ok) {
      Auth.save(await refreshRes.json());
      return request(method, path, body, false);
    } else {
      Auth.clear();
      window.location.href = '/login';
      return;
    }
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || JSON.stringify(err);
    } catch {}
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

const API = {
  get:    (path)         => request('GET',    path),
  post:   (path, body)   => request('POST',   path, body),
  put:    (path, body)   => request('PUT',    path, body),
  delete: (path)         => request('DELETE', path),

  // Auth
  register: (d)   => API.post('/auth/register', d),
  login:    (d)   => API.post('/auth/login', d),
  refresh:  (d)   => API.post('/auth/refresh', d),
  me:       ()    => API.get('/auth/me'),

  // Blogs
  listBlogs:  ()         => API.get('/blogs'),
  getBlog:    (id)       => API.get(`/blogs/${id}`),
  deleteBlog: (id)       => API.delete(`/blogs/${id}`),
  getBlogTokens: (id)    => API.get(`/blogs/${id}/tokens`),

  // Workflow
  startWorkflow:  (data) => API.post('/workflow/start', data),
  workflowStatus: (jobId) => API.get(`/workflow/${jobId}`),
  approvePlan:    (jobId) => API.post(`/workflow/${jobId}/approve-plan`, {}),
  editPlan:       (jobId, plan) => API.post('/workflow/' + jobId + '/edit-plan', plan),

  // Metrics
  usage:       () => API.get('/metrics/usage'),
  agentRuns:   () => API.get('/metrics/agent-runs'),
  blogHistory: () => API.get('/metrics/blog-history'),

  // Preferences
  getPrefs:    ()    => API.get('/preferences'),
  updatePrefs: (d)   => API.put('/preferences', d),

  // Section editing
  getSections:   (blogId)              => API.get(`/blogs/${blogId}/sections`),
  editSection:   (blogId, body)        => API.post(`/blogs/${blogId}/edit-section`, body),
};

// ── Utility helpers ───────────────────────────────────────────────────────────
function guardAuth() {
  if (!Auth.isLoggedIn()) window.location.href = '/login';
}

function formatCost(n) {
  return n < 0.01 ? '<$0.01' : `$${n.toFixed(4)}`;
}

function formatTokens(n) {
  return n >= 1000 ? `${(n/1000).toFixed(1)}k` : String(n);
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
}

function statusBadge(status) {
  const map = {
    pending: 'badge-pending', planning: 'badge-planning',
    running: 'badge-running', awaiting_approval: 'badge-awaiting',
    completed: 'badge-completed', error: 'badge-error',
  };
  const cls = map[status] || 'badge-pending';
  const label = String(status || 'pending').replace(/_/g, ' ');
  return `<span class="badge ${cls}">${label}</span>`;
}

// Sidebar / masthead active state (supports .nav-item and .masthead-nav a)
function setActiveNav() {
  const page = window.location.pathname;
  document.querySelectorAll('.nav-item, .masthead-nav a').forEach(el => {
    el.classList.toggle('active', el.getAttribute('href') === page);
  });
}

// Render user info in sidebar/masthead (supports both legacy + new markup)
async function renderSidebarUser() {
  try {
    const user = await API.me();
    const initial = (user.name || 'E')[0].toUpperCase();
    const wrap = document.getElementById('sidebar-user');
    if (wrap) {
      const n = wrap.querySelector('.user-name');
      const e = wrap.querySelector('.user-email');
      const a = wrap.querySelector('.avatar');
      if (n) n.textContent = user.name;
      if (e) e.textContent = user.email;
      if (a) a.textContent = initial;
    }
    const av2 = document.getElementById('user-avatar');
    if (av2) av2.textContent = initial;
    document.querySelectorAll('.user-name').forEach(el => { el.textContent = user.name; });
    document.querySelectorAll('.user-email').forEach(el => { el.textContent = user.email; });
  } catch {}
}

// Masthead date: "02 OCT 2026 — VOL. 01"
function renderMastheadDate() {
  const els = document.querySelectorAll('[data-masthead-date]');
  if (!els.length) return;
  const s = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
  els.forEach(el => { el.textContent = s; });
}
document.addEventListener('DOMContentLoaded', renderMastheadDate);

function logout() {
  Auth.clear();
  window.location.href = '/login';
}

// ── Editorial Markdown Renderer (marked + monochrome post-process) ────────────
function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function renderMarkdown(md) {
  const src = String(md || '');
  if (window.marked) {
    try {
      if (typeof marked.parse === 'function') return marked.parse(src);
      if (typeof marked === 'function') return marked(src);
    } catch {}
  }
  // Minimal fallback: headings, bold/italic, links, paragraphs, rules.
  return escapeHtml(src)
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/^---$/gm, '<hr>')
    .split(/\n{2,}/).map(b => /^<h|^<hr/.test(b.trim()) ? b : `<p>${b.replace(/\n/g, '<br>')}</p>`).join('\n');
}