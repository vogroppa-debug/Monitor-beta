# -*- coding: utf-8 -*-
"""Índice sintético por ejes del PDES — método B (postes fijos, escala 0-100).

Lo usa `build.py` para la sección «¿Cómo va el plan?» de la portada, y el script
`Indicadores/indice_sintetico/calcular_indice.py` para el Excel con el detalle (provincial y por
departamento). Los dos usan este módulo, así que no pueden diferir.

Selección de indicadores: `datos/Seleccion_indicadores_indice_sintetico.xlsx`, copia de la planilla de
trabajo del CESS (columna A = índice provincial, B = departamental). Para cambiar la selección, se edita
la planilla y se vuelve a copiar a `datos/`.

Reglas (acordadas con el usuario el 22-11-2026):
- Normalización: (x − peor) / (mejor − peor) × 100, con la dirección del `sentido` del spec.
- Postes históricos:
    * TASAS Y PORCENTAJES: mínimo y máximo de todos los valores observados, en todos los años, en la
      provincia y en los 23 departamentos (así las series de dos puntos no quedan clavadas en 0 y 100).
    * TOTALES (toneladas, puestos, pesos...): la historia de la PROPIA serie —la provincial para el
      índice provincial, la de cada departamento para el departamental—.
- Ponderación: 1/3 por eje; dentro del eje, igual peso por SUBEJE; dentro del subeje, por indicador.
- Base: 2022; si no hay, 2021 (un trienio que contiene el año cuenta); si tampoco, el período más
  cercano ANTERIOR a 2022 y, si no hay ninguno anterior, el primero disponible. Último dato: el último
  año completo.
- Fuera: los neutros, los que no tienen rango y, en el departamental, los que no abren por
  departamento. Un departamento sin dato en un indicador no se penaliza: no entra en su promedio.
"""
import re

import openpyxl

import adapters
import catalog
import indicadores as I

ANIO_BASE, ANIO_BASE_ALT = 2022, 2021
ANIO_INICIO = 2018          # primer año de la línea del tablero (actualización 2018 del PDES)
EJES = [(k, v["label"]) for k, v in sorted(catalog.EJES_PDES.items(), key=lambda kv: kv[1]["orden"])]
EJE_LABEL = dict(EJES)
DEPTOS = sorted(adapters._SOC_DEPTOS)


# ------------------------------------------------------------------ selección
def normalizar(nombre):
    """(ficha, nombre) de una celda «II.8Tasa de mortalidad infantil (...)ⓘ». La ficha es parte de
    la clave: hay indicadores homónimos (la mortalidad infantil del trienio DEIS, II.8, y la anual
    del Ministerio de Salud de Salta, sin ficha)."""
    s = str(nombre).replace("ⓘ", "").strip()
    m = re.match(r"^([IVX]+\.\d+|—)\s*", s)
    ficha = m.group(1) if m and m.group(1) != "—" else ""
    s = s[m.end():] if m else s
    return ficha, re.sub(r"\s+", " ", s).strip()


def leer_seleccion(path):
    """[((ficha, nombre), provincial, departamental)] de las filas de indicador marcadas."""
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    sel = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        a, b, nombre, frec = r[0], r[1], r[2], r[3]
        if (a or b) and nombre and frec:                  # las filas de eje y subeje no tienen frecuencia
            sel.append((normalizar(nombre), bool(a), bool(b)))
    return sel


# Frecuencia de actualización en lenguaje claro, para el listado del índice. La columna «Frecuencia» de la
# tabla dice contra qué período se compara la variación; acá interesa cada cuánto llega un dato nuevo.
_ACTUALIZACION = {
    "Intercensal": "Cada 10 años (censo)",
    "Anual": "Cada año",
    "Anual (campaña)": "Cada año (por campaña)",
    "Trimestral": "Cada trimestre",
    "Mensual": "Cada mes",
    "Mensual acum.": "Cada mes",
    "Entre trienios": "Cada año (promedio de 3 años)",
}


def actualizacion(frecuencia, nombre):
    """Cada cuánto se actualiza el dato. Las evaluaciones Aprender no son anuales: van por operativo."""
    if "Aprender" in nombre:
        return "Cada 2 años aprox."
    if frecuencia.startswith("Entre ") and frecuencia[6:7].isdigit():   # «Entre 2018 y 2025»: Relevamiento Anual
        return "Cada año"
    return _ACTUALIZACION.get(frecuencia, frecuencia)


# ------------------------------------------------------------------ series
def specs_de(tid, payload):
    """(nombre de la tabla, spec) del tema: KPIs ya sellados + EXTRA sellados con la misma base."""
    from build import stamp_base          # perezoso: build importa este módulo
    corto, largo = adapters.base_txt()
    out = []
    for s in list(payload["kpis"]) + [stamp_base(x, corto, largo) for x in I.EXTRA.get(tid, [])]:
        u = payload["metricas"].get(s["metrica"], {}).get("unidad", "")
        out.append((I._nombre_con_unidad(s.get("tabla_label") or s["label"], u), s))
    return out


def es_tasa(unidad):
    """Tasas, porcentajes y cocientes (comparables entre territorios) frente a totales."""
    u = (unidad or "").lower()
    return bool(u.startswith("%") or u.startswith("p.p.")
                or re.search(r"\bpor\b|c/|cada|/100|/10k|índice|años", u))


def freq_anual(payload):
    """Control de frecuencia del tema en su opción anual (None si el tema ya es anual)."""
    fr = I._driver_freq(payload)
    if not fr:
        return None
    anual = [v for v, o in fr["map"].items() if o.get("x") == "anio"]
    return {"value": anual[0], "map": fr["map"]} if anual else None


def serie_anual(payload, spec):
    """{año: valor} con años completos, en la agregación anual que usa el sitio."""
    ix = {k: i for i, k in enumerate(payload["fields"])}
    res = I._calcular(payload, ix, spec, freq_anual(payload))
    if res["ultimo"] is None or res["x"] != "anio":
        return {}
    ult = int(str(res["ultimo"])[:4])
    return {int(k): v for k, v in res["mapa"].items() if v is not None and int(str(k)[:4]) <= ult}


def specs_departamentales(payload, spec):
    """{depto: spec con el territorio cambiado}; {} si el indicador no abre por departamento."""
    fx = dict(spec.get("fixed") or {})
    ix = {k: i for i, k in enumerate(payload["fields"])}
    if "territorio" in ix and "nivel_geo" in ix:                       # tableros del PDES 2030
        return {d: dict(spec, fixed=dict(fx, nivel_geo="Departamento", territorio=d)) for d in DEPTOS}
    if "departamento" in ix:
        if not ({r[ix["departamento"]] for r in payload["rows"]} & set(DEPTOS)):
            return {}
        return {d: dict(spec, fixed=dict(fx, departamento=d)) for d in DEPTOS}
    if "unidad_geografica" in ix:                                      # vitivinicultura (INV)
        if not ({r[ix["unidad_geografica"]] for r in payload["rows"]} & set(DEPTOS)):
            return {}
        extra = {"nivel": "departamento"} if "nivel" in fx else {}
        return {d: dict(spec, fixed=dict(fx, unidad_geografica=d, **extra)) for d in DEPTOS}
    return {}


# ------------------------------------------------------------------ períodos
def cobertura(spec, anio):
    """(años que cubre, etiqueta): un trienio «2021-23» guardado como 2023 cubre 2021-2023."""
    lab = (spec.get("periodos") or {}).get(str(anio), "")
    m = re.match(r"^(\d{4})-(\d{2,4})$", lab)
    if m:
        fin = int(m.group(2)) if len(m.group(2)) == 4 else int(m.group(1)[:2] + m.group(2))
        return range(int(m.group(1)), fin + 1), lab
    return range(anio, anio + 1), str(anio)


def elegir_base(spec, serie):
    """(año, etiqueta, regla) del período base de una serie."""
    for objetivo in (ANIO_BASE, ANIO_BASE_ALT):
        for a in sorted(serie):
            rango, lab = cobertura(spec, a)
            if objetivo in rango:
                return a, lab, str(objetivo) if lab == str(objetivo) else "trienio que contiene %d" % objetivo
    antes = [a for a in serie if a < ANIO_BASE]
    if antes:
        a = max(antes)
        return a, cobertura(spec, a)[1], "anterior más cercano a 2022"
    a = min(serie)
    return a, cobertura(spec, a)[1], "primer dato disponible (posterior a 2022)"


def puntos(spec, serie, peor, mejor):
    """Valores y normalizados en el período base y en el último dato."""
    if not serie or peor == mejor:
        return None
    nz = lambda x: (x - peor) / (mejor - peor) * 100       # noqa: E731
    a0, lab0, regla = elegir_base(spec, serie)
    a1 = max(serie)
    return dict(anio_base=a0, base_lab=lab0, regla=regla, v_base=serie[a0], n_base=nz(serie[a0]),
                anio_ult=a1, ult_lab=cobertura(spec, a1)[1], v_ult=serie[a1], n_ult=nz(serie[a1]))


def trayectoria(spec, serie, peor, mejor, anios):
    """{año: normalizado} para cada año de `anios`, para dibujar el índice como línea.

    Cada dato vale desde el primer año que cubre (el trienio 2021-23 rige desde 2021) hasta el
    siguiente dato: un censo vale hasta el próximo censo. Antes del primer dato se usa ese primer
    dato. Es la misma regla de la base —2022, 2021, el anterior más cercano o el primero—, así
    que en 2022 la línea pasa por la base de las tarjetas y en el último año por el último dato.
    """
    if not serie or peor == mejor:
        return None
    nz = lambda x: (x - peor) / (mejor - peor) * 100       # noqa: E731
    obs = sorted((cobertura(spec, a)[0][0], a) for a in serie)
    out = {}
    for y in anios:
        previos = [a for ini, a in obs if ini <= y]
        out[y] = nz(serie[previos[-1] if previos else obs[0][1]])
    return out


def postes(sentido, valores):
    lo, hi = min(valores), max(valores)
    return (hi, lo) if sentido == "menor_mejor" else (lo, hi)          # (peor, mejor)


# ------------------------------------------------------------------ cálculo
def calcular(payloads, tabla, seleccion):
    """(indicadores, excluidos). `payloads` y `tabla` son los del build (o leídos de data/*.json)."""
    sel = leer_seleccion(seleccion)
    filas = {(f["ficha"], f["indicador"]): (g, f) for g in tabla for f in g["filas"]}

    inds, excluidos = [], []
    for clave, en_a, en_b in sel:
        if clave not in filas:
            # Un indicador marcado que el sitio ya no publica (o que cambió de nombre) no tira abajo el
            # build: queda afuera y se informa.
            excluidos.append(dict(nombre=(clave[0] + " " if clave[0] else "") + clave[1], ficha=clave[0],
                                  indice="ambos", motivo="Marcado en la selección pero no está en el sitio "
                                                         "(revisar el nombre en la planilla)."))
            continue
        g, f = filas[clave]
        ficha, nombre = clave
        p = payloads[f["tema_id"]]
        spec = next(s for n, s in specs_de(f["tema_id"], p)
                    if n == nombre and s.get("ficha", "") == ficha)
        unidad = p["metricas"].get(spec["metrica"], {}).get("unidad", "")
        sentido = spec.get("sentido", "mayor_mejor")
        m = dict(nombre=nombre, ficha=ficha, eje=g["id"], subeje=f["subeje"], sentido=sentido, unidad=unidad,
                 tasa=es_tasa(unidad), en_a=en_a, en_b=en_b, fuente=f["fuente_corta"], spec=spec,
                 frecuencia=f["frecuencia"])
        if sentido == "neutro":
            excluidos.append(dict(m, indice="ambos", motivo="Neutro: no se puede decir si subir es mejor o peor."))
            continue
        m["prov"] = serie_anual(p, spec)
        m["dept"] = {d: s for d, s in ((d, serie_anual(p, s))
                     for d, s in specs_departamentales(p, spec).items()) if s}

        # Postes
        if m["tasa"]:
            pool = list(m["prov"].values()) + [v for s in m["dept"].values() for v in s.values()]
            m["origen_postes"] = ("provincia y %d departamentos, todos los años" % len(m["dept"])
                                  if m["dept"] else "serie provincial, todos los años")
            m["postes_prov"] = postes(sentido, pool) if pool else (0, 0)
            m["postes_dept"] = {d: m["postes_prov"] for d in m["dept"]}
        else:
            m["origen_postes"] = "su propia serie (total)"
            m["postes_prov"] = postes(sentido, list(m["prov"].values())) if m["prov"] else (0, 0)
            m["postes_dept"] = {d: postes(sentido, list(s.values())) for d, s in m["dept"].items()}

        m["p_prov"] = puntos(spec, m["prov"], *m["postes_prov"])
        if en_a and m["p_prov"] is None:
            excluidos.append(dict(m, indice="provincial", motivo="Sin rango: el mejor y el peor valor coinciden."))
            m["en_a"] = False
        m["p_dept"] = {d: pt for d, pt in ((d, puntos(spec, s, *m["postes_dept"][d]))
                       for d, s in m["dept"].items()) if pt}
        if en_b and not m["dept"]:
            excluidos.append(dict(m, indice="departamental",
                                  motivo="No abre por departamento (sólo provincia o municipios)."))
            m["en_b"] = False
        if m["en_a"] or m["en_b"]:
            inds.append(m)
    return inds, excluidos


def agregar(items):
    """items: [(eje, subeje, n_base, n_ult)] -> (subejes, ejes, general) con niveles base y último."""
    prom = lambda xs: sum(xs) / len(xs) if xs else None    # noqa: E731
    sub = {}
    for eje, se, nb, nu in items:
        d = sub.setdefault((eje, se), {"b": [], "u": []})
        if nb is not None:
            d["b"].append(nb)
        if nu is not None:
            d["u"].append(nu)
    subejes = {k: {"b": prom(v["b"]), "u": prom(v["u"]), "n": len(v["u"])} for k, v in sub.items()}
    ejes = {}
    for eje, _ in EJES:
        ses = [v for (e, _s), v in subejes.items() if e == eje]
        ejes[eje] = {"b": prom([v["b"] for v in ses if v["b"] is not None]),
                     "u": prom([v["u"] for v in ses if v["u"] is not None]),
                     "n_sub": len([v for v in ses if v["u"] is not None]),
                     "n_ind": sum(v["n"] for v in ses)}
    gen = {"b": prom([v["b"] for v in ejes.values() if v["b"] is not None]),
           "u": prom([v["u"] for v in ejes.values() if v["u"] is not None])}
    return subejes, ejes, gen


def pesos_efectivos(items):
    """Peso de cada indicador en el índice general: 1/3 × 1/subejes del eje × 1/indicadores del subeje."""
    por_sub, por_eje = {}, {}
    for eje, se, _nb, _nu in items:
        por_sub[(eje, se)] = por_sub.get((eje, se), 0) + 1
    for (eje, se) in por_sub:
        por_eje[eje] = por_eje.get(eje, 0) + 1
    n_ejes = len(por_eje)
    return {(eje, se): 1.0 / n_ejes / por_eje[eje] / n for (eje, se), n in por_sub.items()}


def rebase(b, u):
    return u / b * 100 if (b not in (None, 0) and u is not None) else None


# ------------------------------------------------------------------ portada
def _num(x):
    return "" if x is None else ("%.1f" % x).replace(".", ",").replace("-", "−")


def resumen_portada(payloads, tabla, seleccion):
    """Lo que muestra la portada: el índice general y los tres ejes, provinciales."""
    inds, excluidos = calcular(payloads, tabla, seleccion)
    items = [(m["eje"], m["subeje"], m["p_prov"]["n_base"], m["p_prov"]["n_ult"])
             for m in inds if m["en_a"]]
    subejes, ejes, gen = agregar(items)

    def tarjeta(label, d, n_ind=None, n_sub=None, general=False):
        cambio = (d["u"] - d["b"]) if (d["u"] is not None and d["b"] is not None) else None
        return {"label": label, "general": general, "actual": _num(d["u"]), "base": _num(d["b"]),
                # Sin signo: la flecha de la tarjeta ya dice si subió o bajó.
                "cambio": _num(abs(cambio)) if cambio is not None else "",
                "cls": "flat" if cambio is None or abs(cambio) < 0.05 else ("up" if cambio > 0 else "down"),
                "base100": _num(rebase(d["b"], d["u"])), "n_ind": n_ind, "n_sub": n_sub}

    # -- tablero: trayectoria anual del índice (la dibuja assets/js/indice.js, en líneas)
    anios = list(range(ANIO_INICIO, max(m["p_prov"]["anio_ult"] for m in inds if m["en_a"]) + 1))
    orden_sub = I._orden_subejes(catalog.TAGS, catalog.SUBEJE_ORDEN)

    def por_anio(trays):
        """trays: [(eje, subeje, {año: normalizado})] -> [(subejes, ejes, general)] por año."""
        return [agregar([(e, se, t[a], t[a]) for e, se, t in trays]) for a in anios]

    def col(niveles, f):
        return [_r(f(n)) for n in niveles]

    trays = [(m["eje"], m["subeje"], trayectoria(m["spec"], m["prov"], *m["postes_prov"], anios=anios))
             for m in inds if m["en_a"]]
    niv = por_anio([t for t in trays if t[2]])
    provincial = {"general": col(niv, lambda n: n[2]["u"]), "ejes": []}
    for e, lab in EJES:
        ses = sorted({se for (ee, se) in subejes if ee == e and subejes[(ee, se)]["u"] is not None},
                     key=lambda x: (orden_sub.get(x, 99), x))
        provincial["ejes"].append({
            "id": e, "label": lab, "serie": col(niv, lambda n, e=e: n[1][e]["u"]),
            "subejes": [{"label": se, "n": subejes[(e, se)]["n"],
                         "serie": col(niv, lambda n, k=(e, se): n[0][k]["u"])} for se in ses]})

    departamental = []
    for d in DEPTOS:
        tr = [(m["eje"], m["subeje"], trayectoria(m["spec"], m["dept"][d], *m["postes_dept"][d], anios=anios))
              for m in inds if m["en_b"] and d in m["p_dept"]]
        tr = [t for t in tr if t[2]]
        if not tr:
            continue
        nd = por_anio(tr)
        departamental.append({
            "depto": d, "general": col(nd, lambda n: n[2]["u"]),
            "ejes": {e: col(nd, lambda n, e=e: n[1][e]["u"]) for e, _l in EJES},
            "n_ejes": len({t[0] for t in tr}), "n_ind": len(tr)})

    # -- listado de indicadores del índice, por eje y subeje, en el orden de la tabla del sitio
    orden_fila = {(f["ficha"], f["indicador"]): i for i, f in enumerate(f for g in tabla for f in g["filas"])}
    listado = []
    for e, lab in EJES:
        mi = sorted((m for m in inds if m["eje"] == e), key=lambda m: orden_fila.get((m["ficha"], m["nombre"]), 9999))
        ses = sorted({m["subeje"] for m in mi}, key=lambda x: (orden_sub.get(x, 99), x))
        listado.append({"label": lab, "subejes": [{"label": se, "filas": [
            {"ficha": m["ficha"], "nombre": m["nombre"], "prov": m["en_a"], "dept": m["en_b"],
             "sentido": "sube" if m["sentido"] == "mayor_mejor" else "baja",
             "base": m["p_prov"]["base_lab"] if m["en_a"] else "",
             "ult": m["p_prov"]["ult_lab"] if m["en_a"] else "",
             "fuente": m["fuente"], "actualizacion": actualizacion(m["frecuencia"], m["nombre"])} for m in mi if m["subeje"] == se]} for se in ses]})

    return {
        "listado": listado,
        "tarjetas": [tarjeta("Índice general", gen, len(items), general=True)]
                    + [tarjeta(lab, ejes[e], ejes[e]["n_ind"], ejes[e]["n_sub"]) for e, lab in EJES],
        "n_indicadores": len(items),
        "n_indicadores_dept": sum(1 for m in inds if m["en_b"]),
        "excluidos": ["%s (%s): %s" % (e["nombre"], e["indice"], e["motivo"]) for e in excluidos],
        "tablero": {
            "anios": anios,
            "anio_base": ANIO_BASE,
            "ejes": [{"id": e, "label": lab} for e, lab in EJES],
            "provincial": provincial,
            "departamental": departamental,
        },
    }


def _r(x):
    return None if x is None else round(x, 1)
