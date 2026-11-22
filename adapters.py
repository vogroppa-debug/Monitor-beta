# -*- coding: utf-8 -*-
"""
adapters.py — Normaliza cada CSV tidy de indicadores CESS al ESQUEMA CANÓNICO largo.

Esquema canónico de salida (una fila = una observación):
    <dimensiones...> , metrica , valor
donde entre las dimensiones siempre hay un eje temporal (`anio` y/o `periodo`) y,
cuando aplica, una geografía (`departamento` / `unidad_geografica`).

Cada adapter devuelve un dict:
    {
      "fields":  [nombres de columna, la última siempre "valor", la anterior "metrica"],
      "rows":    [[...], ...],                 # valores; `valor` en formato inglés (decimal .)
      "dims":    {dim: [valores ordenados]},   # valores disponibles por dimensión (para filtros)
      "metricas":{clave: {"label":..., "unidad":...}},
      "notas":   [incidencias detectadas para BUILD_NOTES.md],
    }

Por defecto se lee el CSV ya generado (contrato tidy). El build no re-descarga nada.
"""
import os
import math
import functools
import unicodedata
import pandas as pd
import openpyxl

# Los datos fuente se versionan JUNTO al sitio, en sitio-indicadores/datos/, para que
# cualquier clon del repositorio pueda correr build.py. Antes vivían en la carpeta padre y en
# datos-drive/, fuera del repo: una máquina que clonaba no podía reconstruir nada, y un build
# con archivos faltantes se cae a mitad dejando JSON degradados. La procedencia de cada
# archivo (carpetas de Drive) está documentada en README.md.
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")


def _src(name):
    return os.path.join(DATA_DIR, name)


def _drv(name):
    """Alias de `_src`: la separación datos-drive/ desapareció al unificar en datos/.
    Se conserva el nombre para no tocar las llamadas de cada adapter."""
    return _src(name)


@functools.lru_cache(maxsize=1)
def _ipc_anual():
    """IPC NOA promedio anual (base dic-2016=100). Clave: año (int).

    Sólo años COMPLETOS: el promedio de un año a medio publicar no es el nivel de precios de ese
    año y además se mueve con cada mes nuevo del IPC, así que deflactar con él daría una serie que
    cambia sola sin que cambie el dato. El año incompleto queda sin deflactor y el adaptador
    simplemente no emite su valor real (todos los `real()` devuelven None si falta el índice).
    """
    df = pd.read_csv(_src("ipc_noa_mensual.csv"), encoding="utf-8")
    df["anio"] = df["indice_tiempo"].astype(str).str[:4].astype(int)
    g = df.groupby("anio")["ipc_ng_noa"]
    return {a: v for a, v in g.mean().items() if g.size()[a] == 12}


# ------------------------------------------------------------------ base de los pesos constantes
# La base NO es un año fijo: es el ÚLTIMO mes publicado del IPC, así que se recalcula sola en cada
# build y avanza cuando se actualiza `ipc_noa_mensual.csv`. Es una sola para todo el sitio, de modo
# que los montos reales de un tablero se pueden comparar con los de otro.
_MESES = ["ene", "feb", "mar", "abr", "may", "jun",
          "jul", "ago", "sep", "oct", "nov", "dic"]
_MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


@functools.lru_cache(maxsize=1)
def _ipc_base():
    """Período base de los pesos constantes: (AAAAMM, índice) del último mes con IPC publicado."""
    m = {k: v for k, v in _ipc_noa_map().items() if pd.notna(v)}
    p = max(m)
    return p, float(m[p])


def _base_txt(largo=False):
    """Nombre del período base: 'jul-2026' o 'julio de 2026'.

    La forma corta sigue la convención que el repo ya usa en prosa (dic-2016, dic-2023) y es la que
    va en las etiquetas; la larga, en las notas."""
    p, _ = _ipc_base()
    y, m = divmod(p, 100)
    return ("%s de %d" % (_MESES_LARGO[m - 1], y)) if largo else ("%s-%d" % (_MESES[m - 1], y))


def base_txt():
    """(corto, largo) del período base, para que `build.py` resuelva los marcadores {base} y
    {base_largo} del catálogo. `catalog.py` es un spec estático y no puede leer el CSV del IPC:
    vive fuera del repo."""
    return _base_txt(), _base_txt(True)


def _con_base(metricas, *claves):
    """Copia de `metricas` con el período base escrito en la etiqueta de las métricas indicadas.

    La base sale del dato, así que la etiqueta no puede ser un literal. Se resuelve acá y no a nivel
    de módulo porque `ipc_noa_mensual.csv` vive fuera del repo: leerlo al importar rompería a quien
    importa `adapters` sólo por las constantes geográficas (ver `indicadores.py`).
    """
    txt = _base_txt()
    out = dict(metricas)
    for k in claves:
        out[k] = dict(out[k], label=out[k]["label"].replace(
            "pesos constantes", "pesos constantes de " + txt))
    return out


def _xlsx_rows(path, sheet=None, header_row=0):
    """Lee una hoja xlsx (valores cacheados) -> (encabezado, [dict por fila])."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
    data = list(ws.iter_rows(values_only=True))
    wb.close()
    hdr = list(data[header_row])
    out = [dict(zip(hdr, row)) for row in data[header_row + 1:]]
    return hdr, out


# --------------------------------------------------------------------------
# Normalización de nombres de departamento de Salta (Title Case con acentos).
# Los CSV vienen con distinto casing (MAYÚSCULAS en educación, Title en el resto).
# --------------------------------------------------------------------------
_DEPT_CANON = {
    "ANTA": "Anta", "CACHI": "Cachi", "CAFAYATE": "Cafayate", "CAPITAL": "Capital",
    "CERRILLOS": "Cerrillos", "CHICOANA": "Chicoana", "GENERAL GUEMES": "General Güemes",
    "GENERAL JOSE DE SAN MARTIN": "General José de San Martín", "GUACHIPAS": "Guachipas",
    "IRUYA": "Iruya", "LA CALDERA": "La Caldera", "LA CANDELARIA": "La Candelaria",
    "LA POMA": "La Poma", "LA VINA": "La Viña", "LOS ANDES": "Los Andes", "METAN": "Metán",
    "MOLINOS": "Molinos", "ORAN": "Orán", "RIVADAVIA": "Rivadavia",
    "ROSARIO DE LA FRONTERA": "Rosario de la Frontera", "ROSARIO DE LERMA": "Rosario de Lerma",
    "SAN CARLOS": "San Carlos", "SANTA VICTORIA": "Santa Victoria",
}
# Valores que NO son un departamento real (datos enmascarados / sin asignar).
NON_GEO = {"Enmascarado", "Sin datos", "Sin asignar", "Sin Asignar", "SIN DATOS", "ENMASCARADO",
           "Otros Deptos./Local. No Publicables", "Otros Deptos./Local. No Publicable"}
# Tokens de agregado provincial (no son un departamento/municipio; se excluyen de rankings).
# "Total Salta" se usa donde "Salta" ya es un municipio real (Ciudad de Salta), p. ej. construcción.
PROVINCIAL_TOKENS = {"Salta", "Total Salta"}
# Agregados de nivel nacional o regional: no son una unidad territorial DENTRO de Salta, así que
# ni se indexan como departamento en el buscador ni cuentan como desagregación territorial.
NON_DEPT = {"Argentina", "Nacional", "Nación", "Nacion", "País", "Pais", "Total", "Total país",
            "Total pais", "Región Norte", "Region Norte", "NOROESTE", "Noroeste", "Provincia"}


def _unacc_upper(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c)).upper().strip()


def norm_dept(s):
    """Devuelve el nombre canónico del departamento, o el token especial tal cual."""
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return None
    raw = str(s).strip()
    if raw in NON_GEO:
        return raw
    key = _unacc_upper(raw)
    if key in NON_GEO:
        return "Sin datos" if "DATO" in key else ("Sin asignar" if "ASIGNAR" in key else raw.title())
    return _DEPT_CANON.get(key, raw.title())


def _sorted_unique(series):
    return sorted([v for v in series.dropna().unique().tolist()], key=lambda x: str(x))


# ==========================================================================
# TEMA 1 — Educación por departamento
# ==========================================================================
EDU_METRICAS = {
    "matricula":         {"label": "Matrícula",             "unidad": "alumnos"},
    "egresados":         {"label": "Egresados",             "unidad": "alumnos"},
    "repitentes":        {"label": "Repitentes",            "unidad": "alumnos"},
    "sobreedad_alumnos": {"label": "Alumnos con sobreedad", "unidad": "alumnos"},
    "extranjeros":       {"label": "Alumnos extranjeros",   "unidad": "alumnos"},
    "cargos":            {"label": "Cargos docentes",       "unidad": "cargos"},
    "horas":             {"label": "Horas cátedra",         "unidad": "horas"},
}


def educacion():
    df = pd.read_csv(_src("educacion_departamentos_salta_tidy.csv"), encoding="utf-8-sig")
    df["departamento"] = df["departamento"].map(norm_dept)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    notas = []
    n_bad = int(df["valor"].isna().sum())
    if n_bad:
        notas.append(f"educacion: {n_bad} valores no numéricos descartados.")
    df = df.dropna(subset=["valor"])
    fields = ["anio", "departamento", "sector", "ambito", "nivel", "metrica", "valor"]
    df = df[fields]
    return {
        "fields": fields,
        "rows": df.values.tolist(),
        "dims": {
            "anio": _sorted_unique(df["anio"]),
            "departamento": [d for d in _sorted_unique(df["departamento"]) if d not in NON_GEO],
            "sector": _sorted_unique(df["sector"]),
            "ambito": _sorted_unique(df["ambito"]),
            "nivel": ["inicial", "primaria", "secundaria"],
        },
        "metricas": EDU_METRICAS,
        "notas": notas,
    }


# ==========================================================================
# TEMA 2 — Vitivinicultura (INV)
# ==========================================================================
INV_METRICAS = {
    "produccion_uva":           {"label": "Producción de uva",        "unidad": "quintales"},
    "elaboracion_total":        {"label": "Elaboración (vino+mosto)",  "unidad": "hectolitros"},
    "despacho_mercado_interno": {"label": "Despacho al mercado interno", "unidad": "hectolitros"},
    "export_volumen":           {"label": "Exportaciones (volumen)",   "unidad": "hectolitros"},
    "export_valor_fob":         {"label": "Exportaciones (valor FOB)", "unidad": "miles US$"},
    "import_volumen":           {"label": "Importaciones (nacional)",  "unidad": "hectolitros"},
}


def inv():
    df = pd.read_csv(_src("inv_salta_tidy.csv"), encoding="utf-8-sig")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    fields = ["anio", "categoria", "nivel", "unidad_geografica", "metrica", "valor"]
    df = df[fields]
    return {
        "fields": fields,
        "rows": df.values.tolist(),
        "dims": {
            "anio": _sorted_unique(df["anio"]),
            "categoria": _sorted_unique(df["categoria"]),
            "nivel": _sorted_unique(df["nivel"]),
            "unidad_geografica": _sorted_unique(df["unidad_geografica"]),
        },
        "metricas": INV_METRICAS,
        "notas": [],
    }


# ==========================================================================
# TEMA 3 — Producción de petróleo y gas (melt de medidas → metrica/valor)
# ==========================================================================
PROD_MEAS = ["prod_pet", "prod_gas", "prod_agua", "iny_agua", "iny_otro", "tef", "pozos"]
PROD_METRICAS = {
    "prod_pet":  {"label": "Producción de petróleo", "unidad": "m³"},
    "prod_gas":  {"label": "Producción de gas",      "unidad": "miles de m³"},
    "prod_agua": {"label": "Producción de agua",     "unidad": "m³"},
    "iny_agua":  {"label": "Inyección de agua",      "unidad": "m³"},
    "iny_otro":  {"label": "Inyección (otros)",      "unidad": "m³"},
    "tef":       {"label": "Tiempo efectivo",        "unidad": "pozos-mes"},
    "pozos":     {"label": "Pozos",                  "unidad": "pozos"},
}


def _melt_prod(df, id_cols):
    df = df.copy()
    df["departamento"] = df["departamento"].map(norm_dept)
    keep = id_cols + [m for m in PROD_MEAS if m in df.columns]
    long = df[keep].melt(id_vars=id_cols, var_name="metrica", value_name="valor")
    long["valor"] = pd.to_numeric(long["valor"], errors="coerce")
    long = long.dropna(subset=["valor"])
    return long


def produccion_energia():
    """Combina la serie MENSUAL (para el eje temporal) y la ANUAL (para ranking)."""
    mens = pd.read_csv(_src("Produccion_Petroleo_Gas_Salta_por_departamento_desde_2018.csv"),
                       encoding="utf-8-sig")
    anual = pd.read_csv(_src("Produccion_Petroleo_Gas_Salta_por_departamento_anual.csv"),
                        encoding="utf-8-sig")

    long_m = _melt_prod(mens, ["departamento", "anio", "mes", "tipo_de_recurso"])
    long_m["anio"] = long_m["anio"].astype(int)
    long_m["mes"] = long_m["mes"].astype(int)
    long_m["trimestre"] = [_trim_label(a, m) for a, m in zip(long_m["anio"], long_m["mes"])]

    # Descartar meses finales "stub" (dato preliminar que cae a ~0): distorsionarían el
    # trimestre en curso. Regla: un mes final cuya producción de gas es < 10 % del mes previo.
    _gm = (long_m[long_m["metrica"] == "prod_gas"].groupby(["anio", "mes"])["valor"].sum()
           .reset_index().sort_values(["anio", "mes"]))
    _v = _gm["valor"].tolist()
    _ym = list(zip(_gm["anio"].astype(int), _gm["mes"].astype(int)))
    _drop = set()
    for i in range(len(_v) - 1, 0, -1):
        if _v[i] < 0.10 * _v[i - 1]:
            _drop.add(_ym[i])
        else:
            break
    if _drop:
        long_m = long_m[~long_m.apply(lambda x: (int(x["anio"]), int(x["mes"])) in _drop, axis=1)]

    # TRIMESTRAL por tipo de recurso: los flujos (m³) se SUMAN dentro del trimestre.
    trim = (long_m.groupby(["departamento", "anio", "trimestre", "tipo_de_recurso", "metrica"],
                           as_index=False)["valor"].sum())
    trim.insert(0, "grano", "trimestral")

    # ANUAL oficial (para ranking y KPIs), tipo agregado "TOTAL".
    long_a = _melt_prod(anual, ["departamento", "anio"])
    long_a["anio"] = long_a["anio"].astype(int)
    long_a["trimestre"] = ""
    long_a["tipo_de_recurso"] = "TOTAL"
    long_a.insert(0, "grano", "anual")

    fields = ["grano", "departamento", "anio", "trimestre", "tipo_de_recurso", "metrica", "valor"]
    both = pd.concat([trim[fields], long_a[fields]], ignore_index=True)

    # El eje temporal trimestral no debe mostrar el último trimestre parcial (caída ficticia).
    trims_ok, _anios_ok, _tl = _completos(long_m, mes_col="mes")
    rows = _keep_completos(both.values.tolist(), trims_ok, anios_ok=None, gi=0, ai=2, ti=3)

    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": _sorted_unique(both["anio"]),
            "departamento": [d for d in _sorted_unique(long_a["departamento"]) if d not in NON_GEO],
            "tipo_de_recurso": ["CONVENCIONAL", "NO CONVENCIONAL", "NO DISCRIMINADO"],
            "trimestre": sorted(trims_ok, key=_trim_key),
        },
        "metricas": PROD_METRICAS,
        "notas": ["produccion_energia: se descartan iny_gas, iny_co2 y vida_util (todos 0 en Salta).",
                  "produccion_energia: serie temporal agregada por TRIMESTRE (suma de meses); "
                  "el ranking y los KPIs usan el total anual oficial."],
    }


# ==========================================================================
# TEMA 4 — Empleo registrado y remuneraciones (OEDE) por rubro y departamento
#   · empleo:         puestos registrados del sector privado (SUMABLE)
#   · remun_real_idx: índice de remuneración media real, deflactada por IPC NOA,
#                     base dic-2023 = 100, por serie (NO sumable).
# ==========================================================================
EMPLEO_METRICAS = {
    "empleo":         {"label": "Empleo registrado",                        "unidad": "puestos", "agg": "sum"},
    "remun_real_idx": {"label": "Remuneración real (índice dic-2023 = 100)", "unidad": "índice",  "agg": "mean"},
}

# Nombres de sector (rubro) del archivo OEDE: se corrigen tildes/typos de origen.
_RUBRO_LABEL = {
    "Agricultura, ganaderia y pesca":  "Agricultura, ganadería y pesca",
    "Comercio":                        "Comercio",
    "Construccion":                    "Construcción",
    "Electircidad, gas y agua":        "Electricidad, gas y agua",
    "Explotacion de minas y canteras": "Explotación de minas y canteras",
    "Industria manufacturera":         "Industria manufacturera",
    "Servicios":                       "Servicios",
    "Sin rama":                        "Sin rama",
}


@functools.lru_cache(maxsize=1)
def _ipc_noa_map():
    """Serie IPC Nivel General región NOA (base dic-2016=100). Clave: periodo AAAAMM (int).

    Cacheada: además de ahorrar cinco lecturas del CSV, hace que la base de los pesos constantes
    sea LA MISMA para todos los tableros aunque el archivo cambie durante la corrida."""
    df = pd.read_csv(_src("ipc_noa_mensual.csv"), encoding="utf-8")
    ym = df["indice_tiempo"].astype(str).str.slice(0, 7).str.replace("-", "", regex=False).astype(int)
    return dict(zip(ym, pd.to_numeric(df["ipc_ng_noa"], errors="coerce")))


def _wide_long(name, timecol):
    """Archivo ancho (timecol × columnas de departamento) -> largo [timecol, departamento, valor]."""
    df = pd.read_csv(_src(name), encoding="utf-8-sig")
    long = df.melt(id_vars=[timecol], var_name="departamento", value_name="valor")
    long["departamento"] = long["departamento"].map(norm_dept)
    long["valor"] = pd.to_numeric(long["valor"], errors="coerce")
    return long.dropna(subset=["valor"])


def _trim_label(anio, mes):
    return f"{int(anio)}-T{(int(mes) - 1) // 3 + 1}"


def _trim_key(t):
    y, q = t.split("-T")
    return (int(y), int(q))


def _completos(mensual, mes_col="mes"):
    """A partir de un df mensual (con columnas `anio`, `trimestre` y una de mes),
    devuelve (set trimestres completos>=3 meses, set años completos>=12 meses)
    y la lista ordenada de trimestres completos. Sirve para no emitir períodos
    parciales (típicamente el último), que dibujarían una caída ficticia."""
    mc = mensual.groupby("trimestre")[mes_col].nunique()
    trims_ok = sorted([t for t, n in mc.items() if n >= 3], key=_trim_key)
    yc = mensual.groupby("anio")[mes_col].nunique()
    anios_ok = {int(a) for a, n in yc.items() if n >= 12}
    return set(trims_ok), anios_ok, trims_ok


def _keep_completos(rows, trims_ok, anios_ok=None, gi=0, ai=1, ti=2):
    """Filtra filas de series temporales: descarta trimestres incompletos y,
    si se pasa anios_ok, también años incompletos. `rows` es lista de listas con
    grano en gi, anio en ai y etiqueta de trimestre en ti."""
    out = []
    for r in rows:
        if r[gi] == "trimestral" and r[ti] not in trims_ok:
            continue
        if anios_ok is not None and r[gi] == "anual" and int(r[ai]) not in anios_ok:
            continue
        out.append(r)
    return out


def _add_tiempo(df):
    """Agrega columnas anio/mes/trimestre a un largo con `periodo` AAAAMM (int)."""
    df = df.copy()
    df["anio"] = (df["periodo"] // 100).astype(int)
    df["mes"] = (df["periodo"] % 100).astype(int)
    df["trimestre"] = [_trim_label(a, m) for a, m in zip(df["anio"], df["mes"])]
    return df


def _emit_periodos(rows, key_cols, val_col, grano_metrica, group):
    """Agrega `group` (df con anio/trimestre) por trimestre y por año con el agregador
    dado y agrega filas [grano, departamento, anio, trimestre, rubro, metrica, valor].
    grano_metrica: (rubro, metrica, agg) donde agg ∈ {'mean','sum'}."""
    rubro, metrica, agg = grano_metrica
    # Trimestral
    gq = group.groupby(key_cols + ["anio", "trimestre"], as_index=False)[val_col].agg(agg)
    for r in gq.itertuples(index=False):
        d = getattr(r, "departamento")
        rows.append(["trimestral", d, int(r.anio), getattr(r, "trimestre"),
                     rubro, metrica, round(float(getattr(r, val_col)), 1)])
    # Anual
    ga = group.groupby(key_cols + ["anio"], as_index=False)[val_col].agg(agg)
    for r in ga.itertuples(index=False):
        d = getattr(r, "departamento")
        rows.append(["anual", d, int(r.anio), "",
                     rubro, metrica, round(float(getattr(r, val_col)), 1)])


def empleo():
    ipc = _ipc_noa_map()
    BASE = 202312  # base del índice real: diciembre de 2023

    # ---- Series mensuales anchas (empleo y salario por departamento) --------
    emp_m = _add_tiempo(_wide_long("OEDE_Empleo_Salta_departamento_mensual.csv", "periodo"))
    rem_m = _add_tiempo(_wide_long("OEDE_Remuneraciones_Salta_departamento_mensual.csv", "periodo"))

    # Trimestres COMPLETOS (3 meses) -> el KPI compara trimestres completos.
    tmp = emp_m[["trimestre", "periodo"]].drop_duplicates()
    mcount = tmp.groupby("trimestre")["periodo"].nunique()
    trims_completos = sorted([t for t, n in mcount.items() if n >= 3], key=_trim_key)

    rows = []

    # ---- Empleo por RUBRO (sector) y departamento (media de meses) ----------
    det = pd.read_csv(_src("OEDE_Salta_detalle_apertura_mensual.csv"), encoding="utf-8-sig")
    sec = det[det["apertura"] == "sector"].copy()
    sec["departamento"] = sec["departamento"].map(norm_dept)
    sec["rubro"] = sec["categoria"].astype(str).map(lambda c: _RUBRO_LABEL.get(c, c))
    sec["empleo"] = pd.to_numeric(sec["empleo"], errors="coerce")
    sec = sec.dropna(subset=["empleo"])
    sec["anio"] = sec["anio"].astype(int)
    sec["trimestre"] = [_trim_label(a, m) for a, m in zip(sec["anio"], sec["mes"])]
    # media de los meses del período, por (depto, rubro)
    gq = sec.groupby(["departamento", "rubro", "anio", "trimestre"], as_index=False)["empleo"].mean()
    for r in gq.itertuples(index=False):
        rows.append(["trimestral", r.departamento, int(r.anio), r.trimestre, r.rubro, "empleo", round(float(r.empleo), 1)])
    ga = sec.groupby(["departamento", "rubro", "anio"], as_index=False)["empleo"].mean()
    for r in ga.itertuples(index=False):
        rows.append(["anual", r.departamento, int(r.anio), "", r.rubro, "empleo", round(float(r.empleo), 1)])

    # ---- Empleo TOTAL por departamento (media de meses) + provincial -------
    _emit_periodos(rows, ["departamento"], "valor", ("Total", "empleo", "mean"), emp_m)
    # Provincial = suma de los niveles departamentales (por trimestre y por año).
    emp_q = emp_m.groupby(["departamento", "anio", "trimestre"], as_index=False)["valor"].mean()
    for r in emp_q.groupby(["anio", "trimestre"], as_index=False)["valor"].sum().itertuples(index=False):
        rows.append(["trimestral", "Salta", int(r.anio), r.trimestre, "Total", "empleo", round(float(r.valor), 1)])
    emp_y = emp_m.groupby(["departamento", "anio"], as_index=False)["valor"].mean()
    for r in emp_y.groupby("anio", as_index=False)["valor"].sum().itertuples(index=False):
        rows.append(["anual", "Salta", int(r.anio), "", "Total", "empleo", round(float(r.valor), 1)])

    # ---- Remuneración real (índice base dic-2023=100), media de meses ------
    rem_m["ipc"] = rem_m["periodo"].map(ipc)
    rem_m = rem_m.dropna(subset=["ipc"])
    rem_m["real"] = rem_m["valor"] / rem_m["ipc"]
    base_dep = rem_m[rem_m["periodo"] == BASE].set_index("departamento")["real"].to_dict()
    rem_m["idx"] = [100.0 * real / base_dep[dep] if base_dep.get(dep) else None
                    for real, dep in zip(rem_m["real"], rem_m["departamento"])]
    rem_m = rem_m.dropna(subset=["idx"])
    _emit_periodos(rows, ["departamento"], "idx", ("Total", "remun_real_idx", "mean"), rem_m)

    # Provincial: media ponderada por empleo -> masa salarial / empleo total.
    mm = emp_m.merge(rem_m[["periodo", "departamento", "valor", "ipc"]], on=["periodo", "departamento"],
                     suffixes=("_emp", "_sal"))
    mm["mass"] = mm["valor_emp"] * mm["valor_sal"]
    prov = mm.groupby("periodo", as_index=False).agg(emp=("valor_emp", "sum"), mass=("mass", "sum"), ipc=("ipc", "first"))
    prov["salprov"] = prov["mass"] / prov["emp"]
    prov["real"] = prov["salprov"] / prov["ipc"]
    base_prov = prov.loc[prov["periodo"] == BASE, "real"]
    base_prov = float(base_prov.iloc[0]) if len(base_prov) else None
    if base_prov:
        prov["idx"] = 100.0 * prov["real"] / base_prov
        prov = _add_tiempo(prov).dropna(subset=["idx"])
        for r in prov.groupby(["anio", "trimestre"], as_index=False)["idx"].mean().itertuples(index=False):
            rows.append(["trimestral", "Salta", int(r.anio), r.trimestre, "Total", "remun_real_idx", round(float(r.idx), 1)])
        for r in prov.groupby("anio", as_index=False)["idx"].mean().itertuples(index=False):
            rows.append(["anual", "Salta", int(r.anio), "", "Total", "remun_real_idx", round(float(r.idx), 1)])

    fields = ["grano", "departamento", "anio", "trimestre", "rubro", "metrica", "valor"]
    deptos = [d for d in sorted({r[1] for r in rows}) if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    rubros = sorted({r[4] for r in rows if r[4] != "Total"})
    trimestres = sorted({r[3] for r in rows if r[3]}, key=_trim_key)
    anios = sorted({int(r[2]) for r in rows})
    notas = [
        "empleo: remuneración expresada como ÍNDICE REAL (deflactado por IPC NOA, "
        "serie 145.3_INGNOANOA_DICI_M_10 de datos.gob.ar), base dic-2023 = 100 por serie.",
        "empleo: agregación TRIMESTRAL y ANUAL (media de los meses del período para empleo e "
        "índice real). Se incluyen períodos parciales (p. ej. 2025); el KPI compara el último "
        "trimestre completo contra el mismo trimestre del año anterior.",
        "empleo: la remuneración real provincial es media ponderada por empleo "
        "(Σ empleo·salario / Σ empleo); no se suman promedios entre rubros ni departamentos.",
    ]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": anios,
            "departamento": deptos,
            "rubro": rubros + ["Total"],
            "trimestre": trimestres,
        },
        "metricas": EMPLEO_METRICAS,
        "trims_completos": trims_completos,
        "notas": notas,
    }


# ==========================================================================
# TEMA — Turismo (EOH INDEC), consolidado provincial Salta
# ==========================================================================
TURISMO_METRICAS = {
    "viajeros":         {"label": "Viajeros",       "unidad": "viajeros",         "agg": "sum"},
    "pernoctaciones":   {"label": "Pernoctaciones",  "unidad": "noches",           "agg": "sum"},
    "ocupacion_hab":    {"label": "Ocupación de habitaciones", "unidad": "%",       "agg": "mean"},
    "estadia":          {"label": "Estadía media",   "unidad": "noches",           "agg": "mean"},
    "establecimientos": {"label": "Establecimientos", "unidad": "establecimientos", "agg": "mean"},
}


def turismo():
    df = pd.read_csv(_drv("Salta_turismo_EOH_mensual.csv"), encoding="utf-8-sig")
    df = df[(df["ambito"] == "localidad") & (df["provincia"] == "Salta")].copy()
    num = ["habitaciones_disponibles", "habitaciones_ocupadas", "viajeros", "viajeros_residentes",
           "viajeros_no_residentes", "pernoctaciones", "pernoctaciones_residentes",
           "pernoctaciones_no_residentes", "establecimientos"]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["anio"] = df["anio"].astype(int)
    df["n_mes"] = df["n_mes"].astype(int)
    df["trimestre"] = [_trim_label(a, m) for a, m in zip(df["anio"], df["n_mes"])]
    df["mes_lbl"] = [f"{a}-{m:02d}" for a, m in zip(df["anio"], df["n_mes"])]

    # Consolidar las localidades de Salta por mes (sumar conteos).
    mens = df.groupby(["anio", "n_mes", "mes_lbl", "trimestre"], as_index=False)[num].sum()

    rows = []
    # segmentos de viajeros y pernoctaciones
    SEG_V = [("Total", "viajeros"), ("Residentes", "viajeros_residentes"), ("No residentes", "viajeros_no_residentes")]
    SEG_P = [("Total", "pernoctaciones"), ("Residentes", "pernoctaciones_residentes"), ("No residentes", "pernoctaciones_no_residentes")]

    def push(grano, mes_lbl, trim, anio, sub):
        # sub: dict con columnas ya agregadas para el período (sumas de conteos)
        hd, ho = sub["habitaciones_disponibles"], sub["habitaciones_ocupadas"]
        for seg, col in SEG_V:
            rows.append([grano, anio, mes_lbl, trim, seg, "viajeros", round(sub[col], 1)])
        for seg, col in SEG_P:
            rows.append([grano, anio, mes_lbl, trim, seg, "pernoctaciones", round(sub[col], 1)])
        if hd:
            rows.append([grano, anio, mes_lbl, trim, "Total", "ocupacion_hab", round(100.0 * ho / hd, 1)])
        if sub["viajeros"]:
            rows.append([grano, anio, mes_lbl, trim, "Total", "estadia", round(sub["pernoctaciones"] / sub["viajeros"], 2)])
        rows.append([grano, anio, mes_lbl, trim, "Total", "establecimientos", round(sub["establecimientos"], 1)])

    # Mensual (cada mes) — conteos por mes; establecimientos es stock del mes.
    for r in mens.itertuples(index=False):
        d = r._asdict()
        push("mensual", d["mes_lbl"], d["trimestre"], int(d["anio"]), d)
    # Trimestral y anual: sumar conteos de los meses; establecimientos = promedio del período.
    def agg_group(keys, grano, mes_lbl_fn, trim_fn):
        g = mens.groupby(keys, as_index=False).agg(
            {**{c: "sum" for c in num if c != "establecimientos"}, "establecimientos": "mean", "anio": "first"})
        for r in g.itertuples(index=False):
            d = r._asdict()
            push(grano, mes_lbl_fn(d), trim_fn(d), int(d["anio"]), d)
    agg_group(["anio", "trimestre"], "trimestral", lambda d: "", lambda d: d["trimestre"])
    agg_group(["anio"], "anual", lambda d: "", lambda d: "")

    # No emitir trimestres/años incompletos (la EOH termina a mitad de año => caída ficticia).
    trims_ok, anios_ok, trims_completos = _completos(mens, mes_col="n_mes")
    rows = _keep_completos(rows, trims_ok, anios_ok, gi=0, ai=1, ti=3)

    fields = ["grano", "anio", "mes", "trimestre", "segmento", "metrica", "valor"]
    anios = sorted({r[1] for r in rows})
    trimestres = sorted({r[3] for r in rows if r[3]}, key=_trim_key)
    meses = sorted({r[2] for r in rows if r[2]})
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": anios, "trimestre": trimestres, "mes": meses,
            "segmento": ["Total", "Residentes", "No residentes"],
        },
        "metricas": TURISMO_METRICAS,
        "trims_completos": trims_completos,
        "notas": [
            "turismo: consolidado provincial de Salta (Ciudad de Salta + Cafayate) a partir de la "
            "EOH-INDEC; conteos sumados entre localidades y tasas (ocupación, estadía) recalculadas.",
            "turismo: agregación trimestral/anual por suma de los meses (conteos); la EOH termina "
            "en noviembre de 2025 (serie discontinuada).",
        ],
    }


# ==========================================================================
# TEMA — Agricultura (MAGyP), por cultivo y departamento
# ==========================================================================
AGRI_METRICAS = {
    "superficie_sembrada_ha":  {"label": "Superficie sembrada",  "unidad": "ha",         "agg": "sum"},
    "superficie_cosechada_ha": {"label": "Superficie cosechada", "unidad": "ha",         "agg": "sum"},
    "produccion_tm":           {"label": "Producción",           "unidad": "toneladas",  "agg": "sum"},
    "rendimiento_kgxha":       {"label": "Rendimiento",          "unidad": "kg/ha",      "agg": "mean"},
}


def agricultura():
    wb = openpyxl.load_workbook(_drv("CESS_Agricultura.xlsx"), read_only=True, data_only=True)
    frames = []
    for sh in wb.sheetnames:
        if sh.endswith("1a") or sh.endswith("2a"):   # evita doble conteo con "Soja" total
            continue
        data = list(wb[sh].iter_rows(values_only=True))
        if not data:
            continue
        hdr = list(data[0])
        frames.append(pd.DataFrame(data[1:], columns=hdr))
    wb.close()
    df = pd.concat(frames, ignore_index=True)
    df["departamento"] = df["departamento"].map(norm_dept)
    df["cultivo"] = df["cultivo"].astype(str).str.capitalize()
    for c in ["anio", "superficie_sembrada_ha", "superficie_cosechada_ha", "produccion_tm", "rendimiento_kgxha"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["anio"])
    df["anio"] = df["anio"].astype(int)

    # Descartar la(s) campaña(s) final(es) claramente parciales (aún sin los cultivos de
    # verano): si el total producido de un año es < 50% del anterior, no está completo.
    tot = df.groupby("anio")["produccion_tm"].sum().sort_index()
    years = list(tot.index)
    while len(years) >= 2 and tot[years[-1]] < 0.5 * tot[years[-2]]:
        years.pop()
    df = df[df["anio"].isin(years)]

    rows = []
    metcols = ["superficie_sembrada_ha", "superficie_cosechada_ha", "produccion_tm"]
    # Nivel departamento (valores tal cual; rendimiento de origen).
    for r in df.itertuples(index=False):
        d = r._asdict()
        for m in metcols:
            if pd.notna(d[m]):
                rows.append([int(d["anio"]), d["departamento"], d["cultivo"], m, round(float(d[m]), 1)])
        if pd.notna(d["rendimiento_kgxha"]):
            rows.append([int(d["anio"]), d["departamento"], d["cultivo"], "rendimiento_kgxha", round(float(d["rendimiento_kgxha"]), 1)])
    # Provincial "Salta" por (anio, cultivo): sumar superficies/producción; rendimiento ponderado.
    prov = df.groupby(["anio", "cultivo"], as_index=False)[metcols].sum()
    for r in prov.itertuples(index=False):
        d = r._asdict()
        for m in metcols:
            rows.append([int(d["anio"]), "Salta", d["cultivo"], m, round(float(d[m]), 1)])
        sc = d["superficie_cosechada_ha"]
        if sc:
            rows.append([int(d["anio"]), "Salta", d["cultivo"], "rendimiento_kgxha",
                         round(1000.0 * d["produccion_tm"] / sc, 1)])

    fields = ["anio", "departamento", "cultivo", "metrica", "valor"]
    deptos = [d for d in sorted({r[1] for r in rows}) if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "departamento": deptos,
            "cultivo": sorted({r[2] for r in rows}),
        },
        "metricas": AGRI_METRICAS,
        "notas": [
            "agricultura: campañas 2018/19–2025/26 (MAGyP); el año indica el inicio de campaña.",
            "agricultura: 'Salta' es el total provincial (suma de departamentos); el rendimiento "
            "provincial se calcula como producción/superficie cosechada, no como promedio simple.",
        ],
    }


# ==========================================================================
# TEMA — Gobierno / Finanzas públicas provinciales (ejecución del gasto)
# ==========================================================================
GOB_METRICAS = {
    "gasto_corr": {"label": "Gasto (pesos corrientes)",  "unidad": "pesos", "agg": "sum"},
    "gasto_real": {"label": "Gasto (pesos constantes)",  "unidad": "pesos", "agg": "sum"},
    "pct_aif":    {"label": "Participación (%)",         "unidad": "%",     "agg": "mean"},
}
# Indicadores AIF (DNAP): nombre -> (numerador, denominador) del Esquema Ahorro-Inversión-Financiamiento.
_AIF_IND = {
    "Gasto en personal / gasto primario":              ("Personal", "X. GASTOS PRIMARIOS"),
    "Inversión real directa / gasto primario":         ("Inversión Real Directa", "X. GASTOS PRIMARIOS"),
    "Recursos tributarios propios / ingresos totales": ("De Orígen Provincial", "VI. INGRESOS TOTALES"),
}
_AIF_NOA = ["Salta", "Jujuy", "Tucumán", "Catamarca", "La Rioja", "Santiago del Estero"]
_GOB_PERSONAL = "Gastos en personal"
# Etiquetas legibles por código de objeto (el concepto del PDF viene en mayúsculas y a veces truncado).
_OBJ_LABELS = {
    "1": "Gastos en personal", "2": "Bienes de consumo", "3": "Servicios no personales",
    "4": "Bienes de uso", "5": "Transferencias", "6": "Activos financieros",
    "7": "Servicio de la deuda", "8": "Otros gastos", "9": "Gastos figurativos",
}


def gobierno():
    ipc = _ipc_anual()
    _, base = _ipc_base()   # pesos del último mes publicado del IPC

    def real(v, y):
        return v * base / ipc[y] if ipc.get(y) else None

    rows = []
    YEARS = [2021, 2022, 2023, 2024, 2025]

    # ---- Objeto del gasto (ejecutado = compromisos) ------------------------
    _, obj = _xlsx_rows(_src("Ejecucion_Compromisos_Objeto_Gasto_Salta_2021-2025.xlsx"), header_row=4)
    tot = {y: 0.0 for y in YEARS}
    for r in obj:
        code = str(r.get("Código") or "").strip()
        concepto = r.get("Concepto")
        if not code or code in ("None",) or concepto is None:
            continue
        if len(code) != 1 or not code.isdigit():   # solo los rubros de primer nivel
            continue
        partida = _OBJ_LABELS.get(code, str(concepto).strip().capitalize())
        for y in YEARS:
            v = r.get(str(y))
            if v is None:
                continue
            v = float(v)
            rows.append([y, "objeto", "principal", partida, "gasto_corr", round(v, 1)])
            rows.append([y, "objeto", "principal", partida, "gasto_real", round(real(v, y), 1)])
            tot[y] += v
    for y in YEARS:
        rows.append([y, "objeto", "total", "Total ejecutado", "gasto_corr", round(tot[y], 1)])
        rows.append([y, "objeto", "total", "Total ejecutado", "gasto_real", round(real(tot[y], y), 1)])

    # ---- Finalidad (hoja Serie (total)) ------------------------------------
    _, fin = _xlsx_rows(_src("Ejecucion_Finalidad_Funcion_Salta_2021-2025.xlsx"),
                        sheet="Serie (total)", header_row=4)
    for r in fin:
        code = str(r.get("Código") or "").strip()
        nombre = r.get("Finalidad / Función / Subfunción")
        if not code or "." in code or not code.isdigit() or nombre is None:
            continue  # solo finalidades (código de un dígito, sin punto)
        partida = str(nombre).strip().title()
        for y in YEARS:
            v = r.get(str(y))
            if v is None:
                continue
            v = float(v)
            rows.append([y, "finalidad", "finalidad", partida, "gasto_corr", round(v, 1)])
            rows.append([y, "finalidad", "finalidad", partida, "gasto_real", round(real(v, y), 1)])

    # ---- Transferencias corrientes vs capital (del tidy) -------------------
    tr = pd.read_csv(_src("transferencias_ff_salta_tidy.csv"), encoding="utf-8-sig")
    tr = tr[tr["code"].astype(str) == "0"]
    for r in tr.itertuples(index=False):
        y = int(r.anio)
        if y not in YEARS:
            continue
        for etq, col in [("Corrientes", "corrientes"), ("Capital", "capital")]:
            v = float(getattr(r, col))
            rows.append([y, "transferencia", "tipo", etq, "gasto_corr", round(v, 1)])
            rows.append([y, "transferencia", "tipo", etq, "gasto_real", round(real(v, y), 1)])

    # ---- Indicadores AIF (DNAP): en estas filas `nivel` = ámbito y `partida` = indicador ----
    aif = pd.read_csv(_src("Salta_AIF_DNAP_anual.csv"), encoding="utf-8-sig")
    aif = aif.drop_duplicates(["provincia", "concepto", "anio"])  # el AIF repite nombres (p. ej. transferencias)

    def _serie(provs, prefijo):
        s = aif[aif["provincia"].isin(provs) & aif["concepto"].str.startswith(prefijo)]
        return s.groupby("anio")["millones_pesos"].sum()

    for ambito, provs in [("Salta", ["Salta"]), ("NOA", _AIF_NOA), ("Total provincias", ["Consolidado"])]:
        for ind, (num, den) in _AIF_IND.items():
            r = (100 * _serie(provs, num) / _serie(provs, den)).dropna()
            for y, v in r.items():
                rows.append([int(y), "aif", ambito, ind, "pct_aif", round(float(v), 1)])

    fields = ["anio", "clasificador", "nivel", "partida", "metrica", "valor"]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "clasificador": ["objeto", "finalidad", "transferencia", "aif"],
            "nivel": ["principal", "total", "finalidad", "tipo", "Salta", "NOA", "Total provincias"],
            "partida": sorted({r[3] for r in rows}),
        },
        "metricas": _con_base(GOB_METRICAS, "gasto_real"),
        "notas": [
            "gobierno: ejecución del gasto provincial (consolidado Adm. Central + Organismos "
            "Descentralizados), acumulada a diciembre; fuente presupuesto.salta.gob.ar.",
            "gobierno: 'objeto' usa los compromisos ejecutados; el gasto es un flujo ANUAL, así que "
            "se deflacta por el IPC NOA promedio del año y se expresa en pesos de %s (la base es el "
            "último mes publicado del IPC y se mueve con él)." % _base_txt(True),
            "gobierno: gasto en personal e inversión real directa sobre gasto primario, y recursos "
            "tributarios de origen provincial sobre ingresos totales, del Esquema AIF de la DNAP "
            "(APNF, 2015–2025; 2024–2025 provisorios). NOA = suma de las seis provincias.",
        ],
    }


# ==========================================================================
# TEMA — Ganadería bovina (MAGyP), stock por departamento y categoría
# ==========================================================================
GAN_METRICAS = {
    "stock_bovino":  {"label": "Stock bovino",         "unidad": "cabezas", "agg": "sum"},
    "unidades_prod": {"label": "Unidades productivas", "unidad": "UP",      "agg": "sum"},
}
_GAN_CAT = {
    "total_bovinos": "Total", "vacas": "Vacas", "vaquillonas": "Vaquillonas",
    "novillos": "Novillos", "novillitos": "Novillitos", "terneros": "Terneros",
    "terneras": "Terneras", "toros": "Toros", "toritos": "Toritos", "bueyes": "Bueyes",
}


def ganaderia():
    df = pd.read_csv(_src("Ganaderia_Stock_Bovino_Salta_departamento_2012-2025.csv"), encoding="utf-8-sig")
    df["departamento"] = df["departamento"].map(norm_dept)
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["anio", "valor"])
    df["anio"] = df["anio"].astype(int)

    rows = []
    for r in df.itertuples(index=False):
        cat = _GAN_CAT.get(r.metrica)
        if cat is not None:
            rows.append([int(r.anio), r.departamento, cat, "stock_bovino", round(float(r.valor), 1)])
        elif r.metrica == "cantidad_up":
            rows.append([int(r.anio), r.departamento, "Total", "unidades_prod", round(float(r.valor), 1)])
    # Provincial "Salta" = suma de departamentos por (anio, categoria, metrica).
    prov = {}
    for a, dep, cat, met, val in rows:
        prov[(a, cat, met)] = prov.get((a, cat, met), 0.0) + val
    prov_rows = [[a, "Salta", cat, met, round(v, 1)] for (a, cat, met), v in prov.items()]

    allrows = rows + prov_rows
    fields = ["anio", "departamento", "categoria", "metrica", "valor"]
    deptos = [d for d in sorted({r[1] for r in allrows}) if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    return {
        "fields": fields,
        "rows": allrows,
        "dims": {
            "anio": sorted({r[0] for r in allrows}),
            "departamento": deptos,
            "categoria": ["Total", "Vacas", "Vaquillonas", "Novillos", "Novillitos",
                          "Terneros", "Terneras", "Toros", "Toritos", "Bueyes"],
        },
        "metricas": GAN_METRICAS,
        "notas": [
            "ganaderia: existencias bovinas al 31/12 de cada año (MAGyP), 2012–2025; "
            "'Salta' es el total provincial (suma de departamentos)."],
    }


# ==========================================================================
# TEMA — Minería: empleo minero (Salta) + recaudación tributaria (nacional)
# ==========================================================================
MINERIA_METRICAS = {
    "empleo_min":  {"label": "Empleo minero",              "unidad": "puestos",       "agg": "sum"},
    "recaud_ars":  {"label": "Recaudación (millones $)",   "unidad": "millones de $", "agg": "sum"},
    "recaud_usd":  {"label": "Recaudación (millones US$)", "unidad": "millones US$",  "agg": "sum"},
}
_MIN_IMP = {2: "Ganancias (sociedades)", 3: "Derechos de exportación", 4: "Seguridad social",
            5: "Créditos y débitos", 6: "Regalías y canon", 7: "Tasa ambiental"}


def _sq(v):
    """Quita comillas envolventes de los strings del bloque Empleo del xlsx."""
    return str(v).strip().strip('"').strip() if v is not None else v


def mineria():
    wb = openpyxl.load_workbook(_drv("CESS_Mineria.xlsx"), read_only=True, data_only=True)
    rows = []

    # ---- Empleo minero mensual (Salta) por rubro y género -------------------
    emp = list(wb["Empleo"].iter_rows(values_only=True))
    recs = []
    for r in emp[1:]:
        if not r or r[0] is None:
            continue
        fecha = r[0]
        anio, mes = fecha.year, fecha.month
        genero, rubro, cant = _sq(r[2]), _sq(r[3]), r[4]
        if cant is None:
            continue
        recs.append((anio, mes, _trim_label(anio, mes), genero, rubro, float(cant)))
    emp_df = pd.DataFrame(recs, columns=["anio", "mes", "trimestre", "genero", "rubro", "cant"])

    frames = []
    base = emp_df.groupby(["anio", "mes", "trimestre", "genero", "rubro"], as_index=False)["cant"].sum()
    frames.append(base.rename(columns={"genero": "g", "rubro": "r", "cant": "v"}))
    gt = emp_df.groupby(["anio", "mes", "trimestre", "rubro"], as_index=False)["cant"].sum()
    gt["g"] = "Total"; frames.append(gt.rename(columns={"rubro": "r", "cant": "v"}))
    rt = emp_df.groupby(["anio", "mes", "trimestre", "genero"], as_index=False)["cant"].sum()
    rt["r"] = "Total"; frames.append(rt.rename(columns={"genero": "g", "cant": "v"}))
    bt = emp_df.groupby(["anio", "mes", "trimestre"], as_index=False)["cant"].sum()
    bt["g"] = "Total"; bt["r"] = "Total"; frames.append(bt.rename(columns={"cant": "v"}))
    base = pd.concat(frames, ignore_index=True)

    def emit_emp(grano, keys, has_trim):
        g = base.groupby(keys, as_index=False)["v"].mean()
        for r in g.itertuples(index=False):
            d = r._asdict()
            rows.append([grano, int(d["anio"]), d["trimestre"] if has_trim else "",
                         d["g"], d["r"], "", "", "empleo_min", round(float(d["v"]), 1)])
    emit_emp("trimestral", ["g", "r", "anio", "trimestre"], True)
    emit_emp("anual", ["g", "r", "anio"], False)

    mc = emp_df.groupby("trimestre")["mes"].nunique()
    trims_completos = sorted([t for t, n in mc.items() if n >= 3], key=_trim_key)

    # ---- Recaudación tributaria anual por empresa e impuesto (nacional) -----
    imp = list(wb["Impuestos pagados 19-23"].iter_rows(values_only=True))
    for r in imp[1:]:
        if not r or r[0] is None:
            continue
        try:
            anio = int(r[0])
        except (TypeError, ValueError):
            continue
        empresa = str(r[1]).strip()
        for ci, label in _MIN_IMP.items():
            ars = r[ci]
            usd = r[ci + 12]   # bloque USD desplazado 12 columnas
            if ars is not None:
                rows.append(["anual", anio, "", "", "", empresa, label, "recaud_ars", round(float(ars), 3)])
            if usd is not None:
                rows.append(["anual", anio, "", "", "", empresa, label, "recaud_usd", round(float(usd), 3)])
    wb.close()

    fields = ["grano", "anio", "trimestre", "genero", "rubro", "empresa", "impuesto", "metrica", "valor"]
    anios = sorted({int(r[1]) for r in rows})
    trimestres = sorted({r[2] for r in rows if r[2]}, key=_trim_key)
    rubros = sorted({r[4] for r in rows if r[4] and r[4] != "Total"})
    empresas = sorted({r[5] for r in rows if r[5]})
    impuestos = [v for v in _MIN_IMP.values()]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": anios, "trimestre": trimestres,
            "genero": ["Total", "Femenino", "Masculino"],
            "rubro": rubros + ["Total"],
            "empresa": empresas, "impuesto": impuestos,
        },
        "metricas": MINERIA_METRICAS,
        "trims_completos": trims_completos,
        "notas": [
            "mineria: el empleo minero es de Salta (registro mensual desde 2007, media de meses por "
            "trimestre/año). La recaudación tributaria es NACIONAL del sector (por empresa, 2019–2023), "
            "no atribuible a Salta; el total en USD se recalcula como suma de impuestos.",
        ],
    }


# ==========================================================================
# TEMA — Financiero: préstamos y depósitos (BCRA) + inclusión financiera
# ==========================================================================
FIN_METRICAS = {
    "monto_corr": {"label": "Monto (pesos corrientes)", "unidad": "pesos", "agg": "sum"},
    "monto_real": {"label": "Monto (pesos constantes)", "unidad": "pesos", "agg": "sum"},
    "pda_10m":    {"label": "Puntos de acceso (cada 10.000 adultos)", "unidad": "PDA/10k", "agg": "mean"},
}


def financiero():
    ipcm = _ipc_noa_map()
    _, base = _ipc_base()

    def real_trim(v, anio, trim):
        """Préstamos y depósitos son un STOCK medido a fin de trimestre, así que les corresponde el
        nivel de precios de ESE momento (T1 -> marzo, T2 -> junio...) y no el promedio del año: con
        inflación de tres dígitos el promedio anual sobrestima el T1 y subestima el T4 (en 2024,
        +18,7 % y -17,5 %)."""
        ipc = ipcm.get(int(anio) * 100 + int(trim) * 3)
        return v * base / ipc if ipc and pd.notna(ipc) else float("nan")

    dp = pd.read_csv(_drv("BCRA_dep_pres_localidad_Salta.csv"), encoding="utf-8-sig")
    dp = dp[dp["moneda"] == "total"].copy()
    for c in ["anio", "trimestre", "prestamos_sector_privado", "depositos_sector_privado"]:
        dp[c] = pd.to_numeric(dp[c], errors="coerce")
    dp = dp.dropna(subset=["anio", "trimestre"])
    dp["anio"] = dp["anio"].astype(int)
    dp["trim_lbl"] = [f"{a}-T{int(t)}" for a, t in zip(dp["anio"], dp["trimestre"])]

    def geo(row):
        return "Salta" if row["nivel"] == "provincia" else norm_dept(row["departamento"])

    rows = []
    OPS = [("Préstamos", "prestamos_sector_privado"), ("Depósitos", "depositos_sector_privado")]
    sub = dp[dp["nivel"].isin(["departamento", "provincia"])].copy()
    sub["geo"] = sub.apply(geo, axis=1)
    def _media_completa(x):
        # Si a algún trimestre le falta el IPC, el año no tiene promedio real: promediar los que
        # están daría un "anual" que en realidad son tres trimestres.
        return x.mean() if x.notna().all() else float("nan")

    for op, col in OPS:
        g = sub.groupby(["geo", "anio", "trimestre", "trim_lbl"], as_index=False)[col].sum()
        g["corr"] = g[col] * 1000.0                                  # miles de $ -> $
        g["real"] = [real_trim(v, a, t) for v, a, t in zip(g["corr"], g["anio"], g["trimestre"])]
        for r in g.itertuples(index=False):
            rows.append(["trimestral", int(r.anio), r.trim_lbl, r.geo, op, "monto_corr",
                         round(float(r.corr), 1)])
            if pd.notna(r.real):
                rows.append(["trimestral", int(r.anio), r.trim_lbl, r.geo, op, "monto_real",
                             round(float(r.real), 1)])
        # Anual = promedio de los trimestres del año. Los reales se promedian YA DEFLACTADOS: como
        # cada trimestre lleva su propio deflactor, no hay un índice único que sirva para el año.
        ga = g.groupby(["geo", "anio"], as_index=False).agg(corr=("corr", "mean"),
                                                            real=("real", _media_completa))
        for r in ga.itertuples(index=False):
            rows.append(["anual", int(r.anio), "", r.geo, op, "monto_corr", round(float(r.corr), 1)])
            if pd.notna(r.real):
                rows.append(["anual", int(r.anio), "", r.geo, op, "monto_real", round(float(r.real), 1)])

    # ---- Inclusión financiera: PDA por 10.000 adultos, por departamento -----
    inc = pd.read_csv(_drv("BCRA_IF_Salta_puntos_acceso_10000_adultos.csv"), encoding="utf-8-sig")
    inc["nu_pda_10m"] = pd.to_numeric(inc["nu_pda_10m"], errors="coerce")
    inc["anio"] = pd.to_numeric(inc["anio"], errors="coerce")
    inc = inc.dropna(subset=["nu_pda_10m", "anio"])
    inc["anio"] = inc["anio"].astype(int)
    inc["departamento"] = inc["tx_departamento"].map(norm_dept)
    # total de puntos = suma de tipos de PDA por (anio, mes, depto); anual = media de meses
    mensual = inc.groupby(["anio", "mes", "departamento"], as_index=False)["nu_pda_10m"].sum()
    anual = mensual.groupby(["anio", "departamento"], as_index=False)["nu_pda_10m"].mean()
    for r in anual.itertuples(index=False):
        rows.append(["anual", int(r.anio), "", r.departamento, "PDA", "pda_10m", round(float(r.nu_pda_10m), 2)])
    prov_inc = mensual.groupby(["anio", "mes"], as_index=False)["nu_pda_10m"].sum() \
                      .groupby("anio", as_index=False)["nu_pda_10m"].mean()
    for r in prov_inc.itertuples(index=False):
        rows.append(["anual", int(r.anio), "", "Salta", "PDA", "pda_10m", round(float(r.nu_pda_10m), 2)])

    fields = ["grano", "anio", "trimestre", "departamento", "operacion", "metrica", "valor"]
    deptos = [d for d in sorted({r[3] for r in rows}) if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    trimestres = sorted({r[2] for r in rows if r[2]}, key=_trim_key)
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "trimestre": trimestres,
            "departamento": deptos,
            "operacion": ["Préstamos", "Depósitos", "PDA"],
        },
        "metricas": _con_base(FIN_METRICAS, "monto_real"),
        "trims_completos": trimestres,
        "notas": [
            "financiero: préstamos y depósitos al sector privado (BCRA, stock a fin de trimestre, "
            "miles de $); 'Salta' es el total provincial. Los reales se deflactan por el IPC NOA del "
            "ÚLTIMO MES DEL TRIMESTRE, porque el dato es un stock a esa fecha, y quedan en pesos de "
            "%s; la base es el último mes publicado del IPC y se mueve con él. El dato anual "
            "promedia los trimestres ya deflactados." % _base_txt(True),
            "financiero: inclusión financiera = puntos de acceso cada 10.000 adultos (promedio anual, "
            "suma de tipos); cobertura desde 2019.",
        ],
    }


# ==========================================================================
# TEMA — Permisos de construcción (INDEC), por municipio
# ==========================================================================
CONSTR_METRICAS = {
    "permisos":     {"label": "Permisos otorgados",   "unidad": "permisos", "agg": "sum"},
    "superficie_m2": {"label": "Superficie autorizada", "unidad": "m²",      "agg": "sum"},
    "share_sup_pct": {"label": "Participación en el país", "unidad": "%",     "agg": "mean"},
}


def _q_from_month_col(anio, mes_str):
    # mes_str tipo 'YYYY-MM-01'; devuelve (mes_lbl, trimestre)
    m = int(str(mes_str)[5:7])
    return f"{anio}-{m:02d}", _trim_label(anio, m)


def construccion():
    muni = pd.read_csv(_drv("Salta_permisos_construccion_INDEC_municipio_mensual.csv"), encoding="utf-8-sig")
    tot = pd.read_csv(_drv("Salta_permisos_construccion_INDEC_totales_mensual.csv"), encoding="utf-8-sig")
    for c in ["anio", "permisos_otorgados", "superficie_autorizada_m2"]:
        muni[c] = pd.to_numeric(muni[c], errors="coerce")
    muni = muni.dropna(subset=["anio"])
    muni["anio"] = muni["anio"].astype(int)
    # "Salta" (municipio) es la Ciudad de Salta: se renombra para no chocar con el token provincial.
    muni["municipio"] = muni["municipio"].map(lambda x: "Salta (ciudad)" if str(x).strip() == "Salta" else str(x).strip())
    muni["mes_lbl"] = [f"{a}-{int(str(m)[5:7]):02d}" for a, m in zip(muni["anio"], muni["mes"])]
    muni["trimestre"] = [_trim_label(a, int(str(m)[5:7])) for a, m in zip(muni["anio"], muni["mes"])]

    rows = []

    def emit_flows(df, geocol, geolabel_fn):
        MET = [("permisos", "permisos_otorgados"), ("superficie_m2", "superficie_autorizada_m2")]
        for met, col in MET:
            # mensual
            for r in df.itertuples(index=False):
                d = r._asdict()
                if pd.notna(d[col]):
                    rows.append(["mensual", int(d["anio"]), d["mes_lbl"], d["trimestre"],
                                 geolabel_fn(d), met, round(float(d[col]), 1)])
            # trimestral (suma) y anual (suma)
            gq = df.groupby([geocol, "anio", "trimestre"], as_index=False)[col].sum()
            for r in gq.itertuples(index=False):
                d = r._asdict()
                rows.append(["trimestral", int(d["anio"]), "", d["trimestre"], d[geocol], met, round(float(d[col]), 1)])
            ga = df.groupby([geocol, "anio"], as_index=False)[col].sum()
            for r in ga.itertuples(index=False):
                d = r._asdict()
                rows.append(["anual", int(d["anio"]), "", "", d[geocol], met, round(float(d[col]), 1)])

    emit_flows(muni, "municipio", lambda d: d["municipio"])

    # Provincial "Total Salta" = suma de municipios (por período). Se usa "Total Salta" porque
    # "Salta" ya es un municipio real (Ciudad de Salta).
    prov = muni.copy()
    prov["municipio"] = "Total Salta"
    emit_flows(prov, "municipio", lambda d: "Total Salta")

    # Participación nacional (del archivo de totales), provincial.
    tot["anio"] = pd.to_numeric(tot["anio"], errors="coerce").astype("Int64")
    tot["share_superficie_pct"] = pd.to_numeric(tot["share_superficie_pct"], errors="coerce")
    tot = tot.dropna(subset=["anio"])
    tot["mes_lbl"] = [f"{int(a)}-{int(str(m)[5:7]):02d}" for a, m in zip(tot["anio"], tot["mes"])]
    tot["trimestre"] = [_trim_label(int(a), int(str(m)[5:7])) for a, m in zip(tot["anio"], tot["mes"])]
    for r in tot.itertuples(index=False):
        d = r._asdict()
        if pd.notna(d["share_superficie_pct"]):
            rows.append(["mensual", int(d["anio"]), d["mes_lbl"], d["trimestre"], "Total Salta", "share_sup_pct", round(float(d["share_superficie_pct"]), 2)])
    tq = tot.groupby(["anio", "trimestre"], as_index=False)["share_superficie_pct"].mean()
    for r in tq.itertuples(index=False):
        rows.append(["trimestral", int(r.anio), "", r.trimestre, "Total Salta", "share_sup_pct", round(float(r.share_superficie_pct), 2)])
    ty = tot.groupby("anio", as_index=False)["share_superficie_pct"].mean()
    for r in ty.itertuples(index=False):
        rows.append(["anual", int(r.anio), "", "", "Total Salta", "share_sup_pct", round(float(r.share_superficie_pct), 2)])

    # No emitir trimestres/años incompletos (último período parcial => caída ficticia).
    trims_ok, anios_ok, trims_completos = _completos(muni, mes_col="mes_lbl")
    rows = _keep_completos(rows, trims_ok, anios_ok, gi=0, ai=1, ti=3)

    fields = ["grano", "anio", "mes", "trimestre", "municipio", "metrica", "valor"]
    munis = [m for m in sorted({r[4] for r in rows}) if m not in NON_GEO and m not in PROVINCIAL_TOKENS]
    trimestres = sorted({r[3] for r in rows if r[3]}, key=_trim_key)
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "mes": sorted({r[2] for r in rows if r[2]}),
            "trimestre": trimestres,
            "municipio": munis,
        },
        "metricas": CONSTR_METRICAS,
        "trims_completos": trims_completos,
        "notas": [
            "construccion: permisos de edificación privada informados a INDEC por 5 municipios de "
            "Salta (mensual); los flujos se SUMAN por trimestre/año. La superficie es intención de "
            "construir, no obra ejecutada; 'Salta' suma los municipios."],
    }


# ==========================================================================
# TEMA — Recursos a municipios (Contaduría Gral. de Salta)
# ==========================================================================
RECURSOS_METRICAS = {
    "monto_corr": {"label": "Monto (pesos corrientes)", "unidad": "pesos", "agg": "sum"},
    "monto_real": {"label": "Monto (pesos constantes)", "unidad": "pesos", "agg": "sum"},
}


def recursos_municipios():
    ipcm = _ipc_noa_map()
    _, base = _ipc_base()

    df = pd.read_csv(_drv("Salta_recursos_municipios_mensual.csv"), encoding="utf-8-sig")
    df["departamento"] = df["departamento"].map(norm_dept)
    # El municipio "Salta" es la Ciudad de Salta: se renombra para no chocar con el token provincial.
    df["municipio"] = df["municipio"].map(lambda x: "Salta (ciudad)" if str(x).strip() == "Salta" else str(x).strip())
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    df = df.dropna(subset=["anio", "mes", "monto"])
    df["anio"] = df["anio"].astype(int)
    df["trimestre"] = [_trim_label(a, m) for a, m in zip(df["anio"], df["mes"])]

    # Los recursos son un flujo MENSUAL: cada mes se deflacta con SU propio IPC y recién después se
    # suma a trimestre y año. Deflactar la suma con el promedio anual metía un serrucho dentro de
    # cada año (con la inflación de 2023, el T1 quedaba un 53 % por encima de su valor real).
    df["P"] = [ipcm.get(a * 100 + int(m)) for a, m in zip(df["anio"], df["mes"])]
    # Un mes sin IPC todavía se descarta ENTERO, no sólo de la serie real: si sólo se cayera de los
    # reales, el trimestre publicaría tres meses en corrientes y dos en constantes bajo la misma
    # etiqueta. Descartado el mes, `_completos` se encarga de bajar el trimestre incompleto.
    sin_ipc = sorted({"%d-%02d" % (a, m) for a, m, P in zip(df["anio"], df["mes"], df["P"])
                      if P is None or pd.isna(P)})
    df = df[df["P"].notna()].copy()
    df["real"] = df["monto"] * base / df["P"]

    rows = []

    def emit(keycols, group):
        # trimestral y anual (suma de meses); corrientes + reales
        for grano, extra, trim in (("trimestral", ["anio", "trimestre"], True),
                                   ("anual", ["anio"], False)):
            g = group.groupby(keycols + extra, as_index=False).agg(
                corr=("monto", "sum"), real=("real", "sum"))
            for r in g.itertuples(index=False):
                d = r._asdict(); y = int(d["anio"])
                t = d["trimestre"] if trim else ""
                for met, v in (("monto_corr", d["corr"]), ("monto_real", d["real"])):
                    rows.append([grano, y, t, d["departamento"], d["municipio"], d["grupo"],
                                 met, round(float(v), 1)])

    emit(["departamento", "municipio", "grupo"], df)

    # No emitir períodos incompletos (último trimestre/año parcial => caída ficticia).
    trims_ok, anios_ok, trims_ok_list = _completos(df, mes_col="mes")
    rows = _keep_completos(rows, trims_ok, anios_ok)

    fields = ["grano", "anio", "trimestre", "departamento", "municipio", "grupo", "metrica", "valor"]
    deptos = [d for d in sorted({r[3] for r in rows}) if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    munis = [m for m in sorted({r[4] for r in rows}) if m and m not in PROVINCIAL_TOKENS]
    trimestres = sorted({r[2] for r in rows if r[2]}, key=_trim_key)
    grupos = sorted({r[5] for r in rows if r[5]})
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "trimestre": trimestres,
            "departamento": deptos,
            "municipio": munis,
            "grupo": grupos,
        },
        "metricas": _con_base(RECURSOS_METRICAS, "monto_real"),
        "trims_completos": trims_ok_list,
        "notas": [
            "recursos-municipios: transferencias a municipios de Salta (Contaduría Gral.), mensual "
            "desde 2021, sumadas por trimestre/año. Cada MES se deflacta con el IPC NOA de ese mes "
            "antes de sumar, y el resultado queda en pesos de %s; la base es el último mes "
            "publicado del IPC y se mueve con él. " % _base_txt(True) +
            "Grupos: Coparticipación, Regalías, Canon, Fondo compensador, Otros."],
    }


# ==========================================================================
# TEMA — Energía eléctrica renovable (CAMMESA): generación por fuente y potencia
# ==========================================================================
ENERGIA_METRICAS = {
    "generacion_gwh":      {"label": "Generación",           "unidad": "GWh", "agg": "sum"},
    "gen_central_gwh":     {"label": "Generación por central", "unidad": "GWh", "agg": "sum"},
    "share_renovable_pct": {"label": "Participación renovable", "unidad": "%",  "agg": "mean"},
    "potencia_mw":         {"label": "Potencia instalada",    "unidad": "MW",  "agg": "sum"},
}
_ENE_FUENTE = {"hidraulica": "Hidráulica", "renovable": "Renovable", "termica": "Térmica"}


def energia_renovable():
    rows = []

    # ---- Generación por fuente (archivo ancho, MWh -> GWh) ------------------
    fu = pd.read_csv(_drv("Salta_generacion_CAMMESA_fuente_mensual.csv"), encoding="utf-8-sig")
    fu["anio"] = pd.to_numeric(fu["anio"], errors="coerce").astype("Int64")
    fu = fu.dropna(subset=["anio"])
    fu["anio"] = fu["anio"].astype(int)
    fu["m"] = fu["mes"].astype(str).str.slice(5, 7).astype(int)
    fu["trimestre"] = [_trim_label(a, m) for a, m in zip(fu["anio"], fu["m"])]
    long = fu.melt(id_vars=["anio", "trimestre"], value_vars=list(_ENE_FUENTE.keys()),
                   var_name="fu", value_name="v")
    long["v"] = pd.to_numeric(long["v"], errors="coerce") / 1000.0   # MWh -> GWh
    long["fuente"] = long["fu"].map(_ENE_FUENTE)
    long = long.dropna(subset=["v"])
    gq = long.groupby(["fuente", "anio", "trimestre"], as_index=False)["v"].sum()
    for r in gq.itertuples(index=False):
        rows.append(["trimestral", int(r.anio), r.trimestre, r.fuente, "", "generacion_gwh", round(float(r.v), 1)])
    ga = long.groupby(["fuente", "anio"], as_index=False)["v"].sum()
    for r in ga.itertuples(index=False):
        rows.append(["anual", int(r.anio), "", r.fuente, "", "generacion_gwh", round(float(r.v), 1)])

    # ---- % renovable (media del período) -----------------------------------
    fu["share_renovable_pct"] = pd.to_numeric(fu["share_renovable_pct"], errors="coerce")
    sq = fu.groupby(["anio", "trimestre"], as_index=False)["share_renovable_pct"].mean()
    for r in sq.itertuples(index=False):
        rows.append(["trimestral", int(r.anio), r.trimestre, "", "", "share_renovable_pct", round(float(r.share_renovable_pct), 1)])
    sa = fu.groupby("anio", as_index=False)["share_renovable_pct"].mean()
    for r in sa.itertuples(index=False):
        rows.append(["anual", int(r.anio), "", "", "", "share_renovable_pct", round(float(r.share_renovable_pct), 1)])

    # Completitud a partir de la cobertura mensual por fuente.
    _trims_ok, _anios_ok, trims_completos = _completos(fu, mes_col="m")

    # ---- Generación por central (MWh -> GWh), anual ------------------------
    ce = pd.read_csv(_drv("Salta_generacion_CAMMESA_central_mensual.csv"), encoding="utf-8-sig")
    ce["anio"] = pd.to_numeric(ce["anio"], errors="coerce").astype("Int64")
    ce = ce.dropna(subset=["anio"])
    ce["anio"] = ce["anio"].astype(int)
    ce["gwh"] = pd.to_numeric(ce["generacion_neta_mwh"], errors="coerce") / 1000.0
    ce["central"] = ce["agente_descripcion"].astype(str).str.strip()
    gc = ce.groupby(["central", "anio"], as_index=False)["gwh"].sum()
    for r in gc.itertuples(index=False):
        rows.append(["anual", int(r.anio), "", "", r.central, "gen_central_gwh", round(float(r.gwh), 1)])

    # ---- Potencia instalada por central (snapshot, MW) ---------------------
    po = pd.read_csv(_drv("Salta_generacion_CAMMESA_potencia_instalada.csv"), encoding="utf-8-sig")
    po["mw"] = pd.to_numeric(po["potencia_instalada_mw"], errors="coerce")
    po["central"] = po["agente_descripcion"].astype(str).str.strip()
    po["anio"] = pd.to_numeric(po["anio"], errors="coerce").astype("Int64")
    po = po.dropna(subset=["mw"])
    pot_anio = int(po["anio"].max())
    pg = po.groupby("central", as_index=False)["mw"].sum()
    for r in pg.itertuples(index=False):
        rows.append(["anual", pot_anio, "", "", r.central, "potencia_mw", round(float(r.mw), 1)])

    # No emitir períodos incompletos: trimestres parciales (todas las series) y años parciales
    # SOLO para los flujos de generación (la potencia es una foto del último año y se conserva).
    _GEN_ANUAL = {"generacion_gwh", "gen_central_gwh"}
    rows = [r for r in rows
            if not (r[0] == "trimestral" and r[2] not in _trims_ok)
            and not (r[0] == "anual" and r[5] in _GEN_ANUAL and int(r[1]) not in _anios_ok)]

    fields = ["grano", "anio", "trimestre", "fuente", "central", "metrica", "valor"]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "trimestre": trims_completos,
            "fuente": ["Hidráulica", "Renovable", "Térmica"],
            "central": sorted({r[4] for r in rows if r[4]}),
        },
        "metricas": ENERGIA_METRICAS,
        "trims_completos": trims_completos,
        "notas": [
            "energia-renovable: generación eléctrica de Salta (CAMMESA), MWh convertidos a GWh; "
            "los flujos se suman por trimestre/año. 'Renovable' = régimen Ley 27.191; la potencia "
            "instalada es una foto al último mes disponible."],
    }


# ==========================================================================
# TEMA — Inversión en I+D e innovación (RICyT/MINCyT), provincial Salta
#   Dataset chico y estático (Sheet sin script ETL); se embebe verificado.
# ==========================================================================
ID_METRICAS = {
    "inv_id_corr": {"label": "Inversión en I+D (pesos corrientes)", "unidad": "millones de $", "agg": "sum"},
    "inv_id_real": {"label": "Inversión en I+D (pesos de 2017)",   "unidad": "millones de $", "agg": "sum"},
    "personal_id": {"label": "Personal en I+D",                     "unidad": "personas",      "agg": "sum"},
}
# Inversión I+D de Salta: anio -> (millones $ corrientes, millones $ constantes 2017)
_ID_INV = {2017: (678, 678), 2018: (859, 640), 2019: (1083, 528), 2020: (1199, 416),
           2021: (1909, 451), 2022: (3400, 464), 2023: (8196, 478), 2024: (22608, 408)}
# Personal en I+D por función (headcount): anio -> (investigadores/as y becarios/as, técnicos y apoyo)
_ID_PERS = {
    2003: (462, None), 2004: (489, None), 2005: (508, None), 2006: (679, None),
    2007: (708, None), 2008: (730, None), 2009: (710, 296), 2010: (648, 282),
    2011: (691, 278), 2012: (674, 324), 2013: (672, 344), 2014: (762, 349),
    2015: (914, 322), 2016: (865, 333), 2017: (868, 323), 2018: (920, 293),
    2019: (923, 279), 2020: (887, 298), 2021: (911, 315), 2022: (919, 342),
    2023: (934, 373), 2024: (925, 382),
}


def id_innovacion():
    rows = []
    for a, (corr, real) in _ID_INV.items():
        rows.append([a, "", "inv_id_corr", float(corr)])
        rows.append([a, "", "inv_id_real", float(real)])
    for a, (inv, tec) in _ID_PERS.items():
        if inv is not None:
            rows.append([a, "Investigadores y becarios", "personal_id", float(inv)])
        if tec is not None:
            rows.append([a, "Personal técnico y de apoyo", "personal_id", float(tec)])

    fields = ["anio", "funcion", "metrica", "valor"]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "funcion": ["Investigadores y becarios", "Personal técnico y de apoyo"],
        },
        "metricas": ID_METRICAS,
        "notas": [
            "id-innovacion: inversión provincial en I+D (millones de $ corrientes y en pesos "
            "constantes de 2017) y personal en I+D por función; fuente RICyT/MINCyT. En términos "
            "reales la inversión se mantuvo casi estancada (678 en 2017 → 408 en 2024)."],
    }


# ==========================================================================
# TEMA — Resultado fiscal provincial (Esquema Ahorro-Inversión-Financiamiento)
# ==========================================================================
RESFISC_METRICAS = {
    "monto_corr": {"label": "Monto (pesos corrientes)", "unidad": "pesos", "agg": "sum"},
    "monto_real": {"label": "Monto (pesos constantes)", "unidad": "pesos", "agg": "sum"},
    # Cociente contra el gasto primario. Es un RATIO: no depende de la deflación (verificado
    # período por período, corrientes y constantes dan el mismo valor), así que no se duplica
    # en corr/real. agg "mean" es defensivo: sumar los porcentajes de dos conceptos no
    # significaría nada, y los gráficos siempre fijan o abren el concepto en series.
    "pct_gprim": {"label": "En % del gasto primario", "unidad": "% del gasto primario",
                  "agg": "mean"},
}
# (etiqueta legible, prefijo de columna en el CSV). XI == VIII en Salta: se usa XI como
# "Resultado financiero". El primario es cálculo propio (XI + intereses de deuda).
_RESFISC_CONCEPTOS = [
    ("Ingresos totales",      "ingresos_totales"),
    ("Gastos totales",        "gastos_totales"),
    ("Resultado financiero",  "res_financiero_xi"),
    ("Resultado primario",    "res_primario"),
    ("Intereses de la deuda", "intereses_deuda"),
]
# Gasto primario = gastos totales − intereses de la deuda. La identidad se verificó contra la
# propia fuente: ingresos − gasto primario == resultado primario, exacto en todos los períodos.
_RESFISC_GPRIM = "Gasto primario"
# Conceptos que se expresan como % del gasto primario.
_RESFISC_PCT = ["Resultado financiero", "Resultado primario"]


def resultado_fiscal():
    ipcm = _ipc_noa_map()
    _, base = _ipc_base()
    # thousands="," tolera exportaciones con separador de miles entrecomillado
    # ("12,021,478,627"); en el CSV limpio (decimal con punto) es inocuo.
    df = pd.read_csv(_drv("Resultado_Fiscal_Salta_AIF_mensual_desde_2021.csv"),
                     encoding="utf-8-sig", thousands=",")
    for c in df.columns:
        if c not in ("provincia", "periodo", "fecha_corte"):
            df[c] = pd.to_numeric(df[c], errors="coerce")

    rows = []
    for _, r in df.iterrows():
        if pd.isna(r["anio"]) or pd.isna(r["mes"]):
            continue
        y, m = int(r["anio"]), int(r["mes"])
        periodo = f"{y}-{m:02d}"
        ipc = ipcm.get(y * 100 + m)
        for vista, suf in (("acumulado", "acum"), ("mensual", "mensual")):
            vals = {}
            for concepto, pref in _RESFISC_CONCEPTOS:
                v = r.get(f"{pref}_{suf}")
                if v is None or pd.isna(v):
                    continue
                v = float(v)
                vals[concepto] = v
                rows.append([vista, y, m, periodo, concepto, "monto_corr", round(v, 1)])
                if ipc:
                    rows.append([vista, y, m, periodo, concepto, "monto_real", round(v * base / ipc, 1)])

            # Gasto primario y los resultados expresados en % de ese gasto.
            gt, it = vals.get("Gastos totales"), vals.get("Intereses de la deuda")
            if gt is None or it is None:
                continue
            gprim = gt - it
            rows.append([vista, y, m, periodo, _RESFISC_GPRIM, "monto_corr", round(gprim, 1)])
            if ipc:
                rows.append([vista, y, m, periodo, _RESFISC_GPRIM, "monto_real",
                             round(gprim * base / ipc, 1)])
            if gprim:
                for concepto in _RESFISC_PCT:
                    if concepto in vals:
                        rows.append([vista, y, m, periodo, concepto, "pct_gprim",
                                     round(vals[concepto] / gprim * 100, 2)])

    fields = ["grano", "anio", "mes", "periodo", "concepto", "metrica", "valor"]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "grano": ["acumulado", "mensual"],
            "anio": sorted({r[1] for r in rows}),
            "periodo": sorted({r[3] for r in rows}),
            "concepto": [c for c, _ in _RESFISC_CONCEPTOS] + [_RESFISC_GPRIM],
        },
        "metricas": _con_base(RESFISC_METRICAS, "monto_real"),
        "notas": [
            "resultado-fiscal: Esquema Ahorro-Inversión-Financiamiento (ejecución consolidada Adm. "
            "Central + Organismos Descentralizados, devengado), fuente presupuesto.salta.gob.ar. "
            "Resultado financiero = ingresos totales − gastos totales (VIII = XI en Salta).",
            "resultado-fiscal: el resultado primario es un cálculo propio (resultado financiero + "
            "intereses de la deuda), la fuente no publica una línea primaria. Los reales se deflactan "
            "por el IPC NOA del mes y quedan en pesos de %s; la base es el último mes publicado del "
            "IPC y se mueve con él." % _base_txt(True),
            "resultado-fiscal: en la vista ACUMULADA el total enero-mes se deflacta por el índice del "
            "mes de cierre, no mes a mes. Sirve para comparar el mismo mes entre años, que es para lo "
            "que está el acumulado, pero no para comparar meses dentro de un año.",
            "resultado-fiscal: `pct_gprim` expresa el resultado financiero y el primario como % del "
            "GASTO PRIMARIO (gastos totales − intereses de la deuda). Es la medida de esfuerzo fiscal "
            "que no depende de la inflación ni del tamaño nominal del presupuesto. Al ser un cociente "
            "entre dos flujos del mismo período da idéntico en pesos corrientes y constantes, así que "
            "no se duplica por moneda. En el acumulado los meses NO son comparables entre sí (enero "
            "arranca alto y el ratio baja al avanzar el año): la comparación válida es contra el mismo "
            "mes del año anterior.",
            "resultado-fiscal: el informe de diciembre es el cierre anual y reexpresa el resultado del "
            "año (el flujo mensual de diciembre incorpora ajustes de cierre); 2024-12 no fue publicado.",
        ],
    }


# ==========================================================================
# TEMA — Recaudación de Ingresos Brutos (Convenio Multilateral), por sector
# ==========================================================================
RECAUD_METRICAS = {
    "recaud_corr": {"label": "Recaudación (pesos corrientes)", "unidad": "pesos", "agg": "sum"},
    "recaud_real": {"label": "Recaudación (pesos constantes)", "unidad": "pesos", "agg": "sum"},
}
# Etiqueta legible por letra CIIU (sección de actividad).
_SECTOR_LABEL = {
    "A": "Agro, ganadería y silvicultura", "B": "Pesca", "C": "Minas y canteras",
    "D": "Industria manufacturera", "E": "Electricidad, gas y agua", "F": "Construcción",
    "G": "Comercio", "H": "Hotelería y restaurantes", "I": "Transporte y comunicaciones",
    "J": "Intermediación financiera", "K": "Servicios inmobiliarios y empresariales",
    "L": "Administración pública", "M": "Enseñanza", "N": "Salud y servicios sociales",
    "O": "Servicios comunitarios y personales", "P": "Servicio doméstico",
    "Q": "Organizaciones extraterritoriales",
}


def _sector_label(letra):
    key = str(letra).strip().upper()
    if key.startswith("SIN"):
        return "Sin clasificar"
    return _SECTOR_LABEL.get(key, str(letra).strip().title())


def recaudacion():
    ipcm = _ipc_noa_map()
    _, base = _ipc_base()
    df = pd.read_csv(_drv("Recaudacion_AAEE_ConvenioMultilateral_Salta_por_letra_desde_2021.csv"),
                     encoding="utf-8-sig", thousands=",")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")
    df["recaudacion_ars"] = pd.to_numeric(df["recaudacion_ars"], errors="coerce")
    df = df.dropna(subset=["anio", "mes", "recaudacion_ars"])
    df["anio"] = df["anio"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["sector"] = df["letra"].map(_sector_label)
    df["trimestre"] = [_trim_label(a, m) for a, m in zip(df["anio"], df["mes"])]
    df["ipc"] = (df["anio"] * 100 + df["mes"]).map(ipcm)
    # Un mes sin IPC se descarta ENTERO, no sólo de la serie real: los agregados usan .sum(), que
    # saltea los NaN, así que el trimestre habría publicado tres meses en corrientes y dos en
    # constantes bajo la misma etiqueta. Descartado el mes, `_completos` baja el trimestre.
    df = df[df["ipc"].notna()].copy()
    df["real"] = df["recaudacion_ars"] * base / df["ipc"]

    rows = []
    # Mensual (cada mes, por sector)
    for r in df.itertuples(index=False):
        y, m = int(r.anio), int(r.mes)
        periodo = f"{y}-{m:02d}"
        rows.append(["mensual", y, m, r.trimestre, periodo, r.sector, "recaud_corr", round(float(r.recaudacion_ars), 1)])
        if pd.notna(r.real):
            rows.append(["mensual", y, m, r.trimestre, periodo, r.sector, "recaud_real", round(float(r.real), 1)])
    # Trimestral y anual (suma de meses), por sector
    gq = df.groupby(["sector", "anio", "trimestre"], as_index=False).agg(corr=("recaudacion_ars", "sum"), real=("real", "sum"))
    for r in gq.itertuples(index=False):
        rows.append(["trimestral", int(r.anio), 0, r.trimestre, "", r.sector, "recaud_corr", round(float(r.corr), 1)])
        rows.append(["trimestral", int(r.anio), 0, r.trimestre, "", r.sector, "recaud_real", round(float(r.real), 1)])
    ga = df.groupby(["sector", "anio"], as_index=False).agg(corr=("recaudacion_ars", "sum"), real=("real", "sum"))
    for r in ga.itertuples(index=False):
        rows.append(["anual", int(r.anio), 0, "", "", r.sector, "recaud_corr", round(float(r.corr), 1)])
        rows.append(["anual", int(r.anio), 0, "", "", r.sector, "recaud_real", round(float(r.real), 1)])

    # No emitir el último trimestre/año incompleto (caída ficticia).
    trims_ok, anios_ok, _tl = _completos(df, mes_col="mes")
    rows = _keep_completos(rows, trims_ok, anios_ok, gi=0, ai=1, ti=3)

    fields = ["grano", "anio", "mes", "trimestre", "periodo", "sector", "metrica", "valor"]
    sectores = [s for s in _SECTOR_LABEL.values()] + ["Sin clasificar"]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "grano": ["mensual", "trimestral", "anual"],
            "anio": sorted({r[1] for r in rows if r[0] == "anual"}),
            "trimestre": sorted({r[3] for r in rows if r[0] == "trimestral" and r[3]}, key=_trim_key),
            "periodo": sorted({r[4] for r in rows if r[4]}),
            "sector": [s for s in sectores if s in {r[5] for r in rows}],
        },
        "metricas": _con_base(RECAUD_METRICAS, "recaud_real"),
        "notas": [
            "recaudacion: Impuesto a las Actividades Económicas (Ingresos Brutos), régimen CONVENIO "
            "MULTILATERAL únicamente (no incluye contribuyentes locales/directos); por sector de "
            "actividad (CIIU). Fuente: DGR / Ministerio de Economía de Salta.",
            "recaudacion: mensual desde 2021, sumada por trimestre/año; cada mes se deflacta con el "
            "IPC NOA de ese mes y queda en pesos de %s (la base es el último mes publicado del IPC y "
            "se mueve con él). No se emite el último período incompleto." % _base_txt(True),
        ],
    }


# ==========================================================================
# TEMA — Exportaciones de Salta por rubro y país de destino (INDEC COMEX)
# ==========================================================================
# Valor FOB en dólares CORRIENTES: no se deflacta (no hay deflactor de comercio exterior en
# el repo y el estándar del INDEC es dólares corrientes). Se emite en USD enteros y en
# toneladas, NO en millones: el formateador compacto de charts.js abrevia 1447,687 como
# "1,4 K" (ambiguo, son 1.447 millones) mientras que 1.447.687.147 lo abrevia "1447,7 M".
EXPO_METRICAS = {
    "fob_usd": {"label": "Exportaciones (USD FOB)", "unidad": "USD", "agg": "sum"},
    "peso_ton": {"label": "Volumen exportado (toneladas)", "unidad": "toneladas", "agg": "sum"},
}

# Primer dígito del código de país del INDEC -> continente. Verificado contra los 146 países
# presentes (cada bloque trae además su propio "Indeterminado (América)", "(Europa)", etc.).
_EXPO_CONTINENTE = {
    "1": "África", "2": "América", "3": "Asia", "4": "Europa", "5": "Oceanía",
    "9": "Indeterminado",
}
_EXPO_CONT_ORDEN = ["América", "Asia", "Europa", "África", "Oceanía", "Indeterminado"]

# Etiquetas más cortas para las leyendas: las del CSV son las del INDEC, demasiado largas.
_EXPO_GR_LABEL = {
    "Manufacturas de origen agropecuario (MOA)": "Manufacturas agropecuarias (MOA)",
    "Manufacturas de origen industrial (MOI)": "Manufacturas industriales (MOI)",
}
_EXPO_GR_ORDEN = ["Productos primarios", "Manufacturas agropecuarias (MOA)",
                  "Manufacturas industriales (MOI)", "Combustibles y energía"]
# Los rubros x9899 son el agregado por secreto estadístico: el INDEC no publica el rubro fino,
# sólo el gran rubro. Se muestran como categoría propia (no se reparten ni se excluyen), así
# que necesitan una etiqueta corta para el ranking.
_EXPO_RUBRO_LABEL = {
    "Productos primarios (confidencial)": "Confidencial (primarios)",
    "Manufacturas de origen agropecuario (confidencial)": "Confidencial (MOA)",
    "Manufacturas de origen industrial (confidencial)": "Confidencial (MOI)",
    "Combustibles y energía (confidencial)": "Confidencial (combustibles)",
    "Resto de los productos de molinería y de las preparaciones a base de cereales,harina,"
    "almidón,fécula o leche,productos de pastelería": "Resto de molinería y panificados",
    "Resto de residuos alimenticios y preparados para animales": "Resto de alimento animal",
    "Resto de hortalizas y legumbres sin elaborar": "Resto de hortalizas sin elaborar",
    "Resto de azúcar y artículos de confitería": "Resto de azúcar y confitería",
    "Resto semillas y frutos oleaginosos": "Resto de semillas oleaginosas",
}


def exportaciones():
    df = pd.read_csv(_drv("Salta_exportaciones_INDEC_rubro_destino_desde_2021.csv"),
                     encoding="utf-8-sig")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["fob_usd"] = pd.to_numeric(df["fob_usd"], errors="coerce")
    df["peso_neto_kg"] = pd.to_numeric(df["peso_neto_kg"], errors="coerce")
    df = df.dropna(subset=["anio", "fob_usd"])
    df["anio"] = df["anio"].astype(int)

    df["gran_rubro"] = [_EXPO_GR_LABEL.get(g, g) for g in df["gran_rubro"].astype(str).str.strip()]
    ru = df["rubro"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    df["rubro"] = [_EXPO_RUBRO_LABEL.get(r, r) for r in ru]
    df["continente"] = df["pais_cod"].astype(str).str.strip().str[0].map(_EXPO_CONTINENTE)
    faltan_cont = int(df["continente"].isna().sum())
    df["continente"] = df["continente"].fillna("Indeterminado")

    # Sólo filas atómicas (anio x rubro x país): ningún total precalculado, así el navegador
    # agrega por gran rubro / continente / país / rubro sin riesgo de doble conteo.
    rows = []
    for r in df.itertuples(index=False):
        rows.append([r.anio, r.gran_rubro, r.rubro, r.continente, r.pais_destino,
                     "fob_usd", round(float(r.fob_usd), 2)])
        if pd.notna(r.peso_neto_kg):
            rows.append([r.anio, r.gran_rubro, r.rubro, r.continente, r.pais_destino,
                         "peso_ton", round(float(r.peso_neto_kg) / 1000.0, 3)])

    fields = ["anio", "gran_rubro", "rubro", "continente", "pais_destino", "metrica", "valor"]
    tot = df.groupby("anio")["fob_usd"].sum()
    conf = df[df["confidencial"] == 1].groupby("anio")["fob_usd"].sum()
    pct = (conf / tot * 100).round(1).dropna()
    notas = [
        "exportaciones: exportaciones de Salta por rubro y país de destino, base ANUAL del INDEC "
        "(COMEX, `Datos_origen_2002_2025.xlsb`, provincia de ORIGEN). Valor FOB en dólares "
        "CORRIENTES (sin deflactar) y peso neto. Metodología y controles en "
        "`datos-drive/Metodologia_Salta_exportaciones_INDEC_rubro_destino.md`.",
        "exportaciones: el secreto estadístico oculta el rubro fino de una parte creciente del "
        "valor exportado (" + "; ".join("%d: %s %%" % (a, p) for a, p in pct.items()) + "). Esas "
        "operaciones se muestran como categoría propia ('Confidencial (…)'), conservan país de "
        "destino y gran rubro, y NO se reparten entre los rubros identificados.",
        "exportaciones: `gran_rubro` y `continente` se derivan del primer dígito del código de "
        "rubro y de país del INDEC. El máximo detalle de producto con apertura provincial es el "
        "rubro; la posición arancelaria (NCM) sólo existe a nivel nacional.",
        "exportaciones: el control automático de saltos de magnitud marca valores a >1000× de la "
        "mediana. NO es un artefacto de parseo: la fuente es binaria (.xlsb leído con pyxlsb, sin "
        "separadores que interpretar) y la distribución del comercio es de cola muy larga (la "
        "mediana de una celda rubro×país ronda los 135.000 USD y la mayor supera los 380 M). "
        "Verificado además contra el total nacional del INDEC, con diferencia de 0,98 USD sobre "
        "87.111 M.",
    ]
    if faltan_cont:
        notas.append("exportaciones: %d filas con código de país sin continente asignable; "
                     "se agrupan en 'Indeterminado'." % faltan_cont)
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "gran_rubro": [g for g in _EXPO_GR_ORDEN if g in {r[1] for r in rows}],
            "rubro": sorted({r[2] for r in rows}),
            "continente": [c for c in _EXPO_CONT_ORDEN if c in {r[3] for r in rows}],
            "pais_destino": sorted({r[4] for r in rows}),
        },
        "metricas": EXPO_METRICAS,
        "notas": notas,
    }


# ==========================================================================
# TEMA — Salud (estadísticas vitales y de servicios, MSP Salta)
# ==========================================================================
# Cuatro CSV con unidades de análisis distintas se funden en un solo esquema canónico:
#   provincial            -> departamento="Salta", area_operativa="Total"
#   por Área Operativa    -> departamento=<depto>, area_operativa=<AO>
#   por departamento      -> departamento=<depto>, area_operativa="Total"
# `nacidos_vivos` (provincial, con apertura por peso) y `nacidos_vivos_res` (por residencia)
# son métricas DISTINTAS a propósito: comparten el concepto pero no la unidad de análisis, y
# mezclarlas haría que un gráfico sin filtro sumara la serie provincial con sus propias aperturas.
SALUD_METRICAS = {
    "nacidos_vivos":         {"label": "Nacidos vivos",                 "unidad": "nacimientos", "agg": "sum"},
    "nacidos_vivos_res":     {"label": "Nacidos vivos (por residencia)", "unidad": "nacimientos", "agg": "sum"},
    "defunciones":           {"label": "Defunciones",                   "unidad": "defunciones", "agg": "sum"},
    "defunciones_infantiles": {"label": "Defunciones de menores de 1 año", "unidad": "defunciones", "agg": "sum"},
    "defunciones_maternas":  {"label": "Defunciones maternas",          "unidad": "defunciones", "agg": "sum"},
    "defunciones_fetales":   {"label": "Defunciones fetales",           "unidad": "defunciones", "agg": "sum"},
    "otras_defunciones":     {"label": "Otras defunciones",             "unidad": "defunciones", "agg": "sum"},
    "matrimonios":           {"label": "Matrimonios",                   "unidad": "matrimonios", "agg": "sum"},
    "tasa_natalidad":        {"label": "Tasa de natalidad",             "unidad": "por mil habitantes",    "agg": "mean"},
    "tasa_mortalidad_general": {"label": "Tasa de mortalidad general",  "unidad": "por mil habitantes",    "agg": "mean"},
    "tasa_mortalidad_infantil": {"label": "Tasa de mortalidad infantil", "unidad": "por mil nacidos vivos", "agg": "mean"},
    "tasa_mortalidad_materna": {"label": "Tasa de mortalidad materna",  "unidad": "por diez mil nacidos vivos", "agg": "mean"},
    "poblacion":             {"label": "Población estimada",            "unidad": "habitantes", "agg": "mean"},
    "consultas_medicas":     {"label": "Consultas médicas",             "unidad": "consultas",  "agg": "sum"},
    "consultas_por_habitante": {"label": "Consultas médicas por habitante", "unidad": "consultas/hab.", "agg": "mean"},
    "camas_disponibles":     {"label": "Camas disponibles",             "unidad": "camas (promedio)", "agg": "sum"},
    "pacientes_dia":         {"label": "Pacientes-día",                 "unidad": "pacientes (promedio)", "agg": "sum"},
    "ocupacion_camas":       {"label": "Ocupación de camas",            "unidad": "%",          "agg": "mean"},
    "permanencia_promedio":  {"label": "Permanencia promedio",          "unidad": "días",       "agg": "mean"},
    "giro_camas":            {"label": "Giro de camas",                 "unidad": "egresos/cama", "agg": "mean"},
    "egresos":               {"label": "Egresos hospitalarios",         "unidad": "egresos",    "agg": "sum"},
    "altas":                 {"label": "Altas",                         "unidad": "altas",      "agg": "sum"},
    "defunciones_hosp":      {"label": "Defunciones hospitalarias",     "unidad": "defunciones", "agg": "sum"},
    "pases":                 {"label": "Pases internos",                "unidad": "pases",      "agg": "sum"},
    "establecimientos":      {"label": "Establecimientos con internación", "unidad": "establecimientos", "agg": "sum"},
    "tasa_mortalidad_hospitalaria": {"label": "Tasa de mortalidad hospitalaria", "unidad": "%", "agg": "mean"},
}
_SALUD_DESAG_ORDEN = [
    "Total", "1 año y más", "De 1 a 4 años", "Menores de 1 año",
    "Neonatal (< 28 días)", "Posneonatal (28 días y más)",
    "Menos de 2.500 g", "2.500 g y más", "Peso sin especificar",
]


def salud():
    fields = ["anio", "departamento", "area_operativa", "desagregacion", "metrica", "valor"]
    rows, notas = [], []

    def _num(df):
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        n = int(df["valor"].isna().sum())
        if n:
            notas.append("salud: %d valores no numéricos descartados." % n)
        return df.dropna(subset=["anio", "valor"])

    # -- hechos vitales provinciales (2020-2025) ----------------------------
    hv = _num(pd.read_csv(_drv("Salud_Hechos_Vitales_Salta_provincia_2020-2025.csv"),
                          encoding="utf-8-sig"))
    for r in hv.itertuples(index=False):
        rows.append([int(r.anio), "Salta", "Total", r.desagregacion, r.metrica, float(r.valor)])

    # -- servicios provinciales: consultas e internación (2021-2025) --------
    sv = _num(pd.read_csv(_drv("Salud_Servicios_Salta_provincia_2021-2025.csv"),
                          encoding="utf-8-sig"))
    for r in sv.itertuples(index=False):
        rows.append([int(r.anio), "Salta", "Total", "Total", r.metrica, float(r.valor)])

    # -- nacidos vivos por Área Operativa de residencia (2021-2025) --------
    ao = _num(pd.read_csv(_drv("Salud_Nacidos_Vivos_Salta_area_operativa_2021-2025.csv"),
                          encoding="utf-8-sig"))
    ao["departamento"] = ao["departamento"].map(norm_dept)
    for r in ao.itertuples(index=False):
        rows.append([int(r.anio), r.departamento, r.area_operativa, "Total",
                     r.metrica, float(r.valor)])

    # -- internación por departamento (sólo 2025) --------------------------
    # No trae fila provincial: esa serie ya viene del CSV de servicios y duplicarla haría que
    # los gráficos por departamento contaran dos veces el total.
    it = _num(pd.read_csv(_drv("Salud_Internacion_Salta_departamento_2025.csv"),
                          encoding="utf-8-sig"))
    it["departamento"] = it["departamento"].map(norm_dept)
    anios_it = sorted({int(a) for a in it["anio"]})
    for r in it.itertuples(index=False):
        rows.append([int(r.anio), r.departamento, "Total", "Total", r.metrica, float(r.valor)])

    deptos = [d for d in sorted({r[1] for r in rows})
              if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    aos = [a for a in sorted({r[2] for r in rows}) if a != "Total"]
    desag = ([d for d in _SALUD_DESAG_ORDEN if d in {r[3] for r in rows}]
             + sorted({r[3] for r in rows} - set(_SALUD_DESAG_ORDEN)))

    notas += [
        "salud: la apertura territorial de nacimientos es por ÁREA OPERATIVA de residencia "
        "(circunscripción sanitaria), no por departamento; el pasaje a departamento lo hace el "
        "script de datos-drive/Actualizar_Salud_Estadisticas_Vitales_Salta.md y es una "
        "aproximación. La suma de las 47 AO coincide exactamente con el total provincial en los "
        "cinco años.",
        "salud: el detalle departamental de internación existe sólo para %s; la serie 2021–2025 "
        "de internación es provincial. Los cocientes por departamento (ocupación, permanencia, "
        "giro, mortalidad) se recalculan sobre los totales sumados de sus establecimientos, no se "
        "promedian." % ", ".join(str(a) for a in anios_it),
        "salud: las tres tablas provinciales del documento fuente se contradicen entre sí "
        "(defunciones 2021/2024/2025, nacidos vivos 2025). Se publica la Tabla 1 (Resumen "
        "Quinquenal), la única internamente consistente y la única que cierra contra la apertura "
        "territorial. El detalle está en datos-drive/Metodologia_Salud_Estadisticas_Vitales_Salta.md.",
        "salud: las tasas de mortalidad general de 2021 y 2022 no se reproducen con la población "
        "que publica el propio documento (la fuente usó proyecciones anteriores a las INDEC "
        "2022–2040); se publican tal como las emitió el MSP.",
        "salud: 2025 es provisorio en toda la fuente.",
    ]
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "departamento": deptos,
            "area_operativa": aos,
            "desagregacion": desag,
        },
        "metricas": SALUD_METRICAS,
        "notas": notas,
    }


# ==========================================================================
# TEMA — Conectividad: internet fijo (ENACOM) + tasa por departamento (Censo 2022)
# ==========================================================================
CON_METRICAS = {
    "acc_100_hog": {"label": "Accesos cada 100 hogares", "unidad": "accesos/100 hogares", "agg": "mean"},
    "acc_100_hab": {"label": "Accesos cada 100 habitantes", "unidad": "accesos/100 hab.", "agg": "mean"},
    "accesos":     {"label": "Accesos a internet fijo", "unidad": "accesos", "agg": "sum"},
    "vel_mbps":    {"label": "Velocidad media de bajada", "unidad": "Mbps", "agg": "mean"},
    "acc_100_hog_censo": {"label": "Accesos cada 100 hogares (Censo 2022)", "unidad": "accesos/100 hogares",
                          "agg": "mean"},
    "pct_fibra":   {"label": "Accesos por fibra óptica (% del total)", "unidad": "%", "agg": "mean"},
}
_CON_TECNO = {"adsl": "ADSL", "cablemodem": "Cablemódem", "fibra_optica": "Fibra óptica",
              "wireless": "Wireless", "otros": "Otros"}


def conectividad():
    rows = []

    def ambito(p):
        return "Argentina" if str(p).strip().lower() == "total país" else ("Salta" if str(p).lower() == "salta" else None)

    def add(grano, y, t, depto, amb, tec, met, v):
        if pd.notna(v):
            rows.append([grano, int(y), t, depto, amb, tec, met, round(float(v), 2)])

    pen = pd.read_csv(_src("ENACOM_internet_penetracion_provincias.csv"), encoding="utf-8-sig")
    vel = pd.read_csv(_src("ENACOM_internet_velocidad_media_provincias.csv"), encoding="utf-8-sig")
    acc = pd.read_csv(_src("ENACOM_internet_accesos_tecnologia_provincias.csv"), encoding="utf-8-sig")
    vcol = next(c for c in vel.columns if "mbps" in c)
    for df, cols in ((pen, {"accesos_cada_100_hogares": "acc_100_hog", "accesos_cada_100_habitantes": "acc_100_hab"}),
                     (vel, {vcol: "vel_mbps"})):
        for r in df.itertuples(index=False):
            d = dict(zip(df.columns, r))
            amb = ambito(d["provincia"])
            if amb is None:
                continue
            t = f"{int(d['año'])}-T{int(d['trimestre'])}"
            for c, m in cols.items():
                add("trimestral", d["año"], t, "Salta", amb, "Total", m, pd.to_numeric(d[c], errors="coerce"))
    for r in acc.itertuples(index=False):
        d = dict(zip(acc.columns, r))
        if ambito(d["provincia"]) != "Salta":
            continue
        t = f"{int(d['año'])}-T{int(d['trimestre'])}"
        for c, tec in list(_CON_TECNO.items()) + [("total", "Total")]:
            add("trimestral", d["año"], t, "Salta", "Salta", tec, "accesos", pd.to_numeric(d[c], errors="coerce"))
    # Anual = promedio de los trimestres del año (como en `financiero`)
    tri = pd.DataFrame(rows, columns=["grano", "anio", "trimestre", "departamento", "ambito", "tecnologia",
                                      "metrica", "valor"])
    for k, v in tri.groupby(["anio", "departamento", "ambito", "tecnologia", "metrica"])["valor"].mean().items():
        add("anual", k[0], "", k[1], k[2], k[3], k[4], v)

    # Por departamento (desde 2026-T2): 'anual' = último trimestre disponible de cada año
    dep = pd.read_csv(_src("ENACOM_internet_departamentos_Salta.csv"), encoding="utf-8-sig", dtype={"depto_cod": str})
    dep = dep[dep["hogares_censo2022"].notna()]
    dep["departamento"] = dep["departamento"].map(norm_dept)
    ult = dep.sort_values(["anio", "trimestre"]).groupby("anio")["trimestre"].transform("max") == dep["trimestre"]
    for grano, sub in (("trimestral", dep), ("anual", dep[ult])):
        for r in sub.itertuples(index=False):
            t = f"{r.anio}-T{r.trimestre}" if grano == "trimestral" else ""
            add(grano, r.anio, t, r.departamento, "Salta", "Total", "acc_100_hog_censo", r.accesos_cada_100_hogares)
            add(grano, r.anio, t, r.departamento, "Salta", "Total", "pct_fibra", r.pct_fibra_optica)
        g = sub.groupby(["anio", "trimestre"], as_index=False)[["total", "hogares_censo2022", "Fibra óptica"]].sum()
        for r in g.itertuples(index=False):
            t = f"{r.anio}-T{r.trimestre}" if grano == "trimestral" else ""
            add(grano, r.anio, t, "Salta", "Salta", "Total", "acc_100_hog_censo", 100 * r.total / r.hogares_censo2022)
            add(grano, r.anio, t, "Salta", "Salta", "Total", "pct_fibra", 100 * r[4] / r.total)  # r[4] = Fibra óptica

    fields = ["grano", "anio", "trimestre", "departamento", "ambito", "tecnologia", "metrica", "valor"]
    deptos = [d for d in sorted({r[3] for r in rows}) if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    trimestres = sorted({r[2] for r in rows if r[2]}, key=_trim_key)
    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "trimestre": trimestres,
            "departamento": deptos,
            "ambito": ["Salta", "Argentina"],
            "tecnologia": list(_CON_TECNO.values()) + ["Total"],
        },
        "metricas": CON_METRICAS,
        "trims_completos": trimestres,
        "notas": [
            "conectividad: ENACOM, accesos a internet fijo por provincia (trimestral desde 2015). La "
            "penetración por hogares se recalculó con proyecciones del Censo 2022, lo que baja los "
            "valores desde 2022; el salto de accesos de Salta entre 2025-T4 y 2026-T1 responde a "
            "cambios en la fuente.",
            "conectividad: la apertura por departamento parte de la tabla de ENACOM por localidad, que "
            "solo publica el último trimestre (serie desde 2026-T2, se acumula en cada actualización); "
            "la tasa usa hogares del Censo 2022 (no comparable estrictamente con la provincial de ENACOM).",
        ],
    }


# ==========================================================================
# TEMAS SOCIALES — Dimensiones I a IV de las notas técnicas de indicadores sociales
# (xlsx estáticos elaborados por el CESS, en datos-drive/). Casi todo es UN corte por
# departamento; la única serie temporal es la anual de suicidios 2017-2024.
# ==========================================================================
_SOC_DEPTOS = set(_DEPT_CANON.values())


def _soc_celda(c):
    """Valor de la celda; los porcentajes con formato % de Excel vienen como fracción."""
    v = getattr(c, "value", None)
    if isinstance(v, (int, float)) and "%" in (getattr(c, "number_format", "") or ""):
        return v * 100
    return v


@functools.lru_cache(maxsize=None)
def _soc_libro(archivo):
    wb = openpyxl.load_workbook(_drv(archivo), read_only=True, data_only=True)
    libro = {ws.title.strip(): [tuple(_soc_celda(c) for c in f) for f in ws.iter_rows()]
             for ws in wb.worksheets}
    wb.close()
    return libro


def _soc_tabla(archivo, hoja, clave="Departamento", bloque=0):
    """Filas de la tabla que arranca en la fila cuyo primer valor es `clave` (la `bloque`-ésima
    de la hoja) y termina en la primera fila vacía."""
    filas = _soc_libro(archivo)[hoja]
    i = [k for k, f in enumerate(filas) if f and str(f[0] or "").strip() == clave][bloque]
    out = []
    for f in filas[i + 1:]:
        if not f or f[0] is None or not str(f[0]).strip():
            break
        out.append(f)
    return out


def _soc_num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:  # texto: "5,586" (miles con coma), "14.2%", "ND"
        return float(str(v).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


def _soc_depto(s):
    """'Total Provincia' -> 'Salta'; quita la marca '(*)' de Aprender. None si no es depto."""
    s = str(s).replace("(*)", "").strip()
    if s == "Total Provincia":
        return "Salta"
    d = norm_dept(s)
    return d if d in _SOC_DEPTOS else None


def _soc_leer(archivo, specs):
    """specs: [(hoja, col, metrica, anio, {dim: valor}, bloque)] -> registros (dict)."""
    regs = []
    for hoja, col, met, anio, dims, bloque in specs:
        for f in _soc_tabla(archivo, hoja, bloque=bloque):
            d, v = _soc_depto(f[0]), _soc_num(f[col] if col < len(f) else None)
            if d is not None and v is not None:
                regs.append(dict(dims, anio=anio, departamento=d, metrica=met, valor=round(v, 4)))
    return regs


def _soc_payload(regs, fields, metricas, notas):
    rows = [[r.get(k, "Total") for k in fields[:-2]] + [r["metrica"], r["valor"]] for r in regs]
    dims = {k: sorted({r[i] for r in rows}, key=str) for i, k in enumerate(fields[:-2])}
    dims["departamento"] = [d for d in dims["departamento"] if d not in PROVINCIAL_TOKENS]
    return {"fields": fields, "rows": rows, "dims": dims, "metricas": metricas, "notas": notas}


# -- Dimensión I: condiciones de vida (privación material, Censo 2022) -------
CV_ARCHIVO = "Dimension_I_CV_vf.xlsx"
CV_METRICAS = {
    "pct_hogares": {"label": "Hogares en situación de privación (%)", "unidad": "% de hogares", "agg": "mean"},
    "hogares_priv": {"label": "Hogares en situación de privación", "unidad": "hogares", "agg": "sum"},
}
# hoja -> (indicador, columna de hogares privados, columna del %)
_CV_HOJAS = {
    "NBI": ("NBI", 3, 4),
    "Hacinamiento": ("Hacinamiento crítico", 3, 4),
    "Condiciones sanitarias": ("Condiciones sanitarias (NBI)", 3, 4),
    "Capacidad de subsistencia": ("Capacidad de subsistencia (NBI)", 3, 4),
    "Clima educativo": ("Clima educativo bajo o muy bajo", 4, 5),
    "Agua": ("Sin agua por cañería en la vivienda", 4, 5),
    "Inodoro": ("Sin inodoro con descarga de agua", 4, 5),
    "Propiedad de la vivienda": ("No propietarios de la vivienda", 3, 4),
    "Computadora-tablet": ("Sin computadora ni tablet", 3, 4),
    "Internet en la vivienda": ("Sin internet en la vivienda", 3, 4),
    "Celular con internet": ("Sin celular con internet", 3, 4),
}


def condiciones_vida():
    specs = []
    for hoja, (ind, c_n, c_pct) in _CV_HOJAS.items():
        specs += [(hoja, c_n, "hogares_priv", 2022, {"indicador": ind}, 0),
                  (hoja, c_pct, "pct_hogares", 2022, {"indicador": ind}, 0)]
    regs = _soc_leer(CV_ARCHIVO, specs)
    return _soc_payload(regs, ["anio", "departamento", "indicador", "metrica", "valor"], CV_METRICAS, [
        "condiciones-vida: privación material de los hogares según el Censo 2022 (INDEC/REDATAM), "
        "un solo corte por departamento; xlsx estático elaborado por el CESS (Dimensión I).",
    ])


# -- Dimensión II: salud y reproducción (trienio 2021-2023 + Censo 2022) -----
SR_ARCHIVO = "Dimension_II_Salud_vf.xlsx"
SR_METRICAS = {
    "esperanza_vida":     {"label": "Esperanza de vida al nacer", "unidad": "años", "agg": "mean"},
    "tasa_bruta_mort":    {"label": "Tasa bruta de mortalidad", "unidad": "por mil hab.", "agg": "mean"},
    "tasa_mort_ajustada": {"label": "Mortalidad ajustada por edad", "unidad": "por mil hab.", "agg": "mean"},
    "razon_brecha_mort":  {"label": "Mortalidad ajustada respecto de la provincial", "unidad": "razón (provincia = 1)", "agg": "mean"},
    "cv_mort_territorial": {"label": "Dispersión territorial de la mortalidad ajustada (coef. de variación)", "unidad": "%", "agg": "mean"},
    "razon_max_min_mort": {"label": "Razón entre el departamento de mayor y menor mortalidad ajustada", "unidad": "veces", "agg": "mean"},
    "mort_prematura":     {"label": "Mortalidad prematura (30 a 69 años)", "unidad": "por cien mil hab.", "agg": "mean"},
    "apvp":               {"label": "Años potenciales de vida perdidos", "unidad": "años por cien mil hab.", "agg": "mean"},
    "mort_cardiovascular": {"label": "Mortalidad cardiovascular", "unidad": "por cien mil hab.", "agg": "mean"},
    "mort_cancer":        {"label": "Mortalidad por cáncer", "unidad": "por cien mil hab.", "agg": "mean"},
    "mort_diabetes":      {"label": "Mortalidad por diabetes", "unidad": "por cien mil hab.", "agg": "mean"},
    "tmi":                {"label": "Mortalidad infantil", "unidad": "por mil nacidos vivos", "agg": "mean"},
    "mort_menores5":      {"label": "Mortalidad de menores de 5 años", "unidad": "por mil nacidos vivos", "agg": "mean"},
    "rmm":                {"label": "Mortalidad materna", "unidad": "por cien mil nacidos vivos", "agg": "mean"},
    "pct_bajo_peso":      {"label": "Nacidos con bajo peso (< 2.500 g)", "unidad": "% de nacidos vivos", "agg": "mean"},
    "tgf":                {"label": "Tasa global de fecundidad", "unidad": "hijos por mujer", "agg": "mean"},
    "tasa_gral_fec":      {"label": "Tasa general de fecundidad", "unidad": "por mil mujeres de 15 a 49", "agg": "mean"},
    "tef":                {"label": "Tasa específica de fecundidad", "unidad": "por mil mujeres", "agg": "mean"},
    "fec_15_19":          {"label": "Fecundidad adolescente (15 a 19)", "unidad": "por mil mujeres", "agg": "mean"},
    "fec_10_14":          {"label": "Fecundidad adolescente temprana (10 a 14)", "unidad": "por mil niñas", "agg": "mean"},
    "pct_madres_adolesc": {"label": "Nacimientos de madres adolescentes", "unidad": "% de nacidos vivos", "agg": "mean"},
    "edad_media_mat":     {"label": "Edad media de la maternidad", "unidad": "años", "agg": "mean"},
}
_SR_EDADES = ["15 a 19", "20 a 24", "25 a 29", "30 a 34", "35 a 39", "40 a 44", "45 y más"]


def salud_reproduccion():
    a = 2023  # trienio 2021-2023
    sx = lambda s: {"sexo": s}
    specs = [
        ("Esperanza de vida al nacer", 1, "esperanza_vida", a, sx("Total"), 0),
        ("Esperanza de vida al nacer", 2, "esperanza_vida", a, sx("Varones"), 0),
        ("Esperanza de vida al nacer", 3, "esperanza_vida", a, sx("Mujeres"), 0),
        ("Tasa bruta de mortalidad", 3, "tasa_bruta_mort", a, sx("Total"), 0),
        ("Tasa bruta de mortalidad", 6, "tasa_bruta_mort", a, sx("Varones"), 0),
        ("Tasa bruta de mortalidad", 6, "tasa_bruta_mort", a, sx("Mujeres"), 1),
        ("Mortalidad ajustada por edad", 1, "tasa_mort_ajustada", a, sx("Total"), 0),
        ("Mortalidad ajustada por edad", 2, "tasa_mort_ajustada", a, sx("Varones"), 0),
        ("Mortalidad ajustada por edad", 3, "tasa_mort_ajustada", a, sx("Mujeres"), 0),
        ("Brecha territorial mortalidad", 2, "razon_brecha_mort", a, {}, 0),
        ("Mortalidad prematura 30-69", 3, "mort_prematura", a, {}, 0),
        ("APVP", 1, "apvp", a, {}, 0),
        ("Mortalidad cardiovascular", 3, "mort_cardiovascular", a, {}, 0),
        ("Mortalidad por cáncer", 3, "mort_cancer", a, {}, 0),
        ("Mortalidad por diabetes", 3, "mort_diabetes", a, {}, 0),
        ("TMI", 3, "tmi", a, {}, 0),
        ("Mortalidad menores de 5", 4, "mort_menores5", a, {}, 0),
        ("Mortalidad materna", 3, "rmm", a, {}, 0),
        ("Bajo peso al nacer", 3, "pct_bajo_peso", a, {}, 0),
        ("Tasa global de fecundidad", 1, "tgf", a, {}, 0),
        ("Tasa general de fecundidad", 3, "tasa_gral_fec", a, {}, 0),
        ("Fecundidad adolescente 15-19", 3, "fec_15_19", a, {}, 0),
        ("Fecundidad adolescente 10-14", 3, "fec_10_14", a, {}, 0),
        ("Nacim. madres adolescentes", 3, "pct_madres_adolesc", a, {}, 0),
        ("Edad media maternidad", 1, "edad_media_mat", a, {}, 0),
    ] + [("Tasas especif. fecundidad", i + 1, "tef", a, {"edad": e}, 0) for i, e in enumerate(_SR_EDADES)]
    regs = _soc_leer(SR_ARCHIVO, specs)
    # Medidas de dispersión de la ficha II.4: filas sueltas al pie de la hoja.
    for f in _soc_libro(SR_ARCHIVO)["Brecha territorial mortalidad"]:
        txt, v = str(f[0] or "") if f else "", _soc_num(f[1]) if f and len(f) > 1 else None
        met = ("cv_mort_territorial" if txt.startswith("Coeficiente de variación") else
               "razon_max_min_mort" if txt.startswith("Razón entre el departamento") else None)
        if met and v is not None:
            regs.append({"anio": a, "departamento": "Salta", "metrica": met, "valor": round(v, 4)})
    return _soc_payload(regs, ["anio", "departamento", "sexo", "edad", "metrica", "valor"], SR_METRICAS, [
        "salud-reproduccion: tasas medias anuales del trienio 2021-2023 (defunciones y nacimientos "
        "DEIS) sobre población del Censo 2022; se publican con anio=2023. Un solo corte por "
        "departamento; en departamentos chicos las tasas son inestables (pocos casos).",
    ])


# -- Dimensión III: educación (Relevamiento Anual 2025 + Aprender 2025) ------
EA_ARCHIVO = "Dimension_III_Educacion_vf.xlsx"
EA_METRICAS = {
    "matricula":               {"label": "Matrícula", "unidad": "alumnos", "agg": "sum"},
    "pct_repitencia":          {"label": "Repitencia", "unidad": "% de la matrícula", "agg": "mean"},
    "egresados":               {"label": "Egresados", "unidad": "alumnos", "agg": "sum"},
    "tasa_egreso_aparente":    {"label": "Tasa de egreso aparente", "unidad": "%", "agg": "mean"},
    "alumnos_establecimiento": {"label": "Alumnos por establecimiento", "unidad": "alumnos", "agg": "mean"},
    "alumnos_cargo":           {"label": "Alumnos por cargo docente", "unidad": "alumnos", "agg": "mean"},
    "pct_extranjeros":         {"label": "Alumnos extranjeros", "unidad": "% de la matrícula", "agg": "mean"},
    "pct_satisf_lengua":       {"label": "Aprender Lengua: satisfactorio o avanzado", "unidad": "% de alumnos", "agg": "mean"},
    "pct_satisf_mat":          {"label": "Aprender Matemática: satisfactorio o avanzado", "unidad": "% de alumnos", "agg": "mean"},
    "aprender_lengua":         {"label": "Aprender Lengua", "unidad": "% de alumnos", "agg": "mean"},
    "aprender_matematica":     {"label": "Aprender Matemática", "unidad": "% de alumnos", "agg": "mean"},
    "aprender_sobreedad":      {"label": "Sobreedad", "unidad": "% de alumnos", "agg": "mean"},
    "aprender_nse":            {"label": "Nivel socioeconómico", "unidad": "% de alumnos", "agg": "mean"},
}
_EA_DESEMP = ["1 · Por debajo del básico", "2 · Básico", "3 · Satisfactorio", "4 · Avanzado"]
_EA_SOBRE = ["Sin sobreedad", "1 año de sobreedad", "2 años o más de sobreedad"]
_EA_NSE = ["Q1 (más bajo)", "Q2", "Q3", "Q4", "Q5 (más alto)"]


def educacion_aprendizajes():
    a, P, S = 2025, {"nivel": "Primaria"}, {"nivel": "Secundaria"}
    specs = [
        ("Matrícula por nivel", 1, "matricula", a, P, 0),
        ("Matrícula por nivel", 2, "matricula", a, S, 0),
        ("Repitencia", 1, "pct_repitencia", a, P, 0),
        ("Repitencia", 2, "pct_repitencia", a, S, 0),
        ("Egresados", 1, "egresados", a, P, 0),
        ("Egresados", 2, "egresados", a, S, 0),
        ("Egresados", 3, "tasa_egreso_aparente", a, P, 0),
        ("Egresados", 4, "tasa_egreso_aparente", a, S, 0),
        ("Estudiantes por establecimiento", 3, "alumnos_establecimiento", a, P, 0),
        ("Estudiantes por establecimiento", 6, "alumnos_establecimiento", a, S, 0),
        ("Estudiantes por cargo docente", 3, "alumnos_cargo", a, P, 0),
        ("Estudiantes por cargo docente", 6, "alumnos_cargo", a, S, 0),
        ("Extranjeros", 1, "pct_extranjeros", a, P, 0),
        ("Extranjeros", 2, "pct_extranjeros", a, S, 0),
        ("Aprender Lengua", 6, "pct_satisf_lengua", a, P, 0),
        ("Aprender Matemática", 6, "pct_satisf_mat", a, P, 0),
    ]
    for hoja, met, cats, c0 in (("Aprender Lengua", "aprender_lengua", _EA_DESEMP, 2),
                                ("Aprender Matemática", "aprender_matematica", _EA_DESEMP, 2),
                                ("Aprender Sobreedad", "aprender_sobreedad", _EA_SOBRE, 2),
                                ("Aprender NSE", "aprender_nse", _EA_NSE, 2)):
        specs += [(hoja, c0 + i, met, a, dict(P, categoria=c), 0) for i, c in enumerate(cats)]
    regs = _soc_leer(EA_ARCHIVO, specs)
    return _soc_payload(regs, ["anio", "departamento", "nivel", "categoria", "metrica", "valor"], EA_METRICAS, [
        "educacion-aprendizajes: Relevamiento Anual 2025 (primaria y secundaria) y Aprender 2025 "
        "(6.º grado), por departamento; xlsx estático elaborado por el CESS (Dimensión III). Los "
        "departamentos sin dato confiable en Aprender (ND) se omiten.",
    ])


# -- Dimensión IV: seguridad (suicidios SATSSBU 2017-2024, tránsito 2021-2023) -
SEG_ARCHIVO = "Dimension_IV_Seguridad_vf.xlsx"
SEG_METRICAS = {
    "tasa_suicidio_anual":   {"label": "Tasa de suicidio", "unidad": "por cien mil hab.", "agg": "mean"},
    "suicidios_anual":       {"label": "Suicidios", "unidad": "casos", "agg": "sum"},
    "tasa_suicidio_1724":    {"label": "Tasa de suicidio (media 2017-2024)", "unidad": "por cien mil hab.", "agg": "mean"},
    "suicidios_1724":        {"label": "Suicidios (2017-2024)", "unidad": "casos", "agg": "sum"},
    "tasa_suicidio_trienio": {"label": "Tasa de suicidio (media 2021-2023)", "unidad": "por cien mil hab.", "agg": "mean"},
    "tasa_suicidio_adolesc": {"label": "Tasa de suicidio adolescente (10 a 19)", "unidad": "por cien mil hab. de 10 a 19", "agg": "mean"},
    "pct_suicidio_adolesc":  {"label": "Suicidios de adolescentes sobre el total", "unidad": "%", "agg": "mean"},
    "razon_masc_suicidio":   {"label": "Razón de tasas varones / mujeres", "unidad": "veces", "agg": "mean"},
    "pct_ahorcamiento":      {"label": "Suicidios por ahorcamiento", "unidad": "%", "agg": "mean"},
    "pct_domicilio":         {"label": "Suicidios en domicilio particular", "unidad": "%", "agg": "mean"},
    "suicidios_metodo":      {"label": "Suicidios por método (2017-2024)", "unidad": "casos", "agg": "sum"},
    "suicidios_lugar":       {"label": "Suicidios por lugar (2017-2024)", "unidad": "casos", "agg": "sum"},
    "tasa_mort_transito":    {"label": "Mortalidad por lesiones de tránsito", "unidad": "por cien mil hab.", "agg": "mean"},
    "def_transito":          {"label": "Defunciones por lesiones de tránsito (2021-2023)", "unidad": "defunciones", "agg": "sum"},
}


def seguridad():
    sx = lambda s: {"sexo": s}
    specs = [
        ("Tasa de suicidio", 3, "tasa_suicidio_trienio", 2023, {}, 0),
        ("Suicidios, tasa 2017-2024", 1, "suicidios_1724", 2024, sx("Total"), 0),
        ("Suicidios, tasa 2017-2024", 2, "tasa_suicidio_1724", 2024, sx("Total"), 0),
        ("Suicidios por sexo", 1, "suicidios_1724", 2024, sx("Varones"), 0),
        ("Suicidios por sexo", 2, "tasa_suicidio_1724", 2024, sx("Varones"), 0),
        ("Suicidios por sexo", 3, "suicidios_1724", 2024, sx("Mujeres"), 0),
        ("Suicidios por sexo", 4, "tasa_suicidio_1724", 2024, sx("Mujeres"), 0),
        ("Razón masculinidad suicidio", 2, "razon_masc_suicidio", 2024, {}, 0),
        ("Suicidio adolescente (10-19)", 2, "tasa_suicidio_adolesc", 2024, {}, 0),
        ("Prop. suicidios adolesc.", 3, "pct_suicidio_adolesc", 2024, {}, 0),
        ("Suicidios, modalidad", 3, "pct_ahorcamiento", 2024, {}, 0),
        ("Suicidios, lugar del hecho", 3, "pct_domicilio", 2024, {}, 0),
        ("Mortalidad lesiones de tránsito", 2, "def_transito", 2023, {}, 0),
        ("Mortalidad lesiones de tránsito", 3, "tasa_mort_transito", 2023, {}, 0),
    ]
    regs = _soc_leer(SEG_ARCHIVO, specs)
    # Tablas provinciales: serie anual y detalle por método / lugar.
    for f in _soc_tabla(SEG_ARCHIVO, "Suicidios, serie anual", clave="Año"):
        for col, met in ((1, "suicidios_anual"), (2, "tasa_suicidio_anual")):
            if _soc_num(f[col]) is not None:
                regs.append({"anio": int(_soc_num(f[0])), "departamento": "Salta",
                             "metrica": met, "valor": round(_soc_num(f[col]), 4)})
    for hoja, clave, met in (("Suicidios, modalidad", "Método", "suicidios_metodo"),
                             ("Suicidios, lugar del hecho", "Lugar", "suicidios_lugar")):
        for f in _soc_tabla(SEG_ARCHIVO, hoja, clave=clave):
            if _soc_num(f[1]) is not None:
                regs.append({"anio": 2024, "departamento": "Salta", "categoria": str(f[0]).strip(),
                             "metrica": met, "valor": _soc_num(f[1])})
    return _soc_payload(regs, ["anio", "departamento", "sexo", "categoria", "metrica", "valor"], SEG_METRICAS, [
        "seguridad: suicidios del SATSSBU (2017-2024; tasas medias anuales, publicadas con "
        "anio=2024) y del trienio 2021-2023 (DEIS, anio=2023), sobre población del Censo 2022. "
        "La serie anual es sólo provincial: por departamento los casos por año son muy pocos.",
        "seguridad: mortalidad por lesiones de tránsito, tasa media anual 2021-2023 (DEIS), no "
        "ajustada por edad.",
    ])


# ==========================================================================
# TEMA — Bosque nativo y uso del suelo (MapBiomas Argentina, Colección 3)
# ==========================================================================
BOS_SRC_DEP = "MapBiomas_Bosques_Salta_departamento_1987-2025.csv"
BOS_SRC_COB = "MapBiomas_Cobertura_Salta_provincia_1985-2025.csv"

# Último año que MapBiomas da por cerrado. El producto de transiciones aplica reglas de fin de
# serie a los últimos cuatro años y la colección siguiente los reescribe: en 2024 el stock de
# bosque SUBE 27.725 ha y en 2025 cae 139.417 ha. La metodología (§6) pide reportar hasta 2021.
BOS_ANIO_CONSOLIDADO = 2021

BOS_METRICAS = {
    "superficie_bosque_ha": {"label": "Superficie de bosque nativo", "unidad": "ha", "agg": "sum"},
    "share_bosque_pct": {"label": "Bosque sobre la superficie del territorio", "unidad": "%",
                         "agg": "mean"},
    "desmonte_bosque_ha": {"label": "Desmonte de bosque", "unidad": "ha", "agg": "sum"},
    "desmonte_bosque_primario_ha": {"label": "Desmonte de bosque primario", "unidad": "ha",
                                    "agg": "sum"},
    "desmonte_bosque_secundario_ha": {"label": "Desmonte de bosque secundario", "unidad": "ha",
                                      "agg": "sum"},
    "regeneracion_bosque_ha": {"label": "Regeneración de bosque", "unidad": "ha", "agg": "sum"},
    "bosque_a_otra_vegetacion_natural_ha": {"label": "Bosque que pasa a otra vegetación natural",
                                            "unidad": "ha", "agg": "sum"},
    "bosque_perdido_ha": {"label": "Bosque perdido (todas las causas)", "unidad": "ha",
                          "agg": "sum"},
    "superficie_clase_ha": {"label": "Superficie por clase de cobertura", "unidad": "ha",
                            "agg": "sum"},
    "superficie_grupo_ha": {"label": "Superficie por grupo de cobertura", "unidad": "ha",
                            "agg": "sum"},
}

# Métricas del CSV departamental que se publican tal cual. `superficie_total_ha` NO está: sólo
# sirve para derivar el porcentaje y como serie propia sería ruido.
BOS_PASAN = ["superficie_bosque_ha", "desmonte_bosque_ha", "desmonte_bosque_primario_ha",
             "desmonte_bosque_secundario_ha", "regeneracion_bosque_ha",
             "bosque_a_otra_vegetacion_natural_ha", "bosque_perdido_ha"]

# Las 18 clases de cobertura, agrupadas para que el apilado se lea: 18 series apiladas son
# ilegibles y la paleta no tiene 18 colores distinguibles. El detalle por clase sigue estando
# en `superficie_clase_ha`, que alimenta el ranking.
#
# "Otras áreas no vegetadas" NO va con lo urbano aunque las dos sean suelo sin vegetación: son
# 2,67 millones de hectáreas de puna, salares y roca contra 39.000 ha de ciudad. Agrupadas
# bajo una etiqueta con la palabra "urbano", la banda más ancha del gráfico diría lo contrario
# de lo que es.
BOS_GRUPO = {
    "Bosques cerrados": "Bosques", "Bosques abiertos": "Bosques",
    "Bosques inundables": "Bosques",
    "Arbustales cerrados": "Otra vegetación natural",
    "Arbustales abiertos": "Otra vegetación natural",
    "Mosaicos de arbustos y herbáceas": "Otra vegetación natural",
    "Herbáceas": "Otra vegetación natural",
    "Herbáceas inundables": "Otra vegetación natural",
    "Cultivos temporarios": "Agropecuario", "Cultivos perennes": "Agropecuario",
    "Pasturas": "Agropecuario", "Mosaico de usos": "Agropecuario",
    "Silvicultura": "Agropecuario",
    "Otras áreas no vegetadas": "Suelo desnudo y salares",
    "Hielo y nieve permanente": "Suelo desnudo y salares",
    "No observado": "Suelo desnudo y salares",
    "Ríos, lagunas, lagos y océano": "Agua",
    "Áreas urbanas": "Áreas urbanas",
}


def _bos_serie(anio):
    """Etiqueta de vintage del año. ES LA PALANCA QUE PARA LOS KPI EN 2021.

    Ni `renderKpis` (charts.js) ni su espejo `_calcular` (indicadores.py) miran el `year` del
    spec: los dos toman el último período con dato. Lo único que ambos respetan es `fixed`, así
    que los KPI fijan `serie: "Consolidada"` y su último dato queda en 2021, mientras los
    gráficos —que NO fijan la dimensión— reconstruyen la serie entera 1987-2025.

    El invariante que lo hace funcionar: cada (anio, departamento, clase, métrica) existe bajo
    UN solo valor de `serie`, así que sumar sobre la dimensión no duplica nada. Por eso ningún
    gráfico debe llevar un `select` sobre `serie`: partiría la serie en dos pedazos.
    """
    return "Consolidada" if int(anio) <= BOS_ANIO_CONSOLIDADO else "Provisoria"


def bosques():
    """Bosque nativo por departamento + cobertura y uso del suelo provincial (MapBiomas C3).

    Dos CSV tidy con geografías distintas que conviven en un esquema único: las filas de bosque
    llevan `clase = "Total"` y abren por departamento; las de cobertura llevan
    `departamento = "Salta"` y abren por clase. Cada gráfico elige una familia con su métrica,
    así que no se mezclan.
    """
    dep = pd.read_csv(_src(BOS_SRC_DEP), encoding="utf-8-sig")
    dep["departamento"] = dep["departamento"].map(norm_dept)
    dep["anio"] = pd.to_numeric(dep["anio"], errors="coerce").astype("Int64")
    dep["valor"] = pd.to_numeric(dep["valor"], errors="coerce")
    dep = dep.dropna(subset=["anio", "valor"])
    dep["anio"] = dep["anio"].astype(int)

    # El CSV no trae fila provincial a propósito: una fila "Salta" duplicaría todo al sumar por
    # departamento. Se arma acá, como en `ganaderia`, porque es la opción "Salta (provincia)"
    # del selector y la que leen los KPI.
    utiles = set(BOS_PASAN) | {"superficie_total_ha"}
    por_dep, prov = {}, {}
    for r in dep.itertuples(index=False):
        if r.metrica not in utiles:
            continue
        por_dep[(int(r.anio), r.departamento, r.metrica)] = float(r.valor)
        k = (int(r.anio), r.metrica)
        prov[k] = prov.get(k, 0.0) + float(r.valor)

    rows = []
    for (anio, depto, met), val in por_dep.items():
        if met in BOS_PASAN:
            rows.append([anio, depto, "Total", _bos_serie(anio), met, round(val, 1)])
    for (anio, met), val in prov.items():
        if met in BOS_PASAN:
            rows.append([anio, "Salta", "Total", _bos_serie(anio), met, round(val, 1)])

    # Porcentaje del territorio con bosque: el stock en hectáreas no se lee sin saber que Salta
    # tiene 15,5 millones. Se calcula por departamento y para la provincia.
    for (anio, depto, met), val in por_dep.items():
        if met != "superficie_bosque_ha":
            continue
        tot = por_dep.get((anio, depto, "superficie_total_ha"))
        if tot:
            rows.append([anio, depto, "Total", _bos_serie(anio), "share_bosque_pct",
                         round(val / tot * 100, 2)])
    for (anio, met), val in prov.items():
        if met != "superficie_bosque_ha":
            continue
        tot = prov.get((anio, "superficie_total_ha"))
        if tot:
            rows.append([anio, "Salta", "Total", _bos_serie(anio), "share_bosque_pct",
                         round(val / tot * 100, 2)])

    # ---- Cobertura y uso del suelo (planilla oficial por provincia) ----
    cob = pd.read_csv(_src(BOS_SRC_COB), encoding="utf-8-sig")
    cob["anio"] = pd.to_numeric(cob["anio"], errors="coerce").astype("Int64")
    cob["valor"] = pd.to_numeric(cob["valor"], errors="coerce")
    cob = cob.dropna(subset=["anio", "valor"])
    cob["anio"] = cob["anio"].astype(int)

    sin_grupo, grupos = set(), {}
    for r in cob.itertuples(index=False):
        clase = str(r.clase).strip()
        anio = int(r.anio)
        rows.append([anio, "Salta", clase, _bos_serie(anio), "superficie_clase_ha",
                     round(float(r.valor), 1)])
        g = BOS_GRUPO.get(clase)
        if g is None:
            sin_grupo.add(clase)
            continue
        grupos[(anio, g)] = grupos.get((anio, g), 0.0) + float(r.valor)
    for (anio, g), val in grupos.items():
        rows.append([anio, "Salta", g, _bos_serie(anio), "superficie_grupo_ha", round(val, 1)])

    fields = ["anio", "departamento", "clase", "serie", "metrica", "valor"]
    deptos = [d for d in sorted({r[1] for r in rows})
              if d not in NON_GEO and d not in PROVINCIAL_TOKENS]
    clases = sorted({r[2] for r in rows if r[2] != "Total"})

    notas = [
        "bosques: MapBiomas Argentina, Colección 3. El stock por clase sale de la planilla "
        "oficial por provincia; el desmonte y la regeneración, del producto de transiciones "
        "reducido por departamento en Earth Engine (la planilla sólo trae stock, y la resta "
        "entre años es cambio NETO, no desmonte).",
        "bosques: 2022-2025 son PROVISORIOS —el ráster aplica reglas de fin de serie a los "
        "últimos cuatro años y la colección siguiente los reescribe—. Los KPI y la tabla de "
        "indicadores se paran en %d, el último año consolidado, fijando serie='Consolidada'; "
        "los gráficos muestran la serie completa con la franja final marcada."
        % BOS_ANIO_CONSOLIDADO,
        "bosques: desmonte no es lo mismo que pérdida de bosque. `desmonte_bosque_ha` exige "
        "conversión a uso antrópico; `bosque_perdido_ha` incluye además el bosque que pasa a "
        "arbustal o pastizal (31.000-58.000 ha/año), donde se mezclan degradación, incendios y "
        "oscilación de la clasificación entre clases vecinas, que el producto no separa.",
        "bosques: 'regeneración' no es 'reforestación'. Es vegetación que vuelve sobre suelo "
        "que tuvo uso antrópico; no distingue restauración activa de abandono de lotes, y en "
        "los últimos años está subestimada por construcción (necesita años posteriores para "
        "confirmarse).",
        "bosques: los niveles no son comparables con Greenpeace ni con la UMSEF —para 2022 "
        "MapBiomas da 44.723 ha de desmonte y Greenpeace 15.230 ha, muy probablemente por la "
        "definición de bosque—. Usar una sola fuente y leer la tendencia, no el nivel.",
        "bosques: qc_saltos avisa sobre siete métricas, y en las siete los valores señalados "
        "están en el extremo BAJO, no en el alto: son los departamentos de puna —La Poma, "
        "Cachi, Molinos, Los Andes—, donde el bosque es marginal (La Poma, 119 ha en 1990, "
        "contra una mediana departamental de 122.082 ha). Es la escala real del territorio, "
        "no un separador decimal mal leído: los avisos son esperados.",
        "bosques: límites departamentales FAO GAUL 2025. Los Andes no tiene bosque en ningún "
        "año de la serie, así que queda fuera de los rankings y de la grilla.",
    ]
    if sin_grupo:
        notas.append("bosques: clases de cobertura sin grupo asignado (quedan fuera del "
                     "apilado): %s. Revisar BOS_GRUPO." % ", ".join(sorted(sin_grupo)))

    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "departamento": deptos,
            "clase": clases,
            "serie": ["Consolidada", "Provisoria"],
        },
        "metricas": BOS_METRICAS,
        "notas": notas,
    }


# ==========================================================================
# TEMA — Transparencia del sector público (municipios y Ejecutivo provincial)
# ==========================================================================
TRA_SRC_CESS = "Transparencia_Municipal_Salta_RelevamientoPropio.csv"
TRA_SRC_PROV = "Transparencia_Provincial_RelevamientoPropio.csv"

# Los 10 criterios de la grilla, agrupados por tema: primero lo presupuestario, después lo
# contractual y al final lo que hace a la apertura. Es el orden del código y de la tabla de
# datos; en el eje X de los gráficos manda el alfabético, que es como ordena `sortX`.
# Las etiquetas son más cortas que los nombres de la grilla ("Planta de personal y sueldos",
# "Declara cuántos empleados tiene"): con 10 categorías en el eje X, aun giradas 40°, los
# nombres largos se pisan. El enunciado completo de cada criterio está en la metodología.
TRA_CRITERIOS = [
    ("presupuesto_vigente", "Presupuesto vigente"),
    ("ejecucion_presupuestaria", "Ejecución presupuestaria"),
    ("planta_personal_sueldos", "Planta y sueldos"),
    ("declara_empleados", "Cantidad de empleados"),
    ("compras_contrataciones", "Compras y contrataciones"),
    ("publica_adjudicaciones", "Adjudicaciones"),
    ("declaraciones_juradas", "Declaraciones juradas"),
    ("boletin_oficial", "Boletín oficial"),
    ("canal_acceso_informacion", "Acceso a la información"),
    ("datos_abiertos", "Datos abiertos"),
]

# Valor crudo -> etiqueta. El orden alfabético de las etiquetas ("No", "No verificado",
# "Parcial", "Sí") apila la barra de peor a mejor, que es como se quiere leer.
TRA_ESTADO = {"si": "Sí", "parcial": "Parcial", "no": "No", "no_verificado": "No verificado"}
TRA_ORDEN_ESTADO = ["No", "No verificado", "Parcial", "Sí"]
# Peso de cada estado en el índice: sí = 1, parcial = 0,5, no y no verificado = 0.
TRA_PESO = {"Sí": 1.0, "Parcial": 0.5, "No": 0.0, "No verificado": 0.0}

# Los CSV de transparencia nombran cuatro municipios de otra forma que el resto del sitio. Sin
# este mapa el mismo municipio aparecería dos veces en el buscador y en el selector.
# "Salta" -> "Salta (ciudad)" es la convención que ya usan construcción y recursos-municipios:
# "Salta" a secas es el token provincial.
TRA_MUNI_ALIAS = {
    "Salta": "Salta (ciudad)",
    "San José de los Cerrillos": "Cerrillos",
    "San José de Metán": "Metán",
    "Profesor Salvador Mazza": "Prof. Salvador Mazza",
}

TRA_METRICAS = {
    "transparencia": {"label": "Índice de transparencia", "unidad": "/100", "agg": "sum"},
    "puntaje_pct": {"label": "Cumplimiento del criterio", "unidad": "/100", "agg": "mean"},
    "municipios": {"label": "Municipios", "unidad": "municipios", "agg": "sum"},
    "municipios_con_sitio": {"label": "Municipios con sitio web oficial",
                             "unidad": "municipios", "agg": "sum"},
    "municipios_en_cero": {"label": "Municipios con índice cero",
                           "unidad": "municipios", "agg": "sum"},
}


def _tra_muni(nombre):
    n = str(nombre).strip()
    return TRA_MUNI_ALIAS.get(n, n)


def transparencia():
    """Transparencia activa de los 60 municipios de Salta y del Ejecutivo provincial.

    Dos relevamientos propios del CESS sobre los mismos 10 criterios conviven en un esquema
    único: el de los 60 municipios y el del Ejecutivo provincial, que se distinguen por
    `nivel`. Cada gráfico elige una familia con su métrica y su `fixed`. No se usa ninguna
    medición de terceros.

    Mide PUBLICACIÓN ACTIVA en canales oficiales en línea, en una fecha: no mide cumplimiento
    legal, ni calidad de lo publicado, ni lo que se entrega a pedido. Las salvedades completas
    están en `datos/metodologia/Metodologia_Transparencia_*.md` y en `notas`.
    """
    cess = pd.read_csv(_src(TRA_SRC_CESS), encoding="utf-8-sig")
    prov = pd.read_csv(_src(TRA_SRC_PROV), encoding="utf-8-sig")

    # El año sale de la fecha de verificación: los dos niveles se relevaron en la misma semana
    # (municipios el 04-11, provincia el 07-11) y la tabla maestra muestra el período, no el día.
    anio = int(str(cess["fecha_verificacion"].iloc[0])[:4])

    rows = []

    def emitir(nivel, dep, muni, crit, estado, met, val):
        rows.append([anio, nivel, dep, muni, crit, estado, met, round(float(val), 2)])

    # ---- Índice por municipio ----
    for r in cess.itertuples(index=False):
        emitir("Municipio", norm_dept(r.departamento), _tra_muni(r.municipio),
               "—", "—", "transparencia", r.transparencia)

    # ---- Conteo por criterio y estado, sobre los 60 ----
    # Se emiten también los ceros: una barra apilada con categorías faltantes se dibuja
    # incompleta y el lector no sabe si el estado no existe o vale cero.
    for clave, etiqueta in TRA_CRITERIOS:
        vals = [TRA_ESTADO.get(str(v).strip(), "No") for v in cess["crit_" + clave]]
        for est in TRA_ORDEN_ESTADO:
            emitir("Municipio", "—", "—", etiqueta, est, "municipios", vals.count(est))

    # ---- Puntaje por criterio: Ejecutivo provincial contra el promedio de los 60 ----
    # Lleva los dos niveles a la misma escala 0-100 para que se puedan dibujar juntos: el
    # provincial es el peso de su propio estado; el municipal, el promedio de los 60 pesos.
    fila_prov = prov.iloc[0]
    for clave, etiqueta in TRA_CRITERIOS:
        est_prov = TRA_ESTADO.get(str(fila_prov["crit_" + clave]).strip(), "No")
        emitir("Ejecutivo provincial", "—", "—", etiqueta, est_prov,
               "puntaje_pct", TRA_PESO[est_prov] * 100)
        pesos = [TRA_PESO[TRA_ESTADO.get(str(v).strip(), "No")] for v in cess["crit_" + clave]]
        emitir("Municipios (promedio)", "—", "—", etiqueta, "—",
               "puntaje_pct", sum(pesos) / len(pesos) * 100)

    # ---- Índice del Ejecutivo provincial ----
    emitir("Ejecutivo provincial", "—", "—", "—", "—",
           "transparencia", fila_prov["transparencia"])

    # ---- Cobertura de los 60 municipios ----
    con_sitio = int(cess["sitio_oficial"].fillna("").astype(str).str.strip().ne("").sum())
    en_cero = int((pd.to_numeric(cess["transparencia"], errors="coerce") == 0).sum())
    emitir("Municipio", "—", "—", "—", "—", "municipios_con_sitio", con_sitio)
    emitir("Municipio", "—", "—", "—", "—", "municipios_en_cero", en_cero)

    fields = ["anio", "nivel", "departamento", "municipio",
              "criterio", "estado", "metrica", "valor"]
    munis = [m for m in sorted({r[3] for r in rows})
             if m != "—" and m not in NON_GEO and m not in PROVINCIAL_TOKENS]
    deptos = [d for d in sorted({r[2] for r in rows})
              if d != "—" and d not in NON_GEO and d not in PROVINCIAL_TOKENS]

    notas = [
        "transparencia: mide PUBLICACIÓN ACTIVA en canales oficiales en línea, en una fecha. No "
        "mide cumplimiento de la ley de acceso a la información, ni la calidad o veracidad de lo "
        "publicado, ni lo que el Estado entrega a pedido. Un municipio que publica su presupuesto "
        "en papel o en el Concejo Deliberante puntúa 0.",
        "transparencia: el indicador del Monitor es el relevamiento propio del CESS, que apoya "
        "cada puntaje en una URL oficial que cualquiera puede abrir y separa 'no publica' de 'no "
        "se pudo verificar'. Lo relevó un asistente de IA con navegador, SIN segundo codificador "
        "humano: la metodología pide que una persona del CESS verifique las evidencias, sobre "
        "todo las de los 11 municipios con puntaje, antes de darlo por publicado.",
        "transparencia: efecto piso. Con 49 de 60 municipios en cero, el promedio provincial lo "
        "determinan los 11 que puntúan y un ranking de 60 barras sería engañoso. Las lecturas "
        "defendibles son el cumplimiento por criterio y el conteo de municipios sobre cero.",
        "transparencia: no hay retrospectiva posible. Los relevamientos propios de noviembre de "
        "2026 son la línea de base, así que no hay variación interanual. "
        "Entre dos tomas, un puntaje puede cambiar porque el gobierno "
        "empezó a publicar o porque el relevador buscó mejor: la comparación honesta es criterio "
        "por criterio, con la evidencia a la vista.",
        "transparencia: la vara municipal le queda chica al nivel provincial. Criterios propios "
        "de una provincia —deuda, transferencias a municipios, presupuesto ciudadano— no se "
        "miden; se dejaron afuera para mantener la comparabilidad. El alcance es sólo el Poder "
        "Ejecutivo: Legislatura, Poder Judicial y Ministerio Público quedan fuera.",
    ]

    return {
        "fields": fields,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "nivel": ["Ejecutivo provincial", "Municipio", "Municipios (promedio)"],
            "departamento": deptos,
            "municipio": munis,
            "criterio": [e for _, e in TRA_CRITERIOS],
            "estado": TRA_ORDEN_ESTADO,
        },
        "metricas": TRA_METRICAS,
        "notas": notas,
    }


# Etiqueta del agregado nacional en los datasets que abren por jurisdicción (INDEC, AFCP).
TOTAL_PAIS = "Total del país"


# ==========================================================================
# TEMA — Movimiento aeroportuario de Salta (ANAC)
# ==========================================================================
# Dos productos distintos de la ANAC, que NO se suman ni se empalman:
#   · aterrizajes (microdatos, 2019-): abiertos por clasificación, clase de vuelo y aerolínea;
#   · series históricas (2001-): sin esas aperturas, pero con 18 años más y las rutas.
# Las cuatro aperturas NO van como cuatro dimensiones paralelas con margen "Total": un gráfico que
# se olvidara de fijar una de ellas sumaría los márgenes y el número se inflaría en silencio. Van
# como DOS columnas, `apertura` + `categoria`, de modo que cada gráfico fija una sola dimensión.
AERO_METRICAS = {
    "pax_arribos":    {"label": "Pasajeros arribados",       "unidad": "pasajeros",    "agg": "sum"},
    "vuelos_arribos": {"label": "Vuelos arribados",          "unidad": "vuelos",       "agg": "sum"},
    "pax_serie":      {"label": "Pasajeros (serie ANAC)",    "unidad": "pasajeros",    "agg": "sum"},
    "mov_serie":      {"label": "Movimientos (serie ANAC)",  "unidad": "movimientos",  "agg": "sum"},
    "pax_ruta":       {"label": "Pasajeros por ruta",        "unidad": "pasajeros",    "agg": "sum"},
}

# El dataset trae 239 explotadores: casi todos son aviación general con un vuelo suelto. El
# ranking publica los primeros por pasajeros y agrupa el resto en "Otras".
AERO_TOP_AEROLINEAS = 10


def aeropuerto():
    notas = []
    rows = []

    def emitir(df, cat_col, apertura, granos=("mensual", "trimestral", "anual")):
        """Agrega `df` (mensual, con columnas anio/n_mes/met/valor) por categoría y emite los
        granos pedidos. `apertura` nombra la lectura; `categoria`, el valor dentro de ella."""
        g = df.groupby(["anio", "n_mes", "met", cat_col], as_index=False)["valor"].sum()
        g["trimestre"] = [_trim_label(a, m) for a, m in zip(g["anio"], g["n_mes"])]
        if "mensual" in granos:
            for r in g.itertuples(index=False):
                d = r._asdict()
                a, m = int(d["anio"]), int(d["n_mes"])
                rows.append(["mensual", a, "%d-%02d" % (a, m), d["trimestre"],
                             apertura, d[cat_col], d["met"], int(round(float(d["valor"])))])
        if "trimestral" in granos:
            gq = g.groupby(["anio", "trimestre", "met", cat_col], as_index=False)["valor"].sum()
            for r in gq.itertuples(index=False):
                d = r._asdict()
                rows.append(["trimestral", int(d["anio"]), "", d["trimestre"],
                             apertura, d[cat_col], d["met"], int(round(float(d["valor"])))])
        if "anual" in granos:
            ga = g.groupby(["anio", "met", cat_col], as_index=False)["valor"].sum()
            for r in ga.itertuples(index=False):
                d = r._asdict()
                rows.append(["anual", int(d["anio"]), "", "",
                             apertura, d[cat_col], d["met"], int(round(float(d["valor"])))])

    def _num(df):
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna(subset=["valor"]).copy()
        df["anio"] = df["anio"].astype(int)
        df["n_mes"] = df["n_mes"].astype(int)
        return df

    # --- A. Aterrizajes (2019-), con las tres aperturas -----------------------------------
    at = _num(pd.read_csv(_drv("Salta_aeropuerto_ANAC_aterrizajes_mensual.csv"), encoding="utf-8-sig"))
    MET_AT = {"pasajeros": "pax_arribos", "vuelos": "vuelos_arribos"}
    at = at[at["metrica"].isin(MET_AT)].copy()
    at["met"] = at["metrica"].map(MET_AT)
    pax = (at[at["met"] == "pax_arribos"].groupby("aerolinea")["valor"].sum()
           .sort_values(ascending=False))
    top = set(pax.head(AERO_TOP_AEROLINEAS).index)
    at["aerolinea_lbl"] = [a if a in top else "Otras" for a in at["aerolinea"]]
    at["todo"] = "Total"
    emitir(at, "todo", "total")
    emitir(at, "clasificacion", "clasificacion")
    emitir(at, "clase_vuelo", "clase")
    emitir(at, "aerolinea_lbl", "aerolinea")

    # --- B. Series históricas (2001-) -----------------------------------------------------
    se = _num(pd.read_csv(_drv("Salta_aeropuerto_ANAC_series_mensual.csv"), encoding="utf-8-sig"))
    MET_SE = {"pasajeros": "pax_serie", "movimientos": "mov_serie"}
    aero = se[(se["serie"] == "aeropuerto") & (se["metrica"].isin(MET_SE))].copy()
    aero["met"] = aero["metrica"].map(MET_SE)
    # La fuente ya trae la fila "Total": NO se suman las tres clasificaciones, que la duplicaría.
    emitir(aero, "clasificacion", "clasificacion")
    tot = aero[aero["clasificacion"] == "Total"].copy()
    tot["todo"] = "Total"
    emitir(tot, "todo", "total")

    # Rutas: sólo en trimestral y anual. El gráfico es un ranking por año, y emitir 309 meses ×
    # 16 rutas engorda el JSON sin que nadie mire ese detalle.
    ruta = se[(se["serie"] == "ruta") & (se["metrica"] == "pasajeros")].copy()
    ruta["met"] = "pax_ruta"
    emitir(ruta, "aeropuerto", "ruta", granos=("trimestral", "anual"))

    # Períodos incompletos: la completitud se calcula sobre la UNIÓN de los dos datasets, porque
    # el de aterrizajes arranca en 2019 y descartaría los trimestres y años anteriores de la
    # serie larga.
    meses = pd.concat([at[["anio", "n_mes"]], se[["anio", "n_mes"]]]).drop_duplicates()
    meses["trimestre"] = [_trim_label(a, m) for a, m in zip(meses["anio"], meses["n_mes"])]
    trims_ok, anios_ok, _tl = _completos(meses, mes_col="n_mes")
    rows = _keep_completos(rows, trims_ok, anios_ok, gi=0, ai=1, ti=3)

    orden_cat = {"Total": 0, "Doméstico": 1, "Cabotaje": 1, "Internacional": 2, "Otras": 99}
    cats = sorted({r[5] for r in rows}, key=lambda c: (orden_cat.get(c, 50), c))
    notas.append(
        "aeropuerto: dos productos de la ANAC en un mismo tablero. Los aterrizajes (2019-) son "
        "sólo los arribos a Salta, abiertos por clasificación, clase de vuelo y aerolínea; la "
        "serie histórica (2001-) cuenta movimientos y pasajeros con otra definición y otro corte "
        "horario. No cierran entre sí y no se suman ni se empalman: ver "
        "`datos/metodologia/Metodologia_Salta_aeropuerto_ANAC.md`.")
    notas.append(
        "aeropuerto: el ranking publica las %d aerolíneas con más pasajeros y agrupa el resto en "
        "«Otras» (el dataset trae 239 explotadores, casi todos de aviación general). Las rutas se "
        "emiten en grano trimestral y anual." % AERO_TOP_AEROLINEAS)
    notas.append(
        "aeropuerto: el control automático de saltos de magnitud marca valores a >1000× de la "
        "mediana. NO es un artefacto de parseo: una misma métrica convive en varias aperturas, y "
        "la mediana cae sobre las categorías chicas (un vuelo escuela sin pasajeros, una ruta con "
        "doce pasajeros al año) mientras el total anual supera los 760.000. Verificado contra el "
        "CSV: el total coincide con la suma de cada apertura, al pasajero.")
    return {
        "fields": ["grano", "anio", "mes", "trimestre", "apertura", "categoria", "metrica", "valor"],
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "mes": sorted({r[2] for r in rows if r[2]}),
            "trimestre": sorted({r[3] for r in rows if r[3]}, key=_trim_key),
            "apertura": ["total", "clasificacion", "clase", "aerolinea", "ruta"],
            "categoria": cats,
        },
        "metricas": AERO_METRICAS,
        "notas": notas,
    }


# ==========================================================================
# TEMA — Ventas de supermercados (Encuesta de Supermercados, INDEC)
# ==========================================================================
SUP_METRICAS = {
    "ventas_corr":    {"label": "Ventas (pesos corrientes)",  "unidad": "pesos",        "agg": "sum"},
    "ventas_real":    {"label": "Ventas (pesos constantes)",  "unidad": "pesos",        "agg": "sum"},
    "operaciones":    {"label": "Operaciones de compra",      "unidad": "operaciones",  "agg": "sum"},
    "share_pais_pct": {"label": "Participación en el país",   "unidad": "%",            "agg": "mean"},
}


def supermercados():
    notas = []
    ipcm = _ipc_noa_map()
    _, base = _ipc_base()
    df = pd.read_csv(_drv("Supermercados_INDEC_jurisdiccion_mensual.csv"), encoding="utf-8-sig")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    df["anio"] = df["anio"].astype(int)
    df["n_mes"] = df["n_mes"].astype(int)
    # CABA, nunca "Capital Federal" ni el nombre largo: así coincide con el tablero de cemento.
    df["jurisdiccion"] = df["jurisdiccion"].replace(
        {"Ciudad Autónoma de Buenos Aires": "CABA"})

    # La serie constante del CSV se IGNORA a propósito: lleva la base del día en que se generó el
    # archivo, mientras que `_ipc_base()` se recalcula en cada build. Deflactar acá deja una sola
    # base para todo el sitio (ver Metodologia_Supermercados_INDEC.md §8.3).
    piv = (df[df["metrica"].isin(["ventas_corrientes_pesos", "cantidad_operaciones"])]
           .pivot_table(index=["anio", "n_mes", "jurisdiccion"], columns="metrica",
                        values="valor", aggfunc="sum").reset_index()
           .rename(columns={"ventas_corrientes_pesos": "ventas",
                            "cantidad_operaciones": "operaciones"}))
    piv["ipc"] = (piv["anio"] * 100 + piv["n_mes"]).map(ipcm)
    # Un mes sin IPC se descarta ENTERO, no sólo de la serie real: los agregados usan .sum(), que
    # saltea los NaN, así que el trimestre publicaría meses en corrientes y meses en constantes
    # bajo la misma etiqueta.
    faltan = sorted({"%d-%02d" % (a, m) for a, m, v
                     in zip(piv["anio"], piv["n_mes"], piv["ipc"]) if pd.isna(v)})
    if faltan:
        notas.append("supermercados: %s sin IPC NOA publicado; el mes se descarta entero (%s)."
                     % ("1 mes" if len(faltan) == 1 else "%d meses" % len(faltan),
                        ", ".join(faltan)))
    piv = piv[piv["ipc"].notna()].copy()
    piv["real"] = piv["ventas"] * base / piv["ipc"]
    piv["trimestre"] = [_trim_label(a, m) for a, m in zip(piv["anio"], piv["n_mes"])]

    rows = []
    VAL = ["ventas", "real", "operaciones"]

    def emitir(g, grano):
        """La participación se recalcula EN CADA GRANO como cociente de los agregados del período,
        no promediando las participaciones mensuales."""
        pais = {}
        for r in g.itertuples(index=False):
            d = r._asdict()
            if d["jurisdiccion"] == TOTAL_PAIS:
                pais[(int(d["anio"]), d["trimestre"], int(d["n_mes"]))] = float(d["ventas"])
        for r in g.itertuples(index=False):
            d = r._asdict()
            a, m = int(d["anio"]), int(d["n_mes"])
            com = [grano, a, "%d-%02d" % (a, m) if grano == "mensual" else "",
                   d["trimestre"] if grano != "anual" else "", d["jurisdiccion"]]
            rows.append(com + ["ventas_corr", round(float(d["ventas"]), 1)])
            rows.append(com + ["ventas_real", round(float(d["real"]), 1)])
            rows.append(com + ["operaciones", int(round(float(d["operaciones"])))])
            tp = pais.get((a, d["trimestre"], m))
            if tp:
                rows.append(com + ["share_pais_pct", round(100.0 * float(d["ventas"]) / tp, 2)])

    emitir(piv, "mensual")
    gq = piv.groupby(["jurisdiccion", "anio", "trimestre"], as_index=False)[VAL].sum()
    gq["n_mes"] = 0
    emitir(gq, "trimestral")
    ga = piv.groupby(["jurisdiccion", "anio"], as_index=False)[VAL].sum()
    ga["n_mes"] = 0
    ga["trimestre"] = ""
    emitir(ga, "anual")

    mens = piv.groupby(["anio", "n_mes", "trimestre"], as_index=False)["ventas"].sum()
    trims_ok, anios_ok, _tl = _completos(mens, mes_col="n_mes")
    rows = _keep_completos(rows, trims_ok, anios_ok, gi=0, ai=1, ti=3)

    jurs = sorted({r[4] for r in rows})
    notas.append(
        "supermercados: Encuesta de Supermercados del INDEC, panel NO probabilístico de empresas "
        "con alguna boca de al menos 200 m² de salón de ventas. El propio INDEC advierte que las "
        "ventas «no se deben considerar aisladamente como un indicador macroeconómico del "
        "consumo». La cantidad de bocas no se publica: es el tamaño del panel, no el universo.")
    notas.append(
        "supermercados: mensual desde 2017, sumado por trimestre/año; cada mes se deflacta con el "
        "IPC NOA de ese mes y queda en pesos de %s (la base es el último mes publicado del IPC y "
        "se mueve con él). La participación en el país se recalcula en cada grano como cociente "
        "de los agregados, no promediando los meses." % _base_txt(True))
    notas.append(
        "supermercados: el control automático de saltos de magnitud marca valores a >1000× de la "
        "mediana en las ventas corrientes. NO es un artefacto de parseo: la fuente es XLSX, con "
        "valores numéricos nativos, y la serie convive con 86× de inflación entre 2017 y 2026 y "
        "con el total del país al lado de Tierra del Fuego. Verificado contra el CSV: la suma de "
        "las jurisdicciones da el total del país.")
    return {
        "fields": ["grano", "anio", "mes", "trimestre", "jurisdiccion", "metrica", "valor"],
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "mes": sorted({r[2] for r in rows if r[2]}),
            "trimestre": sorted({r[3] for r in rows if r[3]}, key=_trim_key),
            "jurisdiccion": jurs,
        },
        "metricas": _con_base(SUP_METRICAS, "ventas_real"),
        "notas": notas,
    }


# ==========================================================================
# TEMA — Despachos de cemento por provincia y envase (AFCP)
# ==========================================================================
CEM_METRICAS = {
    "despachos_t":    {"label": "Despachos de cemento",     "unidad": "toneladas", "agg": "sum"},
    "share_pais_pct": {"label": "Participación en el país", "unidad": "%",         "agg": "mean"},
}


def cemento():
    notas = []
    df = pd.read_csv(_drv("Despachos_cemento_AFCP_provincia_mensual.csv"), encoding="utf-8-sig")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    df["anio"] = df["anio"].astype(int)
    df["n_mes"] = df["n_mes"].astype(int)
    ENVASE = {"despachos_bolsa_t": "Bolsa", "despachos_granel_t": "Granel",
              "despachos_total_t": "Total"}
    df["envase"] = df["metrica"].map(ENVASE)
    df = df.dropna(subset=["envase"]).copy()
    df["trimestre"] = [_trim_label(a, m) for a, m in zip(df["anio"], df["n_mes"])]

    rows = []

    def emitir(g, grano):
        """El total es el que publica la AFCP, no `bolsa + granel`: la fuente redondea cada celda
        por separado y los dos difieren en hasta una tonelada."""
        pais = {}
        for r in g.itertuples(index=False):
            d = r._asdict()
            if d["provincia"] == TOTAL_PAIS and d["envase"] == "Total":
                pais[(int(d["anio"]), d["trimestre"], int(d["n_mes"]))] = float(d["valor"])
        for r in g.itertuples(index=False):
            d = r._asdict()
            a, m = int(d["anio"]), int(d["n_mes"])
            com = [grano, a, "%d-%02d" % (a, m) if grano == "mensual" else "",
                   d["trimestre"] if grano != "anual" else "", d["provincia"], d["envase"]]
            rows.append(com + ["despachos_t", int(round(float(d["valor"])))])
            tp = pais.get((a, d["trimestre"], m))
            if tp and d["envase"] == "Total":
                rows.append(com + ["share_pais_pct", round(100.0 * float(d["valor"]) / tp, 2)])

    emitir(df, "mensual")
    gq = df.groupby(["provincia", "envase", "anio", "trimestre"], as_index=False)["valor"].sum()
    gq["n_mes"] = 0
    emitir(gq, "trimestral")
    ga = df.groupby(["provincia", "envase", "anio"], as_index=False)["valor"].sum()
    ga["n_mes"] = 0
    ga["trimestre"] = ""
    emitir(ga, "anual")

    mens = df.groupby(["anio", "n_mes", "trimestre"], as_index=False)["valor"].sum()
    trims_ok, anios_ok, _tl = _completos(mens, mes_col="n_mes")
    rows = _keep_completos(rows, trims_ok, anios_ok, gi=0, ai=1, ti=3)

    provs = sorted({r[4] for r in rows})
    notas.append(
        "cemento: despachos de la AFCP con DESTINO a cada jurisdicción; no es producción "
        "provincial. Bolsa y granel son envases, no usos: en el sector el granel se lee como obra "
        "grande y la bolsa como obra chica, pero esa lectura no es una definición de la fuente.")
    notas.append(
        "cemento: la apertura por provincia está congelada en septiembre de 2025 (la AFCP publica "
        "despachos nacionales hasta octubre de 2026, sin detalle provincial). El total es el "
        "publicado, no «bolsa + granel»: la fuente redondea cada celda por separado y los dos "
        "difieren en hasta una tonelada.")
    return {
        "fields": ["grano", "anio", "mes", "trimestre", "provincia", "envase", "metrica", "valor"],
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "mes": sorted({r[2] for r in rows if r[2]}),
            "trimestre": sorted({r[3] for r in rows if r[3]}, key=_trim_key),
            "provincia": provs,
            "envase": ["Total", "Bolsa", "Granel"],
        },
        "metricas": CEM_METRICAS,
        "notas": notas,
    }


PAT_METRICAS = {
    "inscripciones_iniciales": {"label": "Vehículos patentados (0 km)", "unidad": "vehículos",
                                "agg": "sum"},
    "transferencias":          {"label": "Transferencias (usados)",     "unidad": "vehículos",
                                "agg": "sum"},
    "parque_automotor":        {"label": "Parque automotor",            "unidad": "automotores",
                                "agg": "mean"},
    "pct_motos":               {"label": "Motos sobre el total patentado", "unidad": "%",
                                "agg": "mean"},
    "transf_por_inscripcion":  {"label": "Transferencias por cada 0 km", "unidad": "veces",
                                "agg": "mean"},
    "renovacion_1000":         {"label": "Autos 0 km cada mil del parque",
                                "unidad": "por mil automotores", "agg": "mean"},
}

PAT_CATEGORIAS = ["Total", "Autos", "Motos", "Maquinarias"]
PAT_JUR = "Salta"


def patentamiento():
    """Patentamiento, transferencias y parque automotor de Salta (DNRPA), mensual.

    Los dos CSV traen las 24 jurisdicciones; este tema muestra Salta. Abrirlo al país o al NOA
    después es agregar gráficos, no rehacer el dataset.
    """
    notas = []
    pat = pd.read_csv(_drv("Vehiculos_DNRPA_patentamiento_jurisdiccion_mensual.csv"),
                      encoding="utf-8-sig")
    par = pd.read_csv(_drv("Vehiculos_DNRPA_parque_automotor_jurisdiccion_mensual.csv"),
                      encoding="utf-8-sig")
    pat = pat[pat["jurisdiccion"] == PAT_JUR].copy()
    par = par[par["jurisdiccion"] == PAT_JUR].copy()
    for df in (pat, par):
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df["anio"] = df["anio"].astype(int)
        df["n_mes"] = df["n_mes"].astype(int)
    pat = pat.dropna(subset=["valor"])
    par = par.dropna(subset=["valor"])
    par["categoria"] = "Autos"          # el parque de la DNRPA es automotor, no incluye motos

    df = pd.concat([pat[["anio", "n_mes", "categoria", "metrica", "valor"]],
                    par[["anio", "n_mes", "categoria", "metrica", "valor"]]], ignore_index=True)
    df["trimestre"] = [_trim_label(a, m) for a, m in zip(df["anio"], df["n_mes"])]

    # Base mensual: (anio, n_mes, categoria) -> {metrica: valor}
    base = {}
    for r in df.itertuples(index=False):
        base.setdefault((int(r.anio), int(r.n_mes), r.categoria), {})[r.metrica] = float(r.valor)

    def periodos(grano):
        if grano == "mensual":
            return {(a, m, c): [(a, m, c)] for (a, m, c) in base}
        out = {}
        for (a, m, c) in base:
            k = (a, _trim_label(a, m), c) if grano == "trimestral" else (a, "", c)
            out.setdefault(k, []).append((a, m, c))
        return out

    # Cuántos meses tiene que tener un período para que se emita. No alcanza con el helper global
    # `_completos`: cada serie arranca en un año distinto (autos en 2000, motos en 2007,
    # maquinarias en septiembre de 2013, el parque en 2010), así que la completitud se mide POR
    # SERIE. Si no, el primer año de cada una se dibujaría como una caída.
    MINIMO = {"mensual": 1, "trimestral": 3, "anual": 12}

    rows = []
    for grano in ("mensual", "trimestral", "anual"):
        for clave, miembros in periodos(grano).items():
            anio, etiqueta, cat = clave
            agreg = {}
            for met in PAT_METRICAS:
                vals = [base[k][met] for k in miembros if met in base[k]]
                if len(vals) < MINIMO[grano]:
                    continue
                info = PAT_METRICAS[met]
                if info["agg"] == "sum":
                    agreg[met] = sum(vals)
                else:
                    agreg[met] = sum(vals) / len(vals)
            com = [grano, anio,
                   "%d-%02d" % (anio, miembros[0][1]) if grano == "mensual" else "",
                   etiqueta if grano == "trimestral" else "", cat]
            for met in ("inscripciones_iniciales", "transferencias"):
                if met in agreg:
                    rows.append(com + [met, int(round(agreg[met]))])
            if "parque_automotor" in agreg:
                rows.append(com + ["parque_automotor", int(round(agreg["parque_automotor"]))])

            # Los cocientes se recalculan en cada grano sobre los agregados, nunca promediando
            # los cocientes mensuales: el promedio de razones no es la razón de los promedios.
            ins, tra = agreg.get("inscripciones_iniciales"), agreg.get("transferencias")
            if ins and tra is not None:
                rows.append(com + ["transf_por_inscripcion", round(tra / ins, 2)])
            if cat == "Total" and ins:
                motos = {}
                for k in miembros:
                    km = (k[0], k[1], "Motos")
                    if km in base and "inscripciones_iniciales" in base[km]:
                        motos[km] = base[km]["inscripciones_iniciales"]
                if len(motos) >= MINIMO[grano]:
                    rows.append(com + ["pct_motos", round(100.0 * sum(motos.values()) / ins, 2)])
            if cat == "Autos" and ins and agreg.get("parque_automotor"):
                rows.append(com + ["renovacion_1000",
                                   round(1000.0 * ins / agreg["parque_automotor"], 2)])

    cats = [c for c in PAT_CATEGORIAS if c in {r[4] for r in rows}]
    ultimo = max((r[1], r[2]) for r in rows if r[0] == "mensual")

    notas.append(
        "patentamiento: inscripciones iniciales (0 km) y transferencias (usados) de la DNRPA, "
        "agregadas por año, mes y provincia. Cada categoría arranca cuando la DNRPA empieza a "
        "publicarla: automotores en 2000, motovehículos en 2007 y maquinarias en septiembre de "
        "2013. La categoría «Total» sólo se emite desde que están las tres, para que no se lea "
        "como crecimiento lo que es un cambio de cobertura.")
    notas.append(
        "patentamiento: el patentamiento se desploma en diciembre y se dispara en enero, en toda "
        "la Argentina y todos los años, porque inscribir en enero da el año modelo nuevo y eso "
        "vale en la reventa. Es estacionalidad de la fuente, no un salto del dato: para leer "
        "tendencia conviene el grano trimestral o anual.")
    notas.append(
        "patentamiento: el parque automotor de la DNRPA NO incluye motos (son 358.452 automotores "
        "en Salta a diciembre de 2024, contra un parque total de 654.998 vehículos que publica la "
        "ANSV para 2022). Por eso la tasa de renovación se calcula sólo sobre autos: numerador y "
        "denominador son los dos automotor.")
    notas.append(
        "patentamiento: NO se usa el archivo del portal de datos abiertos de Salta, que copia "
        "estas mismas series. Está mal: todo 2018 tiene los meses permutados en las seis series, "
        "y en autos además está corrido un año (su «2017» es el 2018 real, su «2018» es el 2019 "
        "real ordenado de mayor a menor, y el 2017 real —24.227 autos, el año récord— no figura). "
        "El cotejo celda por celda está en la metodología.")
    notas.append(
        "patentamiento: el dataset trae las 24 jurisdicciones; este tema muestra Salta. Último "
        "dato: %s." % ultimo[1])

    return {
        "fields": ["grano", "anio", "mes", "trimestre", "categoria", "metrica", "valor"],
        "rows": rows,
        "dims": {
            "anio": sorted({int(r[1]) for r in rows}),
            "mes": sorted({r[2] for r in rows if r[2]}),
            "trimestre": sorted({r[3] for r in rows if r[3]}, key=_trim_key),
            "categoria": cats,
        },
        "metricas": PAT_METRICAS,
        "notas": notas,
    }


# ==========================================================================
# TEMA — Producción de azúcar y alcohol por ingenio (Centro Azucarero Argentino)
# ==========================================================================
AZU_METRICAS = {
    "azucar_total_t":      {"label": "Azúcar producido",       "unidad": "toneladas",
                            "agg": "sum"},
    "cana_molida_t":       {"label": "Caña de azúcar molida",  "unidad": "toneladas",
                            "agg": "sum"},
    "alcohol_m3":          {"label": "Alcohol producido",      "unidad": "m³", "agg": "sum"},
    "azucar_por_cana_pct": {"label": "Azúcar obtenido de la caña", "unidad": "%", "agg": "mean"},
    "alcohol_por_cana_l_t": {"label": "Alcohol obtenido de la caña",
                             "unidad": "litros por tonelada", "agg": "mean"},
    "share_pais_pct":      {"label": "Participación en el azúcar del país", "unidad": "%",
                            "agg": "mean"},
    "share_noa_pct":       {"label": "Participación en el azúcar del NOA", "unidad": "%",
                            "agg": "mean"},
}

AZU_JUR = "Salta"
AZU_PAIS = "Total del país"
AZU_NOA = "NOA"
AZU_PROVINCIAS = [AZU_JUR, "Jujuy", "Tucumán", "Litoral", AZU_NOA, AZU_PAIS]
AZU_INGENIOS = ["Total", "San Isidro", "Tabacal"]
AZU_TIPOS = [("Blanco", "azucar_blanco_t"), ("Crudo", "azucar_crudo_t"),
             ("Refinado", "azucar_refinado_t"), ("Orgánico", "azucar_organico_t")]
# La apertura por ingenio arranca acá y no en 1990: entre 1990 y 2002 la fuente intercambia los
# dos ingenios de Salta (ver la metodología y la columna `calidad` del CSV). El total provincial
# no está afectado y va desde 1990.
AZU_INGENIO_DESDE = 2010
# El alcohol por ingenio no existe entre 1995 y 2006. El eje de los gráficos es categórico: si se
# emitieran los cinco años anteriores, 1994 quedaría pegado a 2007 y el hueco de trece años se
# cerraría sin que se vea. El CSV conserva 1990-1994.
AZU_ALCOHOL_DESDE = 2007


def azucar_alcohol():
    """Producción de azúcar y alcohol del Centro Azucarero Argentino, anual, por ingenio.

    Serie anual pura: `fields` arranca en `anio`, sin grano/mes/trimestre. Las desagregaciones son
    heterogéneas (provincia, ingenio, tipo de azúcar, ranking de ingenios del país), así que van
    con el par `apertura` + `categoria` de `aeropuerto()` en vez de una columna por corte.
    """
    notas = []
    df = pd.read_csv(_drv("Produccion_sucroalcoholera_CAA_ingenio_anual.csv"),
                     encoding="utf-8-sig")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    df["anio"] = df["anio"].astype(int)

    base = {}
    for r in df.itertuples(index=False):
        if r.metrica == "alcohol_m3" and int(r.anio) < AZU_ALCOHOL_DESDE:
            continue
        base.setdefault((int(r.anio), r.provincia, r.ingenio), {})[r.metrica] = float(r.valor)

    rows = []

    def emitir(anio, apertura, categoria, reg):
        """Los tres absolutos de la fuente y los dos cocientes, recalculados sobre los agregados
        de este nivel (no promediando cocientes de ingenios)."""
        for met in ("azucar_total_t", "cana_molida_t", "alcohol_m3"):
            if reg.get(met) is not None:
                rows.append([anio, apertura, categoria, met, int(round(reg[met]))])
        cana = reg.get("cana_molida_t")
        if not cana:
            return
        if reg.get("azucar_total_t") is not None:
            rows.append([anio, apertura, categoria, "azucar_por_cana_pct",
                         round(100.0 * reg["azucar_total_t"] / cana, 2)])
        if reg.get("alcohol_m3") is not None:
            rows.append([anio, apertura, categoria, "alcohol_por_cana_l_t",
                         round(1000.0 * reg["alcohol_m3"] / cana, 1)])

    for (anio, prov, ing), reg in base.items():
        if ing == "Total" and prov in AZU_PROVINCIAS:
            emitir(anio, "provincia", prov, reg)
            if prov == AZU_JUR:
                for etq, met in AZU_TIPOS:
                    if reg.get(met) is not None:
                        rows.append([anio, "tipo", etq, "azucar_total_t", int(round(reg[met]))])
        if ing != "Total":
            if prov == AZU_JUR and anio >= AZU_INGENIO_DESDE:
                emitir(anio, "ingenio", ing, reg)
            etq = "%s (%s)" % (ing, prov)
            for met in ("azucar_total_t", "cana_molida_t", "alcohol_m3"):
                if reg.get(met) is not None:
                    rows.append([anio, "ranking", etq, met, int(round(reg[met]))])
        if prov == AZU_JUR and ing == "Total" and anio >= AZU_INGENIO_DESDE:
            emitir(anio, "ingenio", "Total", reg)

    # Participación de Salta, sobre azúcar producido.
    for anio in sorted({a for (a, _p, _i) in base}):
        sal = base.get((anio, AZU_JUR, "Total"), {})
        for ref_prov, met_out in ((AZU_PAIS, "share_pais_pct"), (AZU_NOA, "share_noa_pct")):
            ref = base.get((anio, ref_prov, "Total"), {})
            if sal.get("azucar_total_t") and ref.get("azucar_total_t"):
                rows.append([anio, "provincia", AZU_JUR, met_out,
                             round(100.0 * sal["azucar_total_t"] / ref["azucar_total_t"], 2)])

    ranking = sorted({r[2] for r in rows if r[1] == "ranking"})
    cats = AZU_PROVINCIAS + [c for c in AZU_INGENIOS if c not in AZU_PROVINCIAS] + \
        [e for e, _m in AZU_TIPOS] + ranking
    anios = sorted({int(r[0]) for r in rows})

    notas.append(
        "azúcar y alcohol: producción de los ingenios azucareros que releva el Centro Azucarero "
        "Argentino, por zafra. La zafra ocupa de mayo a mediados de noviembre, así que el dato "
        "anual es una campaña completa y no un año calendario de actividad.")
    notas.append(
        "azúcar y alcohol: el CAA publica por ingenio, no por departamento. Para Salta coinciden: "
        "San Isidro está en Campo Santo (General Güemes) y San Martín del Tabacal en Hipólito "
        "Yrigoyen (Orán). Es la ubicación de la fábrica, no la del cañaveral: la caña de Tabacal "
        "viene de Orán y San Martín, y la de San Isidro de Güemes y Anta.")
    notas.append(
        "azúcar y alcohol: la apertura por ingenio empieza en %d. Entre 1990 y 2002 la fuente "
        "intercambia los dos ingenios de Salta —lo que rotula «San Isidro» es Tabacal y al revés—, "
        "y el dataset conserva ese tramo tal como se publica, marcado con calidad «rotulo_dudoso». "
        "El total provincial no está afectado y va desde 1990." % AZU_INGENIO_DESDE)
    notas.append(
        "azúcar y alcohol: desde 2016 la fuente informa caña molida BRUTA, y el azúcar obtenido "
        "por tonelada de caña baja cerca de un cuarto en todas las provincias por ese solo cambio "
        "de definición. Lo que distingue a Salta es que después sigue bajando, y eso sí es real: "
        "es caña que va a alcohol en vez de a azúcar.")
    notas.append(
        "azúcar y alcohol: el azúcar refinado y el orgánico recién se publican por separado desde "
        "2023; antes estaban dentro de «blanco». El quiebre de ese año en la composición es de "
        "cobertura, no de producción.")
    notas.append(
        "azúcar y alcohol: la fuente no publica alcohol por ingenio entre 1995 y 2006, así que la "
        "serie del tablero arranca en %d y no en 1990: empalmar los dos tramos cerraría un hueco "
        "de trece años sin que se note. El dataset conserva 1990-1994." % AZU_ALCOHOL_DESDE)
    notas.append(
        "azúcar y alcohol: NOA son las tres provincias azucareras, Jujuy, Salta y Tucumán. "
        "«Litoral» es como el CAA rotula a los tres ingenios de Santa Fe, que dejan de moler en el "
        "tramo final de la serie.")

    return {
        "fields": ["anio", "apertura", "categoria", "metrica", "valor"],
        "rows": rows,
        "dims": {
            "anio": anios,
            "apertura": ["provincia", "ingenio", "tipo", "ranking"],
            "categoria": cats,
        },
        "metricas": AZU_METRICAS,
        "notas": notas,
    }


SV_METRICAS = {
    "victimas_fatales":        {"label": "Víctimas fatales",          "unidad": "personas",
                                "agg": "sum"},
    "siniestros_fatales":      {"label": "Siniestros fatales",        "unidad": "siniestros",
                                "agg": "sum"},
    "siniestros_con_victimas": {"label": "Siniestros con víctimas",   "unidad": "siniestros",
                                "agg": "sum"},
    "siniestros_con_lesionados": {"label": "Siniestros con lesionados", "unidad": "siniestros",
                                  "agg": "sum"},
    "personas_heridas":        {"label": "Personas heridas",          "unidad": "personas",
                                "agg": "sum"},
    "tasa_mortalidad_100mil":  {"label": "Tasa de mortalidad vial",   "unidad": "por cien mil hab.",
                                "agg": "mean"},
    "tasa_fatalidad_10mil_veh": {"label": "Tasa de fatalidad vial",
                                 "unidad": "por diez mil vehículos", "agg": "mean"},
    "tasa_fatalidad_10mil_automotor": {"label": "Tasa de fatalidad cada 10 mil automotores",
                                       "unidad": "por diez mil automotores", "agg": "mean"},
    "tasa_siniestralidad_fatal_100mil": {"label": "Tasa de siniestralidad fatal",
                                         "unidad": "por cien mil hab.", "agg": "mean"},
    "tasa_siniestralidad_fatal_10mil_veh": {"label": "Tasa de siniestralidad fatal",
                                            "unidad": "por diez mil vehículos", "agg": "mean"},
    "poblacion":               {"label": "Población proyectada",      "unidad": "habitantes",
                                "agg": "mean"},
    "parque_vehicular":        {"label": "Parque vehicular registrado", "unidad": "vehículos",
                                "agg": "mean"},
}

SV_TOTAL_USUARIO = "Total"
SV_USUARIOS = [SV_TOTAL_USUARIO, "Motociclista", "Automóvil", "Peatón", "Ciclista",
               "Otros vehículos", "Sin dato"]
SV_OTRAS = "Otra jurisdicción"
SV_ANIO_MAX = 2025          # 2026 es un parcial enero-septiembre: ver nota


def seguridad_vial():
    """Siniestralidad vial por jurisdicción (ANSV), anual.

    Serie anual pura: el dataset no tiene meses, así que no se emiten `grano`, `mes` ni
    `trimestre` y ningún gráfico declara el control de frecuencia. Tampoco corre `_completos`:
    no hay períodos parciales que recortar porque no hay períodos dentro del año.
    """
    notas = []
    df = pd.read_csv(_drv("Siniestralidad_vial_ANSV_jurisdiccion_anual.csv"),
                     encoding="utf-8-sig")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    df["anio"] = df["anio"].astype(int)

    # El último año que publica la ANSV es un acumulado enero-septiembre y además le falta CABA.
    # Queda en el CSV marcado `calidad=parcial` pero no entra al tablero: puesto al lado de años
    # completos dibuja una caída que no existe. Es el mismo criterio que `_completos` aplica a los
    # trimestres en las series mensuales.
    parcial = df[df["anio"] > SV_ANIO_MAX]
    df = df[df["anio"] <= SV_ANIO_MAX]

    # `ambito` no es una dimensión nueva: es una etiqueta derivada de `jurisdiccion`, uno a uno,
    # para que el gráfico de comparación pida tres series en vez de excluir veintitrés.
    def ambito(j):
        return j if j in ("Salta", "NOA", TOTAL_PAIS) else SV_OTRAS

    rows = []
    for r in df.itertuples(index=False):
        d = r._asdict()
        v = float(d["valor"])
        rows.append([int(d["anio"]), d["jurisdiccion"], ambito(d["jurisdiccion"]),
                     d["tipo_usuario"], d["metrica"],
                     round(v, 2) if d["metrica"].startswith("tasa_") else int(round(v))])

    # --- una tasa por vehículo con denominador publicado ---------------------------------
    # La ANSV publica su propia tasa de fatalidad cada 10 mil vehículos, pero se corta en 2023 y
    # su denominador es el parque TOTAL, que para el NOA hay que despejar de las propias tasas
    # porque la tabla de parque de la ANSV no las reproduce. Esta métrica es otra cosa, y mejor
    # fundada: víctimas fatales sobre el PARQUE AUTOMOTOR que publica la DNRPA, mismo criterio
    # para las tres jurisdicciones y para todos los años, y llega hasta donde llegan las víctimas
    # fatales. No reemplaza a la de la ANSV: conviven en el mismo gráfico y miden cosas distintas
    # (el parque automotor no incluye motos).
    par = pd.read_csv(_drv("Vehiculos_DNRPA_parque_automotor_jurisdiccion_mensual.csv"),
                      encoding="utf-8-sig")
    par["valor"] = pd.to_numeric(par["valor"], errors="coerce")
    par = par.dropna(subset=["valor"])
    par["anio"] = par["anio"].astype(int)
    # Promedio de los doce meses, no el stock de diciembre: lo que se quiere medir es la
    # exposición a lo largo del año. Un año incompleto no se usa.
    cuenta = par.groupby(["anio", "jurisdiccion"])["valor"].agg(["mean", "count"])
    parque = {(int(k[0]), k[1]): float(v["mean"])
              for k, v in cuenta.iterrows() if v["count"] >= 12}
    parque.update({(a, "NOA"): sum(parque[(a, j)] for j in _AIF_NOA)
                   for a in {k[0] for k in parque}
                   if all((a, j) in parque for j in _AIF_NOA)})

    vf = {(r[0], r[1]): r[5] for r in rows
          if r[4] == "victimas_fatales" and r[3] == SV_TOTAL_USUARIO}
    nuevas = 0
    for (a, j), v in sorted(vf.items()):
        p = parque.get((a, j))
        if not p:
            continue
        rows.append([a, j, ambito(j), SV_TOTAL_USUARIO, "tasa_fatalidad_10mil_automotor",
                     round(float(1e4 * v / p), 2)])
        nuevas += 1

    jurs = sorted({r[1] for r in rows} - {"NOA", TOTAL_PAIS}) + ["NOA", TOTAL_PAIS]
    anios = sorted({r[0] for r in rows})

    notas.append(
        "seguridad-vial: siniestralidad vial de la ANSV (Observatorio Vial Nacional), que consolida "
        "lo que le reporta cada jurisdicción; en Salta, la Subsecretaría de Seguridad Vial. Víctima "
        "fatal es la persona que fallece en el lugar o hasta 30 días después del siniestro. Los "
        "datos de %d en adelante son preliminares y la ANSV los sigue actualizando; las víctimas "
        "fatales de Buenos Aires y Mendoza llevan un factor de ajuste de 1,3."
        % 2023)
    notas.append(
        "seguridad-vial: NO es lo mismo que la mortalidad por lesiones de tránsito del tema "
        "«Seguridad», que sale de la DEIS. La DEIS cuenta por causa de muerte en el certificado de "
        "defunción y la ANSV por siniestro reportado por la jurisdicción: dan números distintos "
        "para lo que se lee como lo mismo, y ninguno de los dos corrige al otro.")
    notas.append(
        "seguridad-vial: la cobertura es desigual. La única serie sin huecos es víctimas fatales "
        "con su tasa de mortalidad (2016-%d). Los siniestros fatales no están abiertos por "
        "jurisdicción en 2025 y el tipo de usuario de la vía se corta en 2022: los informes "
        "preliminares posteriores sólo lo publican por región y en porcentaje. La tasa por "
        "vehículos es la que publica la ANSV, cada 10 mil vehículos registrados."
        % SV_ANIO_MAX)
    if len(parcial):
        notas.append(
            "seguridad-vial: el dato más reciente de la ANSV (enero-septiembre de %d, sin CABA) "
            "está en el dataset pero fuera de los gráficos, porque es un acumulado parcial. En ese "
            "tramo Salta registra %d víctimas fatales en %d siniestros fatales."
            % (int(parcial["anio"].max()),
               int(parcial[(parcial["jurisdiccion"] == "Salta") &
                           (parcial["metrica"] == "victimas_fatales")]["valor"].sum()),
               int(parcial[(parcial["jurisdiccion"] == "Salta") &
                           (parcial["metrica"] == "siniestros_fatales")]["valor"].sum())))
    notas.append(
        "seguridad-vial: la tasa de fatalidad cada 10 mil AUTOMOTORES la calcula el Monitor sobre "
        "el parque automotor que publica la DNRPA (promedio de los doce meses del año). No "
        "reemplaza a la tasa cada 10 mil vehículos de la ANSV, que usa el parque total: el parque "
        "automotor no incluye motos, así que las dos no dan lo mismo y no son intercambiables. Se "
        "agrega porque la de la ANSV se corta en 2023 y porque su denominador para el NOA hay que "
        "despejarlo, mientras que este está publicado.")
    notas.append(
        "seguridad-vial: el total del país es el publicado por la ANSV, no la suma de las "
        "jurisdicciones. El NOA lo calcula el Monitor sumando Catamarca, Jujuy, La Rioja, Salta, "
        "Santiago del Estero y Tucumán —la agrupación de la propia ANSV—; sus tasas son cociente "
        "de agregados, no promedio de las tasas provinciales.")

    return {
        "fields": ["anio", "jurisdiccion", "ambito", "tipo_usuario", "metrica", "valor"],
        "rows": rows,
        "dims": {
            "anio": anios,
            "jurisdiccion": jurs,
            "ambito": ["Salta", "NOA", TOTAL_PAIS, SV_OTRAS],
            "tipo_usuario": [u for u in SV_USUARIOS if u in {r[3] for r in rows}],
        },
        "metricas": SV_METRICAS,
        "notas": notas,
    }


# ==========================================================================
# TEMAS SOCIALES DEL PDES 2030 — planillas que acompañan el informe «Área Sociocultural del
# PDES 2030. Objetivos, indicadores y brechas territoriales» (J. Paz, 2026). Cada una trae DOS
# períodos (censos 2010 y 2022, trienios, o 2018 y 2025) por departamento y por las 8 regiones
# del PDES. Se leen sólo las hojas de cada período: las de variación vienen como texto
# («-11.0 p.p.») y la variación la calcula el motor del sitio.
# ==========================================================================
# Regiones del PDES con los nombres del informe. Las planillas escriben «Prepuna» o «Pre-Puna» y
# «Valles de Lerma»; el informe, «Pre-Puna» y «Valle de Lerma».
_PDES_REGION = {
    "Puna": "Puna", "Prepuna": "Pre-Puna", "Pre-Puna": "Pre-Puna",
    "Valles Calchaquíes": "Valles Calchaquíes", "AMVL": "AMVL",
    "Valles de Lerma": "Valle de Lerma", "Valle de Lerma": "Valle de Lerma",
    "Valles Centrales": "Valles Centrales", "Chaco": "Chaco", "Yungas": "Yungas",
}
# Filas que no son un territorio: sólo cuentan en el total provincial, como en la fuente.
_PDES_FUERA = {"Departamento sin especificar", "Departamento sin determinar",
               "Celdas enmascaradas (varios dptos.)"}
PDES_FIELDS = ["anio", "periodo", "nivel_geo", "territorio", "metrica", "valor"]


def _pdes_hoja(archivo, hoja):
    """[(territorio en crudo, {encabezado: valor})] de una hoja de período.

    El encabezado es la fila cuyo primer valor empieza con «Departamento» o «Región» (fila 5
    en todas las planillas). Se lee por NOMBRE de columna y no por posición: en Aprender 2018 y
    2025 la misma columna cambia de lugar.
    """
    filas = _soc_libro(archivo)[hoja]
    i = next(k for k, f in enumerate(filas)
             if f and isinstance(f[0], str) and f[0].strip().startswith(("Departamento", "Región")))
    enc = [str(c).strip() if c is not None else "" for c in filas[i]]
    out = []
    for f in filas[i + 1:]:
        if not f or f[0] is None or not str(f[0]).strip():
            break
        out.append((str(f[0]).strip(),
                    {enc[j]: f[j] for j in range(1, min(len(enc), len(f))) if enc[j]}))
    return out


def _pdes_territorio(nombre, es_region):
    """(nivel_geo, territorio) o None si la fila no es un territorio. Aborta ante un nombre
    desconocido: una región mal escrita no puede desaparecer en silencio."""
    if nombre in _PDES_FUERA:
        return None
    if nombre == "Total Salta":
        return None if es_region else ("Provincia", "Salta")
    if es_region:
        if nombre not in _PDES_REGION:
            raise ValueError("Región desconocida en planilla del PDES: %r" % nombre)
        return "Región", "Región " + _PDES_REGION[nombre]
    d = norm_dept(nombre)
    if d not in _SOC_DEPTOS:
        raise ValueError("Departamento desconocido en planilla del PDES: %r" % nombre)
    return "Departamento", d


def _pdes_leer(archivo, periodos, columnas, derivadas=None):
    """periodos: [(anio, etiqueta del período, hoja de departamentos, hoja de regiones)]
    columnas: {metrica: encabezado exacto}; derivadas: {metrica: f(dict de valores)}.
    Devuelve filas [anio, periodo, nivel_geo, territorio, metrica, valor]."""
    rows = []
    for anio, etiqueta, hoja_dep, hoja_reg in periodos:
        for hoja, es_region in ((hoja_dep, False), (hoja_reg, True)):
            filas = _pdes_hoja(archivo, hoja)
            faltan = [c for c in columnas.values() if filas and c not in filas[0][1]]
            if faltan:
                raise ValueError("%s / %s: faltan columnas %s" % (archivo, hoja, faltan))
            for nombre, vals in filas:
                t = _pdes_territorio(nombre, es_region)
                if t is None:
                    continue
                nums = {m: _soc_num(vals.get(enc)) for m, enc in columnas.items()}
                for m, f in (derivadas or {}).items():
                    try:
                        nums[m] = f(nums)
                    except TypeError:          # algún insumo vacío
                        nums[m] = None
                for m, v in nums.items():
                    if v is not None:
                        rows.append([anio, etiqueta, t[0], t[1], m, round(v, 4)])
    return rows


def _pdes_cambios(rows, metricas):
    """Agrega, por territorio, la diferencia entre el último período y el primero (`<m>_dif`):
    alimenta el gráfico de cambio, porque el ranking horizontal descarta valores negativos."""
    por = {}
    for anio, _per, niv, ter, met, val in rows:
        if met in metricas:
            por.setdefault((niv, ter, met), {})[anio] = val
    extra = []
    for (niv, ter, met), serie in por.items():
        if len(serie) >= 2:
            a0, a1 = min(serie), max(serie)
            extra.append([a1, "Cambio", niv, ter, met + "_dif", round(serie[a1] - serie[a0], 4)])
    return rows + extra


def _pdes_payload(rows, metricas, notas):
    territorios = sorted({r[3] for r in rows if r[2] == "Departamento"}) + \
        sorted({r[3] for r in rows if r[2] == "Región"})
    return {
        "fields": PDES_FIELDS,
        "rows": rows,
        "dims": {
            "anio": sorted({r[0] for r in rows}),
            "periodo": sorted({r[1] for r in rows if r[1] != "Cambio"}),
            "nivel_geo": ["Departamento", "Región"],
            "territorio": territorios,
        },
        "metricas": metricas,
        "notas": notas,
    }


def _con_dif(metricas, unidades_dif=None):
    """Métricas + su `<m>_dif` (cambio entre períodos). Los porcentajes cambian en p.p."""
    out = dict(metricas)
    for m, d in metricas.items():
        u = d["unidad"]
        u_dif = (unidades_dif or {}).get(m) or ("p.p." if u.startswith("%") else u)
        out[m + "_dif"] = {"label": "Cambio en " + d["label"][0].lower() + d["label"][1:],
                           "unidad": u_dif, "agg": "sum"}
    return out


_PDES_NOTA_REGIONES = (
    "las 8 regiones del PDES se aproximan con departamentos completos: Puna es sólo Los Andes y "
    "Yungas sólo Orán. Las regiones son sumas de conteos departamentales con el indicador "
    "recalculado, no promedios; los casos sin departamento entran sólo al total provincial.")

# -- Censos 2010 y 2022: privación ------------------------------------------
PDES_CENSO_ARCHIVO = "Indicadores_sociocultural_Salta_2010_2022.xlsx"
PDES_CENSO_METRICAS = {
    "nbi_personas": {"label": "Personas en hogares con NBI", "unidad": "% de personas",
                     "agg": "mean"},
    "sin_agua_red": {"label": "Personas en hogares sin agua de red pública",
                     "unidad": "% de personas", "agg": "mean"},
    "nbi_indigena": {"label": "Personas indígenas en hogares con NBI", "unidad": "% de personas",
                     "agg": "mean"},
}


def pdes_privacion():
    rows = _pdes_leer(PDES_CENSO_ARCHIVO, [
        (2010, "2010", "Departamentos 2010", "Regiones 2010"),
        (2022, "2022", "Departamentos 2022", "Regiones 2022"),
    ], {
        "nbi_personas": "(1) % de personas en hogares con al menos una NBI",
        "sin_agua_red": "(2) % de personas en hogares sin agua de red pública",
        "nbi_indigena": "(3) % de personas indígenas en hogares con al menos una NBI",
    })
    rows = _pdes_cambios(rows, PDES_CENSO_METRICAS)
    return _pdes_payload(rows, _con_dif(PDES_CENSO_METRICAS), [
        "pdes-privacion: CNPV 2010 y 2022, procesamiento de microdatos para el PDES 2030 "
        "(J. Paz). 2010 sale del cuestionario ampliado (muestra expandida, con error muestral en "
        "departamentos chicos); 2022, del censo completo.",
        "pdes-privacion: la NBI indígena cambia de pregunta entre censos (2010 por hogar, 2022 "
        "autorreconocimiento individual): la variación no es la de una misma población.",
        "pdes-privacion: " + _PDES_NOTA_REGIONES,
    ])


# -- Salud: trienios 2018-2020 y 2021-2023 ----------------------------------
PDES_SALUD_ARCHIVO = "Indicadores_salud_Salta_2018_2023_regiones.xlsx"
PDES_SALUD_METRICAS = {
    "tmi": {"label": "Tasa de mortalidad infantil", "unidad": "por mil nacidos vivos",
            "agg": "mean"},
    "bajo_peso": {"label": "Nacidos vivos con bajo peso al nacer", "unidad": "% de nacidos vivos",
                  "agg": "mean"},
    "tfa_15_19": {"label": "Fecundidad adolescente (15 a 19)", "unidad": "por mil mujeres",
                  "agg": "mean"},
    "natalidad": {"label": "Tasa bruta de natalidad", "unidad": "por mil habitantes",
                  "agg": "mean"},
    "nv_sin_peso": {"label": "Nacidos vivos sin peso especificado", "unidad": "% de nacidos vivos",
                    "agg": "mean"},
}


def pdes_salud():
    rows = _pdes_leer(PDES_SALUD_ARCHIVO, [
        (2020, "2018-2020", "Salud 2018-20", "Salud 2018-20 Reg"),
        (2023, "2021-2023", "Salud 2021-23", "Salud 2021-23 Reg"),
    ], {
        "tmi": "TMI (por 1.000 NV)",
        "bajo_peso": "% bajo peso al nacer (< 2.500 g)",
        "tfa_15_19": "TFA 15–19 (por 1.000 mujeres)",
        "natalidad": "Tasa bruta de natalidad (por 1.000 hab.)",
        "nv_sin_peso": "% NV sin peso especificado",
    })
    rows = _pdes_cambios(rows, PDES_SALUD_METRICAS)
    return _pdes_payload(rows, _con_dif(PDES_SALUD_METRICAS), [
        "pdes-salud: estadísticas vitales de la DEIS por residencia, trienios 2018-2020 y "
        "2021-2023 (el año del trienio se guarda como su último año: 2020 y 2023).",
        "pdes-salud: la TMI departamental es inestable en La Poma, Los Andes, Guachipas, La "
        "Caldera y Molinos aun agregando tres años; en Puna y Pre-Puna descansa en pocos casos.",
        "pdes-salud: la población de los denominadores son proyecciones del INDEC base 2010, que "
        "el propio INDEC recomienda usar con reservas para Salta.",
        "pdes-salud: " + _PDES_NOTA_REGIONES,
    ])


# -- Educación: 2018 y 2025 (Relevamiento Anual y Aprender) ------------------
PDES_EDU_ARCHIVO = "Indicadores_educativos_Salta_2018_2025_regiones.xlsx"
PDES_EDU_METRICAS = {
    "matricula_prim_sec": {"label": "Matrícula de primaria y secundaria", "unidad": "alumnos",
                           "agg": "sum"},
    "matricula_inicial": {"label": "Matrícula de nivel inicial", "unidad": "alumnos", "agg": "sum"},
    "matricula_primaria": {"label": "Matrícula de primaria", "unidad": "alumnos", "agg": "sum"},
    "matricula_secundaria": {"label": "Matrícula de secundaria", "unidad": "alumnos", "agg": "sum"},
    "repitencia_pri": {"label": "Repitencia en primaria", "unidad": "% de la matrícula",
                       "agg": "mean"},
    "repitencia_sec": {"label": "Repitencia en secundaria", "unidad": "% de la matrícula",
                       "agg": "mean"},
    "sobreedad_pri": {"label": "Sobreedad en primaria", "unidad": "% de la matrícula",
                      "agg": "mean"},
    "sobreedad_sec": {"label": "Sobreedad en secundaria", "unidad": "% de la matrícula",
                      "agg": "mean"},
    "alumnos_seccion_pri": {"label": "Alumnos por sección en primaria", "unidad": "alumnos",
                            "agg": "mean"},
    "alumnos_seccion_sec": {"label": "Alumnos por sección en secundaria", "unidad": "alumnos",
                            "agg": "mean"},
    "secciones_multiples": {"label": "Secciones múltiples en primaria", "unidad": "% de secciones",
                            "agg": "mean"},
    "pct_estatal": {"label": "Matrícula de primaria y secundaria en el sector estatal",
                    "unidad": "% de la matrícula", "agg": "mean"},
    "pct_rural": {"label": "Matrícula de primaria y secundaria en el ámbito rural",
                  "unidad": "% de la matrícula", "agg": "mean"},
    "mat_debajo_basico": {"label": "Aprender Matemática 6.º: por debajo del nivel básico",
                          "unidad": "% de alumnos", "agg": "mean"},
    "mat_basico": {"label": "Aprender Matemática 6.º: nivel básico", "unidad": "% de alumnos",
                   "agg": "mean"},
    "mat_satisfactorio": {"label": "Aprender Matemática 6.º: nivel satisfactorio",
                          "unidad": "% de alumnos", "agg": "mean"},
    "mat_avanzado": {"label": "Aprender Matemática 6.º: nivel avanzado", "unidad": "% de alumnos",
                     "agg": "mean"},
    "mat_satisf_avanzado": {"label": "Aprender Matemática 6.º: satisfactorio o avanzado",
                            "unidad": "% de alumnos", "agg": "mean"},
    "jardin_sala3": {"label": "Alumnos de 6.º que asistieron al jardín desde sala de 3",
                     "unidad": "% de alumnos", "agg": "mean"},
    "sin_libros": {"label": "Alumnos de 6.º sin libros en el hogar", "unidad": "% de alumnos",
                   "agg": "mean"},
    "madre_secundaria": {"label": "Alumnos de 6.º con madre con secundaria completa",
                         "unidad": "% de alumnos", "agg": "mean"},
}


def pdes_educacion():
    ra = _pdes_leer(PDES_EDU_ARCHIVO, [
        (2018, "2018", "RA 2018", "RA 2018 Reg"),
        (2025, "2025", "RA 2025", "RA 2025 Reg"),
    ], {
        "matricula_inicial": "Matrícula inicial (maternal y salas 2–5)",
        "matricula_primaria": "Matrícula primaria (1.º–7.º)",
        "matricula_secundaria": "Matrícula secundaria (8.º–12.º y 13.º/14.º)",
        "repitencia_pri": "% repitentes primaria",
        "repitencia_sec": "% repitentes secundaria",
        "sobreedad_pri": "% alumnos con sobreedad primaria",
        "sobreedad_sec": "% alumnos con sobreedad secundaria",
        "alumnos_seccion_pri": "Alumnos por sección primaria",
        "alumnos_seccion_sec": "Alumnos por sección secundaria",
        "secciones_multiples": "% secciones múltiples en primaria",
        "pct_estatal": "% matrícula prim.+sec. en sector estatal",
        "pct_rural": "% matrícula prim.+sec. en ámbito rural",
    }, derivadas={
        "matricula_prim_sec": lambda n: n["matricula_primaria"] + n["matricula_secundaria"],
    })
    aprender = _pdes_leer(PDES_EDU_ARCHIVO, [
        (2018, "2018", "Aprender 2018", "Aprender 2018 Reg"),
        (2025, "2025", "Aprender 2025", "Aprender 2025 Reg"),
    ], {
        "mat_debajo_basico": "% por debajo del nivel básico",
        "mat_basico": "% nivel básico",
        "mat_satisfactorio": "% nivel satisfactorio",
        "mat_avanzado": "% nivel avanzado",
        "mat_satisf_avanzado": "% satisfactorio o avanzado",
        "jardin_sala3": "% asistió al jardín desde sala de 3 o antes",
        "sin_libros": "% sin libros en el hogar",
        "madre_secundaria": "% con madre con secundaria completa o más",
    })
    rows = _pdes_cambios(ra + aprender, PDES_EDU_METRICAS)
    return _pdes_payload(rows, _con_dif(PDES_EDU_METRICAS, {
        "matricula_prim_sec": "alumnos", "matricula_inicial": "alumnos",
        "matricula_primaria": "alumnos", "matricula_secundaria": "alumnos",
        "alumnos_seccion_pri": "alumnos", "alumnos_seccion_sec": "alumnos",
    }), [
        "pdes-educacion: Relevamiento Anual (educación común) y Aprender Matemática 6.º grado, "
        "2018 y 2025 (DiNIEE). Primaria = 1.º a 7.º y secundaria = 8.º a 12.º y 13.º/14.º.",
        "pdes-educacion: la fuente enmascara las combinaciones sector × ámbito con pocos casos y "
        "esos casos entran sólo al total: la matrícula departamental está subestimada.",
        "pdes-educacion: Aprender compara dos cohortes distintas (no sigue a los mismos "
        "alumnos) y usa ponderadores; en Guachipas, La Poma y Cachi hay pocos evaluados.",
        "pdes-educacion: " + _PDES_NOTA_REGIONES,
    ])


# -- Trabajo: censos 2010 y 2022 --------------------------------------------
PDES_TRABAJO_ARCHIVO = "Indicadores_trabajo_Salta_2010_2022.xlsx"
PDES_TRABAJO_METRICAS = {
    "desocupacion": {"label": "Tasa de desocupación, 18 años y más", "unidad": "%", "agg": "mean"},
    "informalidad": {"label": "Informalidad laboral, ocupados de 18 a 64 años",
                     "unidad": "% de ocupados", "agg": "mean"},
    "actividad_varones": {"label": "Tasa de actividad de varones, 18 a 64 años", "unidad": "%",
                          "agg": "mean"},
    "actividad_mujeres": {"label": "Tasa de actividad de mujeres, 18 a 64 años", "unidad": "%",
                          "agg": "mean"},
    "brecha_participacion": {"label": "Brecha de participación varones-mujeres, 18 a 64 años",
                             "unidad": "p.p.", "agg": "mean"},
    "informalidad_varones": {"label": "Informalidad de varones ocupados, 18 a 64 años",
                             "unidad": "% de ocupados", "agg": "mean"},
    "informalidad_mujeres": {"label": "Informalidad de mujeres ocupadas, 18 a 64 años",
                             "unidad": "% de ocupados", "agg": "mean"},
}


def pdes_trabajo():
    rows = _pdes_leer(PDES_TRABAJO_ARCHIVO, [
        (2010, "2010", "Departamentos 2010", "Regiones 2010"),
        (2022, "2022", "Departamentos 2022", "Regiones 2022"),
    ], {
        "desocupacion": "(1) Tasa de desocupación, 18 años y más",
        "informalidad": "(2) % de ocupados de 18–64 sin descuento ni aporte jubilatorio",
        "actividad_varones": "Tasa de actividad varones 18–64",
        "actividad_mujeres": "Tasa de actividad mujeres 18–64",
        "brecha_participacion": "(3) Brecha de participación varones–mujeres 18–64 (p.p.)",
        "informalidad_varones": "% de ocupados varones 18–64 sin descuento ni aporte",
        "informalidad_mujeres": "% de ocupadas mujeres 18–64 sin descuento ni aporte",
    })
    rows = _pdes_cambios(rows, PDES_TRABAJO_METRICAS)
    return _pdes_payload(rows, _con_dif(PDES_TRABAJO_METRICAS), [
        "pdes-trabajo: CNPV 2010 (cuestionario ampliado, con error muestral en departamentos "
        "chicos) y 2022 (censo completo), procesamiento de microdatos para el PDES 2030 (J. Paz).",
        "pdes-trabajo: la informalidad mide sólo la falta de protección contributiva (ocupados "
        "sin descuento ni aporte jubilatorio); la desocupación se lee junto con la actividad.",
        "pdes-trabajo: " + _PDES_NOTA_REGIONES,
    ])


# -- Delitos registrados (SNIC): trienios 2013-2015 y 2021-2023 -------------
PDES_SNIC_ARCHIVO = "Indicadores_seguridad_Salta_2013_2023.xlsx"
PDES_SNIC_METRICAS = {
    "homicidio": {"label": "Víctimas de homicidio doloso", "unidad": "por cien mil hab.",
                  "agg": "mean"},
    "robos": {"label": "Robos y tentativas de robo", "unidad": "por cien mil hab.", "agg": "mean"},
    "lesiones": {"label": "Lesiones dolosas", "unidad": "por cien mil hab.", "agg": "mean"},
    "abusos": {"label": "Abusos sexuales con acceso carnal", "unidad": "por cien mil hab.",
               "agg": "mean"},
}


def pdes_delitos():
    rows = _pdes_leer(PDES_SNIC_ARCHIVO, [
        (2015, "2013-2015", "Trienio 2013-2015", "Regiones 2013-2015"),
        (2023, "2021-2023", "Trienio 2021-2023", "Regiones 2021-2023"),
    ], {
        "homicidio": "(1) Tasa de víctimas de homicidio doloso",
        "robos": "(2) Tasa de robos (incluye tentativas)",
        "lesiones": "(3) Tasa de lesiones dolosas",
        "abusos": "(4) Tasa de abusos sexuales con acceso carnal",
    })
    rows = _pdes_cambios(rows, PDES_SNIC_METRICAS)
    return _pdes_payload(rows, _con_dif(PDES_SNIC_METRICAS), [
        "pdes-delitos: SNIC (Ministerio de Seguridad de la Nación), delitos REGISTRADOS por lugar "
        "del hecho, tasas anuales promedio por trienio (el año del trienio es su último año).",
        "pdes-delitos: las tasas bajas de Puna, Pre-Puna y Valles Calchaquíes pueden reflejar "
        "menos denuncias y menor presencia policial; el homicidio es el más comparable.",
        "pdes-delitos: " + _PDES_NOTA_REGIONES,
    ])


# Registro id_tema -> función adapter
ADAPTERS = {
    "aeropuerto": aeropuerto,
    "supermercados": supermercados,
    "cemento": cemento,
    "seguridad-vial": seguridad_vial,
    "patentamiento": patentamiento,
    "azucar-alcohol": azucar_alcohol,
    "educacion": educacion,
    "vitivinicultura": inv,
    "produccion-energia": produccion_energia,
    "empleo": empleo,
    "turismo": turismo,
    "agricultura": agricultura,
    "gobierno": gobierno,
    "ganaderia": ganaderia,
    "mineria": mineria,
    "financiero": financiero,
    "construccion": construccion,
    "recursos-municipios": recursos_municipios,
    "energia-electrica": energia_renovable,   # mismo dataset CAMMESA; el catálogo separa qué muestra
    "energia-renovable": energia_renovable,
    "id-innovacion": id_innovacion,
    "resultado-fiscal": resultado_fiscal,
    "recaudacion": recaudacion,
    "exportaciones": exportaciones,
    "salud": salud,
    "conectividad": conectividad,
    "condiciones-vida": condiciones_vida,
    "salud-reproduccion": salud_reproduccion,
    "educacion-aprendizajes": educacion_aprendizajes,
    "seguridad": seguridad,
    "bosques": bosques,
    "pdes-privacion": pdes_privacion,
    "pdes-salud": pdes_salud,
    "pdes-educacion": pdes_educacion,
    "pdes-trabajo": pdes_trabajo,
    "pdes-delitos": pdes_delitos,
    "transparencia": transparencia,
}
