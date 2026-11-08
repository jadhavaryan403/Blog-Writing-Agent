/**
 * src/lib/utils.js
 * ────────────────
 * Shared display helpers: formatting, markdown rendering.
 */

import { marked } from 'marked';

export function formatCost(n) {
  return n < 0.01 ? '<$0.01' : `$${n.toFixed(4)}`;
}

export function formatTokens(n) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

export function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Editorial Markdown Renderer (marked + monochrome post-process) ────────────
export function renderMarkdown(md) {
  const src = String(md || '');
  try {
    if (typeof marked.parse === 'function') return marked.parse(src);
    if (typeof marked === 'function') return marked(src);
  } catch {}
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
