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
    ("garmin_pccomponentes", "https://www.pccomponentes.com/garmin-venu-3-reloj-smartwatch-45mm-bisel-acero-inoxidable-con-caja-y-correa-de-silicona-blanca", "010-02784-00"),
    ("citizen_laguardajoiers", "https://laguardajoiers.com/en/bn0150-61e-citizen-promaster-divers-eco-drive.html", "BN0150-61E"),
    ("sinn_sinnde", "https://www.sinn.de/en/watches/104-st-sa-i-w.html", "104.012"),
    ("grandseiko_oficial", "https://www.grand-seiko.com/es-es/collections/sbga413g", "SBGA413"),
    ("omega_wristler", "https://wristler.eu/es/relojes/221320-omega-speedmaster-professional-moonwatch", "310.30.42.50.01.001"),
    ("hamilton_montredo", "https://www.montredo.com/products/hamilton-jazzmaster-automatic-blue-40mm-6-30589", "H32475640"),
    ("hamilton_oficial_es", "https://www.hamiltonwatch.com/es-mx/h32475640-jazzmaster-auto.html", "H32475640"),
    ("seiko_store_ie", "https://store.seiko.ie/collections/seiko/products/srph93j1", "SRPH93J1"),
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
