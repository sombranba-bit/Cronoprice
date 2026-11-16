"""Prueba de acceso: comprueba qué tiendas dejan leer desde GitHub antes de activarlas en radar.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import radar  # noqa: E402

PROBE = {
    "idealo": "https://www.idealo.es/resultados.html?q=SRPD55K1",
    "chollometro": "https://www.chollometro.com/categorias/relojes",
    "elcorteingles": "https://www.elcorteingles.es/buscar/?s=SRPD55K1",   # comprobar condiciones antes de activar
}

get = radar.make_session()
for shop, url in PROBE.items():
    try:
        r = get(url)
        print(shop, getattr(r, "status_code", "?"), len(r.text or ""), flush=True)
    except Exception as e:
        print(shop, "error", type(e).__name__, flush=True)
