"""Pruebas del validador de datos. Se ejecutan con: python scraper/test_validar_datos.py"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validar_datos as V  # noqa: E402

BASE = {
    "id": "ej-1", "brand": "Casio", "name": "G-Shock", "ref": "GA-2100-1A1ER",
    "tipo": "Digital", "categoria": "Deportivo", "caja_mm": 45.4,
    "prices": {"tienda": {"d": "2026-11-20", "p": 99.0, "src": "https://x.es/p"}},
    "history": [{"d": "2026-11-20", "p": 99.0, "s": "tienda"}],
    "fuentes": ["https://x.es/p"],
}


def con(**cambios):
    x = copy.deepcopy(BASE)
    x.update(cambios)
    return [x]


# 1. Un reloj correcto no da errores
errores, avisos = V.validar(con())
assert errores == [], errores
assert avisos == [], avisos

# 2. Precio no positivo y fecha inválida
x = con(prices={"tienda": {"d": "2026-13-01", "p": 0, "src": "u"}})
errores, _ = V.validar(x)
assert any("precio de tienda inválido" in e for e in errores), errores
assert any("fecha de tienda inválida" in e for e in errores), errores

# 3. Moneda desconocida; GBP y CHF son válidas
errores, _ = V.validar(con(prices={"tienda": {"d": "2026-11-20", "p": 5, "moneda": "JPY"}}))
assert any("moneda de tienda desconocida" in e for e in errores), errores
errores, _ = V.validar(con(prices={"tienda": {"d": "2026-11-20", "p": 5, "moneda": "GBP"}}))
assert errores == [], errores

# 4. Referencia y id duplicados
dos = con() + con()
errores, _ = V.validar(dos)
assert any("id duplicado" in e for e in errores), errores
assert any("referencia duplicada" in e for e in errores), errores

# 5. Caja fuera de rango, sin caja solo es aviso
errores, _ = V.validar(con(caja_mm=500))
assert any("caja_mm fuera de rango" in e for e in errores), errores
errores, avisos = V.validar(con(caja_mm=None))
assert errores == [], errores
assert any("sin caja_mm" in a for a in avisos), avisos

# 6. Campos obligatorios
x = con()
del x[0]["tipo"]
errores, _ = V.validar(x)
assert any("falta 'tipo'" in e for e in errores), errores

# 7. Historial mal formado
errores, _ = V.validar(con(history=[{"d": "nope", "p": 1}]))
assert any("historial mal formada" in e for e in errores), errores

# 8. Moneda en historial desconocida
errores, _ = V.validar(con(history=[{"d": "2026-11-20", "p": 1, "moneda": "XYZ"}]))
assert any("moneda de historial desconocida" in e for e in errores), errores

# 9. Los datos reales del repositorio pasan el validador
ruta = Path(__file__).resolve().parent.parent / "data" / "relojes.json"
relojes = json.loads(ruta.read_text(encoding="utf-8"))
errores, _ = V.validar(relojes)
assert errores == [], errores[:5]

print("validar_datos: todas las pruebas pasan")
