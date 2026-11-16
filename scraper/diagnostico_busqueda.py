"""Prueba de búsqueda: ¿cada tienda deja buscar una referencia y devuelve su ficha? (desde el runner)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import radar  # noqa: E402

# tienda -> plantilla de búsqueda ({q} = referencia)
BUSQUEDA = {
    "idealo": "https://www.idealo.es/resultados.html?q={q}",
    "elcorteingles": "https://www.elcorteingles.es/buscar/?s={q}",
    "pccomponentes": "https://www.pccomponentes.com/buscar/?query={q}",
    "quera": "https://www.quera.es/buscar?controller=search&s={q}",
    "nicols": "https://www.nicols.es/es/buscar?controller=search&s={q}",
    "prjoyeros": "https://www.prjoyeros.com/es/buscar?controller=search&s={q}",
    "zapatajoyeros": "https://www.zapatajoyeros.com/es/buscar?controller=search&s={q}",
    "laguardajoiers": "https://laguardajoiers.com/en/search?controller=search&s={q}",
    "lepage": "https://www.lepage.fr/en/search?controller=search&s={q}",
    "maier": "https://en.maier.fr/search?controller=search&s={q}",
    "montredo": "https://www.montredo.com/search?q={q}",
    "worldwatchmuseum": "https://worldwatchmuseum.com/?s={q}",
    "seikoboutique": "https://seikoboutique.es/buscar?q={q}",
    "chrono24": "https://www.chrono24.es/search/index.htm?query={q}",
    "wristler": "https://wristler.eu/search?q={q}",
}
PRUEBAS = [("Seiko", "SRPD55K1"), ("Rolex", "126610LN")]

get = radar.make_session()
for shop, tpl in BUSQUEDA.items():
    for marca, ref in PRUEBAS:
        url = tpl.format(q=re.sub(r"\s+", "+", ref))
        try:
            r = get(url)
            txt = r.text or ""
            ok_ref = bool(re.search(re.escape(ref).replace(r"\.", r"[.\s-]?"), txt, re.I))
            link = radar.best_link(txt, tpl, {"ref": ref, "brand": marca, "descartadas": []}) if r.status_code == 200 else None
            print(shop, ref, getattr(r, "status_code", "?"), len(txt), "ref:" + ("sí" if ok_ref else "no"),
                  "ficha:" + (link or "-"), flush=True)
        except Exception as e:
            print(shop, ref, "error", type(e).__name__, flush=True)
