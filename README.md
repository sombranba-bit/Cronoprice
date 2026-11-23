# Cronoprice

Comparador y rastreador de precios de relojes en España: relojes clásicos y smartwatches, con los chollos de relojes de Chollometro. Funciona solo en GitHub, sin servidor:

- **La página** (`index.html` + `app/` + `maquetas/`) se publica con GitHub Pages y lee `data/*.json`.
- **La pasada** (`.github/workflows/radar.yml`) corre cada 30 minutos, revisa los relojes que llevan más tiempo sin revisar, guarda precio y foto y hace commit en `data/`.
- Basado en la arquitectura de [radar-perfumes](https://github.com/sombranba-bit/radar-perfumes) (Fragans): ver `DESIGN.md` para el sistema visual.

## Estructura

```
index.html                  portada (SPA sin frameworks)
app/cronoprice.css          sistema visual (tokens de DESIGN.md, paleta azul tinta)
app/logica.js                cálculos puros (precio mínimo, dispersión, bajada) sin DOM
app/cronoprice.js           vistas: inicio, catálogo con filtros, ficha, chollos, guardados
data/relojes.json           catálogo: ref, marca, categoría, tipo, precios, historial, fotos
data/chollos.json           chollos de relojes (Chollometro)
data/estado.json            resumen de la última pasada por tienda
scraper/radar.py            lector de precios (una pasada)
scraper/test_radar.py       pruebas del lector (se ejecutan antes de cada pasada)
scraper/diagnostico.py      prueba de acceso a las tiendas
scraper/validar_datos.py    valida relojes.json antes de publicar
scraper/compactar_historial.py recorta el historial si el archivo crece
scraper/alertas_tiendas.py  avisa de tiendas bloqueadas pasada tras pasada
.github/workflows/radar.yml       pasada cada 30 min (input "relojes": 70 normal)
.github/workflows/diagnostico.yml prueba manual de tiendas
```

## Cómo empareja los precios

Cada reloj se identifica por su **referencia del fabricante** (`ref`, p. ej. `SRPD55K1`, `GA-2100-1A1ER`), no por el nombre. La referencia admite guiones, puntos y espacios, y no empareja con otra más larga (`SRPD55` no vale por `SRPD55K1`). Si la ficha no menciona la referencia, el precio se descarta.

Controles de calidad:
- precio fuera de la mediana de las demás tiendas (0,55× a 1,5×, o 1,8× en tiendas oficiales) se descarta y se cuenta como dudoso;
- las ofertas de Idealo con «réplica», «reacondicionado», «segunda mano», «outlet», «estuche» o «lote» se ignoran;
- un precio leído por el programa que sale muy alto frente a las demás tiendas se quita del historial.

## Montarlo (una vez)

1. Crear el repositorio `cronoprice` en GitHub, público (Pages gratis solo funciona en repos públicos).
2. Subir todo el contenido de esta carpeta, incluida `.github`.
3. **Settings → Pages**: rama `main`, carpeta `/ (root)`.
4. **Settings → Actions → General → Workflow permissions**: **Read and write permissions**.
5. **Actions → Diagnóstico de tiendas → Run workflow** para ver qué tiendas dejan entrar.
6. **Actions → Pasada de precios de relojes → Run workflow** para lanzar la primera pasada.

## Pendiente antes de dar la pasada por buena

- **Catálogo.** 206 referencias, todas con caja y 201 con precio. Las 5 que faltan tienen su motivo en `sin_precio_motivo`. Cada referencia nueva necesita al menos dos fuentes de fabricante o tienda antes de añadirse.
- **Tiendas.** Solo Idealo está activa en la búsqueda. Para cada tienda hay que comprobar con el diagnóstico que deja leer desde GitHub antes de añadirla a `SEARCH`.
- **Amazon.** Está marcada como `MANUAL` (no se lee automáticamente). Sus condiciones de uso prohíben el scraping; si se quiere su precio, hay que usar una fuente autorizada.
- **Idealo como puerta trasera.** `IDEALO_SHOPS` se llena con los números de tienda de Idealo. Antes de activarlo conviene revisar las condiciones de uso de Idealo y de cada tienda.
- **Chollometro.** La URL `categorias/relojes` está sin comprobar; el diagnóstico la revisa.
- **Ficha técnica.** El bloque olfativo de Fragans se sustituye por una ficha técnica (movimiento, calibre, diámetro, grosor, hermeticidad, cristal, peso). Todavía no está en la web.
- **Fotos.** Solo se guarda la dirección de la foto; nunca se copia el archivo.

## Pruebas

```
pip install -r requirements.txt
python3 scraper/test_radar.py
python3 scraper/test_validar_datos.py
python3 scraper/test_compactar_historial.py
python3 scraper/test_alertas_tiendas.py
node app/test_logica.js
```

En cada pasada (radar.yml) se ejecutan estas pruebas, se recorta el historial si `relojes.json` supera 1 MB, se valida el catálogo (un error bloquea la publicación) y se avisa si una tienda lleva 3 pasadas seguidas bloqueada (`data/bloqueos.json`).
