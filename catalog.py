# -*- coding: utf-8 -*-
"""
catalog.py — Metadatos y definición declarativa de tableros del Monitor CESS.

Cada tema declara: identidad + descripción en lenguaje llano + fuente + palabras
clave (para el buscador) + KPIs + gráficos. Los gráficos son especificaciones que
consume `assets/js/charts.js`; la agregación (filtrar / agrupar / sumar) ocurre en
el navegador para que los filtros sean interactivos.

Spec de gráfico:
  id, type: line | stacked-area | bar | barh | stacked-bar
  title, descr
  x:           dimensión del eje X (anio | periodo | departamento | ...)
  seriesBy:    dimensión que se abre en series (o None = una sola serie)
  metrica:     clave de métrica a graficar (valor donde metrica == esta)
  fixed:       {dim: valor} pre-filtro de igualdad
  controls:    [{dim, label, kind: select|year|metric|freq, all: bool, options:[...],
                 default: valor inicial, allValue/allLabel: qué aplica/muestra la opción "Todos"}]
               freq: opciones [{value,label,x,grano}] que definen el eje X y el `grano` a fijar
               (Trimestral/Anual); el front conmuta la agregación temporal.
  exclude:     valores a excluir del eje X (departamentos "Sin datos"/provincial)
  seriesExclude: valores de `seriesBy` a excluir de las series (p. ej. "Total")
  geoDim:      dimensión geográfica (departamento|unidad_geografica); habilita el
               selector de departamento y la vista de GRILLA (pequeños múltiplos)
  sort:        'desc' | 'asc' | None   (para barh)
  topN:        int (solo barh) - recorta el ranking a las primeras N categorias; sin esto se
               dibujan TODAS y el alto del grafico crece sin tope (p. ej. 146 paises)
  stack:       bool
  yMax:        tope fijo del eje Y (p. ej. 100 en distribuciones porcentuales apiladas)
  unidad:      etiqueta de unidad (si metrica es conmutable, la resuelve el front)
  seriesColor: {nombre de serie: color} - fija el color de esas series por encima de la paleta
               categórica, que reparte por posición alfabética. Para categorías con un color
               convencional (gris para áreas urbanas). El color puede ser una cadena o
               {"light": ..., "dark": ...} si hace falta distinguir por modo.
  provisorio_desde: int - sombrea el eje X desde ese valor con la etiqueta «provisorio».
               Para fuentes cuyos últimos períodos la propia fuente va a reescribir (MapBiomas
               aplica reglas de fin de serie a los últimos cuatro años). Es sólo la marca
               visual: la salvedad va además en `descr`, y parar un KPI en el último período
               firme se hace fijando una dimensión en `fixed` (ver abajo).
  fuente/fuente_url: fuente propia del gráfico (si difiere de la del tema)

Campo de tema opcional:
  advertencia: salvedad que condiciona la lectura del tablero, en un recuadro bajo el título.
       Para lo que el lector tiene que saber ANTES de mirar los gráficos (un dato sin
       verificación humana, una serie provisoria). El `resumen` largo no sirve para esto:
       `tema.html` muestra sólo `resumen_corto`, y el largo va a la tarjeta del buscador.

Campos de tema para la tabla maestra:
  subeje: subeje de la tabla de la portada. Si falta, se usa la etiqueta del PRIMER `tag`
          (válido en el eje económico-productivo, donde los subejes SON los tags).

Spec de KPI (el front muestra la VARIACIÓN INTERANUAL, no el valor absoluto):
  label, metrica, fixed, year('latest'|'latest_complete'|int), unidad, format
  OJO con `year`: NO sirve para parar un indicador en un período anterior al último. Ni
       `renderKpis` (charts.js) ni su espejo `_calcular` (indicadores.py) lo miran: los dos
       toman el último período con dato. Lo único que ambos respetan es `fixed`, así que un
       indicador que deba quedarse en un año firme necesita una dimensión propia en el
       adapter —`serie` en `bosques`— que el KPI fije y los gráficos no.
  tabla_label: nombre para la tabla maestra de la portada (si el `label` es ambiguo fuera
               de su tablero, p. ej. "Vacas" o "Pozos"); tabla_nota: aclaración al pie
  subeje: pisa el subeje del tema para ESTE indicador (temas que mezclan subejes)
  ficha: código de la ficha del indicador en las notas técnicas («III.5»): romano del
       subeje + correlativo. Se carga a mano porque la fuente del documento vive fuera
       del repo (`../notas-tecnicas-fuente/fichas.js`). ORDENA la tabla maestra dentro
       de cada subeje, así que la numeración se lee corrida. Los indicadores todavía sin
       ficha (sociales, turismo, ambiente) lo dejan vacío y van al final de su subeje.
  grafico: id del gráfico al que enlaza la tarjeta del indicador (por defecto, el primero
       que publica su métrica; hace falta cuando varios gráficos comparten métrica).
  tipo: 'resultado' (por defecto) | 'oferta'. Clase del indicador en la tabla de la portada, que
       dentro de cada subeje lista primero los «De resultados» y después los «De oferta o
       proceso». De oferta o proceso son los que miden recursos, capacidad instalada, insumos
       o la actividad de los establecimientos que prestan el servicio (camas, consultas,
       egresos, cargos docentes, gasto, potencia instalada); de resultados, lo que se obtiene
       con ellos o el estado de la población y de la economía (mortalidad, aprendizajes,
       producción, empleo). Sólo se declara en los de
       oferta; `BUILD_NOTES.md` los lista todos para que la clasificación se pueda revisar.
  var: 'anterior' -> la variación se calcula contra el período anterior CON DATO de la serie
       (2022 contra 2010, un trienio contra el anterior), no contra el mismo período del año
       anterior. Para series espaciadas: censos, trienios, relevamientos de años salteados.
       Va siempre junto con una `frecuencia` que diga qué compara («Intercensal», «Entre
       trienios»): la tabla de la portada no aclara la base y se deduce de esa columna. Lo
       aplican `indicadores._calcular` y `renderKpis` (charts.js).
  periodos: {"2023": "2021-23"} -> cómo se muestra cada período en la tabla y en la tarjeta,
       para las series que guardan un trienio con su último año como `anio`.
  (`frecuencia` también puede ir a nivel de TEMA: vale para todos sus indicadores.)
  frecuencia: pisa la columna "Frecuencia" de la tabla maestra, que si no se deduce de la serie.
       Para un dato de una sola toma ("Toma única"), donde el valor deducido sería "Anual" y
       sugeriría una serie que no existe.
  display: 'nivel' -> muestra el NIVEL en vez de la variación. Pensado para magnitudes con
       signo (resultado fiscal: superávit verde / déficit rojo).
  sentido: 'mayor_mejor' (por defecto) | 'menor_mejor' | 'neutro'
       De qué color se pinta la variación. Por defecto subir es verde y bajar rojo, que es lo
       correcto para producción, empleo o recaudación pero se lee al revés en defunciones o
       tasas de mortalidad ('menor_mejor'), y no significa nada en indicadores de dos filos
       como consultas por habitante u ocupación de camas ('neutro', se muestra sin color).
       La FLECHA siempre marca la dirección real del cambio: esto sólo elige el color. En un
       KPI con display 'nivel', declarar `sentido` además cambia el criterio de color del
       signo del valor a la dirección del cambio (una tasa nunca es negativa, así que su
       signo no informa nada). Lo consumen `kpiClaseColor` (charts.js) e `indicadores.py`.
  geo / geo_nota: pisan la desagregación territorial que la tabla maestra calcula sola.
       Por defecto el nivel sale de las FILAS de la métrica (la apertura más fina con más de
       un valor territorial); sólo hace falta declararlo cuando la apertura del concepto vive
       en una métrica hermana, como `nacidos_vivos` / `nacidos_vivos_res` en salud.
  meta_2030_nota: aclaración al pie de la celda de meta (p. ej. cuando el PDES fija la
       cobertura y el Monitor mide la carencia, y hay que invertir el sentido)
  base_valor / base_periodo: línea de base del PDES y el período al que corresponde
  meta_2030 / meta_2040 / meta_2050: metas del PDES 2050 en los tres cortes
       Cargar `base_valor` y las metas como NÚMEROS, no como texto ya formateado: la tabla
       maestra los formatea sola y necesita operar con ellos para calcular la brecha a 2050
       (= meta_2050 − último dato observado). Van en la MISMA unidad que la métrica.
       Vacías hasta que el PDES las defina; entonces la brecha aparece sola.
       CUIDADO con las métricas en PESOS CONSTANTES (`gasto_real`, `monto_real`, `recaud_real`):
       la base se mueve con el IPC, así que una meta cargada hoy en pesos de un mes quedaría
       desfasada en el próximo build. Para esas métricas, la meta hay que expresarla en términos
       reales relativos (variación, % del gasto) o rebasarla junto con la serie.
  cmp: 'quarter' -> último trimestre completo vs mismo trimestre del año anterior
       (por defecto, año vs año). (`agg` de la métrica sale de metricas[...]: 'sum'|'mean')
"""

AREAS = {
    "economico":    {"label": "Económico-Productivo", "orden": 1},
    "energia":      {"label": "Energía",              "orden": 2},
    "social":       {"label": "Social",               "orden": 3},
    "agropecuario": {"label": "Agropecuario",         "orden": 4},
    "mineria":      {"label": "Minería",              "orden": 5},
    "turismo":      {"label": "Turismo",              "orden": 6},
    "fiscal":       {"label": "Finanzas públicas",    "orden": 7},
    "financiero":   {"label": "Financiero",           "orden": 8},
    "ambiente":     {"label": "Ambiente y energía",   "orden": 9},
    "construccion": {"label": "Construcción",          "orden": 10},
    "ciencia":      {"label": "Ciencia y tecnología",  "orden": 11},
    "institucional": {"label": "Gestión pública",        "orden": 12},
}

# Ejes transversales de desarrollo productivo. Un tema puede tener varios (campo
# `tags`). Son la agrupación principal del menú y la portada; el `area` queda como
# chip de color. Se definen los 5 aunque algún eje aún no tenga temas (fase 2).
# `num` es el romano con que las notas técnicas numeran el subeje: la primera mitad del
# código de ficha de sus indicadores (`III.5`). El build lo usa para verificar que el
# romano de cada ficha coincida con el subeje en el que la fila efectivamente cae.
TAGS = {
    "actividad-productividad":   {"label": "Actividad, estructura productiva y productividad",       "orden": 1, "num": "I",
                                  "corto": "Actividad y productividad",
                                  "descr": "Qué y cuánto se produce en Salta, y con qué productividad."},
    "empleo-capacidades":        {"label": "Empleo y capacidades productivas",                       "orden": 2, "num": "II",
                                  "corto": "Empleo y capacidades",
                                  "descr": "Trabajo registrado, remuneraciones y formación del capital humano."},
    "inversion-financiamiento":  {"label": "Inversión y financiamiento",                             "orden": 3, "num": "III",
                                  "corto": "Inversión y financiamiento",
                                  "descr": "Recursos que financian la actividad y la inversión productiva."},
    "infraestructura-logistica": {"label": "Infraestructura, logística y condiciones para producir", "orden": 4, "num": "IV",
                                  "corto": "Infraestructura y logística",
                                  "descr": "Energía, transporte y servicios que habilitan la producción."},
    "innovacion-mercados":       {"label": "Innovación e inserción en mercados",                     "orden": 5, "num": "V",
                                  "corto": "Innovación y mercados",
                                  "descr": "Exportaciones, diversificación y llegada a nuevos mercados."},
}

# Subejes de la tabla maestra de indicadores. En el eje económico-productivo son los TAGS de
# arriba (se toma el primero del tema); los otros dos ejes usan una taxonomía temática propia,
# declarada tema por tema con el campo `subeje`. El número es solo el orden de aparición.
# Columnas de línea de base, metas 2030/2040/2050 y brecha a 2050 en la tabla de la portada.
# En False se ocultan: las metas del PDES todavía no están definidas y en una presentación una
# docena de columnas vacías distrae. El cálculo sigue intacto en `indicadores.py` y los campos
# `base_valor` / `meta_2030` / ... siguen siendo válidos en el spec de KPI, así que volver a
# mostrarlas es cambiar esto a True y reconstruir.
MOSTRAR_METAS = False

# La meta 2030 vuelve SOLA, sin el resto del bloque de metas: es la única con datos cargados.
# El título lleva la fuente porque existe otra versión del plan (PDES 2018) cuyas metas no
# coinciden con esta —en stock bovino, por ejemplo, fija 3.000.000 en vez de 2.000.000—.
# Fuente: `sectores, objetivos y metas 2024.xlsx`. De sus 64 filas, 27 traen meta 2030 y sólo
# 7 tienen un indicador equivalente en el Monitor: el resto del PDES no quedó cuantificado, o
# mide cosas que el Monitor no publica.
MOSTRAR_META_2030 = True

# Columna «Línea de base» de la tabla de la portada, antes de la meta 2030. La base es el dato del
# año BASE_ANIO, en el MISMO período del año que el último dato: si el último es 2T2026 la base es
# 2T2024; si es mar-2026, mar-2024; si es anual, el año entero. Así base y último dato son
# comparables (un total anual contra un trimestre sería cuatro veces más grande). Sin dato en ese
# período —series que terminan antes, o la serie consolidada de bosques, que se para en 2021—
# queda vacía. Un `base_valor` escrito a mano en el spec manda sobre el cálculo. Es también la
# base que usa el semáforo. (El bloque de MOSTRAR_METAS trae su propia columna de base: no
# prender los dos a la vez.)
MOSTRAR_LINEA_BASE = True
BASE_ANIO = 2024

# Columna CIIU (sección de actividad) en la tabla del eje económico-productivo. Oculta por pedido;
# la letra se sigue cargando y se sigue usando para ORDENAR los indicadores dentro de cada subeje,
# así que volver a mostrarla es cambiar esto a True y reconstruir.
MOSTRAR_CIIU = False
META_2030_TITULO = "Meta 2030 (PDES 2024)"

# Fuentes de las planillas del PDES 2030 (J. Paz, 2026). Van como constantes porque las usan los
# tableros y la tabla de formas cortas.
PDES_FUENTE_CENSO = ("Censos Nacionales de Población, Hogares y Viviendas 2010 y 2022 (INDEC), "
                     "procesamiento de microdatos para el PDES 2030 (J. Paz)")
PDES_FUENTE_SALUD = ("Estadísticas vitales (DEIS, Ministerio de Salud de la Nación), trienios "
                     "2018-2020 y 2021-2023, procesadas para el PDES 2030 (J. Paz)")
PDES_FUENTE_EDUCACION = ("Relevamiento Anual y Aprender 2018 y 2025 (DiNIEE, Ministerio de Capital "
                         "Humano), procesados para el PDES 2030 (J. Paz)")
PDES_FUENTE_SNIC = ("Sistema Nacional de Información Criminal (SNIC, Ministerio de Seguridad de la "
                    "Nación), trienios 2013-2015 y 2021-2023, procesado para el PDES 2030 (J. Paz)")

# Forma corta de cada fuente para la columna «Fuente» de la tabla de la portada. La clave es el
# texto COMPLETO de la fuente tal como lo declara el tema (o el gráfico, cuando tiene una propia);
# la celda muestra la forma corta y el texto completo aparece al pasar el mouse; si el valor es un
# par (forma corta, texto del mouse), el mouse muestra ese texto en vez de la fuente completa.
# Una fuente nueva
# sin forma corta se muestra completa y queda anotada en BUILD_NOTES.md para agregarla acá.
FUENTE_CORTA = {
    "CESS sobre la base del Censo Nacional de Población, Hogares y Viviendas 2022 (INDEC/REDATAM)":
        "CNPV 2022",
    "CESS sobre la base de defunciones y nacimientos 2021-2023 (DEIS, Ministerio de Salud) y "
    "Censo 2022 (INDEC)": "DEIS e INDEC",
    "Programa de Estadísticas de Información en Salud — Ministerio de Salud Pública de Salta":
        "Salud Salta",
    "CESS sobre la base del Relevamiento Anual 2025 y Aprender 2025 (Ministerio de Educación de "
    "la Nación)": "Educación Nación",
    "Relevamiento Anual (RA) — Ministerio de Educación de la Nación":
        "Educación Nación",
    "CESS sobre la base del Sistema de Alerta Temprana de Suicidios (SATSSBU, suicidios "
    "2017-2024), DEIS (defunciones 2021-2023) y Censo 2022 (INDEC)": "Alerta Suicidios y DEIS",
    "Estimaciones Agrícolas — Ministerio de Economía (MAGyP)": "MAGyP",
    "Existencias bovinas (SENASA) — Ministerio de Economía (MAGyP)": "SENASA y MAGyP",
    "Instituto Nacional de Vitivinicultura (INV)": "INV",
    "Secretaría de Energía de la Nación — datos abiertos (producción por pozo)":
        "Sec. de Energía",
    "Permisos de edificación — INDEC": "INDEC",
    "OEDE — Observatorio de Empleo y Dinámica Empresarial (Min. de Trabajo / Capital Humano)":
        "OEDE",
    "OEDE (empleo y remuneraciones) e IPC NOA — INDEC (deflactor), vía datos.gob.ar":
        "OEDE e INDEC",
    "Empleo: OEDE (Min. de Trabajo). Recaudación: Secretaría de Minería de la Nación":
        "OEDE y Minería",
    "Secretaría de Minería de la Nación (aporte tributario del sector, nacional)":
        "Sec. Minería",
    "Esquema Ahorro-Inversión-Financiamiento — Presupuesto de la Provincia de Salta":
        "Ppto. Salta",
    "Dirección General de Rentas — Ministerio de Economía de Salta": "DGR Salta",
    "Banco Central de la República Argentina (BCRA)": "BCRA",
    "Esquema Ahorro-Inversión-Financiamiento provincial — DNAP, Ministerio de Economía de la "
    "Nación": "DNAP",
    "Ejecución presupuestaria — Ministerio de Economía de Salta": "Economía Salta",
    # Con texto propio para el mouse: el pedido fue «Contaduría Gral de la Pvcia», no la fuente
    # completa del tema.
    "Contaduría General de la Provincia de Salta": ("CGP", "Contaduría Gral. de la Pvcia."),
    "CAMMESA — Informe de síntesis mensual": "CAMMESA",
    "ENACOM (datos abiertos de internet) e INDEC (Censo 2022, hogares)": "ENACOM e INDEC",
    "INDEC — Comercio Exterior (COMEX), base anual por provincia de origen": "INDEC, COMEX",
    "RICyT / MINCyT — Indicadores de ciencia y tecnología": "RICyT / MINCyT",
    "Relevamiento propio del CESS sobre canales oficiales (municipios y Ejecutivo provincial)":
        "Elab. propia",
    "MapBiomas Argentina — Colección 3 (cobertura y uso; desmonte y vegetación secundaria)":
        "MapBiomas",
    "Encuesta de Ocupación Hotelera (EOH) — INDEC": "INDEC, EOH",
    PDES_FUENTE_CENSO: "CNPV 2010-2022",
    PDES_FUENTE_SALUD: "DEIS",
    PDES_FUENTE_EDUCACION: "RA y Aprender",
    PDES_FUENTE_SNIC: "SNIC",
    "Administración Nacional de Aviación Civil (ANAC)": "ANAC",
    "Asociación de Fabricantes de Cemento Portland (AFCP)": "Asoc. Fab. Cemento",
    "Agencia Nacional de Seguridad Vial (ANSV)": "ANSV",
    "Dirección Nacional de los Registros Nacionales de la Propiedad del Automotor (DNRPA)": "DNRPA",
    "Encuesta de Supermercados — INDEC": "INDEC",
}

# Semáforo de avance hacia la meta 2030 (sección de la portada + marca en la columna de la meta).
# El avance es la parte recorrida del camino entre la línea de base y la meta:
#     avance = (último dato − línea de base) / (meta 2030 − línea de base)
# y sólo se calcula cuando el indicador tiene las tres cosas (`base_valor` y `meta_2030` en su
# spec, y un dato publicado). Lo que no se puede calcular queda en gris, CONTADO y con su
# motivo: es un esqueleto, y que se vea cuánto falta cargar es parte de lo que muestra.
# La regla completa está en `indicadores._avance`.
MOSTRAR_SEMAFORO = True
SEMAFORO_UMBRALES = {"verde": 90, "amarillo": 70}   # % de avance: >= verde, >= amarillo, resto rojo
SEMAFORO_TOP = 5                                    # largo de «Mejores desempeños» / «Mayores rezagos»

SUBEJE_ORDEN = {
    # sociocultural
    "Condiciones de vida": 1, "Salud": 2, "Educación": 3, "Trabajo": 4, "Seguridad": 5,
    # territorio, ambiente y turismo (Territorio todavía sin temas)
    "Territorio": 1, "Ambiente": 2, "Turismo": 3,
}
# Romano de cada subeje sociocultural en las Notas técnicas integradas de indicadores sociales
# (Dimensiones I a IV). Cumple el papel del `num` de TAGS para el control de fichas.
SUBEJE_NUM = {"Condiciones de vida": "I", "Salud": "II", "Educación": "III", "Seguridad": "IV"}

# Secciones de actividad económica (nomenclador CLANAE/CIIU rev.4). Se muestran como letra
# con tooltip en la Tabla de indicadores del eje económico-productivo. Un indicador declara
# su letra con `ciiu` a nivel de tema (por defecto para todos sus KPIs) o de KPI (override,
# cuando un tema mezcla sectores, p. ej. uva=A vs. vino=C). Sólo se marcan los casos claros.
CIIU_SECCIONES = {
    "A": "Agricultura, ganadería, caza, silvicultura y pesca",
    "B": "Explotación de minas y canteras",
    "C": "Industria manufacturera",
    "D": "Suministro de electricidad, gas, vapor y aire acondicionado",
    "E": "Suministro de agua, cloacas, gestión de residuos, recuperación de materiales y saneamiento público",
    "F": "Construcción",
    "G": "Comercio al por mayor y al por menor; reparación de vehículos automotores y motocicletas",
    "H": "Servicios de transporte y almacenamiento",
    "I": "Servicios de alojamiento y servicios de comida",
    "J": "Información y comunicaciones",
    "K": "Intermediación financiera y servicios de seguros",
    "L": "Servicios inmobiliarios",
    "M": "Servicios profesionales, científicos y técnicos",
    "N": "Actividades administrativas y servicios de apoyo",
    "O": "Administración pública, defensa y seguridad social obligatoria",
    "P": "Enseñanza",
    "Q": "Salud humana y servicios sociales",
    "R": "Servicios artísticos, culturales, deportivos y de esparcimiento",
    "S": "Servicios de asociaciones y servicios personales",
    "T": "Servicios de hogares privados que contratan servicio doméstico",
    "U": "Servicios de organizaciones y órganos extraterritoriales",
}

SITE = {
    "nombre": "Monitor de Indicadores (versión Beta)",
    "subtitulo": "Seguimiento del Plan de Desarrollo Estratégico de Salta (PDES 2030)",
    "institucion": "Consejo Económico y Social de Salta (CESS)",
}

# Ejes estratégicos del PDES 2050 (nivel superior de agrupación en la portada y el menú).
# Dentro de cada eje del PDES, los temas se subagrupan por los TAGS transversales de arriba.
EJES_PDES = {
    "sociocultural":               {"label": "Sociocultural",                  "orden": 1,
                                    "descr": "Educación, salud, trabajo y condiciones de vida de la población."},
    "economico-productivo":        {"label": "Económico-productivo",           "orden": 2,
                                    "descr": "Producción, empleo, inversión y financiamiento de la economía salteña."},
    "territorio-ambiente-turismo": {"label": "Territorio, ambiente y turismo",  "orden": 3,
                                    "descr": "Uso del territorio, energía y ambiente, y actividad turística."},
}

TEMAS = [
    # ======================================================================
    {
        "id": "educacion",
        "subeje": "Educación",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Educación por departamento",
        "resumen": (
            "Cuántos alumnos, docentes y egresados hay en el sistema educativo de Salta, "
            "abierto por departamento, nivel (inicial, primaria, secundaria), sector de "
            "gestión (estatal/privado) y ámbito (urbano/rural), entre 2011 y 2024."
        ),
        "resumen_corto": "Alumnos, docentes y egresados del sistema educativo, por departamento.",
        "fuente": "Relevamiento Anual (RA) — Ministerio de Educación de la Nación",
        "fuente_url": "https://www.argentina.gob.ar/educacion/evaluacion-informacion-educativa",
        "cobertura": "2011–2024",
        "keywords": [
            "educación", "escuelas", "matrícula", "alumnos", "estudiantes", "docentes",
            "cargos", "repitencia", "repitentes", "egresados", "primaria", "secundaria",
            "inicial", "nivel educativo", "sobreedad", "deserción", "extranjeros",
            "sector estatal", "sector privado", "urbano", "rural",
        ],
        "tags": ["empleo-capacidades"],
        "kpis": [
            {"label": "Matrícula total", "metrica": "matricula", "fixed": {}, "year": "latest",
             "unidad": "alumnos", "format": "int"},
            {"label": "Egresados de secundaria", "metrica": "egresados",
             "fixed": {"nivel": "secundaria"}, "year": "latest", "unidad": "alumnos", "format": "int"},
            {"tipo": "oferta", "label": "Cargos docentes", "metrica": "cargos", "fixed": {}, "year": "latest",
             "unidad": "cargos", "format": "int"},
        ],
        "charts": [
            {"id": "edu-matricula-nivel", "type": "line",
             "title": "Evolución de la matrícula por nivel",
             "descr": "Alumnos matriculados cada año, según el nivel educativo.",
             "x": "anio", "seriesBy": "nivel", "metrica": "matricula", "fixed": {}, "geoDim": "departamento",
             "controls": [{"dim": "departamento", "label": "Departamento", "kind": "select", "all": True}],
             "unidad": "alumnos"},
            {"id": "edu-ranking-depto", "type": "barh",
             "title": "Matrícula por departamento",
             "descr": "Ranking de departamentos por cantidad de alumnos, para el año y el nivel seleccionados.",
             "x": "departamento", "seriesBy": None, "metrica": "matricula", "fixed": {},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"dim": "nivel", "label": "Nivel", "kind": "select", "all": True},
             ],
             "sort": "desc", "unidad": "alumnos"},
            {"id": "edu-sector", "type": "stacked-area",
             "title": "Matrícula por sector de gestión",
             "descr": "Cómo se reparte la matrícula entre gestión estatal y privada a lo largo del tiempo.",
             "x": "anio", "seriesBy": "sector", "metrica": "matricula", "fixed": {}, "stack": True,
             "geoDim": "departamento",
             "controls": [
                 {"dim": "nivel", "label": "Nivel", "kind": "select", "all": True},
                 {"dim": "departamento", "label": "Departamento", "kind": "select", "all": True},
             ],
             "unidad": "alumnos"},
        ],
    },
    # ======================================================================
    {
        "id": "vitivinicultura",
        "area": "economico",
        "eje_pdes": "economico-productivo",
        "title": "Vitivinicultura (INV)",
        "resumen": (
            "La cadena del vino en Salta: producción de uva y elaboración de vino y mosto por "
            "departamento de los Valles Calchaquíes, despachos al mercado interno y exportaciones "
            "de la provincia, desde 2015 (mercado interno desde 2016)."
        ),
        "resumen_corto": "La cadena del vino en Salta: uva, elaboración y exportaciones.",
        "fuente": "Instituto Nacional de Vitivinicultura (INV)",
        "fuente_url": "https://www.argentina.gob.ar/inv/vinos/estadisticas",
        "cobertura": "2015–2025",
        "keywords": [
            "vino", "vid", "uva", "bodegas", "vitivinicultura", "INV", "cosecha", "elaboración",
            "mosto", "exportaciones", "Cafayate", "Cachi", "Molinos", "San Carlos",
            "Valles Calchaquíes", "mercado interno", "hectolitros", "quintales", "vendimia",
        ],
        "tags": ["actividad-productividad", "innovacion-mercados"],
        "kpis": [
            {"ficha": "I.6", "label": "Producción de uva", "metrica": "produccion_uva", "ciiu": "A",
             "fixed": {"categoria": "cosecha_elaboracion"}, "year": "latest", "unidad": "quintales", "format": "int"},
            {"ficha": "I.7", "label": "Elaboración de vino y mosto", "metrica": "elaboracion_total", "ciiu": "C",
             "fixed": {"categoria": "cosecha_elaboracion"}, "year": "latest", "unidad": "hectolitros", "format": "int"},
            {"ficha": "I.8", "label": "Exportaciones (valor FOB)", "tabla_label": "Exportaciones de vino, valor FOB (miles US$)",
             "metrica": "export_valor_fob",
             "fixed": {"categoria": "mercado_externo"}, "year": "latest", "unidad": "miles US$", "format": "int"},
        ],
        "charts": [
            {"id": "inv-uva-depto", "type": "stacked-area",
             "title": "Producción de uva por departamento",
             "descr": "Quintales de uva cosechada, apilados por departamento de los Valles Calchaquíes.",
             "x": "anio", "seriesBy": "unidad_geografica", "metrica": "produccion_uva",
             "fixed": {"categoria": "cosecha_elaboracion", "nivel": "departamento"}, "stack": True,
             "geoDim": "unidad_geografica",
             "controls": [], "unidad": "quintales"},
            {"id": "inv-elaboracion-depto", "type": "stacked-area",
             "title": "Elaboración de vino y mosto por departamento",
             "descr": "Hectolitros elaborados por departamento.",
             "x": "anio", "seriesBy": "unidad_geografica", "metrica": "elaboracion_total",
             "fixed": {"categoria": "cosecha_elaboracion", "nivel": "departamento"}, "stack": True,
             "geoDim": "unidad_geografica",
             "controls": [], "unidad": "hectolitros"},
            {"id": "inv-exportaciones", "type": "line",
             "title": "Exportaciones de vino de Salta",
             "descr": "Exportaciones provinciales de vino, en valor (miles de US$) o volumen (hectolitros).",
             "x": "anio", "seriesBy": None, "metrica": "export_valor_fob",
             "fixed": {"categoria": "mercado_externo", "nivel": "provincia"},
             "controls": [{"kind": "metric", "label": "Medida",
                           "options": ["export_valor_fob", "export_volumen"]}],
             "unidad": "miles US$"},
        ],
    },
    # ======================================================================
    {
        "id": "produccion-energia",
        "ciiu": "B",
        "area": "energia",
        "eje_pdes": "economico-productivo",
        "title": "Producción de petróleo y gas",
        "resumen": (
            "Producción de hidrocarburos en Salta a partir de los pozos declarados a la Secretaría "
            "de Energía: evolución mensual de gas y petróleo (convencional y no convencional) y "
            "distribución por departamento, desde 2018."
        ),
        "resumen_corto": "Producción de petróleo y gas por departamento y en el tiempo.",
        "fuente": "Secretaría de Energía de la Nación — datos abiertos (producción por pozo)",
        "fuente_url": "http://datos.energia.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo",
        "cobertura": "2018–2026",
        "keywords": [
            "petróleo", "gas", "hidrocarburos", "energía", "pozos", "producción", "extracción",
            "convencional", "no convencional", "Rivadavia", "San Martín", "Orán", "regalías",
            "combustibles", "yacimientos", "shale",
        ],
        "tags": ["actividad-productividad", "infraestructura-logistica"],
        "kpis": [
            {"ficha": "I.10", "label": "Producción de gas", "metrica": "prod_gas", "fixed": {"grano": "anual"},
             "year": "latest_complete", "unidad": "miles de m³", "format": "int"},
            {"ficha": "I.11", "label": "Producción de petróleo", "metrica": "prod_pet", "fixed": {"grano": "anual"},
             "year": "latest_complete", "unidad": "m³", "format": "int"},
            {"tipo": "oferta", "ficha": "I.12", "label": "Pozos", "tabla_label": "Pozos en producción", "metrica": "pozos", "fixed": {"grano": "anual"},
             "year": "latest_complete", "unidad": "pozos", "format": "int"},
        ],
        "charts": [
            {"id": "prod-gas-mensual", "type": "stacked-area",
             "title": "Producción de gas",
             "descr": "Miles de m³ de gas por trimestre, apilados según el tipo de recurso.",
             "x": "trimestre", "seriesBy": "tipo_de_recurso", "metrica": "prod_gas",
             "fixed": {}, "stack": True, "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select", "all": True},
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "trimestral"}]},
             ],
             "unidad": "miles de m³"},
            {"id": "prod-pet-mensual", "type": "stacked-area",
             "title": "Producción de petróleo",
             "descr": "m³ de petróleo por trimestre, apilados según el tipo de recurso.",
             "x": "trimestre", "seriesBy": "tipo_de_recurso", "metrica": "prod_pet",
             "fixed": {}, "stack": True, "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select", "all": True},
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "trimestral"}]},
             ],
             "unidad": "m³"},
            {"id": "prod-ranking-depto", "type": "barh",
             "title": "Producción por departamento",
             "descr": "Ranking de departamentos productores de gas o petróleo, para el año seleccionado.",
             "x": "departamento", "seriesBy": None, "metrica": "prod_gas", "fixed": {"grano": "anual"},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "metric", "label": "Recurso", "options": ["prod_gas", "prod_pet"]},
             ],
             "sort": "desc", "unidad": "miles de m³"},
        ],
    },
    # ======================================================================
    {
        "id": "empleo",
        "area": "economico",
        "eje_pdes": "economico-productivo",
        "title": "Empleo registrado y remuneraciones",
        "resumen": (
            "Cuántos puestos de trabajo registrados del sector privado hay en Salta, abiertos por "
            "rama de actividad (rubro) y por departamento, y cómo evolucionó el poder de compra del "
            "salario: la remuneración real, descontada la inflación del NOA (índice base dic-2023 = "
            "100), desde 2019."
        ),
        "resumen_corto": "Empleo registrado y salario real, por rubro y departamento.",
        "fuente": "OEDE — Observatorio de Empleo y Dinámica Empresarial (Min. de Trabajo / Capital Humano)",
        "fuente_url": "https://www.argentina.gob.ar/trabajo/estadisticas/oede-estadisticas-provinciales",
        "cobertura": "2019–2025",
        "keywords": [
            "empleo", "puestos", "trabajo registrado", "asalariados", "sector privado", "salarios",
            "sueldos", "remuneraciones", "salario real", "remuneración real", "poder adquisitivo",
            "poder de compra", "rubro", "rama de actividad", "sector", "actividad", "OEDE",
            "Capital Humano", "comercio", "servicios", "industria manufacturera", "construcción",
            "agricultura", "minas", "IPC", "inflación", "deflactor",
        ],
        "tags": ["empleo-capacidades"],
        "kpis": [
            {"ficha": "II.1", "label": "Empleo registrado (provincia)", "tabla_label": "Empleo registrado", "metrica": "empleo",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "rubro": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "puestos", "format": "int"},
            {"ficha": "II.2", "label": "Remuneración real (índice dic-23 = 100)", "metrica": "remun_real_idx",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "rubro": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "índice", "format": "int"},
        ],
        "charts": [
            {"id": "emp-rubro", "type": "stacked-area",
             "title": "Empleo registrado por rubro",
             "descr": "Puestos de trabajo registrados según la rama de actividad. 'Todos' muestra la "
                      "provincia; cada departamento puede verse por separado.",
             "x": "trimestre", "seriesBy": "rubro", "metrica": "empleo",
             "fixed": {}, "seriesExclude": ["Total"], "stack": True,
             "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select", "all": True},
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "puestos"},
            {"id": "emp-depto", "type": "barh",
             "title": "Empleo por departamento",
             "descr": "Ranking de departamentos por cantidad de puestos registrados, para el año y el "
                      "rubro seleccionados.",
             "x": "departamento", "seriesBy": None, "metrica": "empleo",
             "fixed": {"grano": "anual", "rubro": "Total"},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"dim": "rubro", "label": "Rubro", "kind": "select", "default": "Total"},
             ],
             "sort": "desc", "unidad": "puestos"},
            {"id": "emp-remun-depto", "type": "barh",
             "title": "Remuneración real por departamento",
             "descr": "Índice de salario real por departamento (base dic-2023 = 100): por encima de 100 "
                      "el poder de compra creció respecto de diciembre de 2023; por debajo, cayó.",
             "x": "departamento", "seriesBy": None, "metrica": "remun_real_idx",
             "fixed": {"grano": "anual", "rubro": "Total"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "índice",
             "fuente": "OEDE (empleo y remuneraciones) e IPC NOA — INDEC (deflactor), vía datos.gob.ar",
             "fuente_url": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31"},
            {"id": "emp-remun-tiempo", "type": "line",
             "title": "Remuneración real en el tiempo",
             "descr": "Evolución del salario real (base dic-2023 = 100). Muestra la caída de comienzos "
                      "de 2024 y la recuperación posterior. 'Salta (provincial)' es el promedio "
                      "ponderado por empleo.",
             "x": "trimestre", "seriesBy": None, "metrica": "remun_real_idx",
             "fixed": {"rubro": "Total"}, "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincial)"},
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "índice",
             "fuente": "OEDE (empleo y remuneraciones) e IPC NOA — INDEC (deflactor), vía datos.gob.ar",
             "fuente_url": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31"},
        ],
    },
    # ======================================================================
    {
        "id": "turismo",
        "subeje": "Turismo",
        "area": "turismo",
        "eje_pdes": "territorio-ambiente-turismo",
        "title": "Turismo (ocupación hotelera)",
        "resumen": (
            "Actividad turística de Salta medida por la Encuesta de Ocupación Hotelera (EOH) del "
            "INDEC: viajeros, pernoctaciones, ocupación de habitaciones y estadía media, "
            "consolidando la Ciudad de Salta y Cafayate, desde 2021."
        ),
        "resumen_corto": "Viajeros, pernoctaciones y ocupación hotelera de Salta.",
        "fuente": "Encuesta de Ocupación Hotelera (EOH) — INDEC",
        "fuente_url": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-13-56",
        "cobertura": "2021–2025",
        "keywords": [
            "turismo", "hotel", "hotelería", "ocupación hotelera", "viajeros", "turistas",
            "pernoctaciones", "estadía", "plazas", "habitaciones", "EOH", "Cafayate",
            "residentes", "no residentes", "extranjeros", "temporada",
        ],
        "tags": ["actividad-productividad"],
        "kpis": [
            {"label": "Ocupación de habitaciones", "metrica": "ocupacion_hab",
             "fixed": {"grano": "trimestral", "segmento": "Total"}, "cmp": "quarter",
             "year": "latest", "unidad": "%", "format": "int"},
            {"label": "Viajeros", "metrica": "viajeros",
             "fixed": {"grano": "trimestral", "segmento": "Total"}, "cmp": "quarter",
             "year": "latest", "unidad": "viajeros", "format": "int"},
        ],
        "charts": [
            {"id": "tur-viajeros", "type": "line",
             "title": "Viajeros por tipo de residencia",
             "descr": "Viajeros hospedados en Salta, según residentes y no residentes en el país.",
             "x": "trimestre", "seriesBy": "segmento", "metrica": "viajeros",
             "fixed": {"grano": "trimestral"}, "seriesExclude": ["Total"],
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "viajeros"},
            {"id": "tur-ocupacion", "type": "line",
             "title": "Ocupación de habitaciones",
             "descr": "Porcentaje de habitaciones ocupadas sobre las disponibles.",
             "x": "trimestre", "seriesBy": None, "metrica": "ocupacion_hab",
             "fixed": {"grano": "trimestral", "segmento": "Total"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "%"},
            {"id": "tur-pernoctaciones", "type": "stacked-area",
             "title": "Pernoctaciones por tipo de residencia",
             "descr": "Noches de alojamiento (pernoctaciones), de residentes y no residentes.",
             "x": "trimestre", "seriesBy": "segmento", "metrica": "pernoctaciones",
             "fixed": {"grano": "trimestral"}, "seriesExclude": ["Total"], "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "noches"},
            {"id": "tur-estadia", "type": "line",
             "title": "Estadía media",
             "descr": "Cantidad promedio de noches por viajero.",
             "x": "trimestre", "seriesBy": None, "metrica": "estadia",
             "fixed": {"grano": "trimestral", "segmento": "Total"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "noches"},
        ],
    },
    # ======================================================================
    {
        "id": "agricultura",
        "ciiu": "A",
        "area": "agropecuario",
        "eje_pdes": "economico-productivo",
        "title": "Agricultura por departamento",
        "resumen": (
            "Superficie sembrada y cosechada, producción y rendimiento de los principales cultivos "
            "de Salta (soja, maíz, trigo, poroto, maní y otros), por departamento y campaña, según "
            "las estimaciones agrícolas del MAGyP, desde la campaña 2018/19."
        ),
        "resumen_corto": "Superficie, producción y rendimiento de los cultivos, por departamento.",
        "fuente": "Estimaciones Agrícolas — Ministerio de Economía (MAGyP)",
        "fuente_url": "https://datos.magyp.gob.ar/dataset/estimaciones-agricolas",
        "cobertura": "campañas 2018/19–2024/25",
        "keywords": [
            "agricultura", "agropecuario", "cultivos", "soja", "maíz", "trigo", "poroto", "maní",
            "sorgo", "girasol", "cebada", "siembra", "cosecha", "superficie", "producción",
            "rendimiento", "campaña", "granos", "MAGyP",
        ],
        "tags": ["actividad-productividad"],
        "kpis": [
            {"ficha": "I.1", "label": "Producción total", "tabla_label": "Producción agrícola total", "metrica": "produccion_tm",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "toneladas", "format": "int"},
            {"tipo": "oferta", "ficha": "I.2", "label": "Superficie sembrada", "metrica": "superficie_sembrada_ha",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "ha", "format": "int"},
        ],
        "charts": [
            {"id": "agri-superficie", "type": "stacked-area",
             "title": "Superficie sembrada por cultivo",
             "descr": "Hectáreas sembradas cada campaña, apiladas por cultivo.",
             "x": "anio", "seriesBy": "cultivo", "metrica": "superficie_sembrada_ha",
             "fixed": {"departamento": "Salta"}, "stack": True, "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "ha"},
            {"id": "agri-produccion-depto", "type": "barh",
             "title": "Producción por departamento",
             "descr": "Ranking de departamentos por toneladas producidas, para la campaña y el cultivo seleccionados.",
             "x": "departamento", "seriesBy": None, "metrica": "produccion_tm", "fixed": {},
             "controls": [
                 {"dim": "anio", "label": "Campaña", "kind": "year"},
                 {"dim": "cultivo", "label": "Cultivo", "kind": "select", "all": True},
             ],
             "sort": "desc", "unidad": "toneladas"},
            {"id": "agri-rendimiento", "type": "line",
             "title": "Rendimiento por cultivo",
             "descr": "Kilogramos por hectárea cosechada, según el cultivo.",
             "x": "anio", "seriesBy": None, "metrica": "rendimiento_kgxha",
             "fixed": {"departamento": "Salta", "cultivo": "Soja"}, "geoDim": "departamento",
             "controls": [
                 {"dim": "cultivo", "label": "Cultivo", "kind": "select", "default": "Soja"},
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "kg/ha"},
        ],
    },
    # ======================================================================
    {
        "id": "gobierno",
        "area": "fiscal",
        "eje_pdes": "economico-productivo",
        "title": "Finanzas públicas provinciales",
        "resumen": (
            "Ejecución del gasto público de la Provincia de Salta: composición por objeto del gasto "
            "(personal, bienes, servicios, transferencias, deuda), por finalidad y función, y las "
            "transferencias corrientes y de capital, en pesos corrientes y constantes de {base_largo}, 2021–2025. "
            "Además, el peso del gasto en personal y de la inversión real directa en el gasto primario, "
            "y de los recursos tributarios propios en los ingresos totales, frente al NOA y al total de "
            "provincias, 2015–2025."
        ),
        "resumen_corto": "Ejecución del gasto provincial, gasto en personal, inversión real directa y recursos propios.",
        "fuente": "Ejecución presupuestaria — Ministerio de Economía de Salta",
        "fuente_url": "https://presupuesto.salta.gob.ar/",
        "cobertura": "2015–2025",
        "keywords": [
            "gasto público", "presupuesto", "ejecución presupuestaria", "finanzas públicas",
            "objeto del gasto", "personal", "bienes de uso", "transferencias", "servicio de la deuda",
            "finalidad", "función", "gasto social", "obra pública", "coparticipación", "erogaciones",
            "gasto en personal", "inversión real directa", "gasto primario", "recursos propios",
            "autonomía fiscal", "recaudación provincial", "AIF",
        ],
        "tags": ["inversion-financiamiento"],
        "kpis": [
            {"tipo": "oferta", "ficha": "III.5", "label": "Gasto ejecutado total (pesos constantes, {base})", "metrica": "gasto_real",
             "fixed": {"clasificador": "objeto", "nivel": "total"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
            {"tipo": "oferta", "ficha": "III.6", "label": "Gasto en personal (pesos constantes, {base})", "metrica": "gasto_real",
             "fixed": {"clasificador": "objeto", "partida": "Gastos en personal"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
            {"tipo": "oferta", "label": "Gasto en personal (% del gasto primario)", "metrica": "pct_aif",
             "tabla_nota": "Esquema AIF (DNAP). Gasto primario = gastos totales − intereses de la deuda. La variación va en puntos porcentuales.",
             "fixed": {"clasificador": "aif", "nivel": "Salta", "partida": "Gasto en personal / gasto primario"},
             "grafico": "gob-personal-primario",
             "year": "latest", "unidad": "%", "format": "int", "display": "nivel", "sentido": "menor_mejor"},
            {"tipo": "oferta", "label": "Inversión real directa (% del gasto primario)", "metrica": "pct_aif",
             "tabla_nota": "Esquema AIF (DNAP): obra pública y bienes de capital. La variación va en puntos porcentuales.",
             "fixed": {"clasificador": "aif", "nivel": "Salta", "partida": "Inversión real directa / gasto primario"},
             "grafico": "gob-ird-primario",
             "year": "latest", "unidad": "%", "format": "int", "display": "nivel", "sentido": "mayor_mejor"},
            {"label": "Recursos tributarios propios (% de ingresos totales)", "metrica": "pct_aif",
             "tabla_nota": "Esquema AIF (DNAP). Grado de autonomía fiscal: recaudación provincial sobre ingresos totales. La variación va en puntos porcentuales.",
             "fixed": {"clasificador": "aif", "nivel": "Salta", "partida": "Recursos tributarios propios / ingresos totales"},
             "grafico": "gob-recursos-propios",
             "year": "latest", "unidad": "%", "format": "int", "display": "nivel", "sentido": "mayor_mejor"},
        ],
        "charts": [
            {"id": "gob-objeto", "type": "stacked-bar",
             "title": "Composición del gasto por objeto",
             "descr": "Distribución del gasto ejecutado según el objeto (personal, bienes, servicios, transferencias, deuda).",
             "x": "anio", "seriesBy": "partida", "metrica": "gasto_real",
             "fixed": {"clasificador": "objeto", "nivel": "principal"}, "stack": True,
             "controls": [
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "gasto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "gasto_real"},
                     {"value": "pct", "label": "% del total", "metric": "gasto_corr", "percent": True, "unidad": "%"}]},
             ],
             "unidad": "pesos"},
            {"id": "gob-finalidad", "type": "barh",
             "title": "Gasto por finalidad",
             "descr": "Ranking de finalidades del gasto ejecutado, para el año seleccionado.",
             "x": "partida", "seriesBy": None, "metrica": "gasto_real",
             "fixed": {"clasificador": "finalidad"},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "gasto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "gasto_real"}]},
             ],
             "sort": "desc", "unidad": "pesos"},
            {"id": "gob-transferencias", "type": "stacked-bar",
             "title": "Transferencias: corrientes y de capital",
             "descr": "Transferencias ejecutadas, separadas en corrientes y de capital.",
             "x": "anio", "seriesBy": "partida", "metrica": "gasto_real",
             "fixed": {"clasificador": "transferencia"}, "stack": True,
             "controls": [
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "gasto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "gasto_real"},
                     {"value": "pct", "label": "% del total", "metric": "gasto_corr", "percent": True, "unidad": "%"}]},
             ],
             "unidad": "pesos"},
            {"id": "gob-personal-primario", "type": "line",
             "title": "Gasto en personal sobre gasto primario",
             "descr": "Porcentaje del gasto primario (sin intereses de la deuda) destinado a salarios del sector público. Salta frente al NOA y al total de provincias.",
             "x": "anio", "seriesBy": "nivel", "metrica": "pct_aif",
             "fixed": {"clasificador": "aif", "partida": "Gasto en personal / gasto primario"},
             "controls": [], "unidad": "%",
             "fuente": "Esquema Ahorro-Inversión-Financiamiento provincial — DNAP, Ministerio de Economía de la Nación",
             "fuente_url": "https://www.argentina.gob.ar/economia/sechacienda/coordinacion-fiscal-provincial/ejecucion-presupuestaria-provincial/ejecuciones"},
            {"id": "gob-ird-primario", "type": "line",
             "title": "Inversión real directa sobre gasto primario",
             "descr": "Porcentaje del gasto primario destinado a obra pública y bienes de capital (inversión real directa). Salta frente al NOA y al total de provincias.",
             "x": "anio", "seriesBy": "nivel", "metrica": "pct_aif",
             "fixed": {"clasificador": "aif", "partida": "Inversión real directa / gasto primario"},
             "controls": [], "unidad": "%",
             "fuente": "Esquema Ahorro-Inversión-Financiamiento provincial — DNAP, Ministerio de Economía de la Nación",
             "fuente_url": "https://www.argentina.gob.ar/economia/sechacienda/coordinacion-fiscal-provincial/ejecucion-presupuestaria-provincial/ejecuciones"},
            {"id": "gob-recursos-propios", "type": "line",
             "title": "Recursos tributarios propios sobre ingresos totales",
             "descr": "Grado de autonomía fiscal: recaudación de impuestos provinciales sobre el total de ingresos de la provincia. Salta frente al NOA y al total de provincias.",
             "x": "anio", "seriesBy": "nivel", "metrica": "pct_aif",
             "fixed": {"clasificador": "aif", "partida": "Recursos tributarios propios / ingresos totales"},
             "controls": [], "unidad": "%",
             "fuente": "Esquema Ahorro-Inversión-Financiamiento provincial — DNAP, Ministerio de Economía de la Nación",
             "fuente_url": "https://www.argentina.gob.ar/economia/sechacienda/coordinacion-fiscal-provincial/ejecucion-presupuestaria-provincial/ejecuciones"},
        ],
    },
    # ======================================================================
    {
        "id": "resultado-fiscal",
        "area": "fiscal",
        "eje_pdes": "economico-productivo",
        "title": "Resultado fiscal provincial",
        "resumen": (
            "Resultado fiscal de la Provincia de Salta según el Esquema Ahorro-Inversión-"
            "Financiamiento: ingresos totales, gastos totales y el resultado financiero "
            "(superávit o déficit devengado), con el resultado primario (antes de intereses de la "
            "deuda), mensual desde 2021, en pesos corrientes y constantes de {base_largo}."
        ),
        "resumen_corto": "Ingresos, gastos y resultado financiero de la provincia, mensual.",
        "fuente": "Esquema Ahorro-Inversión-Financiamiento — Presupuesto de la Provincia de Salta",
        "fuente_url": "https://presupuesto.salta.gob.ar/esquema-ahorro-inversion/",
        "cobertura": "2021–2026",
        "keywords": [
            "resultado fiscal", "superávit", "déficit", "resultado financiero", "resultado primario",
            "ahorro inversión financiamiento", "esquema AIF", "ingresos", "recursos", "gastos",
            "erogaciones", "intereses de la deuda", "servicio de la deuda", "finanzas públicas",
            "ejecución", "devengado", "cuentas públicas", "equilibrio fiscal",
        ],
        "tags": ["inversion-financiamiento"],
        "kpis": [
            {"ficha": "III.1", "label": "Ingresos totales (pesos constantes, {base})", "metrica": "monto_real",
             "fixed": {"grano": "acumulado", "concepto": "Ingresos totales"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
            {"tipo": "oferta", "ficha": "III.2", "label": "Gastos totales (pesos constantes, {base})", "metrica": "monto_real",
             "fixed": {"grano": "acumulado", "concepto": "Gastos totales"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
            {"ficha": "III.3", "label": "Resultado financiero (% del gasto primario)",
             "tabla_label": "Resultado financiero, en % del gasto primario",
             "tabla_nota": "Gasto primario = gastos totales − intereses de la deuda. La variación va en puntos porcentuales, no en %: es un cociente. En el acumulado, la comparación válida es contra el mismo mes del año anterior.",
             "metrica": "pct_gprim",
             "fixed": {"grano": "acumulado", "concepto": "Resultado financiero"}, "year": "latest",
             "unidad": "%", "format": "int", "display": "nivel"},
            {"ficha": "III.4", "label": "Resultado primario (% del gasto primario)",
             "tabla_label": "Resultado primario, en % del gasto primario",
             "tabla_nota": "Excluye los intereses de la deuda de ambos lados del cociente. La variación va en puntos porcentuales.",
             "metrica": "pct_gprim",
             "fixed": {"grano": "acumulado", "concepto": "Resultado primario"}, "year": "latest",
             "unidad": "%", "format": "int", "display": "nivel"},
        ],
        "charts": [
            {"id": "fisc-resultado", "type": "line",
             "title": "Resultado financiero (superávit / déficit)",
             "descr": "Resultado financiero devengado (ingresos totales menos gastos totales). Por "
                      "encima de cero hay superávit; por debajo, déficit. El informe de diciembre "
                      "es el cierre anual del ejercicio.",
             "x": "periodo", "seriesBy": None, "metrica": "monto_real",
             "fixed": {"concepto": "Resultado financiero"},
             "controls": [
                 {"kind": "freq", "label": "Vista", "default": "acumulado", "options": [
                     {"value": "acumulado", "label": "Acumulado (año en curso)", "x": "periodo", "grano": "acumulado"},
                     {"value": "mensual", "label": "Mensual", "x": "periodo", "grano": "mensual"}]},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"}]},
             ],
             "unidad": "pesos"},
            {"id": "fisc-resultado-pct", "type": "line",
             "title": "Resultado fiscal en % del gasto primario",
             "descr": "Los resultados financiero y primario medidos contra el gasto primario "
                      "(gastos totales menos intereses de la deuda). Al ser un cociente no lo afecta "
                      "la inflación ni el tamaño nominal del presupuesto, así que los años se comparan "
                      "directamente. Por encima de cero hay superávit. En la vista acumulada los meses "
                      "no son comparables entre sí —enero arranca alto y el ratio baja al avanzar el "
                      "año—: hay que comparar cada mes con el mismo mes de otro año.",
             "x": "periodo", "seriesBy": "concepto", "metrica": "pct_gprim", "fixed": {},
             "controls": [
                 {"kind": "freq", "label": "Vista", "default": "acumulado", "options": [
                     {"value": "acumulado", "label": "Acumulado (año en curso)", "x": "periodo", "grano": "acumulado"},
                     {"value": "mensual", "label": "Mensual", "x": "periodo", "grano": "mensual"}]},
             ],
             "unidad": "% del gasto primario"},
            {"id": "fisc-ing-gasto", "type": "line",
             "title": "Ingresos y gastos totales",
             "descr": "Ingresos totales y gastos totales de la ejecución provincial consolidada. La "
                      "brecha entre ambos es el resultado financiero.",
             "x": "periodo", "seriesBy": "concepto", "metrica": "monto_real", "fixed": {},
             "seriesExclude": ["Resultado financiero", "Resultado primario", "Intereses de la deuda",
                               "Gasto primario"],
             "controls": [
                 {"kind": "freq", "label": "Vista", "default": "acumulado", "options": [
                     {"value": "acumulado", "label": "Acumulado (año en curso)", "x": "periodo", "grano": "acumulado"},
                     {"value": "mensual", "label": "Mensual", "x": "periodo", "grano": "mensual"}]},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"}]},
             ],
             "unidad": "pesos"},
            {"id": "fisc-primario", "type": "line",
             "title": "Resultado primario y financiero",
             "descr": "Resultado primario (antes de pagar intereses de la deuda) y resultado "
                      "financiero (después). La diferencia entre ambos es el peso de los intereses. "
                      "El resultado primario es un cálculo propio.",
             "x": "periodo", "seriesBy": "concepto", "metrica": "monto_real", "fixed": {},
             "seriesExclude": ["Ingresos totales", "Gastos totales", "Intereses de la deuda",
                               "Gasto primario"],
             "controls": [
                 {"kind": "freq", "label": "Vista", "default": "acumulado", "options": [
                     {"value": "acumulado", "label": "Acumulado (año en curso)", "x": "periodo", "grano": "acumulado"},
                     {"value": "mensual", "label": "Mensual", "x": "periodo", "grano": "mensual"}]},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"}]},
             ],
             "unidad": "pesos"},
        ],
    },
    # ======================================================================
    {
        "id": "recaudacion",
        "area": "fiscal",
        "eje_pdes": "economico-productivo",
        "title": "Recaudación de Ingresos Brutos (Convenio Multilateral)",
        "resumen": (
            "Recaudación del Impuesto a las Actividades Económicas (Ingresos Brutos) de Salta bajo "
            "el régimen de Convenio Multilateral, abierta por sector de actividad, mensual desde "
            "2021, en pesos corrientes y constantes de {base_largo}. No incluye a los contribuyentes locales."
        ),
        "resumen_corto": "Ingresos Brutos (Convenio Multilateral) por sector de actividad.",
        "fuente": "Dirección General de Rentas — Ministerio de Economía de Salta",
        "fuente_url": "https://www.dgrsalta.gov.ar/",
        "cobertura": "2021–2026",
        "keywords": [
            "recaudación", "ingresos brutos", "actividades económicas", "convenio multilateral",
            "impuestos", "tributos", "tributario", "DGR", "rentas", "recursos tributarios",
            "sector", "rama de actividad", "comercio", "industria", "minería", "construcción",
            "presión tributaria", "impuesto provincial",
        ],
        "tags": ["inversion-financiamiento", "actividad-productividad"],
        "kpis": [
            {"ficha": "III.7", "label": "Recaudación de Ingresos Brutos (pesos constantes, {base})", "metrica": "recaud_real",
             "fixed": {}, "year": "latest", "unidad": "pesos", "format": "int"},
            {"ficha": "III.8", "label": "Industria manufacturera (pesos constantes, {base})", "ciiu": "C",
             "tabla_label": "Recaudación de la industria manufacturera (pesos constantes)", "metrica": "recaud_real",
             "fixed": {"sector": "Industria manufacturera"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
        ],
        "charts": [
            {"id": "rec-total", "type": "line",
             "title": "Recaudación total en el tiempo",
             "descr": "Recaudación del Impuesto a las Actividades Económicas (Convenio Multilateral), "
                      "sumando todos los sectores.",
             "x": "trimestre", "seriesBy": None, "metrica": "recaud_real", "fixed": {},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "periodo", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "recaud_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "recaud_real"}]},
             ],
             "unidad": "pesos"},
            {"id": "rec-sector", "type": "stacked-area",
             "title": "Recaudación por sector de actividad",
             "descr": "Composición de la recaudación según el sector de actividad (clasificación CIIU).",
             "x": "trimestre", "seriesBy": "sector", "metrica": "recaud_real", "fixed": {}, "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "recaud_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "recaud_real"},
                     {"value": "pct", "label": "% del total", "metric": "recaud_corr", "percent": True, "unidad": "%"}]},
             ],
             "unidad": "pesos"},
            {"id": "rec-ranking", "type": "barh",
             "title": "Recaudación por sector (ranking)",
             "descr": "Sectores ordenados por recaudación en el año seleccionado.",
             "x": "sector", "seriesBy": None, "metrica": "recaud_real", "fixed": {"grano": "anual"},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "recaud_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "recaud_real"}]},
             ],
             "sort": "desc", "unidad": "pesos"},
        ],
    },
    # ======================================================================
    {
        "id": "ganaderia",
        "ciiu": "A",
        "area": "agropecuario",
        "eje_pdes": "economico-productivo",
        "title": "Ganadería bovina",
        "resumen": (
            "Existencias de ganado bovino en Salta al 31 de diciembre de cada año, por departamento "
            "y categoría de hacienda (vacas, novillos, terneros, toros y otras), según el MAGyP, "
            "desde 2012."
        ),
        "resumen_corto": "Stock bovino por departamento y categoría de hacienda.",
        "fuente": "Existencias bovinas (SENASA) — Ministerio de Economía (MAGyP)",
        "fuente_url": "https://datos.magyp.gob.ar/dataset/existencias-bovinas",
        "cobertura": "2012–2025",
        "keywords": [
            "ganadería", "bovinos", "vacas", "novillos", "terneros", "vaquillonas", "toros",
            "hacienda", "stock", "rodeo", "cabezas", "SENASA", "cría", "invernada", "carne",
        ],
        "tags": ["actividad-productividad"],
        "kpis": [
            {"ficha": "I.4", "label": "Stock bovino total", "metrica": "stock_bovino",
             "fixed": {"categoria": "Total", "departamento": "Salta"}, "year": "latest",
             "unidad": "cabezas", "format": "int",
             "meta_2030": 2000000},
            {"ficha": "I.5", "label": "Vacas", "tabla_label": "Stock de vacas", "metrica": "stock_bovino",
             "fixed": {"categoria": "Vacas", "departamento": "Salta"}, "year": "latest",
             "unidad": "cabezas", "format": "int"},
        ],
        "charts": [
            {"id": "gan-stock", "type": "line",
             "title": "Stock bovino en el tiempo",
             "descr": "Existencias totales de ganado bovino al cierre de cada año.",
             "x": "anio", "seriesBy": None, "metrica": "stock_bovino",
             "fixed": {"categoria": "Total", "departamento": "Salta"}, "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "cabezas"},
            {"id": "gan-categoria", "type": "stacked-area",
             "title": "Composición del rodeo por categoría",
             "descr": "Cabezas por categoría de hacienda, apiladas.",
             "x": "anio", "seriesBy": "categoria", "metrica": "stock_bovino",
             "fixed": {"departamento": "Salta"}, "seriesExclude": ["Total"], "stack": True,
             "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "cabezas"},
            {"id": "gan-depto", "type": "barh",
             "title": "Stock bovino por departamento",
             "descr": "Ranking de departamentos por existencias bovinas, para el año seleccionado.",
             "x": "departamento", "seriesBy": None, "metrica": "stock_bovino",
             "fixed": {"categoria": "Total"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "cabezas"},
        ],
    },
    # ======================================================================
    {
        "id": "mineria",
        "ciiu": "B",
        "area": "mineria",
        "eje_pdes": "economico-productivo",
        "title": "Minería",
        "resumen": (
            "Empleo minero registrado en Salta por rubro (litio, metalíferos, no metalíferos, rocas "
            "de aplicación, servicios) y género, desde 2007; y el aporte tributario del sector minero "
            "a nivel nacional, por empresa e impuesto, en pesos y en dólares, 2019–2023."
        ),
        "resumen_corto": "Empleo minero de Salta y aporte tributario del sector.",
        "fuente": "Empleo: OEDE (Min. de Trabajo). Recaudación: Secretaría de Minería de la Nación",
        "fuente_url": "https://www.argentina.gob.ar/economia/mineria",
        "cobertura": "2007–2025",
        "keywords": [
            "minería", "litio", "metalíferos", "no metalíferos", "rocas de aplicación", "empleo minero",
            "puestos", "regalías", "recaudación", "impuestos", "canon", "exportación", "salares",
            "puna", "género", "servicios mineros",
        ],
        "tags": ["empleo-capacidades", "inversion-financiamiento"],
        "kpis": [
            {"ficha": "II.3", "label": "Empleo minero (Salta)", "tabla_label": "Empleo minero", "metrica": "empleo_min",
             "fixed": {"grano": "trimestral", "genero": "Total", "rubro": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "puestos", "format": "int"},
            {"ficha": "III.9", "label": "Recaudación del sector (USD, nacional)",
             "tabla_label": "Recaudación del sector minero", "subeje": "Inversión y financiamiento",
             "tabla_nota": "Dato nacional del sector, no atribuible a Salta.",
             "metrica": "recaud_usd",
             "fixed": {}, "year": "latest", "unidad": "millones US$", "format": "int"},
        ],
        "charts": [
            {"id": "min-empleo-rubro", "type": "stacked-area",
             "title": "Empleo minero por rubro",
             "descr": "Puestos de trabajo registrados en minería, según el rubro.",
             "x": "trimestre", "seriesBy": "rubro", "metrica": "empleo_min",
             "fixed": {"grano": "trimestral", "genero": "Total"}, "seriesExclude": ["Total"], "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "puestos"},
            {"id": "min-empleo-genero", "type": "line",
             "title": "Empleo minero por género",
             "descr": "Puestos registrados en minería, por género.",
             "x": "trimestre", "seriesBy": "genero", "metrica": "empleo_min",
             "fixed": {"grano": "trimestral", "rubro": "Total"}, "seriesExclude": ["Total"],
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "puestos"},
            {"id": "min-recaud-impuesto", "type": "stacked-bar",
             "title": "Aporte tributario del sector por impuesto (nacional)",
             "descr": "Recaudación del sector minero por tipo de impuesto. Dato nacional, no atribuible a Salta.",
             "x": "anio", "seriesBy": "impuesto", "metrica": "recaud_ars", "fixed": {}, "stack": True,
             "controls": [
                 {"kind": "metric", "label": "Moneda", "options": ["recaud_ars", "recaud_usd"]},
             ],
             "unidad": "millones de $",
             "fuente": "Secretaría de Minería de la Nación (aporte tributario del sector, nacional)"},
        ],
    },
    # ======================================================================
    {
        "id": "financiero",
        "ciiu": "K",
        "area": "financiero",
        "eje_pdes": "economico-productivo",
        "title": "Crédito y depósitos (BCRA)",
        "resumen": (
            "Préstamos y depósitos del sector privado en Salta según el BCRA, por departamento, en "
            "pesos corrientes y constantes de {base_largo}; y la inclusión financiera medida por los puntos de acceso "
            "cada 10.000 adultos, desde 2019."
        ),
        "resumen_corto": "Préstamos, depósitos e inclusión financiera, por departamento.",
        "fuente": "Banco Central de la República Argentina (BCRA)",
        "fuente_url": "https://www.bcra.gob.ar/",
        "cobertura": "2019–2026",
        "keywords": [
            "crédito", "préstamos", "depósitos", "banco", "bancos", "financiero", "BCRA",
            "sector privado", "inclusión financiera", "puntos de acceso", "cajeros", "sucursales",
            "ahorro", "financiamiento",
        ],
        "tags": ["inversion-financiamiento"],
        "kpis": [
            {"ficha": "III.12", "label": "Préstamos al sector privado (pesos constantes, {base})", "metrica": "monto_real",
             "fixed": {"grano": "anual", "departamento": "Salta", "operacion": "Préstamos"},
             "year": "latest_complete", "unidad": "pesos", "format": "int"},
            {"ficha": "III.13", "label": "Depósitos del sector privado (pesos constantes, {base})", "metrica": "monto_real",
             "fixed": {"grano": "anual", "departamento": "Salta", "operacion": "Depósitos"},
             "year": "latest_complete", "unidad": "pesos", "format": "int"},
        ],
        "charts": [
            {"id": "fin-prestamos-depositos", "type": "line",
             "title": "Préstamos y depósitos del sector privado",
             "descr": "Saldos de préstamos y depósitos del sector privado (fin de trimestre).",
             "x": "trimestre", "seriesBy": "operacion", "metrica": "monto_real",
             "fixed": {"grano": "trimestral", "departamento": "Salta"}, "seriesExclude": ["PDA"],
             "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"}]},
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "pesos"},
            {"id": "fin-credito-depto", "type": "barh",
             "title": "Crédito al sector privado por departamento",
             "descr": "Ranking de departamentos por saldo de préstamos al sector privado, para el año seleccionado.",
             "x": "departamento", "seriesBy": None, "metrica": "monto_real",
             "fixed": {"grano": "anual", "operacion": "Préstamos"},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"}]},
             ],
             "sort": "desc", "unidad": "pesos"},
            {"id": "fin-inclusion", "type": "barh",
             "title": "Inclusión financiera por departamento",
             "descr": "Puntos de acceso al sistema financiero cada 10.000 adultos, para el año seleccionado.",
             "x": "departamento", "seriesBy": None, "metrica": "pda_10m",
             "fixed": {"grano": "anual", "operacion": "PDA"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "PDA/10k"},
        ],
    },
    # ======================================================================
    {
        "id": "conectividad",
        "area": "ciencia",
        "eje_pdes": "economico-productivo",
        "title": "Conectividad: internet fijo (ENACOM)",
        "resumen": (
            "Accesos a internet fijo en Salta según ENACOM: penetración cada 100 hogares y cada 100 "
            "habitantes, accesos por tecnología y velocidad media de bajada, trimestral desde 2015, con "
            "el total del país como referencia. Por departamento, accesos cada 100 hogares (base Censo "
            "2022) y participación de la fibra óptica, a partir de los datos por localidad de ENACOM "
            "(desde 2026-T2)."
        ),
        "resumen_corto": "Internet fijo: penetración, tecnologías, velocidad y brecha por departamento.",
        "fuente": "ENACOM (datos abiertos de internet) e INDEC (Censo 2022, hogares)",
        "fuente_url": "https://indicadores.enacom.gob.ar/DatosAbiertos/Internet/default.aspx",
        "cobertura": "2015–2026",
        "keywords": [
            "internet", "conectividad", "banda ancha", "fibra óptica", "ENACOM", "accesos",
            "hogares", "velocidad", "Mbps", "telecomunicaciones", "brecha digital", "economía del conocimiento",
            "cablemódem", "ADSL", "wireless", "satelital", "localidad",
        ],
        "tags": ["infraestructura-logistica"],
        "kpis": [
            {"label": "Accesos a internet fijo cada 100 hogares", "metrica": "acc_100_hog",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "ambito": "Salta", "tecnologia": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "accesos/100 hogares", "format": "dec1"},
            {"label": "Accesos a internet fijo", "metrica": "accesos",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "ambito": "Salta", "tecnologia": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "accesos", "format": "int"},
            {"tipo": "oferta", "label": "Velocidad media de bajada", "metrica": "vel_mbps",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "ambito": "Salta", "tecnologia": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "Mbps", "format": "dec1"},
        ],
        "charts": [
            {"id": "con-penetracion", "type": "line",
             "title": "Accesos a internet fijo: Salta y país",
             "descr": "Accesos cada 100 hogares o cada 100 habitantes, por trimestre. Desde 2022 ENACOM usa "
                      "proyecciones del Censo 2022, lo que baja la tasa por hogares.",
             "x": "trimestre", "seriesBy": "ambito", "metrica": "acc_100_hog",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "tecnologia": "Total"},
             "controls": [{"kind": "metric", "label": "Indicador", "options": ["acc_100_hog", "acc_100_hab"]},
                          {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                 {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                 {"value": "anual", "label": "Anual (promedio)", "x": "anio", "grano": "anual"}]}],
             "unidad": "accesos/100 hogares"},
            {"id": "con-tecnologia", "type": "stacked-area",
             "title": "Accesos a internet fijo por tecnología en Salta",
             "descr": "Cantidad de accesos por tecnología al final de cada trimestre.",
             "x": "trimestre", "seriesBy": "tecnologia", "metrica": "accesos",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "ambito": "Salta"},
             "seriesExclude": ["Total"], "stack": True,
             "controls": [{"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                 {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                 {"value": "anual", "label": "Anual (promedio)", "x": "anio", "grano": "anual"}]}],
             "unidad": "accesos"},
            {"id": "con-velocidad", "type": "line",
             "title": "Velocidad media de bajada: Salta y país",
             "descr": "Velocidad media de bajada de los accesos fijos, en Mbps.",
             "x": "trimestre", "seriesBy": "ambito", "metrica": "vel_mbps",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "tecnologia": "Total"},
             "controls": [{"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                 {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                 {"value": "anual", "label": "Anual (promedio)", "x": "anio", "grano": "anual"}]}],
             "unidad": "Mbps"},
            {"id": "con-depto", "type": "barh",
             "title": "Accesos a internet fijo cada 100 hogares por departamento",
             "descr": "Último trimestre disponible del año seleccionado. Hogares del Censo 2022; en Capital supera "
                      "100 porque incluye accesos de empresas y organismos.",
             "x": "departamento", "seriesBy": None, "metrica": "acc_100_hog_censo",
             "fixed": {"grano": "anual", "ambito": "Salta", "tecnologia": "Total"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "accesos/100 hogares"},
            {"id": "con-fibra-depto", "type": "barh",
             "title": "Participación de la fibra óptica por departamento",
             "descr": "Accesos por fibra óptica como % del total de accesos fijos, último trimestre disponible del año.",
             "x": "departamento", "seriesBy": None, "metrica": "pct_fibra",
             "fixed": {"grano": "anual", "ambito": "Salta", "tecnologia": "Total"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "%"},
        ],
    },
    # ======================================================================
    {
        "id": "construccion",
        "ciiu": "F",
        "area": "construccion",
        "eje_pdes": "economico-productivo",
        "title": "Construcción (permisos de edificación)",
        "resumen": (
            "Permisos de edificación privada y superficie autorizada en los principales municipios "
            "de Salta (Ciudad de Salta, Orán, Tartagal, General Güemes y Metán), según el relevamiento "
            "del INDEC, y la participación de la provincia en el total nacional, desde 2021."
        ),
        "resumen_corto": "Permisos y superficie autorizada para construir, por municipio.",
        "fuente": "Permisos de edificación — INDEC",
        "fuente_url": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-3-42",
        "cobertura": "2021–2026",
        "keywords": [
            "construcción", "permisos", "edificación", "obra privada", "superficie", "m2",
            "metros cuadrados", "vivienda", "INDEC", "Tartagal", "Orán", "Güemes", "Metán",
            "actividad de la construcción",
        ],
        "tags": ["actividad-productividad", "infraestructura-logistica"],
        "kpis": [
            {"ficha": "I.13", "label": "Superficie autorizada", "tabla_label": "Superficie autorizada a construir",
             "metrica": "superficie_m2",
             "fixed": {"grano": "anual", "municipio": "Total Salta"}, "year": "latest_complete",
             "unidad": "m²", "format": "int"},
            {"ficha": "I.14", "label": "Permisos otorgados", "tabla_label": "Permisos de edificación otorgados",
             "metrica": "permisos",
             "fixed": {"grano": "anual", "municipio": "Total Salta"}, "year": "latest_complete",
             "unidad": "permisos", "format": "int"},
        ],
        "charts": [
            {"id": "constr-superficie", "type": "stacked-area",
             "title": "Superficie autorizada por municipio",
             "descr": "Metros cuadrados autorizados en permisos de edificación, apilados por municipio.",
             "x": "trimestre", "seriesBy": "municipio", "metrica": "superficie_m2",
             "fixed": {"grano": "trimestral"}, "seriesExclude": ["Total Salta"], "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "m²"},
            {"id": "constr-permisos", "type": "line",
             "title": "Permisos otorgados (provincia)",
             "descr": "Cantidad de permisos de edificación otorgados en la provincia.",
             "x": "trimestre", "seriesBy": None, "metrica": "permisos",
             "fixed": {"grano": "trimestral", "municipio": "Total Salta"},
             "geoDim": "municipio",
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "permisos"},
            {"id": "constr-share", "type": "line",
             "title": "Participación de Salta en el país",
             "descr": "Porcentaje de la superficie autorizada nacional que corresponde a Salta.",
             "x": "trimestre", "seriesBy": None, "metrica": "share_sup_pct",
             "fixed": {"grano": "trimestral", "municipio": "Total Salta"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "%"},
            {"id": "constr-ranking", "type": "barh",
             "title": "Superficie autorizada por municipio",
             "descr": "Ranking de municipios por metros cuadrados autorizados, para el año seleccionado.",
             "x": "municipio", "seriesBy": None, "metrica": "superficie_m2",
             "fixed": {"grano": "anual"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "m²"},
        ],
    },
    # ======================================================================
    {
        "id": "recursos-municipios",
        "area": "fiscal",
        "eje_pdes": "economico-productivo",
        "title": "Recursos de los municipios",
        "resumen": (
            "Transferencias que reciben los municipios de Salta de la Provincia y la Nación "
            "(coparticipación, regalías, canon minero, fondo compensador y otros), por municipio y "
            "departamento, en pesos corrientes y constantes de {base_largo}, mensual desde 2021."
        ),
        "resumen_corto": "Coparticipación, regalías y otros recursos de los municipios.",
        "fuente": "Contaduría General de la Provincia de Salta",
        "fuente_url": "https://economiasalta.gob.ar/contaduria",
        "cobertura": "2021–2026",
        "keywords": [
            "municipios", "coparticipación", "regalías", "canon minero", "fondo compensador",
            "transferencias", "recursos municipales", "gas", "petróleo", "hidroeléctricas",
            "recaudación", "reparto", "ATN",
        ],
        "tags": ["inversion-financiamiento"],
        "kpis": [
            {"tipo": "oferta", "ficha": "III.10", "label": "Recursos a municipios (pesos constantes, {base})", "metrica": "monto_real",
             "fixed": {"grano": "anual"}, "year": "latest_complete", "unidad": "pesos", "format": "int"},
            {"tipo": "oferta", "ficha": "III.11", "label": "Coparticipación (pesos constantes, {base})", "tabla_label": "Coparticipación a municipios (pesos constantes)",
             "metrica": "monto_real",
             "fixed": {"grano": "anual", "grupo": "Coparticipación"}, "year": "latest_complete",
             "unidad": "pesos", "format": "int"},
        ],
        "charts": [
            {"id": "rec-grupo", "type": "stacked-area",
             "title": "Recursos por tipo",
             "descr": "Transferencias a municipios apiladas por grupo de recurso.",
             "x": "trimestre", "seriesBy": "grupo", "metrica": "monto_real",
             "fixed": {"grano": "trimestral"}, "stack": True, "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select", "all": True},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"},
                     {"value": "pct", "label": "% del total", "metric": "monto_corr", "percent": True, "unidad": "%"}]},
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "pesos"},
            {"id": "rec-municipio", "type": "barh",
             "title": "Recursos por municipio",
             "descr": "Ranking de municipios por recursos recibidos, para el año seleccionado.",
             "x": "municipio", "seriesBy": None, "metrica": "monto_real",
             "fixed": {"grano": "anual"},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"}]},
             ],
             "sort": "desc", "unidad": "pesos"},
            {"id": "rec-departamento", "type": "barh",
             "title": "Recursos por departamento",
             "descr": "Ranking de departamentos por recursos recibidos por sus municipios, para el año seleccionado.",
             "x": "departamento", "seriesBy": None, "metrica": "monto_real",
             "fixed": {"grano": "anual"},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "monto_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "monto_real"}]},
             ],
             "sort": "desc", "unidad": "pesos"},
        ],
    },
    # ======================================================================
    {
        "id": "energia-renovable",
        "subeje": "Ambiente",
        "area": "ambiente",
        "eje_pdes": "territorio-ambiente-turismo",
        "title": "Energías renovables",
        "resumen": (
            "El peso de las energías renovables e hidráulicas en la matriz eléctrica de Salta según "
            "CAMMESA: qué porcentaje de la generación provincial es de origen limpio y cuánta energía "
            "renovable e hidráulica se produce, desde 2019. La generación eléctrica total y por central "
            "está en el tablero de Energía eléctrica."
        ),
        "resumen_corto": "Peso y generación de las energías renovables e hidráulicas.",
        "fuente": "CAMMESA — Informe de síntesis mensual",
        "fuente_url": "https://cammesaweb.cammesa.com/",
        "cobertura": "2019–2026",
        "keywords": [
            "renovable", "renovables", "energía limpia", "solar", "hidráulica", "biomasa", "eólica",
            "matriz energética", "transición energética", "CAMMESA", "GWh", "Ley 27191",
            "parques solares", "Cafayate", "Altiplano", "ambiente", "descarbonización",
        ],
        "tags": ["innovacion-mercados", "infraestructura-logistica"],
        "kpis": [
            {"label": "Participación renovable", "tabla_label": "Participación renovable en la generación",
             "metrica": "share_renovable_pct",
             "fixed": {"grano": "trimestral"}, "cmp": "quarter", "year": "latest",
             "unidad": "%", "format": "int"},
        ],
        "charts": [
            {"id": "ren-share", "type": "line",
             "title": "Participación de las renovables",
             "descr": "Porcentaje de la generación de origen renovable e hidráulico.",
             "x": "trimestre", "seriesBy": None, "metrica": "share_renovable_pct",
             "fixed": {"grano": "trimestral"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "%"},
            {"id": "ren-gen", "type": "stacked-area",
             "title": "Generación de origen renovable e hidráulico",
             "descr": "Energía generada por fuentes limpias (renovable e hidráulica), apilada por "
                      "fuente (GWh). La generación térmica se ve en el tablero de Energía eléctrica.",
             "x": "trimestre", "seriesBy": "fuente", "metrica": "generacion_gwh",
             "fixed": {"grano": "trimestral"}, "seriesExclude": ["Térmica"], "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "GWh"},
        ],
    },
    # ======================================================================
    {
        "id": "bosques",
        "subeje": "Ambiente",
        "area": "ambiente",
        "eje_pdes": "territorio-ambiente-turismo",
        "title": "Bosque nativo y uso del suelo",
        "resumen": (
            "Cuánto bosque nativo queda en Salta, cuánto se desmonta cada año y cuánto se "
            "regenera, por departamento y desde 1987, según MapBiomas Argentina; y en qué se "
            "convierte el territorio, con la cobertura y uso del suelo provincial desde 1985. "
            "Dos salvedades que cambian la lectura: el desmonte es la conversión de bosque a "
            "uso antrópico y no incluye el bosque que pasa a arbustal o pastizal, que se "
            "publica aparte; y los años 2022-2025 son provisorios —la fuente los reescribe "
            "cuando hay años posteriores que confirman o revierten cada cambio—, así que los "
            "indicadores de la portada se detienen en 2021."
        ),
        "resumen_corto": "Bosque nativo, desmonte y regeneración por departamento, y uso del suelo.",
        "fuente": ("MapBiomas Argentina — Colección 3 (cobertura y uso; desmonte y vegetación "
                   "secundaria)"),
        "fuente_url": "https://argentina.mapbiomas.org",
        "cobertura": "1985–2025 (consolidado hasta 2021)",
        "keywords": [
            "bosque", "bosques", "bosque nativo", "desmonte", "deforestación", "tala",
            "regeneración", "MapBiomas", "OTBN", "ordenamiento territorial", "Ley 26331",
            "Chaco", "yungas", "monte", "cobertura del suelo", "uso del suelo", "hectáreas",
            "ambiente", "Anta", "Rivadavia", "Orán", "San Martín", "frontera agropecuaria",
        ],
        "tags": ["actividad-productividad"],
        # Los cuatro fijan `serie: "Consolidada"`, que es lo que los deja en 2021 —el último
        # año que MapBiomas da por cerrado—. No alcanza con `year`: ver la nota del spec de KPI
        # arriba. Los gráficos NO fijan la dimensión, así que muestran hasta 2025.
        "kpis": [
            {"label": "Superficie de bosque nativo", "metrica": "superficie_bosque_ha",
             "tabla_nota": ("Último año consolidado por la fuente. Los gráficos del tablero "
                            "llegan hasta 2025, con la franja provisoria marcada."),
             "fixed": {"serie": "Consolidada", "departamento": "Salta", "clase": "Total"},
             "year": "latest", "unidad": "ha", "format": "int", "sentido": "mayor_mejor"},
            {"label": "Desmonte anual de bosque", "metrica": "desmonte_bosque_ha",
             "tabla_nota": ("Conversión de bosque a uso antrópico; no incluye el bosque que "
                            "pasa a arbustal o pastizal. Último año consolidado por la fuente."),
             "fixed": {"serie": "Consolidada", "departamento": "Salta", "clase": "Total"},
             "year": "latest", "unidad": "ha", "format": "int", "sentido": "menor_mejor"},
            {"label": "Regeneración de bosque", "metrica": "regeneracion_bosque_ha",
             "tabla_nota": ("Vegetación que vuelve sobre suelo que tuvo uso antrópico: no es "
                            "reforestación y no distingue restauración activa de abandono de "
                            "lotes. Último año consolidado por la fuente."),
             "fixed": {"serie": "Consolidada", "departamento": "Salta", "clase": "Total"},
             "year": "latest", "unidad": "ha", "format": "int", "sentido": "mayor_mejor"},
            {"label": "Bosque sobre la superficie provincial",
             "metrica": "share_bosque_pct",
             "tabla_nota": ("Sobre las 15,5 millones de hectáreas de la provincia. Último año "
                            "consolidado por la fuente."),
             "fixed": {"serie": "Consolidada", "departamento": "Salta", "clase": "Total"},
             "year": "latest", "unidad": "%", "format": "dec1", "sentido": "mayor_mejor"},
        ],
        "charts": [
            {"id": "bos-superficie", "type": "line",
             "title": "Evolución del bosque nativo",
             "descr": ("Superficie con bosque al cierre de cada año. Los años 2022-2025 son "
                       "provisorios: la fuente aplica reglas de fin de serie a los últimos "
                       "cuatro años y los reescribe en cada colección nueva."),
             "x": "anio", "seriesBy": None, "metrica": "superficie_bosque_ha",
             "fixed": {"departamento": "Salta", "clase": "Total"}, "geoDim": "departamento",
             "provisorio_desde": 2022,
             "controls": [
                 {"kind": "mode", "label": "Medida", "default": "ha", "options": [
                     {"value": "ha", "label": "Hectáreas", "metric": "superficie_bosque_ha"},
                     {"value": "pct", "label": "% del territorio", "metric": "share_bosque_pct",
                      "unidad": "%"}]},
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "ha"},
            {"id": "bos-flujos", "type": "line",
             "title": "Desmonte y regeneración",
             "descr": ("Hectáreas que cambian de estado cada año. El desmonte exige conversión a uso antrópico;"
                       "el bosque que pasa a arbustal o pastizal va aparte. Ahí se mezclan degradación, incendios y oscilación"
                       "de la clasificación. La regeneración de los últimos años está subestimada por construcción. "
                       "Datos 2022-2025 son provisorios."),
             "x": "anio", "seriesBy": None, "metrica": "desmonte_bosque_ha",
             "fixed": {"departamento": "Salta", "clase": "Total"}, "geoDim": "departamento",
             "provisorio_desde": 2022,
             "controls": [
                 {"kind": "metric", "label": "Flujo", "options": [
                     "desmonte_bosque_ha", "desmonte_bosque_primario_ha",
                     "desmonte_bosque_secundario_ha", "regeneracion_bosque_ha",
                     "bosque_a_otra_vegetacion_natural_ha", "bosque_perdido_ha"]},
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "ha"},
            {"id": "bos-ranking", "type": "barh",
             "title": "Ranking por departamento",
             "descr": ("Departamentos ordenados por la medida y el año seleccionados. Los años "
                       "2022-2025 son provisorios: la fuente los reescribe cuando hay años "
                       "posteriores que confirman o revierten cada cambio."),
             "x": "departamento", "seriesBy": None, "metrica": "desmonte_bosque_ha",
             "fixed": {"clase": "Total"},
             "controls": [
                 {"kind": "metric", "label": "Medida", "options": [
                     "desmonte_bosque_ha", "superficie_bosque_ha", "regeneracion_bosque_ha"]},
                 {"dim": "anio", "label": "Año", "kind": "year"},
             ],
             "sort": "desc", "unidad": "ha"},
            {"id": "bos-grupos", "type": "stacked-area",
             "title": "Cobertura y uso del suelo",
             "descr": ("En qué está cubierto el territorio provincial, por grandes grupos. Es "
                       "el contexto que el dato de desmonte no da por sí solo: a qué se "
                       "convierte lo que deja de ser bosque. Dato provincial de la planilla "
                       "oficial de MapBiomas."),
             "x": "anio", "seriesBy": "clase", "metrica": "superficie_grupo_ha",
             "fixed": {"departamento": "Salta"}, "stack": True,
             "provisorio_desde": 2022,
             # Gris para lo urbanizado: es el color con el que se lee una mancha urbana en
             # cualquier mapa de cobertura, y la paleta le tocaba un tono cualquiera.
             "seriesColor": {"Áreas urbanas": {"light": "#6f767e", "dark": "#9aa2ab"}},
             "controls": [
                 {"kind": "mode", "label": "Medida", "default": "ha", "options": [
                     {"value": "ha", "label": "Hectáreas"},
                     {"value": "pct", "label": "% del total", "percent": True, "unidad": "%"}]},
             ],
             "unidad": "ha"},
            {"id": "bos-clases", "type": "barh",
             "title": "Superficie por clase de cobertura",
             "descr": ("Las 18 clases de MapBiomas para el año seleccionado, el detalle de los "
                       "grupos del gráfico anterior. Los años 2022-2025 son provisorios."),
             "x": "clase", "seriesBy": None, "metrica": "superficie_clase_ha",
             "fixed": {"departamento": "Salta"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "ha"},
        ],
    },
    # ======================================================================
    {
        "id": "transparencia",
        "subeje": "Territorio",
        "area": "institucional",
        "eje_pdes": "territorio-ambiente-turismo",
        "title": "Transparencia del sector público",
        "resumen": (
            "Qué información pública publican en sus canales oficiales los 60 municipios de "
            "Salta y el Poder Ejecutivo provincial, medidos con la misma vara: 10 criterios "
            "—presupuesto, ejecución, planta y sueldos, compras, adjudicaciones, declaraciones "
            "juradas, boletín, acceso a la información y datos abiertos— con un puntaje de 0 a 100"
            "Mide publicación en línea, no cumplimiento de la ley, que puede serlo por otro medio."
        ),
        "resumen_corto": ("Qué publican los 60 municipios y el Ejecutivo provincial, "
                          "en 10 criterios."),
        "advertencia": (
            "El índice mide publicación activa en canales oficiales en línea, no cumplimiento de la ley "
            "(e.d., un municipio que entrega información a pedido, en papel o en el Concejo puntúa 0)."
            
        ),
        "fuente": ("Relevamiento propio del CESS sobre canales oficiales (municipios y "
                   "Ejecutivo provincial)"),
        "fuente_url": "https://boletinoficialsalta.gob.ar/Municipios.php",
        "cobertura": "Toma 2026 (municipios 04-11, provincia 07-11)",
        "keywords": [
            "transparencia", "acceso a la información", "información pública", "datos abiertos",
            "municipios", "gobiernos locales", "intendencias", "boletín oficial",
            "declaraciones juradas", "presupuesto municipal", "compras", "contrataciones",
            "adjudicaciones", "rendición de cuentas", "gobierno abierto", "gestión pública",
        ],
        # Ninguno de los cinco ejes transversales de desarrollo productivo describe esto, y el
        # chip quedaría diciendo algo falso. El subeje va declarado arriba, así que la lista
        # vacía no deja al tablero sin agrupar.
        "tags": [],
        "kpis": [
            {"label": "Transparencia del Ejecutivo provincial",
             "tabla_label": "Transparencia del Ejecutivo provincial (índice 0-100)",
             "tabla_nota": ("Relevamiento propio del CESS sobre canales oficiales, 2026-11-07: "
                            "6 criterios en sí, 2 en parcial y 2 en no. Mide publicación activa "
                            "en línea, no cumplimiento legal. Alcance: sólo el Poder Ejecutivo. "
                            "Las evidencias están pendientes de verificación humana."),
             "metrica": "transparencia",
             "fixed": {"nivel": "Ejecutivo provincial"},
             "year": "latest", "unidad": "/100", "format": "int",
             "display": "nivel", "sentido": "mayor_mejor", "frecuencia": "Toma única",
             # La métrica `transparencia` la comparten los 60 municipios, así que el cálculo
             # automático la daría por municipal: este indicador es de una sola unidad.
             "geo": "Provincia", "geo_nota": "Sólo el Poder Ejecutivo provincial",
             "grafico": "tra-nivel"},
            {"tipo": "oferta", "label": "Municipios con sitio web oficial",
             "tabla_label": "Municipios con sitio web oficial (de 60)",
             "tabla_nota": ("Relevamiento propio del CESS, 2026-11-04. Es la lectura menos "
                            "expuesta al efecto piso: 49 de los 60 municipios tienen índice 0 y "
                            "el índice está midiendo, en buena medida, quién tiene página web."),
             "metrica": "municipios_con_sitio",
             "fixed": {"nivel": "Municipio"},
             "year": "latest", "unidad": "municipios", "format": "int",
             "display": "nivel", "sentido": "mayor_mejor", "frecuencia": "Toma única",
             "geo": "Provincia", "geo_nota": "Conteo sobre los 60 municipios de Salta",
             "grafico": "tra-municipios"},
        ],
        "charts": [
            {"id": "tra-criterios", "type": "stacked-bar",
             "title": "Cumplimiento por criterio, en los 60 municipios",
             "descr": ("Cuántos municipios publican cada cosa. Es la lectura más informativa del "
                       "dato: con 49 municipios en cero, el conteo por criterio dice más que "
                       "cualquier promedio. «No verificado» es el canal que existe pero no se "
                       "pudo leer ese día —sitio caído, certificado vencido—: se cuenta aparte "
                       "de «no», que es lo que se buscó y no está."),
             "x": "criterio", "seriesBy": "estado", "metrica": "municipios",
             "fixed": {"nivel": "Municipio"}, "stack": True,
             "seriesColor": {
                 "Sí": {"light": "#16a97a", "dark": "#1fbe8b"},
                 "Parcial": {"light": "#e0a000", "dark": "#f0b52a"},
                 "No": {"light": "#d4625a", "dark": "#e58078"},
                 "No verificado": {"light": "#6f767e", "dark": "#9aa2ab"}},
             "controls": [],
             "unidad": "municipios"},
            {"id": "tra-nivel", "type": "bar",
             "title": "El Ejecutivo provincial frente a los municipios",
             "descr": ("Cumplimiento de cada criterio en una escala de 0 a 100: la provincia "
                       "vale 100 si publica, 50 si publica en parte y 0 si no; los municipios "
                       "son el promedio de los 60. La brecha entre niveles es grande, pero en "
                       "acceso a la información la provincia está detrás de tres municipios."),
             "x": "criterio", "seriesBy": "nivel", "metrica": "puntaje_pct",
             "fixed": {}, "yMax": 100,
             "controls": [],
             "unidad": "/100"},
            {"id": "tra-municipios", "type": "barh",
             "title": "Municipios con puntaje",
             "descr": ("Sólo los municipios que superan el cero: son 11 de 60. Cinco de ellos "
                       "tienen 5 puntos, que vienen únicamente del boletín. Los otros 49 "
                       "municipios quedan en 0; a 40 de ellos no se les halló un sitio "
                       "oficial."),
             "x": "municipio", "seriesBy": None, "metrica": "transparencia",
             "fixed": {"nivel": "Municipio"},
             "controls": [],
             "sort": "desc", "unidad": "/100"},
        ],
    },
    # ======================================================================
    {
        "id": "energia-electrica",
        "ciiu": "D",
        "area": "energia",
        "eje_pdes": "economico-productivo",
        "title": "Energía eléctrica",
        "resumen": (
            "Generación de energía eléctrica en Salta según CAMMESA: la matriz por fuente (hidráulica, "
            "térmica y renovable), la evolución de la generación por central y la potencia instalada, "
            "desde 2019. El peso de las renovables se sigue en el tablero de Energías renovables."
        ),
        "resumen_corto": "Generación eléctrica total, por fuente y por central, y potencia instalada.",
        "fuente": "CAMMESA — Informe de síntesis mensual",
        "fuente_url": "https://cammesaweb.cammesa.com/",
        "cobertura": "2019–2026",
        "keywords": [
            "energía", "electricidad", "generación eléctrica", "matriz energética", "hidráulica",
            "térmica", "renovable", "CAMMESA", "GWh", "MW", "potencia instalada", "centrales",
            "central", "usina", "infraestructura energética",
        ],
        "tags": ["infraestructura-logistica", "actividad-productividad"],
        "kpis": [
            {"ficha": "IV.1", "label": "Generación eléctrica total", "metrica": "generacion_gwh",
             "fixed": {"grano": "trimestral"}, "cmp": "quarter", "year": "latest",
             "unidad": "GWh", "format": "int"},
            {"tipo": "oferta", "ficha": "IV.2", "label": "Potencia instalada", "tabla_nota": "Es un stock (fotografía), no un flujo: no corresponde variación interanual.",
             "metrica": "potencia_mw",
             "fixed": {"grano": "anual"}, "year": "latest", "unidad": "MW", "format": "int"},
        ],
        "charts": [
            {"id": "elec-fuente", "type": "stacked-area",
             "title": "Generación eléctrica por fuente",
             "descr": "Energía generada en Salta, apilada por fuente (GWh).",
             "x": "trimestre", "seriesBy": "fuente", "metrica": "generacion_gwh",
             "fixed": {"grano": "trimestral"}, "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "GWh"},
            {"id": "elec-central", "type": "stacked-area",
             "title": "Generación por central",
             "descr": "Evolución de la energía generada por cada central eléctrica de la provincia "
                      "(GWh por año), apilada. La vista de grilla compara las centrales una a una.",
             "x": "anio", "seriesBy": "central", "metrica": "gen_central_gwh",
             "fixed": {}, "stack": True, "geoDim": "central",
             "controls": [
                 {"dim": "central", "label": "Central", "kind": "select", "all": True},
             ],
             "unidad": "GWh"},
            {"id": "elec-potencia", "type": "barh",
             "title": "Potencia instalada por central",
             "descr": "Potencia eléctrica instalada por central (última información disponible).",
             "x": "central", "seriesBy": None, "metrica": "potencia_mw",
             "fixed": {"grano": "anual"},
             "controls": [],
             "sort": "desc", "unidad": "MW"},
        ],
    },
    # ======================================================================
    {
        "id": "id-innovacion",
        "ciiu": "M",
        "area": "ciencia",
        "eje_pdes": "economico-productivo",
        "title": "Inversión en I+D",
        "resumen": (
            "Inversión provincial en investigación y desarrollo (I+D) de Salta, en pesos corrientes "
            "y constantes, y el personal dedicado a I+D (investigadores/as, becarios/as y personal "
            "técnico), según RICyT/MINCyT, desde 2017 (personal desde 2003)."
        ),
        "resumen_corto": "Inversión y personal en investigación y desarrollo.",
        "fuente": "RICyT / MINCyT — Indicadores de ciencia y tecnología",
        "fuente_url": "https://www.argentina.gob.ar/ciencia/indicadorescti",
        "cobertura": "2003–2024",
        "keywords": [
            "I+D", "investigación", "desarrollo", "innovación", "ciencia", "tecnología", "CONICET",
            "investigadores", "becarios", "MINCyT", "RICyT", "inversión en conocimiento",
        ],
        "tags": ["innovacion-mercados"],
        "kpis": [
            {"tipo": "oferta", "ficha": "V.3", "label": "Inversión en I+D (millones de $ de 2017)", "metrica": "inv_id_real",
             "fixed": {}, "year": "latest", "unidad": "millones de $", "format": "int"},
            {"tipo": "oferta", "ficha": "V.4", "label": "Investigadores/as y becarios/as", "metrica": "personal_id",
             "fixed": {"funcion": "Investigadores y becarios"}, "year": "latest",
             "unidad": "personas", "format": "int"},
        ],
        "charts": [
            {"id": "id-inversion", "type": "line",
             "title": "Inversión en I+D",
             "descr": "Inversión provincial en investigación y desarrollo.",
             "x": "anio", "seriesBy": None, "metrica": "inv_id_real", "fixed": {},
             "controls": [
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "inv_id_corr"},
                     {"value": "real", "label": "Constantes (2017)", "metric": "inv_id_real"}]},
             ],
             "unidad": "millones de $"},
            {"id": "id-personal", "type": "stacked-bar",
             "title": "Personal en I+D por función",
             "descr": "Personas dedicadas a I+D, según investigadores/becarios y personal técnico y de apoyo.",
             "x": "anio", "seriesBy": "funcion", "metrica": "personal_id", "fixed": {}, "stack": True,
             "controls": [],
             "unidad": "personas"},
        ],
    },

    # ======================================================================
    {
        "id": "exportaciones",
        "area": "economico",
        "eje_pdes": "economico-productivo",
        "title": "Exportaciones",
        "resumen": (
            "Exportaciones de la provincia de Salta desde 2021: cuánto se vendió al exterior, qué "
            "productos y a qué países, en valor (dólares FOB) y en volumen (toneladas)."
        ),
        "resumen_corto": "Qué exporta Salta, a qué países y por cuánto.",
        "fuente": "INDEC — Comercio Exterior (COMEX), base anual por provincia de origen",
        "fuente_url": "https://comex.indec.gob.ar/#/database",
        "cobertura": "2021–2025",
        "keywords": [
            "exportaciones", "comercio exterior", "exportar", "destinos", "mercados externos",
            "países", "dólares", "FOB", "divisas", "toneladas", "volumen exportado",
            "productos primarios", "manufacturas", "MOA", "MOI", "combustibles",
            "legumbres", "poroto", "maíz", "tabaco", "soja", "litio", "borato", "vino",
            "Estados Unidos", "China", "Brasil", "Bélgica", "Chile", "Vietnam",
            "inserción internacional", "diversificación", "secreto estadístico", "INDEC", "COMEX",
        ],
        "tags": ["innovacion-mercados", "actividad-productividad"],
        "kpis": [
            {"ficha": "V.1", "label": "Exportaciones totales", "metrica": "fob_usd",
             "fixed": {}, "year": "latest", "unidad": "USD", "format": "int"},
            {"ficha": "V.2", "label": "Volumen exportado", "metrica": "peso_ton",
             "fixed": {}, "year": "latest", "unidad": "toneladas", "format": "int"},
        ],
        "charts": [
            {"id": "expo-total", "type": "line",
             "title": "Exportaciones totales, en dólares FOB",
             "descr": "Valor total exportado por Salta cada año. El botón de medida permite ver el "
                      "volumen en toneladas: si el valor sube y el volumen no, la mejora vino de "
                      "los precios y no de una mayor cantidad vendida.",
             "x": "anio", "seriesBy": None, "metrica": "fob_usd", "fixed": {},
             "controls": [
                 {"kind": "mode", "label": "Medida", "default": "usd", "options": [
                     {"value": "usd", "label": "Dólares FOB", "metric": "fob_usd"},
                     {"value": "ton", "label": "Toneladas", "metric": "peso_ton", "unidad": "toneladas"}]},
             ],
             "unidad": "USD"},
            {"id": "expo-gran-rubro", "type": "stacked-area",
             "title": "Composición por tipo de producto, en dólares FOB",
             "descr": "Cómo se reparte lo exportado entre productos primarios, manufacturas de "
                      "origen agropecuario e industrial y combustibles. En '% del total' se lee la "
                      "estructura: cuánto pesa cada tipo de producto, más allá de si el total creció.",
             "x": "anio", "seriesBy": "gran_rubro", "metrica": "fob_usd", "fixed": {}, "stack": True,
             "controls": [
                 {"kind": "mode", "label": "Medida", "default": "usd", "options": [
                     {"value": "usd", "label": "Dólares FOB", "metric": "fob_usd"},
                     {"value": "ton", "label": "Toneladas", "metric": "peso_ton", "unidad": "toneladas"},
                     {"value": "pct", "label": "% del total", "metric": "fob_usd", "percent": True, "unidad": "%"}]},
             ],
             "unidad": "USD"},
            {"id": "expo-rubro-ranking", "type": "barh",
             "title": "Ranking de productos exportados",
             "descr": "Rubros ordenados por valor exportado en el año elegido, en dólares FOB. "
                      "Las categorías 'Confidencial' son operaciones cuyo producto no "
                      "se publica por secreto estadístico: se muestran porque su magnitud es parte "
                      "de la lectura, no porque sean un producto.",
             "x": "rubro", "seriesBy": None, "metrica": "fob_usd", "fixed": {},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Medida", "default": "usd", "options": [
                     {"value": "usd", "label": "Dólares FOB", "metric": "fob_usd"},
                     {"value": "ton", "label": "Toneladas", "metric": "peso_ton", "unidad": "toneladas"}]},
             ],
             "sort": "desc", "unidad": "USD"},
            {"id": "expo-continente", "type": "stacked-area",
             "title": "Composición por continente de destino, en dólares FOB",
             "descr": "A qué región del mundo se vende. En '% del total' se ve si la provincia "
                      "diversifica destinos o los concentra.",
             "x": "anio", "seriesBy": "continente", "metrica": "fob_usd", "fixed": {}, "stack": True,
             "controls": [
                 {"kind": "mode", "label": "Medida", "default": "usd", "options": [
                     {"value": "usd", "label": "Dólares FOB", "metric": "fob_usd"},
                     {"value": "ton", "label": "Toneladas", "metric": "peso_ton", "unidad": "toneladas"},
                     {"value": "pct", "label": "% del total", "metric": "fob_usd", "percent": True, "unidad": "%"}]},
             ],
             "unidad": "USD"},
            {"id": "expo-destino-ranking", "type": "barh",
             "title": "Principales países de destino",
             "descr": "Los 15 destinos de mayor valor en el año elegido, en dólares FOB. "
                      "Salta exportó a 146 países en el período; el resto queda fuera del gráfico.",
             "x": "pais_destino", "seriesBy": None, "metrica": "fob_usd", "fixed": {},
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Medida", "default": "usd", "options": [
                     {"value": "usd", "label": "Dólares FOB", "metric": "fob_usd"},
                     {"value": "ton", "label": "Toneladas", "metric": "peso_ton", "unidad": "toneladas"}]},
             ],
             "sort": "desc", "topN": 15, "unidad": "USD"},
        ],
    },
    # ======================================================================
    {
        "id": "salud",
        "subeje": "Salud",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Salud",
        "resumen": (
            "Cuánta gente nace y muere en Salta cada año, de qué manera (mortalidad infantil, "
            "materna y fetal, peso al nacer) y cuánta atención presta el sistema público: "
            "consultas médicas por habitante, camas disponibles, ocupación y egresos "
            "hospitalarios. Los nacimientos se abren por departamento y por Área Operativa de "
            "residencia; la internación, por departamento para el último año disponible."
        ),
        "resumen_corto": "Nacimientos, defunciones, tasas vitales y actividad hospitalaria.",
        "fuente": "Programa de Estadísticas de Información en Salud — Ministerio de Salud Pública de Salta",
        # Datos provistos por el MSP a solicitud; NO están publicados en un portal → sin enlace a la fuente.
        "fuente_url": "",
        "cobertura": "2020–2025",
        "keywords": [
            "salud", "sanitario", "hospital", "hospitales", "establecimientos asistenciales",
            "nacimientos", "nacidos vivos", "natalidad", "partos", "peso al nacer",
            "bajo peso", "defunciones", "muertes", "mortalidad", "mortalidad infantil",
            "mortalidad materna", "mortalidad neonatal", "defunciones fetales", "TMI",
            "matrimonios", "estadísticas vitales", "hechos vitales", "consultas médicas",
            "camas", "ocupación de camas", "giro de camas", "internación", "egresos",
            "área operativa", "esperanza de vida", "Ministerio de Salud Pública",
        ],
        "kpis": [
            {"label": "Nacidos vivos", "metrica": "nacidos_vivos",
             "fixed": {"departamento": "Salta", "desagregacion": "Total"}, "year": "latest",
             "unidad": "nacimientos", "format": "int", "sentido": "neutro",
             # La serie provincial es por lugar de OCURRENCIA y no se abre; la apertura
             # territorial existe en `nacidos_vivos_res`, por departamento de RESIDENCIA.
             "geo": "Departamento",
             "geo_nota": "23 departamentos con datos, por departamento de residencia de la madre"},
            {"label": "Defunciones", "metrica": "defunciones",
             "fixed": {"departamento": "Salta", "desagregacion": "Total"}, "year": "latest",
             "unidad": "defunciones", "format": "int", "sentido": "menor_mejor"},
            {"label": "Tasa de mortalidad infantil",
             "tabla_label": "Tasa de mortalidad infantil (por mil nacidos vivos)",
             "tabla_nota": "Defunciones de menores de 1 año cada 1.000 nacidos vivos. La variación "
                           "va en puntos, no en porcentaje: es un cociente.",
             "metrica": "tasa_mortalidad_infantil",
             "fixed": {"departamento": "Salta", "desagregacion": "Total"}, "year": "latest",
             "unidad": "por mil nacidos vivos", "format": "int", "display": "nivel",
             "sentido": "menor_mejor"},
            {"tipo": "oferta", "label": "Consultas médicas por habitante", "metrica": "consultas_por_habitante",
             "fixed": {"departamento": "Salta"}, "year": "latest",
             "unidad": "consultas/hab.", "format": "int", "display": "nivel",
             "sentido": "neutro"},
            {"tipo": "oferta", "label": "Ocupación de camas",
             "tabla_label": "Ocupación de camas en establecimientos públicos",
             "metrica": "ocupacion_camas",
             "fixed": {"departamento": "Salta"}, "year": "latest",
             "unidad": "%", "format": "int", "display": "nivel", "sentido": "neutro"},
        ],
        "charts": [
            {"id": "sal-hechos-vitales", "type": "line",
             "title": "Nacimientos, defunciones y matrimonios",
             "descr": "Hechos vitales registrados en la provincia cada año.",
             "x": "anio", "seriesBy": None, "metrica": "nacidos_vivos",
             "fixed": {"departamento": "Salta", "desagregacion": "Total"},
             "controls": [{"kind": "metric", "label": "Hecho vital",
                           "options": ["nacidos_vivos", "defunciones", "matrimonios",
                                       "defunciones_fetales", "defunciones_maternas"]}],
             "unidad": "casos"},
            {"id": "sal-tasas", "type": "line",
             "title": "Tasas vitales",
             "descr": "Natalidad y mortalidad general por mil habitantes; mortalidad infantil por "
                      "mil nacidos vivos y materna por diez mil.",
             "x": "anio", "seriesBy": None, "metrica": "tasa_mortalidad_infantil",
             "fixed": {"departamento": "Salta", "desagregacion": "Total"},
             "controls": [{"kind": "metric", "label": "Tasa",
                           "options": ["tasa_mortalidad_infantil", "tasa_natalidad",
                                       "tasa_mortalidad_general", "tasa_mortalidad_materna"]}],
             "unidad": "por mil"},
            {"id": "sal-mortalidad-infantil", "type": "stacked-bar",
             "title": "Mortalidad infantil por momento de la defunción",
             "descr": "Defunciones de menores de 1 año, separadas entre neonatales (antes de los "
                      "28 días de vida) y posneonatales.",
             "x": "anio", "seriesBy": "desagregacion", "metrica": "defunciones_infantiles",
             "fixed": {"departamento": "Salta"}, "seriesExclude": ["Total"], "stack": True,
             "controls": [],
             "unidad": "defunciones"},
            {"id": "sal-peso-nacer", "type": "stacked-bar",
             "title": "Nacidos vivos por peso al nacer",
             "descr": "Cuántos nacimientos son de bajo peso (menos de 2.500 gramos), un indicador "
                      "temprano de riesgo para la salud del recién nacido.",
             "x": "anio", "seriesBy": "desagregacion", "metrica": "nacidos_vivos",
             "fixed": {"departamento": "Salta"}, "seriesExclude": ["Total"], "stack": True,
             "controls": [
                 {"kind": "mode", "label": "Valores", "default": "abs", "options": [
                     {"value": "abs", "label": "Nacimientos", "metric": "nacidos_vivos"},
                     {"value": "pct", "label": "% del total", "metric": "nacidos_vivos",
                      "percent": True, "unidad": "%"}]},
             ],
             "unidad": "nacimientos"},
            {"id": "sal-nv-depto", "type": "barh",
             "title": "Nacidos vivos por departamento",
             "descr": "Ranking de departamentos por nacimientos, según el departamento de "
                      "residencia de la madre, para el año seleccionado.",
             "x": "departamento", "seriesBy": None, "metrica": "nacidos_vivos_res", "fixed": {},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "nacimientos"},
            {"id": "sal-nv-serie", "type": "line",
             "title": "Nacidos vivos en el tiempo, por departamento",
             "descr": "Serie de nacimientos por departamento de residencia. La vista de grilla "
                      "compara los 23 departamentos a la vez.",
             "x": "anio", "seriesBy": None, "metrica": "nacidos_vivos_res", "fixed": {},
             "geoDim": "departamento",
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "nacimientos"},
            {"id": "sal-nv-ao", "type": "barh",
             "title": "Nacidos vivos por Área Operativa de residencia",
             "descr": "Apertura original de la fuente: la circunscripción sanitaria de cada "
                      "hospital cabecera, más fina que el departamento. Las 20 mayores.",
             "x": "area_operativa", "seriesBy": None, "metrica": "nacidos_vivos_res", "fixed": {},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "topN": 20, "unidad": "nacimientos"},
            {"id": "sal-consultas", "type": "line",
             "title": "Consultas médicas",
             "descr": "Consultas atendidas en el subsector público y su relación con la población "
                      "estimada de la provincia.",
             "x": "anio", "seriesBy": None, "metrica": "consultas_por_habitante",
             "fixed": {"departamento": "Salta"},
             "controls": [{"kind": "metric", "label": "Medida",
                           "options": ["consultas_por_habitante", "consultas_medicas"]}],
             "unidad": "consultas/hab."},
            {"id": "sal-internacion", "type": "line",
             "title": "Internación en establecimientos públicos",
             "descr": "Rendimiento de la red pública de internación: camas disponibles, cuánto se "
                      "usan y cuántos pacientes egresan.",
             "x": "anio", "seriesBy": None, "metrica": "ocupacion_camas",
             "fixed": {"departamento": "Salta", "desagregacion": "Total"},
             "controls": [{"kind": "metric", "label": "Indicador",
                           "options": ["ocupacion_camas", "camas_disponibles", "egresos",
                                       "giro_camas", "permanencia_promedio",
                                       "tasa_mortalidad_hospitalaria"]}],
             "unidad": "%"},
            {"id": "sal-internacion-depto", "type": "barh",
             "title": "Internación por departamento (2025)",
             "descr": "Los 53 establecimientos públicos con internación, agregados a su "
                      "departamento. La fuente publica este detalle sólo para 2025, por eso el "
                      "año está fijo. Los cocientes se recalculan sobre los totales del "
                      "departamento, no se promedian entre hospitales.",
             "x": "departamento", "seriesBy": None, "metrica": "ocupacion_camas",
             "fixed": {"anio": 2025},
             "controls": [{"kind": "metric", "label": "Indicador",
                           "options": ["ocupacion_camas", "camas_disponibles", "egresos",
                                       "giro_camas", "permanencia_promedio",
                                       "tasa_mortalidad_hospitalaria"]}],
             "sort": "desc", "unidad": "%"},
        ],
    },
    # ======================================================================
    # Temas sociales (Dimensiones I-IV de las notas técnicas de indicadores sociales):
    # xlsx estáticos, un corte por departamento. Los KPIs muestran el NIVEL (no hay
    # período previo con qué comparar), salvo la tasa anual de suicidio.
    # ======================================================================
    {
        "id": "condiciones-vida",
        # Fuente CNPV: la frecuencia es intercensal, no anual. Esta planilla sólo trae 2022, así
        # que la variación queda «sin base»; la comparación con 2010 está en «pdes-privacion».
        "frecuencia": "Intercensal",
        "subeje": "Condiciones de vida",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Condiciones de vida de los hogares",
        "resumen": (
            "Qué proporción de los hogares de cada departamento tiene necesidades básicas "
            "insatisfechas (NBI), vive en hacinamiento, no tiene agua por cañería o inodoro con "
            "descarga, no es dueña de su vivienda o no tiene computadora ni internet. Datos del "
            "Censo 2022: es una foto, no una serie."
        ),
        "resumen_corto": "Privación material de los hogares (NBI, vivienda, servicios, TIC), por departamento.",
        "fuente": "CESS sobre la base del Censo Nacional de Población, Hogares y Viviendas 2022 (INDEC/REDATAM)",
        "fuente_url": "https://redatam.indec.gob.ar/",
        "cobertura": "2022 (Censo)",
        "keywords": [
            "condiciones de vida", "pobreza estructural", "NBI", "necesidades básicas insatisfechas",
            "hacinamiento", "vivienda", "agua", "agua potable", "cañería", "inodoro", "baño",
            "saneamiento", "tenencia de la vivienda", "propietarios", "inquilinos", "clima educativo",
            "computadora", "tablet", "internet", "celular", "brecha digital", "hogares", "censo 2022",
            "privación",
        ],
        "kpis": [
            {"ficha": "I.1", "label": "Hogares con NBI", "metrica": "pct_hogares",
             "fixed": {"departamento": "Salta", "indicador": "NBI"}, "year": "latest",
             "unidad": "% de hogares", "format": "int", "display": "nivel", "sentido": "menor_mejor",
             "meta_2030": 10, "meta_2030_nota": "El PDES fija la meta al Censo 2030."},
            {"ficha": "I.2", "label": "Hogares con hacinamiento crítico", "metrica": "pct_hogares",
             "fixed": {"departamento": "Salta", "indicador": "Hacinamiento crítico"}, "year": "latest",
             "unidad": "% de hogares", "format": "int", "display": "nivel", "sentido": "menor_mejor",
             "meta_2030": 4, "meta_2030_nota": "El PDES fija la meta al Censo 2030."},
            {"ficha": "I.6", "label": "Hogares sin agua por cañería en la vivienda", "metrica": "pct_hogares",
             "fixed": {"departamento": "Salta", "indicador": "Sin agua por cañería en la vivienda"},
             "year": "latest", "unidad": "% de hogares", "format": "int", "display": "nivel",
             "sentido": "menor_mejor",
             # Sin meta: la del PDES es de cobertura de agua de RED (93 %) y pasó al indicador
             # de personas sin agua de red pública del tablero «pdes-privacion».
             "tabla_nota": "Agua por cañería dentro de la vivienda, cualquiera sea su "
                           "procedencia. La meta del PDES de agua de red está en el indicador "
                           "de personas sin agua de red pública."},
            {"ficha": "I.10", "label": "Hogares sin internet en la vivienda", "metrica": "pct_hogares",
             "fixed": {"departamento": "Salta", "indicador": "Sin internet en la vivienda"},
             "year": "latest", "unidad": "% de hogares", "format": "int", "display": "nivel",
             "sentido": "menor_mejor"},
            {"ficha": "I.5", "label": "Hogares con clima educativo bajo", "metrica": "pct_hogares",
             "tabla_label": "Hogares con clima educativo bajo o muy bajo",
             "fixed": {"departamento": "Salta", "indicador": "Clima educativo bajo o muy bajo"},
             "year": "latest", "unidad": "% de hogares", "format": "int", "display": "nivel",
             "sentido": "menor_mejor"},
        ],
        "charts": [
            {"id": "cv-ranking", "type": "barh",
             "title": "Privación de los hogares por departamento",
             "descr": "Ranking de departamentos según la carencia elegida. Censo 2022.",
             "x": "departamento", "seriesBy": None, "metrica": "pct_hogares", "fixed": {},
             "controls": [
                 {"dim": "indicador", "label": "Carencia", "kind": "select", "default": "NBI"},
                 {"kind": "metric", "label": "Valores", "options": ["pct_hogares", "hogares_priv"]},
             ],
             "sort": "desc", "unidad": "% de hogares"},
            {"id": "cv-perfil", "type": "barh",
             "title": "Perfil de carencias",
             "descr": "Todas las carencias juntas, para la provincia o el departamento elegido.",
             "x": "indicador", "seriesBy": None, "metrica": "pct_hogares", "fixed": {},
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "sort": "desc", "unidad": "% de hogares"},
        ],
    },
    # ======================================================================
    {
        "id": "salud-reproduccion",
        "subeje": "Salud",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Salud y reproducción por departamento",
        "resumen": (
            "Cuánto vive y de qué muere la población de cada departamento: esperanza de vida, "
            "mortalidad general y ajustada por edad, mortalidad prematura, infantil y materna, "
            "y por enfermedades cardiovasculares, cáncer y diabetes. Suma la fecundidad, incluida "
            "la adolescente. Son tasas medias del trienio 2021-2023: una foto, no una serie."
        ),
        "resumen_corto": "Esperanza de vida, mortalidad y fecundidad por departamento (2021-2023).",
        "fuente": "CESS sobre la base de defunciones y nacimientos 2021-2023 (DEIS, Ministerio de Salud) y Censo 2022 (INDEC)",
        "fuente_url": "https://www.argentina.gob.ar/salud/deis",
        "cobertura": "2021–2023 (trienio)",
        "keywords": [
            "salud", "esperanza de vida", "mortalidad", "tasa de mortalidad", "mortalidad ajustada",
            "mortalidad prematura", "años potenciales de vida perdidos", "APVP", "mortalidad infantil",
            "TMI", "mortalidad materna", "menores de 5", "bajo peso al nacer", "cardiovascular",
            "cáncer", "diabetes", "fecundidad", "natalidad", "embarazo adolescente",
            "madres adolescentes", "maternidad", "brecha territorial", "DEIS",
        ],
        "kpis": [
            {"ficha": "II.1", "label": "Esperanza de vida al nacer", "metrica": "esperanza_vida",
             "fixed": {"departamento": "Salta", "sexo": "Total"}, "year": "latest",
             "unidad": "años", "format": "int", "display": "nivel", "sentido": "mayor_mejor"},
            # II.8 (mortalidad infantil) pasó al tablero «pdes-salud»: trienios 2018-20 y 2021-23.
            {"ficha": "II.7", "label": "Mortalidad materna", "metrica": "rmm", "fixed": {"departamento": "Salta"},
             "year": "latest", "unidad": "por cien mil nacidos vivos", "format": "int",
             "display": "nivel", "sentido": "menor_mejor"},
            {"ficha": "II.5", "label": "Mortalidad prematura (30 a 69 años)", "metrica": "mort_prematura",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "por cien mil hab.",
             "format": "int", "display": "nivel", "sentido": "menor_mejor"},
            # II.18 (fecundidad adolescente) pasó al tablero «pdes-salud».
        ],
        "charts": [
            {"id": "sr-vida-mortalidad", "type": "barh",
             "title": "Esperanza de vida y mortalidad general",
             "descr": "Ranking de departamentos. La mortalidad ajustada por edad permite comparar "
                      "departamentos con poblaciones de distinta edad; la razón compara cada uno "
                      "contra la provincia (1 = igual).",
             "x": "departamento", "seriesBy": None, "metrica": "esperanza_vida", "fixed": {},
             "controls": [
                 {"kind": "metric", "label": "Indicador",
                  "options": ["esperanza_vida", "tasa_mort_ajustada", "tasa_bruta_mort",
                              "razon_brecha_mort"]},
                 {"dim": "sexo", "label": "Sexo", "kind": "select", "default": "Total"},
             ],
             "sort": "desc", "unidad": "años"},
            {"id": "sr-sexo", "type": "bar",
             "title": "Varones y mujeres por departamento",
             "descr": "La brecha entre sexos en esperanza de vida y mortalidad.",
             "x": "departamento", "seriesBy": "sexo", "metrica": "esperanza_vida", "fixed": {},
             "seriesExclude": ["Total"],
             "controls": [
                 {"kind": "metric", "label": "Indicador",
                  "options": ["esperanza_vida", "tasa_mort_ajustada", "tasa_bruta_mort"]},
             ],
             "unidad": "años"},
            {"id": "sr-causas", "type": "barh",
             "title": "Mortalidad prematura y por causas",
             "descr": "Tasas medias anuales por cien mil habitantes, trienio 2021-2023.",
             "x": "departamento", "seriesBy": None, "metrica": "mort_prematura", "fixed": {},
             "controls": [
                 {"kind": "metric", "label": "Indicador",
                  "options": ["mort_prematura", "apvp", "mort_cardiovascular", "mort_cancer",
                              "mort_diabetes"]},
             ],
             "sort": "desc", "unidad": "por cien mil hab."},
            {"id": "sr-materno-infantil", "type": "barh",
             "title": "Salud materno-infantil",
             "descr": "Mortalidad infantil, de menores de 5 años y materna, y bajo peso al nacer. "
                      "En departamentos con pocos nacimientos un solo caso mueve mucho la tasa.",
             "x": "departamento", "seriesBy": None, "metrica": "tmi", "fixed": {},
             "controls": [
                 {"kind": "metric", "label": "Indicador",
                  "options": ["tmi", "mort_menores5", "rmm", "pct_bajo_peso"]},
             ],
             "sort": "desc", "unidad": "por mil nacidos vivos"},
            {"id": "sr-fecundidad", "type": "barh",
             "title": "Fecundidad",
             "descr": "Hijos por mujer, nacimientos por mujer en edad fértil y fecundidad adolescente.",
             "x": "departamento", "seriesBy": None, "metrica": "tgf", "fixed": {},
             "controls": [
                 {"kind": "metric", "label": "Indicador",
                  "options": ["tgf", "tasa_gral_fec", "fec_15_19", "fec_10_14",
                              "pct_madres_adolesc", "edad_media_mat"]},
             ],
             "sort": "desc", "unidad": "hijos por mujer"},
            {"id": "sr-tef", "type": "bar",
             "title": "Fecundidad por edad de la madre",
             "descr": "Nacimientos por cada mil mujeres de cada grupo de edad.",
             "x": "edad", "seriesBy": None, "metrica": "tef", "fixed": {},
             "seriesExclude": ["Total"], "exclude": ["Total"],
             "controls": [
                 {"dim": "departamento", "label": "Departamento", "kind": "select",
                  "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
             ],
             "unidad": "por mil mujeres"},
        ],
    },
    # ======================================================================
    {
        "id": "educacion-aprendizajes",
        "subeje": "Educación",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Trayectorias y aprendizajes por departamento",
        "resumen": (
            "Cómo avanzan los alumnos de primaria y secundaria en cada departamento (repitencia, "
            "egreso, alumnos por escuela y por docente) y qué aprenden: resultados de las pruebas "
            "Aprender de 6.º grado en Lengua y Matemática, sobreedad y nivel socioeconómico. "
            "Datos de 2025: una foto, no una serie."
        ),
        "resumen_corto": "Repitencia, egreso y resultados Aprender 2025, por departamento.",
        "fuente": "CESS sobre la base del Relevamiento Anual 2025 y Aprender 2025 (Ministerio de Educación de la Nación)",
        "fuente_url": "https://www.argentina.gob.ar/educacion/evaluacion-informacion-educativa",
        "cobertura": "2025",
        "keywords": [
            "educación", "aprendizajes", "Aprender", "pruebas Aprender", "lengua", "matemática",
            "desempeño", "satisfactorio", "repitencia", "egreso", "tasa de egreso", "sobreedad",
            "nivel socioeconómico", "alumnos por docente", "alumnos por escuela", "extranjeros",
            "primaria", "secundaria", "6to grado", "calidad educativa",
        ],
        "kpis": [
            # III.2 (repitencia en secundaria) pasó al tablero «pdes-educacion»: 2018 y 2025.
            {"ficha": "III.3", "label": "Tasa de egreso aparente de secundaria", "metrica": "tasa_egreso_aparente",
             "fixed": {"departamento": "Salta", "nivel": "Secundaria"}, "year": "latest",
             "unidad": "%", "format": "int", "display": "nivel", "sentido": "mayor_mejor"},
            {"ficha": "III.7", "label": "Lengua: satisfactorio o avanzado", "metrica": "pct_satisf_lengua",
             "tabla_label": "Aprender 6.º grado, Lengua: alumnos en nivel satisfactorio o avanzado",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "% de alumnos",
             "format": "int", "display": "nivel", "sentido": "mayor_mejor"},
            # III.8 (Aprender Matemática) pasó al tablero «pdes-educacion»: 2018 y 2025.
        ],
        "charts": [
            {"id": "ea-trayectorias", "type": "barh",
             "title": "Trayectorias escolares y recursos",
             "descr": "Ranking de departamentos para el nivel elegido. Relevamiento Anual 2025.",
             "x": "departamento", "seriesBy": None, "metrica": "pct_repitencia", "fixed": {},
             "controls": [
                 {"kind": "metric", "label": "Indicador",
                  "options": ["pct_repitencia", "tasa_egreso_aparente", "alumnos_cargo",
                              "alumnos_establecimiento", "pct_extranjeros", "matricula"]},
                 {"dim": "nivel", "label": "Nivel", "kind": "select", "default": "Secundaria"},
             ],
             "sort": "desc", "unidad": "% de la matrícula"},
            {"id": "ea-aprender-ranking", "type": "barh",
             "title": "Aprender 2025: alumnos con desempeño satisfactorio o avanzado",
             "descr": "Alumnos de 6.º grado que alcanzan al menos el nivel satisfactorio. Los "
                      "departamentos sin dato confiable no aparecen.",
             "x": "departamento", "seriesBy": None, "metrica": "pct_satisf_lengua", "fixed": {},
             "controls": [
                 {"kind": "metric", "label": "Área", "options": ["pct_satisf_lengua", "pct_satisf_mat"]},
             ],
             "sort": "desc", "unidad": "% de alumnos"},
            {"id": "ea-aprender-dist", "type": "stacked-bar",
             "title": "Aprender 2025: distribución de los alumnos de 6.º grado",
             "descr": "Cómo se reparten los alumnos entre niveles de desempeño, años de sobreedad "
                      "o quintiles de nivel socioeconómico, en cada departamento.",
             "x": "departamento", "seriesBy": "categoria", "metrica": "aprender_lengua",
             "fixed": {}, "seriesExclude": ["Total"], "stack": True, "yMax": 100,
             "controls": [
                 {"kind": "metric", "label": "Distribución",
                  "options": ["aprender_lengua", "aprender_matematica", "aprender_sobreedad",
                              "aprender_nse"]},
             ],
             "unidad": "% de alumnos"},
        ],
    },
    # ======================================================================
    {
        "id": "seguridad",
        "subeje": "Seguridad",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Seguridad: suicidios y siniestros viales",
        "resumen": (
            "Cuántas personas mueren por suicidio y por lesiones de tránsito en Salta. Incluye "
            "la serie anual provincial de suicidios desde 2017, las tasas por departamento, "
            "sexo y edad (adolescentes), y cómo y dónde ocurren. La mortalidad por tránsito es la "
            "media del trienio 2021-2023."
        ),
        "resumen_corto": "Suicidios (2017-2024) y mortalidad por lesiones de tránsito, por departamento.",
        "fuente": ("CESS sobre la base del Sistema de Alerta Temprana de Suicidios (SATSSBU, "
                   "suicidios 2017-2024), DEIS (defunciones 2021-2023) y Censo 2022 (INDEC)"),
        "fuente_url": "",
        "cobertura": "2017–2024",
        "keywords": [
            "seguridad", "suicidio", "suicidios", "salud mental", "suicidio adolescente",
            "adolescentes", "razón de masculinidad", "ahorcamiento", "lesiones de tránsito",
            "siniestros viales", "accidentes de tránsito", "seguridad vial", "muertes violentas",
            "causas externas", "SATSSBU",
        ],
        "kpis": [
            {"ficha": "IV.9", "label": "Tasa de suicidio", "metrica": "tasa_suicidio_anual",
             "tabla_label": "Tasa de suicidio (por cien mil habitantes)",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "por cien mil hab.",
             "format": "int", "display": "nivel", "sentido": "menor_mejor",
             "geo": "Provincia"},
            {"ficha": "IV.5", "label": "Tasa de suicidio adolescente (10 a 19)", "metrica": "tasa_suicidio_adolesc",
             "fixed": {"departamento": "Salta"}, "year": "latest",
             "unidad": "por cien mil hab. de 10 a 19", "format": "int", "display": "nivel",
             "sentido": "menor_mejor"},
            {"ficha": "IV.4", "label": "Razón de suicidio varones / mujeres", "metrica": "razon_masc_suicidio",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "veces",
             "format": "int", "display": "nivel", "sentido": "neutro"},
            {"ficha": "IV.10", "label": "Mortalidad por lesiones de tránsito", "metrica": "tasa_mort_transito",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "por cien mil hab.",
             "format": "int", "display": "nivel", "sentido": "menor_mejor"},
        ],
        "charts": [
            {"id": "seg-serie", "type": "line",
             "title": "Suicidios en la provincia, 2017-2024",
             "descr": "Serie provincial: por departamento los casos por año son demasiado pocos "
                      "para una tasa anual confiable. La tasa usa la población del Censo 2022.",
             "x": "anio", "seriesBy": None, "metrica": "tasa_suicidio_anual",
             "fixed": {"departamento": "Salta"},
             "controls": [{"kind": "metric", "label": "Valores",
                           "options": ["tasa_suicidio_anual", "suicidios_anual"]}],
             "unidad": "por cien mil hab."},
            {"id": "seg-ranking", "type": "barh",
             "title": "Suicidios por departamento",
             "descr": "Tasas medias anuales y composición de los casos, 2017-2024 (la tasa del "
                      "trienio, 2021-2023). En departamentos chicos pocos casos mueven mucho la tasa.",
             "x": "departamento", "seriesBy": None, "metrica": "tasa_suicidio_1724", "fixed": {},
             "controls": [
                 {"kind": "metric", "label": "Indicador",
                  "options": ["tasa_suicidio_1724", "tasa_suicidio_trienio", "tasa_suicidio_adolesc",
                              "pct_suicidio_adolesc", "razon_masc_suicidio", "pct_ahorcamiento",
                              "pct_domicilio", "suicidios_1724"]},
             ],
             "sort": "desc", "unidad": "por cien mil hab."},
            {"id": "seg-sexo", "type": "bar",
             "title": "Tasa de suicidio de varones y mujeres",
             "descr": "Tasa media anual 2017-2024 por sexo y departamento.",
             "x": "departamento", "seriesBy": "sexo", "metrica": "tasa_suicidio_1724", "fixed": {},
             "seriesExclude": ["Total"], "controls": [],
             "unidad": "por cien mil hab."},
            {"id": "seg-metodo", "type": "barh",
             "title": "Cómo y dónde ocurren los suicidios",
             "descr": "Casos en la provincia, 2017-2024.",
             "x": "categoria", "seriesBy": None, "metrica": "suicidios_metodo",
             "fixed": {"departamento": "Salta"}, "exclude": ["Total"],
             "controls": [{"kind": "metric", "label": "Según",
                           "options": ["suicidios_metodo", "suicidios_lugar"]}],
             "sort": "desc", "unidad": "casos"},
            {"id": "seg-transito", "type": "barh",
             "title": "Mortalidad por lesiones de tránsito",
             "descr": "Tasa media anual del trienio 2021-2023, no ajustada por edad.",
             "x": "departamento", "seriesBy": None, "metrica": "tasa_mort_transito", "fixed": {},
             "controls": [{"kind": "metric", "label": "Valores",
                           "options": ["tasa_mort_transito", "def_transito"]}],
             "sort": "desc", "unidad": "por cien mil hab."},
        ],
    },

    # ======================================================================
    {
        "id": "seguridad-vial",
        "subeje": "Seguridad",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Seguridad vial",
        "resumen": (
            "Muertos y heridos en siniestros viales en Salta según la Agencia Nacional de Seguridad Vial."
            " Tasas cada 100 mil habitantes y cada 10 mil vehículos"
            "Perfil de las víctimas fatales según movilidad."
        ),
        "resumen_corto": "Cuántos mueren en las rutas y las calles de Salta, y cómo se movían.",
        "advertencia": (
            "Siniestros reportados por provincia. Agencia Nacional de Seguridad Vial (ANSV)."
        ),
        "fuente": "Agencia Nacional de Seguridad Vial (ANSV)",
        "fuente_url": "https://www.argentina.gob.ar/seguridadvial/observatoriovialnacional/anuarios",
        "cobertura": "2016–2025",
        "keywords": [
            "seguridad vial", "siniestros viales", "accidentes de tránsito", "víctimas fatales",
            "muertos en accidentes", "motociclistas", "moto", "ciclistas", "bicicleta",
            "peatones", "tasa de mortalidad vial", "siniestralidad", "ANSV", "observatorio vial",
            "heridos", "lesionados", "parque automotor", "tránsito", "rutas", "casco",
        ],
        "kpis": [
            {"label": "Víctimas fatales en siniestros viales",
             "tabla_label": "Víctimas fatales en siniestros viales",
             "metrica": "victimas_fatales",
             "fixed": {"jurisdiccion": "Salta", "tipo_usuario": "Total"},
             "year": "latest", "unidad": "personas", "format": "int",
             "display": "nivel", "sentido": "menor_mejor", "geo": "Provincia"},
            {"label": "Tasa de mortalidad vial",
             "tabla_label": "Tasa de mortalidad vial (por cien mil habitantes)",
             "metrica": "tasa_mortalidad_100mil",
             "fixed": {"jurisdiccion": "Salta", "tipo_usuario": "Total"},
             "year": "latest", "unidad": "por cien mil hab.", "format": "dec1",
             "display": "nivel", "sentido": "menor_mejor", "geo": "Provincia",
             "grafico": "sv-tasa-comparada"},
            {"label": "Víctimas fatales motociclistas",
             "tabla_label": "Víctimas fatales motociclistas",
             "tabla_nota": "La ANSV dejó de abrir el tipo de usuario de la vía por jurisdicción "
                           "después de 2022, así que este indicador se detiene ahí mientras los "
                           "demás llegan a 2025.",
             "metrica": "victimas_fatales",
             "fixed": {"jurisdiccion": "Salta", "tipo_usuario": "Motociclista"},
             "year": "latest", "unidad": "personas", "format": "int",
             "display": "nivel", "sentido": "menor_mejor", "geo": "Provincia",
             "grafico": "sv-usuario"},
        ],
        "charts": [
            {"id": "sv-tasa-comparada", "type": "line",
             "title": "Mortalidad vial: Salta, el NOA y el país",
             "descr": "Víctimas fatales cada 100 mil habitantes. El NOA son las seis provincias "
                      "que agrupa la propia ANSV, y su tasa es cociente de agregados: víctimas "
                      "fatales del NOA sobre población del NOA, no promedio de las seis tasas.",
             "x": "anio", "seriesBy": "ambito", "metrica": "tasa_mortalidad_100mil",
             "fixed": {"tipo_usuario": "Total"},
             "seriesExclude": ["Otra jurisdicción"],
             "controls": [], "unidad": "por cien mil hab."},
            {"id": "sv-salta", "type": "line",
             "title": "Víctimas y siniestros fatales en Salta",
             "descr": "Siempre hay más víctimas que siniestros, porque en un mismo hecho puede "
                      "morir más de una persona. La ANSV no abrió los siniestros fatales por "
                      "jurisdicción en 2025.",
             "x": "anio", "seriesBy": None, "metrica": "victimas_fatales",
             "fixed": {"jurisdiccion": "Salta", "tipo_usuario": "Total"},
             "controls": [{"kind": "metric", "label": "Valores",
                           "options": ["victimas_fatales", "siniestros_fatales"]}],
             "unidad": "personas"},
            {"id": "sv-usuario", "type": "stacked-area",
             "title": "Víctimas fatales según cómo se movían",
             "descr": "Cuatro de cada diez muertos en las calles y rutas de Salta iban en moto. "
                      "«Otros vehículos» incluye camioneta, utilitario, transporte de carga y de "
                      "pasajeros. Se corta en 2022, que es hasta donde la ANSV lo abre por "
                      "provincia.",
             "x": "anio", "seriesBy": "tipo_usuario", "metrica": "victimas_fatales",
             "fixed": {"jurisdiccion": "Salta"},
             "seriesExclude": ["Total"], "stack": True,
             "controls": [], "unidad": "personas"},
            {"id": "sv-vehiculos", "type": "line",
             "title": "Mortalidad vial por vehículo registrado",
             "descr": "Mirado por vehículo y no por habitante, el cuadro cambia: pesa el tamaño "
                      "del parque. Las dos tasas no son intercambiables. La de la ANSV usa el "
                      "parque total —autos, motos, acoplados y maquinarias— y se corta en 2023, "
                      "que es cuando dejó de publicarla. La otra la calcula el Monitor sobre el "
                      "parque automotor de la DNRPA, que no incluye motos: da más alta porque el "
                      "denominador es menor, pero llega hasta 2025 y su denominador está "
                      "publicado para las tres jurisdicciones.",
             "x": "anio", "seriesBy": "ambito", "metrica": "tasa_fatalidad_10mil_automotor",
             "fixed": {"tipo_usuario": "Total"},
             "seriesExclude": ["Otra jurisdicción"],
             "controls": [{"kind": "metric", "label": "Denominador",
                           "options": ["tasa_fatalidad_10mil_automotor",
                                       "tasa_fatalidad_10mil_veh"]}],
             "unidad": "por diez mil automotores"},
            {"id": "sv-ranking", "type": "barh",
             "title": "Jurisdicciones (ranking)",
             "descr": "Las 24 jurisdicciones ordenadas en el año elegido. El total del país y el "
                      "NOA quedan fuera del ranking porque son agregados.",
             "x": "jurisdiccion", "seriesBy": None, "metrica": "tasa_mortalidad_100mil",
             "fixed": {"tipo_usuario": "Total"},
             "exclude": ["Total del país", "NOA"],
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "metric", "label": "Indicador",
                  "options": ["tasa_mortalidad_100mil", "tasa_siniestralidad_fatal_100mil",
                              "tasa_fatalidad_10mil_veh", "victimas_fatales",
                              "siniestros_fatales"]},
             ],
             "sort": "desc", "unidad": "por cien mil hab."},
            {"id": "sv-lesionados", "type": "line",
             "title": "Siniestros y personas heridas en Salta",
             "descr": "Lo que no termina en muerte. Es la parte más despareja de la fuente: "
                      "depende de que cada provincia registre los siniestros con lesionados, y "
                      "varias dejaron de hacerlo. Corta en 2022.",
             "x": "anio", "seriesBy": None, "metrica": "personas_heridas",
             "fixed": {"jurisdiccion": "Salta", "tipo_usuario": "Total"},
             "controls": [{"kind": "metric", "label": "Valores",
                           "options": ["personas_heridas", "siniestros_con_lesionados",
                                       "siniestros_con_victimas"]}],
             "unidad": "personas"},
        ],
    },

    # ======================================================================
    {
        "id": "patentamiento",
        "ciiu": "G",
        "area": "economico",
        "eje_pdes": "economico-productivo",
        "title": "Patentamiento de vehículos",
        "resumen": (
            "Vehículos 0 km inscriptos y vehículos usados transferidos en Salta según los "
            "registros de la propiedad del automotor, mensual, abierto en autos, motos y "
            "maquinarias, con el parque automotor de la provincia y la tasa con que se renueva."
        ),
        "resumen_corto": "Cuántos vehículos se patentan en Salta, y cuántos de esos son motos.",
        "advertencia": (
            "El patentamiento se desploma en diciembre y se dispara en enero, todos los años y en "
            "todo el país: inscribir en enero da el año modelo nuevo y eso vale en la reventa. Es "
            "estacionalidad de la fuente, no un salto del dato, y por eso conviene mirarlo "
            "trimestral o anual. Además el parque automotor no incluye motos, así que la tasa de "
            "renovación se calcula sólo sobre autos."
        ),
        "fuente": "Dirección Nacional de los Registros Nacionales de la Propiedad del Automotor (DNRPA)",
        "fuente_url": "https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-automotores",
        "cobertura": "2000–2026",
        "keywords": [
            "patentamiento", "patentamientos", "inscripciones iniciales", "0 km", "cero kilómetro",
            "transferencias", "usados", "autos", "automóviles", "motos", "motovehículos",
            "maquinarias", "parque automotor", "DNRPA", "registro automotor", "vehículos",
            "consumo durable", "concesionarias", "venta de autos", "renovación de la flota",
        ],
        "tags": ["actividad-productividad"],
        "kpis": [
            {"label": "Vehículos patentados", "tabla_label": "Vehículos patentados (0 km)",
             "metrica": "inscripciones_iniciales",
             "fixed": {"grano": "trimestral", "categoria": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "vehículos", "format": "int",
             "geo": "Provincia"},
            {"label": "Motos patentadas", "tabla_label": "Motos patentadas (0 km)",
             "tabla_nota": "Dos de cada tres vehículos que se patentan en Salta son motos. Es el "
                           "mismo parque que explica que el 42 % de las víctimas fatales de "
                           "siniestros viales de la provincia sean motociclistas.",
             "metrica": "inscripciones_iniciales",
             "fixed": {"grano": "trimestral", "categoria": "Motos"},
             "cmp": "quarter", "year": "latest", "unidad": "vehículos", "format": "int",
             "geo": "Provincia", "grafico": "pat-categoria"},
            {"label": "Parque automotor", "tabla_label": "Parque automotor (automotores)",
             "tabla_nota": "Automotores en condiciones registrales de circular. No incluye motos: "
                           "la DNRPA no publica el parque de motovehículos.",
             "metrica": "parque_automotor",
             "fixed": {"grano": "trimestral", "categoria": "Autos"},
             "cmp": "quarter", "year": "latest", "unidad": "automotores", "format": "int",
             "geo": "Provincia", "grafico": "pat-parque"},
        ],
        "charts": [
            {"id": "pat-total", "type": "line",
             "title": "Vehículos patentados y transferidos en Salta",
             "descr": "Inscripciones iniciales son vehículos 0 km; transferencias son cambios de "
                      "titular de usados. La serie del total arranca en septiembre de 2013, que "
                      "es desde cuándo la DNRPA publica las tres categorías.",
             "x": "trimestre", "seriesBy": None, "metrica": "inscripciones_iniciales",
             "fixed": {"grano": "trimestral", "categoria": "Total"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
                 {"kind": "metric", "label": "Operación",
                  "options": ["inscripciones_iniciales", "transferencias"]},
             ],
             "unidad": "vehículos"},
            {"id": "pat-categoria", "type": "stacked-area",
             "title": "Patentamiento por tipo de vehículo",
             "descr": "Autos, motos y maquinarias, apilados. Las motos entran a la serie en 2007 "
                      "y las maquinarias en septiembre de 2013, que es cuando la DNRPA empieza a "
                      "publicarlas: antes de esas fechas la categoría no existe, no vale cero.",
             "x": "trimestre", "seriesBy": "categoria", "metrica": "inscripciones_iniciales",
             "fixed": {"grano": "trimestral"},
             "seriesExclude": ["Total"], "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
                 {"kind": "metric", "label": "Operación",
                  "options": ["inscripciones_iniciales", "transferencias"]},
             ],
             "unidad": "vehículos"},
            {"id": "pat-motos-pct", "type": "line",
             "title": "Peso de las motos en el patentamiento",
             "descr": "Porcentaje de los vehículos 0 km patentados en Salta que son motos. Es el "
                      "dato que conecta con la seguridad vial: el parque de motos es el que "
                      "explica que cuatro de cada diez muertos en siniestros viales de la "
                      "provincia sean motociclistas.",
             "x": "trimestre", "seriesBy": None, "metrica": "pct_motos",
             "fixed": {"grano": "trimestral", "categoria": "Total"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "%"},
            {"id": "pat-usados", "type": "line",
             "title": "Usados por cada 0 km",
             "descr": "Transferencias de usados por cada vehículo nuevo patentado. Sube cuando el "
                      "0 km se vuelve inalcanzable y el mercado se mueve al usado.",
             "x": "trimestre", "seriesBy": None, "metrica": "transf_por_inscripcion",
             "fixed": {"grano": "trimestral", "categoria": "Total"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "veces"},
            {"id": "pat-parque", "type": "line",
             "title": "Parque automotor de Salta",
             "descr": "Automotores en condiciones registrales de circular a fin de cada mes. Es "
                      "un stock, así que al cambiar de frecuencia se promedia, no se suma. No "
                      "incluye motos: la DNRPA no publica el parque de motovehículos.",
             "x": "trimestre", "seriesBy": None, "metrica": "parque_automotor",
             "fixed": {"grano": "trimestral", "categoria": "Autos"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "automotores"},
            {"id": "pat-renovacion", "type": "line",
             "title": "Renovación de la flota",
             "descr": "Autos 0 km patentados cada mil automotores del parque. Numerador y "
                      "denominador son los dos automotor, así que la tasa cierra. Cuanto más "
                      "baja, más vieja se vuelve la flota que circula.",
             "x": "anio", "seriesBy": None, "metrica": "renovacion_1000",
             "fixed": {"grano": "anual", "categoria": "Autos"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "anual", "options": [
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"},
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"}]},
             ],
             "unidad": "por mil automotores"},
        ],
    },

    # ======================================================================
    {
        "id": "aeropuerto",
        "subeje": "Turismo",
        "area": "turismo",
        "eje_pdes": "territorio-ambiente-turismo",
        "title": "Movimiento aeroportuario",
        "resumen": (
            "Movimiento del aeropuerto Martín Miguel de Güemes según la Administración Nacional de "
            "Aviación Civil: pasajeros y vuelos que aterrizan en Salta desde 2019, abiertos por "
            "clasificación, clase de vuelo y aerolínea, y la serie histórica de pasajeros y "
            "movimientos desde 2001, con las rutas que conectan a la provincia."
        ),
        "resumen_corto": "Pasajeros y vuelos que llegan al aeropuerto de Salta.",
        "advertencia": (
            "Movimiento aeroportuario (no turismo receptivo)."
        ),
        "fuente": "Administración Nacional de Aviación Civil (ANAC)",
        "fuente_url": "https://datos.gob.ar/dataset/aterrizajes-y-despegues-procesados-por-la-administracion-nacional-de-aviacion-civil-anac",
        "cobertura": "2001–2026",
        "keywords": [
            "aeropuerto", "aviación", "vuelos", "pasajeros", "aterrizajes", "ANAC", "aéreo",
            "Martín Miguel de Güemes", "aerolíneas", "Aerolíneas Argentinas", "JetSmart",
            "Flybondi", "cabotaje", "internacional", "rutas", "conectividad aérea", "turismo",
        ],
        "tags": ["actividad-productividad"],
        "kpis": [
            {"label": "Pasajeros arribados", "metrica": "pax_arribos",
             "fixed": {"grano": "trimestral", "apertura": "total", "categoria": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "pasajeros", "format": "int",
             "geo": "Provincia"},
            {"label": "Vuelos arribados", "metrica": "vuelos_arribos",
             "fixed": {"grano": "trimestral", "apertura": "total", "categoria": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "vuelos", "format": "int",
             "geo": "Provincia"},
        ],
        "charts": [
            {"id": "aero-pax", "type": "line",
             "title": "Pasajeros que aterrizan en Salta",
             "descr": "Pasajeros desembarcados en el aeropuerto de Salta, según el vuelo sea "
                      "doméstico o internacional. Sólo arribos: no incluye a los que despegan.",
             "x": "trimestre", "seriesBy": "categoria", "metrica": "pax_arribos",
             "fixed": {"grano": "trimestral", "apertura": "clasificacion"},
             "seriesExclude": ["Total"],
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "pasajeros"},
            {"id": "aero-vuelos", "type": "stacked-area",
             "title": "Vuelos que aterrizan, por clase",
             "descr": "Aterrizajes según la clase de vuelo que declara la ANAC. Los regulares son "
                      "las frecuencias de línea; el resto incluye chárter, aviación privada, "
                      "vuelos escuela y vuelos oficiales.",
             "x": "trimestre", "seriesBy": "categoria", "metrica": "vuelos_arribos",
             "fixed": {"grano": "trimestral", "apertura": "clase"},
             "seriesExclude": ["Total"], "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "vuelos"},
            {"id": "aero-aerolineas", "type": "barh",
             "title": "Pasajeros por aerolínea",
             "descr": "Aerolíneas ordenadas por pasajeros desembarcados en el año seleccionado. "
                      "Se publican las diez primeras de toda la serie; el resto se agrupa en "
                      "«Otras», y «Sin informar» es aviación general sin explotador declarado.",
             "x": "categoria", "seriesBy": None, "metrica": "pax_arribos",
             "fixed": {"grano": "anual", "apertura": "aerolinea"}, "exclude": ["Total"],
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "topN": 10, "unidad": "pasajeros"},
            {"id": "aero-serie-larga", "type": "line",
             "title": "Pasajeros desde 2001 (serie histórica)",
             "descr": "Serie larga de la ANAC, que cuenta pasajeros comerciales de cabotaje e "
                      "internacionales con otra definición y otro corte horario que el tablero de "
                      "aterrizajes: no cierra con él y no se empalman.",
             "x": "trimestre", "seriesBy": "categoria", "metrica": "pax_serie",
             "fixed": {"grano": "trimestral", "apertura": "clasificacion"},
             "seriesExclude": ["Total"],
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
                 {"kind": "metric", "label": "Medida", "options": ["pax_serie", "mov_serie"]},
             ],
             "unidad": "pasajeros"},
            {"id": "aero-rutas", "type": "barh",
             "title": "Pasajeros por ruta",
             "descr": "Rutas que conectan a Salta, ordenadas por pasajeros transportados en el "
                      "año seleccionado. Cuenta los dos sentidos del trayecto.",
             "x": "categoria", "seriesBy": None, "metrica": "pax_ruta",
             "fixed": {"grano": "anual", "apertura": "ruta"}, "exclude": ["Total"],
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "pasajeros"},
        ],
    },

    # ======================================================================
    {
        "id": "supermercados",
        "ciiu": "G",
        "area": "economico",
        "eje_pdes": "economico-productivo",
        "title": "Ventas de supermercados",
        "resumen": (
            "Ventas y cantidad de operaciones de los supermercados de Salta según la Encuesta de "
            "Supermercados del INDEC, mensual desde 2017, en pesos corrientes y constantes de "
            "{base_largo}, con la participación de la provincia en el total del país y la "
            "comparación con las demás jurisdicciones."
        ),
        "resumen_corto": "Cuánto y cuántas veces se compra en los supermercados de Salta.",
        "advertencia": (
            "Las ventas de supermercados «no se deben considerar aisladamente como un indicador macroeconómico del consumo"
            "Se mide un canal comercial, no el gasto de los hogares.  Panel no probabilístico de empresas con alguna boca "
            "de al menos 200 m² de salón de ventas. No incluye almacenes, autoservicios chicos y mayoristas."
            
        ),
        "fuente": "Encuesta de Supermercados — INDEC",
        "fuente_url": "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-1-34",
        "cobertura": "2017–2026",
        "keywords": [
            "supermercados", "ventas", "consumo", "comercio", "minorista", "canasta",
            "operaciones", "tickets", "INDEC", "EMAS", "góndola", "precios corrientes",
            "precios constantes", "poder de compra", "hipermercado", "autoservicio",
        ],
        "tags": ["actividad-productividad"],
        "kpis": [
            {"label": "Ventas de supermercados (pesos constantes, {base})", "metrica": "ventas_real",
             "tabla_label": "Ventas de supermercados (pesos constantes)",
             "fixed": {"grano": "trimestral", "jurisdiccion": "Salta"},
             "cmp": "quarter", "year": "latest", "unidad": "pesos", "format": "int",
             "geo": "Provincia"},
            {"label": "Operaciones de compra", "metrica": "operaciones",
             "tabla_label": "Operaciones de compra en supermercados",
             "fixed": {"grano": "trimestral", "jurisdiccion": "Salta"},
             "cmp": "quarter", "year": "latest", "unidad": "operaciones", "format": "int",
             "geo": "Provincia"},
        ],
        "charts": [
            {"id": "sup-ventas", "type": "line",
             "title": "Ventas de supermercados en Salta",
             "descr": "Ventas totales a precios corrientes y a precios constantes, deflactadas "
                      "por el IPC Nivel General de la región NOA.",
             "x": "trimestre", "seriesBy": None, "metrica": "ventas_real",
             "fixed": {"grano": "trimestral", "jurisdiccion": "Salta"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "ventas_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "ventas_real"}]},
             ],
             "unidad": "pesos"},
            {"id": "sup-operaciones", "type": "line",
             "title": "Cantidad de operaciones",
             "descr": "Operaciones de compra registradas en las cajas de los supermercados de "
                      "Salta. A diferencia de las ventas, no la afecta la inflación.",
             "x": "trimestre", "seriesBy": None, "metrica": "operaciones",
             "fixed": {"grano": "trimestral", "jurisdiccion": "Salta"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "operaciones"},
            {"id": "sup-share", "type": "line",
             "title": "Participación de Salta en el país",
             "descr": "Porcentaje de las ventas de supermercados del país que corresponde a Salta.",
             "x": "trimestre", "seriesBy": None, "metrica": "share_pais_pct",
             "fixed": {"grano": "trimestral", "jurisdiccion": "Salta"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "%"},
            {"id": "sup-ranking", "type": "barh",
             "title": "Ventas por jurisdicción (ranking)",
             "descr": "Jurisdicciones ordenadas por ventas de supermercados en el año "
                      "seleccionado. El INDEC publica Buenos Aires partida en dos.",
             "x": "jurisdiccion", "seriesBy": None, "metrica": "ventas_real",
             "fixed": {"grano": "anual"}, "exclude": ["Total del país"],
             "controls": [
                 {"dim": "anio", "label": "Año", "kind": "year"},
                 {"kind": "mode", "label": "Valores", "default": "real", "options": [
                     {"value": "corriente", "label": "Corrientes", "metric": "ventas_corr"},
                     {"value": "real", "label": "Constantes ({base})", "metric": "ventas_real"}]},
             ],
             "sort": "desc", "unidad": "pesos"},
        ],
    },

    # ======================================================================
    {
        "id": "cemento",
        "ciiu": "F",
        "area": "economico",
        "eje_pdes": "economico-productivo",
        "title": "Despachos de cemento",
        "resumen": (
            "Cemento despachado con destino a Salta según la Asociación de Fabricantes de Cemento "
            "Portland, mensual desde 2017, abierto en bolsa y granel, con la participación de la "
            "provincia en el total del país y la comparación con las demás jurisdicciones."
        ),
        "resumen_corto": "Cemento despachado a Salta, en bolsa y a granel.",
        "advertencia": (
            "La apertura por provincia está congelada en septiembre de 2025: la AFCP sigue "
            "publicando despachos nacionales, pero dejó de abrirlos por jurisdicción."
            "Despachos con destino a Salta, no producción de Salta."
        ),
        "fuente": "Asociación de Fabricantes de Cemento Portland (AFCP)",
        "fuente_url": "https://www.afcp.org.ar/copia-de-despacho-total-de-cemento",
        "cobertura": "2017–2025",
        "keywords": [
            "cemento", "despachos", "construcción", "obra", "bolsa", "granel", "AFCP",
            "portland", "hormigón", "actividad de la construcción", "insumos", "toneladas",
            "obra privada", "obra pública", "autoconstrucción",
        ],
        "tags": ["actividad-productividad", "infraestructura-logistica"],
        "kpis": [
            {"label": "Despachos de cemento", "tabla_label": "Cemento despachado a Salta",
             "metrica": "despachos_t",
             "fixed": {"grano": "trimestral", "provincia": "Salta", "envase": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "toneladas", "format": "int",
             "geo": "Provincia"},
            {"label": "Despachos a granel", "tabla_label": "Cemento despachado a granel",
             "tabla_nota": "El granel abastece sobre todo a hormigoneras y obra grande; la bolsa, "
                           "a obra chica y autoconstrucción. Es una lectura del sector, no una "
                           "definición de la AFCP.",
             "metrica": "despachos_t",
             "fixed": {"grano": "trimestral", "provincia": "Salta", "envase": "Granel"},
             "cmp": "quarter", "year": "latest", "unidad": "toneladas", "format": "int",
             "geo": "Provincia", "grafico": "cem-envase"},
        ],
        "charts": [
            {"id": "cem-envase", "type": "stacked-area",
             "title": "Despachos a Salta por envase",
             "descr": "Cemento despachado a la provincia, apilando bolsa y granel. El granel va "
                      "sobre todo a hormigoneras y obra grande; la bolsa, a obra chica.",
             "x": "trimestre", "seriesBy": "envase", "metrica": "despachos_t",
             "fixed": {"grano": "trimestral", "provincia": "Salta"},
             "seriesExclude": ["Total"], "stack": True,
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "toneladas"},
            {"id": "cem-total", "type": "line",
             "title": "Despachos totales a Salta",
             "descr": "Total de cemento despachado a la provincia, tal como lo publica la AFCP.",
             "x": "trimestre", "seriesBy": None, "metrica": "despachos_t",
             "fixed": {"grano": "trimestral", "provincia": "Salta", "envase": "Total"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "toneladas"},
            {"id": "cem-share", "type": "line",
             "title": "Participación de Salta en el país",
             "descr": "Porcentaje del cemento despachado en el país que tiene destino en Salta.",
             "x": "trimestre", "seriesBy": None, "metrica": "share_pais_pct",
             "fixed": {"grano": "trimestral", "provincia": "Salta", "envase": "Total"},
             "controls": [
                 {"kind": "freq", "label": "Frecuencia", "default": "trimestral", "options": [
                     {"value": "trimestral", "label": "Trimestral", "x": "trimestre", "grano": "trimestral"},
                     {"value": "mensual", "label": "Mensual", "x": "mes", "grano": "mensual"},
                     {"value": "anual", "label": "Anual", "x": "anio", "grano": "anual"}]},
             ],
             "unidad": "%"},
            {"id": "cem-ranking", "type": "barh",
             "title": "Despachos por jurisdicción (ranking)",
             "descr": "Jurisdicciones ordenadas por cemento recibido en el año seleccionado. La "
                      "AFCP publica Buenos Aires partida en tres: CABA, Gran Buenos Aires y el "
                      "resto de la provincia.",
             "x": "provincia", "seriesBy": None, "metrica": "despachos_t",
             "fixed": {"grano": "anual", "envase": "Total"}, "exclude": ["Total del país"],
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "toneladas"},
        ],
    },
]
# ==========================================================================
# EJE SOCIOCULTURAL — planillas del PDES 2030 (J. Paz, 2026): dos períodos por indicador, por
# departamento y por las 8 regiones del PDES. Los cinco tableros comparten la misma estructura
# de datos (`adapters.PDES_FIELDS`) y los mismos tres gráficos.
# ==========================================================================
# Frecuencia + base de la variación. Cada spec despliega una con **: la frecuencia dice contra qué
# período se compara, porque la tabla de la portada no lo aclara en el encabezado.
INTERCENSAL = {"frecuencia": "Intercensal", "var": "anterior"}
ENTRE_TRIENIOS_SALUD = {"frecuencia": "Entre trienios", "var": "anterior",
                        "periodos": {"2020": "2018-20", "2023": "2021-23"}}
ENTRE_TRIENIOS_SNIC = {"frecuencia": "Entre trienios", "var": "anterior",
                       "periodos": {"2015": "2013-15", "2023": "2021-23"}}
ENTRE_2018_2025 = {"frecuencia": "Entre 2018 y 2025", "var": "anterior"}


def _pdes_kpi(label, metrica, unidad, sentido, frecuencia, **extra):
    """Spec de KPI de los tableros del PDES: total provincial, nivel (no variación relativa) y
    apertura por departamento y región."""
    spec = {"label": label, "metrica": metrica,
            "fixed": {"nivel_geo": "Provincia", "territorio": "Salta"}, "year": "latest",
            "unidad": unidad, "format": "int", "display": "nivel", "sentido": sentido,
            "geo": "Departamento y región",
            "geo_nota": "23 departamentos y 8 regiones del PDES"}
    spec.update(frecuencia)
    spec.update(extra)
    return spec


def _pdes_graficos(pref, base, opciones, periodo_ultimo, unidad, nota_ranking=""):
    """Los tres gráficos de cada tablero del PDES. `opciones`: métricas que se pueden elegir."""
    return [
        {"id": pref + "-ranking", "type": "barh",
         "title": "Ranking por departamento o región",
         "descr": ("Cada departamento, o cada región del PDES, en el período elegido. "
                   + nota_ranking).strip(),
         "x": "territorio", "seriesBy": None, "metrica": base, "fixed": {},
         "exclude": ["Salta"],
         "controls": [
             {"kind": "metric", "label": "Indicador", "options": opciones},
             {"dim": "nivel_geo", "label": "Apertura", "kind": "select", "default": "Departamento"},
             {"dim": "periodo", "label": "Período", "kind": "select", "default": periodo_ultimo},
         ],
         "sort": "desc", "unidad": unidad},
        {"id": pref + "-comparacion", "type": "bar",
         "title": "Comparación entre los dos períodos",
         "descr": "El indicador en cada período, para la provincia, un departamento o una región.",
         "x": "periodo", "seriesBy": None, "metrica": base, "fixed": {},
         "controls": [
             {"kind": "metric", "label": "Indicador", "options": opciones},
             {"dim": "territorio", "label": "Territorio", "kind": "select",
              "all": True, "allValue": "Salta", "allLabel": "Salta (provincia)"},
         ],
         "unidad": unidad},
        {"id": pref + "-cambio", "type": "bar",
         "title": "Cambio entre los dos períodos",
         "descr": ("Último período menos el primero, por departamento o región: los porcentajes, "
                   "en puntos porcentuales. Que un indicador de privación baje es una mejora."),
         "x": "territorio", "seriesBy": None, "metrica": base + "_dif", "fixed": {},
         "exclude": ["Salta"],
         "controls": [
             {"kind": "metric", "label": "Indicador", "options": [m + "_dif" for m in opciones]},
             {"dim": "nivel_geo", "label": "Apertura", "kind": "select", "default": "Departamento"},
         ],
         "unidad": unidad},
    ]


_PDES_AVISO_REGIONES = ("Las regiones del PDES se aproximan con departamentos completos: Puna es "
                        "sólo Los Andes y Yungas sólo Orán.")

TEMAS += [
    # ======================================================================
    {
        "id": "pdes-privacion",
        "subeje": "Condiciones de vida",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Privación por departamento y región (censos 2010 y 2022)",
        "resumen": (
            "Personas en hogares con necesidades básicas insatisfechas, sin agua de red pública y, "
            "entre la población indígena, con NBI, según los censos 2010 y 2022, por departamento "
            "y por las 8 regiones del PDES 2030. Permite ver la variación intercensal: en la "
            "provincia, la NBI bajó de 25,5 % a 16,9 % de las personas."
        ),
        "resumen_corto": "NBI, agua de red y NBI indígena entre los censos 2010 y 2022.",
        "advertencia": (
            "2010 sale de la muestra del cuestionario ampliado y 2022 del censo completo: en los "
            "departamentos chicos la estimación de 2010 tiene error muestral. La NBI indígena "
            "cambia de pregunta entre censos (por hogar en 2010, autorreconocimiento en 2022), así "
            "que su variación no es la de una misma población. «Sin agua de red» no significa sin "
            "agua apta. " + _PDES_AVISO_REGIONES
        ),
        "fuente": PDES_FUENTE_CENSO, "fuente_url": "",
        "cobertura": "Censos 2010 y 2022",
        "keywords": ["NBI", "necesidades básicas insatisfechas", "pobreza estructural", "agua",
                     "agua de red", "indígenas", "pueblos originarios", "censo", "intercensal",
                     "regiones", "privación"],
        "tags": [],
        "kpis": [
            _pdes_kpi("Personas en hogares con NBI", "nbi_personas", "%", "menor_mejor",
                      INTERCENSAL, meta_2030=12,
                      meta_2030_nota="El PDES fija la meta de «NBI población» al Censo 2030 "
                                     "(la de NBI hogares, 10 %, está en el indicador de hogares)."),
            _pdes_kpi("Personas en hogares sin agua de red pública", "sin_agua_red", "%",
                      "menor_mejor", INTERCENSAL, meta_2030=7,
                      meta_2030_nota="El PDES fija una cobertura de agua de red del 93 % al Censo "
                                     "2030; acá se expresa como su complemento, porque el Monitor "
                                     "mide la carencia y no la cobertura."),
            _pdes_kpi("Personas indígenas en hogares con NBI", "nbi_indigena", "%", "menor_mejor",
                      INTERCENSAL,
                      tabla_nota="La pregunta cambia entre censos (por hogar en 2010, "
                                 "autorreconocimiento individual en 2022): la variación no es la "
                                 "de una misma población."),
        ],
        "charts": _pdes_graficos("pp", "nbi_personas",
                                 ["nbi_personas", "sin_agua_red", "nbi_indigena"], "2022", "%"),
    },
    # ======================================================================
    {
        "id": "pdes-salud",
        "subeje": "Salud",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Salud materno-infantil por departamento y región",
        "resumen": (
            "Mortalidad infantil, bajo peso al nacer, fecundidad adolescente y natalidad en los "
            "trienios 2018-2020 y 2021-2023, por departamento y por las 8 regiones del PDES 2030, "
            "según las estadísticas vitales de la DEIS. La mortalidad infantil bajó de 10,9 a 9,1 "
            "por mil nacidos vivos y la fecundidad adolescente, de 55,1 a 34,6 por mil."
        ),
        "resumen_corto": "Mortalidad infantil, bajo peso y fecundidad adolescente por trienio.",
        "advertencia": (
            "Los trienios agregan tres años de casos, pero en departamentos chicos (La Poma, Los "
            "Andes, Guachipas, La Caldera, Molinos) la mortalidad infantil sigue siendo inestable: "
            "una o dos defunciones mueven la tasa. La fecundidad adolescente no es el porcentaje de "
            "adolescentes que fueron madres y no incluye a las menores de 15. "
            + _PDES_AVISO_REGIONES
        ),
        "fuente": PDES_FUENTE_SALUD, "fuente_url": "",
        "cobertura": "Trienios 2018-2020 y 2021-2023",
        "keywords": ["mortalidad infantil", "TMI", "bajo peso al nacer", "fecundidad adolescente",
                     "embarazo adolescente", "natalidad", "nacidos vivos", "DEIS", "trienio",
                     "regiones", "salud materno-infantil"],
        "tags": [],
        "kpis": [
            _pdes_kpi("Tasa de mortalidad infantil", "tmi", "por mil nacidos vivos",
                      "menor_mejor", ENTRE_TRIENIOS_SALUD, ficha="II.8"),
            _pdes_kpi("Nacidos vivos con bajo peso al nacer", "bajo_peso", "%", "menor_mejor",
                      ENTRE_TRIENIOS_SALUD, ficha="II.10",
                      tabla_nota="Menos de 2.500 g, sobre los nacidos vivos con peso informado."),
            _pdes_kpi("Fecundidad adolescente (15 a 19)", "tfa_15_19", "por mil mujeres",
                      "menor_mejor", ENTRE_TRIENIOS_SALUD, ficha="II.18"),
        ],
        "charts": _pdes_graficos("ps", "tmi", ["tmi", "bajo_peso", "tfa_15_19", "natalidad",
                                               "nv_sin_peso"], "2021-2023",
                                 "por mil nacidos vivos"),
    },
    # ======================================================================
    {
        "id": "pdes-educacion",
        "subeje": "Educación",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Trayectorias y aprendizajes, 2018 y 2025",
        "resumen": (
            "Matrícula, repitencia y sobreedad del Relevamiento Anual, y desempeño en Matemática "
            "de 6.º grado en Aprender, en 2018 y 2025, por departamento y por las 8 regiones del "
            "PDES 2030. La sobreedad en secundaria bajó de 41,1 % a 29,3 %; los alumnos con "
            "desempeño satisfactorio o avanzado en Matemática, de 59,9 % a 51,0 %."
        ),
        "resumen_corto": "Repitencia, sobreedad y Aprender Matemática entre 2018 y 2025.",
        "advertencia": (
            "La fuente enmascara las combinaciones con pocos casos y esos alumnos entran sólo al "
            "total: la matrícula por departamento está subestimada. Aprender compara dos cohortes "
            "distintas, no a los mismos alumnos, y en Guachipas, La Poma y Cachi hay pocos "
            "evaluados. " + _PDES_AVISO_REGIONES
        ),
        "fuente": PDES_FUENTE_EDUCACION, "fuente_url": "",
        "cobertura": "2018 y 2025",
        "keywords": ["educación", "matrícula", "repitencia", "sobreedad", "Aprender",
                     "matemática", "desempeño", "jardín", "nivel inicial", "secciones múltiples",
                     "escuela rural", "regiones", "trayectorias escolares"],
        "tags": [],
        "kpis": [
            _pdes_kpi("Matrícula de primaria y secundaria", "matricula_prim_sec", "alumnos",
                      "neutro", ENTRE_2018_2025, ficha="III.1"),
            _pdes_kpi("Repitencia en secundaria", "repitencia_sec", "% de la matrícula",
                      "menor_mejor", ENTRE_2018_2025, ficha="III.2"),
            _pdes_kpi("Aprender Matemática 6.º: satisfactorio o avanzado", "mat_satisf_avanzado",
                      "% de alumnos", "mayor_mejor", ENTRE_2018_2025, ficha="III.8",
                      tabla_label="Aprender 6.º grado, Matemática: alumnos en nivel satisfactorio "
                                  "o avanzado"),
            _pdes_kpi("Repitencia en primaria", "repitencia_pri", "% de la matrícula",
                      "menor_mejor", ENTRE_2018_2025),
            _pdes_kpi("Sobreedad en primaria", "sobreedad_pri", "% de la matrícula",
                      "menor_mejor", ENTRE_2018_2025),
            _pdes_kpi("Sobreedad en secundaria", "sobreedad_sec", "% de la matrícula",
                      "menor_mejor", ENTRE_2018_2025),
            _pdes_kpi("Aprender Matemática 6.º: por debajo del nivel básico", "mat_debajo_basico",
                      "% de alumnos", "menor_mejor", ENTRE_2018_2025,
                      tabla_label="Aprender 6.º grado, Matemática: alumnos por debajo del nivel "
                                  "básico"),
            _pdes_kpi("Alumnos de 6.º que asistieron al jardín desde sala de 3", "jardin_sala3",
                      "% de alumnos", "mayor_mejor", ENTRE_2018_2025),
        ],
        "charts": _pdes_graficos("pe", "repitencia_sec", [
            "repitencia_sec", "repitencia_pri", "sobreedad_sec", "sobreedad_pri",
            "mat_satisf_avanzado", "mat_debajo_basico", "jardin_sala3", "sin_libros",
            "madre_secundaria", "matricula_prim_sec", "matricula_inicial", "alumnos_seccion_pri",
            "alumnos_seccion_sec", "secciones_multiples", "pct_estatal", "pct_rural"], "2025",
            "% de la matrícula"),
    },
    # ======================================================================
    {
        "id": "pdes-trabajo",
        "subeje": "Trabajo",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Trabajo por departamento y región (censos 2010 y 2022)",
        "resumen": (
            "Desocupación, informalidad y participación laboral de varones y mujeres según los "
            "censos 2010 y 2022, por departamento y por las 8 regiones del PDES 2030. La "
            "informalidad bajó de 49,3 % a 45,6 % de los ocupados y la brecha de participación "
            "entre varones y mujeres se achicó de 26,4 a 17,5 puntos."
        ),
        "resumen_corto": "Desocupación, informalidad y brecha de participación entre censos.",
        "advertencia": (
            "2010 sale de la muestra del cuestionario ampliado y 2022 del censo completo: en los "
            "departamentos chicos la estimación de 2010 tiene error muestral. La informalidad mide "
            "sólo la falta de protección contributiva (ocupados sin descuento ni aporte "
            "jubilatorio), y la desocupación se lee junto con la participación. "
            + _PDES_AVISO_REGIONES
        ),
        "fuente": PDES_FUENTE_CENSO, "fuente_url": "",
        "cobertura": "Censos 2010 y 2022",
        "keywords": ["trabajo", "empleo", "desocupación", "desempleo", "informalidad",
                     "trabajo no registrado", "participación laboral", "tasa de actividad",
                     "brecha de género", "mujeres", "censo", "intercensal", "regiones"],
        "tags": [],
        "kpis": [
            _pdes_kpi("Tasa de desocupación, 18 años y más", "desocupacion", "%", "menor_mejor",
                      INTERCENSAL),
            _pdes_kpi("Informalidad laboral, ocupados de 18 a 64 años", "informalidad", "%",
                      "menor_mejor", INTERCENSAL,
                      tabla_nota="Ocupados sin descuento ni aporte jubilatorio."),
            _pdes_kpi("Brecha de participación varones-mujeres, 18 a 64 años",
                      "brecha_participacion", "p.p.", "menor_mejor", INTERCENSAL,
                      tabla_nota="Tasa de actividad de varones menos la de mujeres."),
            _pdes_kpi("Tasa de actividad de mujeres, 18 a 64 años", "actividad_mujeres", "%",
                      "mayor_mejor", INTERCENSAL),
            _pdes_kpi("Tasa de actividad de varones, 18 a 64 años", "actividad_varones", "%",
                      "neutro", INTERCENSAL),
        ],
        "charts": _pdes_graficos("pt", "informalidad", [
            "informalidad", "desocupacion", "brecha_participacion", "actividad_mujeres",
            "actividad_varones", "informalidad_mujeres", "informalidad_varones"], "2022", "%"),
    },
    # ======================================================================
    {
        "id": "pdes-delitos",
        "subeje": "Seguridad",
        "area": "social",
        "eje_pdes": "sociocultural",
        "title": "Delitos registrados por departamento y región",
        "resumen": (
            "Tasas de víctimas de homicidio doloso, robos, lesiones dolosas y abusos sexuales con "
            "acceso carnal registrados por el SNIC en los trienios 2013-2015 y 2021-2023, por "
            "departamento y por las 8 regiones del PDES 2030. La tasa de homicidios bajó de 5,8 a "
            "4,1 por cien mil habitantes."
        ),
        "resumen_corto": "Homicidios, robos, lesiones y abusos sexuales registrados, por trienio.",
        "advertencia": (
            "Son delitos registrados, por lugar del hecho: dependen de cuánto se denuncia y de la "
            "presencia policial, y las tasas bajas de Puna, Pre-Puna y Valles Calchaquíes pueden "
            "deberse en parte a subregistro. El homicidio es el indicador más comparable. Los "
            "departamentos sin casos no aparecen en el ranking. " + _PDES_AVISO_REGIONES
        ),
        "fuente": PDES_FUENTE_SNIC, "fuente_url": "",
        "cobertura": "Trienios 2013-2015 y 2021-2023",
        "keywords": ["delitos", "homicidios", "robos", "lesiones", "abuso sexual", "violencia",
                     "inseguridad", "SNIC", "criminalidad", "trienio", "regiones"],
        "tags": [],
        "kpis": [
            _pdes_kpi("Víctimas de homicidio doloso", "homicidio", "por cien mil hab.",
                      "menor_mejor", ENTRE_TRIENIOS_SNIC),
            _pdes_kpi("Robos y tentativas de robo", "robos", "por cien mil hab.", "menor_mejor",
                      ENTRE_TRIENIOS_SNIC),
            _pdes_kpi("Lesiones dolosas", "lesiones", "por cien mil hab.", "menor_mejor",
                      ENTRE_TRIENIOS_SNIC),
            _pdes_kpi("Abusos sexuales con acceso carnal", "abusos", "por cien mil hab.",
                      "menor_mejor", ENTRE_TRIENIOS_SNIC,
                      tabla_nota="Hechos registrados, no víctimas mujeres: entre un tercio y la "
                                 "mitad de las víctimas no tiene sexo registrado."),
        ],
        "charts": _pdes_graficos("pd", "homicidio", ["homicidio", "robos", "lesiones", "abusos"],
                                 "2021-2023", "por cien mil hab."),
    },
]


def tema_by_id(tid):
    for t in TEMAS:
        if t["id"] == tid:
            return t
    raise KeyError(tid)
