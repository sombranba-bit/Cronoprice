"""Pruebas del lector de Cronoprice. Se ejecutan antes de cada pasada (ver radar.yml)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import radar  # noqa: E402

R = radar


def ld(o):
    return '<script type="application/ld+json">' + json.dumps(o) + "</script>"


# 1. Emparejamiento por referencia: una ficha con otra referencia no cuenta
ficha = ld({"@type": "Product", "name": "Seiko Prospex SRPD55K1", "mpn": "SRPD55K1",
            "offers": {"@type": "Offer", "price": "289.00", "priceCurrency": "EUR", "availability": "InStock"}})
assert R.extract(ficha, "SRPD55K1", "https://x.es/p") == (289.0, True, "jsonld")
assert R.extract(ficha, "SRPD55K2", "https://x.es/p")[0] is None
assert R.extract(ficha, "SRPD55", "https://x.es/p")[0] is None, "referencia parcial no debe valer"

# 2. Referencia con guiones y mayúsculas distintas
g = ld({"@type": "Product", "name": "G-Shock GA-2100-1A1ER", "offers": {"price": "99.95", "priceCurrency": "EUR"}})
assert R.extract(g, "ga2100-1a1er", "https://x.es/p")[0] == 99.95

# 3. Agotado se marca como tal
agotado = ld({"@type": "Product", "name": "Casio GA-2100-1A1ER", "offers": {"price": "80", "priceCurrency": "EUR", "availability": "OutOfStock"}})
assert R.extract(agotado, "GA-2100-1A1ER", "https://x.es/p") == (80.0, False, "jsonld")

# 4. Respaldo de texto: la referencia y el precio justo detrás
txt = "<p>Reloj Tissot Le Locle T006.407.11.053.00 · 515,00 €</p>"
assert R.extract(txt, "T006.407.11.053.00", "https://x.es/p") == (515.0, None, "texto")

# 5. Sin la referencia en la página, no hay precio
assert R.extract("<p>Otro reloj 99,00 €</p>", "SRPD55K1", "https://x.es/p")[2] == "sin-referencia"

# 6. Plausibilidad frente a la mediana
assert R.plausible(289, 300) and not R.plausible(40, 300) and not R.plausible(900, 300)
assert R.plausible(50, None) and not R.plausible(50, None, "texto")

# 7. Idealo: se descartan réplicas, reacondicionados y otra referencia
R.IDEALO_SHOPS.update({"111": "tienda-a", "222": "tienda-b"})
pg = ('<li class="productOffers-listItem x"><a href="/relocator/relocate?price=250.00&sid=111">'
      '<span class="productOffers-listItemTitle">Seiko SRPD55K1 Prospex</span></a></li>'
      '<li class="productOffers-listItem x"><a href="/relocator/relocate?price=90.00&sid=222">'
      '<span class="productOffers-listItemTitle">Réplica SRPD55K1 € </span></a></li>'
      '<li class="productOffers-listItem x"><a href="/relocator/relocate?price=200.00&sid=222">'
      '<span class="productOffers-listItemTitle">Seiko SRPD55K2 Prospex € </span></a></li>')
assert R.idealo_offers(pg, "SRPD55K1") == {"tienda-a": 250.0}, R.idealo_offers(pg, "SRPD55K1")

# 8. Enlace de búsqueda: solo la ficha con la referencia exacta
res = ('<a href="/p/seiko-srpd55k1-prospex">Seiko SRPD55K1</a>'
       '<a href="/p/seiko-srpd55k2">Seiko SRPD55K2</a>')
assert R.best_link(res, "https://www.idealo.es/resultados.html?q={q}", {"ref": "SRPD55K1", "brand": "Seiko", "descartadas": []}) \
    == "https://www.idealo.es/p/seiko-srpd55k1-prospex"
assert R.best_link("<a href='/p/otro'>Casio GA-2100</a>", "https://www.idealo.es/resultados.html?q={q}",
                   {"ref": "SRPD55K1", "brand": "Seiko", "descartadas": []}) is None

# 9. Limpieza de precios absurdos leídos por el programa
it = {"id": "x", "prices": {"a": {"p": 100, "gh": True}, "b": {"p": 102, "gh": True}, "c": {"p": 250, "gh": True}},
      "history": [{"s": "c", "p": 250}]}
assert R.clean_outliers(it) == ["c"] and "c" not in it["prices"] and it["history"] == []

# 10. Chollometro: solo los hilos de relojes y el respaldo por enlaces
th = '<a href="https://www.chollometro.com/ofertas/reloj-seiko-prospex-555">x</a>'
assert R.parse_chollos(th)[0]["id"] == 555
assert R.WATCH_WORDS.search("Reloj Casio G-Shock") and not R.WATCH_WORDS.search("Zapatillas running")

# 11. Foto: la dirección, nunca un marcador vacío
assert R.product_image(ld({"@type": "Product", "name": "X", "image": ["https://cdn.x/a.jpg"]})) == "https://cdn.x/a.jpg"
assert R.product_image('<meta property="og:image" content="https://cdn.idealo.com/images/product/1/g.jpg">') is None

print("OK: pruebas del lector superadas")
