# Metodología — Movimientos y pasajeros del aeropuerto de Salta (ANAC)

Datasets: `Salta_aeropuerto_ANAC_series_mensual.csv` y
`Salta_aeropuerto_ANAC_aterrizajes_mensual.csv`
Script que los genera: `Actualizar_Salta_aeropuerto_ANAC.md`
Fecha de elaboración: 2026-11-18.

## Resultado en una línea

Dos series mensuales del aeropuerto Martín Miguel de Güemes: una **larga** (2001–2026, 309 meses
sin huecos) que llega hasta cabotaje/internacional, y una **detallada** (2019–2026, 93 meses) que
abre los aterrizajes por clase de vuelo, clasificación y aerolínea. Salen de dos productos
distintos de ANAC que no cierran entre sí, y por eso van separadas.

## 1. Fuente

Organismo: **Administración Nacional de Aviación Civil (ANAC)**, Secretaría de Transporte,
Ministerio de Economía. Sistema de origen declarado: **SIAC** (Sistema Integrado de Aviación
Civil). Licencia **CC-BY-4.0**. Frecuencia declarada: `R/P1M` (mensual).

### Producto 1 — series históricas (dataset A)

Share público de Nextcloud: <https://docs.anac.gob.ar/index.php/s/4ptegdXanm2rWJG>, carpeta
«tablas de movimientos y pasajeros». Dos libros Excel:

| Archivo | Tamaño | Modificado | Cobertura |
|---|---|---|---|
| `series-historicas-2001-2022.xlsx` | 1.384.081 b | 2025-09-24 | 2001-01 → 2022-12 |
| `series-historicas-2023-2026.xlsx` | 271.485 b | 2026-10-13 | 2023-01 → 2026-09 |

Cada libro trae una hoja `OUT` con **22 tablas** apiladas y una hoja `Notas` con las definiciones.
No se solapan: empalman en 2022-12 / 2023-01.

Se obtienen por **WebDAV** (`https://docs.anac.gob.ar/public.php/webdav/`), usando el token del
share como usuario de basic auth y contraseña vacía. El `PROPFIND` lista la carpeta, así que el
script detecta solo si ANAC agrega o renombra un archivo.

### Producto 2 — microdatos (dataset B)

<https://datos.gob.ar/dataset/aterrizajes-y-despegues-procesados-por-la-administracion-nacional-de-aviacion-civil-anac>,
con los archivos alojados en `datos.transporte.gob.ar`. **Ocho CSV, uno por año (2019–2026)**, un
registro por movimiento. Total descargado: ~350 MB.

**El dataset no publica diccionario de datos.** Ni la página del dataset ni las de los ocho
recursos describen una sola columna. El esquema de la sección 3 sale de leer los archivos, y las
definiciones de la sección 2, de la hoja `Notas` del otro producto.

Dos metadatos del portal que **no** hay que creerle: declara cobertura hasta `2025-01-20` cuando
los recursos llegan a 2026, y rotula el recurso 2019 como formato `XML` cuando es un CSV
(`text/csv`). Manda el archivo.

## 2. Cobertura y unidad de análisis

La hoja `Notas` de las series históricas es la única documentación metodológica que publica ANAC
para cualquiera de los dos productos. Literal:

> «Se considera "Movimiento" a una operación, sea aterrizaje o despegue.»
> «Se considera "Vuelo" a un trayecto origen-destino completo en un único sentido.»
> «Un vuelo de cabotaje implica 2 movimientos; uno internacional, 1 movimiento.»
> «Se consideran pasajeros (adultos, menores y exentos) embarcados y desembarcados en cada etapa
> de vuelo. En su forma más general: 1 pasajero = 1 tarjeta de embarque. No se consideran
> pasajeros en tránsito (no descienden del avión en una escala).»
> «La información de cada mes corresponde al período entre las 0hs día primer día del mes y las
> 23.59hs del último, hora local.»
> «La información de los últimos 3 meses es provisoria.»

**Por qué no se publica `PAX`.** La columna `PAX` de los microdatos no son los pasajeros de un
tramo. Un vuelo de cabotaje deja **dos** filas —el despegue en el aeropuerto de origen y el
aterrizaje en el de destino— y las dos llevan el mismo `Pasajeros`; `PAX` es la mitad, el reparto
entre los dos aeropuertos para que el total del país no duplique. En internacional, donde el otro
extremo no está en el dataset, `PAX = Pasajeros`. Verificado sobre ~5 millones de filas (sección 6).

Sumada sobre los movimientos de **un solo** aeropuerto, `PAX` deja los domésticos a la mitad y los
internacionales enteros: dos escalas en la misma columna, que no sirve como nivel para Salta. **El
dataset B emite `vuelos` y `pasajeros`, y no emite `pax`.** La columna igual se lee en cada
corrida para verificar el invariante, porque esa verificación es la que respalda la decisión y
avisaría si ANAC cambiara el criterio.

Quien necesite cruzar contra un agregado nacional de ANAC tiene que reconstruir `pax` desde
`pasajeros`: la mitad en los domésticos, entero en los internacionales.

### Aeropuerto

En los microdatos, Salta es **`SAL`**, código local de ANAC: no es IATA (`SLA`) ni OACI (`SASA`).
Es el único aeropuerto salteño del dataset —entre los 50 códigos presentes no hay Orán, Tartagal
ni Cafayate— y el séptimo del país por movimientos. En las series históricas es la fila `Salta`,
una de 57 aeropuertos.

### Qué incluye cada dataset

| | Dataset A (series) | Dataset B (microdatos) |
|---|---|---|
| Período | 2001-01 → 2026-09 (309 meses) | 2019-01 → 2026-09 (93 meses) |
| Sentido | Movimientos: aterrizajes **+** despegues | Sólo **aterrizajes** |
| Clases de vuelo | Sólo regulares y no regulares | Las 9, como dimensión |
| Aerolínea | No (sólo a nivel país, en otras tablas) | Sí, 239 nombres |
| Rutas | Las del top 61 nacional que nombran a Salta | No (fuera de alcance) |
| Corte del mes | Hora local | Fecha publicada, rotulada UTC |

El dataset A toma las **tablas 9 a 14** (las que abren por aeropuerto) y, de las **tablas 19 a
22** (las que abren por ruta), las filas que nombran a Salta: Aeroparque, Córdoba, Ezeiza, El
Palomar, Iguazú, Jujuy, Mendoza, Neuquén, Rosario y Tucumán en cabotaje, y Asunción, Iquique,
Lima, Panamá, Punta Cana y Santa Cruz de la Sierra en internacional. Se distinguen con la columna
`serie`.

## 3. Esquema de los CSV

### `Salta_aeropuerto_ANAC_series_mensual.csv` — 9.981 filas

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | entero | Año |
| `n_mes` | entero 1-12 | Mes |
| `mes` | fecha ISO | Primer día del mes, `AAAA-MM-01` |
| `periodo` | texto | `AAAA-MM` |
| `aeropuerto` | texto | `Salta` o el nombre de la ruta (`Aeroparque - Salta`) |
| `serie` | texto | `aeropuerto` \| `ruta` |
| `clasificacion` | texto | `Cabotaje` \| `Internacional` \| `Total` |
| `metrica` | texto | `pasajeros` \| `movimientos` \| `vuelos` |
| `valor` | entero | Ver «unidades» abajo |
| `calidad` | texto | `DEFINITIVO` \| `PROVISORIO` (últimos 3 meses) |

### `Salta_aeropuerto_ANAC_aterrizajes_mensual.csv` — 3.830 filas

| Columna | Tipo | Descripción |
|---|---|---|
| `anio`, `n_mes`, `mes`, `periodo` | — | Igual que arriba |
| `aeropuerto` | texto | Siempre `SAL` |
| `clasificacion` | texto | `Doméstico` \| `Internacional` |
| `clase_vuelo` | texto | Las 9 clases de ANAC |
| `aerolinea` | texto | Nombre tal como viene, o `Sin informar` |
| `calidad` | texto | `DEFINITIVO` \| `PROVISORIO` \| `MIXTO` |
| `metrica` | texto | `vuelos` \| `pasajeros` |
| `valor` | entero | Conteo de aterrizajes o suma de pasajeros desembarcados |

Las 9 clases de vuelo: Regular, No Regular, Trabajo Aéreo, Vuelo Escuela, Vuelo Oficial Nacional,
Vuelo Oficial Extranjero, Vuelo Privado con Matrícula Nacional, Vuelo Privado con Matrícula
Extranjera, Vuelo de Adiestramiento.

### Columnas derivadas (las únicas que agrega este proceso)

`mes`, `periodo` y `n_mes` se derivan de la fecha; `calidad` se deriva de la regla de los tres
meses (dataset A) o de la columna `Calidad dato` agregada al mes (dataset B). Nada más: no se
calculan tasas ni porcentajes. Los cocientes —ocupación, participación internacional, pasajeros
por vuelo— quedan para el tablero, porque no son aditivos entre meses ni entre clases.

## 4. Formato numérico detectado

| Columna / archivo | Configuración detectada | Criterio usado |
|---|---|---|
| XLSX, celdas de las tablas | **Numérica nativa de Excel** | `openpyxl` devuelve `float`; ninguna celda llegó como texto. El script igual aplica `parse_num` si aparece una |
| XLSX, tablas 9, 10, 11, 19, 20 | Miles con 3 decimales (`21.941` = 21.941 pasajeros) | El encabezado dice `[000]`. **Se multiplica por 1.000 al emitir** |
| XLSX, tablas 12, 13, 14, 21, 22 | Unidades (`603`) | El encabezado dice `[#]`. No se toca |
| CSV 2019–2025, `Pasajeros` y `PAX` | **Latina**: decimal `,`, sin separador de miles (`140,00`) | Regla del último separador; la cola tiene 2 dígitos, luego es decimal |
| CSV 2026, `Pasajeros` y `PAX` | **Entera**, sin decimales (`140`) | Sin separador que interpretar |
| CSV, codificación | **UTF-8** | Los ocho decodifican en estricto. Nunca se usa `errors="replace"` |

Ningún valor cayó en la rama ambigua del parser (separador seguido de exactamente 3 dígitos); si
alguno lo hiciera, el script lo reporta como incidencia en vez de resolverlo en silencio.

**Salida:** separador `,`; decimal `.`; sin separador de miles; codificación **UTF-8 con BOM**
(`utf-8-sig`), igual que el resto de los datasets del proyecto.

## 5. Transformaciones aplicadas

1. **Lectura por nombre de encabezado** en los CSV. Los de 2019 a 2025 traen 12 columnas y el de
   2026 agrega `Matrícula` en el medio; leer por posición habría corrido `Pasajeros` y `PAX` un
   lugar.
2. **Localización de bloques por marcador** en los XLSX. Los bloques se buscan por el `TABLA n` de
   la columna A y las columnas de datos, por el nombre del mes en la segunda fila. El libro
   2001–2022 tiene 267 columnas y el 2023–2026, 47.
3. **Normalización de etiquetas** a la forma de 2020 en adelante: `Domestico` → `Doméstico`,
   `ATERRIZAJE` → `Aterrizaje`, `DESPEGUE` → `Despegue`. Afectó **580.764 filas, todas de 2019**;
   ningún otro año.
4. **Pasajeros de las series a unidades**: × 1.000 y redondeo al entero.
5. **`Aerolinea Nombre` = `0` → `Sin informar`.** `0` es el centinela de dato faltante de la
   fuente, no una aerolínea. Son vuelos de aviación general sin explotador declarado: **25.923 de
   los 61.558 aterrizajes** de la serie (42 %). No se borran, porque sostienen el segmento «Vuelo
   Privado» y las clases de instrucción.
6. **`PAX` se lee pero no se emite** (ver sección 2). Es la única columna de la fuente que se
   descarta deliberadamente, y se descarta entera: no se transforma ni se reescala.
7. **Nada más.** No se unifican nombres de aerolínea, no se imputa, no se corrige ningún valor.

## 6. Verificación de totales

Corrida del **2026-11-18**.

### Controles internos que cierran

- **Invariante de `PAX`**, sobre los ~5 millones de filas de los ocho archivos (no sólo Salta):
  `PAX == Pasajeros` en internacional y `PAX == Pasajeros/2` en doméstico. **Una sola violación en
  toda la serie**, documentada en Incidencias. Desde 2026 la fuente redondea `PAX` al entero hacia
  arriba: 95.579 filas de ese año tienen `PAX = ceil(Pasajeros/2)` en vez del medio punto exacto.
- **Cobertura sin huecos.** Dataset A: **309 meses**, de 2001-01 a 2026-09, ningún mes faltante.
  Dataset B: **93 meses**, de 2019-01 a 2026-09, ningún mes faltante.
- **Los dos libros empalman**: ninguna celda aparece con valores distintos en los dos archivos.
- **Saltos de orden de magnitud**: 6 valores en el dataset A, todos del cierre de aeropuertos de
  2020 (abril, 116 pasajeros en todo el mes, contra una mediana de 52.570). Dato real.

### Control cruzado independiente (el más fuerte)

**Entre los dos productos de ANAC.** Los movimientos de Salta de la serie oficial se comparan, mes
a mes, contra los microdatos agregados a la misma definición (regular + no regular, aterrizajes y
despegues):

| Clasificación | Lectura de los microdatos | Meses | Brecha mediana | Rango |
|---|---|---|---|---|
| **Cabotaje** | regular + no regular | 93 | **+0,4 %** | −4,8 % a +15,4 % |
| Cabotaje | sólo regular | 89 | −8,3 % | −96,3 % a −2,0 % |
| Internacional | regular + no regular | 88 | +143,0 % | −1,2 % a +1950 % |
| Internacional | sólo regular | 68 | −56,4 % | −88,6 % a 0,0 % |

**El cabotaje cierra.** Dos agregaciones independientes del mismo sistema, hechas por caminos
distintos y publicadas en formatos distintos, coinciden con una mediana de 0,4 % sobre 93 meses.
Eso valida el pipeline de punta a punta.

**El internacional no cierra, pero queda acotado.** La cifra oficial cae **entre** las dos
lecturas: es mayor que contar sólo los regulares y mucho menor que contar regulares y no regulares.
O sea que lo que ANAC cuenta como «comercial internacional» incluye parte de los no regulares pero
no todos. En Salta los no regulares internacionales son vuelos chicos —1.224 aterrizajes en 2026
con 15 pasajeros de promedio—, y las notas de ANAC declaran la exclusión de cargueros para unas
tablas y no para otras. **No se fuerza la conciliación**: los dos datasets salen por separado, con
su definición escrita, y la brecha se publica.

**El espejo.** Un vuelo de cabotaje X→SAL deja dos filas: el despegue en X y el aterrizaje en SAL.
De los **5.861 aterrizajes domésticos** en SAL de 2026, **3.853 (66 %)** tienen su despegue
correspondiente en el aeropuerto de origen, identificado por matrícula y fecha, y **2.732 de esos
(70,9 %)** traen el **mismo `Pasajeros`**. Los que no aparecen son, en su mayoría, vuelos que
cruzan la medianoche y quedan con otra fecha. Es la confirmación empírica de la nota de ANAC sobre
los dos movimientos del vuelo de cabotaje, y de que `PAX` es un reparto y no una medición.

### Reproducibilidad

Se comparó el bloque `python` del runbook contra `actualizar_aeropuerto_anac.py`: **md5 idéntico**
(`901f33d4…`), o sea que lo documentado es exactamente lo que se corrió.

Con la caché completa en `fuentes/anac/` se corrió dos veces seguidas y los dos CSV salieron
**md5 idénticos** (`5304e495…` el de series, `895f7b3a…` el de aterrizajes). El orden de las filas
es determinista —`sorted` sobre la clave completa— y no hay ningún paso con aleatoriedad ni
dependiente de la hora. Los hashes valen para los datos de esta corrida: cambian cuando ANAC
publica un mes nuevo o revisa uno viejo, que es lo esperado.

### Valores de control

Dataset A, fila `Salta`:

| Período | Clasificación | Movimientos | Pasajeros |
|---|---|---|---|
| 2001-01 | Cabotaje | 603 | 21.941 |
| 2026-09 | Cabotaje | 994 | 136.043 |

Totales 2026 (ene–sep): cabotaje **7.686**, internacional **1.333**, total **9.019** movimientos.

Dataset B, aterrizajes en SAL, todas las clases:

| Mes | Vuelos | Pasajeros |
|---|---|---|
| 2026-01 | 980 | 69.924 |
| 2026-02 | 888 | 64.727 |
| 2026-03 | 919 | 66.583 |
| 2026-04 | 994 | 64.721 |
| 2026-05 | 885 | 58.410 |
| 2026-06 | 703 | 49.665 |
| 2026-07 | 854 | 64.351 |
| 2026-08 | 782 | 57.408 |
| 2026-09 | 986 | 76.872 |

Total ene–sep 2026: **7.991 aterrizajes y 572.661 pasajeros**. Filas de SAL en el archivo crudo
2026 (aterrizajes y despegues): **15.977**.

Aterrizajes en SAL por año: 2019 **8.415**, 2020 **2.739**, 2021 **3.994**, 2022 **7.339**,
2023 **9.040**, 2024 **10.597**, 2025 **11.443**, 2026 (9 meses) **7.991**.

## 7. Incidencias

| # | Incidencia | Veredicto y decisión |
|---|---|---|
| 1 | **El CSV de 2026 agrega la columna `Matrícula`** después de `Aeronave`: 13 columnas contra las 12 de 2019–2025. | **Cambio de esquema de la fuente.** Se lee **por nombre de encabezado**, nunca por posición. Si falta una columna esperada, la corrida aborta en vez de emitir un CSV corrido. |
| 2 | **Sólo 2019 usa `Domestico` sin tilde y `ATERRIZAJE`/`DESPEGUE` en mayúsculas.** | **Defecto de origen.** Se normaliza a la forma de 2020 en adelante y se informa el conteo: 580.764 filas, todas de 2019. |
| 3 | **Cambio de formato numérico**: latina (`140,00`) hasta 2025, entera (`140`) en 2026. | **Cambio de la fuente.** Un único `parse_num` con la regla del último separador cubre los dos. |
| 4 | **Desde 2026 `PAX` viene redondeado al entero** hacia arriba (155 → 78, no 77,5). 95.579 filas de ese año. | **Característica de la fuente.** Sesga `PAX` hacia arriba en los vuelos chicos. No afecta a estos datasets, que no la publican; sí hay que tenerla en cuenta si alguna vez se reconstruye. |
| 5 | **Una fila viola el invariante de `PAX`**: `17/01/2022`, doméstica, aeropuerto `IGU`, destino `2463`, `Pasajeros=3`, `PAX=3`. El destino no es un código de aeropuerto. | **Defecto de origen**, una fila en ~5 millones. Se **deja sin modificar** y se documenta. No toca a Salta. |
| 6 | **El 42 % de los aterrizajes no tiene aerolínea** (`Aerolinea Nombre = "0"`): 25.923 de 61.558. | **Dato real, no error.** Es aviación general sin explotador declarado. Se etiqueta `Sin informar` y se conserva: borrarla destruiría los segmentos de vuelo privado, escuela y adiestramiento. |
| 7 | **Los nombres de aerolínea cambian a lo largo de la serie**: Austral se funde con Aerolíneas en 2021, LAN Argentina pasa a LATAM, Norwegian sale del país, Andes casi desaparece. Hay 239 nombres distintos. | **Característica de la fuente.** **No se unifican.** ANAC sí agrupa Aerolíneas+Austral y las subsidiarias de LATAM, pero sólo en sus tablas nacionales; replicar ese criterio acá sería reescribir el dato. Una serie por aerolínea **tiene cortes** y hay que resolverlos en el tablero. |
| 8 | **Los dos productos no cierran en internacional** (+143 % o −56 % según cómo se lea «comercial»). | **Agregaciones distintas del mismo sistema.** Se publica la brecha acotada; **no se concilia ni se empalman las series**. El cabotaje sí cierra (+0,4 %). |
| 9 | **Los dos productos cortan el mes con relojes distintos**: la serie oficial en hora local, los microdatos en la fecha publicada (rotulada UTC). **3.849 de los 61.558 aterrizajes (6,3 %)** caen entre las 00:00 y las 02:59 UTC y cambiarían de día —a veces de mes— al pasarlos a UTC−3. | **Límite conocido.** Se deja la fecha **tal como la publica la fuente** y se documenta la magnitud. Convertirla sería inventar una precisión que el archivo no garantiza (no dice si la hora es de bloque o de toque). |
| 10 | **Desplome de 2020**: abril y mayo caen a 53 y 54 aterrizajes contra 658 en enero; en la serie larga, 43 pasajeros en todo julio. Dispara la alarma de saltos de magnitud. | **Dato real.** Cierre de aeropuertos por la pandemia. Se documenta, no se corrige. Una serie que arranque en 2019 necesita la advertencia. |
| 11 | **Metadatos del portal desactualizados**: declara cobertura hasta `2025-01-20` y rotula el recurso 2019 como `XML`. | **Error del catálogo.** Manda el archivo: el recurso 2026 llega al 30/09/2026 y los ocho son `text/csv`. |
| 12 | **La hoja `Notas` rotula la Tabla 12 como `[000]`** y el encabezado de la tabla dice `[#]`. | **Error de la fuente.** Manda el encabezado: 603 movimientos en 2001-01 no son 603 mil. |
| 13 | Mojibake, duplicados y rangos. | **Sin incidencias.** Los ocho CSV decodifican en UTF-8 estricto; `COMPAÑÍA DE AVIACIÓN PARAGUAYA S.A.` y `FB LÍNEAS AÉREAS - FLYBONDI` llegan enteras. Sin claves duplicadas ni valores negativos. |

## 8. Supuestos y limitaciones

1. **`SAL` es el aeropuerto de la ciudad de Salta**, y es el único de la provincia en el dataset.
   Estas series **no** cubren Orán, Tartagal ni ningún aeródromo menor: no están en la fuente.
2. **El dataset B son sólo aterrizajes.** Los pasajeros que suma son los que **llegaron** a Salta;
   los que salieron no están. Para movimiento total del aeropuerto hay que usar el dataset A, o
   volver a correr el script sin el filtro de `Tipo de Movimiento`.
3. **`pasajeros` son los desembarcados.** Es la ocupación del vuelo que aterrizó, sin pasajeros en
   tránsito. La columna `PAX` de la fuente **no se publica**, porque es el reparto de ANAC entre
   los dos aeropuertos del vuelo —la mitad en doméstico, entero en internacional— y no un nivel de
   este aeropuerto. Si alguna vez hace falta para cruzar contra un agregado nacional, se
   reconstruye desde `pasajeros` con esa misma regla.
4. **El dataset A cuenta movimientos, no vuelos.** Un vuelo de cabotaje que llega y se va deja 2
   movimientos en Salta. No dividir por dos para «estimar vuelos»: la mezcla con los
   internacionales hace que el divisor no sea constante.
5. **Las dos series no se empalman.** Tienen definiciones, universos y relojes distintos. Para una
   serie larga va el dataset A completo; el B es la apertura de los últimos años, no su
   continuación.
6. **Una serie por aerolínea tiene cortes societarios**, no sólo de mercado (incidencia 7).
7. **Los últimos tres meses son provisorios** y ANAC revisa hacia atrás: los recursos de 2019 a
   2025 figuran actualizados en abril de 2026. Un número puede cambiar entre corridas sin que
   cambie nada de este proceso; por eso la caché de `fuentes/anac/` es parte del entregable.
8. **Las rutas del dataset A no son todas las de Salta**, sino las que entran en el top 61
   nacional de cada tabla. Una ruta puede aparecer y desaparecer de la serie por quedar fuera del
   ranking, no por dejar de volarse.
9. **Este proceso no construye ningún indicador del Monitor.** Entrega los datasets y su
   documentación; qué métrica se publica y con qué base es decisión del tablero.
