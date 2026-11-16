"""Prueba de búsqueda: ¿qué tiendas dejan buscar una referencia y devuelven su ficha? (desde el runner)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import radar  # noqa: E402

# tienda -> dominio base
TIENDAS = {
    "miralahora": "https://www.miralahora.com",
    "planetarelojes": "https://www.planetarelojes.com",
    "joyeriapato": "https://www.joyeriapato.com",
    "santamariajoyeros": "https://www.santamariajoyeros.es",
    "joyeriaroberto": "https://www.joyeriaroberto.com",
    "joyeriariver": "https://www.joyeriariver.com",
    "larrabe": "https://larrabe.com",
    "relojeriajoyeria": "https://www.relojeriajoyeria.com",
    "elegance": "https://www.elegance.com.es",
    "relojes-japoneses": "https://relojes-japoneses.com",
    "smjoyeros": "https://smjoyeros.es",
    "joyeriadeluxe": "https://www.joyeriadeluxe.com",
    "pepewatch": "https://pepewatch.com",
}
# patrones de búsqueda habituales (Shopify, PrestaShop, WooCommerce, Magento, propios)
PATRONES = [
    "/search?q={q}", "/buscar?q={q}", "/?s={q}", "/buscar?s={q}", "/es/buscar?s={q}",
    "/buscar?controller=search&s={q}", "/es/buscar?controller=search&s={q}",
    "/search?controller=search&s={q}", "/busqueda?s={q}", "/es/busqueda?s={q}",
]
PRUEBAS = [("Seiko", "SRPD55K1"), ("Citizen", "BN0150-61E")]

get = radar.make_session()
for shop, base in TIENDAS.items():
    for patron in PATRONES:
        ok_pat = False
        for marca, ref in PRUEBAS:
            url = base + patron.format(q=re.sub(r"\s+", "+", ref))
            try:
                r = get(url)
                txt = r.text or ""
                ok_ref = bool(re.search(re.escape(ref).replace(r"\.", r"[.\s-]?"), txt, re.I))
                link = None
                if r.status_code == 200:
                    link = radar.best_link(txt, base + "/", {"ref": ref, "brand": marca, "descartadas": []})
                if link or (r.status_code == 200 and ok_ref):
                    ok_pat = True
                print(shop, patron, ref, getattr(r, "status_code", "?"), len(txt),
                      "ref:" + ("sí" if ok_ref else "no"), "ficha:" + (link or "-"), flush=True)
            except Exception as e:
                print(shop, patron, ref, "error", type(e).__name__, flush=True)
        if ok_pat:
            print("  >>> FUNCIONA:", shop, patron, flush=True)
