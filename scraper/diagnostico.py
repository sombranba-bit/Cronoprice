"""Prueba de acceso: comprueba qué tiendas dejan leer desde GitHub antes de activarlas en radar.py."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import radar  # noqa: E402

PROBE = {
    "idealo": "https://www.idealo.es/resultados.html?q=SRPD55K1",
    "chollometro": "https://www.chollometro.com/categorias/relojes",
    "elcorteingles": "https://www.elcorteingles.es/buscar/?s=SRPD55K1",   # comprobar condiciones antes de activar
    # Especialistas y tiendas oficiales (ficha con garantía y papeles)
    "tourneau": "https://www.tourneau.com/watches/grand-seiko/spring-drive-sbga413-sbga413-GSA0100004.html",
    "lepage": "https://lepage.fr/en/10093-hamilton-jazzmaster-gent-automatic-watch-blue-dial-blue-leather-strap-40-mm-h32475640.html",
    "maier": "https://en.maier.fr/watchmaking-jewelry-brands/omega/watches/moonwatch/moonwatch-professional-coaeuraxial-master-chronometer-chronograph-42-mm_310-30-42-50-01-001",
    "watchesofswitzerland": "https://www.watchesofswitzerland.com/pages/rolex/submariner-m126610ln-0001",
    "the1916company": "https://www.the1916company.com/watches/tudor/black-bay-58/m79030n-0001/",
    "tudor": "https://tudorwatch.com/en/watches/black-bay-58/m79030n-0001",
    "omega": "https://www.omegawatches.com/media/pdf/watches/product-sheet/dk/en-gb/31030425001001-en-gb.pdf",
    "rolex": "https://www.rolex.com/en/watches/submariner/m126610ln-0001",
    "sinn": "https://www.sinn.de/en/watches/104-st-sa-i-w.html",
    "seiko": "https://seikowatches.com/us-en/products/presage/srph93j1",
    "seiko_ph": "https://www.seikowatches.com/ph-en/products/presage/srph93j1",
    "watchesofswitzerland_tudor": "https://www.watchesofswitzerland.com/en-int/products/tudor-black-bay-m79030n-0001-40993201",
}

# Referencia que debe aparecer en la página, para saber si es la ficha correcta
REF = {
    "tourneau": "SBGA413", "lepage": "H32475640", "maier": "310.30.42.50.01.001",
    "watchesofswitzerland": "126610LN", "the1916company": "M79030N", "tudor": "M79030N",
    "omega": "310.30.42.50.01.001", "rolex": "126610LN", "sinn": "104", "seiko": "SRPH93J1", "seiko_ph": "SRPH93J1", "watchesofswitzerland_tudor": "M79030N",
}
PRECIO = re.compile(r"(€|EUR|\$|£)\s?\d|\d[\d.,]*\s?(€|EUR)")
GARANTIA = re.compile(r"garant|warranty|guarantee|papeles|certificat|certificate|papers", re.I)

get = radar.make_session()
for shop, url in PROBE.items():
    try:
        r = get(url)
        txt = r.text or ""
        ref = REF.get(shop)
        ref_ok = "-" if not ref else ("sí" if re.search(re.escape(ref).replace("\\.", "[.\\s-]?"), txt, re.I) else "no")
        m = PRECIO.search(txt)
        if m:
            print("  snippet:", re.sub(r"\s+", " ", txt[max(0, m.start()-60):m.end()+40]), flush=True)
        print(shop, getattr(r, "status_code", "?"), len(txt),
              "ref:" + ref_ok,
              "precios:" + str(len(PRECIO.findall(txt))),
              "garantia:" + str(len(GARANTIA.findall(txt))), flush=True)
    except Exception as e:
        print(shop, "error", type(e).__name__, flush=True)
