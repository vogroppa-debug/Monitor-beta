# Metodología del build — Monitor de Indicadores CESS

Generado por `build.py`. Convierte los CSV tidy de los indicadores en JSON para el sitio.

## Formato numérico
Los CSV de origen (`Actualizar_*` / scripts) ya están en **formato inglés** (decimal `.`, sin separador de miles), UTF-8-sig. El build los lee como numéricos y **no** aplica conversión de separadores. Se verifica ausencia de saltos de orden de magnitud espurios por métrica.

## Transformaciones por tema
- **educacion**: normalización de nombres de departamento a Title Case con acentos; se excluyen `Enmascarado`/`Sin datos` de los rankings por departamento.
- **vitivinicultura**: sin transformación de valores (ya tidy).
- **produccion-energia**: `melt` de las 10 medidas físicas a `metrica`/`valor`; se descartan `iny_gas`, `iny_co2`, `vida_util` (todos 0 en Salta). La serie temporal se agrega por **trimestre** (suma de meses, por tipo de recurso); el ranking usa el total anual oficial.
- **empleo**: empleo por rubro/departamento y remuneración real, agregados por **trimestre** y por **año** (media de los meses del período). La remuneración es un **índice de salario real** deflactado por el **IPC NOA** (serie `145.3_INGNOANOA_DICI_M_10` de datos.gob.ar, base dic-2016), rebasado a **dic-2023 = 100** por serie; la provincial es media ponderada por empleo (Σ empleo·salario / Σ empleo). Se incluyen períodos parciales (2025); el KPI compara el último trimestre completo contra el mismo trimestre del año anterior.

## Números de ficha de la tabla de indicadores
Los códigos `I.1`…`V.4` de la Tabla de indicadores son los de las **notas técnicas de indicadores económico-productivos**, generadas desde `../notas-tecnicas-fuente/fichas.js`. Ese archivo vive **fuera del repo**, así que el código se carga a mano en el spec del indicador (`catalog.py`, y `EXTRA` en `indicadores.py`) y `qc_fichas()` lo verifica en cada build: aborta ante un código repetido o con el romano cambiado, y avisa acá abajo de los huecos. El número **ordena** la tabla dentro de cada subeje. En el eje sociocultural los códigos `I.1`…`IV.10` son los de las **Notas técnicas integradas de indicadores sociales** (Dimensiones I a IV, PDF en la carpeta de Drive de los xlsx); la numeración es propia de cada eje, así que el control de duplicados es por eje. Turismo, ambiente y los tableros sociales previos (educación por departamento, salud) no tienen ficha y muestran «—».

## Fuentes externas materializadas
- `ipc_noa_mensual.csv` — IPC Nivel General región NOA (INDEC), vía `https://apis.datos.gob.ar/series/api/series?ids=145.3_INGNOANOA_DICI_M_10&format=csv`. Refrescar volviendo a descargar ese CSV.
- **Base de los pesos constantes: julio de 2026** (último mes publicado de ese CSV). No es un año fijo: se recalcula en cada build, es la misma para todos los tableros y se mueve sola cuando se actualiza el IPC. Las variaciones porcentuales no dependen de la base; los niveles en pesos, sí. El índice de salario real (base dic-2023 = 100) y la inversión en I+D (pesos de 2017, ya deflactada por la fuente) NO usan esta base.

## Incidencias detectadas
### produccion-energia
- produccion_energia: se descartan iny_gas, iny_co2 y vida_util (todos 0 en Salta).
- produccion_energia: serie temporal agregada por TRIMESTRE (suma de meses); el ranking y los KPIs usan el total anual oficial.
- prod_gas: 32 valor(es) a >1000× de la mediana (mediana=432.893); revisar posible artefacto de parseo.
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
- gobierno: 'objeto' usa los compromisos ejecutados; el gasto es un flujo ANUAL, así que se deflacta por el IPC NOA promedio del año y se expresa en pesos de julio de 2026 (la base es el último mes publicado del IPC y se mueve con él).
- gobierno: gasto en personal e inversión real directa sobre gasto primario, y recursos tributarios de origen provincial sobre ingresos totales, del Esquema AIF de la DNAP (APNF, 2015–2025; 2024–2025 provisorios). NOA = suma de las seis provincias.
- gasto_corr: 4 valor(es) a >1000× de la mediana (mediana=5.62828e+10); revisar posible artefacto de parseo.
- gasto_real: 4 valor(es) a >1000× de la mediana (mediana=2.96965e+11); revisar posible artefacto de parseo.
### resultado-fiscal
- resultado-fiscal: Esquema Ahorro-Inversión-Financiamiento (ejecución consolidada Adm. Central + Organismos Descentralizados, devengado), fuente presupuesto.salta.gob.ar. Resultado financiero = ingresos totales − gastos totales (VIII = XI en Salta).
- resultado-fiscal: el resultado primario es un cálculo propio (resultado financiero + intereses de la deuda), la fuente no publica una línea primaria. Los reales se deflactan por el IPC NOA del mes y quedan en pesos de julio de 2026; la base es el último mes publicado del IPC y se mueve con él.
- resultado-fiscal: en la vista ACUMULADA el total enero-mes se deflacta por el índice del mes de cierre, no mes a mes. Sirve para comparar el mismo mes entre años, que es para lo que está el acumulado, pero no para comparar meses dentro de un año.
- resultado-fiscal: `pct_gprim` expresa el resultado financiero y el primario como % del GASTO PRIMARIO (gastos totales − intereses de la deuda). Es la medida de esfuerzo fiscal que no depende de la inflación ni del tamaño nominal del presupuesto. Al ser un cociente entre dos flujos del mismo período da idéntico en pesos corrientes y constantes, así que no se duplica por moneda. En el acumulado los meses NO son comparables entre sí (enero arranca alto y el ratio baja al avanzar el año): la comparación válida es contra el mismo mes del año anterior.
- resultado-fiscal: el informe de diciembre es el cierre anual y reexpresa el resultado del año (el flujo mensual de diciembre incorpora ajustes de cierre); 2024-12 no fue publicado.
- monto_real: 2 valor(es) a >1000× de la mediana (mediana=3.14336e+11); revisar posible artefacto de parseo.
### recaudacion
- recaudacion: Impuesto a las Actividades Económicas (Ingresos Brutos), régimen CONVENIO MULTILATERAL únicamente (no incluye contribuyentes locales/directos); por sector de actividad (CIIU). Fuente: DGR / Ministerio de Economía de Salta.
- recaudacion: mensual desde 2021, sumada por trimestre/año; cada mes se deflacta con el IPC NOA de ese mes y queda en pesos de julio de 2026 (la base es el último mes publicado del IPC y se mueve con él). No se emite el último período incompleto.
- recaud_corr: 60 valor(es) a >1000× de la mediana (mediana=2.50491e+08); revisar posible artefacto de parseo.
- recaud_real: 55 valor(es) a >1000× de la mediana (mediana=1.13564e+09); revisar posible artefacto de parseo.
### ganaderia
- ganaderia: existencias bovinas al 31/12 de cada año (MAGyP), 2012–2025; 'Salta' es el total provincial (suma de departamentos).
- stock_bovino: 30 valor(es) a >1000× de la mediana (mediana=1993); revisar posible artefacto de parseo.
### mineria
- mineria: el empleo minero es de Salta (registro mensual desde 2007, media de meses por trimestre/año). La recaudación tributaria es NACIONAL del sector (por empresa, 2019–2023), no atribuible a Salta; el total en USD se recalcula como suma de impuestos.
- recaud_ars: 26 valor(es) a >1000× de la mediana (mediana=297); revisar posible artefacto de parseo.
- recaud_usd: 17 valor(es) a >1000× de la mediana (mediana=2.909); revisar posible artefacto de parseo.
### financiero
- financiero: préstamos y depósitos al sector privado (BCRA, stock a fin de trimestre, miles de $); 'Salta' es el total provincial. Los reales se deflactan por el IPC NOA del ÚLTIMO MES DEL TRIMESTRE, porque el dato es un stock a esa fecha, y quedan en pesos de julio de 2026; la base es el último mes publicado del IPC y se mueve con él. El dato anual promedia los trimestres ya deflactados.
- financiero: inclusión financiera = puntos de acceso cada 10.000 adultos (promedio anual, suma de tipos); cobertura desde 2019.
- monto_corr tiene 108 período(s) sin su par monto_real (el IPC no llega a ese período); en modo Constantes no se dibujan.
### conectividad
- conectividad: ENACOM, accesos a internet fijo por provincia (trimestral desde 2015). La penetración por hogares se recalculó con proyecciones del Censo 2022, lo que baja los valores desde 2022; el salto de accesos de Salta entre 2025-T4 y 2026-T1 responde a cambios en la fuente.
- conectividad: la apertura por departamento parte de la tabla de ENACOM por localidad, que solo publica el último trimestre (serie desde 2026-T2, se acumula en cada actualización); la tasa usa hogares del Censo 2022 (no comparable estrictamente con la provincial de ENACOM).
### construccion
- construccion: permisos de edificación privada informados a INDEC por 5 municipios de Salta (mensual); los flujos se SUMAN por trimestre/año. La superficie es intención de construir, no obra ejecutada; 'Salta' suma los municipios.
### recursos-municipios
- recursos-municipios: transferencias a municipios de Salta (Contaduría Gral.), mensual desde 2021, sumadas por trimestre/año. Cada MES se deflacta con el IPC NOA de ese mes antes de sumar, y el resultado queda en pesos de julio de 2026; la base es el último mes publicado del IPC y se mueve con él. Grupos: Coparticipación, Regalías, Canon, Fondo compensador, Otros.
- monto_corr: 278 valor(es) a >1000× de la mediana (mediana=1.94172e+07); revisar posible artefacto de parseo.
- monto_real: 270 valor(es) a >1000× de la mediana (mediana=1.15985e+08); revisar posible artefacto de parseo.
### energia-renovable
- energia-renovable: generación eléctrica de Salta (CAMMESA), MWh convertidos a GWh; los flujos se suman por trimestre/año. 'Renovable' = régimen Ley 27.191; la potencia instalada es una foto al último mes disponible.
### bosques
- bosques: MapBiomas Argentina, Colección 3. El stock por clase sale de la planilla oficial por provincia; el desmonte y la regeneración, del producto de transiciones reducido por departamento en Earth Engine (la planilla sólo trae stock, y la resta entre años es cambio NETO, no desmonte).
- bosques: 2022-2025 son PROVISORIOS —el ráster aplica reglas de fin de serie a los últimos cuatro años y la colección siguiente los reescribe—. Los KPI y la tabla de indicadores se paran en 2021, el último año consolidado, fijando serie='Consolidada'; los gráficos muestran la serie completa con la franja final marcada.
- bosques: desmonte no es lo mismo que pérdida de bosque. `desmonte_bosque_ha` exige conversión a uso antrópico; `bosque_perdido_ha` incluye además el bosque que pasa a arbustal o pastizal (31.000-58.000 ha/año), donde se mezclan degradación, incendios y oscilación de la clasificación entre clases vecinas, que el producto no separa.
- bosques: 'regeneración' no es 'reforestación'. Es vegetación que vuelve sobre suelo que tuvo uso antrópico; no distingue restauración activa de abandono de lotes, y en los últimos años está subestimada por construcción (necesita años posteriores para confirmarse).
- bosques: los niveles no son comparables con Greenpeace ni con la UMSEF —para 2022 MapBiomas da 44.723 ha de desmonte y Greenpeace 15.230 ha, muy probablemente por la definición de bosque—. Usar una sola fuente y leer la tendencia, no el nivel.
- bosques: qc_saltos avisa sobre siete métricas, y en las siete los valores señalados están en el extremo BAJO, no en el alto: son los departamentos de puna —La Poma, Cachi, Molinos, Los Andes—, donde el bosque es marginal (La Poma, 119 ha en 1990, contra una mediana departamental de 122.082 ha). Es la escala real del territorio, no un separador decimal mal leído: los avisos son esperados.
- bosques: límites departamentales FAO GAUL 2025. Los Andes no tiene bosque en ningún año de la serie, así que queda fuera de los rankings y de la grilla.
- superficie_bosque_ha: 16 valor(es) a >1000× de la mediana (mediana=122082); revisar posible artefacto de parseo.
- desmonte_bosque_ha: 9 valor(es) a >1000× de la mediana (mediana=245.8); revisar posible artefacto de parseo.
- desmonte_bosque_primario_ha: 5 valor(es) a >1000× de la mediana (mediana=142.6); revisar posible artefacto de parseo.
- desmonte_bosque_secundario_ha: 8 valor(es) a >1000× de la mediana (mediana=112); revisar posible artefacto de parseo.
- regeneracion_bosque_ha: 17 valor(es) a >1000× de la mediana (mediana=261.3); revisar posible artefacto de parseo.
- bosque_perdido_ha: 1 valor(es) a >1000× de la mediana (mediana=1596.5); revisar posible artefacto de parseo.
- share_bosque_pct: 32 valor(es) a >1000× de la mediana (mediana=56.53); revisar posible artefacto de parseo.
### transparencia
- transparencia: mide PUBLICACIÓN ACTIVA en canales oficiales en línea, en una fecha. No mide cumplimiento de la ley de acceso a la información, ni la calidad o veracidad de lo publicado, ni lo que el Estado entrega a pedido. Un municipio que publica su presupuesto en papel o en el Concejo Deliberante puntúa 0.
- transparencia: el indicador del Monitor es el relevamiento propio del CESS, que apoya cada puntaje en una URL oficial que cualquiera puede abrir y separa 'no publica' de 'no se pudo verificar'. Lo relevó un asistente de IA con navegador, SIN segundo codificador humano: la metodología pide que una persona del CESS verifique las evidencias, sobre todo las de los 11 municipios con puntaje, antes de darlo por publicado.
- transparencia: efecto piso. Con 49 de 60 municipios en cero, el promedio provincial lo determinan los 11 que puntúan y un ranking de 60 barras sería engañoso. Las lecturas defendibles son el cumplimiento por criterio y el conteo de municipios sobre cero.
- transparencia: no hay retrospectiva posible. Los relevamientos propios de noviembre de 2026 son la línea de base, así que no hay variación interanual. Entre dos tomas, un puntaje puede cambiar porque el gobierno empezó a publicar o porque el relevador buscó mejor: la comparación honesta es criterio por criterio, con la evidencia a la vista.
- transparencia: la vara municipal le queda chica al nivel provincial. Criterios propios de una provincia —deuda, transferencias a municipios, presupuesto ciudadano— no se miden; se dejaron afuera para mantener la comparabilidad. El alcance es sólo el Poder Ejecutivo: Legislatura, Poder Judicial y Ministerio Público quedan fuera.
### energia-electrica
- energia-renovable: generación eléctrica de Salta (CAMMESA), MWh convertidos a GWh; los flujos se suman por trimestre/año. 'Renovable' = régimen Ley 27.191; la potencia instalada es una foto al último mes disponible.
### id-innovacion
- id-innovacion: inversión provincial en I+D (millones de $ corrientes y en pesos constantes de 2017) y personal en I+D por función; fuente RICyT/MINCyT. En términos reales la inversión se mantuvo casi estancada (678 en 2017 → 408 en 2024).
### exportaciones
- exportaciones: exportaciones de Salta por rubro y país de destino, base ANUAL del INDEC (COMEX, `Datos_origen_2002_2025.xlsb`, provincia de ORIGEN). Valor FOB en dólares CORRIENTES (sin deflactar) y peso neto. Metodología y controles en `datos-drive/Metodologia_Salta_exportaciones_INDEC_rubro_destino.md`.
- exportaciones: el secreto estadístico oculta el rubro fino de una parte creciente del valor exportado (2021: 33.5 %; 2022: 20.3 %; 2023: 21.1 %; 2024: 46.0 %; 2025: 43.4 %). Esas operaciones se muestran como categoría propia ('Confidencial (…)'), conservan país de destino y gran rubro, y NO se reparten entre los rubros identificados.
- exportaciones: `gran_rubro` y `continente` se derivan del primer dígito del código de rubro y de país del INDEC. El máximo detalle de producto con apertura provincial es el rubro; la posición arancelaria (NCM) sólo existe a nivel nacional.
- exportaciones: el control automático de saltos de magnitud marca valores a >1000× de la mediana. NO es un artefacto de parseo: la fuente es binaria (.xlsb leído con pyxlsb, sin separadores que interpretar) y la distribución del comercio es de cola muy larga (la mediana de una celda rubro×país ronda los 135.000 USD y la mayor supera los 380 M). Verificado además contra el total nacional del INDEC, con diferencia de 0,98 USD sobre 87.111 M.
- fob_usd: 113 valor(es) a >1000× de la mediana (mediana=134582); revisar posible artefacto de parseo.
- peso_ton: 97 valor(es) a >1000× de la mediana (mediana=129.085); revisar posible artefacto de parseo.
### salud
- salud: la apertura territorial de nacimientos es por ÁREA OPERATIVA de residencia (circunscripción sanitaria), no por departamento; el pasaje a departamento lo hace el script de datos-drive/Actualizar_Salud_Estadisticas_Vitales_Salta.md y es una aproximación. La suma de las 47 AO coincide exactamente con el total provincial en los cinco años.
- salud: el detalle departamental de internación existe sólo para 2025; la serie 2021–2025 de internación es provincial. Los cocientes por departamento (ocupación, permanencia, giro, mortalidad) se recalculan sobre los totales sumados de sus establecimientos, no se promedian.
- salud: las tres tablas provinciales del documento fuente se contradicen entre sí (defunciones 2021/2024/2025, nacidos vivos 2025). Se publica la Tabla 1 (Resumen Quinquenal), la única internamente consistente y la única que cierra contra la apertura territorial. El detalle está en datos-drive/Metodologia_Salud_Estadisticas_Vitales_Salta.md.
- salud: las tasas de mortalidad general de 2021 y 2022 no se reproducen con la población que publica el propio documento (la fuente usó proyecciones anteriores a las INDEC 2022–2040); se publican tal como las emitió el MSP.
- salud: 2025 es provisorio en toda la fuente.
### condiciones-vida
- condiciones-vida: privación material de los hogares según el Censo 2022 (INDEC/REDATAM), un solo corte por departamento; xlsx estático elaborado por el CESS (Dimensión I).
### salud-reproduccion
- salud-reproduccion: tasas medias anuales del trienio 2021-2023 (defunciones y nacimientos DEIS) sobre población del Censo 2022; se publican con anio=2023. Un solo corte por departamento; en departamentos chicos las tasas son inestables (pocos casos).
### educacion-aprendizajes
- educacion-aprendizajes: Relevamiento Anual 2025 (primaria y secundaria) y Aprender 2025 (6.º grado), por departamento; xlsx estático elaborado por el CESS (Dimensión III). Los departamentos sin dato confiable en Aprender (ND) se omiten.
### seguridad
- seguridad: suicidios del SATSSBU (2017-2024; tasas medias anuales, publicadas con anio=2024) y del trienio 2021-2023 (DEIS, anio=2023), sobre población del Censo 2022. La serie anual es sólo provincial: por departamento los casos por año son muy pocos.
- seguridad: mortalidad por lesiones de tránsito, tasa media anual 2021-2023 (DEIS), no ajustada por edad.
### seguridad-vial
- seguridad-vial: siniestralidad vial de la ANSV (Observatorio Vial Nacional), que consolida lo que le reporta cada jurisdicción; en Salta, la Subsecretaría de Seguridad Vial. Víctima fatal es la persona que fallece en el lugar o hasta 30 días después del siniestro. Los datos de 2023 en adelante son preliminares y la ANSV los sigue actualizando; las víctimas fatales de Buenos Aires y Mendoza llevan un factor de ajuste de 1,3.
- seguridad-vial: NO es lo mismo que la mortalidad por lesiones de tránsito del tema «Seguridad», que sale de la DEIS. La DEIS cuenta por causa de muerte en el certificado de defunción y la ANSV por siniestro reportado por la jurisdicción: dan números distintos para lo que se lee como lo mismo, y ninguno de los dos corrige al otro.
- seguridad-vial: la cobertura es desigual. La única serie sin huecos es víctimas fatales con su tasa de mortalidad (2016-2025). Los siniestros fatales no están abiertos por jurisdicción en 2025 y el tipo de usuario de la vía se corta en 2022: los informes preliminares posteriores sólo lo publican por región y en porcentaje. La tasa por vehículos es la que publica la ANSV, cada 10 mil vehículos registrados.
- seguridad-vial: el dato más reciente de la ANSV (enero-septiembre de 2026, sin CABA) está en el dataset pero fuera de los gráficos, porque es un acumulado parcial. En ese tramo Salta registra 93 víctimas fatales en 89 siniestros fatales.
- seguridad-vial: el total del país es el publicado por la ANSV, no la suma de las jurisdicciones. El NOA lo calcula el Monitor sumando Catamarca, Jujuy, La Rioja, Salta, Santiago del Estero y Tucumán —la agrupación de la propia ANSV—; sus tasas son cociente de agregados, no promedio de las tasas provinciales.
### aeropuerto
- aeropuerto: dos productos de la ANAC en un mismo tablero. Los aterrizajes (2019-) son sólo los arribos a Salta, abiertos por clasificación, clase de vuelo y aerolínea; la serie histórica (2001-) cuenta movimientos y pasajeros con otra definición y otro corte horario. No cierran entre sí y no se suman ni se empalman: ver `datos/metodologia/Metodologia_Salta_aeropuerto_ANAC.md`.
- aeropuerto: el ranking publica las 10 aerolíneas con más pasajeros y agrupa el resto en «Otras» (el dataset trae 239 explotadores, casi todos de aviación general). Las rutas se emiten en grano trimestral y anual.
- aeropuerto: el control automático de saltos de magnitud marca valores a >1000× de la mediana. NO es un artefacto de parseo: una misma métrica convive en varias aperturas, y la mediana cae sobre las categorías chicas (un vuelo escuela sin pasajeros, una ruta con doce pasajeros al año) mientras el total anual supera los 760.000. Verificado contra el CSV: el total coincide con la suma de cada apertura, al pasajero.
- pax_arribos: 32 valor(es) a >1000× de la mediana (mediana=2841.5); revisar posible artefacto de parseo.
- pax_serie: 32 valor(es) a >1000× de la mediana (mediana=49680); revisar posible artefacto de parseo.
- pax_ruta: 38 valor(es) a >1000× de la mediana (mediana=4267); revisar posible artefacto de parseo.
### supermercados
- supermercados: 1 mes sin IPC NOA publicado; el mes se descarta entero (2026-08).
- supermercados: Encuesta de Supermercados del INDEC, panel NO probabilístico de empresas con alguna boca de al menos 200 m² de salón de ventas. El propio INDEC advierte que las ventas «no se deben considerar aisladamente como un indicador macroeconómico del consumo». La cantidad de bocas no se publica: es el tamaño del panel, no el universo.
- supermercados: mensual desde 2017, sumado por trimestre/año; cada mes se deflacta con el IPC NOA de ese mes y queda en pesos de julio de 2026 (la base es el último mes publicado del IPC y se mueve con él). La participación en el país se recalcula en cada grano como cociente de los agregados, no promediando los meses.
- supermercados: el control automático de saltos de magnitud marca valores a >1000× de la mediana en las ventas corrientes. NO es un artefacto de parseo: la fuente es XLSX, con valores numéricos nativos, y la serie convive con 86× de inflación entre 2017 y 2026 y con el total del país al lado de Tierra del Fuego. Verificado contra el CSV: la suma de las jurisdicciones da el total del país.
- ventas_corr: 5 valor(es) a >1000× de la mediana (mediana=6.80686e+09); revisar posible artefacto de parseo.
### cemento
- cemento: despachos de la AFCP con DESTINO a cada jurisdicción; no es producción provincial. Bolsa y granel son envases, no usos: en el sector el granel se lee como obra grande y la bolsa como obra chica, pero esa lectura no es una definición de la fuente.
- cemento: la apertura por provincia está congelada en septiembre de 2025 (la AFCP publica despachos nacionales hasta octubre de 2026, sin detalle provincial). El total es el publicado, no «bolsa + granel»: la fuente redondea cada celda por separado y los dos difieren en hasta una tonelada.
### pdes-privacion
- pdes-privacion: CNPV 2010 y 2022, procesamiento de microdatos para el PDES 2030 (J. Paz). 2010 sale del cuestionario ampliado (muestra expandida, con error muestral en departamentos chicos); 2022, del censo completo.
- pdes-privacion: la NBI indígena cambia de pregunta entre censos (2010 por hogar, 2022 autorreconocimiento individual): la variación no es la de una misma población.
- pdes-privacion: las 8 regiones del PDES se aproximan con departamentos completos: Puna es sólo Los Andes y Yungas sólo Orán. Las regiones son sumas de conteos departamentales con el indicador recalculado, no promedios; los casos sin departamento entran sólo al total provincial.
### pdes-salud
- pdes-salud: estadísticas vitales de la DEIS por residencia, trienios 2018-2020 y 2021-2023 (el año del trienio se guarda como su último año: 2020 y 2023).
- pdes-salud: la TMI departamental es inestable en La Poma, Los Andes, Guachipas, La Caldera y Molinos aun agregando tres años; en Puna y Pre-Puna descansa en pocos casos.
- pdes-salud: la población de los denominadores son proyecciones del INDEC base 2010, que el propio INDEC recomienda usar con reservas para Salta.
- pdes-salud: las 8 regiones del PDES se aproximan con departamentos completos: Puna es sólo Los Andes y Yungas sólo Orán. Las regiones son sumas de conteos departamentales con el indicador recalculado, no promedios; los casos sin departamento entran sólo al total provincial.
### pdes-educacion
- pdes-educacion: Relevamiento Anual (educación común) y Aprender Matemática 6.º grado, 2018 y 2025 (DiNIEE). Primaria = 1.º a 7.º y secundaria = 8.º a 12.º y 13.º/14.º.
- pdes-educacion: la fuente enmascara las combinaciones sector × ámbito con pocos casos y esos casos entran sólo al total: la matrícula departamental está subestimada.
- pdes-educacion: Aprender compara dos cohortes distintas (no sigue a los mismos alumnos) y usa ponderadores; en Guachipas, La Poma y Cachi hay pocos evaluados.
- pdes-educacion: las 8 regiones del PDES se aproximan con departamentos completos: Puna es sólo Los Andes y Yungas sólo Orán. Las regiones son sumas de conteos departamentales con el indicador recalculado, no promedios; los casos sin departamento entran sólo al total provincial.
### pdes-trabajo
- pdes-trabajo: CNPV 2010 (cuestionario ampliado, con error muestral en departamentos chicos) y 2022 (censo completo), procesamiento de microdatos para el PDES 2030 (J. Paz).
- pdes-trabajo: la informalidad mide sólo la falta de protección contributiva (ocupados sin descuento ni aporte jubilatorio); la desocupación se lee junto con la actividad.
- pdes-trabajo: las 8 regiones del PDES se aproximan con departamentos completos: Puna es sólo Los Andes y Yungas sólo Orán. Las regiones son sumas de conteos departamentales con el indicador recalculado, no promedios; los casos sin departamento entran sólo al total provincial.
### pdes-delitos
- pdes-delitos: SNIC (Ministerio de Seguridad de la Nación), delitos REGISTRADOS por lugar del hecho, tasas anuales promedio por trienio (el año del trienio es su último año).
- pdes-delitos: las tasas bajas de Puna, Pre-Puna y Valles Calchaquíes pueden reflejar menos denuncias y menor presencia policial; el homicidio es el más comparable.
- pdes-delitos: las 8 regiones del PDES se aproximan con departamentos completos: Puna es sólo Los Andes y Yungas sólo Orán. Las regiones son sumas de conteos departamentales con el indicador recalculado, no promedios; los casos sin departamento entran sólo al total provincial.
### tabla de indicadores
- 58 indicadores todavía sin ficha en las notas técnicas (muestran «—» y van al final de su subeje): Personas en hogares con NBI (%), Personas en hogares sin agua de red pública (%), Personas indígenas en hogares con NBI (%), Nacidos vivos, Defunciones, Tasa de mortalidad infantil (c/ mil nacidos vivos), Tasa de natalidad (c/ mil hab.), Tasa de mortalidad general (c/ mil hab.), Tasa de mortalidad materna (c/ 10 mil nacidos vivos), Esperanza de vida al nacer (años). Mujeres, Esperanza de vida al nacer (años). Varones, Consultas médicas por habitante, Ocupación de camas en establecimientos públicos (%), Egresos hospitalarios, Camas disponibles (promedio), Matrícula total (alumnos), Egresados de secundaria (alumnos), Repitencia en primaria (%), Sobreedad en primaria (%), Sobreedad en secundaria (%), Aprender 6.º grado, Matemática: alumnos por debajo del nivel básico (%), Alumnos de 6.º que asistieron al jardín desde sala de 3 (%), Cargos docentes, Tasa de desocupación, 18 años y más (%), Informalidad laboral, ocupados de 18 a 64 años (%), Brecha de participación varones-mujeres, 18 a 64 años (p.p.), Tasa de actividad de mujeres, 18 a 64 años (%), Tasa de actividad de varones, 18 a 64 años (%), Víctimas de homicidio doloso (c/ 100 mil hab.), Robos y tentativas de robo (c/ 100 mil hab.), Lesiones dolosas (c/ 100 mil hab.), Abusos sexuales con acceso carnal (c/ 100 mil hab.), Víctimas fatales en siniestros viales (personas), Tasa de mortalidad vial (c/ 100 mil hab.), Víctimas fatales motociclistas (personas), Cemento despachado a Salta (toneladas), Cemento despachado a granel (toneladas), Ventas de supermercados (pesos constantes), Operaciones de compra en supermercados, Recursos tributarios propios (% de ingresos totales), Gasto en personal (% del gasto primario), Inversión real directa (% del gasto primario), Accesos a internet fijo cada 100 hogares, Accesos a internet fijo, Velocidad media de bajada (Mbps), Transparencia del Ejecutivo provincial (índice 0-100), Municipios con sitio web oficial (de 60), Superficie de bosque nativo (ha), Desmonte anual de bosque (ha), Regeneración de bosque (ha), Bosque sobre la superficie provincial (%), Participación renovable en la generación (%), Pasajeros arribados, Vuelos arribados, Ocupación de habitaciones (%), Viajeros, Pernoctaciones (noches), Estadía media (noches).
### clase de los indicadores
- 22 de 147 indicadores están clasificados como «De oferta o proceso»; los demás, como «De resultados» (`tipo` en el spec, ver catalog.py).
- De oferta o proceso — Sociocultural / Salud: Consultas médicas por habitante
- De oferta o proceso — Sociocultural / Salud: Ocupación de camas en establecimientos públicos (%)
- De oferta o proceso — Sociocultural / Salud: Egresos hospitalarios
- De oferta o proceso — Sociocultural / Salud: Camas disponibles (promedio)
- De oferta o proceso — Sociocultural / Educación: Alumnos por establecimiento. Secundaria
- De oferta o proceso — Sociocultural / Educación: Alumnos por cargo docente. Secundaria
- De oferta o proceso — Sociocultural / Educación: Cargos docentes
- De oferta o proceso — Económico-productivo / Actividad y productividad: Superficie sembrada (ha)
- De oferta o proceso — Económico-productivo / Actividad y productividad: Pozos en producción
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Gastos totales (pesos constantes, jul-2026)
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Gasto ejecutado total (pesos constantes, jul-2026)
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Gasto en personal (pesos constantes, jul-2026)
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Recursos a municipios (pesos constantes, jul-2026)
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Coparticipación a municipios (pesos constantes)
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Puntos de acceso al sistema financiero (c/ 10 mil adultos)
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Gasto en personal (% del gasto primario)
- De oferta o proceso — Económico-productivo / Inversión y financiamiento: Inversión real directa (% del gasto primario)
- De oferta o proceso — Económico-productivo / Infraestructura y logística: Potencia instalada (MW)
- De oferta o proceso — Económico-productivo / Infraestructura y logística: Velocidad media de bajada (Mbps)
- De oferta o proceso — Económico-productivo / Innovación y mercados: Inversión en I+D (millones de $ de 2017)
- De oferta o proceso — Económico-productivo / Innovación y mercados: Investigadores/as y becarios/as (personas)
- De oferta o proceso — Territorio, ambiente y turismo / Territorio: Municipios con sitio web oficial (de 60)

## Control (filas por tema)
- `educacion`: 11202 filas, cobertura 2011–2024.
- `vitivinicultura`: 178 filas, cobertura 2015–2025.
- `produccion-energia`: 3150 filas, cobertura 2018–2026.
- `empleo`: 4345 filas, cobertura 2019–2025.
- `turismo`: 738 filas, cobertura 2021–2025.
- `agricultura`: 3932 filas, cobertura campañas 2018/19–2024/25.
- `gobierno`: 269 filas, cobertura 2015–2025.
- `resultado-fiscal`: 1736 filas, cobertura 2021–2026.
- `recaudacion`: 3276 filas, cobertura 2021–2026.
- `ganaderia`: 3323 filas, cobertura 2012–2025.
- `mineria`: 3024 filas, cobertura 2007–2025.
- `financiero`: 1480 filas, cobertura 2019–2026.
- `conectividad`: 792 filas, cobertura 2015–2026.
- `construccion`: 1682 filas, cobertura 2021–2026.
- `recursos-municipios`: 10044 filas, cobertura 2021–2026.
- `energia-renovable`: 233 filas, cobertura 2019–2026.
- `bosques`: 8472 filas, cobertura 1985–2025 (consolidado hasta 2021).
- `transparencia`: 123 filas, cobertura Toma 2026 (municipios 04-11, provincia 07-11).
- `energia-electrica`: 233 filas, cobertura 2019–2026.
- `id-innovacion`: 54 filas, cobertura 2003–2024.
- `exportaciones`: 5306 filas, cobertura 2021–2025.
- `salud`: 652 filas, cobertura 2020–2025.
- `condiciones-vida`: 528 filas, cobertura 2022 (Censo).
- `salud-reproduccion`: 770 filas, cobertura 2021–2023 (trienio).
- `educacion-aprendizajes`: 748 filas, cobertura 2025.
- `seguridad`: 361 filas, cobertura 2017–2024.
- `seguridad-vial`: 2669 filas, cobertura 2016–2025.
- `aeropuerto`: 9170 filas, cobertura 2001–2026.
- `supermercados`: 16848 filas, cobertura 2017–2026.
- `cemento`: 15392 filas, cobertura 2017–2025.
- `pdes-privacion`: 288 filas, cobertura Censos 2010 y 2022.
- `pdes-salud`: 480 filas, cobertura Trienios 2018-2020 y 2021-2023.
- `pdes-educacion`: 2016 filas, cobertura 2018 y 2025.
- `pdes-trabajo`: 672 filas, cobertura Censos 2010 y 2022.
- `pdes-delitos`: 384 filas, cobertura Trienios 2013-2015 y 2021-2023.
