# Metodología — Patentamiento, transferencias y parque automotor (DNRPA)

Datasets: `Vehiculos_DNRPA_patentamiento_jurisdiccion_mensual.csv` ·
`Vehiculos_DNRPA_parque_automotor_jurisdiccion_mensual.csv`
Script: `actualizar_vehiculos_dnrpa.py` · Runbook: `Actualizar_Vehiculos_DNRPA.md`

---

## Resultado en una línea

Serie mensual de vehículos 0 km inscriptos y usados transferidos para las 24 jurisdicciones, desde
2000, más el parque automotor desde 2010, de la Dirección Nacional de los Registros Nacionales de
la Propiedad del Automotor. **43.800 y 5.050 filas, datos hasta octubre de 2026, 13 de 13 valores
de control exactos.**

---

## 1. Fuente

Dirección Nacional de los Registros Nacionales de la Propiedad del Automotor (DNRPA), Ministerio
de Justicia. **Dos orígenes distintos**, los dos scripteables sin navegador.

### 1.1 Seis CSV agregados, en el portal de datos abiertos de Justicia

<https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-automotores> ·
<https://datos.gob.ar/dataset/estadistica-de-tramites-de-motovehiculos> ·
<https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-maquinarias>

Licencia CC-BY 4.0, **actualización mensual**, datos al 31 de octubre de 2026. Son agregados por
año, mes y provincia —no microdatos— y el más grande pesa 370 KB. Esquema idéntico en los seis:

```
tipo_vehiculo, anio_*, mes_*, provincia_*, letra_provincia_*, cantidad_*, provincia_id
```

| categoría | operación | cobertura |
|---|---|---|
| Autos (automotores) | inscripciones iniciales · transferencias | 2000-01 → 2026-10 (322 meses) |
| Motos (motovehículos) | inscripciones iniciales · transferencias | 2007-01 → 2026-10 (238 meses) |
| Maquinarias | inscripciones iniciales · transferencias | 2013-09 → 2026-10 (158 meses) |

Cada categoría arranca cuando la DNRPA empieza a publicarla. **Antes de esa fecha la categoría no
existe, no vale cero**, y por eso la serie del total se trata como se explica en §5.

### 1.2 El parque activo, una página HTML por año

`https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_parque.php?anio=AAAA&origen=portal_dnrpa`,
de 2010 a 2026. Cada página trae una tabla de 24 provincias × 12 meses más la fila TOTAL.

No existe como dato abierto: es la única vía. Responde a un **GET limpio, sin sesión** —el
formulario POST de inscripciones de la misma sección sí la exige y devuelve «No existe un id de
sesión válida», el parque no—.

### 1.3 Qué es cada cosa

- **Inscripción inicial**: alta registral de un vehículo **0 km**. Es el patentamiento.
- **Transferencia**: cambio de titular de un vehículo **usado**.
- **Parque activo**: vehículos **en condiciones registrales de circular** a fin de cada mes. Es un
  stock, no un flujo.

Las tres se cuentan por la **provincia del registro seccional** donde se hizo el trámite, que no
siempre es donde el vehículo circula.

---

## 2. Por qué no se usa el archivo del portal provincial

El pedido apuntaba a `06_patentamiento_transferencias_vehiculos_salta_2014_2026.csv`, del portal de
datos abiertos de Salta (Dirección General de Estadísticas), publicado el 19 de noviembre de 2026.
Ese archivo copia estas mismas series de la DNRPA. **Está mal.** El cotejo celda por celda lo
produce el propio script con `--contra-salta`:

| categoría | operación | años con diferencias |
|---|---|---|
| Autos | inscripciones iniciales | **2017 (12 meses, total 21.380 vs 24.227); 2018 (12 meses, total 10.952 vs 21.380)**; 2026 (2 meses) |
| Autos | transferencias | 2018 (8 meses) |
| Motos | inscripciones iniciales | 2018 (8 meses); 2023 (1 mes, total 19.313 vs 19.312); 2026 (2 meses) |
| Motos | transferencias | 2018 (8 meses); 2024 (1 mes, total 3.846 vs 3.845) |
| Maquinarias | inscripciones iniciales | 2018 (8 meses) |
| Maquinarias | transferencias | 2018 (7 meses) |

Son tres defectos distintos:

1. **Todo 2018 está permutado, en las seis series.** El total anual coincide, pero 7 u 8 de los 12
   meses están en el lugar equivocado.
2. **Autos / inscripciones iniciales está además corrida un año.** Su columna «2017» es el 2018
   real de la DNRPA; su «2018» son los doce valores del 2019 real **ordenados de mayor a menor**
   (1.385, 1.170, 957, 955, 905, 875, 841, 821, 802, 782, 761, 698: estrictamente decreciente, que
   ninguna serie mensual real es); y su «2019» es el 2019 real otra vez. **El 2017 real —24.227
   autos, el año récord de la serie— no figura en el archivo.**
3. **Dos celdas de diciembre con una unidad de diferencia** (motos insc. 2023-12, motos transf.
   2024-12), donde el archivo provincial está por encima. Parece una revisión posterior de la
   fuente.

De las 72 series anuales del archivo provincial, **exactamente una es monótona** (autos 2018,
decreciente) y **exactamente un par de años comparte el mismo multiconjunto de doce valores**
(autos 2018 y 2019). La firma es la de una planilla ordenada por la columna de cantidad y guardada
así.

Publicado tal cual, el tablero mostraría un derrumbe del 49 % en 2018 que nunca ocurrió y borraría
el pico de 2017. La serie correcta pone el derrumbe donde fue: **2019**, cuando el patentamiento
total de Salta cae de 46.088 a 23.537.

El archivo provincial tampoco llega tan lejos: corta en **febrero de 2026**, ocho meses antes que
la DNRPA.

---

## 3. Esquema de los CSV

**Patentamiento** — 43.800 filas, 25 jurisdicciones (24 más el total del país), 322 meses:
```
anio,n_mes,mes,periodo,jurisdiccion,categoria,metrica,valor
```
`categoria`: `Total` · `Autos` · `Motos` · `Maquinarias`.
`metrica`: `inscripciones_iniciales` · `transferencias`.

**Parque automotor** — 5.050 filas, 25 jurisdicciones, 202 meses:
```
anio,n_mes,mes,periodo,jurisdiccion,metrica,valor
```
`metrica`: `parque_automotor`.

Los dos en UTF-8 con BOM, separador `,`, decimal `.`, CRLF, como el resto del repositorio. Todos
los valores son enteros; no hay celdas vacías.

`categoria` es un **margen**: `Total` es la suma de las otras tres, no una categoría más. Un
gráfico que no la fije suma el margen con sus partes y duplica el total. Es el mismo esquema que
`envase` en cemento y `tipo_usuario` en seguridad vial.

---

## 4. Formato numérico detectado

| origen | configuración | criterio |
|---|---|---|
| los seis CSV agregados | **inglesa**, enteros sin separador | la columna `cantidad_*` no tiene ni punto ni coma en ninguna de sus filas |
| las páginas de parque | **latina**, miles con punto (`17.759.435`) | el punto siempre va seguido de exactamente 3 dígitos y en posiciones de agrupamiento; ningún valor tiene decimales |

La salida queda toda en configuración inglesa. Verificación posterior sobre los dos CSV: **0
valores con coma, 0 valores que no parsean, 0 celdas vacías**, todos enteros.

---

## 5. Transformaciones aplicadas

1. **Normalización de jurisdicciones.** Las dos fuentes las escriben distinto: los CSV en
   mayúsculas y minúsculas con acentos (`Ciudad Autónoma de Bs.As.`), las páginas de parque en
   mayúsculas sin acentos y abreviadas (`CABA`, `S. DEL ESTERO`, `T. DEL FUEGO`). Un diccionario
   único las lleva a la forma del Monitor; una etiqueta que no esté en él es incidencia, nunca se
   adivina. **`Ciudad Autónoma de Bs.As.` sale como `CABA`.**
2. **`Total del país`**: suma de las 24 jurisdicciones en patentamiento (la fuente no lo publica);
   **fila TOTAL publicada** en el parque, con la suma usada sólo para verificar.
3. **Categoría `Total`: sólo desde septiembre de 2013**, que es cuando están las tres. Sumar lo que
   hubiera dibujaría dos escalones —uno en 2007, cuando entran las motos, y otro en 2013-09, cuando
   entran las maquinarias— que serían cambios de cobertura, no de patentamiento. Se omite en 164
   meses.
4. **Relleno con cero de un caso**: la fuente no trae ninguna fila de **La Rioja en transferencias
   de maquinarias durante todo 2014** (12 celdas). Los agregados de la DNRPA sí emiten ceros
   explícitos —570 en esa misma serie—, así que una fila ausente no es su forma normal de escribir
   un cero; se completa igual, porque dejar el hueco haría que la categoría `Total` de esos meses
   se calcule sobre 23 jurisdicciones en vez de 24. Queda reportado como incidencia.
5. **Descarte de los meses del parque todavía no publicados.** En el año en curso la fuente los
   devuelve con **0**, y un parque no puede ser cero. Se descartan por la fila TOTAL del país, que
   es el único testigo confiable: en esta corrida, noviembre y diciembre de 2026.

---

## 6. Verificación

### Valores de control

Verificados contra la fuente, **13 de 13 exactos**:

| serie | valor |
|---|---|
| Salta, autos, inscripciones, 2014 · 2017 · 2018 · 2019 · 2025 | 14.892 · **24.227** · **21.380** · 10.952 · 13.911 |
| Salta, motos, inscripciones, 2017 · 2025 | 30.833 · 25.103 |
| Salta, maquinarias, inscripciones, 2025 | 208 |
| Salta, autos, transferencias, 2025 | 22.218 |
| Salta, parque automotor, dic-2010 · dic-2019 · dic-2024 | 158.954 · 313.471 · 358.452 |
| País, parque automotor, dic-2024 | 18.064.236 |

Los dos en negrita son justamente los que el archivo provincial tiene mal.

### Controles automáticos

- **Continuidad**: ningún mes faltante dentro del rango de cada serie, y las 24 jurisdicciones en
  todos los meses.
- **Suma de jurisdicciones contra el total publicado del parque**: desvío máximo **0** en los 202
  meses. El total que publica la DNRPA es exactamente la suma de sus provincias.
- **Monotonía del parque**: un stock no se derrumba de un mes al otro. Caída mensual máxima
  **3,48 %**, 3 casos por encima del 2 % (ver incidencias).
- **Saltos de orden de magnitud** en las seis series de Salta, con dos excepciones medidas sobre
  esta serie y no inventadas: se ignoran los pares donde alguno de los dos valores es menor a 30
  (en maquinarias un mes pasa de 14 a 1 sin que nada raro ocurra), y el paso de diciembre a enero
  exige una razón mayor por lo que se explica abajo.

### La estacionalidad de diciembre y enero

**El patentamiento se desploma en diciembre y se dispara en enero**, todos los años y en todo el
país, porque inscribir en enero da el año modelo nuevo y eso vale en la reventa. En el total del
país enero suele ser tres o cuatro veces diciembre (dic-2005 = 14.754 contra ene-2006 = 66.276), y
en una provincia chica la razón llega a once. **Es estacionalidad de la fuente, no un salto del
dato**: para leer tendencia conviene el grano trimestral o anual, y por eso el tablero abre en
trimestral.

---

## 7. Incidencias

Cuatro, todas de la fuente y todas explicadas:

| incidencia | qué es |
|---|---|
| La Rioja, transferencias de maquinarias, 2014 | 12 celdas que la fuente no trae; se completan con cero (§5.4) |
| Parque de CABA: −3,1 % entre 2012-10 y 2012-11 | depuración registral |
| Parque de CABA: −3,5 % entre 2016-02 y 2016-03 | depuración registral |
| Parque de Tierra del Fuego: −2,5 % entre 2016-02 y 2016-03 | la misma depuración de marzo de 2016 |

Ninguna es del proceso.

Dos rarezas más, detectadas al contrastar cada serie contra su propia mediana. **Las dos son
reales**, no artefactos de parseo, y ninguna toca a Salta:

- **Tierra del Fuego, motos 0 km, abril a noviembre de 2025.** La serie pasa de unas 50 o 100
  inscripciones mensuales a 7.428 en octubre de 2025, y vuelve a 45 en febrero de 2026. No es un
  pico aislado sino una subida y una bajada graduales a lo largo de ocho meses —535, 1.337, 2.082,
  4.736, 5.514, 6.101, 7.428, 812—, que es la forma de un fenómeno registral y no la de un error
  de lectura. Encaja con el régimen fiscal especial de la provincia. Se deja tal cual y se
  documenta.
- **Maquinarias, septiembre de 2013.** El primer mes de la serie es parcial: 31 inscripciones y 3
  transferencias en todo el país, contra 746 y 355 en octubre. La serie arranca a mitad de mes. Por
  eso el trimestre 2013-T3 y el año 2013 de maquinarias no se emiten en el tablero: la regla de
  completitud se aplica **por serie**, no de forma global, justamente para que el primer período de
  cada categoría no se dibuje como una caída.

---

## 8. Supuestos y limitaciones

1. **El parque activo de la DNRPA es sólo AUTOMOTOR: no incluye motos.** La página no tiene
   selector de tipo, trae una sola tabla y se rotula «Tipo de Vehículo: Automotor». Para Salta en
   diciembre de 2024 da 358.452 automotores, mientras que el parque **total** que publica la ANSV
   para 2022 son 654.998, de los cuales 331.144 son automotores y 313.060 motovehículos.
   Consecuencias: la tasa de renovación del tablero se calcula **sólo sobre autos**, para que
   numerador y denominador sean lo mismo; y **no alcanza para recalcular la tasa de fatalidad por
   vehículo de la ANSV**, que usa el parque total. Lo que sí habilita está en el punto 2.
2. **La métrica `tasa_fatalidad_10mil_automotor` del tema `seguridad-vial`** se calcula con este
   parque (promedio de los doce meses del año, que mide la exposición a lo largo del año mejor que
   el stock de diciembre). **No reemplaza** a la tasa cada 10 mil vehículos de la ANSV: miden cosas
   distintas y dan distinto, porque el denominador de una es la mitad del de la otra. Se agrega
   porque la de la ANSV se corta en 2023 y porque su denominador para el NOA hay que despejarlo,
   mientras que éste está publicado.
3. **El lugar del trámite no es el lugar de uso.** Todo se imputa a la provincia del registro
   seccional. Un vehículo inscripto en Salta puede circular en otra provincia y al revés.
4. **El parque de motovehículos no existe** como dato abierto de la DNRPA ni como consulta web. La
   ANSV lo publica sólo para 2017, 2019, 2020 y 2022.
5. **Los nombres de archivo de los seis CSV llevan el rango de meses** (`…-2000-01-2026-10.csv`) y
   por lo tanto **cambian en cada actualización mensual de la fuente**. Hay que actualizarlos en
   `FUENTES` dentro del script; está explicado en el runbook.
6. **No se emite el detalle por tipo de automotor** (auto, camioneta, pesado). Los agregados de la
   DNRPA no lo abren; eso está en los microdatos, que son otra cosa y otro tamaño.
