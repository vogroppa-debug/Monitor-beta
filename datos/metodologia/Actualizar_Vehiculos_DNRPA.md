# Actualización — Patentamiento, transferencias y parque automotor (DNRPA)

Regenera la serie mensual de vehículos 0 km inscriptos y usados transferidos para las 24
jurisdicciones, más el parque automotor, a partir de la Dirección Nacional de los Registros
Nacionales de la Propiedad del Automotor:

- <https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-automotores> (autos, desde 2000)
- <https://datos.gob.ar/dataset/estadistica-de-tramites-de-motovehiculos> (motos, desde 2007)
- <https://datos.jus.gob.ar/dataset/estadistica-de-tramites-de-maquinarias> (maquinarias, desde 2013)
- <https://www.dnrpa.gov.ar/portal_dnrpa/boletines_estadisticos2.php> (parque activo, desde 2010)

> **Los nombres de archivo de los seis CSV llevan el rango de meses y cambian todos los meses.**
> `…-automotores-2000-01-2026-10.csv` pasa a `…-2026-11.csv` en la actualización siguiente. Hay
> que corregirlos en el diccionario `FUENTES` del script; es lo único que requiere mantenimiento.
> Si una URL caduca, el script lo dice con una incidencia «no se pudo bajar» en vez de emitir una
> serie corta en silencio.

> **El parque activo no es un dato abierto**: es una página HTML por año. Responde a un GET limpio
> sin sesión, pero el formulario POST de inscripciones de la misma sección sí la exige. Por eso el
> parque se baja con `urllib` y las inscripciones se toman de los CSV, no de la web.

> **El parque es SÓLO AUTOMOTOR: no incluye motos.** Para Salta en diciembre de 2024 da 358.452,
> contra un parque total de 654.998 que publica la ANSV para 2022. Sirve para tasas referidas a
> autos y no para reproducir las tasas por vehículo de la ANSV.

> **No se usa el archivo del portal de datos abiertos de Salta**, que copia estas mismas series y
> está mal: todo 2018 permutado en las seis series, y autos corrido un año. Correr con
> `--contra-salta` reproduce el cotejo. El detalle está en `Metodologia_Vehiculos_DNRPA.md`.

> **`Ciudad Autónoma de Bs.As.` se emite como `CABA`.**

## Qué genera (en `datos-drive/`)

| Archivo | Base de origen | Período | Dimensiones propias |
|---|---|---|---|
| `Vehiculos_DNRPA_patentamiento_jurisdiccion_mensual.csv` | 6 CSV agregados de datos.jus.gob.ar | 2000-01 → 2026-10 | `jurisdiccion` (25), `categoria` (4), `metrica` (2) |
| `Vehiculos_DNRPA_parque_automotor_jurisdiccion_mensual.csv` | 17 páginas de `tram_parque.php` | 2010-01 → 2026-10 | `jurisdiccion` (25) |

Los dos cierran en `metrica, valor`, el esquema canónico del Monitor.

```
anio,n_mes,mes,periodo,jurisdiccion,categoria,metrica,valor
2025,9,2025-09-01,2025-09,Salta,Motos,inscripciones_iniciales,2446
2025,9,2025-09-01,2025-09,Salta,Autos,inscripciones_iniciales,1226
```

`categoria` es un **margen**: `Total` es la suma de las otras tres, no una categoría más. Todo
gráfico tiene que fijarla o va a duplicar el total.

## 1. Requisitos

```
(ninguno)
```

Sólo biblioteca estándar: `urllib` para bajar, `csv` para los seis agregados y `html.parser` para
las páginas de parque. No hace falta `pandas`.

## 2. Correr el script

```
python actualizar_vehiculos_dnrpa.py
```

| Argumento | Para qué |
|---|---|
| `--salida DIR` | Carpeta de salida. Por defecto, `datos-drive/` |
| `--fuentes DIR` | Caché de los archivos originales. Por defecto, `datos-drive/fuentes/dnrpa_vehiculos/` |
| `--refrescar` | Vuelve a bajar todo, incluso lo cacheado |
| `--contra-salta` | Coteja las seis series de Salta contra el archivo del portal provincial |

Para traer un mes nuevo hay que correr con `--refrescar` **después** de actualizar los nombres de
archivo en `FUENTES`: la caché es permanente y, si no, devuelve lo viejo.

## 3. Verificar antes de dar por buena la actualización

**A. Los seis agregados.** Cada serie imprime su cantidad de meses y su rango. Autos tiene que
arrancar en 2000-01, motos en 2007-01 y maquinarias en 2013-09; los tres terminan en el mismo mes.
Si una termina antes que las otras, esa URL quedó vieja.

**B. El parque.** Tiene que leer 24 jurisdicciones por año. La línea `meses sin publicar
descartados` dice cuáles se tiraron por venir en cero; en el año en curso eso es normal, en un año
cerrado no.

**C. Verificaciones.**

- **`suma de jurisdicciones vs. total publicado`**: hoy, desvío **0** en los 202 meses. El total
  que publica la DNRPA es exactamente la suma de sus provincias; cualquier desvío es un error de
  lectura de la tabla.
- **`caida mensual maxima del parque`**: hoy 3,48 %, con 3 casos por encima del 2 % (CABA en
  2012-11 y 2016-03, Tierra del Fuego en 2016-03), que son depuraciones registrales. Un stock que
  se derrumba de un mes al otro es una baja masiva o un error de lectura, y hay que mirarlo.
- **Saltos de magnitud**: hoy, ninguno. El control ignora los pares con valores menores a 30 y
  exige una razón mayor en el paso de diciembre a enero, porque ahí hay estacionalidad estructural
  —el patentamiento se desploma en diciembre y se dispara en enero, ya que inscribir en enero da el
  año modelo nuevo—.

**E. Salida.** `categoria Total omitida en N meses sin las tres categorías` tiene que decir «hasta
2013-08». Si dijera una fecha posterior, alguna categoría dejó de bajarse.

**Incidencias.** Hoy son **cuatro**: las 12 celdas de La Rioja en transferencias de maquinarias de
2014 que la fuente no trae, y las tres caídas del parque. Las cuatro están explicadas en la
metodología; una quinta hay que investigarla antes de publicar.

**Valores de control.** Salta: 24.227 autos 0 km en 2017 (el año récord), 21.380 en 2018, 10.952 en
2019, 13.911 en 2025; 25.103 motos en 2025; 208 maquinarias en 2025; 22.218 transferencias de autos
en 2025. Parque automotor de Salta: 158.954 en diciembre de 2010, 313.471 en 2019 y 358.452 en
2024. Parque del país en diciembre de 2024: 18.064.236.

**Cotejo con el archivo provincial** (`--contra-salta`). Tiene que reportar exactamente esto, y
nada más:

```
Autos        inscripciones_iniciales  2017 (12 meses, total 21380 vs 24227); 2018 (12 meses, total 10952 vs 21380); 2026 (2 meses)
Autos        transferencias           2018 (8 meses)
Motos        inscripciones_iniciales  2018 (8 meses); 2023 (1 meses, total 19313 vs 19312); 2026 (2 meses)
Motos        transferencias           2018 (8 meses); 2024 (1 meses, total 3846 vs 3845)
Maquinarias  inscripciones_iniciales  2018 (8 meses)
Maquinarias  transferencias           2018 (7 meses)
```

Las diferencias de 2026 son sólo el corte del archivo provincial, que llega a febrero.

## 4. Copiar al sitio

El adapter del Monitor lee de `sitio-indicadores/datos/`, no de `datos-drive/`:

```powershell
copy datos-drive\Vehiculos_DNRPA_*.csv sitio-indicadores\datos\
```

Después, `python build.py` en `sitio-indicadores/`. Los dos CSV los usan dos temas: `patentamiento`
lee los dos, y `seguridad-vial` lee el del parque para su tasa de fatalidad cada 10 mil
automotores.

## Script completo

`actualizar_vehiculos_dnrpa.py`, md5 `0990f5c5f28e98eb259b8ffb59e433c6`.

```python
# -*- coding: utf-8 -*-
"""
Patentamiento, transferencias y parque automotor por jurisdiccion (DNRPA) -- base mensual.

Genera dos CSV a partir de los datos de la Direccion Nacional de los Registros Nacionales de la
Propiedad del Automotor:

    Vehiculos_DNRPA_patentamiento_jurisdiccion_mensual.csv
    Vehiculos_DNRPA_parque_automotor_jurisdiccion_mensual.csv

DOS ORIGENES DISTINTOS
    1. SEIS CSV AGREGADOS por anio, mes y provincia, en el portal de datos abiertos de Justicia
       (datos.jus.gob.ar), licencia CC-BY 4.0, actualizacion mensual. Son chicos y estan limpios.
       Tres categorias (automotores, motovehiculos, maquinarias) por dos operaciones (inscripciones
       iniciales y transferencias). Cada categoria arranca en un anio distinto, que es cuando la
       DNRPA empezo a publicarla.

    2. PARQUE ACTIVO, una pagina HTML por anio en dnrpa.gov.ar. Es la unica forma de obtenerlo: no
       existe como dato abierto. Responde a un GET limpio, sin sesion -- el formulario POST de
       inscripciones de la misma seccion si exige sesion, pero el parque no.

EL PARQUE ES SOLO AUTOMOTOR
    La pagina no tiene selector de tipo: trae una sola tabla y se rotula "Tipo de Vehiculo:
    Automotor". NO incluye motovehiculos. Para Salta en diciembre de 2024 da 358.452, mientras que
    el parque TOTAL que publica la ANSV para 2022 son 654.998, de los cuales 331.144 son
    automotores y 313.060 motovehiculos. Por eso este parque sirve para tasas referidas a autos
    (renovacion de la flota) y NO para reproducir las tasas por vehiculo de la ANSV.

POR QUE NO SE USA EL ARCHIVO DE LA PROVINCIA
    El portal de datos abiertos de Salta publica
    `06_patentamiento_transferencias_vehiculos_salta_2014_2026.csv`, que copia estas mismas series.
    Esta mal: todo 2018 tiene los meses permutados en las seis series, y en autos ademas esta
    corrido un anio (la columna "2017" es el 2018 real, la "2018" es el 2019 real ORDENADO de mayor
    a menor, y el 2017 real -- 24.227 autos, el anio record -- no figura). Correr este script con
    `--contra-salta` reproduce ese cotejo celda por celda.

UNIDAD
    Cantidad de tramites (inscripciones iniciales o transferencias) en el mes, y cantidad de
    vehiculos en condiciones registrales de circular a fin de cada mes para el parque.

Formato de salida (convencion del repo): decimal '.', sin separador de miles, CSV con ',',
UTF-8 con BOM.

Correr:  python actualizar_vehiculos_dnrpa.py [--salida DIR] [--fuentes DIR] [--refrescar]
                                              [--contra-salta]
"""

import argparse
import collections
import csv
import datetime
import io
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "CESS-Salta-indicadores/1.0 (indicadores PDES 2030)"}

SALIDA_PAT = "Vehiculos_DNRPA_patentamiento_jurisdiccion_mensual.csv"
SALIDA_PAR = "Vehiculos_DNRPA_parque_automotor_jurisdiccion_mensual.csv"
CAMPOS_PAT = ["anio", "n_mes", "mes", "periodo", "jurisdiccion", "categoria", "metrica", "valor"]
CAMPOS_PAR = ["anio", "n_mes", "mes", "periodo", "jurisdiccion", "metrica", "valor"]

JUS = "https://datos.jus.gob.ar/dataset/%s/resource/%s/download/%s"

# (categoria, metrica) -> (dataset_id, resource_id, archivo). El nombre del archivo lleva el rango
# de meses, asi que CAMBIA en cada actualizacion mensual de la fuente: ver el runbook.
FUENTES = {
    ("Autos", "inscripciones_iniciales"): (
        "1ab0cc03-ab9b-4520-975c-5757d87d1061", "4358c995-bb04-4ad9-be4a-a9076dc3e42c",
        "estadistica-inscripciones-iniciales-automotores-2000-01-2026-10.csv"),
    ("Autos", "transferencias"): (
        "1ab0cc03-ab9b-4520-975c-5757d87d1061", "7912aa2b-7e9a-49dd-8c14-0570ca043d27",
        "estadistica-transferencias-automotores-2000-01-2026-10.csv"),
    ("Motos", "inscripciones_iniciales"): (
        "72d85f23-b751-4d12-935b-25e32ed9445e", "d523dd08-5c12-467e-b947-aa3206a24d21",
        "estadistica-inscripciones-iniciales-motovehiculos-2007-01-2026-10.csv"),
    ("Motos", "transferencias"): (
        "72d85f23-b751-4d12-935b-25e32ed9445e", "6422d3c8-fa7d-47b4-96e9-4b2f2fab1e90",
        "estadistica-transferencias-motovehiculos-2007-01-2026-10.csv"),
    ("Maquinarias", "inscripciones_iniciales"): (
        "852b58b1-98b5-4f80-9f80-62e09cf3cfbb", "c8ca86f7-beb5-4a40-bc26-3a411d87de5e",
        "estadistica-inscripciones-iniciales-maquinarias-2013-09-2026-10.csv"),
    ("Maquinarias", "transferencias"): (
        "852b58b1-98b5-4f80-9f80-62e09cf3cfbb", "9bb1bec9-c309-45d5-ac8b-dafb086c6298",
        "estadistica-transferencias-maquinarias-2013-09-2026-10.csv"),
}
CATEGORIAS = ["Autos", "Motos", "Maquinarias"]
TOTAL_CAT = "Total"
METRICAS_PAT = ["inscripciones_iniciales", "transferencias"]

PARQUE_URL = ("https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/"
              "tram_parque.php?anio=%d&origen=portal_dnrpa")
PARQUE_DESDE = 2010

SALTA_CSV = ("https://datospublicos.salta.gob.ar/dataset/857b8020-ee8f-40d2-865f-e3c5eeeae20a/"
             "resource/7221534c-dcd5-42a7-b09b-6e535aa319c0/download/"
             "06_patentamiento_transferencias_vehiculos_salta_2014_2026.csv")

# Las dos fuentes escriben las jurisdicciones distinto: los CSV en mayusculas y minusculas con
# acentos, las paginas de parque en mayusculas sin acentos y con abreviaturas. Se normalizan con
# este diccionario y nada mas: una etiqueta que no este aca aborta la corrida, para que un cambio
# de la fuente no pase callado. "Ciudad Autonoma de Bs.As." sale como CABA.
JURISDICCIONES = {
    "Buenos Aires": "Buenos Aires",            "BUENOS AIRES": "Buenos Aires",
    "Ciudad Autónoma de Bs.As.": "CABA",       "CABA": "CABA",
    "Catamarca": "Catamarca",                  "CATAMARCA": "Catamarca",
    "Chaco": "Chaco",                          "CHACO": "Chaco",
    "Chubut": "Chubut",                        "CHUBUT": "Chubut",
    "Córdoba": "Córdoba",                      "CORDOBA": "Córdoba",
    "Corrientes": "Corrientes",                "CORRIENTES": "Corrientes",
    "Entre Ríos": "Entre Ríos",                "ENTRE RIOS": "Entre Ríos",
    "Formosa": "Formosa",                      "FORMOSA": "Formosa",
    "Jujuy": "Jujuy",                          "JUJUY": "Jujuy",
    "La Pampa": "La Pampa",                    "LA PAMPA": "La Pampa",
    "La Rioja": "La Rioja",                    "LA RIOJA": "La Rioja",
    "Mendoza": "Mendoza",                      "MENDOZA": "Mendoza",
    "Misiones": "Misiones",                    "MISIONES": "Misiones",
    "Neuquén": "Neuquén",                      "NEUQUEN": "Neuquén",
    "Río Negro": "Río Negro",                  "RIO NEGRO": "Río Negro",
    "Salta": "Salta",                          "SALTA": "Salta",
    "San Juan": "San Juan",                    "SAN JUAN": "San Juan",
    "San Luis": "San Luis",                    "SAN LUIS": "San Luis",
    "Santa Cruz": "Santa Cruz",                "SANTA CRUZ": "Santa Cruz",
    "Santa Fe": "Santa Fe",                    "SANTA FE": "Santa Fe",
    "Santiago del Estero": "Santiago del Estero", "S. DEL ESTERO": "Santiago del Estero",
    "Tierra del Fuego": "Tierra del Fuego",    "T. DEL FUEGO": "Tierra del Fuego",
    "Tucumán": "Tucumán",                      "TUCUMAN": "Tucumán",
}
PROVINCIAS = sorted(set(JURISDICCIONES.values()))
TOTAL_PAIS = "Total del país"

incidencias = []


def inc(msg):
    incidencias.append(msg)


# --------------------------------------------------------------------------- descarga y escritura

def bajar(url, destino, nombre, refrescar=False):
    """Bytes del recurso, con cache permanente en `destino`."""
    os.makedirs(destino, exist_ok=True)
    ruta = os.path.join(destino, nombre)
    if os.path.exists(ruta) and not refrescar:
        with open(ruta, "rb") as f:
            return f.read()
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            datos = r.read()
    except Exception as e:
        inc("no se pudo bajar %s (%s): %s" % (nombre, url, e))
        return None
    with open(ruta, "wb") as f:
        f.write(datos)
    return datos


def escribir_csv(ruta, campos, filas):
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print("   %s  (%d filas)" % (ruta, len(filas)))


def jur(etiqueta):
    """Nombre canonico de la jurisdiccion, o None si la etiqueta no es una."""
    return JURISDICCIONES.get(" ".join(etiqueta.split()))


# ------------------------------------------------------------------- 1. los seis CSV agregados

def leer_csv_dnrpa(datos, categoria, metrica):
    """{(anio, mes, jurisdiccion): cantidad} de uno de los seis agregados."""
    filas = list(csv.DictReader(io.StringIO(datos.decode("utf-8-sig"))))
    if not filas:
        inc("%s / %s: el CSV vino vacio" % (categoria, metrica))
        return {}
    cols = list(filas[0])

    def col(pref):
        c = [x for x in cols if x.startswith(pref) and x != "provincia_id"]
        return c[0] if c else None

    ca, cm, cp, cq = col("anio"), col("mes"), col("provincia"), col("cantidad")
    if not all((ca, cm, cp, cq)):
        inc("%s / %s: el CSV cambio de columnas (%s)" % (categoria, metrica, cols))
        return {}
    out, desconocidas = {}, set()
    for r in filas:
        j = jur(r[cp])
        if j is None:
            desconocidas.add(r[cp])
            continue
        out[(int(r[ca]), int(r[cm]), j)] = int(r[cq])
    if desconocidas:
        inc("%s / %s: jurisdicciones desconocidas %s"
            % (categoria, metrica, sorted(desconocidas)))
    return out


# --------------------------------------------------------------------- 2. el parque, pagina a pagina

def completar_cero(d, etiqueta):
    """Completa con cero las jurisdicciones ausentes dentro del rango de la serie.

    Los agregados de la DNRPA emiten ceros explicitos (570 en transferencias de maquinarias), asi
    que una fila ausente no es la forma normal de escribir un cero. Igual se completa, porque el
    unico caso que aparece es una jurisdiccion entera durante un anio entero -- La Rioja en 2014,
    en transferencias de maquinarias, donde la fuente no reporto nada -- y dejar el hueco haria que
    la categoria Total de esos meses se calcule sobre 23 jurisdicciones en vez de 24.
    """
    periodos = sorted({(a, m) for (a, m, _) in d})
    if not periodos:
        return d
    faltan = [(a, m, j) for (a, m) in periodos for j in PROVINCIAS if (a, m, j) not in d]
    for k in faltan:
        d[k] = 0
    if faltan:
        det = collections.Counter(j for (_, _, j) in faltan)
        inc("%s: la fuente no trae %d celdas (%s); se completan con cero"
            % (etiqueta, len(faltan), ", ".join("%s x%d" % (j, n) for j, n in det.most_common(3))))
    return d


class TablaParque(HTMLParser):
    """Lee la tabla del parque activo: una fila por jurisdiccion con doce celdas de numeros.

    El markup es <tr><td><b>PROVINCIA</b></td><td align=right>N</td> x12 </tr>, asi que alcanza
    con acumular el texto de cada celda y cerrar la fila en </tr>. La fila del total del pais pone
    su etiqueta en un <th> en vez de un <td>, por eso se leen los dos.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.filas = []
        self._fila, self._celda, self._en_celda = None, [], False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._fila = []
        elif tag in ("td", "th") and self._fila is not None:
            self._celda, self._en_celda = [], True

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._en_celda:
            self._fila.append(" ".join("".join(self._celda).split()))
            self._en_celda = False
        elif tag == "tr" and self._fila is not None:
            if len(self._fila) == 13:
                self.filas.append(self._fila)
            self._fila = None

    def handle_data(self, d):
        if self._en_celda:
            self._celda.append(d)


RE_MILES = re.compile(r"^\d{1,3}(?:\.\d{3})*$")


def leer_parque(datos, anio):
    """({(anio, mes, jurisdiccion): cantidad}, {mes: total_pais_publicado})."""
    p = TablaParque()
    p.feed(datos.decode("utf-8", "replace"))
    out, totales, desconocidas = {}, {}, set()
    for fila in p.filas:
        etq, vals = fila[0], fila[1:]
        j = jur(etq)
        es_total = etq.strip().upper().startswith("TOTAL")
        if j is None and not es_total:
            if any(RE_MILES.match(v) for v in vals):
                desconocidas.add(etq)
            continue
        for m, v in enumerate(vals, 1):
            if not RE_MILES.match(v):
                continue
            n = int(v.replace(".", ""))
            if es_total:
                totales[m] = n
            else:
                out[(anio, m, j)] = n
    if desconocidas:
        inc("parque %d: etiquetas desconocidas con numeros al lado: %s" % (anio, sorted(desconocidas)))
    return out, totales


# ------------------------------------------------------------------------------- verificaciones

def verif_continuidad(datos, etiqueta, nj=len(PROVINCIAS)):
    """Ningun mes faltante dentro del rango, y las 24 jurisdicciones en todos."""
    periodos = sorted({(a, m) for (a, m, _) in datos})
    if not periodos:
        return
    esperados = []
    y, m = periodos[0]
    while (y, m) <= periodos[-1]:
        esperados.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    faltan = [p for p in esperados if p not in periodos]
    if faltan:
        inc("%s: faltan %d meses en la serie (ej. %s)"
            % (etiqueta, len(faltan), ", ".join("%d-%02d" % p for p in faltan[:4])))
    incompletos = [p for p in periodos
                   if len({j for (a, mm, j) in datos if (a, mm) == p}) != nj]
    if incompletos:
        inc("%s: %d meses no traen las %d jurisdicciones (ej. %s)"
            % (etiqueta, len(incompletos), nj,
               ", ".join("%d-%02d" % p for p in incompletos[:4])))
    print("   %-34s %3d meses, de %d-%02d a %d-%02d" %
          (etiqueta, len(periodos), periodos[0][0], periodos[0][1],
           periodos[-1][0], periodos[-1][1]))


def verif_suma_parque(parque, totales):
    """El total del pais publicado contra la suma de las 24 jurisdicciones."""
    peor, n = 0, 0
    for (a, m), tot in sorted(totales.items()):
        s = sum(v for (y, mm, _), v in parque.items() if (y, mm) == (a, m))
        if not s:
            continue
        d = abs(s - tot)
        peor = max(peor, d)
        n += (d > 0)
    print("   suma de jurisdicciones vs. total publicado: desvio maximo %d, %d meses con desvio"
          % (peor, n))
    if peor > 0:
        inc("el parque publicado como total del pais no coincide con la suma de las "
            "jurisdicciones: desvio maximo %d" % peor)


def verif_parque_monotono(parque):
    """Un stock no se derrumba de un mes al otro. Una caida fuerte es una baja masiva de la fuente
    o un error de lectura, y en los dos casos hay que mirarla."""
    peor, n = 0.0, 0
    for j in PROVINCIAS:
        serie = sorted((a, m, v) for (a, m, jj), v in parque.items() if jj == j)
        for (a0, m0, v0), (a1, m1, v1) in zip(serie, serie[1:]):
            if not v0:
                continue
            caida = (v0 - v1) / v0 * 100
            if caida > 2.0:
                n += 1
                inc("parque de %s: cae %.1f%% entre %d-%02d y %d-%02d (%d -> %d)"
                    % (j, caida, a0, m0, a1, m1, v0, v1))
            peor = max(peor, caida)
    print("   caida mensual maxima del parque: %.2f%%, %d casos por encima del 2%%" % (peor, n))


def saltos_de_magnitud(pares, etiqueta):
    """Un salto de orden de magnitud entre meses consecutivos es la firma de un separador mal
    leido. Se reporta, no se corrige.

    Dos excepciones, las dos medidas sobre esta serie y no inventadas:

    - Se ignoran los pares en que alguno de los dos valores es menor a 30. En maquinarias un mes
      pasa de 14 a 1 sin que nada raro ocurra: con conteos de un digito la razon no significa nada.
    - El paso de diciembre a enero exige una razon mayor, porque ahi hay un patron estructural y
      nacional: el patentamiento se desploma en diciembre y se dispara en enero, ya que inscribir
      en enero da el anio modelo nuevo y eso vale en la reventa. En el total del pais, enero suele
      ser tres o cuatro veces diciembre, y en una provincia chica la razon llega a once.
    """
    ser = [(p, v) for p, v in sorted(pares) if v]
    for (p0, v0), (p1, v1) in zip(ser, ser[1:]):
        if min(v0, v1) < 30:
            continue
        umbral = 15.0 if p0.endswith("-12") and p1.endswith("-01") else 9.5
        if max(v0, v1) / min(v0, v1) >= umbral:
            inc("salto de orden de magnitud en %s: %s=%g -> %s=%g" % (etiqueta, p0, v0, p1, v1))


def cotejo_contra_salta(pat, destino, refrescar=False):
    """Compara las seis series de Salta contra el archivo del portal provincial.

    No alimenta el dataset: documenta por que no se lo usa como fuente.
    """
    datos = bajar(SALTA_CSV, destino, "06_patentamiento_salta_2014_2026.csv", refrescar)
    if datos is None:
        print("   no se pudo bajar el archivo provincial; se omite el cotejo")
        return
    OPER = {"Inscripciones iniciales": "inscripciones_iniciales",
            "Transferencias": "transferencias"}
    prov = {}
    for r in csv.DictReader(io.StringIO(datos.decode("utf-8-sig"))):
        met = OPER.get(r["tipo_operacion"])
        if met:
            prov[(int(r["anio"]), int(r["mes"]), r["categoria_vehiculo"], met)] = int(r["cantidad"])
    anios = sorted({a for (a, _, _, _) in prov})
    print("   archivo provincial: %d filas, %d-%d" % (len(prov), anios[0], anios[-1]))
    print("   %-12s %-24s %s" % ("categoria", "metrica", "anios con diferencias"))
    for cat in CATEGORIAS:
        for met in METRICAS_PAT:
            det = []
            for a in anios:
                meses = [m for m in range(1, 13) if (a, m, cat, met) in prov]
                dif = [m for m in meses if prov[(a, m, cat, met)] != pat.get((a, m, "Salta", cat, met))]
                if dif:
                    sp = sum(prov[(a, m, cat, met)] for m in meses)
                    sd = sum(pat.get((a, m, "Salta", cat, met), 0) for m in meses)
                    det.append("%d (%d meses%s)" % (a, len(dif),
                                                    "" if sp == sd else ", total %d vs %d" % (sp, sd)))
            print("   %-12s %-24s %s" % (cat, met, "; ".join(det) or "coincide en todo"))


# ------------------------------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(
        description="Patentamiento, transferencias y parque automotor por jurisdiccion (DNRPA)")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "dnrpa_vehiculos"),
                    help="Cache de los archivos originales")
    ap.add_argument("--refrescar", action="store_true",
                    help="Vuelve a bajar todo, incluso lo cacheado")
    ap.add_argument("--contra-salta", action="store_true",
                    help="Coteja las series de Salta contra el archivo del portal provincial")
    args = ap.parse_args()

    print("A. Los seis agregados de datos.jus.gob.ar")
    pat = {}          # (anio, mes, jurisdiccion, categoria, metrica) -> cantidad
    for (cat, met), (ds, res, arch) in FUENTES.items():
        datos = bajar(JUS % (ds, res, arch), args.fuentes, arch, args.refrescar)
        if datos is None:
            continue
        d = completar_cero(leer_csv_dnrpa(datos, cat, met), "%s / %s" % (cat, met))
        for (a, m, j), v in d.items():
            pat[(a, m, j, cat, met)] = v
        verif_continuidad(d, "%s / %s" % (cat, met))
    if not pat:
        raise SystemExit("no se pudo leer ninguno de los agregados de la DNRPA")

    print("B. El parque activo, pagina por anio")
    hoy = datetime.date.today()
    parque, totales, vacios = {}, {}, []
    for anio in range(PARQUE_DESDE, hoy.year + 1):
        datos = bajar(PARQUE_URL % anio, args.fuentes, "parque_%d.html" % anio, args.refrescar)
        if datos is None:
            continue
        d, tot = leer_parque(datos, anio)
        # En el anio en curso los meses todavia no publicados vienen con cero, y un parque no
        # puede ser cero: se descartan por el total del pais, que es el unico testigo confiable.
        sin_publicar = [m for m, v in tot.items() if not v]
        for m in sin_publicar:
            for j in PROVINCIAS:
                d.pop((anio, m, j), None)
            tot.pop(m, None)
        if sin_publicar:
            vacios.append("%d: %s" % (anio, ",".join(str(m) for m in sorted(sin_publicar))))
        parque.update(d)
        for m, v in tot.items():
            totales[(anio, m)] = v
    if vacios:
        print("   meses sin publicar descartados -> %s" % "; ".join(vacios))
    verif_continuidad(parque, "parque automotor")

    print("C. Verificaciones")
    verif_suma_parque(parque, totales)
    verif_parque_monotono(parque)
    for cat in CATEGORIAS:
        for met in METRICAS_PAT:
            saltos_de_magnitud(
                [("%d-%02d" % (a, m), v) for (a, m, j, c, mm), v in pat.items()
                 if j == "Salta" and c == cat and mm == met],
                "Salta / %s / %s" % (cat, met))
    print("   saltos de magnitud revisados en las seis series de Salta")

    if args.contra_salta:
        print("D. Cotejo contra el archivo del portal provincial")
        cotejo_contra_salta(pat, args.fuentes, args.refrescar)

    print("E. Salida")
    # Dos agregados, porque la fuente no los publica: el total del pais por suma de las
    # jurisdicciones, y la categoria Total por suma de las tres categorias.
    #
    # La categoria Total SOLO se emite en los meses en que estan las tres: autos arrancan en 2000,
    # motos en 2007 y maquinarias en septiembre de 2013. Sumar lo que haya dibujaria dos escalones
    # -- uno en 2007 y otro en 2013 -- que serian cambios de cobertura, no de patentamiento.
    por_mes = collections.defaultdict(set)
    for (a, m, j, c, met) in pat:
        por_mes[(a, m, met)].add(c)
    completos = {k for k, v in por_mes.items() if v >= set(CATEGORIAS)}
    recortados = sorted({(a, m) for (a, m, _) in por_mes} - {(a, m) for (a, m, _) in completos})
    if recortados:
        print("   categoria Total omitida en %d meses sin las tres categorias (hasta %d-%02d)"
              % (len(recortados), recortados[-1][0], recortados[-1][1]))

    agregados = collections.defaultdict(int)
    for (a, m, j, c, met), v in pat.items():
        agregados[(a, m, TOTAL_PAIS, c, met)] += v
        if (a, m, met) in completos:
            agregados[(a, m, j, TOTAL_CAT, met)] += v
            agregados[(a, m, TOTAL_PAIS, TOTAL_CAT, met)] += v
    pat.update(agregados)

    orden_j = {j: i for i, j in enumerate(PROVINCIAS + [TOTAL_PAIS])}
    orden_c = {c: i for i, c in enumerate([TOTAL_CAT] + CATEGORIAS)}
    orden_m = {m: i for i, m in enumerate(METRICAS_PAT)}
    filas = [{"anio": a, "n_mes": m, "mes": "%d-%02d-01" % (a, m), "periodo": "%d-%02d" % (a, m),
              "jurisdiccion": j, "categoria": c, "metrica": met, "valor": v}
             for (a, m, j, c, met), v in pat.items()]
    filas.sort(key=lambda f: (orden_j[f["jurisdiccion"]], orden_c[f["categoria"]],
                              orden_m[f["metrica"]], f["anio"], f["n_mes"]))
    escribir_csv(os.path.join(args.salida, SALIDA_PAT), CAMPOS_PAT, filas)

    for (a, m), v in totales.items():
        parque[(a, m, TOTAL_PAIS)] = v
    filas = [{"anio": a, "n_mes": m, "mes": "%d-%02d-01" % (a, m), "periodo": "%d-%02d" % (a, m),
              "jurisdiccion": j, "metrica": "parque_automotor", "valor": v}
             for (a, m, j), v in parque.items()]
    filas.sort(key=lambda f: (orden_j[f["jurisdiccion"]], f["anio"], f["n_mes"]))
    escribir_csv(os.path.join(args.salida, SALIDA_PAR), CAMPOS_PAR, filas)

    print()
    if incidencias:
        print("Incidencias (%d):" % len(incidencias))
        for x in incidencias[:40]:
            print("  -", x)
        if len(incidencias) > 40:
            print("  ... y %d mas" % (len(incidencias) - 40))
    else:
        print("Sin incidencias detectadas.")


if __name__ == "__main__":
    main()
```
