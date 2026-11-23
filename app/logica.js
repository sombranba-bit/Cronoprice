/* Cronoprice · cálculos puros (sin DOM) para la app y para las pruebas con node. */
(function (root) {
  'use strict';
  const FRESH_DAYS = 14;

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const eur = (n) => (n == null ? '—' : n.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €');
  // Precio de una oferta: si la moneda no es EUR, se muestra el importe con una etiqueta de moneda (p. ej. GBP)
  const pr = (v) => (v.moneda && v.moneda !== 'EUR'
    ? `${v.p.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span class="pill" title="Precio en ${v.moneda}, no convertido">${v.moneda}</span>`
    : eur(v.p));

  // Solo EUR entra en el mejor precio y en la dispersión: no se mezclan monedas sin convertir
  const fresh = (item, now = Date.now()) => Object.entries(item.prices || {})
    .filter(([, v]) => v && v.p && v.stock !== false && (!v.moneda || v.moneda === 'EUR') && (now - new Date(v.d).getTime()) / 864e5 <= FRESH_DAYS)
    .map(([s, v]) => ({ s, ...v }));
  const best = (item, now) => fresh(item, now).sort((a, b) => a.p - b.p)[0] || null;
  const spread = (item, now) => { const f = fresh(item, now); return f.length > 1 ? Math.max(...f.map((x) => x.p)) - Math.min(...f.map((x) => x.p)) : 0; };

  // Bajada frente a la media de los últimos 30 días del historial (solo EUR)
  const drop = (item, now = Date.now()) => {
    const b = best(item, now); if (!b) return null;
    const cut = now - 30 * 864e5;
    const vals = (item.history || []).filter((h) => !h.moneda || h.moneda === 'EUR').filter((h) => new Date(h.d).getTime() >= cut).map((h) => h.p);
    if (vals.length < 3) return null;
    const avg = vals.reduce((a, c) => a + c, 0) / vals.length;
    return { pct: (b.p - avg) / avg, avg };
  };

  const api = { FRESH_DAYS, esc, eur, pr, fresh, best, spread, drop };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.CronoLogica = api;
})(typeof window !== 'undefined' ? window : globalThis);
