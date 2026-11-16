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
    ("montredo_0_sucia", "https://www.montredo.com/products/seiko-5-sports-automatic-green-42mm-2-35273?_pos=1&_sid=5c505206d&_ss=r", "SRPD63K1"),
    ("montredo_0_limpia", "https://www.montredo.com/products/seiko-5-sports-automatic-green-42mm-2-35273", "SRPD63K1"),
    ("montredo_1_sucia", "https://www.montredo.com/products/seiko-5-sports-automatic-black-40mm-2-35292?_pos=1&_sid=b7d678110&_ss=r", "SRPE55K1"),
    ("montredo_1_limpia", "https://www.montredo.com/products/seiko-5-sports-automatic-black-40mm-2-35292", "SRPE55K1"),
    ("montredo_2_sucia", "https://www.montredo.com/products/seiko-5-sports-automatic-black-39mm-2-35277?_pos=1&_sid=82850ba17&_ss=r", "SRPG27K1"),
    ("montredo_2_limpia", "https://www.montredo.com/products/seiko-5-sports-automatic-black-39mm-2-35277", "SRPG27K1"),
    ("montredo_3_sucia", "https://www.montredo.com/products/seiko-5-sports-automatic-blue-39mm-35278?_pos=1&_sid=99a55cbe3&_ss=r", "SRPG29K1"),
    ("montredo_3_limpia", "https://www.montredo.com/products/seiko-5-sports-automatic-blue-39mm-35278", "SRPG29K1"),
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
            txt = r.text or ""
            print("  jsonld:", txt.count("application/ld+json"), "| mpn/sku:", bool(re.search(r'"(sku|mpn|gtin)"', txt)), flush=True)
            for k, bloque in enumerate(re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', txt, re.S)[:3]):
                print("  ld", k, ":", re.sub(r"\s+", " ", bloque)[:300], flush=True)
            for k, m in enumerate(list(ref_regex(ref).finditer(txt))[:3]):
                ventana = re.sub(r"\s+", " ", txt[m.start(): m.end() + 220])
                print("  ventana", k, ":", ventana[:260], flush=True)
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
