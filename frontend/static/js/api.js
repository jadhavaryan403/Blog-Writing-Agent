/**
 * static/js/api.js
 * ─────────────────
 * Centralised API client for all backend calls.
 * Handles: auth headers, token refresh, error parsing, toast notifications.
 * Upgraded with a high-fidelity, block-based Cyberpunk Markdown Engine.
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

// ── Toast notifications ───────────────────────────────────────────────────────
const Toast = {
  container: null,
  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  },
  show(message, type = 'info', duration = 4000) {
    this.init();
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
    this.container.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(120%)';
      setTimeout(() => el.remove(), 300); }, duration);
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
  startWorkflow:  (topic) => API.post('/workflow/start', { topic }),
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
  return `<span class="badge ${cls}">${status.replace(/_/g,' ')}</span>`;
}

// Sidebar active state
function setActiveNav() {
  const page = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.getAttribute('href') === page);
  });
}

// Render user info in sidebar
async function renderSidebarUser() {
  try {
    const user = await API.me();
    const el = document.getElementById('sidebar-user');
    if (el) {
      el.querySelector('.user-name').textContent = user.name;
      el.querySelector('.user-email').textContent = user.email;
      el.querySelector('.avatar').textContent = user.name[0].toUpperCase();
    }
  } catch {}
}

function logout() {
  Auth.clear();
  window.location.href = '/login';
}

// ── Flawless Cyberpunk Markdown Renderer (Block-Based Lexer Architecture) ─────
function renderMarkdown(md) {
  return marked.parse(md);
}