# Reglas para variantes de referencia

Aplican al rellenar `caja_mm`, `material`, `resistencia_m` y `prices` en `data/relojes.json`.

## 1. Coincidencia exacta (prioridad máxima)
- Un precio solo cuenta como válido si la referencia del anuncio coincide con la del catálogo (`ref`), sin contar espacios.
- Si el anuncio muestra solo el código base sin sufijo de país (p. ej. `GA-2100-7A` frente a `GA-2100-7AER`), se considera coincidencia de modelo y se acepta; se anota en `variante` solo si el sufijo cambia.

## 2. Variante de correa o color (se acepta con marca)
Se acepta un precio de otra referencia cuando cambian SOLO color de esfera, correa o pulsera, y se cumplen las tres condiciones:
- Misma familia y mismo código base (p. ej. `GA-2100-7A7ER` para `GA-2100-7AER`).
- Misma caja (diámetro y material) y mismo movimiento.
- Precio en EUR, con IVA incluido, de tienda oficial o distribuidor autorizado.

Se guarda con `"variante": "<ref del anuncio>"` dentro del precio. Nunca se usa para `caja_mm` si el diámetro varía.

## 3. Variante de talla o tamaño (no se acepta)
- Si cambia el diámetro (p. ej. 40 mm frente a 41 mm), no se acepta para precio ni para caja.
- Si cambia el movimiento o la generación, no se acepta.
- Caja y material sí se pueden copiar de la familia si el diámetro es idéntico y está confirmado por la ficha de la tienda.

## 4. Exclusiones de precio
- Segunda mano, usado, reacondicionado, pre-owned o "sin caja/papeles" sin precio nuevo de referencia.
- Precio en USD, GBP o CHF: se acepta solo si la tienda es oficial o distribuidor autorizado, y se guarda con `"moneda"` (sin convertir). La app lo muestra con una etiqueta y lo deja fuera del mejor precio, de la dispersión y de la bajada, que solo usan EUR.
- "Precio a consultar", "Request PVP" o sin precio público visible.
- Packs, bundles, ofertas con regalo o cupón condicionado.
- Vendedores de marketplace (eBay, Amazon, Chollometro) solo si no hay tienda oficial o distribuidor autorizado; en ese caso se anota `"fuente_tipo": "marketplace"`.

## 5. Trazabilidad y moneda
- Historial: cada entrada no EUR lleva `"moneda"`, para que la bajada de precio no compare libras con euros.
- Cada precio guarda `d` (fecha), `manual: true`, `src` (URL exacta) y, si aplica, `variante`.
- Cada fuente entra en `fuentes`.
- Si la búsqueda no encuentra nada válido, el hueco se queda sin rellenar. No se estima.

## 6. Qué se verifica después
- El usuario comprueba garantía, papeles y estado real de los relojes de segunda mano antes de comprar.
