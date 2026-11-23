// Pruebas de los cálculos de la app. Se ejecutan con: node app/test_logica.js
'use strict';
const assert = require('node:assert/strict');
const L = require('./logica.js');

const NOW = Date.parse('2026-11-23T12:00:00Z');
const dia = (n) => new Date(NOW - n * 864e5).toISOString().slice(0, 10);

// esc: escapa HTML
assert.equal(L.esc('<a href="x">&\'</a>'), '&lt;a href=&quot;x&quot;&gt;&amp;&#39;&lt;/a&gt;');
assert.equal(L.esc(null), '');

// eur: formato español con dos decimales
assert.equal(L.eur(12345.5), '12.345,50 €'); // es-ES no agrupa miles de cuatro cifras
assert.equal(L.eur(null), '—');

// pr: EUR sin etiqueta; otras monedas con etiqueta
assert.equal(L.pr({ p: 10 }), '10,00 €');
assert.match(L.pr({ p: 10, moneda: 'GBP' }), /GBP<\/span>$/);

// fresh: solo EUR, sin agotados y sin ofertas viejas
const item = {
  prices: {
    a: { p: 100, d: dia(1) },
    b: { p: 90, d: dia(2), moneda: 'EUR' },
    c: { p: 50, d: dia(1), moneda: 'GBP' },          // otra moneda: fuera
    d: { p: 80, d: dia(1), stock: false },           // agotado: fuera
    e: { p: 70, d: dia(30) },                        // demasiado antiguo: fuera
  },
};
const f = L.fresh(item, NOW);
assert.deepEqual(f.map((x) => x.s).sort(), ['a', 'b']);

// best: el más barato entre los frescos EUR
assert.equal(L.best(item, NOW).s, 'b');
assert.equal(L.best({ prices: {} }, NOW), null);

// spread: diferencia entre el más caro y el más barato frescos EUR
assert.equal(L.spread(item, NOW), 10);
assert.equal(L.spread({ prices: { a: { p: 5, d: dia(1) } } }, NOW), 0);

// drop: compara con la media de 30 días; ignora historial en otras monedas
const hist = [
  { d: dia(1), p: 100 }, { d: dia(5), p: 100 }, { d: dia(10), p: 100 },
  { d: dia(3), p: 1, moneda: 'GBP' },              // no cuenta
];
const bajada = L.drop({ prices: { a: { p: 80, d: dia(1) } }, history: hist }, NOW);
assert.ok(bajada, 'debería haber bajada');
assert.ok(Math.abs(bajada.pct - (-0.2)) < 1e-9, String(bajada.pct));
assert.equal(L.drop({ prices: { a: { p: 80, d: dia(1) } }, history: hist.slice(0, 2) }, NOW), null, 'menos de 3 datos');

// Los datos reales del repositorio se pueden calcular sin errores
const fs = require('node:fs');
const path = require('node:path');
const relojes = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'relojes.json'), 'utf-8'));
for (const r of relojes) {
  L.best(r);
  L.spread(r);
  L.drop(r);
}

console.log('logica: todas las pruebas pasan');
