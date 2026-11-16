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
    ("casio-ga-2100-1a1e_dist", "https://www.watchclick.com/es/products/mens-watch-casio-g-shock-ga-2100-1a1er", "GA-2100-1A1ER"),
    ("tissot-prx-t137-41_ofic", "https://www.tissotwatches.com/es-es/T1374101105100.html", "T137.410.11.051.00"),
    ("hamilton-khaki-fie_ofic", "https://www.hamiltonwatch.com/es-es/h70605160-khaki-field-auto.html", "H70605160"),
    ("garmin-venu-3-010-_dist", "https://www.pccomponentes.com/garmin-venu-3-reloj-smartwatch-45mm-bisel-acero-inoxidable-con-caja-y-correa-de-silicona-blanca", "010-02784-00"),
    ("citizen-promaster-_dist", "https://laguardajoiers.com/en/bn0150-61e-citizen-promaster-divers-eco-drive.html", "BN0150-61E"),
    ("oris-aquis-date-01_dist", "https://en.maier.fr/watchmaking-jewelry-brands/oris/watches/aquis/aquis-date_01-733-7730-4135-07-8-24-05peb", "01 733 7730 4135-07 8 24 05PEB"),
    ("longines-spirit-l3_dist", "https://www.bucherer.com/de/en/watches/longines/spirit/1331-428-6.html", "L3.810.4.53.0"),
    ("mido-ocean-star-20_dist", "https://en.maier.fr/watchmaking-jewelry-brands/mido/watches/ocean-star-200/ocean-star-200_m026-430-11-051-00", "M026.430.11.051.00"),
    ("hamilton-jazzmaste_dist", "https://lepage.fr/en/10093-hamilton-jazzmaster-gent-automatic-watch-blue-dial-blue-leather-strap-40-mm-h32475640.html", "H32475640"),
    ("seiko-presage-srph_ofic", "https://store.seiko.ie/collections/seiko/products/srph93j1", "SRPH93J1"),
    ("sinn-104-st-sa-i-w_ofic", "https://www.sinn.de/en/watches/104-st-sa-i-w.html", "104.012"),
    ("grand-seiko-sbga41_ofic", "https://www.grand-seiko.com/es-es/collections/sbga413g", "SBGA413"),
    ("omega-speedmaster-_dist", "https://bucherer.com/de/en/watches/omega/speedmaster/1337-038-0.html", "310.30.42.50.01.001"),
    ("tudor-black-bay-58_dist", "https://www.bucherer.com/at/en/watches/tudor/black-bay/1307-202-3.html", "M79030N-0001"),
    ("breitling-navitime_dist", "https://en.maier.fr/watchmaking-jewelry-brands/breitling/watches/navitimer/navitimer-b01-chronograph-43_ab0138211b1p1", "AB0138211B1P1"),
    ("rolex-submariner-d_dist", "https://www.weirandsons.ie/m126610ln-0001.html", "126610LN"),
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
