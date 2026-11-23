"""Valida data/relojes.json antes de publicar una pasada.

Uso: python scraper/validar_datos.py [ruta]
Sale con código 1 si hay errores (la pasada no debe publicar datos rotos).
Los avisos (warnings) no bloquean: son huecos conocidos del catálogo.
"""
import datetime
import json
import os
import sys

MONEDAS = {"EUR", "GBP", "CHF", "USD"}
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RUTA_POR_DEFECTO = os.path.join(RAIZ, "data", "relojes.json")
CAMPOS_OBLIGATORIOS = ("id", "brand", "name", "ref", "tipo", "categoria")


def _fecha_valida(texto):
    try:
        datetime.date.fromisoformat(str(texto))
        return True
    except (TypeError, ValueError):
        return False


def validar(relojes):
    """Devuelve (errores, avisos) como listas de texto."""
    errores, avisos = [], []
    if not isinstance(relojes, list):
        return ["el catálogo no es una lista"], avisos

    ids, refs = set(), {}
    for i, x in enumerate(relojes):
        etiqueta = f"#{i} ({x.get('ref', '?')})" if isinstance(x, dict) else f"#{i}"
        if not isinstance(x, dict):
            errores.append(f"{etiqueta}: no es un objeto")
            continue

        for campo in CAMPOS_OBLIGATORIOS:
            if not x.get(campo):
                errores.append(f"{etiqueta}: falta '{campo}'")

        if x.get("id") in ids:
            errores.append(f"{etiqueta}: id duplicado '{x.get('id')}'")
        ids.add(x.get("id"))
        if x.get("ref"):
            if x["ref"] in refs:
                errores.append(f"{etiqueta}: referencia duplicada '{x['ref']}'")
            refs[x["ref"]] = True

        caja = x.get("caja_mm")
        if caja is None:
            avisos.append(f"{etiqueta}: sin caja_mm")
        elif not isinstance(caja, (int, float)) or not 10 <= caja <= 80:
            errores.append(f"{etiqueta}: caja_mm fuera de rango ({caja!r})")

        prices = x.get("prices") or {}
        if not isinstance(prices, dict):
            errores.append(f"{etiqueta}: 'prices' no es un objeto")
            prices = {}
        for tienda, v in prices.items():
            if not isinstance(v, dict):
                errores.append(f"{etiqueta}: precio de {tienda} no es un objeto")
                continue
            p = v.get("p")
            if not isinstance(p, (int, float)) or p <= 0:
                errores.append(f"{etiqueta}: precio de {tienda} inválido ({p!r})")
            if not _fecha_valida(v.get("d")):
                errores.append(f"{etiqueta}: fecha de {tienda} inválida ({v.get('d')!r})")
            moneda = v.get("moneda", "EUR")
            if moneda not in MONEDAS:
                errores.append(f"{etiqueta}: moneda de {tienda} desconocida ({moneda!r})")

        historial = x.get("history") or []
        for h in historial:
            if not isinstance(h, dict) or not _fecha_valida(h.get("d")) or not isinstance(h.get("p"), (int, float)):
                errores.append(f"{etiqueta}: entrada de historial mal formada ({h!r})")
                break
            if h.get("moneda") and h["moneda"] not in MONEDAS:
                errores.append(f"{etiqueta}: moneda de historial desconocida ({h['moneda']!r})")

        fuentes = x.get("fuentes")
        if fuentes is not None and not (isinstance(fuentes, list) and all(isinstance(f, str) and f for f in fuentes)):
            errores.append(f"{etiqueta}: 'fuentes' debe ser una lista de textos no vacíos")

        if prices and not x.get("fuentes"):
            avisos.append(f"{etiqueta}: tiene precios y no tiene fuentes")
        if prices and not x.get("history"):
            avisos.append(f"{etiqueta}: tiene precios y no tiene historial")
        if not prices:
            avisos.append(f"{etiqueta}: sin precio")

    return errores, avisos


def main(argv):
    ruta = argv[1] if len(argv) > 1 else RUTA_POR_DEFECTO
    with open(ruta, encoding="utf-8") as f:
        relojes = json.load(f)
    errores, avisos = validar(relojes)
    for linea in errores:
        print("ERROR", linea)
    for linea in avisos:
        print("aviso", linea)
    total = len(relojes) if isinstance(relojes, list) else 0
    print(f"{total} referencias, {len(errores)} errores, {len(avisos)} avisos")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
