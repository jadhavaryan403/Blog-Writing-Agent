/**
 * src/components/ToastProvider.jsx
 * ────────────────────────────────
 * Toast notifications (monochrome, instant) — React port of the old
 * DOM-based Toast helper. The container keeps the same #toast-container
 * id so the existing CSS applies unchanged.
 */

import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';

const ICONS = { success: '✓', error: '✕', info: '§' };

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const show = useCallback((message, type = 'info', duration = 4000) => {
    const id = ++idRef.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const value = useMemo(() => ({
    show,
    success: (msg) => show(msg, 'success'),
    error:   (msg) => show(msg, 'error'),
    info:    (msg) => show(msg, 'info'),
  }), [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div id="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.type}`} role="status">
            <span aria-hidden="true">{ICONS[t.type] || ICONS.info}</span>
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within a ToastProvider');
  return ctx;
}
