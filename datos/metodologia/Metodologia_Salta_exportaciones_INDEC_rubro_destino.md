# Metodología — Exportaciones de Salta por rubro y destino (INDEC COMEX)

Dataset: `Salta_exportaciones_INDEC_rubro_destino_desde_2021.csv`
Fecha de elaboración: 2026-08-25.

## Fuente

- **Organismo:** INDEC — Comercio Exterior (COMEX Argentina), <https://comex.indec.gob.ar/#/database>.
- **Archivo de origen:** `Datos_origen_2002_2025.xlsb`, hojas `datos origen_2012-2022` y
  `datos origen_2023-2025`.
- **Cómo se obtuvo:** el formulario del sitio (Tipo de comercio = Exportación, Año = 2025,
  Modalidad = Anual) resuelve a la URL directa
  `https://comex.indec.gob.ar/files/zips/exports_2025_Y.zip` (12.027.921 bytes). El `.zip` se
  descargó el 2026-08-25 y contiene, además del `.xlsb`, los archivos `expona25.csv`,
  `expopa25.csv`, `etotna25.csv`, `etotpa25.csv`, `prod_soja_acum_2002_2025.xlsx` y dos `.docx`
  explicativos.
- **Por qué el `.xlsb` y no los `.csv` del mismo `.zip`:** `expona25.csv` / `expopa25.csv` son de
  alcance **nacional** (posición NCM × país de destino) y **no tienen provincia de origen**. La
  apertura provincial solo está en `Datos_origen_2002_2025.xlsb`.
- **Lectura:** Python con `pyxlsb` 1.0.10 (`open_workbook`, recorrido fila por fila).

## Cobertura y unidad de análisis

- Provincia de origen **Salta** (código `SA`), años **2021 a 2025** — 2.653 filas.
- Una fila por combinación **año × rubro × país de destino**. Sin duplicados de esa clave
  (verificado: 0).
- **Periodicidad anual.** La columna `CMES` del origen vale `12` en todas las filas: es la base
  anual acumulada, no un dato de diciembre. Por eso el CSV no lleva columna de mes.
- Columnas del origen usadas: `CANIO`, `PCIA`/`DESCRIP_PCIA`, `CCOD_RUBRO`/`DESCRIP_RUBRO`,
  `CCOD_PAIS`/`DESCRIP_PAIS`, `DOLARES_FOB`, `PESO_NETO_KG`.

## Esquema del CSV

Separador `,`; decimal `.`; sin separador de miles; codificación **UTF-8 con BOM** (`utf-8-sig`),
igual que el resto de los datasets del proyecto.

| Columna | Tipo | Descripción |
|---|---|---|
| `provincia` | texto | Siempre `Salta`. |
| `anio` | entero | 2021–2025. |
| `gran_rubro` | texto | Productos primarios / MOA / MOI / Combustibles y energía (derivada, ver abajo). |
| `rubro_cod` | texto | Código de rubro del INDEC (`104C`, `19899`, …). Se conserva como texto: tiene letras. |
| `rubro` | texto | Descripción del rubro tal como viene en la fuente. |
| `confidencial` | 0/1 | 1 = fila de secreto estadístico (ver más abajo). |
| `pais_cod` | entero | Código de país del INDEC. |
| `pais_destino` | texto | Nombre del país de destino. |
| `fob_usd` | decimal | Valor FOB en dólares estadounidenses. |
| `peso_neto_kg` | decimal | Peso neto en kilogramos. |

### Columnas derivadas (las únicas dos que agrega este proceso)

- **`gran_rubro`**: se deduce del **primer dígito** de `rubro_cod` (`1` → Productos primarios,
  `2` → MOA, `3` → MOI, `4` → Combustibles y energía). La regla se validó contra las descripciones
  que la propia fuente da a sus agregados confidenciales (`19899` = "Productos primarios
  (confidencial)", `29899` = MOA, `39899` = MOI, `49899` = Combustibles y energía). Los 29 códigos
  presentes en el período quedaron asignados; **ninguno sin gran rubro**.
- **`confidencial`**: 1 cuando `rubro_cod` termina en `9899`.

## Formato numérico detectado

| Columna | Configuración detectada | Criterio usado |
|---|---|---|
| `DOLARES_FOB` | **Ninguna (binario nativo)** | El `.xlsb` almacena números en binario; `pyxlsb` devuelve `float` de Python. No hay separadores que interpretar, por lo que **no existe riesgo de confusión inglés/latino** en el origen. |
| `PESO_NETO_KG` | **Ninguna (binario nativo)** | Ídem. |
| `CANIO`, `CCOD_PAIS` | texto de dígitos | Convertidos a entero. |

Se verificó que **el 100 % de las celdas FOB/KG llegó como número** (`isinstance(v, (int, float))`):
**0 celdas no numéricas**. En particular, no aparece el marcador `s` de secreto estadístico que sí
usan los `.csv` nacionales del mismo `.zip` (`expona25.csv` trae valores `s`, `s2`, `s3`…); en la
base provincial el secreto se maneja agrupando en los rubros `x9899`, no enmascarando celdas.

La escritura se hizo en formato inglés. **Relectura de control** con las mismas opciones que usa
`adapters.py` (`pd.read_csv(..., encoding="utf-8-sig")`): 0 valores con coma en las columnas
numéricas, 0 que no parsean, `fob_usd` y `peso_neto_kg` como `float64`, 0 nulos en todo el archivo.

## Verificación de totales (control cruzado independiente)

Se sumó el FOB de **todas** las provincias del `.xlsb` para 2025 y se comparó con el total nacional
que declara `etotna25.csv`, archivo distinto dentro del mismo `.zip`:

| | USD FOB |
|---|---|
| Suma de las 27 unidades del `.xlsb` (incluye Extranjero, Indeterminado y Plataforma Continental) | 87.111.196.819,24 |
| `etotna25.csv` (total nacional declarado) | 87.111.196.818,26 |
| **Diferencia** | **0,98 (+0,000001 %)** — redondeo |

Los totales anuales de Salta que resultan:

| Año | FOB USD | Peso neto kg | Confidencial (USD) | % confidencial |
|---|---|---|---|---|
| 2021 | 1.262.871.152 | 2.277.645.209 | 422.518.194 | 33,5 % |
| 2022 | 1.333.363.413 | 2.016.112.294 | 270.627.728 | 20,3 % |
| 2023 | 1.118.753.887 | 1.523.577.717 | 235.596.197 | 21,1 % |
| 2024 | 1.123.823.718 | 1.751.637.491 | 516.672.329 | 46,0 % |
| 2025 | 1.447.687.147 | 1.990.905.885 | 627.992.715 | 43,4 % |

## Incidencias

- **Valores que no parsean:** ninguno (0 de 5.306 celdas numéricas).
- **Duplicados** de la clave (año, rubro, país): 0.
- **Descripciones inconsistentes:** ningún `rubro_cod` ni `pais_cod` tiene más de una descripción a
  lo largo del período.
- **Valores negativos o FOB = 0:** ninguno.
- **Encoding / mojibake:** sin coincidencias de `Ã`, `Â`, `â€` en `rubro` ni `pais_destino`.
- **Saltos de orden de magnitud:** se compararon las series (rubro × país) a lo largo de los cinco
  años contra su mediana; **10 valores** superan 100× o quedan por debajo de 0,01× (p. ej. rubro
  `39899` a Estados Unidos: 158.138 USD en 2023 contra una mediana de 167,9 M). **No son artefactos
  de parseo** — el origen es binario, no hay separadores que malinterpretar — sino variabilidad real
  del comercio: un destino que compra un año y casi no compra otro. Se dejan **sin modificar** y se
  documentan aquí.

## Supuestos y limitaciones

- **El secreto estadístico es alto y creciente: 43–46 % del valor exportado en 2024 y 2025.** Esas
  filas (`confidencial = 1`) conservan el país de destino y el gran rubro, pero **no el rubro
  específico**. Cualquier lectura "por producto" debe tratarlas como una categoría propia y no
  repartirlas entre los rubros conocidos; los rankings de rubro fino subestiman el total.
- **Rubro ≠ posición arancelaria.** El máximo detalle de producto disponible con apertura provincial
  es el rubro (29 categorías en el período). La apertura por NCM existe solo a nivel nacional
  (`expona25.csv`).
- **Provincia de origen**, no de despacho ni de radicación del exportador. Existen además las
  categorías `Extranjero`, `Indeterminado` y `Plataforma Continental`, excluidas de este dataset por
  no corresponder a Salta.
- **Valores FOB corrientes en dólares.** No se aplicó deflactor alguno; la comparación entre años es
  nominal.
- **2025 es año cerrado** (base anual publicada). Para actualizar a 2026 hay que volver a descargar
  el `.zip` del año correspondiente: el `.xlsb` histórico viaja dentro del paquete anual del último
  año disponible.
- La hoja `datos origen_2002-2011` no se leyó (fuera del período pedido). Se observó que allí los
  nombres de provincia vienen en mayúsculas sin acentos (`SALTA`) y desde 2012 en formato normal
  (`Salta`); si en el futuro se extiende la serie hacia atrás, hay que normalizar ese campo.
