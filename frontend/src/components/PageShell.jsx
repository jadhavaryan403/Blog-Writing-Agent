/**
 * src/components/PageShell.jsx
 * ────────────────────────────
 * The chrome shared by every page: skip link + floating clay blobs.
 */

export default function PageShell({ skipHref, skipLabel, children }) {
  return (
    <>
      <a className="skip-link" href={skipHref}>{skipLabel}</a>
      <div className="clay-blobs" aria-hidden="true">
        <div className="clay-blob clay-blob-1"></div>
        <div className="clay-blob clay-blob-2"></div>
        <div className="clay-blob clay-blob-3"></div>
      </div>
      {children}
    </>
  );
}
