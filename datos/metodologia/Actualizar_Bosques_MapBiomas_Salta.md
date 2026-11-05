# Actualización — Bosque nativo, desmonte y regeneración (Salta), MapBiomas Argentina

Script reproducible en Python que arma la serie de **bosque nativo de Salta** y sus flujos
—**desmonte** y **regeneración**— a partir de **MapBiomas Argentina, Colección 3**
(<https://argentina.mapbiomas.org>). La metodología completa, con las verificaciones y los
resultados, está en
[`Metodologia_Bosques_MapBiomas_Salta.md`](Metodologia_Bosques_MapBiomas_Salta.md).

> **Dónde está el script.** A diferencia del resto de los datasets, acá el código no va
> embebido en este archivo: vive en `Indicadores/bosques/mapbiomas_bosques_salta.py`, fuera
> del repositorio del sitio, junto a su `cache/`. Necesita credenciales de Google Earth Engine
> y **no** es entrada de `build.py`: el build sólo lee los dos CSV ya generados que están en
> `datos/`.

> ## Leer esto antes de usar la salida
>
> - **Desmonte ≠ cambio de stock.** La planilla oficial de MapBiomas da solo superficie por
>   clase; la resta entre años es el cambio **neto**. El desmonte bruto sale del producto de
>   transiciones y por eso necesita Earth Engine.
> - **2022-2025 son provisorios.** El ráster aplica reglas de fin de serie a los últimos 4 años
>   y la colección siguiente los reescribe. En 2024 el bosque *sube* y en 2025 cae 139.000 ha.
>   Reportar como consolidado **hasta 2021**.
> - **No mezclar con Greenpeace ni con la UMSEF.** MapBiomas da niveles 2-3 veces más altos
>   (2022: 44.723 ha contra 15.230 de Greenpeace), muy probablemente por la definición de
>   bosque. Usar una sola fuente y leer tendencias.
> - **"Regeneración" no es "reforestación".** Es vegetación que vuelve sobre suelo que tuvo
>   uso antrópico; no distingue restauración activa de abandono.

## Qué genera

- **`MapBiomas_Cobertura_Salta_provincia_1985-2025.csv`** — tidy: `provincia, anio, clase,
  metrica, valor`. Superficie (ha) de las 18 clases de cobertura y uso, total provincial.
  Copia fiel de la planilla oficial; no requiere Earth Engine.
- **`MapBiomas_Bosques_Salta_departamento_1987-2025.csv`** — tidy: `departamento, anio,
  metrica, valor`. Por departamento (23) y año: `superficie_bosque_ha`, `desmonte_bosque_ha`
  (y su apertura en primario / secundario), `perdida_otra_vegetacion_natural_ha`,
  `regeneracion_bosque_ha`, `regeneracion_vegetacion_natural_ha`,
  `superficie_vegetacion_secundaria_ha`, `bosque_perdido_ha`, `bosque_ganado_ha`,
  `bosque_a_otra_vegetacion_natural_ha`, `superficie_total_ha`.
  Las definiciones exactas están en §2 de la metodología. **No trae fila de total
  provincial**: se obtiene sumando departamentos (una fila de total duplicaría todo al sumar).

## Evaluación de la fuente (contexto)

- MapBiomas publica planillas por provincia, pero **solo de stock**. La planilla de la
  Colección 2, que según la página incluye transiciones, devuelve HTTP 403.
- El producto *Desmonte y vegetación secundaria* está público en Earth Engine
  (`projects/mapbiomas-public/assets/argentina/lulc/collection3/`) y codifica, por año, la
  transición y la cobertura del año anterior. Con eso se separa el desmonte de bosque de la
  pérdida de pastizal o arbustal.
- Los límites departamentales son **FAO GAUL 2025** (23 departamentos). Su suma coincide con
  la superficie provincial de MapBiomas dentro del 0,07 %.

## Notas / caveats

- Cada corrida verifica: la leyenda contra la planilla (2025, por clase), el stock de bosque
  año por año contra la planilla (peor diferencia medida: −0,068 %), la superficie de cada
  departamento constante entre años, y el **balance** `bosque(t) − bosque(t−1) = ganado −
  perdido` (residuo medido: 0,0 ha). Si alguna falla, lo imprime como incidencia.
- La correspondencia código → clase de cobertura **no está documentada en el asset**: se
  dedujo de los datos y se valida en cada corrida. Si MapBiomas renumera clases, la
  verificación 1 lo detecta.
- Una reducción sincrónica sobre toda la provincia excede el tiempo de cómputo de Earth
  Engine; se hace por departamento, en la proyección nativa del ráster y en lotes de 5 años
  (con más, Earth Engine responde *Too many concurrent aggregations*). Son ~5 min en total.
- Los resultados crudos de Earth Engine se cachean por departamento en
  `bosques/cache/gee/`; una corrida interrumpida retoma donde quedó.
- La serie de transiciones arranca en **1987** (1985-1986 son calentamiento de las reglas
  del producto).
- Falta el cruce con las categorías del **OTBN** (roja / amarilla / verde): no se encontró una
  capa pública del ordenamiento de Salta.

> **Requisitos:** `pip install earthengine-api openpyxl`
> más una **cuenta de Google Earth Engine** con un proyecto Cloud registrado (uso no
> comercial: gratis). Solo la serie provincial (`--solo-oficial`) funciona sin Earth Engine.

## Cómo se corre

Una sola vez:

```bash
earthengine authenticate
```

Serie completa (provincial + departamental):

```bash
python bosques/mapbiomas_bosques_salta.py --proyecto TU-PROYECTO-GEE
```

Solo la serie provincial oficial, sin Earth Engine:

```bash
python bosques/mapbiomas_bosques_salta.py --solo-oficial
```

**Actualizar:** cuando MapBiomas publique una colección nueva (suele ser anual, en
septiembre), cambiar en el script `URL_OFICIAL`, `ASSET` y `ANIO_FIN`, **borrar
`bosques/cache/`** y volver a correr. Toda la serie se recalcula —las colecciones nuevas
reprocesan los años anteriores—, así que no se debe pegar el año nuevo sobre la serie vieja.

---

## Script completo

```python
# -*- coding: utf-8 -*-
"""
Bosque nativo, desmonte y regeneración en Salta — MapBiomas Argentina, Colección 3.

Genera dos series tidy:

  A. MapBiomas_Cobertura_Salta_provincia_1985-2025.csv
     Superficie por clase de cobertura y uso, total provincial, 1985-2025.
     Fuente: planilla oficial de estadísticas por provincia publicada por MapBiomas.
     No requiere Earth Engine.

  B. MapBiomas_Bosques_Salta_departamento_1987-2025.csv
     Por departamento y año: superficie de bosque, desmonte (pérdida bruta de
     bosque), pérdida de otra vegetación natural, regeneración y stock de
     vegetación secundaria.
     Fuente: rásteres públicos de MapBiomas en Google Earth Engine (cobertura +
     desmonte y vegetación secundaria), reducidos sobre los límites
     departamentales FAO GAUL 2025.

La planilla oficial solo trae STOCK por clase, y la diferencia de stock entre dos
años es el cambio NETO: 10.000 ha desmontadas y 4.000 ha que se regeneran se ven
como -6.000 ha. Por eso B se calcula desde el producto de transiciones, que
separa la pérdida bruta de la ganancia.

Uso:
    python bosques/mapbiomas_bosques_salta.py --proyecto ee-vogroppa
    python bosques/mapbiomas_bosques_salta.py --solo-oficial      # solo A, sin GEE

Formato de salida (convención del repo): decimal '.', sin separador de miles,
CSV con ',', UTF-8 con BOM.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.request
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CACHE = os.path.join(AQUI, "cache")

URL_OFICIAL = ("https://argentina.mapbiomas.org/wp-content/uploads/sites/8/2026/09/"
               "Estadisticas_por_Provincia.zip")
HOJA_HIST = "Salta Hist"
UA = {"User-Agent": "CESS-Salta-indicadores/1.0 (indicadores PDES 2030)"}

ASSET = "projects/mapbiomas-public/assets/argentina/lulc/collection3/mapbiomas_argentina_collection3_"
ASSET_COBERTURA = ASSET + "coverage_v1"
ASSET_TRANSICION = ASSET + "deforestation_secondary_vegetation_annual_v1"
LIMITES = "FAO/GAUL/2025/level2"

ANIO_INI_TRANSICION = 1987   # 1985-1986 son calentamiento de las reglas temporales
ANIO_FIN = 2025
LOTE_ANIOS = 5               # más de ~5 reducciones por petición -> "Too many concurrent aggregations"

# ---------------------------------------------------------------------------
# Leyenda de cobertura (MapBiomas Argentina, Colección 3)
# ---------------------------------------------------------------------------
# Verificada contra la planilla oficial: la suma departamental 2025 de cada
# código coincide con la clase homónima de la hoja "Salta Cob" dentro del 1 %
# (ver Metodologia_Bosques_MapBiomas_Salta.md). El script lo vuelve a
# comprobar en cada corrida.
LEYENDA = {
    3: "Bosques cerrados", 4: "Bosques abiertos", 6: "Bosques inundables",
    66: "Arbustales cerrados", 77: "Arbustales abiertos",
    63: "Mosaicos de arbustos y herbáceas", 12: "Herbáceas", 11: "Herbáceas inundables",
    73: "Turberas",
    19: "Cultivos temporarios", 36: "Cultivos perennes", 15: "Pasturas",
    9: "Silvicultura", 21: "Mosaico de usos",
    24: "Áreas urbanas", 25: "Otras áreas no vegetadas",
    34: "Hielo y nieve permanente", 33: "Ríos, lagunas, lagos y océano",
    27: "No observado",
}
BOSQUE = {3, 4, 6}
NATURAL_NO_BOSQUE = {11, 12, 34, 63, 66, 73, 77}

# Transiciones del producto de desmonte y vegetación secundaria.
T_SIN_DATO, T_ANTROPICO, T_PRIMARIA, T_SECUNDARIA = 0, 1, 2, 3
T_SUPRESION_PRIMARIA, T_RECUPERACION, T_SUPRESION_SECUNDARIA, T_OTRA = 4, 5, 6, 7

# Nombres de departamento: convención de los demás CSV del repo.
ALIAS_DEPTO = {
    "General José De San Martín": "General José de San Martín",
    "Rosario De La Frontera": "Rosario de la Frontera",
    "Rosario De Lerma": "Rosario de Lerma",
}


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def escribir_csv(ruta, campos, filas):
    with io.open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


# ===========================================================================
# A. Planilla oficial por provincia
# ===========================================================================
def descargar_oficial() -> bytes:
    """Devuelve el .xlsx de estadísticas por provincia (descarga una vez y cachea)."""
    destino = os.path.join(CACHE, "oficial")
    os.makedirs(destino, exist_ok=True)
    zp = os.path.join(destino, "Estadisticas_por_Provincia.zip")
    if not os.path.exists(zp):
        req = urllib.request.Request(URL_OFICIAL, headers=UA)
        with urllib.request.urlopen(req, timeout=120) as r:
            datos = r.read()
        with open(zp, "wb") as fh:
            fh.write(datos)
    with zipfile.ZipFile(zp) as z:
        nombres = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
        if len(nombres) != 1:
            sys.exit(f"Se esperaba un único .xlsx dentro del zip; hay {nombres}")
        return z.read(nombres[0])


def a_numero(x):
    """Valor de celda -> float. Las celdas de la planilla son numéricas nativas
    de Excel; si alguna llegara como texto se interpreta con la regla del
    último separador y se informa."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(" ", "").replace(" ", "")
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    print(f"     AVISO: celda numérica como texto: {x!r} -> {s}")
    return float(s)


def leer_oficial(xlsx: bytes):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True, data_only=True)
    if HOJA_HIST not in wb.sheetnames:
        sys.exit(f"No está la hoja {HOJA_HIST!r}. Hojas: {wb.sheetnames}")
    filas = list(wb[HOJA_HIST].iter_rows(values_only=True))
    cab = filas[0]
    anios = [(i, int(c)) for i, c in enumerate(cab) if isinstance(c, (int, float))]
    if anios[0][1] != 1985 or anios[-1][1] != ANIO_FIN:
        sys.exit(f"Rango de años inesperado en la planilla: {anios[0][1]}-{anios[-1][1]}")
    tidy = []
    for f in filas[1:]:
        if not f or not f[0]:
            continue
        clase = str(f[0]).strip()
        for i, anio in anios:
            v = a_numero(f[i])
            if v is not None:
                tidy.append({"provincia": "Salta", "anio": anio, "clase": clase,
                             "metrica": "superficie_ha", "valor": round(v, 2)})
    return tidy


# ===========================================================================
# B. Earth Engine por departamento
# ===========================================================================
def inicializar(proyecto):
    import ee
    try:
        ee.Initialize(project=proyecto)
    except Exception as exc:
        sys.exit(f"No se pudo inicializar Earth Engine con '{proyecto}': {exc}\n"
                 "Correr `earthengine authenticate` y verificar el proyecto Cloud.")
    return ee


def extraer_departamento(ee, depto_geom, proj, anios):
    """Para cada año, superficie (ha) agrupada por el código combinado
    transición*10000 + clase_anterior*100 + clase_actual."""
    area = ee.Image.pixelArea().divide(1e4)
    trans = ee.Image(ASSET_TRANSICION)
    cob = ee.Image(ASSET_COBERTURA)

    def reducir(anio):
        b = f"classification_{anio}"
        a = trans.select(b).toInt32()
        codigo = (a.divide(100).floor().multiply(10000)
                  .add(a.mod(100).multiply(100))
                  .add(cob.select(b).toInt32()))
        return area.addBands(codigo.rename("c")).reduceRegion(
            reducer=ee.Reducer.sum().group(groupField=1, groupName="c"),
            geometry=depto_geom, crs=proj["crs"], crsTransform=proj["transform"],
            maxPixels=int(1e11), tileScale=4).get("groups")

    salida = {}
    for i in range(0, len(anios), LOTE_ANIOS):
        lote = anios[i:i + LOTE_ANIOS]
        for intento in range(5):
            try:
                res = ee.List([reducir(y) for y in lote]).getInfo()
                break
            except ee.EEException as exc:
                if intento < 4 and ("concurrent" in str(exc) or "timed out" in str(exc)):
                    time.sleep(10 * (intento + 1))
                    continue
                raise
        for y, grupos in zip(lote, res):
            salida[str(y)] = {str(int(g["c"])): g["sum"] for g in grupos}
    return salida


def metricas(grupos: dict) -> dict:
    """Métricas de un departamento-año a partir de los grupos de código."""
    m = {k: 0.0 for k in (
        "superficie_bosque_ha", "desmonte_bosque_ha", "desmonte_bosque_primario_ha",
        "desmonte_bosque_secundario_ha", "perdida_otra_vegetacion_natural_ha",
        "regeneracion_bosque_ha", "regeneracion_vegetacion_natural_ha",
        "superficie_vegetacion_secundaria_ha", "superficie_total_ha",
        "bosque_perdido_ha", "bosque_ganado_ha",
        "bosque_a_otra_vegetacion_natural_ha")}
    for codigo, ha in grupos.items():
        c = int(codigo)
        t, ant, act = c // 10000, (c // 100) % 100, c % 100
        m["superficie_total_ha"] += ha
        if act in BOSQUE:
            m["superficie_bosque_ha"] += ha
        if t in (T_SUPRESION_PRIMARIA, T_SUPRESION_SECUNDARIA):
            if ant in BOSQUE:
                m["desmonte_bosque_ha"] += ha
                key = ("desmonte_bosque_primario_ha" if t == T_SUPRESION_PRIMARIA
                       else "desmonte_bosque_secundario_ha")
                m[key] += ha
            elif ant in NATURAL_NO_BOSQUE:
                m["perdida_otra_vegetacion_natural_ha"] += ha
        if t == T_RECUPERACION:
            m["regeneracion_vegetacion_natural_ha"] += ha
            if act in BOSQUE:
                m["regeneracion_bosque_ha"] += ha
        if t in (T_SECUNDARIA, T_RECUPERACION):
            m["superficie_vegetacion_secundaria_ha"] += ha
        # Flujos brutos de cobertura: cierran el balance del stock por construcción.
        # `ant` es 0 en el primer año de la serie o donde no hay dato el año previo.
        if ant and ant in BOSQUE and act not in BOSQUE:
            m["bosque_perdido_ha"] += ha
            if act in NATURAL_NO_BOSQUE:
                m["bosque_a_otra_vegetacion_natural_ha"] += ha
        if ant and ant not in BOSQUE and act in BOSQUE:
            m["bosque_ganado_ha"] += ha
    return m


def correr_gee(proyecto):
    ee = inicializar(proyecto)
    proj = ee.Image(ASSET_COBERTURA).projection().getInfo()
    deptos = ee.FeatureCollection(LIMITES).filter(ee.Filter.eq("GAUL1_NAME", "Salta"))
    nombres = sorted(deptos.aggregate_array("GAUL2_NAME").getInfo())
    if len(nombres) != 23:
        sys.exit(f"Se esperaban 23 departamentos de Salta en {LIMITES}; hay {len(nombres)}")
    anios = list(range(ANIO_INI_TRANSICION, ANIO_FIN + 1))
    cache = os.path.join(CACHE, "gee")
    os.makedirs(cache, exist_ok=True)

    datos = {}
    t0 = time.time()
    for i, n in enumerate(nombres, 1):
        ruta = os.path.join(cache, slug(n) + ".json")
        if os.path.exists(ruta):
            datos[n] = json.load(open(ruta, encoding="utf-8"))
            print(f"     {i:2d}/23 {n:30s} (cache)")
            continue
        geom = deptos.filter(ee.Filter.eq("GAUL2_NAME", n)).geometry()
        datos[n] = extraer_departamento(ee, geom, proj, anios)
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(datos[n], fh)
        print(f"     {i:2d}/23 {n:30s} ({time.time() - t0:.0f} s)")
    return datos


# ===========================================================================
# Verificaciones
# ===========================================================================
def verificar(oficial, datos):
    """Devuelve lista de incidencias (texto). Imprime el detalle."""
    inc = []

    # 1. Leyenda y límites: cobertura 2025 por clase, suma departamental vs oficial.
    of25 = {r["clase"]: r["valor"] for r in oficial if r["anio"] == ANIO_FIN}
    calc = {}
    for d in datos.values():
        for codigo, ha in d[str(ANIO_FIN)].items():
            act = int(codigo) % 100
            calc[act] = calc.get(act, 0.0) + ha
    print("\n  Verificación 1 — cobertura 2025: suma departamental vs planilla oficial")
    print(f"  {'clase':38s} {'oficial ha':>13s} {'GEE ha':>13s} {'dif %':>7s}")
    for cod, nombre in LEYENDA.items():
        o, c = of25.get(nombre), calc.get(cod, 0.0)
        if o is None:
            continue
        dif = 100 * (c - o) / o if o else 0.0
        marca = ""
        if o >= 10000 and abs(dif) > 1.0:
            marca = "  <-- INCIDENCIA"
            inc.append(f"Clase {nombre}: dif {dif:+.2f} % entre GEE y planilla (2025)")
        print(f"  {nombre[:38]:38s} {o:13.0f} {c:13.0f} {dif:7.2f}{marca}")

    # 2. Stock de bosque por año: departamental vs oficial.
    of_b = {}
    for r in oficial:
        if r["clase"].startswith("Bosques"):
            of_b[r["anio"]] = of_b.get(r["anio"], 0.0) + r["valor"]
    peor = (0.0, None)
    for y in range(ANIO_INI_TRANSICION, ANIO_FIN + 1):
        c = sum(metricas(d[str(y)])["superficie_bosque_ha"] for d in datos.values())
        dif = 100 * (c - of_b[y]) / of_b[y]
        if abs(dif) > abs(peor[0]):
            peor = (dif, y)
    print(f"\n  Verificación 2 — bosque total por año, peor diferencia: "
          f"{peor[0]:+.3f} % ({peor[1]})")
    if abs(peor[0]) > 1.0:
        inc.append(f"Bosque total difiere {peor[0]:+.2f} % de la planilla en {peor[1]}")

    # 3. Superficie de cada departamento constante entre años.
    for n, d in datos.items():
        tot = [sum(d[str(y)].values()) for y in range(ANIO_INI_TRANSICION, ANIO_FIN + 1)]
        rango = (max(tot) - min(tot)) / max(tot)
        if rango > 1e-4:
            inc.append(f"{n}: la superficie total varía {100*rango:.3f} % entre años")
    print(f"  Verificación 3 — superficie departamental constante entre años: "
          f"{'OK' if not any('varía' in x for x in inc) else 'FALLA'}")

    # 4. Balance del stock: bosque(t) - bosque(t-1) = ganado(t) - perdido(t).
    #    Comprueba que la "clase anterior" codificada en el producto de transiciones
    #    sea de verdad la cobertura del año previo. Si no cierra, las métricas de
    #    flujo no son confiables.
    peor = (0.0, None)
    for y in range(ANIO_INI_TRANSICION + 1, ANIO_FIN + 1):
        d = g = p = 0.0
        for dd in datos.values():
            m1, m0 = metricas(dd[str(y)]), metricas(dd[str(y - 1)])
            d += m1["superficie_bosque_ha"] - m0["superficie_bosque_ha"]
            g += m1["bosque_ganado_ha"]
            p += m1["bosque_perdido_ha"]
        res = d - (g - p)
        if abs(res) > abs(peor[0]):
            peor = (res, y)
    print(f"  Verificación 4 — balance stock = ganado - perdido, peor residuo: "
          f"{peor[0]:+.1f} ha ({peor[1]})")
    if abs(peor[0]) > 100:
        inc.append(f"El balance del stock de bosque no cierra: residuo {peor[0]:+.0f} ha en {peor[1]}")
    return inc


def saltos_de_magnitud(filas, metrica, umbral_ha=500):
    """Regla de la skill `datasets`: un valor > 100x o < 1/100 de la mediana de su
    serie, o un salto >= 3 órdenes de magnitud con su vecino, sobre valores
    suficientemente grandes como para que el log tenga sentido."""
    marcas = []
    series = {}
    for r in filas:
        if r["metrica"] == metrica:
            series.setdefault(r["departamento"], []).append((r["anio"], r["valor"]))
    for depto, serie in series.items():
        serie.sort()
        vals = [v for _, v in serie if v >= umbral_ha]
        if len(vals) < 5:
            continue
        med = sorted(vals)[len(vals) // 2]
        for (y, v) in serie:
            if v >= umbral_ha and (v / med > 100 or v / med < 0.01):
                marcas.append((depto, y, v, med))
        for (y0, v0), (y1, v1) in zip(serie, serie[1:]):
            if v0 >= umbral_ha and v1 >= umbral_ha and abs(math.log10(v1) - math.log10(v0)) >= 3:
                marcas.append((depto, y1, v1, v0))
    return marcas


# ===========================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proyecto", help="Proyecto Cloud de Earth Engine (requerido sin --solo-oficial)")
    ap.add_argument("--solo-oficial", action="store_true",
                    help="Solo la serie provincial de la planilla, sin Earth Engine")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, la raíz del repo)")
    args = ap.parse_args()
    if not args.solo_oficial and not args.proyecto:
        ap.error("--proyecto es obligatorio salvo con --solo-oficial")

    print("A. Planilla oficial MapBiomas por provincia ...")
    oficial = leer_oficial(descargar_oficial())
    ruta_a = os.path.join(args.salida, f"MapBiomas_Cobertura_Salta_provincia_1985-{ANIO_FIN}.csv")
    escribir_csv(ruta_a, ["provincia", "anio", "clase", "metrica", "valor"], oficial)
    print(f"   {len(oficial)} filas -> {ruta_a}")
    if args.solo_oficial:
        return

    print("\nB. Earth Engine, por departamento (~35 s cada uno; se cachea) ...")
    datos = correr_gee(args.proyecto)

    filas = []
    for n in sorted(datos):
        depto = ALIAS_DEPTO.get(n, n)
        for y in range(ANIO_INI_TRANSICION, ANIO_FIN + 1):
            for k, v in metricas(datos[n][str(y)]).items():
                filas.append({"departamento": depto, "anio": y, "metrica": k,
                              "valor": round(v, 2)})

    inc = verificar(oficial, datos)

    claves = [(r["departamento"], r["anio"], r["metrica"]) for r in filas]
    if len(claves) != len(set(claves)):
        inc.append("Hay filas duplicadas departamento-año-métrica")
    if any(r["valor"] < 0 for r in filas):
        inc.append("Hay valores negativos")
    for metrica in ("superficie_bosque_ha",):
        for depto, y, v, ref in saltos_de_magnitud(filas, metrica):
            inc.append(f"Salto de magnitud en {metrica}, {depto} {y}: {v:.0f} vs {ref:.0f}")

    ruta_b = os.path.join(args.salida,
                          f"MapBiomas_Bosques_Salta_departamento_{ANIO_INI_TRANSICION}-{ANIO_FIN}.csv")
    escribir_csv(ruta_b, ["departamento", "anio", "metrica", "valor"], filas)
    print(f"\n   {len(filas)} filas -> {ruta_b}")

    print("\nResumen provincial (suma de departamentos), ha:")
    print(f"  {'año':>4s} {'bosque':>12s} {'perdido':>9s} {'desmonte':>9s} {'a o.veg':>9s} "
          f"{'ganado':>9s} {'regen.':>8s}")
    for y in range(ANIO_INI_TRANSICION, ANIO_FIN + 1):
        s = {}
        for r in filas:
            if r["anio"] == y:
                s[r["metrica"]] = s.get(r["metrica"], 0.0) + r["valor"]
        print(f"  {y:4d} {s['superficie_bosque_ha']:12.0f} {s['bosque_perdido_ha']:9.0f} "
              f"{s['desmonte_bosque_ha']:9.0f} {s['bosque_a_otra_vegetacion_natural_ha']:9.0f} "
              f"{s['bosque_ganado_ha']:9.0f} {s['regeneracion_bosque_ha']:8.0f}")

    print("\nIncidencias:" if inc else "\nSin incidencias detectadas.")
    for x in inc:
        print("  -", x)


if __name__ == "__main__":
    main()
```
