"""Vigila las tiendas que se bloquean pasada tras pasada.

Lee data/estado.json (resumen de la última pasada) y mantiene data/bloqueos.json con
cuántas pasadas seguidas ha sido bloqueada cada tienda. Una pasada cuenta como
bloqueada si hubo más consultas bloqueadas que correctas. Si la racha llega al
umbral, imprime un aviso que GitHub Actions muestra en el resumen de la ejecución.

Uso: python scraper/alertas_tiendas.py   (no falla nunca: es solo un aviso)
"""
import json
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ESTADO = os.path.join(RAIZ, "data", "estado.json")
BLOQUEOS = os.path.join(RAIZ, "data", "bloqueos.json")
UMBRAL = 3  # pasadas seguidas bloqueadas antes de avisar


def actualizar(racha_previa, tiendas):
    """Devuelve la nueva racha por tienda: sube si la pasada fue mayoritariamente bloqueada."""
    nueva = dict(racha_previa)                 # tiendas no consultadas en la pasada se conservan
    for tienda, st in tiendas.items():
        previa = int(racha_previa.get(tienda, 0))
        if st.get("pausada"):                  # una pausa cuenta como pasada bloqueada
            nueva[tienda] = previa + 1
            continue
        ok = int(st.get("ok", 0))
        bloqueada = int(st.get("bloqueada", 0))
        nueva[tienda] = previa + 1 if bloqueada > ok else 0
    return nueva


def avisos(racha):
    return [t for t, n in sorted(racha.items()) if n >= UMBRAL]


def main():
    with open(ESTADO, encoding="utf-8") as f:
        tiendas = json.load(f).get("tiendas", {})
    previa = {}
    if os.path.exists(BLOQUEOS):
        with open(BLOQUEOS, encoding="utf-8") as f:
            previa = json.load(f)
    racha = actualizar(previa, tiendas)
    with open(BLOQUEOS, "w", encoding="utf-8") as f:
        json.dump(racha, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    for t in avisos(racha):
        print(f"::warning title=Tienda bloqueada::{t} lleva {racha[t]} pasadas seguidas bloqueada")
    print(f"tiendas vigiladas: {len(racha)}; con aviso: {len(avisos(racha))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
