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

Línea de base: se lee de `base_valor` / `base_periodo` en el spec del KPI (`catalog.py`).
Mientras no estén definidas, las celdas quedan vacías.
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
    "energia-renovable": [
        {"label": "Generación eléctrica total", "metrica": "generacion_gwh", "fixed": {}},
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


def tabla(payloads, catalogo, ejes_pdes_meta, tags_meta, subeje_orden):
    """payloads: {tema_id: payload}; catalogo: temas livianos YA ORDENADOS;
    ejes_pdes_meta: catalog.EJES_PDES; tags_meta: catalog.TAGS;
    subeje_orden: catalog.SUBEJE_ORDEN. Devuelve [{id, label, filas: [...]}]."""
    orden_tag = {}
    for v in tags_meta.values():
        orden_tag[v["label"]] = v["orden"]
        if v.get("corto"):
            orden_tag[v["corto"]] = v["orden"]
    orden_tag.update(subeje_orden)
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
                var_cls = "flat" if abs(v) < 0.05 else ("up" if v > 0 else "down")
                flecha = "≈" if var_cls == "flat" else ("▲" if var_cls == "up" else "▼")
                var_txt = "%s %s %s" % (flecha, _pct(abs(v)), "p.p." if pp else "%")
                ref = "%s/%s" % (_periodo_corto(res["ultimo"]), _periodo_corto(res["prev"]))
            filas.append({
                "eje": t.get("eje_pdes"),
                "subeje": _subeje(s, t, tags_meta),
                "indicador": s.get("tabla_label") or s["label"],
                "nota": s.get("tabla_nota", ""),
                "tema_id": t["id"], "tema_title": t["title"],
                "frecuencia": _frecuencia(res, t["id"]),
                "ultimo": _periodo_corto(res["ultimo"]),
                "base_valor": s.get("base_valor", ""),
                "base_periodo": s.get("base_periodo", ""),
                "var_txt": var_txt, "var_cls": var_cls, "var_ref": ref,
            })

    grupos = []
    for eje_id, eje in sorted(ejes_pdes_meta.items(), key=lambda kv: kv[1]["orden"]):
        sub = [f for f in filas if f["eje"] == eje_id]
        if not sub:
            continue
        # Agrupadas por subeje: si no, la columna repite valores salteados y no se lee.
        sub.sort(key=lambda f: orden_tag.get(f["subeje"], 99))
        grupos.append({"id": eje_id, "label": eje["label"], "filas": sub})
    return grupos
