# Metodología — Padrón de empresas exportadoras de Salta (ArgentinaTradeNet)

Dataset: `Exportadores_Salta_ArgentinaTradeNet.csv`.
Runbook y script: `Actualizar_Exportadores_Salta_ArgentinaTradeNet.md`.
Fecha de elaboración: **2026-09-20**. Primera toma: **2026-09-20**.

## Fuente

- **Organismo:** Ministerio de Relaciones Exteriores, Comercio Internacional y Culto (Cancillería),
  programa **ArgentinaTradeNet** — *Directorio de Exportadores*.
- **Portal:** <https://cancilleria.gob.ar/es/argentinatradenet/directorio-de-contactos/directorio-de-exportadores>
- **De dónde sale realmente el dato:** esa página es una cáscara de Drupal con **dos iframes** a
  `https://exportaciones.cancilleria.gob.ar`, una aplicación CakePHP independiente. El relevamiento
  se hace contra esa aplicación:
  - Listado: `POST /sitios/tabla_directorios_exportadores/1` con `pageNo=1..280`. Devuelve JSON
    (`total`, `pageNo`, `result`); `result` es un fragmento HTML del que se extraen los
    identificadores `ficha_directorio/{id}`.
  - Ficha: `GET /sitios/ficha_directorio/{id}`.
- **Por qué esos endpoints y no los de la interfaz pública:** la aplicación expone dos interfaces
  sobre los mismos datos. La pública, que es la embebida en la página, tiene el listado **topeado en
  100 filas sin paginado** y una ficha reducida (`ficha_directorio_mobile`) que **no incluye
  domicilio, provincia, certificaciones ni el campo de productos orgánicos**. Usarla haría imposible
  el filtro provincial. Los endpoints elegidos son los de la interfaz anterior, accesibles
  anónimamente y completos.
- **Acceso:** no requiere usuario, sesión ni cookies, pese a que la página promociona "Inicie
  sesión". No hay CAPTCHA ni WAF. `robots.txt` de `cancilleria.gob.ar` no prohíbe estas rutas
  (declara `Crawl-delay: 10` para el host institucional, que este proceso consulta una sola vez);
  el host `exportaciones.cancilleria.gob.ar` no publica `robots.txt`. Aun así el script usa 4 hilos
  y pausa entre pedidos.
- **Licencia:** no se declara ninguna. Es un directorio público de promoción comercial.

## Cobertura y unidad de análisis

| | |
|---|---|
| Universo recorrido | **2.663** fichas del padrón nacional (280 páginas × 10) |
| Errores de descarga | **0** |
| Empresas de Salta | **30** |
| Unidad de análisis | La **empresa registrada**, identificada por su razón social |
| Clave del dataset | `fecha_registro` + `empresa` |
| Periodicidad | La que decida el CESS; prevista semestral o anual |

**Criterio de pertenencia a Salta:** 29 empresas porque la ficha declara `Provincia: Salta`, y 1 más
recuperada por ciudad/localidad entre las fichas sin provincia. La columna `criterio_salta`
distingue ambos casos (`provincia` / `imputada`).

**El conteo es un piso, no un valor exacto.** 458 de las 2.663 fichas del país (17,2 %) no declaran
provincia; de ellas sólo se recupera la que menciona Salta en ciudad o localidad. Cualquier empresa
salteña que haya dejado vacíos los tres campos es invisible para este método y para cualquier otro.

## Esquema del CSV

Separador `,`; codificación **UTF-8 con BOM** (`utf-8-sig`); una fila por empresa y por
relevamiento. Formato **ancho**: una columna por posición arancelaria.

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha_registro` | fecha | Día del relevamiento. La fuente no tiene fecha propia (ver incidencia 5). |
| `empresa` | texto | **Razón social.** Es el dato autoritativo y la unidad de conteo. |
| `nombre_fantasia` | texto | Encabezado de la ficha, cargado libremente por el inscripto. |
| `codigo_tradenet` | texto | Identificador del registro, p. ej. `EXPCANCI7582`. |
| `provincia` | texto | Siempre `Salta`. |
| `ciudad`, `localidad` | texto | Tal como los carga la empresa. Ver incidencia 2. |
| `departamento` | texto | **Derivado.** Uno de los 23 canónicos o `Sin asignar`. |
| `organicos` | texto | `Sí` / `No` según la ficha. |
| `certificaciones` | texto | Certificaciones declaradas y "otras certificaciones", separadas por `;`. |
| `n_posiciones` | entero | Cantidad de posiciones arancelarias declaradas. |
| `Posición 1` … `Posición 19` | **texto** | Código NCM. **No es numérico** (ver abajo). |
| `criterio_salta` | texto | `provincia` o `imputada`. |
| `url_ficha` | texto | Enlace a la ficha, para auditar la fila contra la fuente. |

En esta primera toma el máximo de posiciones de una empresa es **19**, de modo que el archivo tiene
32 columnas. El ancho se recalcula en cada corrida y se unifica con el de las tomas previas.

### Columnas derivadas (las únicas que agrega el proceso)

- **`departamento`**: cruce de `localidad` y, si falla, `ciudad`, contra el padrón municipal de
  `Salta_recursos_municipios_mensual.csv` (60 municipios → los 23 departamentos canónicos, con la
  grafía del resto del Monitor), ampliado con alias para las variantes y erratas observadas
  (`Salta capital`, `Slata Capital`, `Rosario de LaFrontera`, `Oran`). La comparación se hace en
  mayúsculas y sin acentos. **Lo que no matchea queda en `Sin asignar`**: no se usa la
  normalización genérica del proyecto porque ante un nombre desconocido devuelve el texto
  capitalizado y fabricaría un departamento inexistente.
- **`n_posiciones`**, **`criterio_salta`** y **`fecha_registro`**.

## Formato numérico detectado

El dataset **no tiene magnitudes numéricas**: es un padrón. La única columna entera es
`n_posiciones`, calculada por el proceso. No hay separadores decimales ni de miles que resolver.

| Columna | Configuración | Criterio |
|---|---|---|
| `Posición 1..N` | **texto, no numérico** | Los códigos NCM llevan ceros a la izquierda (`07102200`) y relleno con guiones (`07----`, `1005--`, `071320--`). Convertirlos a número los destruye. |
| `n_posiciones` | entero | Derivada; recuento. |
| resto | texto | Nombres, domicilios y certificaciones. |

**Relectura de control:** se relee el CSV escrito con `utf-8-sig` y se verifica que para cada fila
la cantidad de celdas `Posición N` no vacías coincida con `n_posiciones`. En esta toma: **30 de 30
correctas**.

## Transformaciones aplicadas

1. Recorrido de las 280 páginas del listado y extracción de los identificadores de ficha
   (2.663 únicos).
2. Descarga de cada ficha con caché en `fuentes/tradenet/`, escritura atómica (`.tmp` → `replace`)
   para poder interrumpir y retomar, y reintento con espera creciente.
3. Parseo de los campos por su etiqueta literal (`<b>Etiqueta:</b>`), decodificando en **UTF-8** y
   resolviendo entidades HTML.
4. **Certificaciones**: la lista controlada se cierra en la fuente con una etiqueta `</select>`
   huérfana (defecto del template); se usa esa marca como delimitador y se le suma el campo libre
   "Otras Certificaciones", deduplicando.
5. **Posiciones arancelarias**: el campo es un bloque con líneas `código - descripción`; se conserva
   **sólo el código, como texto**, en el orden de la ficha. La descripción queda en la ficha
   original, enlazada en `url_ficha`.
6. Filtro por provincia e imputación por ciudad/localidad para las fichas sin provincia.
7. Derivación del departamento y volcado a formato ancho.
8. **Acumulación**: si el CSV existe, se leen las tomas anteriores, se descartan las filas cuya
   `fecha_registro` coincida con la corrida (para que re-correr el mismo día no duplique) y se
   concatena la toma nueva, unificando el conjunto de columnas `Posición N`.

## Verificación

### Controles internos que cierran
- **Descarga**: 2.663 fichas, **0 errores**.
- **Determinismo del padrón**: el recorrido del listado es estable; dos pasadas devuelven el mismo
  conjunto de identificadores.
- **Coherencia posiciones**: `n_posiciones` coincide con las celdas `Posición N` llenas en las 30
  filas.
- **Acumulación**: correr dos veces el mismo día deja 30 filas; simular una segunda fecha deja 60
  filas repartidas en dos `fecha_registro`. Verificado.

### Control cruzado independiente
Se reprocesaron las 30 fichas con un parser independiente, escrito aparte del usado en el script, y
se compararon `empresa`, `provincia`, `organicos` y el recuento de posiciones contra el CSV:
**0 discrepancias sobre 30 fichas**.

Como contraste externo, el propio sitio anuncia "+2.600 empresas exportadoras argentinas", coherente
con las 2.663 relevadas.

## Incidencias

| # | Incidencia | Veredicto y decisión |
|---|---|---|
| 1 | **El 17,2 % de las fichas del país (458 de 2.663) no declara provincia.** | **Limitación de origen.** Se recupera lo posible por ciudad/localidad — 1 empresa salteña así identificada. El conteo de Salta es un **piso**. Se expone el criterio en la columna `criterio_salta`. |
| 2 | **`Ciudad` y `Localidad` son campos distintos pero se usan de manera inconsistente.** A veces ciudad es el departamento y localidad el pueblo, a veces al revés, y en 179 fichas del país la localidad repite la provincia. En Salta, 17 de 30 empresas dejan ambos vacíos. | **Dato real, mal cargado en origen.** Se conservan **las dos columnas crudas**, sin fusionarlas, y el departamento derivado queda en `Sin asignar` cuando no hay con qué. |
| 3 | **El encabezado de la ficha no es la razón social.** En 9 de las 30 fichas de Salta difieren, y en una muestra nacional de 400 fichas difieren en el 36 %. El caso extremo: la ficha `86279` se titula `MINERA SANTA RITA SRL` pero su razón social es `MANUFACTURAS LOS ANDES S.A`, y existe otra ficha (`81916`) que sí es Minera Santa Rita. Otra ficha se titula con el nombre de una persona (`ALVARO HERRERA`) y su razón social es `OXIGENO Y TECNOLOGIA S.R.L.`. | **Defecto de la fuente, con consecuencia directa sobre el conteo.** Contar por el encabezado fusionaría dos empresas distintas en una. Se **cuenta por razón social** y se conserva el encabezado en `nombre_fantasia` para poder auditarlo. Con este criterio, las 30 empresas son 30 razones sociales distintas. |
| 4 | **17 de 30 empresas quedan sin departamento.** | **Consecuencia de la incidencia 2**, no del cruce: esas fichas no traen ni ciudad ni localidad. De las 13 que sí los traen, **las 13 matchearon**: Capital 8, Rosario de la Frontera 3, Cerrillos 1, Orán 1. |
| 5 | **La fuente no tiene fecha.** Ni el directorio ni las fichas informan fecha de alta, de actualización ni de vigencia. | **Limitación estructural.** La única fecha del dataset es la del relevamiento, que pone este proceso. Es la razón por la que el archivo es acumulativo: la serie se construye desde afuera. |
| 6 | **Ningún registro salteño declara exportar productos orgánicos** (30 de 30 en `No`). A nivel país sólo el 2,2 % declara `Sí`. | **Dato real.** Se publica tal cual. No debe leerse como ausencia de producción orgánica en Salta, sino como ausencia de la declaración en este registro. |
| 7 | **Sólo 3 de 30 empresas declaran certificaciones** (ISO 9001, ISO 14001, HACCP-APPCC). | **Dato real**, coherente con el carácter incompleto del registro. |
| 8 | Saltos de orden de magnitud, mojibake y duplicados de clave. | **Sin incidencias.** No aplica el control de magnitudes (no hay variables numéricas). El texto se decodifica en UTF-8 estricto y no se observaron caracteres corruptos. No hay claves `fecha_registro` + `empresa` repetidas. |

## Supuestos y limitaciones

1. **El directorio es de inscripción voluntaria y auto-declarada.** Mide empresas *registradas como
   exportadoras*, no empresas que exportaron. No es un censo ni un padrón fiscal, y su variación
   entre tomas puede reflejar altas y bajas administrativas antes que actividad económica real. Es
   la advertencia más importante para cualquier uso del conteo.
2. **No hay validación de los datos por parte del organismo**: los campos los carga la empresa. De
   ahí los domicilios vacíos, los encabezados con nombres de personas y las erratas
   (`Slata Capital`, `Rosario de LaFrontera`).
3. **Las 30 empresas no son comparables con las exportaciones del INDEC** ya publicadas en el
   Monitor: aquéllas miden flujos de comercio por provincia de origen declarada en la operación;
   ésta, inscripciones en un directorio de promoción comercial. Son universos distintos.
4. **Las posiciones arancelarias mezclan niveles de agregación**: conviven capítulos (`07----`),
   partidas (`1005--`) y posiciones completas de ocho dígitos. `n_posiciones` cuenta todas las
   declaradas, sin distinguir jerarquía.
5. **La caché de fichas no se distribuye** con el dataset (20 MB, 2.663 archivos) porque se
   regenera en unos 5 minutos y cada fila lleva su `url_ficha` para auditarla contra la fuente viva.
6. **El sitio puede cambiar.** El script depende de dos endpoints de una interfaz anterior y del
   etiquetado de los campos de la ficha; si el organismo rediseña la aplicación, el proceso debe
   fallar ruidosamente y no en silencio. Conviene revisar el conteo contra la toma previa antes de
   publicar.
