# -*- coding: utf-8 -*-
"""
build.py — Construye el sitio estático del Monitor de Indicadores CESS.

Pasos:
  1. Por cada tema: corre su adapter -> datos canónicos largos.
  2. Control de calidad numérico (skill `datasets`): formato inglés + saltos de magnitud.
  3. Resuelve años ('latest' / 'latest_complete') y completa los controles de filtro.
  4. Escribe data/<id>.json (datos + specs) y data/catalog.json (manifiesto liviano).
  5. Renderiza index.html y tema/<id>.html con Jinja2.
  6. Escribe BUILD_NOTES.md (metodología del build).

Uso:  python build.py
Requisitos:  pip install pandas jinja2
"""
import os
import json
import math
import time
import statistics
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader, select_autoescape

import catalog
import adapters

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_OUT = os.path.join(HERE, "data")
TEMA_OUT = os.path.join(HERE, "tema")
TEMPLATES = os.path.join(HERE, "templates")


# --------------------------------------------------------------------------
# Control de calidad numérico (skill datasets): saltos de orden de magnitud.
# Los CSV de origen ya están en formato inglés (decimal `.`); acá verificamos.
# --------------------------------------------------------------------------
def qc_saltos(fields, rows):
    mi, mv = fields.index("metrica"), fields.index("valor")
    por_metrica = defaultdict(list)
    for r in rows:
        por_metrica[r[mi]].append(r[mv])
    incidencias = []
    for met, vals in por_metrica.items():
        positivos = [v for v in vals if isinstance(v, (int, float)) and v > 0]
        if len(positivos) < 5:
            continue
        med = statistics.median(positivos)
        if med <= 0:
            continue
        raros = [v for v in positivos if v / med > 1000 or v / med < 0.001]
        if raros:
            incidencias.append(f"{met}: {len(raros)} valor(es) a >1000× de la mediana "
                               f"(mediana={med:g}); revisar posible artefacto de parseo.")
    return incidencias


def anio_latest(dims):
    return max(dims["anio"])


GEO_DIMS = ("departamento", "municipio", "unidad_geografica", "localidad")

# Agregados no departamentales que no deben indexarse como "departamento" en el buscador.
NON_DEPT = {"Argentina", "Nacional", "Nación", "Nacion", "País", "Pais", "Total", "Total país",
            "Total pais", "Región Norte", "Region Norte", "NOROESTE", "Noroeste", "Provincia"}


def geo_values(dims):
    """Valores geográficos (departamentos/municipios/localidades) con datos, para el buscador."""
    vals, seen = [], set()
    excl = adapters.NON_GEO | adapters.PROVINCIAL_TOKENS | NON_DEPT
    for dim in GEO_DIMS:
        for v in dims.get(dim, []):
            if v in excl or v in seen:
                continue
            seen.add(v)
            vals.append(v)
    return sorted(vals)


def anio_latest_complete(fields, rows):
    """Último año completo (12 meses mensuales o 4 trimestres) para no mostrar años parciales."""
    if "mes" in fields and "grano" in fields:
        gi, ai, mi = fields.index("grano"), fields.index("anio"), fields.index("mes")
        meses = defaultdict(set)
        for r in rows:
            if r[gi] == "mensual":
                meses[r[ai]].add(r[mi])
        completos = [a for a, ms in meses.items() if len(ms) >= 12]
        if completos:
            return max(completos)
    if "trimestre" in fields:
        ti, ai = fields.index("trimestre"), fields.index("anio")
        trims = defaultdict(set)
        for r in rows:
            if r[ti]:
                trims[r[ai]].add(r[ti])
        completos = [a for a, ts in trims.items() if len(ts) >= 4]
        if completos:
            return max(completos)
    return None


# --------------------------------------------------------------------------
# Resolución de specs: años + valores de controles resueltos para el front.
# --------------------------------------------------------------------------
def resolver_anio(spec_year, dims, fields, rows):
    if isinstance(spec_year, int):
        return spec_year
    if spec_year == "latest_complete":
        ac = anio_latest_complete(fields, rows)
        if ac is not None:
            return ac
    return anio_latest(dims)


def resolver_kpi_cmp(k, dims, fields, rows, trims_completos):
    """Devuelve {"dim","now","prev"} para la variación interanual del KPI.
    cmp=='quarter': último trimestre completo vs el mismo trimestre del año anterior.
    default: último año con dato vs el año anterior con dato (variación anual)."""
    if k.get("cmp") == "quarter" and trims_completos:
        now = trims_completos[-1]
        y, q = now.split("-T")
        prev = f"{int(y) - 1}-T{q}"
        if prev not in trims_completos:
            prev = None
        return {"dim": "trimestre", "now": now, "prev": prev}

    # Variación anual (por defecto)
    mi, ai = fields.index("metrica"), fields.index("anio")
    fx = [(fields.index(d), v) for d, v in k.get("fixed", {}).items() if d in fields and d != "anio"]
    anios = set()
    for row in rows:
        if row[mi] != k["metrica"]:
            continue
        if all(str(row[i]) == str(v) for i, v in fx):
            anios.add(row[ai])
    anios = sorted(anios)

    if isinstance(k["year"], int):
        anio = k["year"]
    elif not anios:
        anio = anio_latest(dims)
    elif k["year"] == "latest_complete":
        lc = anio_latest_complete(fields, rows)
        anio = lc if lc in anios else anios[-1]
    else:
        anio = anios[-1]

    previos = [a for a in anios if a < anio]
    anio_prev = previos[-1] if previos else None
    return {"dim": "anio", "now": anio, "prev": anio_prev}


def _years_for_metric(chart, fields, rows):
    """Años con dato para la métrica base del gráfico (evita defaults en años sin datos).
    Si el gráfico fija `grano` (p. ej. un ranking anual), sólo cuentan los años con datos
    en ese grano — así el selector no ofrece un año que en ese grano quedaría vacío."""
    if not (fields and rows) or "anio" not in fields or "metrica" not in fields:
        return None
    mi, ai = fields.index("metrica"), fields.index("anio")
    met = chart.get("metrica")
    gi = fields.index("grano") if "grano" in fields else None
    grano_fijo = chart.get("fixed", {}).get("grano")
    ys = sorted({row[ai] for row in rows if row[mi] == met
                 and (gi is None or grano_fijo is None or row[gi] == grano_fijo)})
    return ys or None


def preparar_controles(chart, dims, metricas, anio_default, fields=None, rows=None):
    yrs_metric = _years_for_metric(chart, fields, rows)
    for c in chart.get("controls", []):
        kind = c.get("kind")
        if kind == "year":
            yrs = yrs_metric or dims["anio"]
            c["values"] = yrs
            c["default"] = anio_default if anio_default in yrs else yrs[-1]
        elif kind == "select":
            c["values"] = dims.get(c["dim"], [])
        elif kind == "metric":
            c["labels"] = {m: metricas.get(m, {}).get("label", m) for m in c["options"]}
            c["unidades"] = {m: metricas.get(m, {}).get("unidad", "") for m in c["options"]}
    return chart


def construir_tema(tmeta):
    data = adapters.ADAPTERS[tmeta["id"]]()
    fields, rows, dims, metricas = data["fields"], data["rows"], data["dims"], data["metricas"]
    trims_completos = data.get("trims_completos", [])
    notas = list(data.get("notas", []))
    notas += qc_saltos(fields, rows)

    a_latest = anio_latest(dims)
    a_complete = anio_latest_complete(fields, rows) or a_latest

    # KPIs: la comparación interanual del último dato se calcula en el navegador
    # (charts.js renderKpis), ligada a la frecuencia del gráfico conductor.
    kpis = []
    for k in tmeta["kpis"]:
        met = metricas.get(k["metrica"], {})
        kpis.append({**k,
                     "agg": met.get("agg", "sum"),
                     "metrica_label": met.get("label", k["metrica"])})

    # Charts: resolver controles
    charts = []
    for ch in tmeta["charts"]:
        ch = json.loads(json.dumps(ch))  # copia profunda
        anio_def = a_complete if ch.get("grano") == "anual" or "grano" in ch.get("fixed", {}) else a_latest
        if ch.get("grano") == "mensual" or ch.get("fixed", {}).get("grano") == "mensual":
            anio_def = a_latest
        preparar_controles(ch, dims, metricas,
                           anio_def if ch.get("fixed", {}).get("grano") != "anual" else a_complete,
                           fields=fields, rows=rows)
        if ch.get("x") in ("departamento", "municipio", "unidad_geografica", "localidad"):
            ch["exclude"] = sorted(adapters.NON_GEO | adapters.PROVINCIAL_TOKENS)
        # Fuente efectiva: propia del gráfico o heredada del tema.
        ch["fuente"] = ch.get("fuente") or tmeta["fuente"]
        ch["fuente_url"] = ch.get("fuente_url") or tmeta.get("fuente_url", "")
        charts.append(ch)

    area = catalog.AREAS[tmeta["area"]]
    payload = {
        "id": tmeta["id"], "title": tmeta["title"], "area": tmeta["area"],
        "eje_pdes": tmeta.get("eje_pdes"),
        "area_label": area["label"], "resumen": tmeta["resumen"],
        "resumen_corto": tmeta.get("resumen_corto", tmeta["resumen"]),
        "fuente": tmeta["fuente"], "fuente_url": tmeta["fuente_url"],
        "cobertura": tmeta["cobertura"], "keywords": tmeta["keywords"],
        "tags": tmeta.get("tags", []),
        "dims": dims, "metricas": metricas,
        "fields": fields, "rows": rows,
        "kpis": kpis, "charts": charts,
    }
    return payload, notas


def escribir_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main():
    for d in (DATA_OUT, TEMA_OUT):
        os.makedirs(d, exist_ok=True)

    env = Environment(loader=FileSystemLoader(TEMPLATES),
                      autoescape=select_autoescape(["html", "xml"]))
    asset_ver = str(int(time.time()))   # cache-busting de CSS/JS locales por build

    catalogo = []
    todas_notas = {}
    resumen_build = []

    for tmeta in catalog.TEMAS:
        payload, notas = construir_tema(tmeta)
        escribir_json(os.path.join(DATA_OUT, f"{payload['id']}.json"), payload)
        todas_notas[payload["id"]] = notas
        resumen_build.append((payload["id"], len(payload["rows"]), payload["cobertura"]))

        # Documento liviano para landing + buscador (sin filas de datos)
        tags = payload["tags"]
        catalogo.append({
            "id": payload["id"], "title": payload["title"], "area": payload["area"],
            "eje_pdes": payload["eje_pdes"],
            "eje_pdes_label": catalog.EJES_PDES.get(payload["eje_pdes"], {}).get("label", ""),
            "area_label": payload["area_label"], "resumen": payload["resumen"],
            "resumen_corto": payload["resumen_corto"],
            "fuente": payload["fuente"], "fuente_url": payload["fuente_url"],
            "cobertura": payload["cobertura"], "keywords": payload["keywords"],
            "tags": tags,
            "tags_labels": [catalog.TAGS[t]["label"] for t in tags if t in catalog.TAGS],
            "departamentos": geo_values(payload["dims"]),
            "metricas": [m["label"] for m in payload["metricas"].values()],
            "charts": [{"id": c["id"], "title": c["title"], "descr": c["descr"],
                        "fuente": c["fuente"], "fuente_url": c["fuente_url"]} for c in payload["charts"]],
        })

    # Ordenar catálogo por área y título
    catalogo.sort(key=lambda t: (catalog.AREAS[t["area"]]["orden"], t["title"]))
    escribir_json(os.path.join(DATA_OUT, "catalog.json"),
                  {"site": catalog.SITE, "areas": catalog.AREAS,
                   "tags": catalog.TAGS, "ejes_pdes": catalog.EJES_PDES,
                   "temas": catalogo})

    # Agrupar en DOS NIVELES: eje del PDES (nivel 1) y, dentro, eje transversal / tag (nivel 2).
    # Un tema puede aparecer en varios subgrupos dentro de su eje. Solo se muestran ejes/subgrupos
    # con temas.
    ejes_pdes = []
    for eje_id, eje in sorted(catalog.EJES_PDES.items(), key=lambda kv: kv[1]["orden"]):
        temas_eje = [t for t in catalogo if t.get("eje_pdes") == eje_id]
        if not temas_eje:
            continue
        subgrupos = []
        for tid, tg in sorted(catalog.TAGS.items(), key=lambda kv: kv[1]["orden"]):
            temas_tag = [t for t in temas_eje if tid in t.get("tags", [])]
            if temas_tag:
                subgrupos.append({"id": tid, "label": tg["label"],
                                  "descr": tg.get("descr", ""), "temas": temas_tag})
        con_tag = {t["id"] for sg in subgrupos for t in sg["temas"]}
        sueltos = [t for t in temas_eje if t["id"] not in con_tag]
        if sueltos:
            subgrupos.append({"id": "otros", "label": "Otros indicadores",
                              "descr": "", "temas": sueltos})
        ejes_pdes.append({"id": eje_id, "label": eje["label"], "descr": eje.get("descr", ""),
                          "temas": temas_eje, "subgrupos": subgrupos})

    # index.html
    tpl_index = env.get_template("index.html")
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(tpl_index.render(site=catalog.SITE, ejes=ejes_pdes, base=".", asset_ver=asset_ver))

    # tema/<id>.html
    tpl_tema = env.get_template("tema.html")
    for t in catalogo:
        with open(os.path.join(TEMA_OUT, f"{t['id']}.html"), "w", encoding="utf-8") as f:
            f.write(tpl_tema.render(site=catalog.SITE, ejes=ejes_pdes, tema=t, base="..", asset_ver=asset_ver))

    # BUILD_NOTES.md
    escribir_build_notes(todas_notas, resumen_build)

    print("BUILD OK")
    for tid, n, cob in resumen_build:
        print(f"  {tid:22s} {n:6d} filas  {cob}")
    print(f"  {len(catalogo)} temas | index.html + {len(catalogo)} páginas de tema")


def escribir_build_notes(todas_notas, resumen_build):
    lines = [
        "# Metodología del build — Monitor de Indicadores CESS",
        "",
        "Generado por `build.py`. Convierte los CSV tidy de los indicadores en JSON para el sitio.",
        "",
        "## Formato numérico",
        "Los CSV de origen (`Actualizar_*` / scripts) ya están en **formato inglés** "
        "(decimal `.`, sin separador de miles), UTF-8-sig. El build los lee como numéricos y "
        "**no** aplica conversión de separadores. Se verifica ausencia de saltos de orden de "
        "magnitud espurios por métrica.",
        "",
        "## Transformaciones por tema",
        "- **educacion**: normalización de nombres de departamento a Title Case con acentos; "
        "se excluyen `Enmascarado`/`Sin datos` de los rankings por departamento.",
        "- **vitivinicultura**: sin transformación de valores (ya tidy).",
        "- **produccion-energia**: `melt` de las 10 medidas físicas a `metrica`/`valor`; se "
        "descartan `iny_gas`, `iny_co2`, `vida_util` (todos 0 en Salta). La serie temporal se "
        "agrega por **trimestre** (suma de meses, por tipo de recurso); el ranking usa el total "
        "anual oficial.",
        "- **empleo**: empleo por rubro/departamento y remuneración real, agregados por "
        "**trimestre** y por **año** (media de los meses del período). La remuneración es un "
        "**índice de salario real** deflactado por el **IPC NOA** (serie "
        "`145.3_INGNOANOA_DICI_M_10` de datos.gob.ar, base dic-2016), rebasado a **dic-2023 = 100** "
        "por serie; la provincial es media ponderada por empleo (Σ empleo·salario / Σ empleo). Se "
        "incluyen períodos parciales (2025); el KPI compara el último trimestre completo contra el "
        "mismo trimestre del año anterior.",
        "",
        "## Fuentes externas materializadas",
        "- `ipc_noa_mensual.csv` — IPC Nivel General región NOA (INDEC), vía "
        "`https://apis.datos.gob.ar/series/api/series?ids=145.3_INGNOANOA_DICI_M_10&format=csv`. "
        "Refrescar volviendo a descargar ese CSV.",
        "",
        "## Incidencias detectadas",
    ]
    hubo = False
    for tid, notas in todas_notas.items():
        if notas:
            hubo = True
            lines.append(f"### {tid}")
            for n in notas:
                lines.append(f"- {n}")
    if not hubo:
        lines.append("- Sin incidencias detectadas (formato numérico consistente; sin saltos de magnitud espurios).")
    lines += ["", "## Control (filas por tema)"]
    for tid, n, cob in resumen_build:
        lines.append(f"- `{tid}`: {n} filas, cobertura {cob}.")
    lines.append("")
    with open(os.path.join(HERE, "BUILD_NOTES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
