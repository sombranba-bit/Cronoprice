"""Pruebas del vigilante de tiendas bloqueadas. Se ejecutan con: python scraper/test_alertas_tiendas.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import alertas_tiendas as A  # noqa: E402

# La racha sube si la pasada fue mayoritariamente bloqueada y se reinicia si no
r = A.actualizar({"x": 2}, {"x": {"ok": 0, "bloqueada": 3}, "y": {"ok": 5, "bloqueada": 1}})
assert r == {"x": 3, "y": 0}, r

# Empate no cuenta como bloqueo
assert A.actualizar({"z": 1}, {"z": {"ok": 2, "bloqueada": 2}}) == {"z": 0}

# Solo avisa a partir del umbral
assert A.avisos({"x": A.UMBRAL - 1, "y": A.UMBRAL}) == ["y"]

# Una tienda pausada suma pasada bloqueada; una no consultada conserva su racha
r = A.actualizar({"p": 3, "q": 5}, {"p": {"pausada": 1}})
assert r == {"p": 4, "q": 5}, r

print("alertas_tiendas: todas las pruebas pasan")
