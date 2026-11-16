# DESIGN.md · Cronoprice

Sistema visual de Cronoprice. Hereda el de Fragans (ver DESIGN.md de radar-perfumes) con estos cambios:

- **Nombre y lema:** Cronoprice · «Comparador de precios de relojes».
- **Logo:** lupa con una esfera de reloj dentro (SVG 28×28, trazo `currentColor` 2 px, aguja en `--accent`).
- **Titular de portada:** «Encuentra tu reloj *al mejor precio*».
- **Color de marca:** azul tinta `#2b4a9b` (claro) y `#9fb6ec` (oscuro). Verde solo para ahorro y bajadas; un único color de acento.
- **Tipografía, espacio, radios, sombras y movimiento:** iguales a Fragans (Fraunces para títulos, Geist para la interfaz, `--r-lg:18px`, curva `cubic-bezier(.22,1,.36,1)`).
- **Ficha:** la ficha técnica sustituye al bloque olfativo. Pendiente de implementar.
- **Categorías:** clásicos y smartwatches en lugar de familias de perfume.

## Tokens

Claro: `--bg #f7f2f2`, `--surface #fff`, `--surface-2 #f0e8e8`, `--text #141311`, `--muted #69655d`, `--faint #6e6a62`, `--accent #2b4a9b`, `--pos #17663f`, `--neg #a12a22`.

Oscuro: `--bg #120c0d`, `--surface #1c1516`, `--text #f1eee8`, `--muted #a7a196`, `--accent #9fb6ec`, `--pos #7fd6a3`, `--neg #f08a7f`.

`--faint` se ha oscurecido frente a Fragans (`#8f8a80` daba 3,5:1 sobre blanco, por debajo de WCAG AA 4,5:1).

## Reglas

- Sin emojis, sin etiquetas en mayúsculas espaciadas, sin degradados de color sobre superficies.
- Cada precio lleva la fecha en que se leyó («hace 2 días»).
- Sin cifras inventadas: si un dato no existe, no se muestra.
