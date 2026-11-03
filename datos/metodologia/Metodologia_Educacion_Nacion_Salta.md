# Metodología — Educación (bases nacionales «agregada»), Provincia de Salta

Datasets: los 8 `Educacion_*_Salta_departamento_2021-2025.csv` de `datos-drive/`.
Script que los genera: `Actualizar_Educacion_Nacion_Salta.md`.
Fecha de elaboración: **2026-09-05**.

## Fuente

- **Organismo:** Subsecretaría de Información y Evaluación Educativa, Secretaría de Educación
  (Ministerio de Capital Humano de la Nación).
- **Portal:** <https://www.argentina.gob.ar/educacion/evaluacion-e-informacion-educativa/datos-abiertos-de-la-secretaria-de-educacion>
- **Bases usadas:** Relevamiento Anual «agregada» (Matrícula, Matrícula por edad, Trayectoria,
  Cargos, Cargos Bis, Características, Población) y **APRENDER censal agregada** (Desempeños de
  Lengua y de Matemática), años **2021 a 2025**.
- **Cómo se obtiene (importante):** la página **no publica enlaces**. Es un widget que lee un
  **Google Sheet** público (`1XaSz7AJ-EkpLqj_qjx3TPdBfJaQvqEZwg3sOYagtOsI`), y ese Sheet apunta a
  archivos alojados en el **OneDrive del Ministerio**. El script baja el catálogo del Sheet, extrae
  `user` + `token` de cada enlace y lo reescribe a la forma de descarga anónima
  `/_layouts/15/download.aspx?share=<token>`. **No se hardcodean URLs**: el catálogo es la autoridad.
- **Detección de token revocado:** un token dado de baja responde **HTTP 200** y redirige al login
  de Microsoft. El script aborta si la URL final contiene `login.microsoftonline` o si el
  `Content-Type` es HTML. Nunca se confía en el status code.
- **Por qué no datos.gob.ar:** el CKAN nacional publica otro producto («Base de Datos por Escuela»,
  bases *por escuela*), no estas bases «agregada». Se usó la fuente que el usuario indicó.
- **Licencia:** la página remite a CC BY 4.0. La restricción operativa es la **Ley 17.622** de
  secreto estadístico, que es la que produce el enmascaramiento (ver Incidencias).

## Cobertura y unidad de análisis

- **Cobertura:** 2021, 2022, 2023, 2024 y 2025 en las 7 bases del Relevamiento Anual.
- **Unidad de análisis de la fuente:** `provincia × departamento × sector × ámbito`
  (**Educación Común**). `Matrícula por edad` agrega `grado`; `Cargos Bis` viene ya en formato
  largo con `nivel × tipo × categoría × cargo × planta_tipo`.
- **Granularidad geográfica máxima: DEPARTAMENTO.** No existe `localidad` en ninguna de estas
  bases, ni códigos INDEC: el departamento viene únicamente como texto.
- Salta aporta **44 filas por base y por año** (23 departamentos reales + `Enmascarado`) ×
  combinaciones sector-ámbito; en `Cargos` y `Cargos Bis` aparece además `Sin datos`.
- **APRENDER** trae `jurisdiccion` (no `provincia`) pero **sí trae `departamento`**, con el mismo
  juego de etiquetas que el Relevamiento Anual, lo que permite cruzarlas.

| CSV | Filas | Dimensiones propias |
|---|---:|---|
| `..._Matricula_...` | 4.928 | `nivel` |
| `..._MatriculaEdad_...` | 24.180 | `nivel`, `edad` |
| `..._Trayectoria_...` | 12.320 | `nivel`, `sexo` |
| `..._Cargos_...` | 12.936 | `nivel`, `funcion`, `estado` |
| `..._CargosPlanta_...` | 23.955 | `nivel`, `tipo`, `categoria`, `planta_tipo` |
| `..._Establecimientos_...` | 13.596 | `grupo`, `detalle` |
| `..._PoblacionEscolar_...` | 28.644 | `nivel`, `grupo`, `detalle` |
| `..._APRENDER_...` | 1.656 | `nivel_evaluado`, `area`, `nivel_desempeno` |

## Esquema de los CSV

Todos: separador `,`; decimal `.`; **sin** separador de miles; codificación **UTF-8 con BOM**
(`utf-8-sig`), igual que el resto de los datasets del proyecto. Prefijo común
`anio, departamento, sector, ambito`, dimensiones propias, y cierre `metrica, valor`.

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | entero | Año del relevamiento. **La fuente no trae columna de año**: se inyecta desde el catálogo. |
| `departamento` | texto | Uno de los 23 de Salta, en Title Case con acentos, o `Enmascarado` / `Sin datos`. |
| `sector` | texto | `Estatal` / `Privado`. |
| `ambito` | texto | `Urbano` / `Rural`. |
| `nivel` | texto | `inicial`, `primaria`, `secundaria`, `snu`, `no_graduada` (y `multinivel` en secciones). |
| `metrica` | texto | Nombre de la medida (ver abajo). |
| `valor` | decimal | Valor en formato inglés. |

**Métricas por CSV.** Matrícula: `matricula`, `varones`, `repitentes`, `sobreedad`, `secciones`,
`secciones_multigrado`. Matrícula por edad: `matricula` (dimensión `edad` de 0 a 29 y `30 y más`).
Trayectoria: `matricula_inicial`, `entrados`, `salidos_con_pase`, `salidos_sin_pase`,
`matricula_final`, `promovidos`, `promovidos_examen`, `no_promovidos`, `regulares`, `otros`,
`egresados`. Cargos: `cargos`, `horas`. Cargos Bis: `cargos`. Características: `localizaciones`.
Población escolar: `alumnos` (+ `localizaciones` para el total). APRENDER: `alumnos_ponderados`.

### Corte grado → nivel (Salta, Ley 7546)

`primaria = grados 1 a 7`; `secundaria = 8 a 12 (+ 13/14)`; `inicial = lactantes, deambuladores,
salas de 2 a 5`; `snu`; y `no_graduada` (columna `_20`, organización no graduada). Es el mismo
corte que usa el dataset histórico del Monitor, y por eso las series empalman.

## Formato numérico detectado (skill `datasets`)

Las bases se cargan **como texto** y se convierten con un único parser (`parse_num`), que decide
por la **regla del último separador** y por el **agrupamiento de 3 dígitos**.

| Columna / origen | Configuración detectada | Criterio usado |
|---|---|---|
| Medidas del Relevamiento Anual | **latina** (decimal `,`; sin separador de miles) | Valores como `1,5` / `2023,5`; cero coincidencias del patrón de miles `\d+\.\d{3}` en el archivo |
| Medidas de APRENDER | **latina**, flotantes ya ponderados | Valores como `293,4372808` (decimal coma, muchos decimales) |
| `total` de Cargos Bis | **latina** (enteros) | Sin separadores; se valida que parsee |
| Salida de los 8 CSV | **inglesa** (decimal `.`) | Unificación obligatoria: contrato del proyecto |

- **Celdas vacías o suprimidas** vienen como **un espacio** (`" "`), no como cadena vacía; el
  parser las trata como faltantes y se emiten como `0` cuando la medida es un conteo aditivo.
- `Cargos Bis` usa el literal **`NULL`** en sus columnas de dimensión → se normaliza a
  `Sin especificar`.
- **Verificación de cumplimiento:** re-lectura de los 8 CSV con `utf-8-sig` + `pd.to_numeric`:
  **0 valores no numéricos** y **0 comas latinas remanentes** en la columna `valor`.

## Transformaciones aplicadas

1. Filtro provincial: `provincia` (o `jurisdiccion` en APRENDER) igual a *Salta*.
2. Inyección de `anio` desde el catálogo (la fuente no lo trae).
3. Normalización de departamentos a **Title Case con acentos** contra un diccionario de los 23
   canónicos (`General Güemes`, `General José de San Martín`, `La Viña`, `Metán`, `Orán`…), igual
   que el resto del Monitor. `Enmascarado` y `Sin datos` se conservan como tokens.
4. Agregación de columnas de grado a `nivel` según el corte de la Ley 7546.
5. Pasaje a formato largo (`metrica`, `valor`) y unificación numérica a formato inglés.
6. **Lectura de columnas insensible a mayúsculas** (ver Incidencia 1).
7. **Matrícula por edad:** se emiten sólo las **edades simples** (0 a 29) más `30 y más`. Se
   **descartan** las columnas agregadas de la fuente (`Menosde18años`, `6añosymás`, `18añosymás`,
   `25añosymás`, `11añosymenos`, `De20a24años`, `De25a29años`) porque **se solapan** con las
   simples y sumarlas duplicaría alumnos.
8. **Cargos:** `nopof` / `hs_fuera` se emiten como `funcion` y `estado` = `Fuera de planta`, de
   modo que sumar sobre `funcion × estado` da el total del nivel **sin doble conteo** (no se creó
   ninguna fila «Total»).
9. **No se calcularon tasas.** Se emiten numerador y denominador (p. ej. `repitentes` y
   `matricula`) y el cociente queda para el tablero: los porcentajes no son aditivos entre
   departamentos.

## Verificación de totales

### Controles internos que cierran
- **Cierre contra la fuente**, año por año: Σ `matricula` del CSV == Σ de las columnas de grado de
  la base de matrícula para Salta. Diferencia **0,00** en los 5 años
  (2021 = 418.940 · 2022 = 414.532 · 2023 = 416.752 · 2024 = 411.309 · 2025 = 405.607).
- `repitentes`, `sobreedad` y `varones` **nunca** superan `matricula`: 0 violaciones en 1.232 celdas.
- `promovidos` ≤ `matricula_final`: 0 violaciones en 572 celdas.
- `Mujeres` ≤ `Total` en trayectoria: 0 violaciones en 6.160 celdas.
- Departamentos: exactamente los 23 canónicos + `Enmascarado` (+ `Sin datos` en Cargos). Ningún
  nombre inesperado.

### Control cruzado independiente (el más fuerte)
Se comparó la **matrícula por departamento × nivel, 2021–2024**, contra el dataset histórico del
Monitor (`educacion_departamentos_salta_tidy.csv`), que se construyó desde **otra fuente** (las
bases *por escuela* de datos.gob.ar) y con otro código:

> **288 de 288 celdas coinciden exactamente** (total 1.466.473 alumnos en ambos; diferencia 0,000 %).

Dos pipelines independientes, dos productos distintos de la misma Secretaría, resultado idéntico.
Esto valida el filtro provincial, el corte grado→nivel y el parseo numérico.

### Reproducibilidad
Se extrajo el bloque `python` del runbook y se corrió en una carpeta limpia: los 8 CSV salieron
**md5 idénticos** a los entregados.

## Incidencias

| # | Incidencia | Veredicto y decisión |
|---|---|---|
| 1 | **2024 escribe `Departamento` y `Grado` con mayúscula inicial** (Población, Características, Matrícula por edad). | **Bug real detectado y corregido.** Con lectura exacta, todas las filas de 2024 caían en `Sin datos` y la base de matrícula por edad de 2024 se perdía completa. Se pasó a lectura de columnas **insensible a mayúsculas** (`gv()`). |
| 2 | **APRENDER 2021 trae `LA VIï¿½A`** en `departamento`: la fuente guardó un carácter de reemplazo (U+FFFD) donde iba la `Ñ` y lo volvió a codificar. | **Defecto de origen.** Se repara sustituyendo la secuencia por `N` y reintentando el match contra el diccionario canónico → `La Viña`. Queda registrado en cada corrida. |
| 3 | **`Enmascarado`**: la fuente funde en un departamento ficticio, por secreto estadístico (Ley 17.622), a los departamentos con **≤3 establecimientos** en una combinación sector-ámbito-nivel; si un solo departamento queda en el umbral, **también enmascara al siguiente más chico**. | **Dato real, no error.** Se **conserva**. Es imprescindible para que los totales provinciales cierren; los rankings departamentales del tablero deberían excluirlo pero los totales no. |
| 4 | **Deriva de esquema entre años**: 2025 agrega África y Oceanía a Población (131 → 147 columnas); Características pasa de 65 (2021-22) a 66 (2023-24) y 67 (2025) columnas. | **Esperado.** El mapeo es **por nombre de columna**, nunca por posición, y las columnas nuevas se incorporan solas. Cualquier columna sin grupo asignado se reporta como incidencia (hoy: ninguna). |
| 5 | **APRENDER 2022: la cantidad de alumnos ponderados difiere mucho entre áreas** (Salta: 14.949 en Lengua vs 8.855 en Matemática; a nivel nacional 440.348 vs 275.248). | **Característica de la fuente**, no de este proceso: cada instrumento trae su propio ponderador. **No comparar conteos absolutos entre áreas**; usar la distribución porcentual dentro de cada área. |
| 6 | **APRENDER rota el nivel evaluado**: primaria 6° en 2021, 2023 y 2025; secundaria 5°-6° en 2022 y 2024. No hay APRENDER 2020. | **Dato real.** Se emite `nivel_evaluado` como dimensión. Una serie anual continua **mezcla niveles**: hay que filtrar por `nivel_evaluado` (primaria 6° da 3 puntos: 2021, 2023, 2025). |
| 7 | **Valores de APRENDER ya ponderados** por la fuente (flotantes con muchos decimales). | **No se re-ponderan.** Se redondean a 2 decimales al emitir. |
| 8 | Saltos de orden de magnitud dentro de una serie. | **Sin incidencias.** No se detectaron picos que reviertan (la firma de un separador mal parseado); los rangos son coherentes con conteos de matrícula, cargos y localizaciones. |
| 9 | Mojibake, duplicados y rangos. | Los archivos decodifican en **UTF-8 estricto** (se decodifica sin `errors="replace"`, justamente para no enmascarar problemas). Único mojibake: el de la incidencia 2, que es de origen. |

## Supuestos y limitaciones

1. **No hay localidad.** El pedido original mencionaba «localidad o departamento»: la fuente sólo
   llega a **departamento**, así que ése es el nivel de todos los CSV. Bajar a localidad exigiría
   otra fuente (el sistema SICDIE, `data.educacion.gob.ar`, o un pedido a la Secretaría).
2. **No hay códigos INDEC** de provincia ni de departamento en estas bases; el empalme con otros
   datasets del Monitor se hace **por nombre normalizado**.
3. **Sólo Educación Común.** Las bases «agregada» excluyen las modalidades especiales; los totales
   no son comparables con el Anuario Estadístico completo.
4. **`Localizacion` sólo existe** en Características y Población (donde es denominador). Para
   tasas por establecimiento en las otras bases hay que ir al Anuario o a SICDIE.
5. **Los conteos son aditivos; los porcentajes no.** Los CSV no traen tasas calculadas a propósito.
6. **Las métricas de tasa o porcentaje que se deriven en el tablero deben declarar `agg: "mean"`**
   en el adapter. `EDU_METRICAS` hoy no declara `agg` y todo cae en `sum`: sumar porcentajes entre
   departamentos daría cualquier cosa.
7. **La fuente revisa archivos sin avisar** (los de APRENDER 2024 están anotados «datos
   actualizados a noviembre de 2025»). Conviene re-descargar y re-verificar antes de publicar.
8. **Durabilidad del hosting:** los archivos cuelgan del OneDrive personal de un agente del
   Ministerio; si esa cuenta se da de baja, todas las URLs se rompen a la vez. La caché en
   `datos-drive/fuentes/` es parte del entregable.
9. **2025 es el último año publicado** al momento de esta elaboración.
