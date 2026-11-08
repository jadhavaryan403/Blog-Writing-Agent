/**
 * src/lib/hooks.js
 * ────────────────
 * Small shared hooks.
 */

import { useEffect, useRef } from 'react';

/**
 * Schedule one-shot timeouts that are automatically cleared on unmount,
 * mirroring how page-level setTimeout calls died with the old HTML pages.
 * Returns a stable function so it is safe in effect dependency arrays.
 */
export function useTimeouts() {
  const timers = useRef([]);
  const scheduleRef = useRef(null);

  if (!scheduleRef.current) {
    scheduleRef.current = (fn, ms) => {
      const id = setTimeout(fn, ms);
      timers.current.push(id);
      return id;
    };
  }

  useEffect(() => {
    const list = timers.current;
    return () => list.forEach(clearTimeout);
  }, []);

  return scheduleRef.current;
}
