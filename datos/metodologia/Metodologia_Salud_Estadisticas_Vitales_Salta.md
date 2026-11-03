# Metodología — Estadísticas vitales y de servicios de salud, Provincia de Salta

Datasets:
`Salud_Hechos_Vitales_Salta_provincia_2020-2025.csv`,
`Salud_Nacidos_Vivos_Salta_area_operativa_2021-2025.csv`,
`Salud_Servicios_Salta_provincia_2021-2025.csv`,
`Salud_Internacion_Salta_departamento_2025.csv`.

Fecha de elaboración: 2026-09-02.
Runbook y script: `Actualizar_Salud_Estadisticas_Vitales_Salta.md`.

> ### Estado de esta corrida (2026-09-02)
>
> Los CSV publicados **todavía no salieron de una corrida del script contra los archivos
> originales**: la descarga directa desde el Drive exige autenticación, así que los binarios aún no
> están en `fuentes/`. Se generaron alimentando las mismas funciones del script con las tablas del
> documento transcritas celda por celda, y **superando los mismos controles** que se describen en
> *Verificación* —incluida la coincidencia exacta de la suma de las 47 Áreas Operativas con el total
> provincial en los cinco años, que por sí sola audita las 235 celdas de la tabla territorial—.
>
> Para dejarlo cerrado: bajar los dos archivos a `datos-drive/fuentes/` y correr el script del
> runbook. Si algún número difiere, el script lo marca. Las dos únicas series sin identidad
> aritmética que las valide de forma independiente son `otras_defunciones` y la
> `tasa_mortalidad_hospitalaria` provincial.

---

## Fuente

**Programa de Estadísticas de Información en Salud**, Subsecretaría de Gestión de Salud, Ministerio
de Salud Pública de la Provincia de Salta. La información fue remitida al Consejo Económico y Social
por nota del 27 de julio de 2026, firmada por la Jefa del Programa de Estadísticas.

| Archivo de origen | Contenido | Cómo se lee |
|---|---|---|
| `INDICADORES  PROVINCIAL DE ESTADISTICAS DE SALUD  PARA CONSEJO ECONOMICO SOCIAL 2026.docx` (356.092 bytes) | 6 tablas: hechos vitales quinquenales, TMM, nacidos vivos por Área Operativa, estadísticas vitales 2020–2025, consultas médicas por habitante, producción y rendimiento de establecimientos, tasas vitales | `python-docx`, recorriendo `document.tables` |
| `Resumen provisorio de internación año 2.025.pdf` (349.583 bytes) | Rendimiento por establecimiento en internación, 53 hospitales + `TOTAL ZONA`, anual 2025 | `pdfplumber`, `extract_text()` + expresión regular por fila |

**Por qué estos archivos y no otros.** No existe una publicación abierta y descargable equivalente:
el Programa de Estadísticas no publica estas series en un portal de datos, y el tablero público del
Ministerio no permite exportar. Los documentos remitidos al CESS son la fuente primaria disponible.
El PDF `Resumen provisorio de consultas año 2.025.pdf`, de la misma carpeta, **no se procesa**: la
serie provincial de consultas 2021–2025 ya está en el `.docx` y no se requirió su apertura
territorial. Queda disponible para una ampliación futura y admite el mismo mapeo Área
Operativa → departamento que se construyó acá.

**El origen es texto tipeado, no un sistema.** Las tablas del `.docx` fueron cargadas a mano, y eso
explica la mayoría de las incidencias de más abajo. Por eso el script parsea los documentos
originales y **aborta** si alguna identidad aritmética no cierra, en lugar de publicar lo que
encuentre.

---

## Cobertura y unidad de análisis

| Dataset | Universo | Años | Filas | Clave única | Periodicidad |
|---|---|---|---|---|---|
| Hechos vitales | Provincia de Salta | 2020–2025 | 109 | `anio + desagregacion + metrica` ✔ sin duplicados | anual |
| Nacidos vivos por AO | 47 Áreas Operativas de residencia + total provincial | 2021–2025 | 240 | `anio + cod_ao + metrica` ✔ | anual |
| Servicios provinciales | Subsector público provincial | 2021–2025 | 50 | `anio + metrica` ✔ | anual |
| Internación por departamento | 53 establecimientos públicos con internación, agregados a 23 departamentos | 2025 | 253 | `anio + departamento + metrica` ✔ | anual |

**La unidad territorial de los nacimientos es el Área Operativa, no el departamento.** La columna
del `.docx` se titula "Departamento", pero sus 47 valores son Áreas Operativas: circunscripciones
sanitarias organizadas alrededor de un hospital cabecera (Colonia Santa Rosa, Campo Quijano,
Seclantás, Alto La Sierra, El Potrero…). Salta tiene 23 departamentos, no 47. Se conserva la
apertura original en la columna `area_operativa` y se agrega la columna `departamento` derivada.

Los códigos de Área Operativa de la fuente van del 1 al 53 pero **faltan el 20, el 40, el 41, el 42,
el 43 y el 47**: son 47 áreas efectivas. La numeración del `.docx` tampoco coincide con la del PDF de
internación, que usa códigos de establecimiento de cinco dígitos; los dos mapeos son independientes.

---

## Esquema de los CSV

Todos: separador `,`, decimal `.`, **sin** separador de miles, codificación `utf-8-sig`.
Última columna siempre `valor`; la anterior, `metrica`.

### `Salud_Hechos_Vitales_Salta_provincia_2020-2025.csv`

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | entero | 2020–2025 |
| `desagregacion` | texto | `Total` o la apertura de la métrica (ver abajo) |
| `metrica` | texto | clave snake_case |
| `valor` | float | |

| `metrica` | Desagregaciones | Unidad |
|---|---|---|
| `defunciones` | `Total`, `1 año y más`, `De 1 a 4 años`, `Menores de 1 año` | defunciones |
| `defunciones_infantiles` | `Total`, `Neonatal (< 28 días)`, `Posneonatal (28 días y más)` | defunciones |
| `defunciones_maternas`, `defunciones_fetales`, `otras_defunciones`, `matrimonios` | `Total` | casos |
| `nacidos_vivos` | `Total`, `Menos de 2.500 g`, `2.500 g y más`, `Peso sin especificar` | nacimientos |
| `tasa_natalidad`, `tasa_mortalidad_general` | `Total` | por mil habitantes |
| `tasa_mortalidad_infantil` | `Total` | por mil nacidos vivos |
| `tasa_mortalidad_materna` | `Total` | por diez mil nacidos vivos |

`otras_defunciones` se transcribe tal como aparece en la Tabla 1. **La fuente no define qué agrupa**
y no forma parte del total de defunciones (`Total = 1 año y más + Menores de 1 año + De 1 a 4 años`
cierra sin ella). Se publica sin interpretarla.

### `Salud_Nacidos_Vivos_Salta_area_operativa_2021-2025.csv`

`anio`, `cod_ao` (código de la fuente; `0` en la fila del total provincial), `area_operativa`
(nombre tal cual la fuente), `departamento` (**derivada**), `metrica` = `nacidos_vivos_res`, `valor`.

La fila con `departamento = "Salta"`, `area_operativa = "Total"` es el agregado provincial.

### `Salud_Servicios_Salta_provincia_2021-2025.csv`

`anio`, `metrica`, `valor`. Métricas: `consultas_medicas`, `poblacion`,
`consultas_por_habitante`, `camas_disponibles`, `pacientes_dia`, `ocupacion_camas`,
`permanencia_promedio`, `giro_camas`, `egresos`, `tasa_mortalidad_hospitalaria`.

### `Salud_Internacion_Salta_departamento_2025.csv`

`anio`, `departamento`, `metrica`, `valor`. Aditivas: `camas_disponibles`, `pacientes_dia`, `altas`,
`defunciones_hosp`, `egresos`, `pases`, `establecimientos`. Derivadas: `ocupacion_camas`,
`permanencia_promedio`, `giro_camas`, `tasa_mortalidad_hospitalaria`.

**No incluye fila provincial**: esa serie ya está en el CSV de servicios, y duplicarla haría que los
gráficos por departamento contaran dos veces el total.

### Columnas derivadas (las únicas que agrega el proceso)

| Columna | Cómo se construye |
|---|---|
| `departamento` (nacidos vivos) | tabla `AO_DEPTO` del script: 47 Áreas Operativas → 23 departamentos |
| `departamento` (internación) | tabla `EST_DEPTO` del script: 53 códigos de establecimiento → 23 departamentos |
| `tasa_mortalidad_materna` | `defunciones_maternas / nacidos_vivos × 10.000`; la fuente sólo la publica para 2024 y 2025, y la fórmula se validó contra esos dos valores |
| `tasa_mortalidad_infantil` de 2020 | `defunciones < 1 año / nacidos_vivos × 1.000`; la fuente no tabula tasas para 2020, y la fórmula se validó contra los cinco años que sí publica |
| `ocupacion_camas`, `permanencia_promedio`, `giro_camas`, `tasa_mortalidad_hospitalaria` por departamento | recalculadas sobre los totales sumados del departamento (ver *Transformaciones*) |

---

## Formato numérico detectado

Los dos documentos usan configuraciones distintas. **Todo se emite en configuración inglesa**, que es
el contrato de `sitio-indicadores/adapters.py`.

| Origen | Columna / celda | Configuración detectada | Criterio usado |
|---|---|---|---|
| `.docx` tabla de consultas | `2.672.823`, `1.441.988` | **latina** (miles `.`) | más de un `.` en el token |
| `.docx` tabla de consultas | `1,85`, `2,21` | **latina** (decimal `,`) | única `,`, sin `.` |
| `.docx` rendimiento | `2.778,72`, `52,40` | **latina** (miles `.`, decimal `,`) | conviven `.` y `,`, la `,` va última |
| `.docx` rendimiento | `110.749` | **latina** (miles `.`) | un `.` con exactamente 3 dígitos detrás |
| `.docx` tabla de tasas | `20.207`, `9.807` | **latina** (miles `.`) | ídem |
| `.docx` Tabla 1 | `8.7`, `9.1` (TMI) | **inglesa** (decimal `.`) | un `.` con 1 dígito detrás |
| `.docx` Tabla 1 y 2020–2025 | `9595`, `20207` | entero sin separadores | sin `.` ni `,` |
| `.pdf` internación | `2451.42`, `63.82` | **inglesa** (decimal `.`) | un `.` con 2 dígitos detrás |

El caso peligroso es el `.` solitario, que en `110.749` es separador de miles y en `8.7` es decimal.
La regla implementada (`parse_num`) resuelve por la cantidad de dígitos a la derecha: exactamente
tres ⇒ miles. **No se confía en la regla**: cada tabla se valida después contra una identidad
aritmética (ver *Verificación*), de modo que un separador mal interpretado rompe el script en vez de
pasar inadvertido. La función se prueba además contra 12 casos fijos de ambas configuraciones.

**Relectura de control.** Los cuatro CSV se releen con
`pd.read_csv(..., encoding="utf-8-sig")` y `pd.to_numeric(..., errors="coerce")` —exactamente las
opciones de `adapters.py`— y se exige cero `NaN`.

---

## Transformaciones aplicadas

1. **Selección entre tablas contradictorias.** El `.docx` publica las mismas series en tres tablas
   con valores distintos. Manda la **Tabla 1 (Resumen Quinquenal)** para defunciones, nacidos vivos,
   matrimonios y sus componentes 2021–2025. De la tabla "Estadísticas vitales 2020–2025" se toma
   sólo lo que la Tabla 1 no trae: el año **2020** completo, la apertura **neonatal/posneonatal** y
   la apertura **por peso al nacer**. Fundamento en *Verificación*.
2. **Reconstrucción de etiquetas partidas.** En la tabla 2020–2025 el nombre de cada fila está
   cortado en dos filas (`Defunciones` / `Generales`). Una fila con etiqueta y sin números se
   interpreta como continuación de la anterior.
3. **Alineación por orden, no por columna.** En la Tabla 1 la celda `HECHOS VITALES` está combinada
   y corre los años una columna respecto de las filas de datos. Los valores se emparejan con los años
   por orden de aparición, y se exige que la cantidad coincida.
4. **Área Operativa → departamento.** 47 → 23 por la tabla `AO_DEPTO`. Los casos no evidentes por el
   nombre: Colonia Santa Rosa, Pichanal, Hipólito Yrigoyen y Urundel → Orán; Aguaray, Salvador
   Mazza, Embarcación, Tartagal y General Mosconi → General José de San Martín; Morillo, Santa
   Victoria Este, Rivadavia Banda Sur, Alto La Sierra y La Unión → Rivadavia; Las Lajitas, J. V.
   González, El Quebrachal y Apolinario Saravia → Anta; El Galpón → Metán; El Tala → La Candelaria;
   El Potrero → Rosario de la Frontera; El Carril → Chicoana; Coronel Moldes → La Viña; Campo
   Quijano → Rosario de Lerma; La Merced → Cerrillos; Seclantás → Molinos; Angastaco → San Carlos;
   Nazareno y Santa Victoria Oeste → Santa Victoria; San Antonio de los Cobres → Los Andes.
5. **Establecimiento → departamento.** 53 → 23 por la tabla `EST_DEPTO`, con clave el código de
   cinco dígitos del PDF. Los siete establecimientos de Capital son San Bernardo, Señor del Milagro,
   Oñativia, Ragone, Papa Francisco y los dos Materno Infantil (pediátrico y adulto).
6. **Agregación de la internación: se suman los aditivos y se recalculan los cocientes.** Promediar
   ocupación, permanencia, giro o mortalidad entre establecimientos daría mal, porque son cocientes
   con denominadores de escalas muy distintas (San Bernardo tiene 364 camas promedio; La Poma, 2,9).
   Para cada departamento:

   ```
   ocupacion_camas              = Σ pacientes_dia / Σ camas_disponibles × 100
   permanencia_promedio         = Σ pacientes_dia × 365 / Σ egresos
   giro_camas                   = Σ egresos / Σ camas_disponibles
   tasa_mortalidad_hospitalaria = Σ defunciones / Σ egresos × 100
   ```

   Las cuatro fórmulas se verificaron primero contra las filas individuales del PDF y contra su
   propio `TOTAL ZONA` (ver *Verificación*).
7. **Nombres canónicos de departamento** vía `norm_dept()` de `adapters.py`, para que empalmen con
   los demás tableros del Monitor.
8. **Métricas separadas para nacidos vivos.** `nacidos_vivos` (provincial, con apertura por peso) y
   `nacidos_vivos_res` (por residencia) son claves distintas a propósito: comparten el concepto pero
   no la unidad de análisis, y unificarlas haría que un gráfico sin filtro sumara la serie
   provincial junto con sus propias aperturas.

---

## Verificación de totales

### Controles internos que cierran (y que fundan el criterio de selección)

| Control | Resultado |
|---|---|
| Tabla 1: `Total Defunciones = mayores + < 1 año + de 1 a 4 años` | ✔ los 5 años, diferencia 0 |
| `Def. < 1 año = neonatal + posneonatal` | ✔ los 6 años |
| Nacidos vivos = suma por peso al nacer | ✔ 2021–2024; falla en 2020 y 2025 (ver *Incidencias*) |
| TMI publicada = `def. < 1 año / nacidos vivos × 1.000` | ✔ los 5 años, a la centésima |
| TMM publicada = `def. maternas / nacidos vivos × 10.000` | ✔ 2024 (4,89) y 2025 (5,02) |
| Consultas por habitante = `consultas / población` | ✔ los 5 años |
| Ocupación y giro de camas provinciales | ✔ los 5 años |

### Control cruzado independiente 1 — apertura territorial contra total provincial

La suma de las 47 Áreas Operativas se compara contra dos totales publicados por separado (la fila
`Total Provincial` de esa misma tabla y la fila `Nacidos Vivos` de la Tabla 1):

| Año | Suma de las 47 AO | Total Provincial publicado | Tabla 1 | Diferencia |
|---|---|---|---|---|
| 2021 | 20.207 | 20.207 | 20.207 | 0 |
| 2022 | 18.587 | 18.587 | 18.587 | 0 |
| 2023 | 16.850 | 16.850 | 16.850 | 0 |
| 2024 | 14.316 | 14.316 | 14.316 | 0 |
| 2025 | 13.941 | 13.941 | 13.941 | 0 |

Coincidencia exacta en los cinco años. Éste es el control decisivo: descarta a la vez un error de
transcripción en cualquiera de las 235 celdas de la tabla territorial y confirma que el valor de
nacidos vivos 2025 correcto es 13.941, no el 13.491 de la tabla 2020–2025.

### Control cruzado independiente 2 — internación, PDF contra su propio total

Los 53 establecimientos se suman y se comparan con la fila `TOTAL ZONA`, calculada por el sistema de
la fuente (`RJi2025®`) de forma independiente:

| Concepto | Suma de los 53 establecimientos | `TOTAL ZONA` | Diferencia |
|---|---|---|---|
| Camas disponibles (promedio) | 2.451,40 | 2.451,42 | −0,02 |
| Pacientes-día (promedio) | 1.564,56 | 1.564,53 | +0,03 |
| Altas | 127.390 | 127.390 | 0 |
| Defunciones | 3.261 | 3.261 | 0 |
| Egresos | 130.651 | 130.651 | 0 |
| Pases internos | 34.010 | 34.010 | 0 |
| Ocupación de camas (recalculada) | 63,82 % | 63,82 % | 0 |
| Permanencia promedio (recalculada) | 4,37 días | 4,37 | 0 |
| Giro de camas (recalculado) | 53,30 | 53,30 | 0 |
| Tasa de mortalidad hospitalaria (recalculada) | 2,50 % | 2,50 | 0 |

Los enteros coinciden exactamente; las diferencias de centésimas en camas y pacientes-día son el
redondeo de promedios que el propio PDF publica ya redondeados. Además, `altas + defunciones =
egresos` se cumple en las **53 filas**, sin excepción.

---

## Incidencias

Ordenadas por gravedad. Las tres primeras son contradicciones entre tablas del mismo documento.

| # | Incidencia | Veredicto y decisión |
|---|---|---|
| 1 | **Nacidos vivos 2025**: la Tabla 1, la tabla de tasas y la suma de Áreas Operativas dicen **13.941**; la tabla "Estadísticas vitales 2020–2025" dice **13.491**. | Transposición de dígitos en la tabla 2020–2025. Tres fuentes independientes contra una. **Se publica 13.941.** |
| 2 | **Defunciones 2025**: Tabla 1 y tabla de tasas dicen **8.204**; la tabla 2020–2025 dice **8.126** (−78). | Sólo la Tabla 1 cierra contra sus componentes (8.041 + 134 + 29 = 8.204). **Se publica 8.204.** |
| 3 | **Defunciones 2024**: Tabla 1 y tabla de tasas dicen **8.734**; la tabla 2020–2025 dice **8.736** (+2). | Ídem: la Tabla 1 cierra contra sus componentes. **Se publica 8.734.** |
| 4 | **Defunciones 2021**: Tabla 1 y tabla 2020–2025 dicen **9.811**; la tabla de tasas dice **9.807** (−4). | Dos contra una. **Se publica 9.811.** |
| 5 | **Defunciones neonatales 2025**: 44 neonatales contra 90 posneonatales. En 2020–2024 lo neonatal fue el 61–75 % de la mortalidad infantil; en 2025 cae al 33 %. | La suma cierra (44 + 90 = 134), así que no es un error de carga del total. El patrón invertido sugiere un **intercambio de las dos filas** en la fuente, pero no hay forma de confirmarlo desde el documento. **Se publica tal cual y se advierte.** Conviene consultarlo al Programa de Estadísticas. |
| 6 | **Nacidos vivos por peso, 2025**: 1.180 + 12.762 + 28 = **13.970**, contra 13.941 del total válido (+29). | Inconsistencia dentro de la tabla 2020–2025, la misma que trae el 13.491 erróneo. **Se publican las tres categorías tal cual**; los gráficos de composición por peso pueden diferir en 29 casos del total. |
| 7 | **Nacidos vivos por peso, 2020**: 1.294 + 16.536 + 42 = **17.872**, contra 17.877 declarado (−5). | Sin explicación en el documento. **Se publica tal cual.** |
| 8 | **Tasa de mortalidad general 2021 y 2022**: no se reproducen con la población que el propio documento publica. 2021: 9.811 / 1.441.988 × 1.000 = **6,80**, publicada **6,89**. 2022: 9.242 / 1.440.672 × 1.000 = **6,42**, publicada **6,60**. De 2023 en adelante cierra exacto. | La fuente usó proyecciones de población anteriores a las INDEC 2022–2040, que aplica desde 2023. **Se publica la tasa tal como la emitió el MSP**, pero la serie no es estrictamente homogénea: el quiebre está entre 2022 y 2023. Lo mismo, en menor medida, en la tasa de natalidad 2022 (12,90 recalculada contra 12,86 publicada). |
| 9 | **Egresos 2025**: el `.docx` publica **130.649**; el PDF por establecimiento, **130.651** (+2). | Diferencia de redondeo o de corte entre dos salidas del mismo sistema. La serie provincial usa el `.docx`; el detalle departamental, el PDF. |
| 10 | **Ocupación de camas superior al 100 %** en tres establecimientos (Materno Infantil pediátrico 109,03 %; Seclantás 111,34 %) y **permanencia de 161,90 días** en el Hospital Ragone. | **No es un artefacto de parseo**: cada fila cumple `altas + defunciones = egresos` y los cuatro cocientes se reproducen desde sus propios componentes. Son camas supernumerarias y un servicio de estadía prolongada. Se publican; afectan el promedio de Capital. |
| 11 | `otras_defunciones` sin definición en la fuente. | No integra el total de defunciones. Se publica sin interpretar. |

No se detectaron valores no numéricos, duplicados de clave, negativos, mojibake ni saltos de orden
de magnitud espurios: el control automático `qc_saltos()` de `build.py` no marca nada en este tema.

---

## Supuestos y limitaciones

1. **El Área Operativa no es el departamento.** El pasaje de 47 AO a 23 departamentos es una
   aproximación: las circunscripciones sanitarias se organizan por accesibilidad al hospital
   cabecera y sus límites no coinciden exactamente con los departamentales. Un nacimiento cuya madre
   reside cerca de un límite puede estar contado en el AO de un departamento vecino. La apertura
   original se conserva en `area_operativa` para que la asignación sea auditable y reversible.
2. **La geografía es de residencia, no de ocurrencia.** Los nacidos vivos se asignan al AO donde
   reside la madre, no donde ocurrió el parto. Es el criterio correcto para leerlos como indicador
   poblacional, y no debe cruzarse con la internación, que es por establecimiento.
3. **La internación por departamento es de un solo año (2025).** No hay variación interanual por
   departamento, y por eso ese gráfico tiene el año fijo. La serie 2021–2025 de internación es
   provincial.
4. **La internación cubre sólo el subsector público provincial.** No incluye obras sociales,
   privados ni efectores nacionales, así que no mide la oferta total de camas de la provincia.
5. **2025 es provisorio** en toda la fuente, incluidos los dos PDF.
6. **Las tasas de 2021–2022 usan una población distinta de las de 2023–2025** (incidencia 8). Las
   comparaciones de punta a punta de la tasa de mortalidad general atraviesan ese quiebre.
7. **Los promedios departamentales de internación están dominados por sus hospitales grandes.** El
   86,66 % de ocupación de Capital es el resultado agregado de sus siete establecimientos, entre
   ellos San Bernardo, no la situación típica de un hospital del departamento.
8. **La cadena de origen es texto tipeado a mano.** Las once incidencias documentadas nacen de ahí.
   Los controles cruzados cubren prácticamente todas las celdas, pero `otras_defunciones` y
   `tasa_mortalidad_hospitalaria` provincial no tienen identidad aritmética que los valide de forma
   independiente.
