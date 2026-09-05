# -*- coding: utf-8 -*-
"""indicadores.py — Tabla maestra de indicadores del Monitor, agrupada por eje del PDES.

Replica la lógica de `renderKpis` de `assets/js/charts.js` (agregación, recorte de la cola
de ceros, descarte de años finales incompletos, período homólogo del año anterior) para que
la tabla de la portada diga EXACTAMENTE lo mismo que las tarjetas KPI de cada tablero. Si esa
lógica cambia en el JS, hay que reflejarlo acá: la validación es abrir cada tablero y
comparar la variación y el período.

Además de los KPIs, incluye los indicadores que se publican en algún gráfico pero no tienen
tarjeta (ver `EXTRA`): el `fixed` de cada uno sale del gráfico que los muestra, que es el
filtro ya validado para obtener el agregado provincial.

Línea de base y metas: se leen de `base_valor` / `base_periodo` y `meta_2030` / `meta_2040` /
`meta_2050` en el spec del KPI (`catalog.py`). Mientras no estén definidas, las celdas quedan
vacías. Los valores deben cargarse como NÚMEROS, no como texto ya formateado: la tabla los
formatea (`_valor`) y necesita operar con ellos para la brecha.

Brecha a 2050 = `meta_2050` − último valor observado. Positiva, al indicador le falta subir
para alcanzar la meta; negativa, le falta bajar. Sólo se calcula cuando hay meta 2050 cargada
y un último dato numérico.
"""
import re

# Indicadores visibles en un gráfico pero sin tarjeta KPI.
EXTRA = {
    "vitivinicultura": [
        {"label": "Exportaciones de vino (volumen)", "metrica": "export_volumen",
         "fixed": {"categoria": "mercado_externo", "nivel": "provincia"}},
    ],
    "turismo": [
        {"label": "Pernoctaciones", "metrica": "pernoctaciones", "fixed": {"segmento": "Total"}},
        {"label": "Estadía media", "metrica": "estadia", "fixed": {"segmento": "Total"}},
    ],
    "agricultura": [
        {"label": "Rendimiento de soja", "metrica": "rendimiento_kgxha",
         "fixed": {"departamento": "Salta", "cultivo": "Soja"}},
    ],
    "financiero": [
        {"label": "Puntos de acceso al sistema financiero", "metrica": "pda_10m",
         "fixed": {"operacion": "PDA"}},
    ],
    "construccion": [
        {"label": "Participación en la superficie nacional",
         "metrica": "share_sup_pct", "fixed": {"municipio": "Total Salta"}},
    ],
    # "Generación eléctrica total" pasó a ser KPI del tablero de Energía eléctrica (antes era un
    # extra del tablero de renovables, que ahora sólo cubre lo renovable/hidráulico).
    "salud": [
        {"label": "Tasa de natalidad", "metrica": "tasa_natalidad",
         "fixed": {"departamento": "Salta", "desagregacion": "Total"}, "sentido": "neutro"},
        {"label": "Tasa de mortalidad general", "metrica": "tasa_mortalidad_general",
         "fixed": {"departamento": "Salta", "desagregacion": "Total"},
         "sentido": "menor_mejor"},
        {"label": "Tasa de mortalidad materna", "metrica": "tasa_mortalidad_materna",
         "fixed": {"departamento": "Salta", "desagregacion": "Total"},
         "sentido": "menor_mejor"},
        {"label": "Egresos hospitalarios", "metrica": "egresos",
         "fixed": {"departamento": "Salta", "desagregacion": "Total"}},
        {"label": "Camas disponibles", "metrica": "camas_disponibles",
         "fixed": {"departamento": "Salta", "desagregacion": "Total"}},
    ],
}


# ------------------------------------------------------------------ motor (espejo de charts.js)
def _agregar(rows, ix, metrica, fixed, x, agg):
    xi, mi, vi = ix[x], ix["metrica"], ix["valor"]
    pares = [(ix[d], fixed[d]) for d in fixed if d in ix and fixed[d] is not None]
    acc, cnt = {}, {}
    for r in rows:
        if r[mi] != metrica:
            continue
        if any(str(r[i]) != str(v) for i, v in pares):
            continue
        xv = r[xi]
        acc[xv] = acc.get(xv, 0) + (r[vi] or 0)
        cnt[xv] = cnt.get(xv, 0) + 1
    if agg == "mean":
        acc = {k: acc[k] / cnt[k] for k in acc}
    return acc


def _serie(payload, ix, spec, x, grano, agg):
    fx = dict(spec.get("fixed") or {})
    if grano is not None and "grano" in ix:
        fx["grano"] = grano          # el grano de la frecuencia PISA al del `fixed` (igual que el JS)
    acc = _agregar(payload["rows"], ix, spec["metrica"], fx, x, agg)
    claves = sorted(acc, key=int) if x == "anio" else sorted(acc, key=str)
    xs = [str(k) for k in claves]
    mapa = {str(k): acc[k] for k in acc}
    while xs and not mapa.get(xs[-1]):   # recorte de la cola de ceros
        xs.pop()
    return xs, mapa


def _periodo_previo(p):
    m = re.match(r"^(\d{4})(.*)$", str(p))
    return str(int(m.group(1)) - 1) + m.group(2) if m else None


def _driver_freq(payload):
    """Primer gráfico con control de frecuencia: fija la granularidad de los KPIs."""
    for ch in payload["charts"]:
        for c in ch.get("controls", []):
            if c.get("kind") == "freq":
                return {"value": c.get("default") or c["options"][0]["value"],
                        "map": {o["value"]: o for o in c["options"]}}
    return None


def _calcular(payload, ix, spec, freq):
    agg = spec.get("agg") or payload["metricas"].get(spec["metrica"], {}).get("agg", "sum")
    granos = ({r[ix["grano"]] for r in payload["rows"] if r[ix["metrica"]] == spec["metrica"]}
              if "grano" in ix else None)

    def grano_anual():
        if granos is None:
            return None
        return "anual" if "anual" in granos else (sorted(granos)[0] if granos else None)

    fopt = freq["map"][freq["value"]] if freq else None
    x, grano = "anio", grano_anual()
    if fopt and (granos is None or fopt["grano"] in granos):
        x, grano = fopt["x"], (None if granos is None else fopt["grano"])

    xs, mapa = _serie(payload, ix, spec, x, grano, agg)
    if not xs and x != "anio":
        x, grano = "anio", grano_anual()
        xs, mapa = _serie(payload, ix, spec, x, grano, agg)

    # En anual, descartar los años finales incompletos contra el grano más fino.
    if x == "anio" and freq:
        fino = None
        for o in freq["map"].values():
            if o["x"] in ("trimestre", "mes"):
                fino = o
        if fino and granos and fino["grano"] in granos:
            fxs, _ = _serie(payload, ix, spec, fino["x"], fino["grano"], agg)
            cnt = {}
            for p in fxs:
                cnt[str(p)[:4]] = cnt.get(str(p)[:4], 0) + 1
            if cnt:
                maxc = max(cnt.values())
                xs = [y for y in xs if cnt.get(str(y), 0) >= maxc]

    ult = xs[-1] if xs else None
    ahora = mapa.get(ult) if ult is not None else None
    prevk = _periodo_previo(ult) if ult is not None else None
    prev = mapa.get(prevk) if prevk is not None else None
    pct = (ahora / prev - 1) * 100 if (ahora is not None and prev not in (None, 0)) else None
    dif = (ahora - prev) if (ahora is not None and prev is not None) else None
    return {"x": x, "grano": grano, "ultimo": ult, "prev": prevk,
            "pct": pct, "dif": dif, "valor": ahora}


# ------------------------------------------------------------------ formato
_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
_FREC = {"mensual": "Mensual", "trimestral": "Trimestral", "anual": "Anual",
         "acumulado": "Mensual acumulado"}


def _periodo_corto(p):
    """2025 -> 2025 | 2025-T3 -> 3T2025 | 2026-03 -> mar-2026"""
    if p is None:
        return ""
    p = str(p)
    m = re.match(r"^(\d{4})-T(\d)$", p)
    if m:
        return "%sT%s" % (m.group(2), m.group(1))
    m = re.match(r"^(\d{4})-(\d{2})$", p)
    if m:
        return "%s-%s" % (_MESES[int(m.group(2)) - 1], m.group(1))
    return p


def _frecuencia(res, tema_id):
    if res["grano"]:
        return _FREC.get(res["grano"], res["grano"].capitalize())
    if res["x"] == "trimestre":
        return "Trimestral"
    if res["x"] in ("periodo", "mes"):
        return "Mensual"
    return "Anual (campaña)" if tema_id == "agricultura" else "Anual"


def _valor(v):
    """Formatea un valor de línea de base, meta o brecha para la tabla maestra.

    Los indicadores del Monitor van de tasas de 9,6 a matrículas de 380.000, así que la
    cantidad de decimales se elige por magnitud. Un valor cargado como texto se deja pasar.
    """
    if v is None or v == "":
        return ""
    if isinstance(v, str):
        return v
    signo = "+" if v > 0 else ("−" if v < 0 else "")
    a = abs(v)
    if a >= 1000:
        txt = "{:,.0f}".format(a).replace(",", ".")
    elif a >= 10:
        txt = "{:.1f}".format(a).replace(".", ",")
    else:
        txt = "{:.2f}".format(a).replace(".", ",")
    return signo, txt


def _medida(v, unidad):
    """Valor observado con su unidad, para la tarjeta de síntesis de la portada.

    Los indicadores van de tasas de 9,6 a matrículas de 380.000: los decimales se eligen
    por magnitud, igual que `_valor`. El % va pegado al número; el resto, separado.
    """
    if v is None:
        return ""
    a = abs(v)
    if a >= 1000:
        txt = "{:,.0f}".format(v).replace(",", ".")
    elif a >= 10:
        txt = "{:.1f}".format(v).replace(".", ",")
    else:
        txt = "{:.2f}".format(v).replace(".", ",")
    txt = txt.replace("-", "−")
    u = str(unidad or "")
    if u.startswith("%"):
        return txt + "%"
    return (txt + " " + u).strip()


def _grafico(payload, metrica):
    """Gráfico del tablero que publica esta métrica: destino del enlace de la tarjeta.

    Primero por la métrica base del gráfico; si no, por las opciones de sus controles
    (`kind: "metric"` las lista como strings; `kind: "mode"`, como `metric` de cada opción).
    Si ninguno la publica, la tarjeta enlaza a la cabecera del tablero.
    """
    for ch in payload["charts"]:
        if ch.get("metrica") == metrica:
            return ch["id"]
    for ch in payload["charts"]:
        for c in ch.get("controls", []):
            for o in c.get("options") or []:
                if (o.get("metric") if isinstance(o, dict) else o) == metrica:
                    return ch["id"]
    return None


def _celda(v):
    """Base y metas: conservan el signo negativo (un déficit puede ser la línea de base),
    pero no llevan '+' explícito."""
    r = _valor(v)
    if isinstance(r, str):
        return r
    signo, txt = r
    return (signo if signo == "−" else "") + txt


def _brecha(v):
    """Brecha: SÍ lleva signo, porque el sentido es la mitad de la información."""
    r = _valor(v)
    return r if isinstance(r, str) else (r[0] + r[1])


def _num(v):
    """Coerción a float de un valor cargado en catalog.py; None si no es numérico."""
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(".", "").replace(",", ".")) if isinstance(v, str) else float(v)
    except (TypeError, ValueError):
        return None


def _pct(v):
    return "{:.1f}".format(v).replace(".", ",")


def _en_pp(spec, metricas):
    """True si la variación de este indicador va en PUNTOS PORCENTUALES.

    Se aplica cuando el KPI declara `display: "nivel"` y la unidad es un porcentaje: son los
    cocientes (resultado fiscal en % del gasto primario), donde el % interanual de un
    porcentaje no significa nada. No se extiende al resto de las métricas en % (ocupación
    hotelera, participación renovable, share de construcción) porque sus tarjetas SÍ muestran
    variación relativa y la tabla no debe contradecir al tablero.
    """
    if spec.get("display") != "nivel":
        return False
    u = str(metricas.get(spec["metrica"], {}).get("unidad", ""))
    return u.startswith("%")


# ------------------------------------------------------------------ API
def _subeje(spec, tema, tags_meta):
    """Subeje del indicador: el propio, el del tema, o la etiqueta de su PRIMER tag.

    En el eje económico-productivo los subejes SON los ejes transversales (tags), así que el
    primer tag alcanza. Sociocultural y territorio-ambiente-turismo usan una taxonomía temática
    y declaran `subeje` en el tema (`catalog.py`).
    """
    if spec.get("subeje"):
        return spec["subeje"]
    if tema.get("subeje"):
        return tema["subeje"]
    for tg in tema.get("tags", []):
        if tg in tags_meta:
            # `corto` existe porque los labels de TAGS son largos (encabezados de la portada)
            # y en una columna partirían la fila en dos líneas.
            return tags_meta[tg].get("corto") or tags_meta[tg]["label"]
    return "—"


def _clase_color(spec, direccion):
    """Color de la variación según si SUBIR es una buena noticia (espejo de `kpiClaseColor`
    en assets/js/charts.js: si cambia una, hay que cambiar la otra).

    `sentido` en el spec del KPI (catalog.py): "mayor_mejor" (por defecto) | "menor_mejor" |
    "neutro". La flecha siempre marca la dirección real del cambio; esto sólo elige el color.
    """
    sentido = spec.get("sentido", "mayor_mejor")
    if sentido == "neutro":
        return direccion + " neutro"
    if sentido == "menor_mejor":
        return direccion + " invertido"
    return direccion


def _orden_subejes(tags_meta, subeje_orden):
    """Orden de aparición de los subejes: los tags por su `orden`, y encima `SUBEJE_ORDEN`
    para los ejes que declaran su propia taxonomía."""
    orden = {}
    for v in tags_meta.values():
        orden[v["label"]] = v["orden"]
        if v.get("corto"):
            orden[v["corto"]] = v["orden"]
    orden.update(subeje_orden)
    return orden


def tabla(payloads, catalogo, ejes_pdes_meta, tags_meta, subeje_orden, ciiu_secciones=None):
    """payloads: {tema_id: payload}; catalogo: temas livianos YA ORDENADOS;
    ejes_pdes_meta: catalog.EJES_PDES; tags_meta: catalog.TAGS;
    subeje_orden: catalog.SUBEJE_ORDEN; ciiu_secciones: catalog.CIIU_SECCIONES (letra→nombre).
    Devuelve [{id, label, filas, has_ciiu, subgrupos: [{label, filas}]}]."""
    ciiu_secciones = ciiu_secciones or {}
    orden_tag = _orden_subejes(tags_meta, subeje_orden)
    # CIIU representativa por tablero (para ordenar dentro del subeje); los sin letra van al final.
    ciiu_orden_tema = {t["id"]: (t.get("ciiu_orden") or "￿") for t in catalogo}
    filas = []
    for t in catalogo:
        payload = payloads[t["id"]]
        ix = {f: i for i, f in enumerate(payload["fields"])}
        freq = _driver_freq(payload)
        specs = list(payload["kpis"]) + EXTRA.get(t["id"], [])
        for s in specs:
            res = _calcular(payload, ix, s, freq)
            pp = _en_pp(s, payload["metricas"])
            v = res["dif"] if pp else res["pct"]
            if v is None:
                var_txt, var_cls = "sin base", "none"
                ref = ""
            else:
                direccion = "flat" if abs(v) < 0.05 else ("up" if v > 0 else "down")
                flecha = "≈" if direccion == "flat" else ("▲" if direccion == "up" else "▼")
                var_cls = _clase_color(s, direccion)
                var_txt = "%s %s %s" % (flecha, _pct(abs(v)), "p.p." if pp else "%")
                ref = "%s/%s" % (_periodo_corto(res["ultimo"]), _periodo_corto(res["prev"]))
            # Brecha a 2050: cuánto le falta al indicador para llegar a la meta final.
            # Queda vacía hasta que se carguen las metas en catalog.py.
            m2050, actual = _num(s.get("meta_2050")), _num(res.get("valor"))
            brecha = (m2050 - actual) if (m2050 is not None and actual is not None) else None

            # Letra CIIU: override por KPI, o la del tema; sólo se muestra en económico-productivo.
            ciiu = s.get("ciiu") or t.get("ciiu") or ""

            filas.append({
                "eje": t.get("eje_pdes"),
                "subeje": _subeje(s, t, tags_meta),
                "ciiu": ciiu, "ciiu_label": ciiu_secciones.get(ciiu, ""),
                "indicador": s.get("tabla_label") or s["label"],
                "nota": s.get("tabla_nota", ""),
                "tema_id": t["id"], "tema_title": t["title"],
                "chart_id": _grafico(payload, s["metrica"]),
                "valor_txt": _medida(res["valor"],
                                     payload["metricas"].get(s["metrica"], {}).get("unidad", "")),
                "frecuencia": _frecuencia(res, t["id"]),
                "ultimo": _periodo_corto(res["ultimo"]),
                "base_valor": _celda(s.get("base_valor")),
                "base_periodo": s.get("base_periodo", ""),
                "meta_2030": _celda(s.get("meta_2030")),
                "meta_2040": _celda(s.get("meta_2040")),
                "meta_2050": _celda(s.get("meta_2050")),
                "brecha_2050": _brecha(brecha),
                "var_txt": var_txt, "var_cls": var_cls, "var_ref": ref,
            })

    grupos = []
    for eje_id, eje in sorted(ejes_pdes_meta.items(), key=lambda kv: kv[1]["orden"]):
        sub = [f for f in filas if f["eje"] == eje_id]
        if not sub:
            continue
        # Ordenadas por subeje y, dentro de cada subeje, por la letra CIIU del tablero (los KPIs
        # de un mismo tablero quedan contiguos porque comparten CIIU y título; el orden estable
        # conserva el orden de los KPIs dentro del tablero).
        sub.sort(key=lambda f: (orden_tag.get(f["subeje"], 99),
                                ciiu_orden_tema.get(f["tema_id"], "￿"), f["tema_title"]))
        # El subeje pasa a ser SUBTÍTULO (fila de encabezado), no una columna: agrupamos las
        # filas consecutivas del mismo subeje conservando el orden ya fijado.
        subgrupos = []
        for f in sub:
            if not subgrupos or subgrupos[-1]["label"] != f["subeje"]:
                subgrupos.append({"label": f["subeje"], "filas": []})
            subgrupos[-1]["filas"].append(f)
        grupos.append({"id": eje_id, "label": eje["label"], "filas": sub,
                       "has_ciiu": eje_id == "economico-productivo", "subgrupos": subgrupos})
    return grupos


def explorar(grupos, tags_meta, subeje_orden):
    """Sección "Explorar por eje del PDES" de la portada: una tarjeta por INDICADOR.

    Toma la salida de `tabla()` y la reagrupa en eje → subeje, de modo que la síntesis del
    menú cuenta exactamente los mismos indicadores que la tabla maestra. No hay grupo
    residual: cada indicador tiene que caer en un subeje declarado (`subeje` en el tema o en
    el KPI, o el primer tag del tema), y si alguno queda sin subeje el build aborta.
    """
    orden = _orden_subejes(tags_meta, subeje_orden)
    huerfanos = ["%s (%s)" % (f["indicador"], f["tema_id"])
                 for g in grupos for f in g["filas"] if not f["subeje"] or f["subeje"] == "—"]
    if huerfanos:
        raise RuntimeError(
            "Indicadores sin subeje: %s. Hay que declarar `subeje` en el tema o en el KPI "
            "(catalog.py); la portada no arma grupos residuales." % ", ".join(huerfanos))
    out = []
    for g in grupos:
        porsub = {}
        for f in g["filas"]:
            porsub.setdefault(f["subeje"], []).append(f)
        subgrupos = [{"label": k, "indicadores": v} for k, v in
                     sorted(porsub.items(), key=lambda kv: (orden.get(kv[0], 99), kv[0]))]
        out.append({"id": g["id"], "label": g["label"],
                    "n": len(g["filas"]), "subgrupos": subgrupos})
    return out
