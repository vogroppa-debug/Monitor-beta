# Metodología — Siniestralidad vial por jurisdicción (ANSV)

Dataset: `Siniestralidad_vial_ANSV_jurisdiccion_anual.csv`
Script: `actualizar_seguridad_vial_ansv.py`
Runbook: `Actualizar_Seguridad_Vial_ANSV.md`

---

## Resultado en una línea

Once métricas de siniestralidad vial para las 24 jurisdicciones argentinas, 2016–2026, extraídas de
los diez PDF del Observatorio Vial Nacional de la ANSV, más dos agregados calculados —`Total del
país`, que se toma publicado, y `NOA`, que se calcula—. **2.701 filas, 26 jurisdicciones, cero
discrepancias en 349 celdas leídas en más de un documento.**

---

## 1. Fuente

Agencia Nacional de Seguridad Vial (ANSV), Dirección Nacional de Observatorio Vial, Dirección de
Estadística Vial. Dos colecciones distintas:

- **Anuarios estadísticos de siniestralidad vial**, 2016 a 2022, con datos definitivos:
  <https://www.argentina.gob.ar/seguridadvial/observatoriovialnacional/anuarios>
- **Informes de siniestralidad vial fatal**, 2023 a 2026, **parciales y preliminares**:
  <https://www.argentina.gob.ar/seguridadvial/observatoriovialnacional/ano-2026>

La ANSV no es la que mide: consolida lo que le reporta cada jurisdicción. En Salta el organismo que
reporta es la **Subsecretaría de Seguridad Vial** (Secretaría de Seguridad, Ministerio de Seguridad
y Justicia). Eso explica buena parte de los huecos y de los cambios de cobertura documentados más
abajo: cuando una provincia cambia de sistema de registro, su serie salta.

### Todo es PDF

**No hay CSV, ni XLSX, ni datos abiertos.** No existe ficha en datos.gob.ar y las páginas del
Observatorio sólo ofrecen PDF. Se verificó en noviembre de 2026 sobre las tres secciones del
Observatorio y con una búsqueda específica de datos abiertos.

Son, eso sí, PDF de **texto nativo**, no escaneos: las tablas se leen con `pdfplumber` sin OCR. Los
diez documentos se guardan en `fuentes/ansv_seguridad_vial/` con caché permanente, porque son la
única prueba de dónde salió cada celda.

### Los diez documentos y qué aporta cada uno

| clave | documento | pág. | aporta |
|---|---|---|---|
| `a2017` | Anuario 2017 | 37 | población, parque, VF y tasas 2017; tipo de usuario; heridos; siniestros según gravedad |
| `a2018` | Anuario 2018 | 50 | **VF y ambas tasas 2016, 2017 y 2018**; tipo de usuario; heridos; siniestros según gravedad |
| `a2019` | Anuario 2019 | 143 | VF 2008-2019 (se usa desde 2016); población, parque y tasas 2019; tipo de usuario; siniestros con víctimas; heridos |
| `a2020` | Anuario 2020 | 46 | población, parque, SF, VF, ambas tasas, tipo de usuario, siniestros con víctimas y con lesionados, heridos |
| `a2021` | Anuario 2021 | 34 | población, SF, VF, tasas, tipo de usuario, heridos |
| `a2022` | Anuario 2022 | 113 | **SF y VF 2017-2022**; población, parque, tasas, tipo de usuario, siniestros con víctimas y con lesionados, heridos |
| `p2023` | Informe preliminar 2023 | 27 | SF y VF por jurisdicción, con tasas cada 100 mil habitantes y cada 10 mil vehículos |
| `p2024` | Informe preliminar 2024 | 21 | ídem, pero **ya sin la tasa cada 10 mil vehículos** |
| `p2025` | Informe preliminar 2025 | 13 | **sólo VF y tasa de mortalidad**: no abre siniestros fatales por jurisdicción |
| `p2026` | Parcial enero–septiembre 2026 | 20 | SF y VF por jurisdicción. **Sin CABA** |

Los informes preliminares son cada vez más pobres: 27 páginas en 2023, 21 en 2024, 13 en 2025. Eso
no es una elección de este dataset, es lo que hay.

---

## 2. Cobertura y unidad de análisis

Unidad: **jurisdicción × año × métrica**, y en víctimas fatales también × tipo de usuario de la vía.

La cobertura es desigual y es el dato más importante de este documento. `✔` = las 24 jurisdicciones;
un número = cuántas de las 24; `·` = la ANSV no lo publica por jurisdicción ese año.

| métrica | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `victimas_fatales` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | 23 |
| `siniestros_fatales` | · | ✔ | 23 | 23 | ✔ | ✔ | ✔ | ✔ | ✔ | · | 23 |
| `siniestros_con_victimas` | · | · | · | 23 | ✔ | · | ✔ | · | · | · | · |
| `siniestros_con_lesionados` | · | ✔ | 21 | · | ✔ | · | 22 | · | · | · | · |
| `personas_heridas` | · | ✔ | 21 | 22 | ✔ | ✔ | ✔ | · | · | · | · |
| `tasa_mortalidad_100mil` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | · |
| `tasa_fatalidad_10mil_veh` | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | · | · | · |
| `tasa_siniestralidad_fatal_100mil` | · | · | · | · | ✔ | ✔ | ✔ | ✔ | ✔ | · | · |
| `tasa_siniestralidad_fatal_10mil_veh` | · | · | · | · | ✔ | ✔ | ✔ | ✔ | · | · | · |
| `poblacion` | · | ✔ | · | ✔ | ✔ | ✔ | ✔ | · | · | · | · |
| `parque_vehicular` | · | ✔ | · | ✔ | ✔ | · | ✔ | · | · | · | · |
| `victimas_fatales` por tipo de usuario | · | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | · | · | · | · |

Las tres lecturas que salen de ahí:

1. **La única serie sin huecos es `victimas_fatales` con su tasa de mortalidad, 2016–2025.** Es la
   que puede sostener un gráfico de tendencia.
2. **`siniestros_fatales` tiene un hueco en 2025**: el informe preliminar de ese año publica el
   total del país (3.255) pero no lo abre por jurisdicción.
3. **El tipo de usuario por jurisdicción se corta en 2022.** Los informes 2023–2026 lo publican por
   *región* y en porcentaje, nunca por provincia.

### Faltantes nominados

No son errores de lectura: la fuente los marca con un signo convencional de dato no registrado.

| métrica | año | jurisdicciones ausentes |
|---|---|---|
| `siniestros_fatales` | 2018 | La Rioja |
| `siniestros_fatales` | 2019 | Mendoza |
| `siniestros_fatales` / `victimas_fatales` | 2026 | CABA (el informe dice «no disponible») |
| `siniestros_con_lesionados` / `personas_heridas` | 2018 | Córdoba, La Rioja, Mendoza |
| `personas_heridas` | 2019 | Córdoba, Mendoza |
| `siniestros_con_victimas` | 2019 | Mendoza |
| `siniestros_con_lesionados` | 2022 | Mendoza, Santa Fe (las dos «trabajando en el cierre de sus datos») |

### Lo que la fuente trae y no se emite

- **Serie 2008–2015.** Existe (anuario 2019, tabla 36), pero está marcada provisoria o parcial en
  seis jurisdicciones. Buenos Aires pasa de 689 víctimas fatales en 2014 a 1.540 en 2016: es
  cobertura, no siniestralidad. Publicarla invitaría a leer una caída que no ocurrió.
- **Datos mensuales.** Los informes 2023, 2024 y 2026 y los anuarios 2020 y 2021 abren por mes,
  pero 2019, 2022 y 2025 no. Una serie mensual con dos huecos en el medio engaña más de lo que
  informa.
- **Tasas derivables.** Morbilidad y siniestralidad con lesionados salen de dividir dos columnas que
  ya están en el CSV. Además la del anuario 2020 está mal publicada (ver incidencias).
- **Aperturas de un solo año**: género, rango etario, tipo de vía, franja horaria, zona. Son
  cortes transversales que no forman serie.

---

## 3. Esquema del CSV

```
anio,jurisdiccion,tipo_usuario,metrica,valor,calidad,fuente_doc
```

| columna | contenido |
|---|---|
| `anio` | 2016 a 2026 |
| `jurisdiccion` | las 24, más `Total del país` y `NOA` |
| `tipo_usuario` | `Total` en todas las métricas agregadas; las seis categorías sólo en `victimas_fatales` 2017–2022 |
| `metrica` | las once de la matriz de cobertura |
| `valor` | formato inglés: decimal `.`, sin separador de miles |
| `calidad` | `definitivo` · `preliminar` · `parcial` · `derivado` |
| `fuente_doc` | documento y página de donde salió la celda, p. ej. `a2022 p43; a2020 p29` |

`tipo_usuario` es un **margen**: la fila `Total` no es una categoría más, es la suma de las otras
seis. Un gráfico que no fije esta dimensión suma el margen con sus partes y duplica el total. Es el
mismo esquema que `envase` en el dataset de cemento.

`calidad` por filas: 2.183 `definitivo`, 373 `preliminar`, 48 `parcial`, 97 `derivado`.

### Qué cuenta cada métrica

- **Víctima fatal**: persona que fallece en el lugar del hecho **o hasta 30 días después**. Es el
  criterio de armonización internacional, y es la razón por la que los datos de un año tardan en
  cerrar.
- **Siniestro fatal**: el hecho, no la persona. Siempre hay más víctimas fatales que siniestros
  fatales (en Salta 2023, 173 víctimas en 154 siniestros).
- **Tasa de mortalidad**: víctimas fatales cada 100.000 habitantes.
- **Tasa de fatalidad**: víctimas fatales cada **10.000 vehículos** registrados. La ANSV publica
  esta base, no «cada 1.000»; se respeta la de la fuente para que el número sea reproducible contra
  el PDF.
- **Tasa de siniestralidad fatal**: lo mismo, pero con siniestros en el numerador.

### Taxonomía de tipo de usuario

La ANSV la cambia en 2019. Hasta 2018 son seis categorías; desde 2019 son nueve, porque abre
camioneta/utilitario, transporte de carga y transporte de pasajeros. Se mapean a **una taxonomía
común de seis**, que preserva exactamente moto y bicicleta:

| categoría del dataset | anuarios 2017–2018 | anuarios 2019–2022 |
|---|---|---|
| `Motociclista` | Motocicleta | Moto |
| `Automóvil` | Automóvil | Automóvil |
| `Peatón` | Peatón | Peatón |
| `Ciclista` | Bicicleta | Ciclista |
| `Otros vehículos` | Otro | Camioneta + T. carga + T. pasajeros + Otro |
| `Sin dato` | Sin especificar | Sin dato |

Salta, víctimas fatales por tipo de usuario:

| año | Motociclista | Automóvil | Peatón | Ciclista | Otros vehículos | Sin dato | TOTAL |
|---|---|---|---|---|---|---|---|
| 2017 | 94 | 53 | 27 | 7 | 22 | 0 | **203** |
| 2018 | 97 | 38 | 33 | 11 | 40 | 0 | **219** |
| 2019 | 95 | 27 | 19 | 6 | 18 | 0 | **165** |
| 2020 | 79 | 19 | 16 | 7 | 16 | 0 | **137** |
| 2021 | 103 | 32 | 17 | 9 | 26 | 0 | **187** |
| 2022 | 63 | 36 | 19 | 13 | 20 | 0 | **151** |

---

## 4. Formato numérico detectado

Los PDF vienen en **configuración latina**: miles con punto, decimales con coma (`1.459`, `15,7`).
El dataset sale en **configuración inglesa**.

| columna | configuración en la fuente | criterio |
|---|---|---|
| conteos (`victimas_fatales`, `siniestros_*`, `personas_heridas`) | latina, sólo miles | punto siempre seguido de exactamente 3 dígitos y en posiciones de agrupamiento (`1.459`, `44.044.811`); ningún valor con decimales |
| tasas (`tasa_*`) | latina, sólo decimal | coma seguida de **un** dígito (`15,7`, `2,1`), nunca de tres |
| `poblacion`, `parque_vehicular` | latina, sólo miles | igual que los conteos (`17.020.012`) |
| columnas de variación porcentual | latina con signo (`-25,4%`) | se leen para contar columnas y **no se emiten** |

Verificación posterior sobre el CSV: **0 valores con coma remanente**, **0 valores que no parsean**,
**0 celdas vacías**, 632 valores con punto decimal, todos con **un solo decimal** (ninguno con tres,
que sería la firma de un separador de miles mal leído).

### Signos convencionales

Los anuarios declaran su tabla de signos (es la del Manual de Estilo del INDEC) y el script la
respeta literalmente:

| signo | significado | tratamiento | veces |
|---|---|---|---|
| `-` | **cero absoluto** | **0** | 395 |
| `.` | dato no registrado | faltante | 31 |
| `ND` | no disponible | faltante | 20 |
| `…` | no disponible a la fecha | faltante | 14 |
| `...` | ídem | faltante | 9 |
| `///` | dato que no corresponde presentar | faltante | 4 |
| `S/D` | sin dato | faltante | 1 |
| `*` | dato provisorio | se descarta el sufijo, se conserva el valor | — |

**El guion es cero y no faltante.** Confundirlos ya costó un error en la serie de cemento: en el
dataset de despachos, un `-` leído como ausente borró un mes entero de La Rioja.

---

## 5. Transformaciones aplicadas

1. **Localización de la tabla por título, nunca por número.** La numeración cambia todos los años
   (la de tipo de usuario es la 8 en 2017, la 10 en 2018, la 49 en 2019, la 19 en 2020 y 2021, la
   15 en 2022). Entre todas las páginas que mencionan el título se elige **la que más filas de
   jurisdicción tiene**, que es lo que saltea el índice: el anuario 2018 repite los 25 títulos en
   una sola página.
2. **Parseo por etiqueta.** Una fila se lee sólo si abre con un nombre de jurisdicción conocido y
   trae exactamente las columnas declaradas. Se normalizan las abreviaturas (`S. del Estero`,
   `T. del Fuego`, `Sgo. del Estero`, `TOTAL PAIS` sin acento) y las marcas de nota al pie pegadas
   al nombre (`CABA1`, `Córdoba*`, `Río Negro(2)`, `Total (2)`).
3. **`Capital Federal` → `CABA`.** La ANSV ya usa CABA, pero el diccionario contempla la
   denominación vieja por si reaparece: en este proyecto no se usa.
4. **Mapeo de la taxonomía de tipo de usuario** a las seis categorías comunes, sumando las tres
   columnas que van a `Otros vehículos`.
5. **Conversión a formato inglés** y a entero cuando el valor lo es.
6. **El preliminar 2025 se parsea por posición de palabra**, no por líneas. Su página de
   jurisdicciones no es una tabla: son dos gráficos de barras lado a lado, con la etiqueta de cada
   barra ubicada donde termina la barra, de modo que la posición horizontal del número no dice nada.
   Los renglones se reconstruyen agrupando por coordenada vertical **con corte por hueco** (dentro
   de un renglón las palabras se desplazan hasta 6 puntos; entre renglones nunca hay menos de 10), y
   dentro de cada renglón se recorre de izquierda a derecha. El total del país no cuelga de ninguna
   barra: se identifica como el número que está debajo del rótulo «Total».

### Agregados calculados

- **`Total del país` se toma de la fila publicada, nunca se suma.** La suma sólo se usa para
  verificar.
- **`NOA` se calcula.** Son las seis provincias que agrupa la propia ANSV: **Catamarca, Jujuy, La
  Rioja, Salta, Santiago del Estero y Tucumán**. No es una elección de este dataset: se verificó
  aritméticamente contra las tablas de víctimas fatales por región que publica la ANSV (anuario
  2019, serie 2008-2019; anuario 2022, serie 2017-2022).
  - En **absolutos**, suma de las seis.
  - En **tasas**, cociente de agregados: `suma(víctimas fatales) / suma(población) × 100.000`.
    **Nunca el promedio de las seis tasas provinciales**, que daría un número sin denominador. Es el
    mismo criterio que usa el Monitor para el NOA en el tema de gobierno.
  - **Los denominadores del NOA se despejan, no se toman de la tabla publicada.** Para cada
    provincia y año, la población sale de invertir el par (víctimas fatales, tasa de mortalidad)
    que la ANSV publica, y el parque vehicular de invertir el par (víctimas fatales, tasa de
    fatalidad). Es deliberado: el denominador que hay que sumar es **el que está implícito en las
    tasas provinciales contra las que el NOA se compara en el mismo gráfico**. Usar la tabla
    publicada haría al NOA incomparable con Salta, porque la ANSV no siempre calcula sus tasas con
    la misma edición del denominador que tabula (ver incidencias, parque vehicular 2020). Todas
    esas celdas van marcadas `calidad=derivado`.

---

## 6. Verificación

### Control de relectura (el más fuerte)

Las mismas celdas aparecen en documentos distintos: el anuario 2022 trae la serie 2017–2022 de
siniestros y víctimas fatales, que repite lo que ya publicó el anuario de cada año; el anuario 2019
trae la serie 2008–2019; el anuario 2018 trae 2016–2018.

> **349 celdas leídas en más de un documento. 0 discrepancias.**

Es el control que descarta un error de lectura de columnas: si el script se corriera una columna,
las dos lecturas no coincidirían.

### Cierre de fila

En las trece tablas con apertura —tipo de usuario, heridos según gravedad y siniestros según
gravedad— la suma de las categorías tiene que dar la columna TOTAL, para las 24 jurisdicciones.

**Es el control que fija el orden de las columnas**, y no es decorativo: el anuario 2019 pone
«Heridos totales» en la **primera** columna mientras 2017, 2018 y 2020 lo ponen en la última, y sin
este control el dataset habría publicado la columna «Sin dato» como si fueran los heridos de 2019
(cero para Salta, entre 5.266 en 2018 y 3.652 en 2020).

Cierran todas. Cuatro filas difieren en ±1 (CABA 2017 y 2018, San Luis 2017, Buenos Aires 2019): es
el redondeo que la propia ANSV declara por los factores de ajuste. Dos filas no abren el total
(Buenos Aires y CABA en los heridos de 2017) y se cuentan aparte. Cualquier otro desvío se reporta
como incidencia y no se corrige.

### Suma de jurisdicciones contra el total publicado

Desvío máximo **10** sobre 6 casos, en series de miles. Mismo origen: factores de ajuste y redondeo.

### Denominador despejado contra denominador publicado

Es la verificación que dice si despejar introduce ruido, y de paso detecta cuándo la ANSV calculó
sus tasas con una edición del denominador distinta de la que tabula.

| denominador | pares | peor jurisdicción | agregado del NOA |
|---|---|---|---|
| `poblacion` | 125 | 1,76 % | **0,15 %** (5 años) |
| `parque_vehicular` | 100 | 9,91 % | **3,00 %** (4 años) |

Al sumar las seis provincias los redondeos se compensan: el error por jurisdicción es el efecto de
la tasa redondeada a un decimal en provincias con pocas víctimas fatales, y se diluye en el
agregado. La población cierra en 0,15 %, que es ruido de redondeo y nada más.

El parque vehicular **no**: su 3 % viene de un solo año. El script marca como incidencia cualquier
año en que los dos denominadores se separen más de 2 % sobre el agregado del NOA, y hoy salta uno
—2020— que está explicado abajo. En 2017, 2019 y 2022 los dos coinciden dentro del 2 %.

### Coherencia interna

Donde están las tres cosas (víctimas fatales, población y tasa publicadas), la tasa se reproduce:
135 pares, desvío máximo **0,115** sobre tasas de entre 2,4 y 31,6. El peor caso es San Luis 2019,
donde la ANSV publica la población redondeada a 502.000.

### Valores de control

Verificados celda por celda contra el PDF: **28 de 28 correctos.**

| año | Salta | valor |
|---|---|---|
| 2016 | víctimas fatales · tasa mortalidad · tasa fatalidad | 212 · 15,7 · 4,6 |
| 2018 | víctimas fatales · motociclistas · ciclistas | 219 · 97 · 11 |
| 2019 | víctimas fatales · motociclistas · ciclistas | 165 · 95 · 6 |
| 2022 | víctimas fatales · siniestros fatales · motociclistas · ciclistas | 151 · 136 · 63 · 13 |
| 2022 | tasa siniestralidad fatal c/100 mil hab · c/10 mil veh | 9,3 · 2,1 |
| 2023 | siniestros fatales · víctimas fatales · tasa mortalidad · tasa fatalidad | 154 · 173 · 11,7 · 2,5 |
| 2025 | víctimas fatales · tasa mortalidad | 130 · 8,7 |
| 2026 ene-sep | siniestros fatales · víctimas fatales | 89 · 93 |

Total del país: 4.711 víctimas fatales y 3.966 siniestros fatales en 2022; 4.060 víctimas fatales en
2025. NOA: 935 víctimas fatales en 2019 y 887 en 2022, coincidentes con la tabla por región que
publica la ANSV.

### Otras comprobaciones

Sin duplicados de clave. Sin valores negativos. Sin mojibake. UTF-8 con BOM y CRLF, como el resto de
los CSV del repositorio.

---

## 7. Incidencias

### De la fuente, no del proceso

Tres saltos de orden de magnitud entre años consecutivos. **Los tres son reales**: cambios de
cobertura del organismo que reporta, no errores de parseo. Se señalan y no se corrigen.

| serie | salto | qué pasó |
|---|---|---|
| Córdoba, `siniestros_con_victimas` | 2019 = 329 → 2020 = 5.579 | en 2019 Córdoba reportó únicamente los siniestros fatales: 329 es exactamente su cifra de siniestros fatales de ese año |
| Mendoza, `personas_heridas` | 2021 = 110 → 2022 = 1.419 | subregistro en 2021 |
| Santa Cruz, `personas_heridas` | 2017 = 44 → 2018 = 496 | subregistro en 2017 |

**El parque vehicular que publica el anuario 2020 no reproduce las tasas de ese mismo anuario.**
Para Salta la tabla dice 628.999 vehículos, pero las 137 víctimas fatales y la tasa de 2,3 cada 10
mil vehículos implican 595.652: un 5 % menos. Lo mismo a nivel país (−5,0 %). En 2017, 2019 y 2022
las dos cifras coinciden. Es una inconsistencia de la fuente, y la razón por la que el NOA usa el
denominador despejado y no el tabulado.

**Buenos Aires y CABA no abren sus heridos de 2017.** La tabla trae el total (41.029 y 11.404) y
escribe el guion de «cero absoluto» en leves y graves, donde correspondía el punto de «dato no
registrado». El total es bueno, que es lo único que se emite; pero arrastra la fila del total del
país, cuya suma de leves y graves (66.117) se aparta del total publicado (118.550) exactamente en
los 52.433 heridos de esas dos jurisdicciones. Queda como incidencia reportada.

Otras dos de la fuente, que no afectan al dataset porque no se emiten esas columnas:

- **El anuario 2020 publica la tasa de siniestralidad con lesionados corrida un factor 10.** Para
  Salta dice 19,9 cada 100 mil habitantes cuando 2.834 siniestros sobre 1.424.397 habitantes dan
  199,0. La tabla de morbilidad del mismo anuario está bien. Por eso este dataset no emite esa tasa:
  el cociente se arma con las dos columnas que sí están.
- **El parque vehicular del anuario 2021 es el de 2020**: la propia tabla lo titula «Año 2020». No
  se emite dos veces.

### Del proceso

Ninguna. La corrida termina con las tres incidencias de arriba y nada más.

---

## 8. Supuestos y limitaciones

1. **Los datos 2023–2026 son preliminares y van a cambiar.** La ANSV trabaja sobre un «dataset
   vivo» hasta que cada jurisdicción confirma el cierre. El informe 2025 está actualizado a abril de
   2026 y el parcial 2026 al 5 de noviembre de 2026.
2. **Las víctimas fatales de Buenos Aires y Mendoza llevan un factor de ajuste de 1,3** aplicado por
   la ANSV sobre las víctimas fatales en el lugar, porque esas jurisdicciones no reportan el
   seguimiento a 30 días. Es un número estimado, no observado, y arrastra al total del país.
3. **Esto no es lo mismo que la mortalidad por lesiones de tránsito de la DEIS**, que el Monitor
   publica en el tema `seguridad`. La DEIS cuenta por causa de muerte en el certificado de
   defunción; la ANSV, por siniestro reportado por la jurisdicción. Van a dar números distintos para
   lo que un lector lee como lo mismo.
4. **La tasa por vehículos usa la base de la ANSV: cada 10.000 vehículos registrados.** Dividir por
   diez para expresarla cada 1.000 pierde precisión, porque la fuente ya redondea a un decimal.
5. **La población es la proyección del INDEC que usa la ANSV en cada edición**, y las ediciones no
   usan la misma vintage. Por eso una misma tasa puede diferir en una décima entre dos documentos.
   El dataset conserva la del documento, no recalcula.
6. **El NOA es un cálculo de este proceso**, salvo en víctimas fatales, donde coincide con la cifra
   que la ANSV publica por región. Sus denominadores están siempre despejados de las tasas
   provinciales publicadas, por la razón explicada en la sección 5; sus tasas llegan hasta donde
   llega la tasa provincial de la que se despejan (2025 para mortalidad, 2023 para la de
   vehículos).
7. **2026 es enero–septiembre y le falta CABA.** Está en el CSV marcado `calidad=parcial`, y el
   tablero del Monitor lo excluye de los gráficos.
8. **No se verificaron las aperturas que no se emiten** (género, edad, tipo de vía, horario, zona).
