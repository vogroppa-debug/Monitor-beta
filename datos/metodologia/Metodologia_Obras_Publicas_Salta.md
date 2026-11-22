# Metodología — Padrón de obras públicas de Salta, reclasificado

Dataset: `Obras_Publicas_Salta_padron_clasificado.csv`
Script: `actualizar_obras_publicas_salta.py`
Corrida de referencia: 21 de noviembre de 2026.

---

## 1. Fuente

| | |
|---|---|
| Título | Padrón Georreferenciado de Obras Públicas de la Provincia de Salta (2020–2026) |
| Organismo | Jefatura de Gabinete de Ministros de la Provincia de Salta |
| Portal | `https://datospublicos.salta.gob.ar/dataset/a3ac6004-0430-42e3-ac16-50c9c5956083` |
| Licencia | Creative Commons Attribution 4.0 |
| Última modificación del recurso | 17 de noviembre de 2026, 23:46 |
| Método | descarga del CSV, con la URL resuelta por la API de CKAN (`package_show`) |
| Universo | 2.947 obras; 2.389 con avance 100 % |

El script **no hardcodea la URL de descarga**: pide `package_show` al CKAN del portal y toma el
primer recurso en formato CSV. El `resource_id` cambia cuando el organismo republica el archivo;
el `dataset_id` no. Queda una URL de respaldo, la vigente al 17-nov-2026, por si la API no
responde, y en ese caso el script lo informa como incidencia.

### Columnas del archivo original

`id`, `nombre`, `descripcion`, `area_responsable`, `tipo`, `etapa`, `porcentaje_avance`,
`monto_contrato`, `financiamiento`, `jurisdiccion` (departamento), `comuna` (municipio), `lat`,
`lng`, `fecha_fin_inicial`, `licitacion_anio`, `mano_obra`, `beneficiarios`, `destacada`.

---

## 2. Por qué se reclasifica

El campo `tipo` de la fuente tiene nueve valores y **«OTRAS» se lleva 1.048 obras, el 35 % del
padrón**:

| tipo de la fuente | obras |
|---|---|
| OTRAS | 1.048 |
| OBRAS VIALES | 499 |
| VIVIENDAS | 443 |
| ARQUITECTURA | 326 |
| ALUMBRADO PUBLICO | 275 |
| AGUA Y SANEAMIENTO | 237 |
| OBRAS HÍDRICAS | 65 |
| CONECTIVIDAD ELÉCTRICA | 43 |
| GAS | 11 |

Dentro de «OTRAS» conviven defensas de río, refacciones de escuela, terminales de ómnibus y
limpieza de canales. Con el padrón tal como se publica no se puede contestar cuántas obras de
cordón cuneta se hicieron, ni cuánto se intervino en escuelas, ni separar una obra nueva de una
refacción. Tampoco ayuda `area_responsable`, que es la repartición que ejecuta y no el tipo de
obra.

La reclasificación agrega **dos ejes separados**, construidos sobre el texto de `nombre` y
`descripcion`:

- **`categoria`** — *qué* se intervino: 31 etiquetas.
- **`accion`** — *qué se hizo* con eso: construir, ampliar, refaccionar, mantener, proveer.

Son dos ejes y no uno porque «Refacciones varias en la escuela N.º 4483» es una escuela en el
primero y una refacción en el segundo, y así se pueden cruzar sin multiplicar las etiquetas.

**Esto es una clasificación propia del CESS, no un campo de la fuente.** Va dicho en el dataset
(columna `regla`), en las notas del build y en la advertencia del tablero.

---

## 3. Cómo clasifica

Sobre `nombre + " | " + descripcion`, normalizados a minúsculas, sin acentos y sin puntuación, se
evalúa una **lista ordenada** de pares *(etiqueta, expresión regular)*. **Gana la primera que
matchea: el orden es la prioridad.** Va de lo específico a lo genérico, y eso resuelve los
solapamientos reales del padrón:

- `cordón cuneta` antes que `pavimento` — «Construcción de cordón cuneta y pavimento articulado»
  es, para esta clasificación, una obra de cordón cuneta.
- `núcleos húmedos` antes que `red de agua potable`.
- `escuela` antes que `edificio`.
- `veredas` antes que `pavimento`.

**El 26 % de las obras dispara dos o más reglas.** Por eso el dataset trae dos columnas y no una:

- `categoria` guarda la ganadora;
- `etiquetas` guarda **todas** las que matchearon, separadas por `|`, así nada se pierde;
- `regla` dice de dónde salió la asignación —el patrón que disparó, el respaldo por `tipo`, o
  `sin regla`—, de modo que cada fila se puede auditar sin volver a correr el script.

Reglas que matchean por obra, sobre las 2.389 finalizadas:

| reglas que matchean | obras |
|---|---|
| 0 | 199 |
| 1 | 1.543 |
| 2 | 583 |
| 3 | 57 |
| 4 | 7 |

### Respaldo por el `tipo` de la fuente

Si ninguna regla matchea, se usa el `tipo` publicado: `OBRAS VIALES` → *Otras obras viales*,
`AGUA Y SANEAMIENTO` → *Otras obras de agua y saneamiento*, `OBRAS HÍDRICAS` → *Otras obras
hidráulicas*, `CONECTIVIDAD ELÉCTRICA` → *Red eléctrica y suministro de energía*,
`ALUMBRADO PUBLICO`, `VIVIENDAS`, `GAS` y `ARQUITECTURA` → *Otras obras de arquitectura*.
`OTRAS` no aporta nada, así que esas obras quedan en **«Otras obras»**.

### Cobertura

| origen de la etiqueta | obras al 100 % | % |
|---|---|---|
| una regla sobre el texto | 2.190 | 91,7 |
| el `tipo` de la fuente | 101 | 4,2 |
| ninguna de las dos → «Otras obras» | **98** | **4,1** |

Las 98 sin regla son casos sueltos que la fuente tampoco abre: complejos fronterizos, obras de
emergencia sin objeto declarado, trabajos en el Centro de Convenciones, provisión de materiales.
**No se escribió una regla a medida de cada una**: una regla hecha para un caso único no es una
regla, y arrastraría obras futuras a la etiqueta equivocada. Quedan en una etiqueta residual
honesta.

---

## 4. Las reglas, en orden de prioridad

### `categoria`

| # | etiqueta | obras al 100 % | patrón |
|---|---|---|---|
| 1 | Cordón cuneta | 170 | `cordon ?cuneta\|cordon y cuneta\|cordones cuneta` |
| 2 | Veredas y peatonales | 21 | `vereda\|peatonal\|senda peatona` |
| 3 | Adoquinado | 25 | `adoquin` |
| 4 | Bacheo y mantenimiento vial | 6 | `bacheo\|bachear\|\bbaches\b\|perfilado\|mantenimiento de calle\|reparacion de calle` |
| 5 | Pavimento y calzadas | 204 | `pavim\|carpeta asfaltica\|asfalt\|hormigon simple\|hormigon articulado\|enripiado\|\bripio\b\|estabilizado granular\|calzada` |
| 6 | Puentes y alcantarillas | 30 | `puente\|alcantarill\|\bbadeo\b\|\bvado\b\|pasarela` |
| 7 | Caminos y accesos | 48 | `camino\|acceso vial\|\bruta\b\|apertura de calle\|senaletica\|senalizacion\|portal de acceso\|terminal de omnibus\|estacion terminal\|complejo fronterizo\|paso fronterizo` |
| 8 | Núcleos húmedos y conexiones domiciliarias | 117 | `nucleo ?s? ?humedo\|conexion(es)? domiciliaria\|modulo sanitario\|sistema sanitario\|\bletrina` |
| 9 | Cloacas y saneamiento | 48 | `cloacal\|cloaca\|saneamiento\|efluente\|colectora\|planta de tratamiento\|liquidos residuales\|desagote\|\bbarros\b` |
| 10 | Red de agua potable | 114 | `agua potable\|red(es)? de agua\|acueducto\|cisterna\|tanque de agua\|distribucion de agua\|provision de agua\|potabiliza\|acceso al agua\|agua corriente\|agua para consumo\|\bpead\b\|optimizacion de redes\|recambio (general )?de red\|electrobomba\|canerias? de impulsion\|impulsion\|\bbombeo\b\|red municipal` |
| 11 | Pozos y perforaciones | 35 | `\bpozo\|perforacion` |
| 12 | Defensas y encauzamiento | 86 | `encauz\|encauce\|\bdefensa\|margen\|gavion\|terraplen\|erosion\|\bcauce\b\|rectificacion\|\bazud\b\|\brepresa\b\|\bdique\b\|crecida` |
| 13 | Canales y desagües | 28 | `\bcanal\|desague\|pluvial\|drenaje\|\bzanja` |
| 14 | Otras obras hidráulicas | 13 | `hidraulic\|hidric\|\bcuenca` |
| 15 | Alumbrado público y luminarias | 212 | `luminaria\|alumbrado\|iluminacion` |
| 16 | Red eléctrica y suministro de energía | 128 | `electrific\|electric\|\benergia\|media tension\|baja tension\|transformador\|tendido\|interconexion\|fotovoltaic\|\bsolar\b\|subestacion` |
| 17 | Gas | 15 | `\bgas\b\|gasoducto\|gasificacion\|odorizacion` |
| 18 | Viviendas y soluciones habitacionales | 308 | `vivienda\|habitacional\|urbanizacion\|lote con servicio\|\bloteo\b` |
| 19 | Centros infantiles y comunitarios | 33 | `desarrollo infantil\|centro infantil\|integrador comunitario\|\bcic\b\|merendero\|comedor\|centro comunitario\|club de dia\|\bhogar\b` |
| 20 | Establecimientos educativos | 314 | `escuela\|\besc\b\|colegio\|educativ\|\baula\|jardin de infantes\|nivel inicial\|albergue\|universidad\|profesorado\|bachillerato\|\bu\.? ?c\.? n\b` |
| 21 | Establecimientos de salud | 96 | `hospital\|centro de salud\|puesto sanitario\|\bcaps\b\|primeros auxilios\|\bsalud\b\|\bsanitaria\b\|\bmaternidad\b` |
| 22 | Deporte y recreación | 47 | `deportiv\|playon\|polideportivo\|cancha\|gimnasio\|natatorio\|estadio\|recreativ\|\bpileta\b\|\bpiscina\b` |
| 23 | Cultura, patrimonio y turismo | 23 | `museo\|cultural\|patrimoni\|iglesia\|capilla\|turist\|centro de interpretacion\|biblioteca\|teatro\|\bhotel\b\|\btermas\b\|centro de convenciones\|\bferia\b` |
| 24 | Seguridad y justicia | 10 | `comisaria\|policia\|bombero\|destacamento\|\bpenal\b\|juzgado\|tribunal\|\bcarcel\b` |
| 25 | Edificios públicos y administrativos | 32 | `centro civico\|ministerio\|municipalidad\|\boficina\|\bsede\b\|delegacion\|\bblock\b\|\bedificio\b\|secretaria` |
| 26 | Plazas y espacios públicos | 50 | `\bplaza\|\bparque\b\|\bpaseo\b\|anfiteatro\|espacio publico\|arbolado\|plazoleta\|costanera\|\bmonumento\b\|\bcartel` |
| 27 | Otras construcciones menores | 31 | `tinglado\|\bcerco\b\|cerramiento\|\bmuro\b\|baranda\|galeria\|\bcubierta\|\blosa\b\|\btecho\|mobiliario\|impermeabiliza\|termomecanic\|\bplatea\b\|\bpasillo\b\|fundacion` |

Más cuatro etiquetas que **no** salen de una regla sino del respaldo por `tipo`, o de su ausencia:
*Otras obras de arquitectura* (22), *Otras obras viales* (14), *Otras obras de agua y saneamiento*
(11) y **«Otras obras»** (98).

### `accion`

| # | etiqueta | obras al 100 % | patrón |
|---|---|---|---|
| 1 | Construcción | 731 | `construccion\|construir\|ejecucion de obra\|\bobra nueva\b\|\bnuev[oa]s?\b\|dotacion` |
| 2 | Refacción y puesta en valor | 757 | `refaccion\|remodelacion\|readecuacion\|refuncionaliza\|puesta en valor\|restauracion\|reacondicionamiento\|reparacion\|recambio\|\bcambio\b\|reemplazo\|sustitucion\|renovacion\|revitalizacion\|\bmejora\|optimizacion\|reconstruccion\|terminacion\|finalizacion\|\barreglo\|acondicionamiento\|impermeabiliza` |
| 3 | Ampliación | 48 | `ampliacion\|ampliar\|\banexo\b\|\bextension\b\|repotenciacion\|habilitacion` |
| 4 | Mantenimiento y limpieza | 46 | `mantenimiento\|limpieza\|desmaleza\|conservacion\|bacheo\|perfilado\|desobstruccion\|liberacion de cauce` |
| 5 | Provisión e instalación | 82 | `provision\|suministro\|adquisicion\|instalacion\|equipamiento\|colocacion\|\bprovee` |

**«Sin especificar»: 725 obras, el 30 %.** No es una falla del clasificador: buena parte de los
nombres del padrón enuncian sólo el objeto —«Cordón cuneta en barrio La Esperanza», «Alumbrado
público», «Plaza barrio El Obraje»— sin decir el verbo. Inferir ahí una acción sería inventarla.

`Construcción` va primero a propósito: una obra descrita como «Construcción … Etapa II» es una
construcción en etapas, no una ampliación.

---

## 5. Esquema del CSV de salida

Una fila por obra, **las 2.947**. El universo pedido eran las finalizadas, pero descartar 558
filas del padrón oficial sería perder dato: se marcan con `finalizada` y el tablero las filtra.

| columna | contenido |
|---|---|
| `id` | el del padrón |
| `nombre`, `descripcion` | texto original, con espacios colapsados |
| `area_responsable` | repartición que ejecuta, de la fuente |
| `tipo_fuente` | **el `tipo` original, conservado**: es lo que permite mostrar qué había dentro de «OTRAS» |
| `categoria` | etiqueta nueva: qué se intervino |
| `accion` | etiqueta nueva: qué se hizo |
| `etiquetas` | todas las reglas que matchearon, separadas por `\|` |
| `regla` | el patrón que disparó, `tipo: <TIPO>` o `sin regla` |
| `etapa` | Finalizada / En ejecución / En licitación |
| `finalizada` | 1 si `porcentaje_avance` = 100 |
| `porcentaje_avance` | avance físico, 0–100 |
| `monto_contrato` | pesos corrientes, **sin deflactar** (ver 6) |
| `financiamiento` | Provincial / Nacional / Internacional y sus combinaciones; **«Sin dato»** donde la fuente pone `0` |
| `departamento` | canónico, los 23 de Salta |
| `municipio` | canónico, los 60 de Salta |
| `lat`, `lng` | coordenadas de la fuente |
| `coord_valida` | 0 si la coordenada cae fuera de Salta |
| `anio_fin_previsto` | año de `fecha_fin_inicial`, que es el fin **previsto** (ver 6) |
| `licitacion_anio` | vacío donde la fuente pone `0` |

Se dejan afuera `mano_obra`, `beneficiarios` y `destacada` (ver 6).

---

## 6. Los cinco defectos de la fuente, y qué se hizo con cada uno

### 6.1. El monto no se puede deflactar

`monto_contrato` son **pesos corrientes sin fecha de precio**. La fuente no informa cuándo se fijó
ese monto:

- `licitacion_anio` viene en **0 en el 82 %** de las filas (2.419 de 2.947);
- entre las 423 obras finalizadas que sí lo traen, la **brecha mediana entre la licitación y el fin
  previsto es de 4 años**, y llega a 14.

El repositorio tiene deflactor (`_ipc_anual()` / `_ipc_base()` en `adapters.py`, IPC NOA) y **no se
usa acá**: deflactar por el año de finalización sería aplicar un índice fijado cuatro años después
del precio, en un período en el que los precios se multiplicaron por decenas. Tampoco los montos
parecen redeterminados: la mediana por año de licitación crece de 5,5 millones en 2018 a 63,6 en
2025, muy por debajo de la inflación del período.

**Decisión:** el monto se publica tal cual y **no se compara entre años**. En el tablero aparece
como composición del padrón, con la unidad escrita («millones de pesos corrientes») y la
advertencia a la vista. La medida comparable del padrón es la **cantidad de obras**.

### 6.2. El año es el de finalización prevista, no la real

`fecha_fin_inicial` es, como dice su nombre, la fecha de fin **inicial**. Hay **72 obras con avance
100 % y fin previsto en 2026**. Se publica como `anio_fin_previsto`, y en el tablero el tema es un
**corte del padrón** —un solo año, el de la publicación— y no una serie anual. El perfil por año
de fin previsto está disponible como una apertura más, con esa salvedad escrita en el gráfico.

### 6.3. Tres coordenadas rotas

Tres registros traen la **longitud repetida de la latitud**, lo que los deja fuera de la provincia:

| id | municipio | lat | lng | obra |
|---|---|---|---|---|
| 255 | Rosario de la Frontera | −25,797897 | −25,797897 | Construcción de 4 aulas y núcleos sanitarios en E.E.T. N.º 31 |
| 852 | Rosario de la Frontera | −25,797897 | −25,797897 | Iluminación de destaque y ornamental en Hotel Termas Rosario |
| 853 | Rivadavia Banda Norte | −23,469256 | −23,469256 | Distribución de agua potable para Paraje 15 Viviendas |

**No se corrigen**: no hay forma de reconstruir la longitud real. Quedan con `coord_valida = 0`.
Las otras 2.944 caen dentro de la caja de la provincia.

### 6.4. Ausencia codificada como cero

| campo | filas en `0` | qué se hizo |
|---|---|---|
| `mano_obra` | 2.089 de 2.389 (87 %) | **no se publica como métrica** |
| `beneficiarios` | 2.038 de 2.389 (85 %) | **no se publica como métrica** |
| `licitacion_anio` | 2.419 de 2.947 (82 %) | se pasa a **vacío**, no a cero |
| `financiamiento` | 15 con el texto `"0"` | se pasa a **«Sin dato»** |

Un cero no es «cero puestos de trabajo»: es que no se cargó el dato. Publicarlos como métrica daría
promedios falsos.

### 6.5. Grafías inconsistentes y filas repetidas

El campo `comuna` mezcla acentuación: `El Galpon` junto a `Embarcación`, `Seclantas`, `Animana`,
`San Ramón De La Nueva Orán`. Se canonizan los 60 municipios contra la grafía que ya usa el
repositorio (ver 7).

Hay **6 pares de filas idénticas** en nombre + municipio + monto. **No se borran** —pueden ser dos
etapas cargadas con el mismo nombre, o una carga duplicada; la fuente no permite distinguirlo—, se
listan como incidencia:

- Construcción de playón deportivo en comunidad Coronillo (Tartagal, 39.838.504,78)
- Construcción de pavimento articulado en calle los Urundeles (General Mosconi, 83.814.735,16)
- Construcción de 3 viviendas de emergencia para comunidades aborígenes (Embarcación, 4.890.784,05)
- Construcción de Puentes Carreteros sobre Río San José y Río Candado (Los Toldos, 29.028.035,47)
- Construcción de 1 Vivienda en Barrio Parque La Vega (Salta, 910.694,00)
- Construcción de 50 viviendas de emergencia para comunidades aborígenes (Tartagal, 47.498.264,00)

---

## 7. Geografía

- **Departamentos**: los 23 de Salta. Los 23 nombres del padrón mapean sin excepción a la tabla
  canónica del repositorio (`_DEPT_CANON` en `adapters.py`). No hizo falta ningún alias nuevo.
- **Municipios**: los 60 de la provincia. 54 coinciden tal cual con la grafía de
  `Salta_recursos_municipios_mensual.csv`; los otros 6 se mapean así:

| en el padrón | canónico |
|---|---|
| Capital | Salta |
| Gral.Ballivian | General Ballivián |
| Joaquin V.Gonzalez | Joaquín V. González |
| Quebrachal | El Quebrachal |
| Salvador Mazza | Prof. Salvador Mazza |
| San Jose de Metan | Metán |

- **Cotejo municipio → departamento** contra el crosswalk del repositorio: **0 desvíos** en los 60
  municipios. La geografía del padrón es internamente consistente con el registro municipal.
- La ubicación es **la declarada por la fuente**: es la obra, no necesariamente el domicilio del
  beneficiario.

---

## 8. Formato numérico

Verificado según la práctica del repositorio: **cargar como texto, decidir la configuración por
columna, unificar a inglés, comprobar que todo parsea**.

| columna | configuración detectada | criterio |
|---|---|---|
| `monto_contrato` | **inglesa** | decimal `.` con dos dígitos (`89321182.56`), ninguna celda con `,` |
| `porcentaje_avance` | **inglesa** | `100.0`, `30.0`; rango 0–100 |
| `lat`, `lng` | **inglesa** | decimal `.` con seis dígitos |
| `licitacion_anio`, `fecha_fin_inicial` | enteros / ISO `AAAA-MM-DD` | sin separadores |

Cumplimiento sobre el CSV de salida:

| comprobación | resultado |
|---|---|
| valores numéricos que no parsean | **0** |
| celdas numéricas con coma | **0** |
| montos en cero o negativos | **0** |
| avances fuera de 0–100 | **0** |
| encoding | UTF-8 con BOM, **0 mojibake** |
| `id` duplicados | **0** |
| saltos de orden de magnitud en el monto (>1000× la mediana de su categoría) | **0** |

El archivo de origen también viene limpio: UTF-8 con BOM, sin mojibake, configuración inglesa en
todas sus columnas numéricas.

---

## 9. Valores de control

Los reproduce el script en cada corrida; si alguno falla, lo informa como incidencia.

| control | valor |
|---|---|
| Filas del padrón | 2.947 |
| Obras al 100 % | 2.389 |
| Obras que la fuente rotula `OTRAS` | 1.048 |
| Departamentos | 23 |
| Municipios | 60 |
| Obras al 100 % en General José de San Martín | 426 |
| Obras al 100 % en Capital | 381 |
| Coordenadas inválidas | 3 |
| Monto contratado de las finalizadas | 150.566.060.301,08 pesos corrientes |

**Resultado de la corrida del 21-nov-2026: 8 de 8 controles exactos.**

---

## 10. Incidencias

Nueve, todas de la fuente y ninguna corregida en silencio:

1. a 3. Las tres coordenadas con la longitud repetida de la latitud (ids 255, 852 y 853) — ver 6.3.
4. a 9. Los seis pares de filas idénticas en nombre + municipio + monto — ver 6.5.

No hubo valores sin parsear, ni separadores latinos remanentes, ni saltos de orden de magnitud, ni
desvíos en el cotejo geográfico.

---

## 11. Supuestos y limitaciones

- **La clasificación es propia y es una lectura de texto.** No hay revisión humana obra por obra ni
  segundo codificador. La columna `regla` deja cada asignación auditable, y `etiquetas` conserva
  las alternativas, pero una obra mal nombrada en el padrón queda mal clasificada acá.
- **El orden de las reglas es una decisión.** «Construcción de cordón cuneta y pavimento» se cuenta
  como cordón cuneta; con otro orden sería pavimento. Por eso se publica el orden completo
  (sección 4) y la columna `etiquetas`.
- **4,1 % de las obras finalizadas queda en «Otras obras»**, sin asignación individual.
- **30 % queda en «Sin especificar»** en el eje `accion`, porque el nombre no dice el verbo.
- **No se verificó la ubicación de cada obra** contra una capa oficial de límites: la caja de
  coordenadas es una comprobación de cordura, no una validación topológica. El repositorio no tiene
  shapefiles departamentales.
- **El padrón no es el universo del gasto en obra pública**: es lo que la Jefatura de Gabinete
  publica como padrón georreferenciado, y puede no incluir obras de otras reparticiones, de
  municipios o de empresas provinciales.
- **No se publica serie temporal.** El único año disponible es el de fin previsto, y el monto no es
  deflactable: las dos cosas juntas impiden medir evolución.
