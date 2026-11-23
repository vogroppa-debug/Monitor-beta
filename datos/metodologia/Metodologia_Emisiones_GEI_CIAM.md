# Metodología — Emisiones de gases de efecto invernadero por jurisdicción (CIAM / CMNUCC)

Datasets: `Emisiones_GEI_Salta_sector_subsector_gas_anual.csv` y
`Emisiones_GEI_jurisdiccion_sector_anual.csv`
Script: `actualizar_emisiones_gei_ciam.py`
Corrida de referencia: 22 de noviembre de 2026.

---

## 1. Fuente

| | |
|---|---|
| Título | Emisiones anuales de GEI desagregadas por provincia |
| Publica | Centro de Información Ambiental (CIAM), Subsecretaría de Ambiente |
| Dato original | **Primer Informe Bienal de Transparencia de la República Argentina a la CMNUCC** (2024) |
| Portal | `https://ciam.ambiente.gob.ar/repositorio.php?tid=9&stid=36&did=422` |
| Serie | 2010–2022 |
| Última actualización | 22 de enero de 2025 |
| Universo | 43.682 filas: 13 años × 25 jurisdicciones × sector × subsector × gas |

### Cómo se llega al archivo

La página del repositorio **es una cáscara JavaScript: no tiene ningún enlace de descarga**. Los
endpoints reales están en su propio `js/site.repositorio.js`, y el `did` de la URL es el id del
dataset:

| endpoint | para qué |
|---|---|
| `https://ciam.ambiente.gob.ar/dt_csv.php?dt_id=422` | el CSV completo (4,4 MB) |
| `https://ciam.ambiente.gob.ar/get_datasets.php?dt_id=422&mode=2` | los metadatos en JSON |

Una inconsistencia menor del propio portal: el JSON de metadatos declara `fecha_desde`
**1990-01-01**, mientras el PDF metodológico y el dato dicen **2010**. El dato manda: la
primera fila de la serie es de 2010.

El CSV viene con **separador `;`**, campos entre comillas, decimal `.`, UTF-8 con BOM y **sin
salto de línea final**. Columnas:
`año`, `provincia`, `sector`, `subsector`, `tipo_de_gas`, `valor_toneladas_gas`,
`valor_toneladas_co2e`.

---

## 2. Qué es y qué no es este dato

Es el **inventario nacional territorializado**, no una medición hecha en cada provincia. Las
emisiones se asignan a una jurisdicción según los datos de actividad que usó el inventario del
país. El propio metadato lo dice: *«Las emisiones se declaran en cada jurisdicción según los datos
de actividad utilizados para la estimación»*.

Tres consecuencias:

1. **«Jurisdicción sin determinar» es enorme.** Reúne las emisiones del estado nacional y las que
   no se pudieron desagregar. En 2022 son **48.914.312 t CO2e: el 12,2 % del total del país**, y
   quedaría segunda en el ranking de jurisdicciones. Entra en el total nacional —lo es— pero nunca
   se mezcla con una provincia, y en el tablero va identificada con su nombre.
2. **No es una cuenta de responsabilidad provincial.** Una emisión declarada en Salta puede
   corresponder a una actividad cuyo producto se consume en otra provincia, y viceversa.
3. **No es comparable con un inventario provincial propio** hecho con otra metodología o con otro
   recorte de fuentes.

Metodología del inventario: Directrices del IPCC de 2006 con el Refinamiento de 2019.

---

## 3. El potencial de calentamiento: el metadato se contradice y el dato decide

El PDF de metadatos oficial afirma **dos cosas incompatibles**:

| campo del metadato | qué dice |
|---|---|
| **Alcance** | «…utilizando los potenciales de calentamiento global a 100 años del **Quinto Informe de Evaluación** del IPCC» (AR5) |
| **Fórmula** | «…utilizando los potenciales de calentamiento global a 100 años del **Segundo Informe de Evaluación** del IPCC» (SAR) |

No es un detalle de redacción: el metano vale **28** en AR5 y **21** en SAR; el óxido nitroso,
**265** contra **310**. Usar uno u otro cambia el total de la provincia en varios puntos
porcentuales.

**El dato lo resuelve.** El dataset trae las dos columnas —toneladas de gas y toneladas de CO2
equivalente—, así que **el cociente entre ellas ES el potencial que se usó**. Calculado sobre los
agregados de cada gas en las 43.682 filas:

| gas | implícito | AR5 | SAR |
|---|---|---|---|
| CH4 | **28,0** | 28 | 21 |
| N2O | **265,0** | 265 | 310 |
| CO2 | 1,0 | 1 | 1 |
| HFC-23 | **12.400,4** | 12.400 | 11.700 |
| HFC-125 | **3.170,0** | 3.170 | 2.800 |
| HFC-143a | **4.800,0** | 4.800 | 3.800 |
| HFC-227ea | **3.350,2** | 3.350 | 2.900 |
| HFC-32 | **677,0** | 677 | 650 |
| HFC-152a | **138,0** | 138 | 140 |
| PFC-143 (CF4) | **6.628,8** | 6.630 | 6.500 |
| PFC-116 (C2F6) | **11.146,8** | 11.100 | 9.200 |
| HFC-236fa | **8.058,5** | 8.060 | 6.300 |
| HFC-245fa | **852,5** | 858 | — |
| HFC-365 | **803,9** | 804 | — |
| HFC-134a | 1.300,0 | 1.300 | 1.300 |

**Los quince gases coinciden con AR5** dentro del 1 %, y sólo dos con SAR —CO2 y HFC-134a, que
valen igual en ambos—. **Vale AR5, y el campo *Fórmula* del metadato está mal.**

El cociente se calcula sobre los **agregados** de cada gas y no como mediana de los cocientes fila
a fila: la fuente publica las toneladas de gas redondeadas a dos decimales, de modo que en los
gases traza —que se miden en décimas de tonelada— el cociente de una fila suelta se desvía hasta
un 3 % por puro redondeo. El script informa, para cada gas, qué proporción de sus filas cae a
menos del 1 % del agregado: 100 % en CO2 y en los gases con volumen, 33 % en HFC-245fa, que tiene
nueve filas de entre 0,09 y 1,65 toneladas.

La columna `gwp_implicito` del CSV de Salta deja ese cociente escrito fila por fila.

---

## 4. Los valores negativos son absorciones

**1.005 filas del país tienen CO2e negativo; 42 son de Salta.** No son errores: son sumideros,
sobre todo «4A. Tierras forestales» (586 filas en el país) y «4B. Tierras de cultivo». La suma es
correcta tal cual, porque lo que se publica son emisiones **netas**.

**No se recortan ni se pasan a cero.**

Hay un problema de visibilidad que conviene conocer: dentro de cada subsector las absorciones
quedan compensadas contra las emisiones de ese mismo subsector, así que el volumen capturado no se
ve en ningún corte. Y el motor de gráficos del sitio descarta los valores no positivos en los
rankings de barras, de modo que una categoría que termina el año capturando más de lo que emite
desaparece del ranking de subsectores.

Por eso el adaptador publica además una métrica propia, **«Absorciones»**, que suma las filas
negativas con el signo dado vuelta. En Salta no es poco:

| año | absorciones (t CO2e) | | año | absorciones (t CO2e) |
|---|---|---|---|---|
| 2010 | 409.435 | | 2017 | 389.080 |
| 2011 | 406.359 | | 2018 | 307.956 |
| 2012 | 380.334 | | 2019 | 549.925 |
| 2013 | 448.575 | | 2020 | 469.149 |
| 2014 | 548.180 | | 2021 | **836.506** |
| 2015 | 651.287 | | 2022 | 455.924 |
| 2016 | 398.314 | | | |

Entre 300 mil y 840 mil toneladas por año, todos los años de la serie.

---

## 5. Los dos totales, con y sin uso de la tierra

En Salta el sector **4. Uso de la tierra** —desmonte y cambio de uso del suelo— gobierna el total:

| año | con uso de la tierra | sin uso de la tierra | % del país |
|---|---|---|---|
| 2010 | 20.031.634 | 8.375.980 | 5,00 % |
| 2011 | 20.421.783 | 8.440.447 | 5,29 % |
| 2012 | 39.426.895 | 8.284.369 | **9,24 %** |
| 2013 | **39.449.130** | 8.127.740 | 9,21 % |
| 2014 | 24.628.629 | 7.994.202 | 6,16 % |
| 2015 | 19.796.838 | 8.239.620 | 5,15 % |
| 2016 | 16.200.874 | 8.385.163 | 4,27 % |
| 2017 | 14.825.333 | **8.525.530** | 3,83 % |
| 2018 | 14.234.897 | 8.279.845 | 3,69 % |
| 2019 | 12.349.658 | 7.692.902 | 3,56 % |
| 2020 | 28.447.169 | 7.089.808 | 7,24 % |
| 2021 | **11.002.777** | **6.468.116** | 2,76 % |
| 2022 | 12.923.057 | 6.923.010 | 3,22 % |

**La misma provincia admite dos lecturas opuestas según se cuente o no ese sector:** con él las
emisiones bajan un **35 %** entre 2010 y 2022; sin él, un **17 %**. Por eso se publican los dos
totales, que es como presentan sus resultados los inventarios nacionales.

Es la misma historia que el tablero de **Bosque nativo** cuenta en hectáreas: los picos de 2012,
2013 y 2020 son años de desmonte alto.

### Salta 2022 por sector

| sector | t CO2e |
|---|---|
| 4. Uso de la tierra | 6.000.047 |
| 1. Energía | 4.476.497 |
| 3. Agricultura y ganadería | 1.872.035 |
| 5. Residuos | 444.006 |
| 2. Procesos industriales | 130.472 |

Salta queda **9.ª entre las 25 jurisdicciones** contando el uso de la tierra, y **12.ª** sin él.

---

## 6. Esquema de los CSV de salida

Se publican dos tablas en vez del archivo completo de 4,4 MB, porque el tablero necesita el
detalle de Salta y, del resto del país, sólo el agregado por sector.

### `Emisiones_GEI_Salta_sector_subsector_gas_anual.csv` — 2.044 filas

```
anio,sector,subsector,tipo_de_gas,toneladas_gas,toneladas_co2e,gwp_implicito
```

Salta tiene **15 de los 22 subsectores** del país y sólo **tres gases** (CO2, CH4 y N2O): no
aparecen HFC ni PFC, que en el inventario se concentran en refrigeración y aluminio.

### `Emisiones_GEI_jurisdiccion_sector_anual.csv` — 1.625 filas

```
anio,jurisdiccion,sector,toneladas_co2e
```

Las 25 jurisdicciones por año y sector. Es lo que alimenta el ranking y el total del país con el
que se calcula la participación.

### Normalizaciones

- Separador a `,` y decimal `.` (el origen trae `;`).
- **Los cinco sectores llevan su número del IPCC adelante** —`1. Energía`,
  `2. Procesos industriales`, `3. Agricultura y ganadería`, `4. Uso de la tierra`,
  `5. Residuos`—, para que el orden alfabético de las series sea el orden del inventario y las
  etiquetas entren en una leyenda.
- **«Ciudad Autónoma de Buenos Aires» se rotula `CABA`**, que es la denominación que usa el resto
  del Monitor.
- «Tierra del Fuego, Antártida e Islas del Atlántico Sur» → `Tierra del Fuego`.
- «Jurisdiccion sin determinar» → `Jurisdicción sin determinar`.

---

## 7. Formato numérico

| columna del origen | configuración detectada | criterio |
|---|---|---|
| `valor_toneladas_gas` | **inglesa** | decimal `.` con dos dígitos (`72924.10`); ninguna celda con `,` |
| `valor_toneladas_co2e` | **inglesa** | ídem (`2041874.89`) |
| `año` | entero | sin separadores |

Lo decisivo en esta fuente **no es el decimal sino el separador de campo**, que es `;`. El decimal
es `.`, así que la configuración es inglesa; si alguna celda numérica trajera una coma sería
latina y cambiaría el valor, de modo que el script la reporta en vez de adivinar.

Cumplimiento:

| comprobación | resultado |
|---|---|
| valores que no parsean | **0** |
| celdas numéricas con coma | **0** |
| reconciliación de los dos CSV contra el origen, año por año | **0 desvíos** |
| encoding | UTF-8 con BOM, **0 mojibake** |
| saltos de orden de magnitud por jurisdicción y sector | 12 en el país, **2 en Salta** (ver incidencias) |

---

## 8. Valores de control

| control | valor |
|---|---|
| Filas del origen · de Salta | 43.682 · 2.044 |
| Años · jurisdicciones · sectores · subsectores | 13 (2010–2022) · 25 · 5 · 22 |
| GWP implícito de CH4 · N2O | 28,0 · 265,0 (AR5) |
| Salta 2022, con · sin uso de la tierra | 12.923.057 · 6.923.010 t CO2e |
| País 2022, con · sin uso de la tierra | 400.920.592 · 349.515.942 t CO2e |
| Participación de Salta 2022 | 3,22 % |
| Puesto de Salta 2022, con · sin uso de la tierra | 9.º · 12.º de 25 |
| Filas con CO2e negativo, país · Salta | 1.005 · 42 |

**Resultado de la corrida del 22-nov-2026: 15 de 15 controles exactos.**

---

## 9. Incidencias

Dos, las dos del mismo hecho:

1. **«2B. Industria química» entra al inventario de Salta en 2021** con 85.160 t CO2e, 32 veces la
   mediana de la serie del sector, y sube a **127.178 t en 2022**. Antes de 2021 el sector
   «Procesos industriales» de Salta eran unas 2.500 toneladas anuales de un solo subsector,
   «2D. Uso de productos no energéticos».
2. Lo mismo informado para 2022.

**No es un error de parseo**: el salto está en la fuente, es un subsector que antes no existía para
la provincia y el valor es coherente con el del año siguiente. La fuente **no identifica el
establecimiento**, así que acá no se afirma cuál es.

No hubo valores sin parsear, ni desvíos de reconciliación, ni jurisdicciones o sectores
desconocidos.

---

## 10. Supuestos y limitaciones

- **Es el inventario nacional territorializado**, con todo lo que eso implica (sección 2).
- **El 12 % de las emisiones del país no está asignado a ninguna provincia.** La participación de
  Salta se calcula sobre el total nacional incluyendo esa bolsa; calcularla sobre el total asignado
  daría un número algo mayor.
- **La serie termina en 2022.** Es lo último que Argentina reportó a la CMNUCC en su Primer
  Informe Bienal de Transparencia; el dataset no se actualiza hasta el próximo informe.
- **Las toneladas de cada gas no se pueden sumar entre gases.** Quedan en el CSV; el tablero
  trabaja siempre en CO2 equivalente.
- **El ranking de subsectores no muestra las categorías con absorción neta**, por el motor de
  gráficos del sitio. Está dicho en la descripción del gráfico y el volumen capturado se publica
  aparte en la métrica «Absorciones».
- **No se verificó contra el informe original.** Los totales nacionales son del orden de los 400
  millones de toneladas, consistentes con lo que Argentina reporta, pero no se hizo un cotejo
  celda por celda contra el PDF del Informe Bienal.
