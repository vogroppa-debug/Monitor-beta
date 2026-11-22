# Metodología — Producción de azúcar y alcohol por ingenio (Centro Azucarero Argentino)

Dataset: `Produccion_sucroalcoholera_CAA_ingenio_anual.csv`
Script: `actualizar_azucar_alcohol_caa.py`
Fecha de obtención: 21 de noviembre de 2026.

## Resultado en una línea

5.658 filas, 36 zafras (1990–2025), 23 ingenios de cuatro provincias más los agregados de
provincia, NOA y país. Los nueve valores de control dan exactos, el total del país cierra contra
NOA + Litoral en las 200 celdas, y el cierre de cada hoja contra su fila TOTAL publicada falla en
una sola celda de las 79 hojas leídas. **La fuente tiene dos defectos localizados, los dos
documentados abajo y ninguno corregido en silencio**: los dos ingenios de Salta están
intercambiados entre 1990 y 2002, y el azúcar de Ledesma en 2024 es imposible en el libro
histórico.

---

## 1. Fuente

El Centro Azucarero Argentino publica, en el menú *Estadísticas* de centroazucarero.com.ar, cuatro
planillas XLSX con **una hoja por año** y **una fila por ingenio**. Las cuatro se usan.

| libro | hojas | columnas que aporta |
|---|---|---|
| `Produccion-de-Azucar-desde-2016.xlsx` | 2016–2025 | crudo, blanco, refinado, orgánico, total, **caña molida bruta**, rendimiento % |
| `produccion-de-azucar-desde-1990.xlsx` | 1990–2024 | blanco, crudo, total, caña molida, total en TMCV |
| `Produccion-de-alcoholes-desde-2016.xlsx` | 2016–2025 | anhidradora, alcohol producido m³ |
| `produccion-de-alcohol-desde-1990-ok.xlsx` | 1990–2023 | anhidradora, alcohol producido m³ |

Hay una quinta planilla, `consumos-de-nafta-desde-2007.xlsx`, que no se usa: es consumo nacional de
naftas, no producción.

**Las URL cambian solas.** El nombre de archivo cuelga de la carpeta de subida de WordPress
(`/wp-content/uploads/2026/07/`), así que cuando el CAA publique la zafra siguiente la dirección va
a ser otra. Por eso el script no las hardcodea: raspa los enlaces `.xlsx` de las cuatro páginas de
estadísticas, los clasifica por nombre (producto × época) y, si una ranura tiene varios candidatos,
se queda con el que trae más años con datos. En la corrida del 21-nov-2026 la ranura
*alcohol/histórico* tenía dos candidatos y uno de ellos,
`produccion-de-alcohol-desde-1990.xlsx`, **devuelve 404**: es un enlace roto de la página del CAA.

### 1.1 Qué es cada cosa

- **Caña molida**: caña entrada a fábrica en la zafra. Desde 2016 la fuente la rotula **bruta**
  (ver §4).
- **Azúcar crudo / blanco / refinado / orgánico**: tipos de azúcar producido, en toneladas. El
  refinado y el orgánico recién se publican por separado desde 2023.
- **TMCV**: el azúcar total expresado en toneladas métricas de valor crudo, la unidad de
  comparación internacional.
- **Alcohol producido**: metros cúbicos. La columna *Anhidradora* nombra a la empresa que
  deshidrata ese alcohol para bioetanol; **es un atributo actual copiado en todas las hojas, no un
  dato del año**, y por eso no entra al dataset.
- **Rendimiento %**: ver §5, no es azúcar sobre caña.

### 1.2 Ingenios y departamentos

El CAA publica por **ingenio**, no por departamento. Para Salta las dos cosas coinciden, porque la
provincia tiene exactamente dos y están en departamentos distintos:

| ingenio | localidad | departamento |
|---|---|---|
| San Isidro | Campo Santo | General Güemes |
| San Martín del Tabacal | Hipólito Yrigoyen | Orán |

**Es la ubicación de la fábrica, no la del cañaveral.** La caña que muele Tabacal viene de Orán y
San Martín, y la de San Isidro de Güemes y Anta. El dataset llena `departamento` sólo para estos
dos ingenios; para los de Tucumán y Jujuy queda vacío, porque no se verificó el mapa.

«Litoral» es como el CAA rotula a los tres ingenios de Santa Fe (Inaza, Las Toscas y San Javier).
Su última zafra en la serie es 2021. El CAA menciona producción en Misiones, pero no aparece en
ninguna planilla.

---

## 2. Los dos ingenios de Salta están intercambiados entre 1990 y 2002

En el libro histórico, lo que figura como **«San Isidro»** (1,0–1,6 millones de toneladas de caña)
es **Tabacal**, y al revés. Tres pruebas convergentes:

**a) La prueba documental.** La Nación del **5 de agosto de 1999** («Volvió el azúcar a Campo
Santo») informa sobre el ingenio San Isidro de Campo Santo: que *en 1996, último año de actividad,
la fábrica produjo 5600 toneladas*, que estuvo **dos años paralizado**, y que al reabrir se
procesarían **220.000 toneladas de caña**. La planilla pone exactamente ese perfil en la fila
rotulada **Tabacal**:

| zafra | azúcar (t) | caña (t) | lo que dice La Nación |
|---|---|---|---|
| 1995 | 5.627 | 56.967 | — |
| 1996 | 5.627 | 56.967 | «5600 toneladas, último año de actividad» |
| 1997 | 0 | 0 | paralizado |
| 1998 | 0 | 0 | paralizado |
| 1999 | 19.458 | 217.519 | «se procesarán 220.000 toneladas de caña» |

**b) La prueba de continuidad.** Corregida la asignación, cada ingenio pasa sin saltos por
2002‑2003. Sin corregir hay un derrumbe del 86 % en uno y un salto de ×9,3 en el otro, **el mismo
año y en sentidos opuestos**: 1.570.336 → 214.494 t de caña en el rotulado San Isidro y 185.014 →
1.719.720 t en el rotulado Tabacal. De las 23 series de ingenio del país es **el único par
espejado**; los demás saltos grandes que detecta el control (Leales 1993, Santa Bárbara 1992, Las
Toscas 2008, Inaza 1991, San Juan 2018) son de un solo lado y corresponden a paradas reales.

**c) La prueba cruzada.** El libro de alcohol, para los mismos años, pone a Tabacal muy por encima
de San Isidro (9.596 contra 3.114 m³ en 1990), que es el orden correcto. Los dos libros se
contradicen entre sí.

**Qué se hizo.** Nada: el dataset conserva el tramo **tal como lo publica la fuente** y marca esas
140 filas con `calidad = rotulo_dudoso`, para que quien las use sepa en qué está parado. El
tablero, por decisión del usuario, **empieza la apertura por ingenio en 2010**, bastante después
del tramo afectado. **El total provincial no está afectado**: la suma de los dos ingenios es la
misma con cualquiera de las dos asignaciones, y va desde 1990.

Como incidencia menor del mismo tramo: 1995 y 1996 tienen **valores idénticos** (5.627 t de azúcar
y 56.967 t de caña), lo que es una copia y no una coincidencia. La Nación atribuye las 5.600 t a
1996, así que el valor dudoso es el de 1995.

---

## 3. El azúcar de Ledesma en 2024 es imposible en el libro histórico

El libro histórico informa para Ledesma en 2024 **593.287 t de azúcar sobre 3.470.652 t de caña**:
el **17,1 %**. La caña tiene del orden del 12 % de sacarosa y el azúcar efectivamente recuperado
nunca llega a eso, así que el número está mal. El libro nuevo corrige esa celda a 249.893 t
(7,2 %). Es la única fila imposible de las 984 que tienen azúcar y caña en los dos libros.

Consecuencia para el dataset: el azúcar de 2024 se toma del libro nuevo —la regla general, §4— y
**el TMCV de ese año se descarta**, porque el libro nuevo no publica TMCV y arrastrar el del
histórico (620.467 t para Ledesma) dejaría en la misma fila un TMCV derivado del valor malo junto a
un azúcar corregido. Por eso la serie de `azucar_tmcv_t` **termina en 2015**, que es donde termina
el tramo en que el libro histórico es la fuente del azúcar.

---

## 4. Precedencia entre libros y qué difieren

**Regla: donde se superponen manda el libro nuevo.** El histórico aporta los años que el nuevo no
trae (1990–2015), los ingenios que el nuevo no trae (los tres del Litoral, que desde 2016 sólo
están en el histórico) y las celdas que el nuevo deja vacías.

El cotejo celda por celda de los **nueve años superpuestos** (2016–2024 en azúcar, 2016–2023 en
alcohol) encuentra 88 celdas distintas en azúcar y 31 en alcohol. Agrupadas:

| qué difiere | años | lectura |
|---|---|---|
| **Caña molida**, casi todos los ingenios | 2016 (20) y 2018 (17) | El libro nuevo informa caña **bruta** y el histórico caña neta. En 2017 y de 2019 en adelante los dos libros coinciden exactamente. |
| **Blanco contra refinado y orgánico** | 2023 y 2024 | No es un desacuerdo: el histórico mete el refinado y el orgánico **dentro de «blanco»** y el nuevo los abre. Los totales coinciden. |
| **La Corona y La Florida intercambiados** | 2016 | Los dos libros se cruzan el azúcar de estos dos ingenios de Tucumán (43.695 y 101.033 contra 101.033 y 43.695). No afecta a Salta y no se corrige. |
| **Ledesma** | 2024 | §3. |
| **Alcohol**, varios ingenios | 2016, 2017, 2019, 2020, 2023 | Revisión de la fuente: el libro nuevo informa menos alcohol que el histórico en 2016 (−75.400 m³ en el país) y más en 2023 (+7.081). |

**En Salta, el azúcar de los dos ingenios da idéntico en los nueve años superpuestos.** Las únicas
diferencias de la provincia son la caña de 2016 y 2018 (bruta contra neta), la apertura de 2023 y
2024 (blanco contra refinado y orgánico, con el total igual) y el alcohol de 2016, 2017 y 2023.

---

## 5. El «Rendimiento %» de la fuente no es azúcar sobre caña

Tabacal 2025: **19.984 t de azúcar sobre 1.802.042 t de caña es el 1,1 %, y la planilla dice
10 %**. En 124 de las 200 filas que traen rendimiento el número publicado no es ese cociente.

La brecha acompaña a la producción de alcohol, lo que sugiere que el rendimiento incluye el azúcar
*equivalente* de la caña desviada a alcohol. Pero la equivalencia implícita **no es estable**: para
cerrar cada fila hacen falta entre −0,19 y 3,88 toneladas de azúcar por m³ de alcohol, con mediana
0,82, lejos de la constancia que tendría una definición técnica. **La definición del indicador
queda sin establecer.**

Por eso `rendimiento_fuente_pct` se publica tal como lo informa la fuente —es un dato de la
fuente y no se tira— **y el tablero no lo usa**: calcula su propio azúcar por tonelada de caña
(`azucar_total_t / cana_molida_t`) y sus propios litros de alcohol por tonelada.

Ojo al leer ese cociente propio: **el escalón de 2016 es de definición, no de producción**. Al
pasar a caña bruta el denominador crece y el cociente baja cerca de un cuarto **en todas las
provincias a la vez** (el país va de 10,9 % en 2015 a 8,0 % en 2016). Lo que distingue a Salta es
que **sigue bajando después** —3,4 % en 2025, contra 7,4 % de Tucumán y 7,6 % de Jujuy—, y eso sí
es real: es caña que va a alcohol en vez de a azúcar. Los litros de alcohol por tonelada de caña de
Salta pasan de 25–36 antes de 2016 a 45–49 ahora, el doble del promedio del país.

---

## 6. Esquema del CSV

```
anio,provincia,departamento,ingenio,metrica,valor,calidad,fuente_doc
```

| columna | contenido |
|---|---|
| `anio` | zafra, 1990–2025 |
| `provincia` | `Jujuy` · `Salta` · `Tucumán` · `Litoral`, más `NOA` y `Total del país` en las filas agregadas |
| `departamento` | `General Güemes` o `Orán`; vacío fuera de Salta |
| `ingenio` | nombre canónico, o `Total` en las filas agregadas |
| `metrica` | ver abajo |
| `valor` | decimal con `.`, sin separador de miles |
| `calidad` | `definitivo` · `historico` · `rotulo_dudoso` · `derivado` |
| `fuente_doc` | el XLSX del que salió la celda; vacío en los agregados |

| `metrica` | unidad | cobertura |
|---|---|---|
| `cana_molida_t` | toneladas | 1990–2025 |
| `azucar_total_t` | toneladas | 1990–2025 |
| `azucar_blanco_t` · `azucar_crudo_t` | toneladas | 1990–2025 |
| `azucar_refinado_t` · `azucar_organico_t` | toneladas | 2023–2025 |
| `azucar_tmcv_t` | toneladas de valor crudo | 1990–2015 (§3) |
| `alcohol_m3` | metros cúbicos | 1990–1994 y 2007–2025 (§7) |
| `rendimiento_fuente_pct` | % | 2016–2025, **no usar sin leer §5** |

Los agregados (`ingenio = Total` por provincia, `NOA` y `Total del país`) son **suma de ingenios**,
calculados acá, con `calidad = derivado`. **No** se toma la fila TOTAL que publica cada hoja:
desde 2016 el libro nuevo sólo trae los 20 ingenios del NOA, así que su TOTAL deja afuera a los
tres del Litoral que el dataset sí conserva, y tomarla rompería la identidad
`país = NOA + Litoral`. Esa fila publicada se usa para **verificar** (§8). `NOA` son las tres
provincias azucareras: Jujuy, Salta y Tucumán.

---

## 7. Faltantes de la fuente, que quedan como huecos y no como ceros

- **Alcohol por ingenio, 1995–2006**: no existe. Las hojas están todas en cero, y de 2000 a 2006
  queda además un total del país suelto en una columna aparte, sin apertura. Un cero no es un dato:
  esos trece años **no se emiten**. El año 2021 tiene el mismo problema en el libro histórico, pero
  lo aporta el nuevo.
- El tablero, además, **arranca la serie de alcohol en 2007** y no en 1990. El eje de los gráficos
  es categórico: si se dibujaran los cinco años previos (1990–1994, entre 7.576 y 12.710 m³ en
  Salta), 1994 quedaría pegado a 2007 y el hueco de trece años se cerraría sin que se vea. **El
  dataset conserva esos cinco años.**
- **Refinado y orgánico**: no existen antes de 2023; estaban dentro de «blanco». El quiebre de ese
  año en la composición es de cobertura, no de producción.

---

## 8. Formato numérico detectado

| origen | configuración | criterio |
|---|---|---|
| las cuatro planillas XLSX | **numérica nativa**, no texto | `openpyxl` devuelve `int`/`float` en todas las celdas de datos; no hay separadores que interpretar y no hay ambigüedad entre configuración inglesa y latina |
| celdas vacías y de texto | descartadas | sólo se toma lo que es `int` o `float`; una celda con texto en una columna numérica no se convierte, se ignora |

No hubo valores que no parsearan, ni separadores latinos remanentes, ni mojibake: los nombres con
acento y la `Ñ` de Ñuñorco llegan bien y se normalizan contra un diccionario cerrado. La salida es
UTF‑8 con BOM, decimal `.`, sin separador de miles.

Verificación de cumplimiento sobre el CSV terminado, releído como texto crudo:

| control | resultado |
|---|---|
| UTF‑8 con BOM, CRLF | sí, 5.659 líneas |
| Valores que no cumplen configuración inglesa | **0** |
| Valores con coma | **0**; máximo 3 decimales (el alcohol) |
| Mojibake (`Ã`, `â€`) | ninguno |
| Claves `anio × provincia × ingenio × métrica` duplicadas | **0** |
| Valores negativos | **0** |
| Porcentajes fuera de 0–100 | **0** |
| Años faltantes dentro del rango 1990–2025 | ninguno |
| Celdas vacías en columnas obligatorias | **0** |
| Ceros | 533, todos reales (un ingenio que no produjo ese tipo de azúcar o no molió ese año); los faltantes van como fila ausente, no como cero |

## 9. Transformaciones aplicadas

1. **Anclaje del encabezado**: en cada hoja se busca la celda que dice «Provincia» y de ahí salen
   la fila de encabezado y la columna de arranque. Hace falta porque el encabezado está en la fila
   1 o en la 2 según el año y varias hojas arrancan en la columna B.
2. **Mapeo de columnas por nombre normalizado** (minúsculas, sin acentos): `Total Caña Molida (tn)`
   y `Total Caña Molida BRUTA (tn)` caen las dos en `cana_molida_t`.
3. **Normalización de nombres de ingenio** contra un diccionario cerrado: `Rio Grande` → `Río
   Grande`, `Santa Barbara` → `Santa Bárbara`, `Tabacal ` → `Tabacal`. En 2013 y 2014 el histórico
   rotula `Famaillá / Fronterita` a lo que el resto de la serie llama `Famaillá`: se toma lo que
   está antes de la barra. **Un rótulo que no esté en el diccionario se reporta como incidencia y
   la fila no entra**, para que un cambio de la fuente no pase callado.
4. **Rendimiento a porcentaje**: la fuente lo guarda como fracción (`0,09`) y se publica como `9`.
5. **Agregados** de provincia, NOA y país por suma.

---

## 10. Verificación

### Valores de control

Nueve, todos exactos. Los dos de 2024 de San Isidro coinciden con el parte de cierre de zafra que
publicó el IPAAT, que es una fuente independiente del CAA.

| serie | valor |
|---|---|
| Salta, San Isidro, caña 2024 · 2025 | 683.063 · 729.127 t |
| Salta, San Isidro, azúcar 2024 | 60.585 t |
| Salta, San Isidro, azúcar orgánico 2025 | 56.878 t |
| Salta, Tabacal, azúcar 2025 | 19.984 t |
| Salta, Tabacal, alcohol 2025 | 115.158,756 m³ |
| Salta, San Isidro (rótulo de la fuente), azúcar 1990 | 118.010 t |
| País, azúcar total 2025 | 1.761.438 t |
| País, caña molida 2025 | 25.095.271 t |

### Controles automáticos

| control | resultado |
|---|---|
| Cierre vertical: suma de ingenios contra la fila TOTAL de cada hoja, columna por columna | 79 hojas, **1 desvío** (histórico 2019, azúcar crudo: la fila dice 149.006 y los ingenios suman 149.206) |
| Cierre horizontal: crudo + blanco + refinado + orgánico = total | 984 filas, **0 desvíos** |
| Azúcar sobre caña por encima del 13 % | **1 fila**, Ledesma 2024 en el histórico (§3) |
| Total del país contra NOA + Litoral | 200 celdas, **0 desvíos** |
| Años con la apertura toda en cero | 13, todos de alcohol (§7) |
| Saltos año a año de más de ×3 o menos de ×0,34 | **12**, todos explicados: el par espejado de Salta 2002‑2003 (§2) y nueve paradas o reaperturas reales de ingenios |

### Los saltos, uno por uno

| serie | años | lectura |
|---|---|---|
| Salta / San Isidro y Salta / Tabacal, azúcar y caña | 2002→2003 | el intercambio de rótulos (§2) |
| Tucumán / San Juan, caña | 2017→2018 | parada del ingenio: 292.452 → 3.932 t |
| Tucumán / Leales, caña | 1992→1993 y 1993→1994 | parada y reapertura |
| Tucumán / Santa Bárbara, azúcar y caña | 1991→1992 y 1992→1993 | parada y reapertura |
| Litoral / Inaza, caña | 1990→1991 | caída de 295.947 a 72.912 t |
| Litoral / Las Toscas, caña | 2007→2008 | caída de 145.540 a 21.874 t |

---

## 11. Incidencias

1. **Los dos ingenios de Salta intercambiados, 1990–2002** (§2). No corregido; 140 filas marcadas
   `rotulo_dudoso`; el tablero abre por ingenio recién en 2010.
2. **1995 repite los valores de 1996** en la fila de uno de los dos ingenios de Salta (§2).
3. **Ledesma 2024 en el histórico: 17,1 % de azúcar sobre caña, imposible** (§3). El dataset usa el
   valor del libro nuevo; el TMCV de 2016 en adelante se descarta por coherencia.
4. **La Corona y La Florida intercambiados en 2016** entre los dos libros (§4). No afecta a Salta;
   no se corrige. El dataset publica la versión del libro nuevo.
5. **Cambio de definición de la caña molida en 2016** (neta → bruta), que mueve todos los cocientes
   por tonelada de caña (§5).
6. **El «Rendimiento %» no es azúcar sobre caña y su definición no pudo establecerse** (§5). Se
   publica, no se usa.
7. **Alcohol por ingenio inexistente entre 1995 y 2006** (§7).
8. **Refinado y orgánico abiertos recién desde 2023** (§7).
9. **Enlace roto en la página del CAA**: `produccion-de-alcohol-desde-1990.xlsx` devuelve 404. El
   script sigue con el otro candidato de la misma ranura.
10. **Las URL de las planillas cambian cada vez que el CAA publica una zafra**, porque llevan la
    carpeta de subida. Resuelto raspando las páginas en vez de fijar las direcciones.

## 12. Supuestos y limitaciones

- El dato es **por zafra** (mayo a mediados de noviembre), no por año calendario de actividad.
- El `departamento` es el de **la fábrica**, no el del cañaveral, y sólo se completa para Salta.
- Los agregados de provincia, NOA y país son **suma de los ingenios que la fuente publica**. Si un
  ingenio no informa un año, no suma: no se imputa nada.
- La producción de Misiones que el CAA menciona en su texto institucional no está en las planillas
  y por lo tanto no está en el dataset.
- El cotejo entre libros se hace sobre los años superpuestos; para 1990–2015 no hay segunda fuente
  con la cual contrastar, salvo los controles internos de cierre y plausibilidad.
