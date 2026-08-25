# Metodología del build — Monitor de Indicadores CESS

Generado por `build.py`. Convierte los CSV tidy de los indicadores en JSON para el sitio.

## Formato numérico
Los CSV de origen (`Actualizar_*` / scripts) ya están en **formato inglés** (decimal `.`, sin separador de miles), UTF-8-sig. El build los lee como numéricos y **no** aplica conversión de separadores. Se verifica ausencia de saltos de orden de magnitud espurios por métrica.

## Transformaciones por tema
- **educacion**: normalización de nombres de departamento a Title Case con acentos; se excluyen `Enmascarado`/`Sin datos` de los rankings por departamento.
- **vitivinicultura**: sin transformación de valores (ya tidy).
- **produccion-energia**: `melt` de las 10 medidas físicas a `metrica`/`valor`; se descartan `iny_gas`, `iny_co2`, `vida_util` (todos 0 en Salta). La serie temporal se agrega por **trimestre** (suma de meses, por tipo de recurso); el ranking usa el total anual oficial.
- **empleo**: empleo por rubro/departamento y remuneración real, agregados por **trimestre** y por **año** (media de los meses del período). La remuneración es un **índice de salario real** deflactado por el **IPC NOA** (serie `145.3_INGNOANOA_DICI_M_10` de datos.gob.ar, base dic-2016), rebasado a **dic-2023 = 100** por serie; la provincial es media ponderada por empleo (Σ empleo·salario / Σ empleo). Se incluyen períodos parciales (2025); el KPI compara el último trimestre completo contra el mismo trimestre del año anterior.

## Fuentes externas materializadas
- `ipc_noa_mensual.csv` — IPC Nivel General región NOA (INDEC), vía `https://apis.datos.gob.ar/series/api/series?ids=145.3_INGNOANOA_DICI_M_10&format=csv`. Refrescar volviendo a descargar ese CSV.

## Incidencias detectadas
### produccion-energia
- produccion_energia: se descartan iny_gas, iny_co2 y vida_util (todos 0 en Salta).
- produccion_energia: serie temporal agregada por TRIMESTRE (suma de meses); el ranking y los KPIs usan el total anual oficial.
- prod_gas: 42 valor(es) a >1000× de la mediana (mediana=240.974); revisar posible artefacto de parseo.
### empleo
- empleo: remuneración expresada como ÍNDICE REAL (deflactado por IPC NOA, serie 145.3_INGNOANOA_DICI_M_10 de datos.gob.ar), base dic-2023 = 100 por serie.
- empleo: agregación TRIMESTRAL y ANUAL (media de los meses del período para empleo e índice real). Se incluyen períodos parciales (p. ej. 2025); el KPI compara el último trimestre completo contra el mismo trimestre del año anterior.
- empleo: la remuneración real provincial es media ponderada por empleo (Σ empleo·salario / Σ empleo); no se suman promedios entre rubros ni departamentos.
### turismo
- turismo: consolidado provincial de Salta (Ciudad de Salta + Cafayate) a partir de la EOH-INDEC; conteos sumados entre localidades y tasas (ocupación, estadía) recalculadas.
- turismo: agregación trimestral/anual por suma de los meses (conteos); la EOH termina en noviembre de 2025 (serie discontinuada).
- viajeros: 1 valor(es) a >1000× de la mediana (mediana=43624.5); revisar posible artefacto de parseo.
- pernoctaciones: 2 valor(es) a >1000× de la mediana (mediana=85928.5); revisar posible artefacto de parseo.
### agricultura
- agricultura: campañas 2018/19–2025/26 (MAGyP); el año indica el inicio de campaña.
- agricultura: 'Salta' es el total provincial (suma de departamentos); el rendimiento provincial se calcula como producción/superficie cosechada, no como promedio simple.
### gobierno
- gobierno: ejecución del gasto provincial (consolidado Adm. Central + Organismos Descentralizados), acumulada a diciembre; fuente presupuesto.salta.gob.ar.
- gobierno: 'objeto' usa los compromisos ejecutados; los pesos constantes se deflactan por el IPC NOA (promedio anual), base 2025.
- gasto_corr: 4 valor(es) a >1000× de la mediana (mediana=5.62828e+10); revisar posible artefacto de parseo.
- gasto_real: 4 valor(es) a >1000× de la mediana (mediana=2.20233e+11); revisar posible artefacto de parseo.
### resultado-fiscal
- resultado-fiscal: Esquema Ahorro-Inversión-Financiamiento (ejecución consolidada Adm. Central + Organismos Descentralizados, devengado), fuente presupuesto.salta.gob.ar. Resultado financiero = ingresos totales − gastos totales (VIII = XI en Salta).
- resultado-fiscal: el resultado primario es un cálculo propio (resultado financiero + intereses de la deuda), la fuente no publica una línea primaria. Reales deflactados por IPC NOA (base 2025).
- resultado-fiscal: el informe de diciembre es el cierre anual y reexpresa el resultado del año (el flujo mensual de diciembre incorpora ajustes de cierre); 2024-12 no fue publicado.
### recaudacion
- recaudacion: Impuesto a las Actividades Económicas (Ingresos Brutos), régimen CONVENIO MULTILATERAL únicamente (no incluye contribuyentes locales/directos); por sector de actividad (CIIU). Fuente: DGR / Ministerio de Economía de Salta.
- recaudacion: mensual desde 2021, sumada por trimestre/año; reales deflactados por IPC NOA (base 2025). No se emite el último período incompleto.
- recaud_corr: 60 valor(es) a >1000× de la mediana (mediana=2.50491e+08); revisar posible artefacto de parseo.
- recaud_real: 55 valor(es) a >1000× de la mediana (mediana=8.42204e+08); revisar posible artefacto de parseo.
### ganaderia
- ganaderia: existencias bovinas al 31/12 de cada año (MAGyP), 2012–2025; 'Salta' es el total provincial (suma de departamentos).
- stock_bovino: 30 valor(es) a >1000× de la mediana (mediana=1993); revisar posible artefacto de parseo.
### mineria
- mineria: el empleo minero es de Salta (registro mensual desde 2007, media de meses por trimestre/año). La recaudación tributaria es NACIONAL del sector (por empresa, 2019–2023), no atribuible a Salta; el total en USD se recalcula como suma de impuestos.
- recaud_ars: 26 valor(es) a >1000× de la mediana (mediana=297); revisar posible artefacto de parseo.
- recaud_usd: 17 valor(es) a >1000× de la mediana (mediana=2.909); revisar posible artefacto de parseo.
### financiero
- financiero: préstamos y depósitos al sector privado (BCRA, stock a fin de trimestre, miles de $); 'Salta' es el total provincial. Reales deflactados por IPC NOA (base 2025).
- financiero: inclusión financiera = puntos de acceso cada 10.000 adultos (promedio anual, suma de tipos); cobertura desde 2019.
### construccion
- construccion: permisos de edificación privada informados a INDEC por 5 municipios de Salta (mensual); los flujos se SUMAN por trimestre/año. La superficie es intención de construir, no obra ejecutada; 'Salta' suma los municipios.
### recursos-municipios
- recursos-municipios: transferencias a municipios de Salta (Contaduría Gral.), mensual desde 2021, sumadas por trimestre/año. Reales deflactados por IPC NOA (base 2025). Grupos: Coparticipación, Regalías, Canon, Fondo compensador, Otros.
- monto_corr: 276 valor(es) a >1000× de la mediana (mediana=1.86279e+07); revisar posible artefacto de parseo.
- monto_real: 243 valor(es) a >1000× de la mediana (mediana=7.55189e+07); revisar posible artefacto de parseo.
### energia-renovable
- energia-renovable: generación eléctrica de Salta (CAMMESA), MWh convertidos a GWh; los flujos se suman por trimestre/año. 'Renovable' = régimen Ley 27.191; la potencia instalada es una foto al último mes disponible.
### id-innovacion
- id-innovacion: inversión provincial en I+D (millones de $ corrientes y en pesos constantes de 2017) y personal en I+D por función; fuente RICyT/MINCyT. En términos reales la inversión se mantuvo casi estancada (678 en 2017 → 408 en 2024).

## Control (filas por tema)
- `educacion`: 11202 filas, cobertura 2011–2024.
- `vitivinicultura`: 132 filas, cobertura 2018–2025.
- `produccion-energia`: 2373 filas, cobertura 2018–2026.
- `empleo`: 4345 filas, cobertura 2019–2025.
- `turismo`: 738 filas, cobertura 2021–2025.
- `agricultura`: 2464 filas, cobertura campañas 2018/19–2024/25.
- `gobierno`: 170 filas, cobertura 2021–2025.
- `resultado-fiscal`: 1240 filas, cobertura 2021–2026.
- `recaudacion`: 3276 filas, cobertura 2021–2026.
- `ganaderia`: 3323 filas, cobertura 2012–2025.
- `mineria`: 3024 filas, cobertura 2007–2025.
- `financiero`: 868 filas, cobertura 2019–2026.
- `construccion`: 1682 filas, cobertura 2021–2026.
- `recursos-municipios`: 9814 filas, cobertura 2021–2026.
- `energia-renovable`: 233 filas, cobertura 2019–2026.
- `id-innovacion`: 54 filas, cobertura 2003–2024.
