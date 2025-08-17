export const fmt = {
  price: (n) => (n == null ? "-" : Number(n).toFixed(2)),
  pct:   (n) => (n == null ? "-" : `${Number(n).toFixed(2)}%`),
  date:  (iso) => new Date(iso).toLocaleString(),
};

export function clamp01(x){ return Math.max(0, Math.min(1, x)); }
export function qs(sel, el=document){ return el.querySelector(sel); }
export function qsa(sel, el=document){ return Array.from(el.querySelectorAll(sel)); }
