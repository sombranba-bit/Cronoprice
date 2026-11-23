"""Pruebas de la compactación del historial. Se ejecutan con: python scraper/test_compactar_historial.py"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compactar_historial as C  # noqa: E402

HOY = datetime.date(2026, 11, 23)

hist = [
    {"d": "2026-11-20", "p": 100.0, "s": "tienda"},
    {"d": "2026-11-20", "p": 98.0, "s": "tienda"},   # mismo día y tienda: se queda la última
    {"d": "2026-11-20", "p": 150.0, "s": "otra"},
    {"d": "2026-11-20", "p": 10.0, "s": "tienda", "moneda": "GBP"},  # otra moneda: se conserva
    {"d": "2024-01-01", "p": 50.0, "s": "tienda"},     # más de un año: fuera
    {"d": "nope", "p": 1.0, "s": "tienda"},            # fecha mala: fuera
]
r = C.compactar(hist, HOY)
assert len(r) == 3, r
assert [h["p"] for h in r if h["s"] == "tienda" and "moneda" not in h] == [98.0], r
assert any(h.get("moneda") == "GBP" for h in r), r
assert all(h["d"] != "2024-01-01" for h in r), r
assert C.compactar([], HOY) == []

print("compactar_historial: todas las pruebas pasan")
