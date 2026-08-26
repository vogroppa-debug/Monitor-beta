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
  unidad:      etiqueta de unidad (si metrica es conmutable, la resuelve el front)
  fuente/fuente_url: fuente propia del gráfico (si difiere de la del tema)

Campos de tema para la tabla maestra:
  subeje: subeje de la tabla de la portada. Si falta, se usa la etiqueta del PRIMER `tag`
          (válido en el eje económico-productivo, donde los subejes SON los tags).

Spec de KPI (el front muestra la VARIACIÓN INTERANUAL, no el valor absoluto):
  label, metrica, fixed, year('latest'|'latest_complete'|int), unidad, format
  tabla_label: nombre para la tabla maestra de la portada (si el `label` es ambiguo fuera
               de su tablero, p. ej. "Vacas" o "Pozos"); tabla_nota: aclaración al pie
  subeje: pisa el subeje del tema para ESTE indicador (temas que mezclan subejes)
  base_valor / base_periodo: línea de base del PDES (vacías hasta que se definan)
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
}

# Ejes transversales de desarrollo productivo. Un tema puede tener varios (campo
# `tags`). Son la agrupación principal del menú y la portada; el `area` queda como
# chip de color. Se definen los 5 aunque algún eje aún no tenga temas (fase 2).
TAGS = {
    "actividad-productividad":   {"label": "Actividad, estructura productiva y productividad",       "orden": 1,
                                  "corto": "Actividad y productividad",
                                  "descr": "Qué y cuánto se produce en Salta, y con qué productividad."},
    "empleo-capacidades":        {"label": "Empleo y capacidades productivas",                       "orden": 2,
                                  "corto": "Empleo y capacidades",
                                  "descr": "Trabajo registrado, remuneraciones y formación del capital humano."},
    "inversion-financiamiento":  {"label": "Inversión y financiamiento",                             "orden": 3,
                                  "corto": "Inversión y financiamiento",
                                  "descr": "Recursos que financian la actividad y la inversión productiva."},
    "infraestructura-logistica": {"label": "Infraestructura, logística y condiciones para producir", "orden": 4,
                                  "corto": "Infraestructura y logística",
                                  "descr": "Energía, transporte y servicios que habilitan la producción."},
    "innovacion-mercados":       {"label": "Innovación e inserción en mercados",                     "orden": 5,
                                  "corto": "Innovación y mercados",
                                  "descr": "Exportaciones, diversificación y llegada a nuevos mercados."},
}

# Subejes de la tabla maestra de indicadores. En el eje económico-productivo son los TAGS de
# arriba (se toma el primero del tema); los otros dos ejes usan una taxonomía temática propia,
# declarada tema por tema con el campo `subeje`. El número es solo el orden de aparición.
SUBEJE_ORDEN = {
    # sociocultural (pendientes: Salud, Condiciones de vida)
    "Educación": 1,
    # territorio, ambiente y turismo (Territorio todavía sin temas)
    "Territorio": 1, "Ambiente": 2, "Turismo": 3,
}

SITE = {
    "nombre": "Monitor de Indicadores (versión Beta)",
    "subtitulo": "Seguimiento del Plan de Desarrollo Estratégico de Salta (PDES 2030)",
    "institucion": "Consejo Económico y Social de Salta (CESS)",
}

# Ejes estratégicos del PDES 2030 (nivel superior de agrupación en la portada y el menú).
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
            {"label": "Cargos docentes", "metrica": "cargos", "fixed": {}, "year": "latest",
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
            "de la provincia, desde 2018."
        ),
        "resumen_corto": "La cadena del vino en Salta: uva, elaboración y exportaciones.",
        "fuente": "Instituto Nacional de Vitivinicultura (INV)",
        "fuente_url": "https://www.argentina.gob.ar/inv/vinos/estadisticas",
        "cobertura": "2018–2025",
        "keywords": [
            "vino", "vid", "uva", "bodegas", "vitivinicultura", "INV", "cosecha", "elaboración",
            "mosto", "exportaciones", "Cafayate", "Cachi", "Molinos", "San Carlos",
            "Valles Calchaquíes", "mercado interno", "hectolitros", "quintales", "vendimia",
        ],
        "tags": ["actividad-productividad", "innovacion-mercados"],
        "kpis": [
            {"label": "Producción de uva", "metrica": "produccion_uva",
             "fixed": {"categoria": "cosecha_elaboracion"}, "year": "latest", "unidad": "quintales", "format": "int"},
            {"label": "Elaboración de vino y mosto", "metrica": "elaboracion_total",
             "fixed": {"categoria": "cosecha_elaboracion"}, "year": "latest", "unidad": "hectolitros", "format": "int"},
            {"label": "Exportaciones (valor FOB)", "tabla_label": "Exportaciones de vino (valor FOB)",
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
            {"label": "Producción de gas", "metrica": "prod_gas", "fixed": {"grano": "anual"},
             "year": "latest_complete", "unidad": "miles de m³", "format": "int"},
            {"label": "Producción de petróleo", "metrica": "prod_pet", "fixed": {"grano": "anual"},
             "year": "latest_complete", "unidad": "m³", "format": "int"},
            {"label": "Pozos", "tabla_label": "Pozos en producción", "metrica": "pozos", "fixed": {"grano": "anual"},
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
            {"label": "Empleo registrado (provincia)", "tabla_label": "Empleo registrado", "metrica": "empleo",
             "fixed": {"grano": "trimestral", "departamento": "Salta", "rubro": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "puestos", "format": "int"},
            {"label": "Remuneración real (índice dic-23 = 100)", "metrica": "remun_real_idx",
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
            {"label": "Producción total", "tabla_label": "Producción agrícola total", "metrica": "produccion_tm",
             "fixed": {"departamento": "Salta"}, "year": "latest", "unidad": "toneladas", "format": "int"},
            {"label": "Superficie sembrada", "metrica": "superficie_sembrada_ha",
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
            "transferencias corrientes y de capital, en pesos corrientes y constantes, 2021–2025."
        ),
        "resumen_corto": "Ejecución del gasto provincial por objeto, finalidad y transferencias.",
        "fuente": "Ejecución presupuestaria — Ministerio de Economía de Salta",
        "fuente_url": "https://presupuesto.salta.gob.ar/",
        "cobertura": "2021–2025",
        "keywords": [
            "gasto público", "presupuesto", "ejecución presupuestaria", "finanzas públicas",
            "objeto del gasto", "personal", "bienes de uso", "transferencias", "servicio de la deuda",
            "finalidad", "función", "gasto social", "obra pública", "coparticipación", "erogaciones",
        ],
        "tags": ["inversion-financiamiento"],
        "kpis": [
            {"label": "Gasto ejecutado total (constante)", "metrica": "gasto_real",
             "fixed": {"clasificador": "objeto", "nivel": "total"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
            {"label": "Gasto en personal (constante)", "metrica": "gasto_real",
             "fixed": {"clasificador": "objeto", "partida": "Gastos en personal"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
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
                     {"value": "real", "label": "Constantes", "metric": "gasto_real"},
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
                     {"value": "real", "label": "Constantes", "metric": "gasto_real"}]},
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
                     {"value": "real", "label": "Constantes", "metric": "gasto_real"},
                     {"value": "pct", "label": "% del total", "metric": "gasto_corr", "percent": True, "unidad": "%"}]},
             ],
             "unidad": "pesos"},
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
            "deuda), mensual desde 2021, en pesos corrientes y constantes."
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
            {"label": "Ingresos totales (constante)", "metrica": "monto_real",
             "fixed": {"grano": "acumulado", "concepto": "Ingresos totales"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
            {"label": "Gastos totales (constante)", "metrica": "monto_real",
             "fixed": {"grano": "acumulado", "concepto": "Gastos totales"}, "year": "latest",
             "unidad": "pesos", "format": "int"},
            {"label": "Resultado financiero (% del gasto primario)",
             "tabla_label": "Resultado financiero, en % del gasto primario",
             "tabla_nota": "Gasto primario = gastos totales − intereses de la deuda. La variación va en puntos porcentuales, no en %: es un cociente. En el acumulado, la comparación válida es contra el mismo mes del año anterior.",
             "metrica": "pct_gprim",
             "fixed": {"grano": "acumulado", "concepto": "Resultado financiero"}, "year": "latest",
             "unidad": "%", "format": "int", "display": "nivel"},
            {"label": "Resultado primario (% del gasto primario)",
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"}]},
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"}]},
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"}]},
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
            "2021, en pesos corrientes y constantes. No incluye a los contribuyentes locales."
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
            {"label": "Recaudación de Ingresos Brutos (constante)", "metrica": "recaud_real",
             "fixed": {}, "year": "latest", "unidad": "pesos", "format": "int"},
            {"label": "Industria manufacturera (constante)",
             "tabla_label": "Recaudación de la industria manufacturera", "metrica": "recaud_real",
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
                     {"value": "real", "label": "Constantes", "metric": "recaud_real"}]},
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
                     {"value": "real", "label": "Constantes", "metric": "recaud_real"},
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
                     {"value": "real", "label": "Constantes", "metric": "recaud_real"}]},
             ],
             "sort": "desc", "unidad": "pesos"},
        ],
    },
    # ======================================================================
    {
        "id": "ganaderia",
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
            {"label": "Stock bovino total", "metrica": "stock_bovino",
             "fixed": {"categoria": "Total", "departamento": "Salta"}, "year": "latest",
             "unidad": "cabezas", "format": "int"},
            {"label": "Vacas", "tabla_label": "Stock de vacas", "metrica": "stock_bovino",
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
            {"label": "Empleo minero (Salta)", "tabla_label": "Empleo minero", "metrica": "empleo_min",
             "fixed": {"grano": "trimestral", "genero": "Total", "rubro": "Total"},
             "cmp": "quarter", "year": "latest", "unidad": "puestos", "format": "int"},
            {"label": "Recaudación del sector (USD, nacional)",
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
        "area": "financiero",
        "eje_pdes": "economico-productivo",
        "title": "Crédito y depósitos (BCRA)",
        "resumen": (
            "Préstamos y depósitos del sector privado en Salta según el BCRA, por departamento, en "
            "pesos corrientes y constantes; y la inclusión financiera medida por los puntos de acceso "
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
            {"label": "Préstamos al sector privado (constante)", "metrica": "monto_real",
             "fixed": {"grano": "anual", "departamento": "Salta", "operacion": "Préstamos"},
             "year": "latest_complete", "unidad": "pesos", "format": "int"},
            {"label": "Depósitos del sector privado (constante)", "metrica": "monto_real",
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"}]},
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"}]},
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
        "id": "construccion",
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
            {"label": "Superficie autorizada", "tabla_label": "Superficie autorizada a construir",
             "metrica": "superficie_m2",
             "fixed": {"grano": "anual", "municipio": "Total Salta"}, "year": "latest_complete",
             "unidad": "m²", "format": "int"},
            {"label": "Permisos otorgados", "tabla_label": "Permisos de edificación otorgados",
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
            "departamento, en pesos corrientes y constantes, mensual desde 2021."
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
            {"label": "Recursos a municipios (constante)", "metrica": "monto_real",
             "fixed": {"grano": "anual"}, "year": "latest_complete", "unidad": "pesos", "format": "int"},
            {"label": "Coparticipación (constante)", "tabla_label": "Coparticipación a municipios",
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"},
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"}]},
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
                     {"value": "real", "label": "Constantes", "metric": "monto_real"}]},
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
        "title": "Energía eléctrica y renovables",
        "resumen": (
            "Generación de energía eléctrica en Salta según CAMMESA, por fuente (hidráulica, térmica "
            "y renovable), la participación de las renovables en la matriz y la potencia instalada por "
            "central, desde 2019."
        ),
        "resumen_corto": "Generación eléctrica por fuente y peso de las renovables.",
        "fuente": "CAMMESA — Informe de síntesis mensual",
        "fuente_url": "https://cammesaweb.cammesa.com/",
        "cobertura": "2019–2026",
        "keywords": [
            "energía", "electricidad", "generación", "renovable", "renovables", "solar", "hidráulica",
            "térmica", "biomasa", "CAMMESA", "potencia instalada", "MW", "GWh", "matriz energética",
            "Cafayate", "Altiplano", "Ley 27191", "parques solares",
        ],
        "tags": ["infraestructura-logistica", "innovacion-mercados"],
        "kpis": [
            {"label": "Participación renovable", "tabla_label": "Participación renovable en la generación",
             "metrica": "share_renovable_pct",
             "fixed": {"grano": "trimestral"}, "cmp": "quarter", "year": "latest",
             "unidad": "%", "format": "int"},
            {"label": "Potencia instalada", "tabla_nota": "Es un stock (fotografía), no un flujo: no corresponde variación interanual.",
             "metrica": "potencia_mw",
             "fixed": {"grano": "anual"}, "year": "latest", "unidad": "MW", "format": "int"},
        ],
        "charts": [
            {"id": "ren-fuente", "type": "stacked-area",
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
            {"id": "ren-central-gen", "type": "barh",
             "title": "Generación por central",
             "descr": "Ranking de centrales por energía generada, para el año seleccionado.",
             "x": "central", "seriesBy": None, "metrica": "gen_central_gwh",
             "fixed": {"grano": "anual"},
             "controls": [{"dim": "anio", "label": "Año", "kind": "year"}],
             "sort": "desc", "unidad": "GWh"},
            {"id": "ren-potencia", "type": "barh",
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
            {"label": "Inversión en I+D (constante)", "metrica": "inv_id_real",
             "fixed": {}, "year": "latest", "unidad": "millones de $", "format": "int"},
            {"label": "Investigadores/as y becarios/as", "metrica": "personal_id",
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
            {"label": "Exportaciones totales", "metrica": "fob_usd",
             "fixed": {}, "year": "latest", "unidad": "USD", "format": "int"},
            {"label": "Volumen exportado", "metrica": "peso_ton",
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
]


def tema_by_id(tid):
    for t in TEMAS:
        if t["id"] == tid:
            return t
    raise KeyError(tid)
