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
    ("casio_dist", "https://relojeshermosos.es/casio-g-shock-ga-2100-1aer.html", "GA-2100-1A"),
    ("garmin_dist", "https://www.pccomponentes.com/garmin-venu-3-reloj-smartwatch-45mm-bisel-acero-inoxidable-con-caja-y-correa-de-silicona-blanca", "010-02784-00"),
    ("citizen_dist", "https://tomasinifrancia.it/en/citizen-promaster-bn0150-61e", "BN0150-61E"),
    ("oris_dist", "https://www.perodri.es/en/relojes/oris/aquis-date/oris-aquis-date-4", "01 733 7730 4135-07"),
    ("longines_dist", "https://www.rabat.net/en/longines-spirit-l38104530", "L3.810.4.53.0"),
    ("mido_dist", "https://en.maier.fr/watchmaking-jewelry-brands/mido/watches/ocean-star-200/ocean-star-200_m026-430-11-051-00", "M026.430.11.051.00"),
    ("hamilton_jazz_dist", "https://en.maier.fr/watchmaking-jewelry-brands/hamilton/watches/jazzmaster/auto_h32475640", "H32475640"),
    ("seiko_presage_dist", "https://en.maier.fr/watchmaking-jewelry-brands/seiko/watches/presage/presage-watch_srph93j1", "SRPH93J1"),
    ("tudor_dist", "https://www.perodri.es/en/discontinued/tudor-black-bay-fifty-eight-2/", "M79030N-0001"),
    ("breitling_dist", "https://www.montredo.com/products/breitling-navitimer-automatic-black-43mm-12-33911", "AB0138211B1P1"),
    ("seiko5_dist", "https://www.montredo.com/watches/seiko/5-sports/srpd55k1/35280/", "SRPD55K1"),
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
