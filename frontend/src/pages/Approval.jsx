/**
 * src/pages/Approval.jsx
 * ──────────────────────
 * Outline review + human approval + live workflow tracking
 * (old frontend/pages/approval.html).
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';

import { API } from '../lib/api.js';
import { useToast } from '../components/ToastProvider.jsx';
import { useTimeouts } from '../lib/hooks.js';
import Masthead from '../components/Masthead.jsx';
import PageShell from '../components/PageShell.jsx';

const NODE_LABELS = {
  researcher:    'Researching',
  generate:      'Writing',
  image_planner: 'Planning images',
  image_search:  'Finding images',
  stitch_blog:   'Assembling blog',
  persist_state: 'Saving',
  END:           'Done',
};

export default function Approval() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('job_id');
  const navigate = useNavigate();
  const toast = useToast();
  const schedule = useTimeouts();

  // Keep navigate fresh for the polling interval without restarting it.
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;

  const [loadError, setLoadError] = useState(null);
  const [planReady, setPlanReady] = useState(false);

  const [title, setTitle] = useState('');
  const [wordCount, setWordCount] = useState('1500');
  const [sections, setSections] = useState([]);
  const [researchTasks, setResearchTasks] = useState([]);

  const [submitting, setSubmitting] = useState(false);

  const [overlayVisible, setOverlayVisible] = useState(false);
  const [overlayTitle, setOverlayTitle] = useState('Processing…');
  const [overlayStatus, setOverlayStatus] = useState('Starting');
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    document.title = 'Review outline — BlogAI';
  }, []);

  const updateOverlayStatus = useCallback((node) => {
    setOverlayTitle(NODE_LABELS[node] || 'Processing…');
    setOverlayStatus(String(node || '…'));
  }, []);

  const showRunningOverlay = useCallback((currentNode) => {
    setOverlayVisible(true);
    updateOverlayStatus(currentNode);
  }, [updateOverlayStatus]);

  const applyPlan = useCallback((plan) => {
    setTitle(plan.title || '');
    setWordCount(String(plan.estimated_word_count || 1500));

    if (plan.research_required) {
      const tasks = plan.research_tasks
        ? (Array.isArray(plan.research_tasks) ? plan.research_tasks : Object.values(plan.research_tasks))
        : [];
      if (tasks.length) setResearchTasks(tasks.map((t) => String(t)));
    }

    setSections((plan.sections || []).map((sec) => ({
      title: sec.title || '',
      description: sec.description || '',
      word_count: sec.word_count || 300,
    })));
    setPlanReady(true);
  }, []);

  // ── Initial plan load (retries while the plan is still generating) ─────────
  useEffect(() => {
    if (!jobId) return;
    let alive = true;
    let retryTimer = null;

    async function loadPlan() {
      try {
        const status = await API.workflowStatus(jobId);
        if (!alive) return;
        if (status.status === 'completed' && status.final_blog) {
          navigateRef.current(`/viewer?id=${status.blog_id}`, { replace: true });
          return;
        }
        if (status.status === 'running') {
          showRunningOverlay(status.current_node);
          setPolling(true);
          return;
        }
        if (!status.plan) {
          retryTimer = setTimeout(loadPlan, 2000);
          return;
        }
        applyPlan(status.plan);
      } catch (err) {
        if (alive) setLoadError(err.message);
      }
    }

    loadPlan();
    return () => {
      alive = false;
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [jobId, applyPlan, showRunningOverlay]);

  // ── Workflow polling (old startPolling) ────────────────────────────────────
  useEffect(() => {
    if (!polling || !jobId) return;

    const timer = setInterval(async () => {
      try {
        const st = await API.workflowStatus(jobId);
        updateOverlayStatus(st.current_node);
        if (st.status === 'completed') {
          clearInterval(timer);
          setPolling(false);
          toast.success('Blog ready. Opening…');
          schedule(() => navigateRef.current(`/viewer?id=${st.blog_id}`), 1000);
        }
        if (st.status === 'error') {
          clearInterval(timer);
          setPolling(false);
          setOverlayVisible(false);
          toast.error('Something went wrong. Please try again.');
        }
      } catch {}
    }, 3000);

    return () => clearInterval(timer);
  }, [polling, jobId, updateOverlayStatus, toast, schedule]);

  if (!jobId) return <Navigate to="/dashboard" replace />;

  function updateSection(idx, field, value) {
    setSections((prev) => prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)));
  }

  function addSection() {
    setSections((prev) => [...prev, { title: '', description: '', word_count: 300 }]);
  }

  function removeSection(idx) {
    setSections((prev) => prev.filter((_, i) => i !== idx));
  }

  async function submitApproval() {
    setSubmitting(true);
    const plan = {
      title: title.trim(),
      sections: sections.map((s) => ({
        title: s.title.trim(),
        description: s.description.trim(),
        word_count: parseInt(s.word_count || 300, 10),
      })),
      estimated_word_count: parseInt(wordCount || 1500, 10),
    };
    if (!plan.title) {
      toast.error('Please enter a blog title.');
      setSubmitting(false);
      return;
    }
    if (!plan.sections.length) {
      toast.error('Add at least one section.');
      setSubmitting(false);
      return;
    }
    try {
      await API.editPlan(jobId, plan);
      toast.success('Plan approved. Writing your blog…');
      showRunningOverlay('researcher');
      setPolling(true);
    } catch (err) {
      toast.error(err.message);
      setSubmitting(false);
    }
  }

  return (
    <PageShell skipHref="#plan-editor" skipLabel="Skip to outline">
      <Masthead />

      <main className="main-content">
        <div className="container" style={{ maxWidth: '52rem' }}>
          <section className="hero">
            <div className="hero-card">
              <p className="eyebrow">Step 2 of 2 — Review</p>
              <h1>Review the outline</h1>
              <p className="lead" style={{ marginTop: '8px' }}>Edit anything, then approve to start writing. <span id="plan-topic"></span></p>
            </div>
          </section>

          <section>
            {loadError ? (
              <div className="card" style={{ textAlign: 'center', padding: '64px' }}>
                <p>{loadError}</p>
              </div>
            ) : !planReady ? (
              <div className="card" style={{ textAlign: 'center', padding: '64px' }}>
                <span className="spinner" style={{ width: '32px', height: '32px' }} aria-hidden="true"></span>
                <p className="eyebrow" style={{ marginTop: '16px' }}>Loading outline…</p>
              </div>
            ) : (
              <>
                <div id="plan-editor">
                  {researchTasks.length > 0 && (
                    <div className="research-banner">
                      <strong>Web research enabled</strong> — the AI will search the web before writing.
                      <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {researchTasks.map((t, i) => (
                          <span key={i} className="research-task-chip">{t}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="plan-header">
                    <label htmlFor="plan-title">Blog title</label>
                    <input
                      type="text"
                      className="plan-title-input"
                      id="plan-title"
                      placeholder="Enter blog title…"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                    />
                    <div style={{ display: 'flex', gap: '20px', alignItems: 'end', flexWrap: 'wrap' }}>
                      <div>
                        <label htmlFor="word-count">Target word count</label>
                        <input
                          type="number"
                          id="word-count"
                          min={200}
                          max={10000}
                          step={100}
                          style={{ width: '150px' }}
                          value={wordCount}
                          onChange={(e) => setWordCount(e.target.value)}
                        />
                      </div>
                      <div id="section-count-display" className="eyebrow">
                        {`${sections.length} section${sections.length !== 1 ? 's' : ''}`}
                      </div>
                    </div>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '20px 4px 12px', flexWrap: 'wrap', gap: '8px' }}>
                      <h2>Sections</h2>
                      <button className="btn btn-secondary btn-sm" onClick={addSection}>+ Add section</button>
                    </div>
                    <div id="sections-list">
                      {sections.map((sec, idx) => (
                        <div className="section-card" key={idx}>
                          <div className="section-number">{idx + 1}</div>
                          <div className="section-body">
                            <input
                              type="text"
                              placeholder="Section title"
                              style={{ width: '100%' }}
                              value={sec.title}
                              onChange={(e) => updateSection(idx, 'title', e.target.value)}
                            />
                            <textarea
                              placeholder="What this section covers…"
                              style={{ width: '100%' }}
                              value={sec.description}
                              onChange={(e) => updateSection(idx, 'description', e.target.value)}
                            />
                            <div className="section-meta">
                              <label>Words:</label>
                              <input
                                type="number"
                                min={50}
                                max={3000}
                                step={50}
                                value={sec.word_count}
                                onChange={(e) => updateSection(idx, 'word_count', e.target.value)}
                              />
                              <button
                                onClick={() => removeSection(idx)}
                                className="btn btn-danger btn-sm"
                                style={{ marginLeft: 'auto' }}
                              >
                                Remove
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="action-bar" id="action-bar">
                  <Link to="/dashboard" className="btn btn-ghost">Cancel</Link>
                  <button
                    className="btn btn-primary"
                    id="approve-btn"
                    onClick={submitApproval}
                    disabled={submitting}
                  >
                    {submitting ? 'Submitting…' : 'Approve & write'}
                  </button>
                </div>
              </>
            )}
          </section>
        </div>
      </main>

      <div className={`workflow-overlay${overlayVisible ? ' visible' : ''}`} role="status" aria-live="polite">
        <div className="workflow-box">
          <div className="big-spinner" aria-hidden="true"></div>
          <h3 style={{ marginBottom: '8px' }}>{overlayTitle}</h3>
          <p className="eyebrow">{overlayStatus}</p>
          <div style={{ marginTop: '20px' }}>
            <div className="workflow-steps" style={{ justifyContent: 'center', flexWrap: 'wrap', gap: '12px' }}></div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
