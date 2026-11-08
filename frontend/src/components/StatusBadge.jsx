/**
 * src/components/StatusBadge.jsx
 * ──────────────────────────────
 * Workflow status pill — port of the old statusBadge() helper.
 */

const BADGE_CLASSES = {
  pending: 'badge-pending',
  planning: 'badge-planning',
  running: 'badge-running',
  awaiting_approval: 'badge-awaiting',
  completed: 'badge-completed',
  error: 'badge-error',
};

export default function StatusBadge({ status }) {
  const cls = BADGE_CLASSES[status] || 'badge-pending';
  const label = String(status || 'pending').replace(/_/g, ' ');
  return <span className={`badge ${cls}`}>{label}</span>;
}
