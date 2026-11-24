/* Cronoprice · vistas, filtros y cálculos. Sin frameworks; todo el texto de las tiendas pasa por esc(). */
(() => {
  'use strict';
  const DATA = 'data/';
  const ICON_WATCH = (n = 96) => `<svg width="${n}" height="${n}" viewBox="0 0 96 96" aria-hidden="true"><rect x="30" y="18" width="36" height="60" rx="8" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="48" cy="48" r="16" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M48 38v10l7 4" stroke="var(--accent)" stroke-width="2" fill="none" stroke-linecap="round"/></svg>`;
  const $ = (s) => document.querySelector(s);
  const main = $('#main');
  const SHOPS = { idealo: 'Idealo', oficial: 'Tienda oficial', distribuidor: 'Distribuidor', eci: 'El Corte Inglés', amazon: 'Amazon' };
  const shopName = (s) => SHOPS[s] || s;
  const store = (k) => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch { return null; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} };
  const favs = () => store('cp-favs') || [];
  const targets = () => store('cp-targets') || {};
  const ago = (d) => { const days = Math.floor((Date.now() - new Date(d).getTime()) / 864e5); return days <= 0 ? 'hoy' : days === 1 ? 'ayer' : `hace ${days} días`; };

  // ---------------------------------------------------------------- datos y cálculos
  let relojes = [], chollos = [];
  const { FRESH_DAYS, esc, eur, pr, fresh, best, spread, drop } = window.CronoLogica;
  const shownName = (i) => `${i.brand} ${i.name}`;

  // ---------------------------------------------------------------- piezas de interfaz
  const card = (i) => {
    const b = best(i), d = drop(i), sp = spread(i);
    const img = Object.values(i.images || {})[0];
    return `<a class="card" href="#r/${esc(i.id)}">
      <div class="plate">${img ? `<img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ICON_WATCH(56)}
        ${d && d.pct < -0.02 ? `<span class="badge">${Math.round(d.pct * 100)} %</span>` : ''}</div>
      <div class="meta"><span class="dot"></span>${esc(i.brand)} · ${esc(i.tipo || '')}${i.caja_mm ? ' · ' + i.caja_mm + ' mm' : ''}</div>
      <div class="name">${esc(i.name)}</div>
      <div class="price"${!b && i.sin_precio_motivo ? ` title="${esc(i.sin_precio_motivo)}"` : ''}>${b ? eur(b.p) : 'Sin precio'}</div>
      ${sp > 0 ? `<span class="pill">${eur(sp)} entre tiendas</span>` : ''}
      ${b ? `<div class="meta">en ${esc(shopName(b.s))}${b.via ? ' · vía ' + esc(shopName(b.via)) : ''}</div>` : ''}
    </a>`;
  };
  const row = (c) => `<a class="row" href="${esc(c.url)}" target="_blank" rel="noopener">
    <div class="plate">${ICON_WATCH(40)}</div>
    <div><div class="rname">${esc(c.t)}</div><div class="rmeta">${esc(c.shop || 'Chollometro')}${c.expired ? ' · caducado' : ''}</div></div>
    <div class="rright"><b>${c.p != null ? eur(c.p) : ''}</b></div></a>`;
  const section = (title, sub, body) => `<div class="sec-h"><h2>${title}</h2><span>${esc(sub || '')}</span></div>${body}`;

  // ---------------------------------------------------------------- vistas
  function home() {
    const top = [...relojes].filter((i) => best(i)).sort((a, b) => (drop(a)?.pct ?? 0) - (drop(b)?.pct ?? 0)).slice(0, 4);
    const saved = favs().map((id) => relojes.find((i) => i.id === id)).filter(Boolean);
    return `<section class="hero">
      <h1>Encuentra tu reloj <em>al mejor precio</em></h1>
      <p>Comparamos relojes clásicos y smartwatches en las tiendas de España. Cada precio lleva la fecha en que se leyó.</p>
      <form id="q" role="search"><input class="search" type="search" name="q" placeholder="Busca marca, modelo o referencia" aria-label="Buscar reloj"></form>
    </section>
    ${saved.length ? section('Tus guardados', `${saved.length}`, `<div class="grid">${saved.slice(0, 4).map(card).join('')}</div>`) : ''}
    ${section('Donde más baja', 'Frente a su media de 30 días', top.length ? `<div class="grid">${top.map(card).join('')}</div>` : '<p class="empty">Todavía no hay precios leídos. La primera pasada los rellena.</p>')}
    ${section('Todo el catálogo', `${relojes.length} relojes`, `<div class="grid">${relojes.slice(0, 8).map(card).join('') || '<p class="empty">Catálogo vacío.</p>'}</div>`)}`;
  }

  function catalog(params) {
    const cat = params.get('cat') || 'todos', tipo = params.get('tipo') || '', marca = params.get('marca') || '', orden = params.get('orden') || 'precio';
    const q = (params.get('q') || '').toLowerCase();
    let list = relojes.filter((i) => (cat === 'todos' || i.categoria === cat) && (!tipo || i.tipo === tipo) && (!marca || i.brand === marca) &&
      (!q || `${i.brand} ${i.name} ${i.ref}`.toLowerCase().includes(q)));
    list = list.sort((a, b) => orden === 'nombre' ? shownName(a).localeCompare(shownName(b)) :
      (best(a)?.p ?? Infinity) - (best(b)?.p ?? Infinity));
    const tipos = [...new Set(relojes.map((i) => i.tipo).filter(Boolean))].sort();
    const marcas = [...new Set(relojes.map((i) => i.brand))].sort();
    const chip = (label, val, cur, key) => `<a class="chip" href="#catalogo?${new URLSearchParams({ ...Object.fromEntries(params), [key]: val }).toString()}" aria-pressed="${val === cur}">${esc(label)}</a>`;
    return `<h1 class="sec-h" style="margin-top:0"><span style="font-size:14px">Catálogo</span></h1>
      <div class="chips" role="group" aria-label="Categoría">
        ${chip('Todos', 'todos', cat, 'cat')}${chip('Clásicos', 'clasico', cat, 'cat')}${chip('Smartwatches', 'smartwatch', cat, 'cat')}
      </div>
      <div class="filters">
        <label>Tipo <select class="sel" data-f="tipo"><option value="">Todos</option>${tipos.map((t) => `<option ${t === tipo ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select></label>
        <label>Marca <select class="sel" data-f="marca"><option value="">Todas</option>${marcas.map((m) => `<option ${m === marca ? 'selected' : ''}>${esc(m)}</option>`).join('')}</select></label>
        <label>Orden <select class="sel" data-f="orden"><option value="precio" ${orden === 'precio' ? 'selected' : ''}>Precio, de menor a mayor</option><option value="nombre" ${orden === 'nombre' ? 'selected' : ''}>Nombre</option></select></label>
        <span class="muted">${list.length} resultados</span>
      </div>
      <div class="grid">${list.map(card).join('') || '<p class="empty">Ningún reloj coincide con esos filtros.</p>'}</div>`;
  }

  function detail(id) {
    const i = relojes.find((x) => x.id === id);
    if (!i) return '<p class="empty">Ese reloj no existe. <a href="#catalogo">Volver al catálogo</a></p>';
    const b = best(i), d = drop(i), fav = favs().includes(i.id), tgt = targets()[i.id];
    const offers = Object.entries(i.prices || {}).filter(([, v]) => v && v.p).map(([s, v]) => ({ s, ...v })).sort((a, c) => a.p - c.p);
    const url = b ? (i.urls || {})[b.s] : null;
    const img = Object.values(i.images || {})[0];
    const deals = chollos.items.filter((c) => c.t && new RegExp(i.ref.replace(/[^A-Za-z0-9]/g, '[^A-Za-z0-9]*'), 'i').test(c.t));
    return `<div class="detail">
      <div><div class="plate" style="aspect-ratio:1">${img ? `<img src="${esc(img)}" alt="${esc(shownName(i))}" referrerpolicy="no-referrer" style="width:70%;height:70%;object-fit:contain;mix-blend-mode:multiply">` : ICON_WATCH(160)}</div></div>
      <div>
        <div class="meta"><span class="dot"></span>${esc(i.brand)} · ${esc(i.tipo || '')} · ${esc(i.categoria === 'smartwatch' ? 'Smartwatch' : 'Clásico')}</div>
        <h1>${esc(i.name)}</h1>
        <p class="muted">Ref. ${esc(i.ref)}${i.caja_mm ? ' · caja ' + i.caja_mm + ' mm' : ''}${i.correa ? ' · ' + esc(i.correa) : ''}${i.verificada ? '' : ' · referencia pendiente de verificar'}</p>
        <div class="panel buy">
          <div class="big">${b ? eur(b.p) : 'Sin precio reciente'}</div>
          ${b ? `<p class="muted">en ${esc(shopName(b.s))}, leído ${ago(b.d)}${d ? ` · ${d.pct < 0 ? '−' : '+'}${Math.abs(Math.round(d.pct * 100))} % frente a su media de 30 días` : ''}</p>` : ''}
          <div class="btn-row">
            ${url ? `<a class="btn" href="${esc(url)}" target="_blank" rel="noopener">Ver en ${esc(shopName(b.s))}</a>` : ''}
            <button class="btn ghost" type="button" data-fav="${esc(i.id)}" aria-pressed="${fav}">${fav ? 'Guardado' : 'Guardar'}</button>
          </div>
          <form class="btn-row" data-target="${esc(i.id)}"><label>Avísame si baja de <input class="sel" type="number" step="0.01" min="0" name="t" value="${tgt ?? ''}" style="width:120px"> €</label><button class="btn ghost" type="submit">Guardar aviso</button></form>
        </div>
        <div class="panel"><h3 style="font-size:22px;margin-bottom:8px">Precio en cada tienda</h3>
          ${offers.length ? `<table><thead><tr><th>Tienda</th><th class="n">Precio</th></tr></thead><tbody>
            ${offers.map((o, k) => `<tr class="${k === 0 ? 'best' : ''}"><td>${esc(shopName(o.s))}${o.via ? ` <span class="muted">vía ${esc(shopName(o.via))}</span>` : ''}<br><span class="muted">${ago(o.d)}${o.stock === false ? ' · agotado' : ''}${o.manual ? ' · verificado a mano' : ''}</span></td><td class="n">${pr(o)}</td></tr>`).join('')}
          </tbody></table>` : `<p class="muted">${i.sin_precio_motivo ? esc(i.sin_precio_motivo) : 'Todavía no hay precios para este reloj.'}</p>`}
        </div>
        ${deals.length ? `<div class="panel"><h3 style="font-size:22px;margin-bottom:8px">Chollos publicados</h3>${deals.slice(0, 4).map((c) => `<p><a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.t)}</a><br><span class="muted">${c.p != null ? eur(c.p) : ''}</span></p>`).join('')}</div>` : ''}
        <p class="disclaimer">Los precios se leen automáticamente cada pasada. Cronoprice no cobra comisión por los enlaces.</p>
      </div></div>`;
  }

  function chollosView() {
    const list = chollos.items.filter((c) => !c.expired);
    return section('Chollos de relojes', chollos.updated ? 'Actualizado ' + ago(chollos.updated) : '',
      list.length ? list.map(row).join('') : '<p class="empty">No hay chollos activos ahora mismo.</p>');
  }

  function guardados() {
    const list = favs().map((id) => relojes.find((i) => i.id === id)).filter(Boolean);
    return section('Guardados', `${list.length}`, list.length ? `<div class="grid">${list.map(card).join('')}</div>` : '<p class="empty">Guarda un reloj con el botón «Guardar» y aparecerá aquí.</p>');
  }

  // ---------------------------------------------------------------- enrutado y eventos
  function render() {
    const [path, qs] = (location.hash.slice(1) || 'inicio').split('?');
    const params = new URLSearchParams(qs || '');
    let html;
    if (path.startsWith('r/')) html = detail(decodeURIComponent(path.slice(2)));
    else if (path === 'catalogo') html = catalog(params);
    else if (path === 'chollos') html = chollosView();
    else if (path === 'guardados') html = guardados();
    else html = home();
    main.innerHTML = html;
    document.querySelectorAll('.nav a').forEach((a) => a.toggleAttribute('aria-current', a.getAttribute('href') === '#' + path));
    const gc = $('#gcount'); const n = favs().length; gc.textContent = n ? String(n) : ''; gc.hidden = !n;
    window.scrollTo(0, 0);
  }

  main.addEventListener('change', (e) => {
    const f = e.target.dataset.f; if (!f) return;
    const p = new URLSearchParams(location.hash.split('?')[1] || '');
    p.set(f, e.target.value); p.delete('') ;
    location.hash = 'catalogo?' + p.toString();
  });
  main.addEventListener('submit', (e) => {
    if (e.target.id === 'q') {
      e.preventDefault();
      const q = new FormData(e.target).get('q');
      location.hash = 'catalogo?q=' + encodeURIComponent(q || '');
    } else if (e.target.dataset.target) {
      e.preventDefault();
      const id = e.target.dataset.target, v = parseFloat(new FormData(e.target).get('t'));
      const t = targets(); if (isNaN(v)) delete t[id]; else t[id] = v; save('cp-targets', t);
      e.target.querySelector('button').textContent = 'Guardado';
    }
  });
  main.addEventListener('click', (e) => {
    const b = e.target.closest('[data-fav]'); if (!b) return;
    const id = b.dataset.fav; let f = favs();
    const on = !f.includes(id); f = on ? [...f, id] : f.filter((x) => x !== id); save('cp-favs', f);
    b.setAttribute('aria-pressed', on); b.textContent = on ? 'Guardado' : 'Guardar';
    const gc = $('#gcount'); gc.textContent = f.length ? String(f.length) : ''; gc.hidden = !f.length;
  });

  // Tema: sigue al sistema y se puede fijar (light | dark), guardado en localStorage
  const THEMES = ['auto', 'light', 'dark'];
  const applyTheme = (t) => { if (t === 'auto') document.documentElement.removeAttribute('data-theme'); else document.documentElement.dataset.theme = t; $('#theme').textContent = { auto: 'Tema: sistema', light: 'Tema: claro', dark: 'Tema: oscuro' }[t]; };
  let cur = (() => { try { return localStorage.getItem('cp-theme') || 'auto'; } catch { return 'auto'; } })();
  applyTheme(cur);
  $('#theme').addEventListener('click', () => { cur = THEMES[(THEMES.indexOf(cur) + 1) % 3]; try { localStorage.setItem('cp-theme', cur); } catch {} applyTheme(cur); });

  window.addEventListener('hashchange', render);
  Promise.all([
    fetch(DATA + 'relojes.json').then((r) => r.json()),
    fetch(DATA + 'chollos.json').then((r) => r.json()).catch(() => ({ items: [] })),
    fetch(DATA + 'estado.json').then((r) => r.json()).catch(() => ({})),
  ]).then(([r, c, est]) => {
    relojes = r; chollos = c;
    const n = relojes.length, shops = new Set(relojes.flatMap((i) => Object.keys(i.prices || {}))).size;
    $('#foot').innerHTML = `<p>Seguimos ${n} relojes en ${shops} tiendas. Última pasada: ${est.at ? esc(new Date(est.at).toLocaleString('es-ES')) : 'pendiente'}.</p>`;
    render();
  }).catch(() => { main.innerHTML = '<p class="empty">No se pudieron cargar los datos. Recarga la página.</p>'; });
})();
