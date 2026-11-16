"""Pasada de precios de Cronoprice (se ejecuta en GitHub Actions).

Lee data/relojes.json, visita las fichas guardadas (urls) de cada reloj, saca
el precio de su referencia exacta (ref) y actualiza prices / history / checked.
Después lee los chollos de relojes de Chollometro (data/chollos.json) y deja un
resumen en data/estado.json.

Cambios frente a la versión de perfumes (radar-perfumes):
- el emparejamiento es por referencia del fabricante (ref), no por tamaño en ml;
- cada reloj se revisa en un bloque aislado: un error no tira la pasada entera;
- el archivo de datos se guarda tras cada reloj, no solo al final;
- si falta curl_cffi, la pasada se detiene con error (no hay respaldo silencioso).
"""
import html as htmllib
import json
import os
import random
import re
import statistics
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/Madrid")
BATCH = int(os.environ.get("RADAR_BATCH", "70"))          # relojes por pasada
DISCOVER_PER_RUN = int(os.environ.get("RADAR_DISCOVER", "20"))
MANUAL = {"amazon", "eci"}                                # tiendas sin lectura automática (ver README)

PRICE_RE = re.compile(r"(\d{1,5}(?:[.\s]\d{3})*(?:[.,]\d{1,2})?)\s*(?:€|&euro;|EUR)")


def now_iso():
    return datetime.now(TZ).isoformat(timespec="seconds")


def to_float(s):
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace("\xa0", "").replace(" ", "")
    if "," in s and "." in s:          # 1.234,56 -> 1234.56
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def norm_ref(s):
    """Referencia sin guiones, espacios ni mayúsculas: 'GA-2100-1A1ER' -> 'GA21001A1ER'."""
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def ref_pattern(ref):
    """Patrón de la referencia que admite guiones, puntos o espacios entre sus caracteres y no pega con otra más larga."""
    r = norm_ref(ref)
    if not r:
        return None
    return re.compile(r"(?<![A-Z0-9])" + r"[-\s./]*".join(re.escape(c) for c in r) + r"(?![A-Z0-9])")


def has_ref(text, ref):
    pat = ref_pattern(ref)
    return bool(pat and pat.search(htmllib.unescape(str(text or "")).upper()))


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _types(o):
    t = o.get("@type", "")
    return {t} if isinstance(t, str) else set(t)


# ---------------------------------------------------------------- extracción
def jsonld_offers(page):
    """[(precio, texto_de_la_oferta, nombre_del_producto, disponible)] de los bloques JSON-LD."""
    out = []
    for raw in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try:
            data = json.loads(raw.strip(), strict=False)
        except Exception:
            try:
                data = json.loads(htmllib.unescape(raw.strip()), strict=False)
            except Exception:
                continue
        for o in _walk(data):
            if not (_types(o) & {"Product", "ProductGroup"}):
                continue
            # en relojes la referencia viene en mpn, sku o gtin; se junta todo para emparejar
            pname = " ".join(str(o.get(k, "")) for k in ("name", "sku", "mpn", "model", "gtin13"))[:300]
            offers = o.get("offers")
            if isinstance(offers, dict) and "offers" in offers:
                offers = offers["offers"]
            if isinstance(offers, dict):
                offers = [offers]
            for of in offers or []:
                if not isinstance(of, dict):
                    continue
                p = to_float(of.get("price") or of.get("lowPrice") or "")
                if not p:
                    continue
                cur = of.get("priceCurrency", "EUR")
                if cur and cur.upper() != "EUR":
                    continue
                desc = " ".join(str(of.get(k, "")) for k in ("name", "sku", "mpn"))
                av = str(of.get("availability", ""))
                out.append((p, desc, pname, "OutOfStock" not in av and "SoldOut" not in av))
    return out


def extract(page, ref, url):
    """(precio, en_stock, metodo) del reloj con esa referencia, o (None, None, motivo)."""
    if not has_ref(page, ref):
        return None, None, "sin-referencia"        # si la ficha no menciona la referencia, no es este reloj
    offers = jsonld_offers(page)
    own = [o for o in offers if has_ref(o[1] + " " + o[2], ref)]
    if own:
        p, _, _, st = min(own, key=lambda o: o[0])
        return p, st, "jsonld"
    # Respaldo de texto: la referencia y, justo detrás, el primer precio en €
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S | re.I)
    txt = htmllib.unescape(re.sub(r"<[^>]+>", " ", txt))
    txt = re.sub(r"\s+", " ", txt)
    m = ref_pattern(ref).search(txt.upper()) if ref_pattern(ref) else None
    if m:
        pm = PRICE_RE.search(txt[m.end(): m.end() + 160])
        if pm:
            p = to_float(pm.group(1))
            if p and 15 <= p <= 100000:
                return p, None, "texto"            # sin stock fiable en texto libre
    return None, None, "sin-precio"


NO_PHOTO = re.compile(r"idealo\.com/images/product/|placeholder|no[-_]?image|sin[-_]imagen", re.I)


def product_image(page):
    pic = _product_image(page)
    return None if pic and NO_PHOTO.search(pic) else pic


def _product_image(page):
    """Dirección de la foto principal (JSON-LD o og:image). Nunca se descarga el archivo."""
    for raw in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try:
            data = json.loads(raw.strip(), strict=False)
        except Exception:
            continue
        for o in _walk(data):
            if not (_types(o) & {"Product", "ProductGroup"}):
                continue
            im = o.get("image")
            if isinstance(im, list):
                im = im[0] if im else None
            if isinstance(im, dict):
                im = im.get("url") or im.get("contentUrl")
            if isinstance(im, str) and im.startswith(("http://", "https://", "//")):
                return htmllib.unescape(im if not im.startswith("//") else "https:" + im)
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page, re.I)
    return htmllib.unescape(m.group(1)) if m and m.group(1).startswith("http") else None


# Tiendas que bloquean la lectura directa pero salen en las ofertas de Idealo.
# El HTML no trae el nombre de la tienda, solo su número en Idealo: se completa a medida que se confirme.
IDEALO_SHOPS = {}
BUNDLE_RE = re.compile(r"reacondicionad|segunda mano|\busad[oa]\b|outlet|correa de repuesto|caja vac[ií]a|"
                       r"\br[ée]plica|\bcopia\b|falsificad|\bset\b|estuche|lote|pack|\+", re.I)


def idealo_offers(page, ref):
    """{tienda: precio} de la lista de ofertas de Idealo para esa referencia, sin reacondicionados ni réplicas."""
    from urllib.parse import parse_qs
    out = {}
    for chunk in re.split(r'<li[^>]+class="productOffers-listItem[\s"]', page)[1:]:
        chunk = htmllib.unescape(chunk)
        link = re.search(r'relocate\?([^"\'\s>]+)', chunk)
        if not link:
            continue
        q = parse_qs(link.group(1))
        sid = IDEALO_SHOPS.get((q.get("sid") or [""])[0])
        p = to_float((q.get("price") or [""])[0])
        if not (sid and p):
            continue
        t0 = chunk.find("productOffers-listItemTitle")
        title = re.sub(r"<[^>]+>", " ", chunk[t0:t0 + 1500]) if t0 >= 0 else ""
        title = title.split("€")[0]
        if BUNDLE_RE.search(title) or not has_ref(title, ref):
            continue
        if sid not in out or p < out[sid]:
            out[sid] = p
    return out


# Tiendas de precio de catálogo (sin rebajas agresivas): tolerancia mayor frente a la mediana
FULL_PRICE = {"oficial"}


def plausible(p, ref, how="jsonld", shop=""):
    """Un precio es plausible si no se aleja mucho de la mediana de las demás tiendas."""
    if ref is None:
        return how != "texto"
    lo, hi = (0.75, 1.3) if how == "texto" else (0.55, 1.8 if shop in FULL_PRICE else 1.5)
    return lo * ref <= p <= hi * ref


def ref_price(prices, shop):
    others = [v["p"] for k, v in prices.items() if k != shop and v and v.get("p") and v.get("stock") is not False]
    return statistics.median(others) if others else (prices.get(shop) or {}).get("p")


def clean_outliers(it):
    """Quita precios leídos por el programa que salen muy por encima de lo que marcan las demás tiendas."""
    prices = it.get("prices") or {}
    gone = []
    for shop, v in list(prices.items()):
        if not v or not v.get("p") or not v.get("gh"):
            continue
        others = [w["p"] for k, w in prices.items() if k != shop and w and w.get("p") and w.get("stock") is not False]
        if len(others) >= 2 and v["p"] > (1.8 if shop in FULL_PRICE else 1.5) * statistics.median(others):
            del prices[shop]
            it["history"] = [h for h in it.get("history", []) if not (h.get("s") == shop and h.get("p") == v["p"])]
            gone.append(shop)
    return gone


# ---------------------------------------------------------------- red
def make_session():
    """curl_cffi con huella de Chrome. Si falta, la pasada falla: no se cambia de cliente en silencio."""
    from curl_cffi import requests as cr          # ImportError deja la pasada parada, a propósito
    s = cr.Session(impersonate="chrome")
    return lambda u: s.get(u, timeout=25, allow_redirects=True)


# ---------------------------------------------------------------- buscar fichas nuevas
# Búsquedas desde GitHub. Cada tienda se activa solo si diagnostico.py confirma que deja entrar.
SEARCH = {
    "idealo": "https://www.idealo.es/resultados.html?q={q}",
}
SKIP_PATH = re.compile(r"/search|/buscar|resultados|/c/|/brands?/|/marcas?/|/categor|login|cart|wishlist|\.(?:css|js|png|jpg|svg|webp)", re.I)


def best_link(page, base, it):
    """La ficha de la página de resultados que tiene la referencia exacta del reloj (o None)."""
    host = re.match(r"https?://[^/]+", base).group(0)
    best, score = None, 0
    for m in re.finditer(r'href="([^"#]+)"', page):
        href = htmllib.unescape(m.group(1))
        ctx = page[m.end(): m.end() + 300].split("href=")[0]
        if href.startswith("/"):
            href = host + href
        if not href.startswith(host) or SKIP_PATH.search(href[len(host):]) or len(href) - len(host) < 12:
            continue
        if href in it.get("descartadas", ()):
            continue
        text = href + " " + re.sub(r"<[^>]+>", " ", ctx)
        if not has_ref(text, it["ref"]) or BUNDLE_RE.search(text):
            continue
        sc = 2 + (it["brand"].lower() in text.lower())
        if sc > score:
            best, score = href, sc
    return best


def discover(it, get, today, budget):
    """Busca la ficha del reloj en las tiendas de SEARCH que aún no tiene. Devuelve cuántas búsquedas gastó."""
    urls = it.setdefault("urls", {})
    tried = it.setdefault("buscado", {})
    spent = 0
    for shop, tpl in SEARCH.items():
        if spent >= budget or urls.get(shop):
            continue
        if tried.get(shop) and (datetime.fromisoformat(today) - datetime.fromisoformat(tried[shop])).days < 7:
            continue
        q = re.sub(r"\s+", "+", it["ref"].strip())
        spent += 1
        tried[shop] = today
        try:
            r = get(tpl.format(q=q))
            if getattr(r, "status_code", 0) == 200:
                link = best_link(r.text, tpl, it)
                if link:
                    urls[shop] = link
        except Exception:
            pass
        time.sleep(1.2)
    return spent


# ---------------------------------------------------------------- pasada
def update_item(it, get, stats, today):
    prices = it.setdefault("prices", {})
    hist = it.setdefault("history", [])
    for shop, url in (it.get("urls") or {}).items():
        if shop in MANUAL or not url:
            continue
        st = stats.setdefault(shop, {"ok": 0, "bloqueada": 0, "sin_precio": 0, "dudoso": 0})
        try:
            r = get(url)
            code = getattr(r, "status_code", 0)
        except Exception:
            st["bloqueada"] += 1
            continue
        if code in (403, 429, 503) or code >= 500:
            st["bloqueada"] += 1
            continue
        if code in (404, 410):
            st["sin_precio"] += 1
            continue
        p, stock, how = extract(r.text, it["ref"], url)
        ref = ref_price(prices, shop)
        if shop == "idealo":
            # las ofertas de la página de Idealo se leen aunque el precio principal se descarte
            for sid, vp in idealo_offers(r.text, it["ref"]).items():
                own = prices.get(sid) or {}
                if own.get("d") == today and not own.get("via"):
                    continue                          # ya leída hoy en la propia tienda
                if not plausible(vp, ref_price(prices, sid), "jsonld"):
                    continue
                vs = stats.setdefault(sid, {"ok": 0, "bloqueada": 0, "sin_precio": 0, "dudoso": 0})
                vs["via_idealo"] = vs.get("via_idealo", 0) + 1
                prices[sid] = {"p": round(vp, 2), "d": today, "auto": True, "gh": True, "via": "idealo"}
                hist[:] = [h for h in hist if not (h.get("d") == today and h.get("s") == sid)]
                hist.append({"d": today, "s": sid, "p": round(vp, 2)})
        ok = bool(p) and plausible(p, ref, how, shop)
        if not p:
            st["sin_precio"] += 1
            continue
        if not ok:
            st["dudoso"] += 1
            ej = st.setdefault("ejemplos", [])
            if len(ej) < 3:
                ej.append({"reloj": it.get("id"), "precio": round(p, 2), "referencia": ref, "metodo": how})
            continue
        st["ok"] += 1
        st[how] = st.get(how, 0) + 1
        pic = product_image(r.text)
        if pic:
            it.setdefault("images", {})[shop] = pic[:500]
        entry = {"p": round(p, 2), "d": today, "auto": True, "gh": True}
        if stock is False:
            entry["stock"] = False
        prices[shop] = entry
        if stock is not False:
            hist[:] = [h for h in hist if not (h.get("d") == today and h.get("s") == shop)]
            hist.append({"d": today, "s": shop, "p": round(p, 2)})
        time.sleep(random.uniform(0.8, 1.8))
    if len(hist) > 800:
        del hist[: len(hist) - 800]
    it["checked"] = now_iso()


# ---------------------------------------------------------------- chollometro
# Categoría de relojes: comprobar la URL con el diagnóstico antes de dar la pasada por buena.
CH_PAGES = ["https://www.chollometro.com/categorias/relojes"]
WATCH_WORDS = re.compile(r"reloj|watch|smartwatch|seiko|casio|citizen|tissot|garmin|orient|hamilton|longines|fossil|g-shock", re.I)


def parse_chollos(page):
    """Hilos de una página de categoría de Chollometro: [{id,t,p,shop,url,expired}]."""
    found = {}
    for _, raw in re.findall(r'data-vue3=(["\'])(.*?)\1', page, re.S):
        try:
            data = json.loads(htmllib.unescape(raw))
        except Exception:
            continue
        for o in _walk(data):
            if "threadId" in o and "title" in o:
                tid = int(o["threadId"])
                link = o.get("shareableLink") or o.get("link") or o.get("url") or ""
                if not str(link).startswith("http"):
                    link = f"https://www.chollometro.com/ofertas/{o.get('titleSlug', 'oferta')}-{tid}"
                merchant = o.get("merchant") or {}
                found[tid] = {"id": tid, "t": str(o["title"])[:120],
                              "p": to_float(o.get("price")) if o.get("price") not in (None, "", 0) else None,
                              "shop": merchant.get("merchantName") if isinstance(merchant, dict) else None,
                              "url": link, "expired": bool(o.get("isExpired"))}
    if not found:   # respaldo: enlaces /ofertas/<slug>-<id>
        for m in re.finditer(r'href="(https://www\.chollometro\.com/ofertas/([^"#?]+)-(\d+))"', page):
            tid = int(m.group(3))
            title = m.group(2).replace("-", " ").capitalize()
            found.setdefault(tid, {"id": tid, "t": title[:120], "p": None, "shop": None, "url": m.group(1), "expired": False})
    return list(found.values())


def pass_chollos(get, estado, brands=()):
    path = DATA / "chollos.json"
    feed = json.loads(path.read_text()) if path.exists() else {"items": []}
    old = {x["id"]: x for x in feed.get("items", [])}
    today = datetime.now(TZ).date().isoformat()
    n = 0
    for u in CH_PAGES:
        try:
            r = get(u)
            if getattr(r, "status_code", 0) != 200:
                estado["chollometro"] = f"error {getattr(r, 'status_code', '?')}"
                continue
            found = parse_chollos(r.text)
            if not found:
                estado["chollometro"] = "0 encontrados"
            found = [x for x in found if WATCH_WORDS.search(x["t"]) or any(b.lower() in x["t"].lower() for b in brands)]
            for x in found:
                x["seen"] = today
                old[x["id"]] = {**old.get(x["id"], {}), **{k: v for k, v in x.items() if v is not None}}
                n += 1
        except Exception as e:
            estado["chollometro"] = f"error {type(e).__name__}"
        time.sleep(1.5)
    items = sorted(old.values(), key=lambda x: x["id"], reverse=True)[:80]
    if n:
        estado["chollometro"] = f"ok {n}"
        feed = {"items": items, "updated": now_iso()}
        path.write_text(json.dumps(feed, ensure_ascii=False, indent=1))
    return n


def main():
    get = make_session()
    path = DATA / "relojes.json"
    relojes = json.loads(path.read_text())
    today = datetime.now(TZ).date().isoformat()
    limpiados = {i["id"]: g for i in relojes if (g := clean_outliers(i))}
    order = sorted(relojes, key=lambda i: i.get("checked") or "")
    stats, errores = {}, []
    budget = DISCOVER_PER_RUN
    for it in order[:BATCH]:
        try:                                          # un reloj con error no tumba la pasada
            budget -= discover(it, get, today, budget)
            update_item(it, get, stats, today)
        except Exception as e:
            errores.append({"reloj": it.get("id"), "error": type(e).__name__})
            print("error", it.get("id"), type(e).__name__, flush=True)
        path.write_text(json.dumps(relojes, ensure_ascii=False, indent=1, sort_keys=True))   # guardado por reloj
        print("%s %s -> %s" % (it["brand"], it["ref"], ", ".join(
            "%s:%s" % (k, v["p"]) for k, v in (it.get("prices") or {}).items() if v and v.get("d") == today) or "-"), flush=True)
    estado = {"at": now_iso(), "revisados": min(BATCH, len(relojes)), "tiendas": stats,
              "limpiados": limpiados, "errores": errores}
    pass_chollos(get, estado, {i["brand"] for i in relojes})
    (DATA / "estado.json").write_text(json.dumps(estado, ensure_ascii=False, indent=1))
    print(json.dumps(estado, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
