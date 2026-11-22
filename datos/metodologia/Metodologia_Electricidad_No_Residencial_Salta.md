# Metodología — Consumo eléctrico no residencial por departamento (ENRESP)

Dataset: `Electricidad_No_Residencial_Salta_departamento_mensual.csv`
Script: `actualizar_electricidad_no_residencial_salta.py`
Corrida de referencia: 22 de noviembre de 2026.

---

## 1. Fuente

| | |
|---|---|
| Título | Matriz de Indicadores de Consumo, Cobertura y Estructura Tarifaria del Servicio Eléctrico |
| Organismo | Ente Regulador de los Servicios Públicos de Salta (ENRESP) |
| Portal | `https://datospublicos.salta.gob.ar/dataset/02134503-89a3-49e6-8ceb-4a74d3d50b5f` |
| Licencia | Creative Commons Attribution 4.0 |
| Última modificación del recurso | 28 de octubre de 2026 |
| Método | descarga del CSV, con la URL resuelta por la API de CKAN (`package_show`) |
| Universo | 23 departamentos × 33 meses = **759 filas**, de enero de 2024 a septiembre de 2026 |

El nombre del archivo lleva el largo de la serie —`1_no_residencial_departamental_maestro_33m.csv`—
así que **cambia en cada actualización**. Por eso el script no hardcodea la URL de descarga: pide
`package_show` con el `dataset_id`, que sí es estable, y toma el primer recurso CSV. Queda una URL
de respaldo, la vigente al 28-oct-2026, y si hay que usarla el script lo informa.

### Columnas del archivo original

`año`, `mes`, `departamento`, `usuarios`, `factura_promedio_pesos`, `consumo_kwh_ponderado`,
`porc_vad`, `porc_impuestos`, `porc_energia`, `mes_num`, `periodo`, `fecha`,
`facturacion_total_estimada_pesos`, `consumo_total_estimado_kwh`, más **dos columnas vacías** al
final de cada línea.

---

## 2. Qué mide, y sobre todo qué no mide

El dataset cubre **únicamente el segmento no residencial**. Tres consecuencias que hay que tener
presentes antes de usar cualquier número de acá:

1. **No es la demanda eléctrica total de la provincia.** Falta el segmento residencial, que el
   ENRESP no publica en este dataset —tiene un solo recurso—.
2. **No se compara con la generación.** El tema `energia-electrica` del Monitor mide generación de
   CAMMESA; esto es consumo facturado de una parte de la demanda. Son dos cosas distintas y no
   cierran entre sí.
3. **«No residencial» es una sola bolsa.** La fuente no abre por categoría tarifaria, así que
   comercio, industria y alumbrado público van juntos. Es lo que explica que General Güemes
   consuma 5.543 kWh por usuario y mes y La Poma 283: son estructuras productivas distintas, no
   un error.

---

## 3. El consumo total es una estimación, no una medición

Se verificó **fila por fila, en las 759**, que:

```
consumo_total_estimado_kwh = usuarios × consumo_kwh_ponderado
```

sin una sola desviación por encima de 0,05 kWh. Lo mismo vale para
`facturacion_total_estimada_pesos = usuarios × factura_promedio_pesos`.

Es decir: **el total no es la suma de los medidores**, es el padrón multiplicado por un consumo
medio. El nombre de la columna ya lo dice («estimada») y el script lo comprueba en cada corrida,
para que quede registrado y no se lo tome por un dato de medición. El tablero lo repite en la
advertencia del tema.

---

## 4. El padrón de usuarios se congela desde julio de 2026

En **los 23 departamentos a la vez**, el valor de junio de 2026 se repite idéntico en julio, agosto
y septiembre, mientras el consumo por usuario sigue moviéndose mes a mes. Capital, por ejemplo:

| mes | usuarios |
|---|---|
| 2026-04 | 15.485 |
| 2026-05 | 15.318 |
| **2026-06** | **15.351** |
| 2026-07 | 15.351 |
| 2026-08 | 15.351 |
| 2026-09 | 15.351 |

**Por qué no es casualidad:** en el resto de la serie hay rachas de valores repetidos —es normal en
un padrón chico que un departamento no registre ningún alta ni baja en un mes—, pero nunca pasan de
**4 departamentos simultáneos**. Acá son **23 de 23**, tres meses seguidos. La fuente arrastró el
último padrón conocido y siguió estimando sobre él.

**Qué se hizo:**

- El CSV **conserva los tres meses** y los marca con `usuarios_arrastrados = 1`.
- El script tiene una verificación dedicada —la que encontró el problema— que vuelve a correr en
  cada actualización y avisa si reaparece.
- En el tablero **la serie de usuarios termina en junio de 2026**, el último mes con padrón propio.
  El adaptador no hardcodea esa fecha: lee la columna `usuarios_arrastrados`, así que el corte se
  mueve solo cuando la fuente retome la actualización.
- **La serie de consumo se publica completa**, hasta septiembre de 2026. El padrón se mueve en
  torno al 1 % mensual, de modo que el error que arrastra la estimación de esos tres meses es del
  mismo orden: cortar cuatro meses de consumo por eso sería perder más de lo que se gana. La
  salvedad queda escrita en el tema.

---

## 5. Los usuarios son un stock; el consumo, un flujo

Dos métricas de naturaleza distinta, y por eso con dos reglas de agregación **en cada dirección**:

| | entre departamentos | entre meses |
|---|---|---|
| `consumo_total_kwh` | se **suma** | se **suma** |
| `usuarios` | se **suma** (el total provincial son los usuarios de los 23) | se **promedia** (el padrón de un trimestre no son los usuarios de sus tres meses sumados) |

En el adaptador del sitio esto se resuelve explícitamente: `ELEC_METRICAS` declara
`"agg": "mean"` para `usuarios` —que es lo que usan `build.py` y `charts.js` para la dirección
temporal, igual que `parque_automotor` en el tema de patentamiento— y el agregado entre
departamentos se calcula sumando, antes de emitir las filas.

Comprobación: el promedio mensual de usuarios de 2025 es **32.575**, no 390.903, que es lo que
daría sumarlos.

---

## 6. Esquema del CSV de salida

Una fila por departamento y mes, las 759. Se conservan todas las columnas de la fuente aunque el
tablero use sólo dos, para no tener que volver a bajar nada si mañana se arma el tablero tarifario.

| columna | contenido |
|---|---|
| `anio`, `mes`, `periodo` | año, número de mes y `AAAA-MM` |
| `departamento` | canónico, los 23 de Salta |
| `usuarios` | usuarios no residenciales con servicio, a fin de mes. **Stock** |
| `consumo_kwh_por_usuario` | el `consumo_kwh_ponderado` de la fuente, renombrado para que se entienda qué es |
| `consumo_total_kwh` | estimación de la fuente: usuarios × consumo por usuario |
| `factura_promedio_pesos` | pesos corrientes |
| `facturacion_total_estimada_pesos` | usuarios × factura promedio, pesos corrientes |
| `porc_energia`, `porc_impuestos`, `porc_vad` | composición de la tarifa, suma 100 |
| `usuarios_arrastrados` | **1** si ese mes repite el padrón anterior en los 23 departamentos a la vez |

Se descartan `fecha` (formato `1/9/2026`, redundante con `periodo`), `mes_num` (idéntico a `mes`) y
las dos columnas vacías del final.

**Las columnas en pesos quedan fuera del tablero.** Son pesos corrientes y, si alguna vez se usan,
hay que deflactarlas con el IPC NOA (`_ipc_anual()` en `adapters.py`) como hace el resto del sitio.

---

## 7. Formato numérico

La comprobación decisiva de esta fuente **no es el decimal sino el separador de campo**: el archivo
viene con `;`, no con `,`. El decimal es `.`, así que la configuración es inglesa; si alguna celda
numérica trajera una coma sería configuración latina y cambiaría el valor, de modo que el script la
reporta como incidencia en vez de adivinar.

| columna | configuración detectada | criterio |
|---|---|---|
| `usuarios` | enteros | sin separadores |
| `consumo_total_estimado_kwh` | **inglesa** | decimal `.` con dos dígitos (`2923876.58`); ninguna celda con `,` |
| `consumo_kwh_ponderado`, `factura_promedio_pesos` | **inglesa** | ídem |
| `porc_*` | **inglesa** | decimal `.`, los tres suman 100,00 |
| `periodo` | `AAAA-MM` | — |

Cumplimiento sobre el CSV de salida:

| comprobación | resultado |
|---|---|
| valores numéricos que no parsean | **0** |
| celdas numéricas con coma | **0** |
| filas con usuarios o consumo no positivos | **0** |
| filas donde energía + impuestos + VAD ≠ 100 | **0** |
| saltos de orden de magnitud (>1000× la mediana del departamento) | **0** |
| filas faltantes o repetidas en el panel | **0** y **0** |
| encoding | UTF-8 con BOM, **0 mojibake** |

El archivo de origen también viene limpio: UTF-8 con BOM, CRLF, sin mojibake.

**Salvedad:** `porc_vad` viene en **cero en 115 de las 759 filas** (los primeros meses de 2024). No
es un valor agregado nulo sino un dato que la fuente todavía no informaba. Queda en el CSV, tal
cual, y fuera del tablero.

---

## 8. Geografía

Los 23 departamentos de Salta, todos presentes en los 33 meses. La fuente escribe
`Rosario De La Frontera` y `Rosario De Lerma` con la preposición en mayúscula; la tabla canónica del
script los resuelve por clave sin acentos, igual que `_DEPT_CANON` en `adapters.py`. Ningún
departamento desconocido.

---

## 9. Valores de control

Los reproduce el script en cada corrida; si alguno falla, lo informa como incidencia.

| control | valor |
|---|---|
| Filas · departamentos · meses | 759 · 23 · 33 |
| Período | 2024-01 a 2026-09 |
| Usuarios, total provincial 2024-01 | 33.421 |
| Usuarios, total provincial 2026-05 | 32.162 |
| Meses con padrón arrastrado | 3 (2026-07 a 2026-09) |
| Consumo 2024 | 803.431 MWh |
| Consumo 2025 | 787.142 MWh |
| Consumo de Capital 2025 | 392.490 MWh |
| Filas que violan la identidad interna | 0 |

**Resultado de la corrida del 22-nov-2026: 11 de 11 controles exactos.**

---

## 10. Lo que muestra el dato

| | 2024 | 2025 | 2026 (9 meses) |
|---|---|---|---|
| Consumo no residencial | 803.431 MWh | 787.142 MWh | 606.235 MWh |
| Usuarios (promedio mensual) | 32.717 | 32.575 | 32.404 |

- **Estacionalidad fuerte:** el pico de enero-febrero (82.171 MWh en 2026-01) casi duplica el piso
  de mayo-junio (55.236 MWh en 2025-05). Cualquier comparación entre meses consecutivos mide
  estación, no actividad; la comparación útil es contra el mismo mes del año anterior, que es la
  que usa el indicador de la portada.
- **Concentración:** Capital explica el **47 %** del consumo no residencial de la provincia
  (385.615 MWh en los últimos doce meses, sobre 813.226).
- **Intensidad muy despareja:** General Güemes es el segundo departamento por consumo
  (92.193 MWh) con sólo 1.386 usuarios, frente a los 15.318 de Capital. Son 5.543 kWh por usuario
  y mes contra 2.098.
- **El padrón se achica despacio:** −1.190 usuarios entre enero de 2024 (33.421) y junio de 2026
  (32.231), un 3,6 % en dos años y medio.

---

## 11. Incidencias

Una, y es de la fuente:

1. **El padrón de usuarios se repite en 2026-07, 2026-08 y 2026-09**, en los 23 departamentos a la
   vez. Son estimaciones sobre un padrón viejo, no altas y bajas reales. Ver la sección 4.

No hubo valores sin parsear, ni separadores latinos, ni filas faltantes o repetidas, ni saltos de
orden de magnitud, ni departamentos desconocidos.

---

## 12. Supuestos y limitaciones

- **Sólo el segmento no residencial.** No hay demanda total de la provincia ni cruce posible con la
  generación de CAMMESA.
- **El consumo total es una reconstrucción** de la fuente (padrón × consumo medio), no una suma de
  medidores. Un error en el padrón se traslada proporcionalmente al consumo.
- **Sin apertura por categoría tarifaria.** No se puede separar comercio de industria ni de
  alumbrado público.
- **La serie es corta:** 33 meses, dos años completos. No alcanza para hablar de tendencia, y
  menos descontando la estacionalidad.
- **Los tres meses con padrón arrastrado** afectan también a la estimación de consumo, aunque en un
  orden del 1 %. Se publican igual, advertidos.
- **No se verificó contra una fuente independiente.** No hay un segundo publicador de consumo
  eléctrico por departamento en Salta con el que cotejar estas series.
