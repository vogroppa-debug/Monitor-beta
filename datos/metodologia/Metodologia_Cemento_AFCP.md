# Metodología — Despachos de cemento por provincia y envase (AFCP)

Dataset: `Despachos_cemento_AFCP_provincia_mensual.csv`
Script que lo genera: `Actualizar_Cemento_AFCP.md`
Fecha de elaboración: 2026-11-18.

## Resultado en una línea

Despachos de cemento en bolsa y a granel, mensuales, en toneladas, para las 25 jurisdicciones que
abre la AFCP —Salta entre ellas— y el total del país, de enero de 2017 a septiembre de 2025:
**8.190 filas**, armadas leyendo 93 páginas HTML sueltas, con cuatro controles que cierran y un
control de relectura que compara 2.106 celdas entre páginas distintas sin encontrar una sola
diferencia.

## 1. Fuente

**«Consumo de Cemento por Provincias y según Envases»**, Asociación de Fabricantes de Cemento
Portland (AFCP).

| | |
|---|---|
| Página índice | <https://www.afcp.org.ar/copia-de-despacho-total-de-cemento> |
| Páginas leídas | `http://afcp.info/ESTADISTICAS/DATOS-DEFINITIVOS/{AAAAMM}/estadistica04.html` (hasta 2022-03) y `…/{AAAAMM}-Provincias/estadistica04.html` (desde 2022-04) |
| Cantidad | **93 páginas**, una por mes, de 2018-01 a 2025-09 (~19 MB en total) |
| Formato | HTML generado con Word, codificado en **windows-1252** |
| Frecuencia | Mensual, sección «Datos Definitivos» |
| Unidad | **Toneladas** (ver §7, incidencia 3) |

La AFCP publica además un **informe mensual provisorio nacional**
(<https://www.afcp.org.ar/despacho-mensual>), que llega a octubre de 2026 pero **no abre por
provincia**. No entra en este dataset.

### Qué es «consumo» acá

Es el **despacho de cemento con destino a cada jurisdicción**, no la producción de esa
jurisdicción. Una provincia sin planta cementera aparece igual, con lo que recibe. La AFCP no
publica una definición más precisa en estas páginas.

## 2. Cobertura y unidad de análisis

### Cada página trae dos años

Además del mes publicado, cada tabla repite **el mismo mes del año anterior**, para comparación.
Dos consecuencias, las dos aprovechadas:

1. La serie **arranca en enero de 2017**, un año antes de lo que anuncia la página índice: los
   doce meses de 2017 salen de los bloques de comparación de las páginas de 2018.
2. **81 meses se leen dos veces**, en páginas distintas publicadas con un año de diferencia. Esa
   relectura es el control cruzado más fuerte que tiene esta fuente y se corre en cada actualización
   (§6).

### Qué incluye el dataset

- **26 jurisdicciones × 105 meses**, de **2017-01 a 2025-09**, sin un solo hueco y con las 26 filas
  presentes en todos los meses.
- Las 25 jurisdicciones de la AFCP más `Total del país`. **Buenos Aires viene partida en tres**:
  `CABA`, `Gran Buenos Aires` y `Buenos Aires`. Se respeta la partición y no se reconstruye la
  provincia sumando pedazos; la AFCP no define dónde corta el Gran Buenos Aires.
- Dos envases, **bolsa** y **granel**, más el total que publica la propia AFCP.
- **Toda la serie es definitiva.** La fuente es la sección «Datos Definitivos» y no marca nada como
  provisorio, así que el CSV no lleva columna `calidad`: sería una columna constante.

### Lo que la fuente trae y no se emite

Las columnas de **acumulado del año** y las de **porcentaje sobre el total**. El acumulado es la
suma corrida dentro del año y el porcentaje es un cociente: los dos se derivan del propio CSV. Se
**leen** en cada corrida y se usan para verificar (§6), pero no se publican.

## 3. Esquema del CSV

`Despachos_cemento_AFCP_provincia_mensual.csv` — 8.190 filas.

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | entero | Año |
| `n_mes` | entero 1-12 | Mes |
| `mes` | fecha ISO | Primer día del mes, `AAAA-MM-01` |
| `periodo` | texto | `AAAA-MM` |
| `provincia` | texto | 26 valores, normalizados (ver §5) |
| `metrica` | texto | `despachos_bolsa_t` \| `despachos_granel_t` \| `despachos_total_t` |
| `valor` | entero | Toneladas |

2.730 filas por métrica (105 meses × 26 jurisdicciones).

### Columnas derivadas (las únicas que agrega este proceso)

`anio`, `n_mes`, `mes` y `periodo`, que salen de la fila de título `Período: <Mes> de <Año>` de
cada bloque.

## 4. Formato numérico detectado

| Columna / archivo | Configuración detectada | Criterio usado |
|---|---|---|
| Las seis columnas de valor (bolsa, granel, total; del mes y acumulado) | **Latina**: miles con `.`, sin decimales (`17.893` = 17.893 t) | **Coherencia.** Bajo la lectura decimal (`17.893` = 17,893 t) no cerraría ninguna de las cuatro identidades de §6. La decisión se toma a nivel de columna, no valor por valor |
| Las seis columnas de porcentaje | **Latina**: decimal `,` (`2,6%`) | No se emiten; no se parsean |
| Codificación de las 93 páginas | **windows-1252**, declarada en el `<meta>` | Las 93 decodifican en estricto. Nunca se usa `errors="replace"` |

Un valor que no respete el agrupamiento de a tres se reporta como incidencia en vez de leerse a la
fuerza. En la corrida del 2026-11-18 no hubo ninguno.

**Salida:** separador `,`; decimal `.`; sin separador de miles; codificación **UTF-8 con BOM**
(`utf-8-sig`), igual que el resto de los datasets del proyecto.

## 5. Transformaciones aplicadas

1. **El guion es cero.** La AFCP escribe `-` cuando una jurisdicción no despachó nada en el mes. Se
   lee como **0**, no como dato faltante, y la identidad lo confirma: La Rioja, abril de 2020,
   bolsa 4.981 + granel `-` = total 4.981. En los 105 meses hay **2 celdas** así; el script
   informa cuántas leyó en cada corrida.
2. **Normalización de las etiquetas de jurisdicción.** Vienen en mayúsculas, sin acentos y
   abreviadas, que es un artefacto de la planilla de Word. Diccionario completo:

   | Fuente | Dataset | | Fuente | Dataset |
   |---|---|---|---|---|
   | `CAPITAL FEDERAL` | **`CABA`** | | `MISIONES` | `Misiones` |
   | `GRAN BUENOS AIRES` | `Gran Buenos Aires` | | `NEUQUEN` | `Neuquén` |
   | `BUENOS AIRES` | `Buenos Aires` | | `RIO NEGRO` | `Río Negro` |
   | `CATAMARCA` | `Catamarca` | | `SALTA` | `Salta` |
   | `CORDOBA` | `Córdoba` | | `SAN JUAN` | `San Juan` |
   | `CORRIENTES` | `Corrientes` | | `SAN LUIS` | `San Luis` |
   | `CHACO` | `Chaco` | | `SANTA CRUZ` | `Santa Cruz` |
   | `CHUBUT` | `Chubut` | | `SANTA FE` | `Santa Fe` |
   | `ENTRE RIOS` | `Entre Ríos` | | `SGO. DEL ESTERO` | `Santiago del Estero` |
   | `FORMOSA` | `Formosa` | | `T. DEL FUEGO` | `Tierra del Fuego` |
   | `JUJUY` | `Jujuy` | | `TUCUMAN` | `Tucumán` |
   | `LA PAMPA` | `La Pampa` | | `TOTALES` | `Total del país` |
   | `LA RIOJA` | `La Rioja` | | `MENDOZA` | `Mendoza` |

   **`CAPITAL FEDERAL` sale como `CABA`**: la denominación de la fuente es vieja y en todo el
   proyecto se usa CABA. Una etiqueta que no esté en este diccionario, con números al lado,
   **aborta la corrida**.
3. **El total se emite como lo publica la AFCP**, no como `bolsa + granel`. En las celdas en que
   difieren por una tonelada (§6), mandar el publicado evita mostrar un número que la fuente no
   dice.
4. **No se emiten el acumulado ni los porcentajes**, por lo dicho en §2.
5. **Ordenamiento determinista**: por orden de jurisdicción en la tabla de la AFCP, año, mes y
   métrica.

## 6. Verificación de totales

Corrida del **2026-11-18**.

### Control de relectura (el más fuerte)

81 meses aparecen en dos páginas distintas, publicadas con un año de diferencia: una vez como mes
corriente y otra como comparación del año siguiente. **2.106 celdas comparadas, 0 discrepancias.**
La AFCP no corrigió nunca un número provincial en ocho años.

### Identidades internas

| Control | Resultado |
|---|---|
| `bolsa + granel = total`, del mes | desvío **máximo 1 t**; 372 celdas de 2.730 difieren |
| `bolsa + granel = total`, acumulado | desvío **máximo 1 t**; 456 celdas difieren |
| `acum(t) − acum(t−1) = del mes`, dentro del año | **0 desvíos** en 2.496 transiciones |
| Suma de las 25 jurisdicciones = `Total del país` | desvío **máximo 4 t**; 217 casos de 315 difieren |

Las diferencias de 1 y de 4 toneladas son **redondeo**: la AFCP redondea cada celda por separado
desde toneladas con decimales. **No se corrigen y no se fuerzan a cerrar.** La tolerancia está
cableada en el script (1 t para las identidades por fila, 10 t para la suma de jurisdicciones): si
crecen, salta como incidencia.

### Control de parseo redundante

Las 93 páginas se parsearon por dos caminos independientes —`html.parser` de la biblioteca estándar
y expresiones regulares sobre `<tr>`/`<td>`— y se compararon las **4.836 filas-jurisdicción**
resultantes: **0 discrepancias**.

### Cobertura

105 meses consecutivos, 2017-01 a 2025-09, con las 26 jurisdicciones en todos. Ningún hueco entre
la primera y la última página publicada.

### Saltos de orden de magnitud

Uno, y es dato real: **el granel de CABA de abril de 2020, 86 t** contra una mediana de ~9.000. Es
el parate de la obra por la pandemia. Se reporta en cada corrida y **no se corrige**. El granel de
Salta del mismo mes —1.151 t contra 5.712 t un año antes— no llega a disparar la regla, pero es el
mismo fenómeno.

### Reproducibilidad

- El bloque `python` de `Actualizar_Cemento_AFCP.md` es **md5-idéntico** al
  `actualizar_cemento_afcp.py` en disco (`6e4e9b27d8559e8dbeef5cc16b8aba35`).
- Dos corridas seguidas producen un CSV con el mismo md5
  (`20f4d6386e4c9c9650f50357fa48c724`).

### Valores de control

Salta, en toneladas:

| Mes | Bolsa | Granel | Total |
|---|---|---|---|
| 2017-01 | 17.893 | 5.332 | 23.225 |
| 2020-04 | 14.226 | 1.151 | 15.377 |
| 2024-09 | 16.288 | 8.252 | 24.540 |
| 2025-09 | 9.680 | 5.430 | 15.110 |
| **2024 completo** | **163.380** | **85.829** | **249.210** |

El total de 2024 ilustra el redondeo: la suma de los totales publicados da 249.210, una tonelada
más que `163.380 + 85.829`. Las dos cifras son correctas; la del CSV es la que publica la AFCP.

Total del país: 2017-01 → 566.123 / 307.653 / 873.775; 2025-09 → 513.908 / 404.168 / 918.077.
Salta explica en promedio el **2,64 %** de los despachos del país, entre **1,49 %** y **3,81 %**
según el mes.

## 7. Incidencias

| # | Incidencia | Veredicto y decisión |
|---|---|---|
| 1 | **La página índice no sirve como catálogo.** Es un sitio Wix que arma los enlaces por JavaScript, **le falta el de agosto de 2022** —que sin embargo existe y responde— y duplica el de agosto de 2023. | **Defecto de origen.** No se scrapean los enlaces: se enumeran los meses y se prueban los patrones de URL. Así entra agosto de 2022 y así entrarán los meses nuevos. |
| 2 | **Dos patrones de URL** según el período: `{AAAAMM}` hasta 2022-03 y `{AAAAMM}-Provincias` desde 2022-04 (2021-04 responde por los dos). | **Cambio de la fuente.** Se prueban los dos, el nuevo primero. |
| 3 | **La página no declara la unidad.** Ni la provincial ni la de acumulados dicen en qué están los números. | **Límite de la fuente.** Son toneladas, según el informe mensual de la propia AFCP: *«Las valores están expresados en toneladas»* (<https://www.afcp.org.ar/despacho-mensual>). |
| 4 | **`bolsa + granel` no da exactamente el total**: 372 celdas difieren, siempre por 1 t. | **Redondeo de origen.** Se publica el total tal como viene; no se fuerza a cerrar. |
| 5 | **La suma de las jurisdicciones no da exactamente el total del país**: hasta 4 t de desvío, en 217 casos de 315. | **Redondeo de origen.** Se documenta la tolerancia; no se corrige. |
| 6 | **Cada página trae dos años.** | **Hallazgo, no problema.** Agrega 2017 entero y da el control de relectura de §6. |
| 7 | **La apertura provincial se corta en 2025-09**, mientras la serie nacional llega a 2026-10. | **Límite conocido.** Las URLs posteriores dan 404 con los dos patrones. El script detecta los meses nuevos solo e informa cuántos faltan. |
| 8 | **El guion `-` como valor.** | **Es cero, no un faltante.** Lo confirma la identidad bolsa + granel = total. 2 celdas en los 105 meses. |
| 9 | **Etiquetas en mayúsculas, sin acentos y abreviadas** (`CORDOBA`, `SGO. DEL ESTERO`, `T. DEL FUEGO`). | **Artefacto de la planilla de Word.** Diccionario explícito (§5); una etiqueta desconocida con números al lado aborta la corrida. |
| 10 | **La fuente dice «CAPITAL FEDERAL»**, denominación vieja. | **Se renombra a `CABA`**, la que usa el proyecto. |
| 11 | **Buenos Aires viene partida en tres** y la AFCP no define dónde corta el Gran Buenos Aires. | **Característica de la fuente.** Se respeta la partición; no se reconstruye la provincia. |
| 12 | **Salto de orden de magnitud**: granel de CABA, abril de 2020, 86 t. | **Dato real**: el parate de la obra por la pandemia. Se reporta y no se corrige. |
| 13 | Mojibake, duplicados y rangos. | **Sin incidencias.** Ninguna secuencia `Ã`, `Â` ni `â€` pese a los acentos de `Córdoba`, `Entre Ríos`, `Neuquén`, `Río Negro` y `Tucumán`; 0 claves `(periodo, provincia, metrica)` duplicadas; 0 negativos; los 8.190 valores son enteros. |

## 8. Supuestos y limitaciones

1. **No es producción provincial.** Es el despacho con destino a cada jurisdicción. Una provincia
   sin planta cementera aparece igual, con lo que recibe.
2. **Bolsa y granel son envases, no usos.** En el sector se los lee como una señal del tipo de
   obra —el granel va sobre todo a hormigoneras y obra grande; la bolsa, a obra chica y
   autoconstrucción—, pero **esa lectura no es una definición de la AFCP** y no se publica como
   tal.
3. **La serie está congelada desde septiembre de 2025.** Mientras la AFCP no retome la apertura
   provincial, el indicador no avanza aunque el sector siga midiéndose a nivel nacional. Es el
   límite más importante de este dataset.
4. **No hay datos antes de 2017** por esta vía. Las páginas más viejas que enero de 2018 no están
   publicadas, y 2017 entra sólo por los bloques de comparación.
5. **No se controlan cambios de cobertura de la AFCP.** Si una empresa entra o sale de la
   asociación, el salto aparece en la serie y la AFCP no publica una nota que permita
   identificarlo.
6. **La asignación geográfica es la que hace la AFCP** y no está documentada en estas páginas: no
   se aclara si el destino es el domicilio del comprador, el de la obra o el del punto de entrega.
7. **El tablero todavía no está armado.** Cuando se arme, va con **toggle de frecuencia mensual /
   trimestral / anual**, siguiendo el patrón de Turismo y Recaudación: `adapters.py` emite la
   dimensión `grano` con los tres granos y `catalog.py` declara el control
   `{"kind": "freq", …}` en cada gráfico. El dataset ya está en forma para eso, porque las tres
   métricas son **sumas de toneladas** y el trimestre y el año son la suma de sus meses, sin
   ponderaciones ni deflactores de por medio. Lo único a respetar es descartar el último trimestre
   y el último año incompletos con `_completos()` / `_keep_completos()` de `adapters.py`, para no
   dibujar una caída ficticia — hoy harían falta, porque la serie corta en septiembre de 2025.
