# Metodología — Bosque nativo, desmonte y regeneración en Salta (MapBiomas Argentina)

Módulo: `bosques/` · Script: `mapbiomas_bosques_salta.py` · Fecha de obtención: 2026-11-04.

## Resultado en una línea

Entre 1987 y 2021 Salta pasó de **9,22 a 7,44 millones de hectáreas de bosque** (−19 %).
El desmonte bruto promedió **73.850 ha/año en 1998-2007** y **60.855 ha/año en 2008-2021**:
bajó un 18 % después del Ordenamiento Territorial de Bosques Nativos, **pero no se detuvo**.
Cuatro departamentos —Anta, General José de San Martín, Orán y Rivadavia— concentran el
**82 %** del desmonte de todo el período. Los años **2022-2025 son provisorios** y no deben
usarse para conclusiones (ver §6).

## 1. Fuente

| Producto | Origen | Uso |
|---|---|---|
| Estadísticas por provincia, Colección 3 | <https://argentina.mapbiomas.org/wp-content/uploads/sites/8/2026/09/Estadisticas_por_Provincia.zip> (publicado 2026-09-23), hoja `Salta Hist` | Serie oficial de superficie por clase, 1985-2025 |
| Cobertura y uso, Colección 3 | Earth Engine: `projects/mapbiomas-public/assets/argentina/lulc/collection3/mapbiomas_argentina_collection3_coverage_v1` | Stock de bosque por departamento |
| Desmonte y vegetación secundaria (anual codificado), Colección 3 | Earth Engine: `…/mapbiomas_argentina_collection3_deforestation_secondary_vegetation_annual_v1` | Desmonte y regeneración por departamento |
| Límites departamentales | Earth Engine: `FAO/GAUL/2025/level2`, `GAUL1_NAME = "Salta"` | 23 departamentos |

Licencia: los datos de MapBiomas son públicos y gratuitos, sujetos a citación (CC BY 4.0).
Citar como *Proyecto MapBiomas Argentina — Colección 3 de la serie anual de mapas de
cobertura y uso del suelo*.

**Por qué no alcanza la planilla oficial.** Trae solo el **stock** por clase. La diferencia de
stock entre dos años es el cambio **neto**: 10.000 ha desmontadas y 4.000 ha regeneradas
aparecen como −6.000 ha. El desmonte es un flujo **bruto**, y solo se obtiene del producto de
transiciones, que no está tabulado por provincia: hay que reducirlo en Earth Engine.

Se intentó también la planilla de la Colección 2, que según la página incluye transiciones:
la URL de descarga devuelve **HTTP 403**.

## 2. Cálculo

**Productos derivados.** La imagen anual codificada guarda, para cada año `t`,
`transición(t) × 100 + cobertura(t−1)`. El script le agrega la cobertura de `t` y forma un
código único por píxel:

```
código = transición(t) × 10000 + cobertura(t−1) × 100 + cobertura(t)
```

y suma `ee.Image.pixelArea()` agrupando por ese código, por departamento y año, en la
**proyección nativa del ráster** (EPSG:4326, ~30 m). Reproyectar a una escala fija hacía que
la reducción provincial excediera el tiempo de cómputo sincrónico; en la proyección nativa el
departamento más grande tarda 3 s por año.

**Transiciones del producto** (leyenda del propio asset): 1 antrópico · 2 vegetación primaria ·
3 vegetación secundaria · 4 supresión de vegetación primaria · 5 recuperación a vegetación
secundaria · 6 supresión de vegetación secundaria · 7 otras transiciones.

**Leyenda de cobertura.** Bosque = códigos **3, 4 y 6** (bosques cerrados, abiertos e
inundables). Otra vegetación natural = 11, 12, 34, 63, 66, 73, 77. La correspondencia
código → nombre **no está en la documentación del asset**; se dedujo de los datos y se
verificó contra la planilla oficial (§4, verificación 1).

**Métricas** (`MapBiomas_Bosques_Salta_departamento_1987-2025.csv`):

| Métrica | Definición |
|---|---|
| `superficie_bosque_ha` | Cobertura de `t` ∈ bosque |
| `desmonte_bosque_ha` | Transición 4 o 6 **y** cobertura de `t−1` ∈ bosque. Conversión de bosque a uso antrópico |
| `desmonte_bosque_primario_ha` | Ídem, solo transición 4 (bosque que nunca había sido desmontado en la serie) |
| `desmonte_bosque_secundario_ha` | Ídem, solo transición 6 (bosque regenerado que se vuelve a desmontar) |
| `perdida_otra_vegetacion_natural_ha` | Transición 4 o 6 con cobertura previa en vegetación natural no boscosa |
| `regeneracion_bosque_ha` | Transición 5 **y** cobertura de `t` ∈ bosque |
| `regeneracion_vegetacion_natural_ha` | Transición 5, cualquier cobertura natural |
| `superficie_vegetacion_secundaria_ha` | Transición 3 o 5: stock de vegetación que se recuperó sobre uso antrópico |
| `bosque_perdido_ha` | Cobertura `t−1` ∈ bosque y `t` ∉ bosque, **por cualquier causa** |
| `bosque_ganado_ha` | Cobertura `t−1` ∉ bosque y `t` ∈ bosque, por cualquier causa |
| `bosque_a_otra_vegetacion_natural_ha` | Cobertura `t−1` ∈ bosque y `t` ∈ vegetación natural no boscosa |
| `superficie_total_ha` | Superficie del departamento (control) |

**Desmonte no es lo mismo que pérdida de bosque.** `bosque_perdido_ha` incluye además el
bosque que pasa a arbustal o pastizal, que es en promedio **31.000-58.000 ha/año**
(`bosque_a_otra_vegetacion_natural_ha`). Ahí se mezclan degradación real, incendios y
oscilación de la clasificación entre clases vecinas; el producto no permite separarlos. Por
eso el indicador de desmonte es `desmonte_bosque_ha`, que exige conversión a uso antrópico,
y no la pérdida total.

**Lo mismo vale para la regeneración.** `regeneracion_bosque_ha` es vegetación que vuelve
sobre una superficie que tuvo uso antrópico. Es lo más cercano a "reforestación" que ofrece el
dato, y debe presentarse como **regeneración detectada**, no como reforestación: no distingue
restauración activa de abandono de lotes.

## 3. Formato numérico detectado

| Columna | Configuración | Criterio |
|---|---|---|
| Planilla `Salta Hist`, columnas de años | Numérica nativa de Excel (sin texto) | `openpyxl` devuelve `float` en todas las celdas; ninguna llegó como texto, así que no hubo separadores que interpretar. El script igual contempla la regla del último separador y avisa si aparece una celda de texto |
| Salida de Earth Engine | Numérica nativa (JSON) | No aplica |

**Salida:** decimal `.`, sin separador de miles, CSV con `,`, UTF-8 con BOM, valores
redondeados a 2 decimales (hectáreas).

## 4. Verificaciones (corrida del 2026-11-04)

1. **Leyenda y límites.** Cobertura 2025, suma de los 23 departamentos contra la planilla
   oficial: las 15 clases con más de 10.000 ha difieren **menos de 0,4 %**; el total da
   15.525.558 ha contra 15.536.461 ha (−0,07 %). Las únicas diferencias grandes son clases
   diminutas: hielo −2,5 % (60 ha) y "no observado" −77 % (425 vs 1.812 ha), que no afectan
   ninguna métrica.
2. **Stock de bosque por año** (suma departamental vs planilla), 1987-2025: peor diferencia
   **−0,068 %** (2024). Los límites GAUL 2025 coinciden muy bien con el recorte provincial
   que usa MapBiomas.
3. **Superficie departamental constante entre años:** OK en los 23.
4. **Balance del stock:** `bosque(t) − bosque(t−1) = ganado(t) − perdido(t)` cierra con
   residuo **0,0 ha** en todos los años. Confirma que la "cobertura anterior" codificada en el
   producto de transiciones es efectivamente la del año previo, así que los flujos son
   internamente consistentes.
5. **Duplicados y negativos:** ninguno.
6. **Saltos de orden de magnitud** (skill `datasets`, sobre `superficie_bosque_ha`, valores
   ≥ 500 ha): ninguno.

**Sin incidencias detectadas** en las verificaciones automáticas. Las salvedades de §6 no son
errores de procesamiento, sino propiedades del dato.

## 5. Resultados

Provincia (suma de departamentos):

| Período | Desmonte (ha/año) | Regeneración de bosque (ha/año) | Bosque → otra veg. natural (ha/año) |
|---|---:|---:|---:|
| 1987-1997 | 40.215 | 16.329 | 30.927 |
| 1998-2007 | **73.850** | 19.187 | 34.210 |
| 2008-2021 | **60.855** | 25.192 | 40.584 |
| 2022-2025 *(provisorio)* | 37.531 | 12.622 | 57.902 |

Pico de desmonte: **2006 (139.268 ha)** y **2008 (134.793 ha)**, inmediatamente antes y
durante la sanción de la Ley 26.331 (nov. 2007) y del ordenamiento provincial. La serie es
consistente con el "apuro por desmontar" antes de la ley que documentó la literatura, pero
este dato por sí solo **no establece causalidad**.

Departamentos con más desmonte, 1987-2021:

| Departamento | Desmonte 1987-2021 (ha) | Desmonte 2008-2021 (ha) | Bosque 1987 (ha) | Bosque 2021 (ha) | Variación |
|---|---:|---:|---:|---:|---:|
| Anta | 833.327 | 325.489 | 2.070.919 | 1.315.358 | −36,5 % |
| General José de San Martín | 432.231 | 162.542 | 1.479.195 | 1.152.602 | −22,1 % |
| Orán | 255.731 | 122.282 | 1.019.158 | 826.171 | −18,9 % |
| Rivadavia | 153.400 | 89.272 | 2.447.714 | 2.265.082 | −7,5 % |
| Metán | 120.696 | 60.840 | 422.559 | 310.309 | −26,6 % |
| Rosario de la Frontera | 100.198 | 46.110 | 433.546 | 352.574 | −18,7 % |

Los cuatro primeros concentran el **82,4 %** del desmonte de 1987-2021.

## 6. Supuestos y limitaciones

- **2022-2025 son provisorios.** La documentación del ráster aplica reglas especiales de fin
  de serie a los últimos 4 años (`RULES_KERNEL4_END`): un desmonte reciente se confirma o se
  revierte cuando hay años posteriores. Se nota en el dato: en 2024 el stock **sube** 27.725 ha
  y en 2025 cae 139.417 ha, con 108.243 ha de bosque que "pasan" a otra vegetación natural en
  un solo año (el triple del promedio). La planilla oficial muestra la misma caída en 2025, así
  que no es un error del script. **La regeneración de los últimos años está subestimada por
  construcción** (necesita varios años para confirmarse). Cada colección nueva reescribe estos
  años; para el monitor conviene reportar hasta 2021 como consolidado.
- **No es comparable en nivel con otras fuentes.** Para 2022, MapBiomas da 44.723 ha de
  desmonte en Salta; Greenpeace, 15.230 ha. Para 2007-2011, MapBiomas suma unas 434.000 ha;
  la Secretaría de Ambiente informó 236.246 ha (2007-jun. 2011). La explicación más probable es
  la **definición de bosque**: MapBiomas incluye bosques abiertos, y la pérdida **neta** entre
  los mapas 2007 y 2011 (359.000 ha) ya supera la cifra oficial de pérdida **bruta**. La
  hipótesis no se verificó. Para el monitor: usar **una sola fuente** y leer la **tendencia**, no mezclar
  niveles.
- **Primer año:** la serie de transiciones arranca en 1987. 1985-1986 son calentamiento de las
  reglas temporales del producto.
- **Filtro espacial:** el producto descarta como "otra transición" las manchas de hasta 3
  píxeles (~0,3 ha). Desmontes muy chicos no cuentan.
- **Límites:** GAUL 2025, no los del IGN. La coincidencia con el recorte provincial de
  MapBiomas es del 0,07 %, pero el reparto entre departamentos limítrofes puede diferir
  marginalmente del oficial.
- **Falta el cruce con las categorías del OTBN** (roja, amarilla, verde). Es el que permitiría
  estimar desmonte en zonas prohibidas. No se encontró una capa pública del ordenamiento de
  Salta.
- **Versión del dato.** Colección 3, `v1`. Cuando MapBiomas publique una colección nueva hay
  que cambiar `ASSET`, `URL_OFICIAL` y `ANIO_FIN`, y borrar `bosques/cache/`: toda la serie se
  recalcula, no solo el año nuevo.
