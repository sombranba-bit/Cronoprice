"""Mantiene data/relojes.json pequeño: recorta el historial de precios.

Reglas (solo se aplican si el archivo supera LIMITE_BYTES):
- se conserva un único precio por tienda y día (el último leído ese día);
- se descartan las entradas de más de RETENCION_DIAS días.
El precio actual de cada tienda (prices) nunca se toca.

Uso: python scraper/compactar_historial.py
"""
import datetime
import json
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RUTA = os.path.join(RAIZ, "data", "relojes.json")
LIMITE_BYTES = 1_000_000
RETENCION_DIAS = 365


def compactar(hist, hoy):
    """Devuelve el historial recortado: un precio por tienda y día, sin lo más antiguo que RETENCION_DIAS."""
    corte = hoy - datetime.timedelta(days=RETENCION_DIAS)
    ultimo = {}
    for h in hist or []:
        try:
            dia = datetime.date.fromisoformat(h["d"])
        except (KeyError, TypeError, ValueError):
            continue
        if dia < corte:
            continue
        # clave por tienda, moneda y día: no se pisan entradas de monedas distintas
        ultimo[(h.get("s"), h.get("moneda", "EUR"), dia)] = h
    return sorted(ultimo.values(), key=lambda h: (h["d"], str(h.get("s"))))


def main():
    tamano = os.path.getsize(RUTA)
    if tamano <= LIMITE_BYTES:
        print(f"historial sin cambios ({tamano} bytes, límite {LIMITE_BYTES})")
        return 0
    with open(RUTA, encoding="utf-8") as f:
        relojes = json.load(f)
    hoy = datetime.date.today()
    antes = despues = 0
    for x in relojes:
        h0 = x.get("history") or []
        antes += len(h0)
        x["history"] = compactar(h0, hoy)
        despues += len(x["history"])
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(relojes, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"historial compactado: {antes} -> {despues} entradas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
