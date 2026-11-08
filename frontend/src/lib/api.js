/**
 * src/lib/api.js
 * ──────────────
 * Centralised API client for all backend calls.
 * Handles: auth headers, token refresh, error parsing.
 * NOTE: All endpoint paths and function signatures are backend contracts.
 * Do not change paths without updating backend routers.
 */

const BASE = '/api/v1';

// ── Token management ──────────────────────────────────────────────────────────
export const Auth = {
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

export const API = {
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

// ── Auth helpers ──────────────────────────────────────────────────────────────
export function logout() {
  Auth.clear();
  window.location.href = '/login';
}
