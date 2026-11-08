/**
 * src/pages/Viewer.jsx
 * ────────────────────
 * Blog reader with sections nav, raw toggle, and AI section editing
 * (old frontend/pages/viewer.html).
 */

import { useEffect, useRef, useState } from 'react';
import { Link, Navigate, useSearchParams } from 'react-router-dom';

import { API } from '../lib/api.js';
import { formatDate, renderMarkdown } from '../lib/utils.js';
import { useToast } from '../components/ToastProvider.jsx';
import { useTimeouts } from '../lib/hooks.js';
import Masthead from '../components/Masthead.jsx';
import PageShell from '../components/PageShell.jsx';
import StatusBadge from '../components/StatusBadge.jsx';

const SUGGESTIONS = [
  'Make more technical',
  'Simplify for beginners',
  'Add examples',
  'Make it more concise',
  'Add more detail',
];

export default function Viewer() {
  const [searchParams] = useSearchParams();
  const blogId = searchParams.get('id');
  const toast = useToast();
  const schedule = useTimeouts();

  const markdownRef = useRef(null);
  const instructionRef = useRef(null);

  const [blog, setBlog] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [rawMarkdown, setRawMarkdown] = useState('');
  const [sections, setSections] = useState([]);
  const [tokens, setTokens] = useState(0);
  const [showingRaw, setShowingRaw] = useState(false);
  const [activeSectionId, setActiveSectionId] = useState(null);
  const [version, setVersion] = useState(null);
  const [banner, setBanner] = useState({ visible: false, text: 'Section updated.' });

  const [editModalVisible, setEditModalVisible] = useState(false);
  const [activeEdit, setActiveEdit] = useState(null);
  const [instruction, setInstruction] = useState('');
  const [modalSubmitting, setModalSubmitting] = useState(false);

  useEffect(() => {
    document.title = 'Blog — BlogAI';
  }, []);

  // ── Load blog + sections + tokens ──────────────────────────────────────────
  useEffect(() => {
    if (!blogId) return;
    let alive = true;

    (async () => {
      try {
        const [b, secs, tok] = await Promise.all([
          API.getBlog(blogId),
          API.getSections(blogId).catch(() => []),
          API.getBlogTokens(blogId),
        ]);
        if (!alive) return;
        setBlog(b);
        setSections(secs);
        setRawMarkdown(b.final_content || '');
        setTokens(tok);
        document.title = (b.title || 'Blog') + ' — BlogAI';
      } catch (err) {
        if (alive) setLoadError(err.message);
      }
    })();

    return () => { alive = false; };
  }, [blogId]);

  // ── Escape closes the edit modal (old document keydown listener) ──────────
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') closeModal();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  if (!blogId) return <Navigate to="/dashboard" replace />;

  function closeModal() {
    setEditModalVisible(false);
    setModalSubmitting(false);
  }

  function handleBackdropClick(e) {
    if (e.target === e.currentTarget) closeModal();
  }

  function scrollToSection(idx, sectionId) {
    setActiveSectionId(sectionId);
    const container = markdownRef.current;
    if (!container) return;
    const headings = container.querySelectorAll('h2');
    if (headings[idx]) {
      headings[idx].scrollIntoView({ behavior: 'smooth', block: 'start' });
      headings[idx].classList.add('section-highlight');
      const el = headings[idx];
      schedule(() => el.classList.remove('section-highlight'), 1000);
    }
  }

  function toggleRaw() {
    setShowingRaw((v) => !v);
  }

  function copyMarkdown() {
    if (!rawMarkdown) {
      toast.error('No content to copy.');
      return;
    }
    navigator.clipboard.writeText(rawMarkdown)
      .then(() => toast.success('Copied to clipboard.'))
      .catch(() => toast.error('Copy failed'));
  }

  function openEditModal(sectionId, title, idx) {
    setActiveEdit({ section_id: sectionId, title, idx });
    setInstruction('');
    setEditModalVisible(true);
    setActiveSectionId(sectionId);
    if (instructionRef.current) instructionRef.current.focus();
  }

  function useChip(text) {
    const current = instruction.trim();
    setInstruction(current ? current + '. ' + text : text);
    if (instructionRef.current) instructionRef.current.focus();
  }

  function extractSectionText(idx) {
    const blocks = rawMarkdown.split(/^## /m);
    if (blocks[idx + 1]) {
      return blocks[idx + 1]
        .replace(/^.+\n/, '')
        .replace(/!\[[^\]]*\]\((.*?)\)/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/[*_`#]/g, '')
        .slice(0, 400)
        .trim();
    }
    return '';
  }

  async function submitEdit() {
    const trimmed = instruction.trim();
    if (!trimmed) {
      toast.error('Please enter an instruction.');
      return;
    }
    if (!activeEdit) return;
    setModalSubmitting(true);
    try {
      const result = await API.editSection(blogId, {
        section_id: activeEdit.section_id,
        instruction: trimmed,
      });
      closeModal();
      setRawMarkdown(result.updated_blog);
      setVersion(result.version);
      setBanner({
        visible: true,
        text: `"${result.section_title}" updated (version ${result.version}).`,
      });
      schedule(() => setBanner((b) => ({ ...b, visible: false })), 5000);
      const sectionId = activeEdit.section_id;
      schedule(() => scrollToSection(result.section_idx, sectionId), 150);
      toast.success('Section updated.');
    } catch (err) {
      toast.error(err.message || 'Edit failed');
      setModalSubmitting(false);
    }
  }

  // ── Loading / error states ─────────────────────────────────────────────────
  const loadingState = loadError ? (
    <div className="card" style={{ textAlign: 'center', padding: '64px' }}>
      <p>{loadError}</p>
    </div>
  ) : !blog ? (
    <div id="loading" className="card" style={{ textAlign: 'center', padding: '64px' }}>
      <span className="spinner" style={{ width: '32px', height: '32px' }} aria-hidden="true"></span>
      <p className="eyebrow" style={{ marginTop: '12px' }}>Loading blog…</p>
    </div>
  ) : null;

  const tokensLabel = typeof tokens === 'number' ? tokens.toLocaleString() : String(tokens);

  return (
    <PageShell skipHref="#markdown-view" skipLabel="Skip to blog">
      <Masthead />

      <main className="main-content">
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '8px 0 20px', flexWrap: 'wrap' }}>
            <Link to="/dashboard" className="btn btn-secondary btn-sm">← Back</Link>
            <div id="blog-status-badge">{blog && <StatusBadge status={blog.status} />}</div>
            {version !== null && (
              <div id="version-badge" style={{ display: 'flex' }}>
                <span className="version-tag">v{version}</span>
              </div>
            )}
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button className="btn btn-secondary btn-sm" onClick={copyMarkdown}>Copy text</button>
              <button className="btn btn-secondary btn-sm" id="raw-toggle-btn" onClick={toggleRaw}>
                {showingRaw ? 'View formatted' : 'View raw'}
              </button>
            </div>
          </div>

          {loadingState}

          <div className={`edit-result-banner${banner.visible ? ' visible' : ''}`}>
            <span aria-hidden="true">✓</span>
            <span>{banner.text}</span>
          </div>

          {blog && (
            <div id="content">
              <div className="viewer-layout">
                <div className="sections-panel">
                  <div className="card" style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <h4 className="eyebrow">Sections</h4>
                      <span id="section-count" className="eyebrow">{sections.length}</span>
                    </div>
                    <div id="sections-nav">
                      {sections.length === 0 ? (
                        <p className="eyebrow" style={{ textAlign: 'center', padding: '16px' }}>No sections</p>
                      ) : (
                        sections.map((sec, i) => (
                          <div
                            key={sec.section_id}
                            id={`nav-item-${sec.section_id}`}
                            className={`section-nav-item${activeSectionId === sec.section_id ? ' active' : ''}`}
                            onClick={() => scrollToSection(i, sec.section_id)}
                          >
                            <div className="section-idx-pill">{i + 1}</div>
                            <div className="section-nav-title" title={sec.title}>{sec.title}</div>
                            <button
                              className="edit-btn"
                              title="Edit this section"
                              onClick={(e) => {
                                e.stopPropagation();
                                openEditModal(sec.section_id, sec.title, i);
                              }}
                            >
                              Edit
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  <div className="card" style={{ padding: '20px', marginTop: '16px' }}>
                    <h4 className="eyebrow" style={{ marginBottom: '8px' }}>Details</h4>
                    <div id="meta-rows">
                      <div className="meta-row"><span className="meta-key">Status</span><span className="meta-val"><StatusBadge status={blog.status} /></span></div>
                      <div className="meta-row"><span className="meta-key">Topic</span><span className="meta-val" style={{ fontSize: '.82rem', maxWidth: '140px', wordBreak: 'break-word' }}>{blog.topic}</span></div>
                      <div className="meta-row"><span className="meta-key">Created</span><span className="meta-val">{formatDate(blog.created_at)}</span></div>
                      <div className="meta-row"><span className="meta-key">Tokens</span><span className="meta-val">{tokensLabel}</span></div>
                    </div>
                  </div>
                </div>

                <div className="blog-panel">
                  <div className="card" style={{ padding: '36px 32px' }}>
                    <div
                      id="markdown-view"
                      className="markdown-body"
                      ref={markdownRef}
                      style={{ display: showingRaw ? 'none' : 'block' }}
                      dangerouslySetInnerHTML={{ __html: rawMarkdown ? renderMarkdown(rawMarkdown) : '<p>No content yet.</p>' }}
                    />
                    <pre
                      id="raw-view"
                      style={{
                        display: showingRaw ? 'block' : 'none',
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'inherit',
                        fontSize: '.9rem',
                        color: '#4c4753',
                        lineHeight: '1.7',
                      }}
                    >{rawMarkdown}</pre>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Edit section modal — always mounted, .visible toggles the CSS transition */}
      <div className={`modal-backdrop${editModalVisible ? ' visible' : ''}`} onClick={handleBackdropClick}>
        <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="modal-header">
            <div>
              <h3 id="modal-title" style={{ marginBottom: '6px' }}>Edit section</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  id="modal-section-idx"
                  style={{
                    background: 'linear-gradient(135deg,#A78BFA,#7C3AED)',
                    color: '#fff',
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '.8rem',
                    fontWeight: '800',
                    fontFamily: 'var(--font-display)',
                  }}
                >
                  {activeEdit ? activeEdit.idx + 1 : ''}
                </span>
                <span id="modal-section-name" style={{ fontWeight: '700' }}>{activeEdit ? activeEdit.title : ''}</span>
              </div>
            </div>
            <button className="modal-close" onClick={closeModal} aria-label="Close">✕</button>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <div className="eyebrow" style={{ marginBottom: '6px' }}>Current content</div>
            <div className="section-preview" id="modal-preview">
              {activeEdit ? (extractSectionText(activeEdit.idx) || '(no content yet)') : ''}
            </div>
          </div>

          <div className="eyebrow" style={{ marginBottom: '6px' }}>Suggestions — tap to add</div>
          <div className="suggestion-chips">
            {SUGGESTIONS.map((text) => (
              <button key={text} className="chip" onClick={() => useChip(text)}>{text}</button>
            ))}
          </div>

          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label htmlFor="edit-instruction">Your instruction</label>
            <textarea
              id="edit-instruction"
              ref={instructionRef}
              rows={3}
              maxLength={1000}
              placeholder="e.g. Make this section more technical with examples."
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
              <span id="char-count" className="eyebrow">{instruction.length} / 1000</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
            <button className="btn btn-ghost" onClick={closeModal}>Cancel</button>
            <button
              className="btn btn-primary"
              id="submit-edit-btn"
              onClick={submitEdit}
              disabled={modalSubmitting}
            >
              {modalSubmitting ? 'Applying…' : 'Apply edit'}
            </button>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
