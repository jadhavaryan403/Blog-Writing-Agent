/**
 * src/pages/Settings.jsx
 * ──────────────────────
 * Default writing preferences (old frontend/pages/settings.html).
 */

import { useEffect, useState } from 'react';

import { API } from '../lib/api.js';
import { formatDate } from '../lib/utils.js';
import { useToast } from '../components/ToastProvider.jsx';
import { useTimeouts } from '../lib/hooks.js';
import Masthead from '../components/Masthead.jsx';
import PageShell from '../components/PageShell.jsx';

const DEFAULTS = {
  preferred_tone:       'professional',
  preferred_style:      'informative',
  technical_depth:      'intermediate',
  preferred_language:   'English',
  preferred_word_count: 1500,
};

const LABELS = {
  preferred_tone:       { label: 'Tone',     fn: (v) => String(v).charAt(0).toUpperCase() + String(v).slice(1) },
  preferred_style:      { label: 'Style',    fn: (v) => String(v).charAt(0).toUpperCase() + String(v).slice(1) },
  technical_depth:      { label: 'Depth',    fn: (v) => String(v).charAt(0).toUpperCase() + String(v).slice(1) },
  preferred_language:   { label: 'Language', fn: (v) => v },
  preferred_word_count: { label: 'Words',    fn: (v) => Number(v).toLocaleString() },
};

export default function Settings() {
  const toast = useToast();
  const schedule = useTimeouts();

  // The form renders immediately with defaults (old loadPrefs behaviour) so
  // the page can never get stuck on "Loading…"; server values upgrade it.
  const [prefs, setPrefs] = useState(DEFAULTS);
  const [tone, setTone] = useState(DEFAULTS.preferred_tone);
  const [style, setStyle] = useState(DEFAULTS.preferred_style);
  const [depth, setDepth] = useState(DEFAULTS.technical_depth);
  const [language, setLanguage] = useState(DEFAULTS.preferred_language);
  const [wordCount, setWordCount] = useState(String(DEFAULTS.preferred_word_count));
  const [updatedAt, setUpdatedAt] = useState(null);
  const [saveStatus, setSaveStatus] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    document.title = 'Settings — BlogAI';
  }, []);

  // Apply a preferences object to the form (old populateForm).
  function applyPrefs(p) {
    p = p || {};
    const rawDepth = String(p.technical_depth || 'intermediate').split(' ')[0].toLowerCase();
    setTone(p.preferred_tone || DEFAULTS.preferred_tone);
    setDepth(rawDepth);
    setLanguage(p.preferred_language || DEFAULTS.preferred_language);

    // Match the stored style to an option case-insensitively; keep the
    // current value when nothing matches (same as the old select loop).
    const styleVal = String(p.preferred_style || DEFAULTS.preferred_style).toLowerCase();
    const options = ['informative', 'tutorial', 'opinion', 'listicle', 'deep-dive', 'news'];
    const matched = options.find((o) => o.toLowerCase() === styleVal);
    if (matched) setStyle(matched);

    setWordCount(String(p.preferred_word_count || DEFAULTS.preferred_word_count));
    if (p.updated_at) setUpdatedAt(p.updated_at);
  }

  useEffect(() => {
    (async () => {
      try {
        const p = await API.getPrefs();
        if (p && typeof p === 'object') {
          applyPrefs(p);
          setPrefs(p);
        }
      } catch {
        setSaveStatus('Could not load saved settings');
        toast.error('Failed to load settings');
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function savePrefs(e) {
    e.preventDefault();
    setSaving(true);
    setSaveStatus('');
    const payload = {
      preferred_tone:       tone,
      preferred_style:      style,
      technical_depth:      depth,
      preferred_language:   language,
      preferred_word_count: parseInt(wordCount, 10),
    };
    try {
      const updated = await API.updatePrefs(payload);
      applyPrefs(updated);
      setPrefs(updated);
      setSavedFlash(true);
      schedule(() => setSavedFlash(false), 1200);
      setSaveStatus('Saved');
      toast.success('Settings saved.');
      schedule(() => setSaveStatus(''), 4000);
    } catch (err) {
      setSaveStatus('Save failed');
      toast.error('Save failed: ' + err.message);
    } finally {
      setSaving(false);
    }
  }

  function resetToDefaults() {
    applyPrefs(DEFAULTS);
    setSaveStatus('Defaults loaded — press Save.');
  }

  const wcBadge = Number(wordCount).toLocaleString() + ' words';

  return (
    <PageShell skipHref="#prefs-form" skipLabel="Skip to settings">
      <Masthead />

      <main className="main-content">
        <div className="container" style={{ maxWidth: '48rem' }}>
          <section className="hero">
            <div className="hero-card">
              <p className="eyebrow">Defaults for every blog</p>
              <h1>Writing settings</h1>
            </div>
          </section>

          <section>
            <div id="pref-summary-wrap" style={{ display: 'block' }}>
              <div className="pref-summary" id="pref-summary">
                {Object.entries(LABELS).map(([key, meta]) => {
                  const val = prefs[key] ?? DEFAULTS[key];
                  return (
                    <div key={key} className="pref-chip">
                      <span className="pref-chip-key">{meta.label}</span>
                      <span className="pref-chip-val">{meta.fn(val)}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className={`card lift${savedFlash ? ' saved-flash' : ''}`} id="prefs-card">
              <form id="prefs-form" onSubmit={savePrefs}>
                <div className="settings-grid">
                  <div className="form-group">
                    <label htmlFor="tone">Tone</label>
                    <select id="tone" value={tone} onChange={(e) => setTone(e.target.value)}>
                      <option value="professional">Professional</option>
                      <option value="conversational">Conversational</option>
                      <option value="technical">Technical</option>
                      <option value="casual">Casual</option>
                      <option value="persuasive">Persuasive</option>
                      <option value="academic">Academic</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="style">Style</label>
                    <select id="style" value={style} onChange={(e) => setStyle(e.target.value)}>
                      <option value="informative">Informative</option>
                      <option value="tutorial">Tutorial / How-To</option>
                      <option value="opinion">Opinion Piece</option>
                      <option value="listicle">Listicle</option>
                      <option value="deep-dive">Deep Dive</option>
                      <option value="news">News / Journalistic</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="depth">Technical depth</label>
                    <select id="depth" value={depth} onChange={(e) => setDepth(e.target.value)}>
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                      <option value="expert">Expert</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="language">Language</label>
                    <select id="language" value={language} onChange={(e) => setLanguage(e.target.value)}>
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
                </div>

                <div className="form-group" style={{ marginTop: '4px' }}>
                  <label htmlFor="word-count">Default length <span id="wc-badge" className="wc-badge" style={{ marginLeft: '10px', verticalAlign: 'middle' }}>{wcBadge}</span></label>
                  <div className="wc-track">
                    <input
                      type="range"
                      id="word-count"
                      min={500}
                      max={5000}
                      step={100}
                      value={wordCount}
                      onChange={(e) => setWordCount(e.target.value)}
                    />
                    <div className="wc-labels">
                      <span className="eyebrow">500</span>
                      <span className="eyebrow">5000</span>
                    </div>
                  </div>
                </div>

                <hr className="divider-soft" />

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <button type="submit" className="btn btn-primary" id="save-btn" disabled={saving}>
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                  <button type="button" className="btn btn-secondary" onClick={resetToDefaults}>Reset</button>
                  <div id="save-status" className="eyebrow" style={{ marginLeft: 'auto' }}>{saveStatus}</div>
                </div>

                {updatedAt && (
                  <div className="updated-line" style={{ display: 'flex' }}>
                    <span className="updated-dot" aria-hidden="true"></span>
                    Saved{'\u00A0'}<span>{formatDate(updatedAt)}</span>
                  </div>
                )}
              </form>
            </div>
          </section>
        </div>
      </main>
    </PageShell>
  );
}
