"""Sonda de fichas oficiales (España): comprueba referencia, precio en euros y garantía.

Uso: python scraper/sonda_fichas.py static   (HTML directo, curl_cffi)
     python scraper/sonda_fichas.py js       (página renderizada, Playwright + Chromium)
Solo informa; no escribe datos ni activa fuentes en radar.py.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# (clave, url, referencia que debe aparecer)
FICHAS = [
    ("rolex_uhrinstinkt", "https://www.uhrinstinkt.de/rolex-submariner-date-126610ln-z100038.html", "126610LN"),
    ("bulova_watchia", "https://www.watchia.com/eu/bulova-precisionist-96b257.html", "96B257"),
    ("citizen_tomasini", "https://tomasinifrancia.it/en/citizen-promaster-bn0150-61e", "BN0150-61E"),
    ("garmin_galador", "https://www.galador.eu/1854-fitness-trackers/20106547-garmin-venu-3-3-56-cm-1-4-amoled-45-mm-digital-454-x-454-pixels-touchscreen-silver-white-wi-fi-gps-satellite", "010-02784-00"),
    ("omega_maier", "https://en.maier.fr/watchmaking-jewelry-brands/omega/watches/moonwatch/moonwatch-professional-coaeuraxial-master-chronometer-chronograph-42-mm_310-30-42-50-01-001", "310.30.42.50.01.001"),
    ("longines_maier", "https://en.maier.fr/watchmaking-jewelry-brands/longines/watches/longines-spirit/longines-spirit_l3-810-4-53-0", "L3.810.4.53.0"),
    ("tudor_maier", "https://en.maier.fr/watchmaking-jewelry-brands/tudor/watches/black-bay-58/black-bay-fifty-eight_m79030n-0001", "M79030N-0001"),
    ("grandseiko_rabat", "https://www.rabat.net/en/grand-seiko-heritage-spring-drive-shunbun-sbga413g", "SBGA413"),
    ("seiko_lepage", "https://www.lepage.fr/en/20185-seiko-presage-style-60s-ruby-automatic-watch-white-dial-steel-bracelet-408-mm-srph93j1.html", "SRPH93J1"),
    ("hamilton_lepage", "https://lepage.fr/en/10093-hamilton-jazzmaster-gent-automatic-watch-blue-dial-blue-leather-strap-40-mm-h32475640.html", "H32475640"),
    ("sinn_jura", "https://jurawatches.co.uk/products/sinn-watch-104-st-sa-i-w-silicone-black-104-012", "104.012"),
]

PRECIO = re.compile(r"\d[\d.\s]*\s?€|€\s?\d[\d.,]*|\d[\d.,]*\s?EUR", re.I)
GARANTIA = re.compile(r"garant[ií]a|papeles|certificado", re.I)


def ref_regex(ref):
    return re.compile(re.escape(ref).replace(r"\.", r"[.\s-]?"), re.I)


def informe(clave, status, txt, ref):
    precios = PRECIO.findall(txt)
    m = PRECIO.search(txt)
    fragmento = re.sub(r"\s+", " ", txt[max(0, m.start() - 50): m.end() + 30]) if m else "-"
    ref_ok = "sí" if ref_regex(ref).search(txt) else "no"
    print(clave, status, len(txt), f"ref:{ref_ok}", f"precios:{len(precios)}",
          f"garantia:{len(GARANTIA.findall(txt))}", flush=True)
    print("  precio:", fragmento, flush=True)


def modo_static():
    import radar
    get = radar.make_session()
    for clave, url, ref in FICHAS:
        try:
            r = get(url)
            informe(clave, getattr(r, "status_code", "?"), r.text or "", ref)
            # Lo que leería de verdad la pasada (misma función que radar.py)
            p, stock, how = radar.extract(r.text or "", ref, url)
            print("  pasada lee:", p, stock, how, flush=True)
        except Exception as e:
            print(clave, "error", type(e).__name__, flush=True)


def modo_js():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        nav = p.chromium.launch(args=["--no-sandbox"])
        page = nav.new_page(locale="es-ES")
        for clave, url, ref in FICHAS:
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(5000)
                informe(clave, getattr(resp, "status", "?"), page.content(), ref)
            except Exception as e:
                print(clave, "error", type(e).__name__, flush=True)
        nav.close()


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "static"
    if modo == "js":
        modo_js()
    else:
        modo_static()
