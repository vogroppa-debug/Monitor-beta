# Metodología — Ventas y operaciones de supermercados por jurisdicción (INDEC)

Dataset: `Supermercados_INDEC_jurisdiccion_mensual.csv`
Script que lo genera: `Actualizar_Supermercados_INDEC.md`
Fecha de elaboración: 2026-11-18.

## Resultado en una línea

Ventas y cantidad de operaciones de supermercados, mensuales, para las 26 jurisdicciones que abre
el INDEC —Salta entre ellas—, de enero de 2017 a agosto de 2026, en pesos corrientes y en pesos
constantes de julio de 2026: **9.022 filas**, construidas desde un solo cuadro de una sola planilla
oficial, con cuatro controles cruzados que cierran en cero.

## 1. Fuente

**Encuesta de Supermercados**, INDEC — Dirección Nacional de Estadísticas Económicas, Dirección de
Estadísticas de Comercio y Servicios.

| | |
|---|---|
| Página | <https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-1-34> |
| Archivo | <https://www.indec.gob.ar/ftp/cuadros/economia/serie_supermercados.xlsx> (863 KB) |
| Cuadro leído | **Cuadro 6** — «Ventas totales a precios corrientes por boca de expendio, metro cuadro y por operación según jurisdicción, en miles de pesos, unidades, metro cuadrado y pesos» |
| Frecuencia | Mensual (`R/P1M`), según el calendario anticipado del INDEC |
| Metodología | *Metodología INDEC N° 30*, octubre de 2018, ISBN 978-950-896-526-4 |
| Licencia | *«Esta publicación utiliza una licencia Creative Commons. Se permite su reproducción con atribución de la fuente.»* |

**Deflactor**: `ipc_noa_mensual.csv` — IPC Nivel General Región NOA del INDEC, base dic-2016=100,
serie `148.3_INIVELNOA_DICI_M_21` de datos.gob.ar. Es el mismo archivo que usa `adapters.py` en el
sitio, de modo que los pesos constantes de este dataset son comparables con los de los tableros
fiscales.

**Archivo de control, no fuente**: <https://www.indec.gob.ar/ftp/cuadros/economia/sh_super_mayoristas.xls>,
la serie histórica 2017-2022 en formato `.xls` (BIFF). Se usa para contrastar la lectura; no aporta
ningún dato que la planilla actual no traiga, y ésta llega cuatro años más lejos.

### Lo que se descartó, y por qué

**La Encuesta de Autoservicios Mayoristas no abre por provincia.** Publica cuatro jurisdicciones
—Total del país, Ciudad Autónoma de Buenos Aires, 24 partidos del Gran Buenos Aires y «Resto del
país»— y Salta queda dentro de la última, sin forma de separarla. Lo verifiqué en los dos archivos
que el INDEC publica, `serie_autoservicios_mayoristas.xlsx` y los cuadros 8 y 9 del histórico
`sh_super_mayoristas.xls`: **la palabra «Salta» no aparece una sola vez**. Su panel es de 33
empresas y ~190 bocas en todo el país, contra 101 empresas y ~3.126 bocas de supermercados.

## 2. Cobertura y unidad de análisis

### Qué mide la encuesta

Es un **panel, no un censo**. En palabras del INDEC: *«Tipo de encuesta: panel no probabilístico»*.
Entran las empresas *«que cuentan por lo menos con alguna boca de expendio cuya superficie en el
salón de ventas sea igual o supere los 200 m2 o que la suma de la superficie del salón de ventas de
todas sus bocas de expendio sea igual o supere los 200 m2»*, clasificadas en ClaNAE 47.111
(hipermercados), 47.112 (supermercados) y 47.113 (minimercados). Quedan afuera los almacenes de
barrio, los autoservicios chicos y los mayoristas.

El propio INDEC advierte: *«Las ventas totales registradas mensualmente de los supermercados […] no
se deben considerar aisladamente como un indicador macroeconómico del consumo.»*

### Definiciones literales

- **Ventas**: *«monto total en pesos, sin centavos, de las ventas realizadas durante el mes de
  referencia […] valuadas al precio de venta en el establecimiento vendedor, neto de bonificaciones
  o descuentos realizados en el local; se incluye el valor del IVA (impuesto al valor agregado), no
  así los cargos o intereses por financiación»*.
- **Operaciones**: *«número de operaciones efectuadas según la ubicación geográfica de la boca de
  expendio donde se realizaron las ventas en el mes calendario de referencia»*.
- **Asignación geográfica**: por **ubicación de la boca de expendio**, no por domicilio de la
  empresa.
- **Período de referencia**: mes calendario.
- **Revisión**: *«los datos permanecen en estado provisorio hasta 24 meses posteriores a su
  publicación, los cuales luego de su revisión pasan a estado definitivo»*.

### Qué incluye el dataset

- **26 jurisdicciones × 116 meses**, de **2017-01 a 2026-08**, sin un solo hueco. La apertura
  provincial existe desde enero de 2017, cuando *«la ampliación del panel permite desagregar los
  datos relevados para las 23 provincias y la Ciudad Autónoma de Buenos Aires»*.
- Buenos Aires viene **partida** por el INDEC en «24 partidos del Gran Buenos Aires» y «Resto de
  Buenos Aires»; CABA va aparte. No se reconstruye la provincia sumando los dos pedazos.
- **No se emite `Cantidad de bocas`**, aunque el cuadro la trae: es el tamaño del panel relevado,
  no el número de supermercados de la jurisdicción. Publicarla junto a las ventas invita a leerla
  como un censo de bocas.

## 3. Esquema del CSV

`Supermercados_INDEC_jurisdiccion_mensual.csv` — 9.022 filas.

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | entero | Año |
| `n_mes` | entero 1-12 | Mes |
| `mes` | fecha ISO | Primer día del mes, `AAAA-MM-01` |
| `periodo` | texto | `AAAA-MM` |
| `jurisdiccion` | texto | Nombre tal como lo escribe el INDEC (26 valores, `Total del país` incluido) |
| `metrica` | texto | `ventas_corrientes_pesos` \| `ventas_constantes_pesos` \| `cantidad_operaciones` |
| `valor` | número | Pesos con 2 decimales las dos de ventas; entero las operaciones |
| `calidad` | texto | `DEFINITIVO` \| `PROVISORIO` (últimos 24 meses) |

Sólo se emiten las combinaciones que existen: un mes sin IPC no lleva fila de
`ventas_constantes_pesos`. Reparto actual: 3.016 filas de ventas corrientes, 3.016 de operaciones y
2.990 de constantes; 1.846 `PROVISORIO` y 7.176 `DEFINITIVO`.

### Columnas derivadas (las únicas que agrega este proceso)

- `anio`, `n_mes`, `mes` y `periodo` salen de la fecha de la columna A de la planilla.
- `calidad`, de la regla de los 24 meses (§5).
- `ventas_constantes_pesos`, de la deflactación (§5).

## 4. Formato numérico detectado

| Columna / archivo | Configuración detectada | Criterio usado |
|---|---|---|
| `serie_supermercados.xlsx`, todas las columnas numéricas | **Ninguna**: es XLSX, los valores están guardados como número de coma flotante, no como texto | No hay separador que interpretar. Verifiqué que **ningún** valor de las 3.016 celdas de cada variable llega como cadena |
| `serie_supermercados.xlsx`, `Ventas totales` | Unidad **«Miles de pesos»**, declarada en la fila 5 del cuadro | Se lee la etiqueta de unidad y, si cambiara, la corrida aborta |
| `ipc_noa_mensual.csv` | **Inglesa**: decimal `.`, sin separador de miles | Lectura directa; el archivo lo produce otro proceso del repo |
| Codificación de la planilla | Irrelevante (XLSX es ZIP+XML); el `.xls` de control se lee con `xlrd` | — |

**La regla del último separador de la skill `datasets` no aplica a esta fuente**, porque no hay
texto numérico que parsear. El único riesgo de magnitud es la conversión de unidad, que está
documentada abajo y verificada contra otros dos cuadros del mismo archivo.

**Salida:** separador `,`; decimal `.`; sin separador de miles; codificación **UTF-8 con BOM**
(`utf-8-sig`), igual que el resto de los datasets del proyecto.

## 5. Transformaciones aplicadas

1. **Miles de pesos → pesos.** Las ventas vienen en «Miles de pesos» y se multiplican por 1.000.
   Los valores de origen traen **más de tres decimales**, así que el resultado son pesos **con
   centavos**, no pesos enteros: `169.582,82973` miles = `169.582.829,73` pesos. Se redondea a 2
   decimales. Es exactamente la forma que tendría un separador de miles mal leído, por eso queda
   escrito acá, y por eso se verifica contra dos cuadros independientes (§6).
2. **Pesos constantes.** `constantes = corrientes × IPC_base / IPC_del_mes`, con el IPC Nivel
   General Región NOA. **Cada mes se deflacta con su propio índice**, no con un promedio anual: es
   un flujo mensual, y es la regla que el repo ya fijó para Recaudación y Recursos. **La base es el
   último mes con IPC publicado** —la misma que calcula `adapters.py:_ipc_base()`—, de modo que los
   montos reales sean comparables entre tableros. En la corrida del 2026-11-18 la base es
   **2026-07**, IPC = 12.181,1952.
3. **`calidad` por la regla de los 24 meses.** El INDEC declara que los datos quedan provisorios
   hasta 24 meses después de publicados. El archivo actual **ya no los marca**; el histórico sí,
   con un asterisco en el nombre del mes, y son exactamente los últimos 24 (desde 2020-10, con la
   serie terminando en 2022-09). Se aplica la regla por cálculo sobre el último mes del archivo:
   hoy, de 2024-09 en adelante.
4. **Nombres de jurisdicción sin tocar**, incluida la partición de Buenos Aires.
5. **No se emite `Cantidad de bocas`** ni las tres razones que calcula el INDEC (`Ventas por boca`,
   `Ventas por m2`, `Ventas por operación`): el cociente queda para el tablero, como en el resto
   del proyecto.
6. **Ordenamiento determinista**: por orden de jurisdicción en la planilla, año, mes y métrica.

## 6. Verificación de totales

Corrida del **2026-11-18**.

### Controles internos que cierran

- **Suma de las jurisdicciones = Total del país.** En ventas y operaciones, los 116 meses: desvío
  relativo máximo **2,55e-13**, que es error de punto flotante.
- **Cobertura sin huecos**: 116 meses consecutivos, 2017-01 a 2026-08, para las 26 jurisdicciones.
  Ni un valor vacío, ni un cero, ni un valor no numérico.
- **Saltos de orden de magnitud**: ninguno disparó la regla (>100× o <1/100 de la mediana de su
  serie). Las ventas nominales de Salta se multiplican por 86 entre 2017 y 2026 —inflación, dato
  real—, pero la razón máximo/mediana es 17,4, bien por debajo del umbral.
- **Mes base**: en 2026-07, `ventas_corrientes_pesos` y `ventas_constantes_pesos` dan idénticos,
  como tiene que ser por construcción.

### Controles cruzados independientes

| Control | Contra qué | Resultado |
|---|---|---|
| Ventas por jurisdicción | «Total» del cuadro de ventas **por grupo de artículos** (otro cuadro de la misma planilla) | 3.016 valores, **0 discrepancias** |
| Total del país | Cuadro nacional **en millones de pesos** (otro cuadro de la misma planilla) | 116 valores, **0 discrepancias** |
| Salta, ventas y operaciones | **Serie histórica 2017-2022**, que es otro archivo del INDEC, en otro formato (`.xls` BIFF) y con otra disposición | 69 meses, **0 discrepancias** |

El tercero es el más fuerte: reproduce exactamente lo que el INDEC publicaba en 2022, leyendo un
archivo distinto con una librería distinta. La única diferencia que existía entre los dos archivos
estaba en la cantidad de bocas de 2022-09 (50 en el histórico, 51 en el actual) —una revisión del
INDEC, coherente con su política— y esa columna no se emite.

### Control del deflactor

Comparé el total nacional deflactado por IPC NOA contra la serie a precios constantes que publica
el propio INDEC: las variaciones interanuales **correlacionan 0,71 y difieren en promedio 3,6
puntos porcentuales**. No es un error de cálculo: el INDEC deflacta cada grupo de artículos con su
índice de precios específico y a escala nacional, mientras que acá se usa un índice regional de
nivel general. Ver §8.

### Reproducibilidad

- El bloque `python` de `Actualizar_Supermercados_INDEC.md` es **md5-idéntico** al
  `actualizar_supermercados_indec.py` en disco (`ab307eebee2df5f6206df4f3a58aa4c0`).
- Dos corridas seguidas producen un CSV con el mismo md5
  (`6794a8d85c53103f83c74fed0ae5a041`).

### Valores de control

Salta, en pesos (constantes de jul-2026):

| Mes | Ventas corrientes | Ventas constantes | Operaciones |
|---|---|---|---|
| 2017-01 | 529.248.073,00 | 63.452.610.755,73 | 1.527.981 |
| 2020-04 | 1.448.956.560,54 | 55.644.356.724,50 | 1.011.235 |
| 2026-07 | 46.149.775.811,14 | 46.149.775.811,14 | 1.166.717 |
| 2026-08 | 45.374.496.988,81 | — | 1.146.918 |

Total del país de 2026-08: **2.616.930.121.204,41** pesos corrientes y **73.573.039** operaciones.
Salta pesa el **1,73 %** de las ventas del país. Sus operaciones mensuales se mueven entre
**806.400** y **1.704.458** a lo largo de los 116 meses. En pesos constantes, las ventas de Salta
de julio de 2026 están **27,3 % por debajo** de las de enero de 2017.

## 7. Incidencias

| # | Incidencia | Veredicto y decisión |
|---|---|---|
| 1 | **La Encuesta de Autoservicios Mayoristas no abre por provincia**: cuatro jurisdicciones y un «Resto del país» que contiene a Salta. | **Límite conocido.** Se descarta la encuesta entera. Queda documentado en §1 para no reintentarlo. |
| 2 | **Los nombres de hoja son inconsistentes**: `Cuadro 1` y `Cuadro 2` sin punto, `Cuadro 3.` a `Cuadro 6.` con punto. | **Defecto de origen.** La hoja se localiza por el texto del título en A1, no por su nombre. |
| 3 | **El archivo actual ya no marca lo provisorio.** El histórico lo hacía con un asterisco en el nombre del mes. | **Cambio de la fuente.** Se aplica la regla de 24 meses que el INDEC declara, validada contra los asteriscos del histórico, donde son exactamente los últimos 24. |
| 4 | **Las ventas vienen en «miles de pesos» con más de tres decimales.** | **Unidad de origen.** ×1.000 da pesos con centavos; se redondea a 2 decimales y se verifica contra otros dos cuadros. |
| 5 | **El IPC NOA llega a 2026-07 y las ventas a 2026-08.** | **Límite conocido.** El último mes sale sin `ventas_constantes_pesos`. Se reporta en cada corrida. |
| 6 | **`ipc_noa_mensual.csv` está tres meses atrasado** respecto de lo que publica la API (llega a 2026-07; hay datos hasta 2026-10). | **Dato pendiente de actualizar, ajeno a esta fuente.** Hay un flag `--actualizar-ipc`, apagado por defecto: el archivo es compartido por todo el sitio y extenderlo mueve la base de los pesos constantes de todos los tableros. |
| 7 | **Deflactar con IPC NOA no reproduce la serie a precios constantes del INDEC** (correlación 0,71 en variaciones interanuales; 3,6 pp de diferencia media). | **Diferencia de método, no error.** Índice regional de nivel general contra deflactores nacionales por grupo de artículos. Ver §8. |
| 8 | **Las ventas nominales se multiplican por 86** entre 2017 y 2026. | **Dato real**: inflación. No dispara la regla de saltos de magnitud (máx/mediana = 17,4 en Salta). Es la razón por la que se publica la serie constante. |
| 9 | **Una revisión del INDEC** entre el histórico y el archivo actual: las bocas de Salta de 2022-09 pasaron de 50 a 51. | **Revisión de la fuente**, coherente con su política de 24 meses. Manda el archivo actual. No afecta al dataset: las bocas no se emiten. |
| 10 | Mojibake, duplicados y rangos. | **Sin incidencias.** Ninguna secuencia `Ã`, `Â` ni `â€` pese a los acentos de `Córdoba`, `Entre Ríos`, `Neuquén`, `Río Negro` y `Tucumán`; 0 claves `(periodo, jurisdiccion, metrica)` duplicadas; 0 negativos; 0 valores que no parseen. |

## 8. Supuestos y limitaciones

1. **Es un panel, no el universo.** Las ventas son las de las empresas relevadas, no las de todo el
   comercio minorista de alimentos de Salta, y no hay expansión a universo. El INDEC pide
   expresamente que no se lea como indicador de consumo. Esa salvedad tiene que viajar con el dato,
   en el copete del indicador.
2. **El deflactor es una elección del proyecto.** Se usa el IPC Nivel General Región NOA porque es
   el que el sitio usa en todos sus tableros y porque, para una serie de Salta, un índice regional
   es más pertinente que uno nacional. La consecuencia es que **esta serie constante no coincide
   con la que publica el INDEC**: sus deflactores son específicos por grupo de artículos y de
   alcance nacional. La divergencia está medida en §6 y es estable, no errática.
3. **La base de los pesos constantes se mueve.** Es el último mes con IPC publicado. Cuando se
   actualice `ipc_noa_mensual.csv`, este CSV hay que regenerarlo, o quedará en una base distinta de
   la del resto del sitio. Si más adelante se arma el tema del Monitor, `adapters.py` debería
   deflactar al momento del build desde `ventas_corrientes_pesos` —como ya hace con los demás
   tableros— y no usar la columna precalculada.
4. **`calidad` es una inferencia, no un dato del archivo.** Sale de aplicar la regla de 24 meses que
   el INDEC declara en su metodología. Está validada contra los asteriscos del archivo histórico,
   pero el archivo actual no la marca.
5. **Los últimos meses se van a mover.** Por la misma política de revisión, los valores provisorios
   cambian de una publicación a otra. Por eso la copia local del original va fechada.
6. **Buenos Aires llega partida** en «24 partidos del Gran Buenos Aires» y «Resto de Buenos Aires».
   Sumarlos da la provincia, pero esa suma no se hace acá.
7. **No hay serie previa a 2017.** La apertura por jurisdicción nace con la ampliación del panel de
   enero de 2017. Las series base 2008 que el INDEC publica en «Estadísticas históricas» son
   nacionales.
8. **No se controlan los cambios de panel.** Si una cadena entra o sale del relevamiento, el salto
   aparece en las ventas de la jurisdicción y el INDEC no publica una nota por jurisdicción que
   permita identificarlo.
9. **La actualización metodológica de 2025 («método directo») no afecta a este dataset**: es sobre
   desestacionalización —X-13ARIMA-SEATS, estimación de la tendencia-ciclo— y toca las series de
   índices, no los niveles de ventas y operaciones que se leen acá. No hay quiebre de serie.
