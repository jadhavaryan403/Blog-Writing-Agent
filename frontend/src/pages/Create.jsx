/**
 * src/pages/Create.jsx
 * ────────────────────
 * "New blog" form — step 1 (old frontend/pages/create.html).
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { API } from '../lib/api.js';
import { useToast } from '../components/ToastProvider.jsx';
import { useTimeouts } from '../lib/hooks.js';
import Masthead from '../components/Masthead.jsx';
import PageShell from '../components/PageShell.jsx';

const EXAMPLE_TOPICS = [
  'LangGraph multi-agent systems',
  'Climate tech innovations 2026',
  'Rust vs Go for backend services',
];

export default function Create() {
  const navigate = useNavigate();
  const toast = useToast();
  const schedule = useTimeouts();
  const topicRef = useRef(null);

  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('');
  const [style, setStyle] = useState('');
  const [depth, setDepth] = useState('');
  const [language, setLanguage] = useState('');
  const [wordCount, setWordCount] = useState('1500');
  const [wcBadge, setWcBadge] = useState('1500 words');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    document.title = 'New blog — BlogAI';
  
    (async () => {
      try {
        const prefs = await API.getPrefs();
  
        if (prefs && typeof prefs === 'object') {
          setTone(prefs.preferred_tone || '');
          setStyle(prefs.preferred_style || '');
          setDepth(
            String(prefs.technical_depth || '')
              .split(' ')[0]
              .toLowerCase()
          );
          setLanguage(prefs.preferred_language || '');
          
          const savedWordCount = Number(prefs.preferred_word_count);
          if (savedWordCount) {
            setWordCount(String(savedWordCount));
            setWcBadge(savedWordCount.toLocaleString() + ' words');
          }
        }
      } catch (err) {
        console.error('Failed to load saved preferences:', err);
      }
    })();
  }, []);

  function pickExample(text) {
    setTopic(text);
    if (topicRef.current) topicRef.current.focus();
  }

  function onWcChange(val) {
    setWordCount(val);
    setWcBadge(Number(val).toLocaleString() + ' words');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = topic.trim();
    if (!trimmed) {
      toast.error('Please enter a topic.');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        topic: trimmed,
        tone: tone || null,
        style: style || null,
        technical_depth: depth || null,
        language: language || null,
        word_count: Number(wordCount) || null,
      };
      const result = await API.startWorkflow(payload);
      toast.success('Outline ready. Opening review…');
      schedule(() => {
        navigate(`/approval?job_id=${result.job_id}&blog_id=${result.blog_id}`);
      }, 800);
    } catch (err) {
      const detail = err && err.message ? err.message : String(err);
      toast.error(detail);
      setSubmitting(false);
    }
  }

  return (
    <PageShell skipHref="#create-form" skipLabel="Skip to form">
      <Masthead />

      <main className="main-content">
        <div className="container" style={{ maxWidth: '46rem' }}>
          <section className="hero">
            <div className="hero-card">
              <p className="eyebrow">Step 1 of 2 — Describe</p>
              <h1>What should we write about?</h1>
            </div>
          </section>

          <section>
            <div className="card lift">
              <form id="create-form" onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="topic">Blog topic</label>
                  <textarea
                    id="topic"
                    ref={topicRef}
                    rows={2}
                    placeholder="e.g. The future of multi-agent AI systems…"
                    required
                    minLength={3}
                    maxLength={100}
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                  />
                  <div className="topic-examples" aria-label="Example topics">
                    {EXAMPLE_TOPICS.map((text) => (
                      <span key={text} className="example-chip" onClick={() => pickExample(text)}>{text}</span>
                    ))}
                  </div>
                </div>

                <hr className="divider-soft" />

                <details style={{ marginBottom: '20px' }}>
                  <summary>Writing preferences (optional — defaults come from Settings)</summary>
                  <div className="pref-row" style={{ marginTop: '12px' }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label htmlFor="tone">Tone</label>
                      <select id="tone" value={tone} onChange={(e) => setTone(e.target.value)}>
                        <option value="">Use default</option>
                        <option value="professional">Professional</option>
                        <option value="conversational">Conversational</option>
                        <option value="technical">Technical</option>
                        <option value="casual">Casual</option>
                        <option value="persuasive">Persuasive</option>
                      </select>
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label htmlFor="style">Style</label>
                      <select id="style" value={style} onChange={(e) => setStyle(e.target.value)}>
                        <option value="">Use default</option>
                        <option value="informative">Informative</option>
                        <option value="tutorial">Tutorial / How-To</option>
                        <option value="opinion">Opinion Piece</option>
                        <option value="listicle">Listicle</option>
                        <option value="deep-dive">Deep Dive</option>
                        <option value="news">News / Journalistic</option>
                      </select>
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label htmlFor="depth">Technical depth</label>
                      <select id="depth" value={depth} onChange={(e) => setDepth(e.target.value)}>
                        <option value="">Use default</option>
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                        <option value="expert">Expert</option>
                      </select>
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label htmlFor="language">Language</label>
                      <select id="language" value={language} onChange={(e) => setLanguage(e.target.value)}>
                        <option value="">Use default</option>
                        <option value="English">English</option>
                        <option value="Spanish">Spanish</option>
                        <option value="French">French</option>
                        <option value="German">German</option>
                        <option value="Portuguese">Portuguese</option>
                        <option value="Japanese">Japanese</option>
                        <option value="Hindi">Hindi</option>
                        <option value="Arabic">Arabic</option>
                        <option value="Korean">Korean</option>
                      </select>
                    </div>
                    <div className="form-group" style={{ marginTop: '4px', gridColumn: '1/-1' }}>
                      <label htmlFor="word-count">Target length <span id="wc-badge" className="wc-badge" style={{ marginLeft: '10px', verticalAlign: 'middle' }}>{wcBadge}</span></label>
                      <div className="wc-track">
                        <input
                          type="range"
                          id="word-count"
                          min={500}
                          max={5000}
                          step={100}
                          value={wordCount}
                          onChange={(e) => onWcChange(e.target.value)}
                        />
                        <div className="wc-labels">
                          <span className="eyebrow">500</span>
                          <span className="eyebrow">5000</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </details>

                <button
                  type="submit"
                  className="btn btn-primary btn-lg"
                  style={{ width: '100%', justifyContent: 'center' }}
                  id="submit-btn"
                  disabled={submitting}
                >
                  {submitting ? 'Generating outline…' : 'Generate outline'}
                </button>
              </form>
            </div>
          </section>
        </div>
      </main>
    </PageShell>
  );
}
