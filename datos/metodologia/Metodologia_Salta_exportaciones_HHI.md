# Metodología — Concentración de las exportaciones de Salta (índice HHI)

Dataset: `Salta_exportaciones_HHI_rubro_destino_anual.csv`
Fecha de elaboración: 2026-09-20.

## Fuente

- **Dataset de origen:** `Salta_exportaciones_INDEC_rubro_destino_desde_2021.csv`, documentado en
  `Metodologia_Salta_exportaciones_INDEC_rubro_destino.md`.
- **Fuente primaria:** INDEC — Comercio Exterior (COMEX), base anual por provincia de origen,
  <https://comex.indec.gob.ar/#/database>.
- **Este proceso no descarga nada.** Es un cálculo derivado sobre un dataset del proyecto. Toda la
  trazabilidad hasta el INDEC está en la metodología del dataset de origen.

## Qué mide

El **índice de Herfindahl-Hirschman normalizado** de la canasta exportadora:

```
HHI  = Σ sᵢ²                        sᵢ = participación de la categoría i en el FOB del año
HHI* = (HHI − 1/n) / (1 − 1/n)      n  = categorías con FOB > 0 en ese año
```

`HHI*` vale **0** cuando todas las categorías pesan exactamente lo mismo (máxima diversificación
posible dado `n`) y tiende a **1** cuando una sola concentra todo. La normalización descuenta el
piso `1/n` que tiene el HHI sin normalizar sólo por el hecho de haber un número finito de
categorías, lo que hace comparables años con distinto `n`.

Se calcula sobre **valor FOB en dólares**, no sobre volumen. Con `peso_neto_kg` el resultado sería
otro y mediría otra cosa.

## Cobertura y unidad de análisis

- Provincia de origen **Salta**, años **2021 a 2025**.
- Una fila por **año × dimensión**: 5 años × 2 dimensiones = **10 filas**.
- Dos dimensiones:
  - **Rubro** — qué se exporta. 27 a 31 categorías según el año.
  - **País de destino** — a quién se le vende. 129 a 139 países según el año.

### Por qué rubro y no capítulo NCM

El pedido original hablaba de "capítulo". **La apertura por capítulo NCM no existe con
desagregación provincial.** La base provincial del INDEC (`Datos_origen_2002_2025.xlsb`) llega
hasta el **rubro**; la apertura por posición arancelaria está sólo en los archivos de alcance
**nacional** del mismo `.zip` (`expona25.csv`), que no traen provincia de origen. Está documentado
en la metodología del dataset de origen, sección "Rubro ≠ posición arancelaria". El rubro es el
máximo detalle de producto disponible para Salta.

## Esquema del CSV

Separador `,`; decimal `.`; sin separador de miles; codificación **UTF-8 con BOM** (`utf-8-sig`).

| Columna | Tipo | Descripción |
|---|---|---|
| `provincia` | texto | Siempre `Salta`. |
| `anio` | entero | 2021–2025. |
| `dimension` | texto | `Rubro` o `País de destino`. |
| `n_categorias` | entero | Categorías con FOB > 0 ese año. **No es constante.** |
| `hhi` | decimal | Σ sᵢ² sin normalizar, 6 decimales. |
| `hhi_normalizado` | decimal | El índice, escala 0–1, 6 decimales. |
| `hhi_normalizado_base100` | decimal | El mismo índice ×100, 4 decimales. |
| `top1_categoria` | texto | Categoría de mayor FOB ese año. |
| `top1_share_pct` | decimal | Su participación en el FOB total, 1 decimal. |
| `fob_usd_total` | decimal | FOB total del año: el denominador de las participaciones. |

### Por qué se publican dos escalas del mismo índice

El front-end del Monitor formatea los tooltips con `maximumFractionDigits: 0`
(`sitio-indicadores/assets/js/charts.js`), de modo que un valor como `0,1242` se renderiza como
**`0`**; el eje Y usa un decimal y mostraría `0,1`. No hay forma de declarar decimales por gráfico.
Todos los índices ya publicados en el Monitor están en escala 0–100 por esta razón. Se conservan
las dos columnas: `hhi_normalizado` es fiel a la fórmula tal como se pidió, y
`hhi_normalizado_base100` es la que el tablero puede graficar.

## Transformaciones aplicadas

1. Lectura con `encoding='utf-8-sig'` y `dtype={'rubro_cod': str}`. **`rubro_cod` es texto**
   (`104A`, `106ZD`, `212AE`): leerlo como número lo destruye.
2. Se descartan filas sin año, sin país o sin FOB, y las de `fob_usd <= 0` (hoy: **ninguna**).
3. Agregación del FOB por **código** —`rubro_cod`, `pais_cod`— y no por descripción: el código es
   la clave estable. Se verificó que ningún código tiene más de una descripción en el período.
4. Participaciones sobre el total del año, y aplicación de la fórmula.
5. `n` es el número de categorías **observadas en ese año**, no una constante. Es la definición
   estándar y la que implica la fórmula pedida, pero tiene una consecuencia: el denominador de la
   normalización cambia de un año a otro.

No se imputa, rellena ni suaviza nada. No se reparten los agregados confidenciales.

## Resultados

| Año | Rubro: n | Rubro HHI | **Rubro HHI\*** | Categoría principal (rubro) |
|---|---|---|---|---|
| 2021 | 27 | 0,156681 | **0,124246** | Legumbres (24,6 %) |
| 2022 | 31 | 0,135845 | **0,107040** | Maíz (22,2 %) |
| 2023 | 31 | 0,136793 | **0,108020** | Legumbres (22,3 %) |
| 2024 | 29 | 0,137181 | **0,106366** | MOI (confidencial) (23,7 %) |
| 2025 | 29 | 0,140214 | **0,109507** | MOI (confidencial) (26,5 %) |

| Año | Destino: n | Destino HHI | **Destino HHI\*** | Destino principal |
|---|---|---|---|---|
| 2021 | 139 | 0,057874 | **0,051047** | Estados Unidos (17,2 %) |
| 2022 | 133 | 0,064990 | **0,057906** | Estados Unidos (18,7 %) |
| 2023 | 129 | 0,069032 | **0,061758** | Estados Unidos (21,0 %) |
| 2024 | 132 | 0,084112 | **0,077121** | Estados Unidos (23,3 %) |
| 2025 | 139 | 0,090554 | **0,083964** | Estados Unidos (23,7 %) |

**Lectura.** La concentración **por producto se mantiene plana** en torno a 0,11 durante los cinco
años — pero ver la advertencia sobre el secreto estadístico, que afecta justamente a esta serie.
La concentración **por destino sube 65 %** (0,051 → 0,084), de forma sostenida y sin ningún año en
contra, traccionada por Estados Unidos, que pasa de 17,2 % a 23,7 % del valor exportado. En niveles
absolutos ambos índices son bajos (0,08 sobre un máximo de 1): Salta no depende de un solo producto
ni de un solo mercado. Lo relevante es la **dirección** de la serie de destinos.

## Verificación

1. **Implementación independiente.** Se recalcularon los 20 valores con una segunda implementación
   —pivot `año × categoría` y álgebra con `numpy`, sin el `groupby` del script—. Diferencia máxima
   sobre `hhi_normalizado`, ambos redondeados a 6 decimales: **0**. `n_categorias` coincide en los
   10 casos.
2. **Totales contra la fuente.** El `fob_usd_total` de cada año coincide **exactamente** con los
   totales publicados en `Metodologia_Salta_exportaciones_INDEC_rubro_destino.md` (1.262.871.152 en
   2021; 1.333.363.413 en 2022; 1.118.753.887 en 2023; 1.123.823.718 en 2024; 1.447.687.147 en
   2025). Además el total es idéntico entre las dos dimensiones del mismo año, como debe ser: las
   dos reparten la misma torta.
3. **Casos límite** sobre datos sintéticos:

   | Caso | HHI* obtenido | Esperado |
   |---|---|---|
   | 2, 5, 29 y 139 categorías iguales | 0,0000000000 | 0 |
   | Una categoría domina (1e9 contra 29 de 1 USD) | 0,9999999400 | → 1 |
   | Reparto 90/10 entre dos categorías | 0,6400000000 | 0,64 |

4. **Chequeos internos del script**, que abortan la corrida: participaciones que no suman 1
   (tolerancia 1e-9), índice fuera de `[0, 1]`, o un año con una sola categoría (la fórmula
   dividiría por cero).
5. **Relectura de control** del CSV escrito con `utf-8-sig`: 10×10, **0 nulos**, las 6 columnas
   numéricas releen como numérico, 0 valores con coma decimal, BOM presente,
   `hhi_normalizado_base100 = hhi_normalizado × 100` en las 10 filas.
6. **Reproducibilidad.** Se extrajo el bloque `python` del runbook —se verificó que haya
   exactamente **uno**—, se corrió en carpeta limpia y el CSV resultante es **md5-idéntico** al
   entregado: `18525d7981ea7b7944912d31cf434bc6`.

## Incidencias

| Incidencia | Veredicto |
|---|---|
| Filas con `fob_usd <= 0` | **Ninguna.** El filtro queda igual como defensa. |
| Códigos con más de una descripción | **Ninguno**, en ninguna de las dos dimensiones. |
| Años con una sola categoría (división por cero) | **Ninguno.** El mínimo es 27 (rubro) y 129 (destino). |
| `HHI*` fuera de `[0, 1]` | **Ninguno.** |
| Negativo de punto flotante con categorías equidistribuidas | **Observado en prueba sintética** (−1e-17 con 29 categorías iguales). Se recorta a 0 con tolerancia 1e-9 antes de validar el rango, para que un dato real casi equidistribuido no aborte la corrida. |
| Saltos de orden de magnitud | **Ninguno.** La mayor variación interanual es **+24,9 %** (destino, 2023→2024), que no es un artefacto: acompaña el salto de Estados Unidos del 21,0 % al 23,3 % del FOB. La serie por rubro se mueve dentro de ±14 %. |

## Supuestos y limitaciones

### El secreto estadístico condiciona la serie por rubro

Es la limitación principal y no es menor. El INDEC agrupa bajo códigos `x9899` las operaciones cuyo
producto no publica. En Salta esa masa **creció de forma abrupta**:

| Año | % del FOB bajo secreto estadístico |
|---|---|
| 2021 | 33,5 % |
| 2022 | 20,3 % |
| 2023 | 21,1 % |
| 2024 | **46,0 %** |
| 2025 | **43,4 %** |

En 2024 y 2025 la categoría más grande de la canasta exportadora **es un agregado confidencial**
(`39899`, MOI confidencial: 23,7 % y 26,5 %). Esto tiene dos consecuencias:

1. **El índice está inflado.** Agrupar en un solo bucket lo que son varios productos distintos
   aumenta Σ sᵢ². El HHI* por rubro es un **techo**, no una medida neutral.
2. **La serie no es estrictamente comparable entre años**, porque el grado de agregación cambia. El
   salto de 20 % a 46 % entre 2023 y 2024 es un cambio en la *publicación*, no necesariamente en la
   economía. **Un movimiento de esta serie debe atribuirse primero a la política de
   confidencialidad del INDEC y sólo después a la estructura exportadora real.**

**Sensibilidad medida.** Se calculó la variante que excluye los rubros confidenciales y renormaliza
sobre el total conocido. Da otro nivel y otra tendencia:

| Año | HHI* incluyendo confidencial (publicado) | HHI* excluyendo confidencial |
|---|---|---|
| 2021 | 0,1242 | 0,2346 |
| 2022 | 0,1070 | 0,1628 |
| 2023 | 0,1080 | 0,1632 |
| 2024 | 0,1064 | 0,1746 |
| 2025 | 0,1095 | 0,1471 |

La serie publicada es **casi plana**; la alternativa **cae con fuerza** (−37 % en el período).
Ninguna de las dos es insesgada: la publicada trata como un producto lo que son varios; la
alternativa descarta hasta el 46 % del valor exportado y renormaliza el resto, lo que también
infla las participaciones que quedan. Se optó por publicar la que **usa el 100 % del valor
exportado** y es la lectura literal de la clasificación tal como el INDEC la publica. La variante
se deja documentada acá para que se sepa cuán sensible es la conclusión al tratamiento; **no debe
leerse la serie por rubro sin esta tabla a la vista**.

### La serie por destino no tiene este problema

Las filas confidenciales **conservan el país de destino**: sólo se oculta el producto. La apertura
por país está completa y el HHI* por destino no sufre ninguna distorsión por secreto estadístico.
Es la más sólida de las dos series, y es además la que se mueve.

### Otras limitaciones

- **`n` no es constante** (27–31 en rubro, 129–139 en destino). La normalización lo corrige en
  parte —para eso existe—, pero el denominador cambia entre años.
- **El índice se calcula sobre valor FOB.** Una canasta diversificada en volumen pero concentrada
  en valor da un HHI alto, y es correcto que así sea; pero no es una medida de diversificación
  física.
- **"Rubro" no es "producto".** Un rubro agrupa posiciones arancelarias heterogéneas, y algunos son
  cajones de sastre ("Resto de MOA", "Resto de productos primarios"). El índice mide concentración
  *de la clasificación del INDEC*, que es la única disponible con apertura provincial.
- **Un país no es un mercado.** La concentración por destino ignora que varios países puedan
  pertenecer al mismo bloque o responder al mismo ciclo. Una apertura por continente daría una
  concentración mayor.
- **Cinco años son pocos** para hablar de tendencia estructural. La serie de destinos es monótona
  creciente en los cinco, lo que le da fuerza, pero conviene recalcularla cada año antes de
  sostener la conclusión.
