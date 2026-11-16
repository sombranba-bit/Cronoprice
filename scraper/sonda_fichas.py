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
    ("hamilton_es", "https://www.hamiltonwatch.com/es-es/h70605160-khaki-field-auto.html", "H70605160"),
    ("tissot_es", "https://www.tissotwatches.com/es-es/T1374101105100.html", "T137.410.11.051.00"),
    ("seiko5_es", "https://www.seikowatches.com/es-es/products/5sports/srpd55", "SRPD55K1"),
    ("seiko_presage_es", "https://www.seikowatches.com/es-es/products/presage/srph93", "SRPH93J1"),
    ("casio_es", "https://www.casio.com/es/watches/gshock/product.GA-2100-1A/", "GA-2100-1A1"),
    ("citizen_laguarda", "https://laguardajoiers.com/en/bn0150-61e-citizen-promaster-divers-eco-drive.html", "BN0150-61E"),
    ("sinn_de", "https://www.sinn.de/en/watches/104-st-sa-i-w.html", "104.012"),
    ("tudor_es", "https://www.tudorwatch.com/es/watches/black-bay-58/m79030n-0001", "M79030N-0001"),
]

PRECIO = re.compile(r"\d[\d.\s]*[,.]\d{2}\s?€|€\s?\d[\d.,]*|\d[\d.,]*\s?EUR", re.I)
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
