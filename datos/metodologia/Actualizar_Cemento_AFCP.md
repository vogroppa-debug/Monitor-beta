# Actualización — Despachos de cemento por provincia y envase (AFCP)

Regenera la serie mensual de despachos de cemento en bolsa y a granel, para las 25 jurisdicciones
que abre la Asociación de Fabricantes de Cemento Portland y el total del país, a partir de
<https://www.afcp.org.ar/copia-de-despacho-total-de-cemento>. La AFCP no publica un archivo
descargable: publica **una página HTML por mes**, generada con Word, y el script las lee todas.

> **La apertura por provincia se corta en septiembre de 2025.** La AFCP sigue publicando despachos
> **nacionales** hasta octubre de 2026, pero su informe mensual provisorio no tiene detalle
> provincial, y las URLs provinciales posteriores a 2025-09 dan 404. El script enumera los meses y
> levanta solos los que vayan apareciendo: cuando la AFCP retome, alcanza con volver a correrlo.

> **La fuente no dice en qué unidad están los números.** Son **toneladas**, según el informe
> mensual de la propia AFCP: *«Las valores están expresados en toneladas»*
> (<https://www.afcp.org.ar/despacho-mensual>). Ni la página provincial ni la de acumulados lo
> aclaran.

> **La serie arranca en 2017, no en 2018.** Cada página trae dos bloques: el mes publicado y el
> mismo mes del año anterior. Eso agrega un año entero por delante y, de paso, hace que 81 meses se
> lean dos veces en páginas distintas — el control cruzado más fuerte que tiene esta fuente.

> **`CAPITAL FEDERAL` se emite como `CABA`.** La denominación de la fuente es vieja.

> **No hay columna `calidad` porque no hace falta.** Todo lo que entra viene de la sección «Datos
> Definitivos»; lo provisorio de la AFCP es el informe nacional, que no entra acá.

Metodología y verificaciones: `Metodologia_Cemento_AFCP.md`.

## Qué genera (en `datos-drive/`)

| Archivo | Base de origen | Período | Dimensiones propias |
|---|---|---|---|
| `Despachos_cemento_AFCP_provincia_mensual.csv` | 93 páginas `estadistica04.html` de `afcp.info` | 2017-01 → 2025-09 | `provincia` (26), `metrica` (bolsa, granel, total) |

Cierra en `metrica, valor`, el esquema canónico del Monitor.

```
anio,n_mes,mes,periodo,provincia,metrica,valor
2025,9,2025-09-01,2025-09,Salta,despachos_bolsa_t,9680
2025,9,2025-09-01,2025-09,Salta,despachos_granel_t,5430
2025,9,2025-09-01,2025-09,Salta,despachos_total_t,15110
```

## 1. Requisitos

```
(ninguno)
```

Sólo biblioteca estándar: `urllib` para la descarga y `html.parser` para el parseo. Esta fuente no
necesita ni `openpyxl` ni `pandas`.

## 2. Correr el script

```
python actualizar_cemento_afcp.py
```

| Argumento | Para qué |
|---|---|
| `--salida DIR` | Carpeta de salida. Por defecto, `datos-drive/` |
| `--fuentes DIR` | Caché de las páginas originales. Por defecto, `datos-drive/fuentes/afcp_cemento/` |
| `--refrescar` | Vuelve a bajar las 93 páginas, incluso las cacheadas |

La primera corrida baja 93 páginas (~19 MB) y tarda unos minutos. Las siguientes sólo piden los
meses nuevos.

## 3. Cómo resuelve la descarga (y por qué así)

- **No se scrapean los enlaces de la página índice.** Es un sitio Wix que los arma por JavaScript,
  **le falta el de agosto de 2022** —que sin embargo existe y responde— y duplica el de agosto de
  2023. El script **enumera los meses** desde enero de 2018 hasta el mes actual y prueba los dos
  patrones de URL que usó la AFCP:

  ```
  .../DATOS-DEFINITIVOS/{AAAAMM}/estadistica04.html              hasta 2022-03
  .../DATOS-DEFINITIVOS/{AAAAMM}-Provincias/estadistica04.html   desde 2022-04
  ```

  Así entra agosto de 2022 y así van a entrar los meses nuevos sin tocar el script. Un 404 después
  del último mes publicado es normal y no es incidencia; **un hueco en el medio sí lo es**.
- **Caché permanente** en `fuentes/afcp_cemento/{AAAAMM}.html`, con los bytes originales. Los datos
  son definitivos y están verificados como no reescritos —0 discrepancias en 2.106 celdas releídas
  entre páginas publicadas con un año de diferencia—, así que un mes ya bajado no se vuelve a
  pedir. `--refrescar` fuerza la re-descarga.
- **Decodificación estricta**, probando `cp1252` (la que declara el `<meta>`), `utf-8` y `latin-1`.
  Nunca `errors="replace"`.
- **Parseo con `html.parser`** de la biblioteca estándar, con una pila de filas abiertas para no
  confundirse con las tablas que Word anida dentro de las celdas. Cada bloque se identifica por su
  fila de título, `Período: <Mes> de <Año>`.
- **Las jurisdicciones se leen por etiqueta, contra un diccionario cerrado.** Una etiqueta
  desconocida **con números al lado aborta la corrida**; sin números, es una fila de encabezado y
  se saltea.

## 4. Verificar antes de dar por buena la actualización

1. **La consola.** Tiene que cerrar con «Sin incidencias detectadas» o con una lista que se
   entienda. Hoy aparece una sola, esperada y real: el granel de CABA de abril de 2020 (86 t contra
   una mediana de ~9.000) dispara la regla de saltos de magnitud. Es el parate de la obra por la
   pandemia, no un error de parseo.

2. **Las cuatro verificaciones automáticas**, que el script imprime:

   | Control | Resultado esperado |
   |---|---|
   | Relectura entre páginas (81 meses × 26 filas) | **2.106 celdas, 0 discrepancias** |
   | `bolsa + granel` vs. total publicado, del mes | desvío **máximo 1 t** (372 celdas difieren) |
   | `acum(t) − acum(t−1)` vs. del mes | **0 desvíos** en 2.496 transiciones |
   | Suma de las 25 jurisdicciones vs. total del país | desvío **máximo 4 t** (217 casos) |

   Los desvíos de 1 y 4 toneladas son **redondeo de la fuente** y no se corrigen. Lo que no puede
   pasar es que crezcan.

3. **Cobertura.** 105 meses consecutivos de 2017-01 a 2025-09, sin huecos, con las 26
   jurisdicciones en cada mes. **8.190 filas.**

4. **Los guiones.** El script informa cuántas celdas leyó como cero; hoy son **2**. La AFCP escribe
   `-` cuando una jurisdicción no despachó nada, y la identidad lo confirma: La Rioja, abril de
   2020, bolsa 4.981 + granel `-` = total 4.981.

5. **Valores de control de Salta**, que tienen que salir clavados (toneladas):

   | Mes | Bolsa | Granel | Total |
   |---|---|---|---|
   | 2017-01 | 17.893 | 5.332 | 23.225 |
   | 2020-04 | 14.226 | 1.151 | 15.377 |
   | 2024-09 | 16.288 | 8.252 | 24.540 |
   | 2025-09 | 9.680 | 5.430 | 15.110 |
   | **2024 completo** | **163.380** | **85.829** | **249.210** |

   Total del país: 2017-01 → 566.123 / 307.653 / 873.775; 2025-09 → 513.908 / 404.168 / 918.077.
   Salta explica en promedio el **2,64 %** de los despachos del país, entre 1,49 % y 3,81 % según
   el mes.

6. **Reproducibilidad.** Dos corridas seguidas tienen que dar el mismo md5, y el bloque `python` de
   abajo tiene que ser idéntico al `.py` en disco.

7. **Formato**, con la skill `datasets`: decimal `.`, sin separador de miles, sin mojibake (ojo con
   `Córdoba`, `Entre Ríos`, `Neuquén`, `Río Negro` y `Tucumán`, que llevan tildes después de
   normalizar), sin negativos, sin claves duplicadas y todos los valores enteros.

---

## Script completo

Guardar el bloque de abajo como `actualizar_cemento_afcp.py` **dentro de `datos-drive/`**.

```python
# -*- coding: utf-8 -*-
"""
Despachos de cemento por provincia y envase (AFCP) -- base mensual.

Genera `Despachos_cemento_AFCP_provincia_mensual.csv` a partir de "Consumo de Cemento por
Provincias y segun Envases", que la Asociacion de Fabricantes de Cemento Portland publica en

    https://www.afcp.org.ar/copia-de-despacho-total-de-cemento

La AFCP no publica un archivo descargable: publica UNA PAGINA HTML POR MES, generada con Word, en
`afcp.info`. Cada pagina trae una tabla con 25 jurisdicciones mas el total del pais, abierta en
bolsa y granel, con el valor del mes y el acumulado del anio.

CADA PAGINA TRAE DOS ANIOS
    Ademas del mes publicado, la tabla repite EL MISMO MES DEL ANIO ANTERIOR, para comparacion.
    Dos consecuencias:
      1. La serie arranca en enero de 2017, un anio antes de lo que anuncia la pagina.
      2. 81 meses se leen dos veces, en paginas distintas publicadas con un anio de diferencia.
         Esa relectura es el control cruzado mas fuerte que tiene esta fuente, y se verifica en
         cada corrida.

POR QUE NO SE SCRAPEAN LOS ENLACES DE LA PAGINA
    El indice es un sitio Wix que arma los enlaces por JavaScript, le FALTA el de agosto de 2022
    -- que sin embargo existe y responde -- y duplica el de agosto de 2023. En vez de leerlo, el
    script enumera los meses y prueba los dos patrones de URL que uso la AFCP:

        .../DATOS-DEFINITIVOS/{AAAAMM}/estadistica04.html              hasta 2022-03
        .../DATOS-DEFINITIVOS/{AAAAMM}-Provincias/estadistica04.html   desde 2022-04

    Asi entra agosto de 2022 y asi van a entrar los meses nuevos sin tocar el script.

QUE NO SE EMITE
    Las columnas de acumulado y las de porcentaje. El acumulado es la suma corrida dentro del anio
    y el porcentaje es un cociente: los dos se derivan del propio CSV. Se LEEN y se usan para
    verificar, pero no se publican.

UNIDAD
    Toneladas. La pagina provincial no lo dice en ningun lado; la unidad sale del informe mensual
    de la propia AFCP (https://www.afcp.org.ar/despacho-mensual), que la declara: "Las valores
    estan expresados en toneladas".

Formato de salida (convencion del repo): decimal '.', sin separador de miles, CSV con ',',
UTF-8 con BOM.

Correr:  python actualizar_cemento_afcp.py [--salida DIR] [--fuentes DIR] [--refrescar]
"""

import argparse
import collections
import csv
import datetime
import io
import os
import re
import statistics
import sys
import urllib.request
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.abspath(__file__))

BASE = "http://afcp.info/ESTADISTICAS/DATOS-DEFINITIVOS/%s/estadistica04.html"
PATRONES = ("%s-Provincias", "%s")          # el nuevo primero
INICIO = (2018, 1)                          # primera pagina publicada
UA = {"User-Agent": "CESS-Salta-indicadores/1.0 (indicadores PDES 2030)"}

SALIDA = "Despachos_cemento_AFCP_provincia_mensual.csv"
CAMPOS = ["anio", "n_mes", "mes", "periodo", "provincia", "metrica", "valor"]

# Las etiquetas de la fuente vienen en mayusculas, sin acentos y abreviadas: es un artefacto de la
# planilla de Word, no una convencion de nombres. Se normalizan con este diccionario y nada mas:
# una etiqueta que no este aca aborta la corrida, para que un cambio de la fuente no pase callado.
# "CAPITAL FEDERAL" sale como CABA: la denominacion de la fuente es vieja.
PROVINCIAS = {
    "CAPITAL FEDERAL": "CABA",
    "GRAN BUENOS AIRES": "Gran Buenos Aires",
    "BUENOS AIRES": "Buenos Aires",
    "CATAMARCA": "Catamarca",
    "CORDOBA": "Córdoba",
    "CORRIENTES": "Corrientes",
    "CHACO": "Chaco",
    "CHUBUT": "Chubut",
    "ENTRE RIOS": "Entre Ríos",
    "FORMOSA": "Formosa",
    "JUJUY": "Jujuy",
    "LA PAMPA": "La Pampa",
    "LA RIOJA": "La Rioja",
    "MENDOZA": "Mendoza",
    "MISIONES": "Misiones",
    "NEUQUEN": "Neuquén",
    "RIO NEGRO": "Río Negro",
    "SALTA": "Salta",
    "SAN JUAN": "San Juan",
    "SAN LUIS": "San Luis",
    "SANTA CRUZ": "Santa Cruz",
    "SANTA FE": "Santa Fe",
    "SGO. DEL ESTERO": "Santiago del Estero",
    "T. DEL FUEGO": "Tierra del Fuego",
    "TUCUMAN": "Tucumán",
    "TOTALES": "Total del país",
}
TOTAL_PAIS = PROVINCIAS["TOTALES"]

MESES_ES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
            "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
            "noviembre": 11, "diciembre": 12}

# Posicion de cada columna dentro del bloque de 12 que sigue al nombre de la jurisdiccion.
COL = {"bolsa": 0, "bolsa_acum": 2, "granel": 4, "granel_acum": 6,
       "total": 8, "total_acum": 10}
ORDEN_METRICA = {"despachos_bolsa_t": 0, "despachos_granel_t": 1, "despachos_total_t": 2}

RE_PERIODO = re.compile(r"Per.odo:\s*([A-Za-zÀ-ÿ]+)\s+de\s+(\d{4})")
RE_MILES = re.compile(r"^-?\d{1,3}(\.\d{3})*$")

incidencias = []


def inc(msg):
    incidencias.append(msg)


# --------------------------------------------------------------------------- descarga y escritura

def bajar_bytes(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def pagina(ym, destino, refrescar=False):
    """Bytes de la pagina del mes `ym` (AAAAMM), con cache permanente.

    Los datos son definitivos y estan verificados como no reescritos (ver el control de relectura),
    asi que un mes ya bajado no se vuelve a pedir. Guardar el original permite explicar despues por
    que un numero cambio.
    """
    dest = os.path.join(destino, "%s.html" % ym)
    if os.path.exists(dest) and not refrescar:
        return open(dest, "rb").read()
    for pat in PATRONES:
        try:
            b = bajar_bytes(BASE % (pat % ym))
        except Exception:
            continue
        os.makedirs(destino, exist_ok=True)
        tmp = dest + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(b)
        os.replace(tmp, dest)
        print("   bajado %s" % ym)
        return b
    return None


def escribir_csv(ruta, campos, filas):
    with io.open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print("   -> %s (%d filas)" % (os.path.basename(ruta), len(filas)))


# ------------------------------------------------------------------------------------- parseo

def decodificar(b, ym):
    """Decodifica en estricto probando cp1252, utf-8 y latin-1. Nunca errors='replace', que
    enmascara el problema en vez de mostrarlo."""
    for enc in ("cp1252", "utf-8", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    raise SystemExit("no se pudo decodificar la pagina de %s" % ym)


class Tablas(HTMLParser):
    """Devuelve las filas de todas las tablas como listas de celdas de texto.

    Lleva una pila de filas abiertas porque el HTML que genera Word anida tablas dentro de celdas;
    con una sola fila "en curso" una tabla anidada pisaria la de afuera.
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.filas = []
        self._pila = []
        self._celda = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._pila.append([])
        elif tag in ("td", "th") and self._pila:
            self._celda = []

    def handle_endtag(self, tag):
        if tag == "tr" and self._pila:
            fila = self._pila.pop()
            if fila:
                self.filas.append(fila)
        elif tag in ("td", "th") and self._celda is not None:
            txt = re.sub(r"\s+", " ", "".join(self._celda).replace(" ", " ")).strip()
            self._pila[-1].append(txt)
            self._celda = None

    def handle_data(self, data):
        if self._celda is not None:
            self._celda.append(data)


guiones = [0]      # celdas con un guion, que la AFCP usa para el cero


def parse_miles(s, ctx):
    """Texto en configuracion latina (miles con '.', sin decimales) -> entero.

    La configuracion se decide A NIVEL DE COLUMNA, como pide la skill `datasets`, y el criterio es
    de coherencia: bajo la lectura decimal ('17.893' = 17,893 t) no cerraria ninguna de las cuatro
    identidades que verifica el script. Un valor que no respete el agrupamiento de a tres se
    reporta como incidencia en vez de leerse a la fuerza.

    El GUION ES CERO, no un dato faltante. La AFCP lo usa cuando una jurisdiccion no despacho nada
    en el mes, y la identidad bolsa + granel = total lo confirma: La Rioja, abril de 2020, bolsa
    4.981, granel '-', total 4.981.
    """
    t = (s or "").replace(" ", "").strip()
    if t in ("-", "--", "–"):
        guiones[0] += 1
        return 0
    if not t:
        return None
    if not RE_MILES.match(t):
        inc("valor con formato inesperado en %s: '%s'" % (ctx, s))
        return None
    return int(t.replace(".", ""))


def leer_pagina(b, ym):
    """Bytes de una pagina -> {(anio, mes): {provincia_normalizada: [12 numeros]}}."""
    p = Tablas()
    p.feed(decodificar(b, ym))
    bloques = {}
    actual = None
    for cel in p.filas:
        m = RE_PERIODO.search(" ".join(cel))
        if m:
            mes = MESES_ES.get(m.group(1).strip().lower())
            if not mes:
                raise SystemExit("mes desconocido '%s' en la pagina de %s" % (m.group(1), ym))
            actual = (int(m.group(2)), mes)
            bloques.setdefault(actual, {})
            continue
        if actual is None or len(cel) < 13 or not cel[0]:
            continue
        etq = cel[0].strip()
        crudo = cel[1:13]
        if etq not in PROVINCIAS:
            # Puede ser una fila de encabezado ("Del Mes", "% / Total", ...). Solo es un problema
            # si trae numeros al lado: ahi la fuente cambio y la corrida se corta.
            if any(RE_MILES.match(c.replace(" ", "").strip()) for c in crudo if c.strip()):
                raise SystemExit("etiqueta de jurisdiccion desconocida '%s' en la pagina de %s"
                                 % (etq, ym))
            continue
        # Solo se leen las seis columnas de valor; las otras seis son porcentajes, que no se
        # emiten (son un cociente derivable) y no tienen el formato de un entero con miles.
        vals = [None] * 12
        for j in sorted(COL.values()):
            vals[j] = parse_miles(crudo[j], "%s %s" % (ym, etq))
        if any(vals[j] is None for j in COL.values()):
            inc("%s, %s: falta alguna de las seis columnas de valor" % (ym, etq))
        bloques[actual][PROVINCIAS[etq]] = vals
    return bloques


# ------------------------------------------------------------------------------ verificaciones

def saltos_de_magnitud(pares, etiqueta, minimo=24):
    """Regla de la skill `datasets`: un valor >100x o <1/100 de la mediana de su serie. Se reporta
    CON los periodos y no se corrige."""
    vals = [v for _, v in pares if v]
    if len(vals) < minimo:
        return
    med = statistics.median(vals)
    if not med:
        return
    raros = [(p, v) for p, v in pares if v and (v / med > 100 or v / med < 0.01)]
    if raros:
        inc("salto de orden de magnitud en %s: %d valores (ej. %s)"
            % (etiqueta, len(raros), ", ".join("%s=%g" % r for r in raros[:3])))


def verif_relectura(lecturas):
    """81 meses se leen dos veces, en paginas distintas publicadas con un anio de diferencia."""
    celdas = 0
    dif = []
    for per, obs in sorted(lecturas.items()):
        if len(obs) < 2:
            continue
        (o1, b1), (o2, b2) = obs[0], obs[1]
        for prov in sorted(set(b1) | set(b2)):
            celdas += 1
            if b1.get(prov) != b2.get(prov):
                dif.append("%d-%02d %s (%s vs %s)" % (per[0], per[1], prov, o1, o2))
    if dif:
        inc("la relectura entre paginas no coincide en %d celdas: %s"
            % (len(dif), ", ".join(dif[:5])))
    print("   relectura entre paginas: %d celdas comparadas, %d discrepancias"
          % (celdas, len(dif)))
    return celdas, len(dif)


def verif_identidades(datos):
    """bolsa + granel = total, en el mes y en el acumulado. La AFCP redondea cada celda por
    separado, asi que se espera una diferencia de hasta 1 t; mas que eso es un problema."""
    out = {}
    for etq, (a, b, c) in (("del mes", ("bolsa", "granel", "total")),
                           ("acumulado", ("bolsa_acum", "granel_acum", "total_acum"))):
        peor = 0
        n = 0
        for (per, prov), v in datos.items():
            x, y, z = v[COL[a]], v[COL[b]], v[COL[c]]
            if None in (x, y, z):
                continue
            d = abs(x + y - z)
            peor = max(peor, d)
            n += (d > 0)
        if peor > 1:
            inc("bolsa + granel no da el total (%s): desvio maximo de %d t" % (etq, peor))
        print("   bolsa + granel vs. total (%s): desvio maximo %d t, %d celdas con desvio"
              % (etq, peor, n))
        out[etq] = (peor, n)
    return out


def verif_cadena_acum(datos, provincias, periodos):
    """acum(t) - acum(t-1) = del mes, dentro de cada anio."""
    mal = 0
    n = 0
    for per in periodos:
        if per[1] == 1:
            continue
        ant = (per[0], per[1] - 1)
        for prov in provincias:
            v, w = datos.get((per, prov)), datos.get((ant, prov))
            if not v or not w:
                continue
            n += 1
            for base, acum in (("bolsa", "bolsa_acum"), ("granel", "granel_acum"),
                               ("total", "total_acum")):
                if None in (v[COL[acum]], w[COL[acum]], v[COL[base]]):
                    continue
                if abs((v[COL[acum]] - w[COL[acum]]) - v[COL[base]]) > 1:
                    mal += 1
                    break
    if mal:
        inc("la cadena del acumulado no cierra en %d casos" % mal)
    print("   cadena acum(t) - acum(t-1) = del mes: %d desvios en %d transiciones" % (mal, n))
    return mal, n


def verif_suma_pais(datos, periodos):
    """La suma de las 25 jurisdicciones tiene que dar TOTALES, con la misma tolerancia de
    redondeo."""
    partes = [p for p in PROVINCIAS.values() if p != TOTAL_PAIS]
    peor = 0
    n = 0
    for per in periodos:
        for k in ("bolsa", "granel", "total"):
            t = datos.get((per, TOTAL_PAIS), [None] * 12)[COL[k]]
            if t is None:
                continue
            s = sum(datos[(per, p)][COL[k]] for p in partes
                    if (per, p) in datos and datos[(per, p)][COL[k]] is not None)
            d = abs(s - t)
            peor = max(peor, d)
            n += (d > 0)
    if peor > 10:
        inc("la suma de las jurisdicciones no da el total del pais: desvio maximo de %d t" % peor)
    print("   suma de jurisdicciones vs. total del pais: desvio maximo %d t, %d casos con desvio"
          % (peor, n))
    return peor, n


# ------------------------------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(
        description="Despachos de cemento por provincia y envase (AFCP)")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "afcp_cemento"),
                    help="Cache de las paginas originales")
    ap.add_argument("--refrescar", action="store_true",
                    help="Vuelve a bajar todas las paginas, incluso las cacheadas")
    args = ap.parse_args()

    hoy = datetime.date.today()
    meses = []
    y, m = INICIO
    while (y, m) <= (hoy.year, hoy.month):
        meses.append("%d%02d" % (y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)

    print("A. Paginas de la AFCP")
    lecturas = collections.defaultdict(list)    # (anio,mes) -> [(origen, {prov: [12]})]
    bajadas = []
    for ym in meses:
        b = pagina(ym, args.fuentes, args.refrescar)
        if b is None:
            continue
        bajadas.append(ym)
        for per, bloque in leer_pagina(b, ym).items():
            if bloque:
                lecturas[per].append((ym, bloque))
    if not bajadas:
        raise SystemExit("no se pudo leer ninguna pagina de la AFCP")
    print("   %d paginas leidas, de %s a %s" % (len(bajadas), bajadas[0], bajadas[-1]))

    # Un 404 despues del ultimo mes publicado es normal; un hueco en el medio, no.
    huecos = [x for x in meses[meses.index(bajadas[0]):meses.index(bajadas[-1]) + 1]
              if x not in bajadas]
    if huecos:
        inc("faltan paginas en el medio de la serie: %s" % ", ".join(huecos))
    pendientes = meses[meses.index(bajadas[-1]) + 1:]
    if pendientes:
        print("   sin publicar todavia: %d meses, de %s a %s"
              % (len(pendientes), pendientes[0], pendientes[-1]))

    print("B. Datos")
    datos = {}
    for per, obs in lecturas.items():
        for prov, vals in obs[0][1].items():
            datos[(per, prov)] = vals
    periodos = sorted({p for p, _ in datos})
    print("   %d meses, de %d-%02d a %d-%02d; %d jurisdicciones"
          % (len(periodos), periodos[0][0], periodos[0][1], periodos[-1][0], periodos[-1][1],
             len({p for _, p in datos})))
    print("   guiones leidos como cero: %d celdas" % guiones[0])

    esperados = []
    y, m = periodos[0]
    while (y, m) <= periodos[-1]:
        esperados.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    faltan = [p for p in esperados if p not in periodos]
    if faltan:
        inc("faltan %d meses en la serie (ej. %s)"
            % (len(faltan), ", ".join("%d-%02d" % p for p in faltan[:4])))
    incompletos = [p for p in periodos if len({q for (pp, q) in datos if pp == p}) != len(PROVINCIAS)]
    if incompletos:
        inc("%d meses no traen las %d jurisdicciones (ej. %s)"
            % (len(incompletos), len(PROVINCIAS),
               ", ".join("%d-%02d" % p for p in incompletos[:4])))

    print("C. Verificaciones")
    verif_relectura(lecturas)
    verif_identidades(datos)
    verif_cadena_acum(datos, sorted({p for _, p in datos}), periodos)
    verif_suma_pais(datos, periodos)

    print("D. Salida")
    orden_prov = {p: i for i, p in enumerate(PROVINCIAS.values())}
    filas = []
    for (per, prov), v in datos.items():
        com = {"anio": per[0], "n_mes": per[1], "mes": "%d-%02d-01" % per,
               "periodo": "%d-%02d" % per, "provincia": prov}
        for met, k in (("despachos_bolsa_t", "bolsa"), ("despachos_granel_t", "granel"),
                       ("despachos_total_t", "total")):
            if v[COL[k]] is None:
                inc("falta %s de %s en %d-%02d" % (met, prov, per[0], per[1]))
                continue
            f = dict(com)
            f["metrica"] = met
            f["valor"] = v[COL[k]]
            filas.append(f)
    filas.sort(key=lambda f: (orden_prov[f["provincia"]], f["anio"], f["n_mes"],
                              ORDEN_METRICA[f["metrica"]]))

    for prov in PROVINCIAS.values():
        for met in ORDEN_METRICA:
            pares = [(f["periodo"], f["valor"]) for f in filas
                     if f["provincia"] == prov and f["metrica"] == met]
            saltos_de_magnitud(pares, "%s / %s" % (prov, met))

    escribir_csv(os.path.join(args.salida, SALIDA), CAMPOS, filas)

    print()
    if incidencias:
        print("Incidencias:")
        for x in incidencias:
            print("  -", x)
    else:
        print("Sin incidencias detectadas.")


if __name__ == "__main__":
    main()
```
