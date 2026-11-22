# Actualización — Producción de azúcar y alcohol por ingenio (Centro Azucarero Argentino)

Regenera la serie anual de caña molida, azúcar por tipo y alcohol de los 23 ingenios azucareros del
país, por zafra, a partir de las planillas que publica el Centro Azucarero Argentino:

- <https://centroazucarero.com.ar/produccion-de-azucar-2020-2029/>
- <https://centroazucarero.com.ar/produccion-de-azucar-1990-1999/>
- <https://centroazucarero.com.ar/produccion-de-alcohol-2020-2029/>
- <https://centroazucarero.com.ar/produccion-de-alcohol-1990-1999/>

> **Las URL de las planillas cambian solas.** El nombre de archivo cuelga de la carpeta de subida
> de WordPress (`/wp-content/uploads/2026/07/…`), así que cuando el CAA publique la zafra siguiente
> la dirección va a ser otra. Por eso el script **no las hardcodea**: raspa los enlaces `.xlsx` de
> las cuatro páginas, los clasifica por nombre (producto × época) y, si una ranura tiene varios
> candidatos, se queda con el que trae más años con datos. **No hay nada que mantener a mano.**

> **La zafra es anual y se publica una vez por año**, después de noviembre. Correr esto más seguido
> que eso no trae nada nuevo.

> **Los dos ingenios de Salta están intercambiados entre 1990 y 2002 en la fuente.** El script no
> lo corrige: marca esas filas con `calidad = rotulo_dudoso` y el tablero abre por ingenio recién
> en 2010. La evidencia está en `Metodologia_Azucar_Alcohol_CAA.md` §2.

> **El «Rendimiento %» de la fuente no es azúcar sobre caña** y su definición no pudo
> establecerse. Se publica tal cual y el tablero no lo usa: calcula el suyo. Ver la metodología §5.

## Qué genera (en `datos-drive/`)

| Archivo | Base de origen | Período | Dimensiones propias |
|---|---|---|---|
| `Produccion_sucroalcoholera_CAA_ingenio_anual.csv` | 4 planillas XLSX del CAA | 1990 → 2025 | `provincia` (6 con agregados), `ingenio` (24 con `Total`), `metrica` (9) |

Cierra en `metrica, valor`, el esquema canónico del Monitor.

```
anio,provincia,departamento,ingenio,metrica,valor,calidad,fuente_doc
2025,Salta,General Güemes,San Isidro,azucar_total_t,65912,definitivo,Produccion-de-Azucar-desde-2016.xlsx
2025,Salta,Orán,Tabacal,alcohol_m3,115158.756,definitivo,Produccion-de-alcoholes-desde-2016.xlsx
2025,Salta,,Total,azucar_total_t,85896,derivado,
```

`ingenio = Total` es un **margen**: es la suma de los ingenios de esa provincia, no un ingenio más.
Lo mismo `provincia = NOA` (Jujuy + Salta + Tucumán) y `provincia = Total del país`. Todo gráfico
tiene que fijarlos o va a duplicar.

`departamento` se completa sólo para los dos ingenios de Salta, y es el de **la fábrica**, no el
del cañaveral.

## 1. Requisitos

```
pip install openpyxl
```

`urllib` para bajar, `html.parser` para descubrir los enlaces y `openpyxl` para leer las planillas.
No hace falta `pandas`.

## 2. Correr el script

```
python actualizar_azucar_alcohol_caa.py
```

| Argumento | Para qué |
|---|---|
| `--salida DIR` | Carpeta de salida. Por defecto, `datos-drive/` |
| `--fuentes DIR` | Caché de los archivos originales. Por defecto, `datos-drive/fuentes/caa_sucroalcoholero/` |
| `--refrescar` | Vuelve a bajar todo, incluso lo cacheado |
| `--detalle-cotejo` | Lista una por una las diferencias de caña entre los dos libros, en vez de resumirlas por año |

**Para traer una zafra nueva hay que correr con `--refrescar`**: la caché es permanente y, si no,
devuelve las planillas viejas. El descubrimiento de enlaces también está cacheado.

## 3. Verificar antes de dar por buena la actualización

La corrida imprime cuatro bloques. Esto es lo que tiene que decir:

**Bloque 1 — las cuatro planillas.** Los cuatro rangos de años, y el año final del libro nuevo
tiene que ser la zafra que se está incorporando. El enlace roto
`produccion-de-alcohol-desde-1990.xlsx` (404) es de la página del CAA y es esperable: el script
sigue con el otro candidato de la misma ranura.

**Bloque 2 — verificaciones de cada libro.** Lo esperado hoy:

```
   cierre vertical produccion-de-alcohol-desde-1990-ok.xlsx: 34 hojas, 0 desvios
   cierre vertical Produccion-de-alcoholes-desde-2016.xlsx: 10 hojas, 0 desvios
   cierre vertical produccion-de-azucar-desde-1990.xlsx: 35 hojas, 1 desvios
   cierre horizontal produccion-de-azucar-desde-1990.xlsx: 784 filas, 0 desvios
   azucar sobre cana produccion-de-azucar-desde-1990.xlsx: 1 filas imposibles
   cierre vertical Produccion-de-Azucar-desde-2016.xlsx: 10 hojas, 0 desvios
   cierre horizontal Produccion-de-Azucar-desde-2016.xlsx: 200 filas, 0 desvios
   azucar sobre cana Produccion-de-Azucar-desde-2016.xlsx: 0 filas imposibles
```

El único desvío vertical es el histórico 2019 (azúcar crudo, 200 t) y la única fila imposible es
Ledesma 2024 en el histórico, las dos documentadas. **Cualquier otra que aparezca hay que mirarla
antes de publicar.** Un ingenio con un rótulo nuevo también sale acá, como
`ingenio desconocido '…'`, y su fila **no entra al dataset** hasta que se lo agregue al diccionario
`INGENIOS`.

**Bloque 3 — cotejo entre libros.** Hoy da 88 celdas distintas en azúcar y 31 en alcohol, y en
Salta ninguna fuera de la caña molida salvo la apertura de 2023 y 2024 y el alcohol de 2016, 2017
y 2023. La línea que importa es la última de cada producto:

```
   cotejo azucar: 9 anios superpuestos (2016-2024), 88 celdas distintas; en Salta, 8 fuera de la cana molida
```

**Bloque 4 — armado.** Tiene que decir **9/9 valores de control exactos** y **0 celdas que no
cierran contra NOA + Litoral**. Los saltos de orden de magnitud tienen que ser los 12 de la tabla
de la metodología §10; uno nuevo hay que explicarlo antes de publicar.

```
   total del pais: 200 celdas, 0 no cierran contra NOA + Litoral
   valores de control: 9/9 exactos
```

## 4. Copiar al sitio

El adapter del Monitor lee de `sitio-indicadores/datos/`, no de `datos-drive/`:

```powershell
copy datos-drive\Produccion_sucroalcoholera_CAA_ingenio_anual.csv sitio-indicadores\datos\
```

Después, `python build.py` en `sitio-indicadores/`. Lo usa el tema `azucar-alcohol`.

Si la zafra nueva agrega un tipo de azúcar o un ingenio, hay que mirar también `AZU_TIPOS` en
`adapters.py` y la cobertura declarada del tema en `catalog.py`.

## Script completo

`actualizar_azucar_alcohol_caa.py`, md5 `9c310c364a74e36fc465ec2206a907f4`.

```python
# -*- coding: utf-8 -*-
"""
Produccion de azucar y alcohol por ingenio (Centro Azucarero Argentino) -- base anual.

Genera un CSV:

    Produccion_sucroalcoholera_CAA_ingenio_anual.csv

LA FUENTE
    El Centro Azucarero Argentino publica, en el menu "Estadisticas" de centroazucarero.com.ar,
    cuatro planillas XLSX con UNA HOJA POR ANIO y UNA FILA POR INGENIO:

        Produccion-de-Azucar-desde-2016.xlsx       2016-2025  crudo, blanco, refinado, organico,
                                                              total, cana molida BRUTA, rendimiento
        produccion-de-azucar-desde-1990.xlsx       1990-2024  blanco, crudo, total, cana molida,
                                                              total en TMCV
        Produccion-de-alcoholes-desde-2016.xlsx    2016-2025  anhidradora, alcohol producido m3
        produccion-de-alcohol-desde-1990-ok.xlsx   1990-2023  anhidradora, alcohol producido m3

    Los nombres de archivo cuelgan de la carpeta de subida (/wp-content/uploads/AAAA/MM/), asi que
    CAMBIAN cuando el CAA publica la zafra siguiente. Por eso este script NO hardcodea las URL:
    raspa los enlaces .xlsx de las cuatro paginas de estadisticas, los clasifica por nombre y, si
    hay mas de un candidato para la misma ranura, se queda con el que trae mas anios con datos.

QUE INGENIO ES CADA DEPARTAMENTO
    El CAA publica por ingenio, no por departamento. Para Salta las dos cosas coinciden: San Isidro
    esta en Campo Santo (departamento General Guemes) y San Martin del Tabacal en Hipolito Yrigoyen
    (departamento Oran). Es la ubicacion de LA FABRICA, no la del canaveral: la cana de Tabacal
    viene de Oran y San Martin, y la de San Isidro de Guemes y Anta.

LOS DOS INGENIOS DE SALTA ESTAN INTERCAMBIADOS ENTRE 1990 Y 2002
    En el libro historico, lo que figura como "San Isidro" (1,0-1,6 M t de cana) es Tabacal, y al
    reves. La Nacion del 5-ago-1999 dice que San Isidro produjo 5.600 t de azucar en 1996, su
    ultimo anio, estuvo parado 1997 y 1998 y reabrio moliendo 220.000 t de cana: la planilla pone
    exactamente eso -- 5.627 / 0 / 0 / 217.519 -- en la fila rotulada "Tabacal". Ademas, corregido,
    cada ingenio pasa sin saltos por 2002-2003; sin corregir hay un derrumbe del 86 % en uno y un
    salto de x9,3 en el otro, el mismo anio y en sentidos opuestos (el unico par espejado de las 23
    series del pais). Y el libro de alcohol, para los mismos anios, pone a Tabacal muy por encima
    de San Isidro, que es el orden correcto.

    ESTE SCRIPT NO LO CORRIGE. Deja el dato tal como lo publica la fuente y marca esas filas con
    calidad = "rotulo_dudoso". El tablero empieza la apertura por ingenio en 2010.

EL "RENDIMIENTO %" DE LA FUENTE NO ES AZUCAR SOBRE CANA
    Tabacal 2025: 19.984 t de azucar sobre 1.802.042 t de cana es 1,1 %, y la planilla dice 10 %.
    La diferencia es la cana que se fue a alcohol. Se publica el rendimiento de la fuente tal cual
    (rendimiento_fuente_pct) y el tablero calcula aparte el azucar efectivo por tonelada de cana.
    `verif_rendimiento` mide cuanta azucar equivalente por m3 de alcohol hace falta para cerrar la
    cuenta y deja el resultado como incidencia informativa.

PRECEDENCIA ENTRE LIBROS
    Donde se superponen manda el libro nuevo (2016+); el historico solo aporta los anios que el
    nuevo no trae y las metricas que el nuevo no publica (TMCV).

UNIDAD
    Toneladas de azucar y de cana molida; metros cubicos de alcohol; porcentaje para el
    rendimiento que declara la fuente.

Formato de salida (convencion del repo): decimal '.', sin separador de miles, CSV con ',',
UTF-8 con BOM.

Correr:  python actualizar_azucar_alcohol_caa.py [--salida DIR] [--fuentes DIR] [--refrescar]
"""

import argparse
import collections
import csv
import io
import os
import re
import sys
import unicodedata
import urllib.request
from html.parser import HTMLParser

try:
    import openpyxl
except ImportError:
    sys.exit("Falta openpyxl: pip install openpyxl")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "CESS-Salta-indicadores/1.0 (indicadores PDES 2030)"}

SALIDA = "Produccion_sucroalcoholera_CAA_ingenio_anual.csv"
CAMPOS = ["anio", "provincia", "departamento", "ingenio", "metrica", "valor", "calidad",
          "fuente_doc"]

BASE = "https://centroazucarero.com.ar/"
PAGINAS = [
    "produccion-de-azucar-2020-2029/",
    "produccion-de-azucar-1990-1999/",
    "produccion-de-alcohol-2020-2029/",
    "produccion-de-alcohol-1990-1999/",
]

# Ranura -> (palabra del producto, palabra de la epoca). El archivo de naftas se descarta.
RANURAS = {
    ("azucar", "nuevo"): ("azucar", "2016"),
    ("azucar", "historico"): ("azucar", "1990"),
    ("alcohol", "nuevo"): ("alcohol", "2016"),
    ("alcohol", "historico"): ("alcohol", "1990"),
}

TOTAL_PAIS = "Total del país"
NOA = "NOA"
TOTAL_ING = "Total"
PROV_NOA = ["Jujuy", "Salta", "Tucumán"]

PROVINCIAS = {
    "jujuy": "Jujuy", "salta": "Salta", "tucuman": "Tucumán",
    "litoral": "Litoral", "santa fe": "Litoral",
}

# Nombre canonico de cada ingenio, por clave sin acentos ni mayusculas. La fuente escribe el mismo
# ingenio de varias formas segun el libro y el anio ("Rio Grande" / "Río Grande", "Tabacal " con
# espacio colgando, "Santa Barbara" / "Santa Bárbara").
INGENIOS = {
    "la esperanza": "La Esperanza", "ledesma": "Ledesma", "rio grande": "Río Grande",
    "san isidro": "San Isidro", "tabacal": "Tabacal",
    "aguilares": "Aguilares", "bella vista": "Bella Vista", "concepcion": "Concepción",
    "cruz alta": "Cruz Alta", "famailla": "Famaillá", "la corona": "La Corona",
    "la florida": "La Florida", "la providencia": "La Providencia",
    "la trinidad": "La Trinidad", "leales": "Leales", "marapa": "Marapa",
    "nunorco": "Ñuñorco", "san juan": "San Juan", "santa barbara": "Santa Bárbara",
    "santa rosa": "Santa Rosa",
    "inaza s.a.": "Inaza S.A.", "inaza": "Inaza S.A.", "las toscas": "Las Toscas",
    "san javier": "San Javier",
}


def ingenio(clave):
    """Nombre canonico. En 2013 y 2014 el libro historico rotula 'Famailla / Fronterita' a lo que
    el resto de la serie llama 'Famailla': se toma lo que esta antes de la barra."""
    return INGENIOS.get(clave) or INGENIOS.get(clave.split("/")[0].strip())

DEPARTAMENTO = {"San Isidro": "General Güemes", "Tabacal": "Orán"}

# Encabezado normalizado -> metrica. Dos nombres distintos caen en cana_molida_t: el libro nuevo
# dice "BRUTA" y el viejo no, y en los anios superpuestos difieren en 2016 y 2018 (ver cotejo).
COLUMNAS = {
    "produccion az. crudo (tn)": "azucar_crudo_t",
    "produccion az. blanco (tn)": "azucar_blanco_t",
    "produccion az. refinado (tn)": "azucar_refinado_t",
    "produccion az. organico (tn)": "azucar_organico_t",
    "azucar total producido (tn)": "azucar_total_t",
    "total cana molida bruta (tn)": "cana_molida_t",
    "total cana molida (tn)": "cana_molida_t",
    "total produccion azucar (tmcv)": "azucar_tmcv_t",
    "rendimiento %": "rendimiento_fuente_pct",
    "alcohol producido m3": "alcohol_m3",
}

# Metricas que se pueden sumar para armar provincia, NOA y pais. El rendimiento de la fuente es un
# cociente y no se agrega.
ADITIVAS = ["cana_molida_t", "azucar_total_t", "azucar_crudo_t", "azucar_blanco_t",
            "azucar_refinado_t", "azucar_organico_t", "azucar_tmcv_t", "alcohol_m3"]
METRICAS = ADITIVAS + ["rendimiento_fuente_pct"]

SALTA_DUDOSO_HASTA = 2002     # ultimo anio con los dos ingenios de Salta intercambiados

incidencias = []


def inc(msg):
    incidencias.append(msg)
    print("   ! " + msg)


def norm(s):
    """Minusculas, sin acentos, sin espacios repetidos. Para comparar rotulos de la fuente."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


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


class Enlaces(HTMLParser):
    """Junta los href de la pagina."""

    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


def descubrir_planillas(destino, refrescar=False):
    """Raspa las paginas de estadisticas y devuelve {ranura: [url, ...]}.

    No se hardcodean las URL porque el CAA sube la planilla nueva a la carpeta del mes y el nombre
    del archivo cambia con ella. Si una ranura tiene varios candidatos se resuelve en `elegir`.
    """
    candidatos = collections.defaultdict(set)
    for pag in PAGINAS:
        url = BASE + pag
        crudo = bajar(url, destino, "pagina_" + pag.strip("/") + ".html", refrescar)
        if crudo is None:
            continue
        p = Enlaces()
        p.feed(crudo.decode("utf-8", "replace"))
        for h in p.hrefs:
            if not h.lower().endswith(".xlsx"):
                continue
            nombre = norm(h.rsplit("/", 1)[-1])
            if "nafta" in nombre:
                continue
            for ranura, (prod, epoca) in RANURAS.items():
                if prod in nombre and epoca in nombre:
                    candidatos[ranura].add(h if h.startswith("http") else BASE + h.lstrip("/"))
    for ranura in RANURAS:
        if not candidatos.get(ranura):
            inc("no se encontro ninguna planilla para la ranura %s en las paginas del CAA"
                % ("/".join(ranura),))
    return {r: sorted(v) for r, v in candidatos.items()}


def leer_hoja(ws, doc, anio):
    """Devuelve ({(provincia, ingenio): {metrica: valor}}, {metrica: valor} de la fila TOTAL).

    No asume posiciones: busca la celda que dice "Provincia", y de esa fila y esa columna salen el
    encabezado y el ancla de las filas. Hace falta porque el encabezado esta en la fila 1 o en la 2
    segun el anio y algunas hojas arrancan en la columna B.
    """
    mat = [list(f) for f in ws.iter_rows(values_only=True)]
    anc = None
    for i, fila in enumerate(mat[:8]):
        for j, c in enumerate(fila):
            if norm(c) == "provincia":
                anc = (i, j)
                break
        if anc:
            break
    if anc is None:
        inc("%s hoja %s: no se encontro el encabezado 'Provincia'" % (doc, anio))
        return {}, {}
    i0, j0 = anc
    cols = {}
    for j, c in enumerate(mat[i0][j0:], start=j0):
        met = COLUMNAS.get(norm(c))
        if met and met not in cols:
            cols[met] = j
    if not cols:
        inc("%s hoja %s: encabezado sin ninguna columna conocida" % (doc, anio))
        return {}, {}

    def val(fila, j):
        v = fila[j] if j < len(fila) else None
        return float(v) if isinstance(v, (int, float)) else None

    datos, total = {}, {}
    for fila in mat[i0 + 1:]:
        if j0 >= len(fila):
            continue
        prov = PROVINCIAS.get(norm(fila[j0]))
        if prov:
            clave_ing = norm(fila[j0 + 1]) if j0 + 1 < len(fila) else ""
            ing = ingenio(clave_ing)
            if ing is None:
                inc("%s hoja %s: ingenio desconocido '%s'" % (doc, anio, clave_ing))
                continue
            d = {m: val(fila, j) for m, j in cols.items()}
            datos[(prov, ing)] = {m: v for m, v in d.items() if v is not None}
        elif not norm(fila[j0]) and total == {}:
            # Fila TOTAL: sin provincia ni ingenio, con numeros. Las lineas de nota que vienen
            # despues tienen texto en la columna del ingenio y no entran.
            if j0 + 1 < len(fila) and norm(fila[j0 + 1]):
                continue
            d = {m: val(fila, j) for m, j in cols.items()}
            if any(v is not None for v in d.values()):
                total = {m: v for m, v in d.items() if v is not None}
    return datos, total


def leer_libro(crudo, doc):
    """{anio: (datos, total)} de todas las hojas que son un anio."""
    wb = openpyxl.load_workbook(io.BytesIO(crudo), data_only=True)
    libro = {}
    for sh in wb.sheetnames:
        if not re.fullmatch(r"(19|20)\d\d", sh.strip()):
            continue
        datos, total = leer_hoja(wb[sh], doc, sh)
        if datos:
            libro[int(sh.strip())] = (datos, total)
    wb.close()
    return libro


def elegir(urls, destino, refrescar):
    """Entre los candidatos de una ranura se queda con el que trae mas anios con datos."""
    mejor = None
    for url in urls:
        nombre = url.rsplit("/", 1)[-1]
        crudo = bajar(url, destino, nombre, refrescar)
        if crudo is None:
            continue
        libro = leer_libro(crudo, nombre)
        con_datos = sum(1 for _a, (d, _t) in libro.items()
                        if any(v for reg in d.values() for v in reg.values()))
        if mejor is None or (con_datos, len(libro)) > (mejor[2], len(mejor[1])):
            mejor = (nombre, libro, con_datos)
    return mejor


def anios_vacios(libro, doc):
    """Anios en que TODOS los ingenios estan en cero: la fuente no publico la apertura ese anio.

    Pasa con el alcohol entre 1995 y 2006 (de 2000 a 2006 queda un total pais suelto en una columna
    aparte) y con 2021 en el libro viejo, que si trae el nuevo. Un cero no es un dato: esos anios
    no se emiten.
    """
    vacios = set()
    for a, (d, _t) in libro.items():
        if not any(v for reg in d.values() for v in reg.values()):
            vacios.add(a)
    if vacios:
        inc("%s: %d anios sin apertura por ingenio (todo en cero), no se emiten: %s"
            % (doc, len(vacios), ", ".join(str(x) for x in sorted(vacios))))
    return vacios


# ---------------------------------------------------------------- verificaciones


def verif_cierre_vertical(libro, doc):
    """Suma de ingenios contra la fila TOTAL publicada en cada hoja, columna por columna."""
    malas = 0
    for a in sorted(libro):
        datos, total = libro[a]
        for met, tot in total.items():
            if met == "rendimiento_fuente_pct":
                continue
            s = sum(reg.get(met, 0.0) for reg in datos.values())
            if abs(s - tot) > max(1.0, abs(tot) * 1e-6):
                malas += 1
                inc("%s %d: %s suma %.1f y la fila TOTAL dice %.1f (dif %.1f)"
                    % (doc, a, met, s, tot, s - tot))
    print("   cierre vertical %s: %d hojas, %d desvios" % (doc, len(libro), malas))


def verif_cierre_horizontal(libro, doc):
    """crudo + blanco + refinado + organico = total (o blanco + crudo = total en el libro viejo)."""
    partes = ["azucar_crudo_t", "azucar_blanco_t", "azucar_refinado_t", "azucar_organico_t"]
    malas = n = 0
    for a in sorted(libro):
        datos, _t = libro[a]
        for (prov, ing), reg in datos.items():
            if "azucar_total_t" not in reg or not any(p in reg for p in partes):
                continue
            n += 1
            s = sum(reg.get(p, 0.0) for p in partes)
            if abs(s - reg["azucar_total_t"]) > 1.0:
                malas += 1
                inc("%s %d %s/%s: partes suman %.1f y el total dice %.1f"
                    % (doc, a, prov, ing, s, reg["azucar_total_t"]))
    print("   cierre horizontal %s: %d filas, %d desvios" % (doc, n, malas))


def verif_plausible(libro, doc):
    """Azucar sobre cana por encima de lo que la cana puede dar.

    La cana tiene del orden del 12 % de sacarosa y el azucar efectivamente recuperado nunca llega
    a eso. Un cociente mayor no es un rendimiento alto: es un numero mal cargado.
    """
    malas = 0
    for a in sorted(libro):
        for (prov, ing), reg in libro[a][0].items():
            az, cana = reg.get("azucar_total_t"), reg.get("cana_molida_t")
            if az and cana and az / cana > 0.13:
                malas += 1
                inc("%s %d %s/%s: %.0f t de azucar sobre %.0f t de cana es %.1f %%, imposible"
                    % (doc, a, prov, ing, az, cana, 100.0 * az / cana))
    print("   azucar sobre cana %s: %d filas imposibles" % (doc, malas))


def verif_cotejo(nuevo, viejo, etiqueta, detalle=False):
    """Celda por celda en los anios superpuestos. Documenta en que difieren los dos libros.

    Las diferencias se resumen por anio y metrica, porque la mayor parte es sistematica: el libro
    nuevo informa cana molida BRUTA y el viejo cana neta, asi que en 2016 y 2018 difieren casi
    todos los ingenios en el mismo sentido. Se detallan una por una las de Salta -- la provincia
    del tablero -- y todas las que no son de cana, que si son sustantivas.
    """
    comunes = sorted(set(nuevo) & set(viejo))
    grupos = collections.defaultdict(list)
    for a in comunes:
        dn, dv = nuevo[a][0], viejo[a][0]
        for clave in sorted(set(dn) | set(dv)):
            rn, rv = dn.get(clave, {}), dv.get(clave, {})
            for met in sorted(set(rn) | set(rv)):
                if met in ("rendimiento_fuente_pct", "azucar_tmcv_t"):
                    continue
                x, y = rn.get(met), rv.get(met)
                if x is None or y is None:
                    if (x or 0) != (y or 0):
                        grupos[(a, met)].append((clave, x, y))
                elif abs(x - y) > 1.0:
                    grupos[(a, met)].append((clave, x, y))
    difs = sum(len(v) for v in grupos.values())
    for (a, met), casos in sorted(grupos.items()):
        sueltos = [c for c in casos if c[0][0] == "Salta" or met != "cana_molida_t" or detalle]
        if len(casos) > len(sueltos):
            inc("cotejo %s %d %s: difieren %d ingenios (el libro nuevo informa cana BRUTA y el "
                "historico cana neta)" % (etiqueta, a, met, len(casos) - len(sueltos)))
        for (prov, ing), x, y in sueltos:
            inc("cotejo %s %d %s/%s %s: nuevo %s, viejo %s"
                % (etiqueta, a, prov, ing, met,
                   "%.1f" % x if x is not None else "-", "%.1f" % y if y is not None else "-"))
    salta = sum(1 for (a, met), casos in grupos.items() for c in casos
                if c[0][0] == "Salta" and met != "cana_molida_t")
    rango = "%d-%d" % (comunes[0], comunes[-1]) if comunes else "-"
    print("   cotejo %s: %d anios superpuestos (%s), %d celdas distintas; en Salta, %d fuera de "
          "la cana molida" % (etiqueta, len(comunes), rango, difs, salta))


def verif_rendimiento(datos):
    """El 'Rendimiento %' de la fuente contra azucar/cana, y cuanto falta para cerrarlo.

    Si el rendimiento fuera azucar fisico sobre cana, Tabacal 2025 daria 1,1 % y la planilla dice
    10 %. La hipotesis es que incluye el azucar EQUIVALENTE de la cana desviada a alcohol. Esta
    verificacion despeja, en los casos con alcohol, cuantas toneladas de azucar equivalente por m3
    de alcohol hacen falta para cerrar la cuenta. Si el valor fuera estable y cercano a 1,4-1,5
    t/m3 (la equivalencia tecnica habitual), la hipotesis quedaria confirmada. NO LO ES: se dispersa
    demasiado, asi que la definicion del rendimiento de la fuente queda sin establecer y el
    indicador NO se usa en el tablero, que calcula su propio azucar por tonelada de cana.
    """
    ks, brechas = [], 0
    for (_a, _prov, _ing), reg in datos.items():
        r = reg.get("rendimiento_fuente_pct")
        cana = reg.get("cana_molida_t")
        az = reg.get("azucar_total_t")
        if not r or not cana or az is None:
            continue
        equiv = r / 100.0 * cana
        alc = reg.get("alcohol_m3") or 0.0
        if abs(equiv - az) > max(500.0, az * 0.02):
            brechas += 1
            if alc > 100:
                ks.append((equiv - az) / alc)
    if ks:
        ks.sort()
        med = ks[len(ks) // 2]
        inc("rendimiento_fuente_pct: en %d filas no es azucar sobre cana. La brecha acompana a la "
            "produccion de alcohol, pero la equivalencia implicita se dispersa (mediana %.2f t de "
            "azucar por m3, entre %.2f y %.2f en %d casos), asi que la definicion del indicador "
            "queda sin establecer. Se publica tal como lo informa la fuente y el tablero no lo usa."
            % (brechas, med, ks[0], ks[-1], len(ks)))


def saltos_de_magnitud(datos):
    """Saltos anio a anio por serie (ingenio x metrica). Firma tipica de un parseo mal hecho."""
    series = collections.defaultdict(dict)
    for (a, prov, ing), reg in datos.items():
        for met in ("cana_molida_t", "azucar_total_t", "alcohol_m3"):
            if reg.get(met):
                series[(prov, ing, met)][a] = reg[met]
    n = 0
    for (prov, ing, met), d in sorted(series.items()):
        ys = sorted(d)
        for x, y in zip(ys, ys[1:]):
            if y != x + 1:
                continue
            a, b = d[x], d[y]
            if max(a, b) < 50000:          # a esta escala un salto grande no dice nada
                continue
            if b / a > 3 or b / a < 0.34:
                n += 1
                inc("salto %s/%s %s: %d->%d  %.0f -> %.0f (x%.2f)"
                    % (prov, ing, met, x, y, a, b, b / a))
    print("   saltos de orden de magnitud: %d" % n)


def verif_control(datos, pais):
    """Valores de control tomados a mano de las planillas y de un parte del IPAAT."""
    pruebas = [
        ((2024, "Salta", "San Isidro"), "cana_molida_t", 683063),
        ((2025, "Salta", "San Isidro"), "cana_molida_t", 729127),
        ((2024, "Salta", "San Isidro"), "azucar_total_t", 60585),
        ((2025, "Salta", "San Isidro"), "azucar_organico_t", 56878),
        ((2025, "Salta", "Tabacal"), "azucar_total_t", 19984),
        ((2025, "Salta", "Tabacal"), "alcohol_m3", 115158.756),
        ((1990, "Salta", "San Isidro"), "azucar_total_t", 118010),
    ]
    ok = 0
    for clave, met, esperado in pruebas:
        v = datos.get(clave, {}).get(met)
        if v is not None and abs(v - esperado) < 0.01:
            ok += 1
        else:
            inc("control %s %s: esperaba %s y dio %s" % (clave, met, esperado, v))
    for a, met, esperado in [(2025, "azucar_total_t", 1761438), (2025, "cana_molida_t", 25095271)]:
        v = pais.get((a, met))
        if v is not None and abs(v - esperado) < 1:
            ok += 1
        else:
            inc("control pais %d %s: esperaba %s y dio %s" % (a, met, esperado, v))
    print("   valores de control: %d/%d exactos" % (ok, len(pruebas) + 2))


# ---------------------------------------------------------------- armado


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=RAIZ)
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "caa_sucroalcoholero"))
    ap.add_argument("--refrescar", action="store_true")
    ap.add_argument("--detalle-cotejo", action="store_true",
                    help="lista una por una las diferencias de cana entre los dos libros")
    args = ap.parse_args()

    print("1. Planillas publicadas en centroazucarero.com.ar")
    cands = descubrir_planillas(args.fuentes, args.refrescar)
    libros = {}
    for ranura in sorted(RANURAS):
        urls = cands.get(ranura) or []
        if len(urls) > 1:
            print("   %s: %d candidatos" % ("/".join(ranura), len(urls)))
        elegido = elegir(urls, args.fuentes, args.refrescar)
        if elegido is None:
            sys.exit("No se pudo leer ninguna planilla para %s" % ("/".join(ranura),))
        nombre, libro, _ = elegido
        libros[ranura] = (nombre, libro)
        ys = sorted(libro)
        print("   %-18s %-44s %d-%d (%d hojas)"
              % ("/".join(ranura), nombre, ys[0], ys[-1], len(ys)))

    print()
    print("2. Verificaciones de cada libro")
    vacios = {}
    for ranura, (nombre, libro) in sorted(libros.items()):
        verif_cierre_vertical(libro, nombre)
        if ranura[0] == "azucar":
            verif_cierre_horizontal(libro, nombre)
            verif_plausible(libro, nombre)
        vacios[ranura] = anios_vacios(libro, nombre)

    print()
    print("3. Cotejo entre el libro nuevo y el historico")
    for prod in ("azucar", "alcohol"):
        nuevo = {a: v for a, v in libros[(prod, "nuevo")][1].items()
                 if a not in vacios[(prod, "nuevo")]}
        viejo = {a: v for a, v in libros[(prod, "historico")][1].items()
                 if a not in vacios[(prod, "historico")]}
        verif_cotejo(nuevo, viejo, prod, args.detalle_cotejo)

    print()
    print("4. Armado del dataset")
    # (anio, provincia, ingenio) -> {metrica: valor}; y la procedencia de cada celda.
    datos = collections.defaultdict(dict)
    origen = {}
    incoherentes = []
    anios_nuevo_azucar = set(libros[("azucar", "nuevo")][1])
    for prod in ("azucar", "alcohol"):
        for epoca, calidad in (("nuevo", "definitivo"), ("historico", "historico")):
            nombre, libro = libros[(prod, epoca)]
            for a in sorted(libro):
                if a in vacios[(prod, epoca)]:
                    continue
                regs = libro[a][0]
                for (prov, ing), reg in regs.items():
                    clave = (a, prov, ing)
                    for met, v in reg.items():
                        if met in datos[clave]:
                            continue          # manda el libro nuevo, que se recorre primero
                        # El TMCV (azucar total expresado en valor crudo) solo lo publica el libro
                        # historico, asi que la serie termina donde empieza el nuevo. Arrastrarlo
                        # mas alla mezclaria los dos libros en la misma celda: en 2024 el TMCV
                        # historico de Ledesma (620.467 t) acompana a un azucar de 593.287 t que
                        # esta mal -- es el 17 % de la cana, imposible -- y que el libro nuevo
                        # corrige a 249.893 t.
                        if met == "azucar_tmcv_t" and a in anios_nuevo_azucar:
                            incoherentes.append(clave)
                            continue
                        datos[clave][met] = v
                        origen[(clave, met)] = (calidad, nombre)

    # El rendimiento viene como fraccion (0,09) y se publica en porcentaje.
    for reg in datos.values():
        if "rendimiento_fuente_pct" in reg:
            r = reg["rendimiento_fuente_pct"]
            reg["rendimiento_fuente_pct"] = round(r * 100.0, 2) if abs(r) <= 1.5 else round(r, 2)

    anios = sorted({a for (a, _p, _i) in datos})
    print("   %d anios (%d-%d), %d combinaciones anio x ingenio"
          % (len(anios), anios[0], anios[-1], len(datos)))
    if incoherentes:
        ys = sorted({a for (a, _p, _i) in incoherentes})
        inc("azucar_tmcv_t: serie disponible hasta %d. Se omiten %d celdas de %d-%d, donde el "
            "libro nuevo es la fuente del azucar y no publica TMCV."
            % (ys[0] - 1, len(incoherentes), ys[0], ys[-1]))

    verif_rendimiento(datos)
    saltos_de_magnitud(datos)

    # ---- agregados: provincia, NOA y total del pais ----------------------------
    agreg = collections.defaultdict(float)
    for (a, prov, _ing), reg in datos.items():
        for met, v in reg.items():
            if met not in ADITIVAS:
                continue
            agreg[(a, prov, TOTAL_ING, met)] += v
            agreg[(a, TOTAL_PAIS, TOTAL_ING, met)] += v
            if prov in PROV_NOA:
                agreg[(a, NOA, TOTAL_ING, met)] += v

    # El total del pais es la SUMA de los ingenios, no la fila TOTAL publicada. Desde 2016 el libro
    # nuevo solo trae los 20 ingenios del NOA, asi que su fila TOTAL deja afuera a los tres del
    # Litoral que el dataset si conserva (los aporta el libro historico): tomarla romperia la
    # identidad pais = NOA + Litoral. Cada fila TOTAL publicada ya quedo verificada contra su
    # propio libro en `verif_cierre_vertical`; aca se controla que la identidad cierre.
    desvios = n = 0
    for (a, prov, _i, met), v in sorted(agreg.items()):
        if prov != TOTAL_PAIS:
            continue
        n += 1
        partes = sum(agreg.get((a, p, TOTAL_ING, met), 0.0) for p in (NOA, "Litoral"))
        if abs(partes - v) > 1.0:
            desvios += 1
            inc("total pais %d %s: %.1f, y NOA + Litoral suman %.1f" % (a, met, v, partes))
    print("   total del pais: %d celdas, %d no cierran contra NOA + Litoral" % (n, desvios))

    pais = {(a, met): v for (a, prov, _i, met), v in agreg.items() if prov == TOTAL_PAIS}
    verif_control(datos, pais)

    # ---- filas ------------------------------------------------------------------
    def fila(a, prov, ing, met, v, calidad, doc):
        return {"anio": a, "provincia": prov, "departamento": DEPARTAMENTO.get(ing, ""),
                "ingenio": ing, "metrica": met,
                "valor": ("%d" % round(v)) if abs(v - round(v)) < 1e-9 else ("%.3f" % v),
                "calidad": calidad, "fuente_doc": doc}

    filas = []
    for (a, prov, ing), reg in datos.items():
        for met, v in reg.items():
            calidad, doc = origen[((a, prov, ing), met)]
            if prov == "Salta" and a <= SALTA_DUDOSO_HASTA:
                calidad = "rotulo_dudoso"
            filas.append(fila(a, prov, ing, met, v, calidad, doc))
    n_dudoso = sum(1 for f in filas if f["calidad"] == "rotulo_dudoso")
    inc("Salta 1990-%d: %d filas por ingenio marcadas 'rotulo_dudoso'. La fuente intercambia San "
        "Isidro y Tabacal en ese tramo (ver la metodologia). El total provincial no esta afectado."
        % (SALTA_DUDOSO_HASTA, n_dudoso))

    for (a, prov, ing, met), v in agreg.items():
        calidad, doc = origen.get(((a, prov, ing), met), ("derivado", ""))
        filas.append(fila(a, prov, ing, met, v, calidad, doc))

    orden_p = {p: i for i, p in enumerate(["Salta", "Jujuy", "Tucumán", "Litoral", NOA,
                                           TOTAL_PAIS])}
    orden_m = {m: i for i, m in enumerate(METRICAS)}
    filas.sort(key=lambda f: (orden_p.get(f["provincia"], 99), f["ingenio"] != TOTAL_ING,
                              f["ingenio"], orden_m.get(f["metrica"], 99), int(f["anio"])))
    print()
    escribir_csv(os.path.join(args.salida, SALIDA), CAMPOS, filas)

    print()
    if incidencias:
        print("Incidencias (%d):" % len(incidencias))
        for x in incidencias[:60]:
            print("  -", x)
        if len(incidencias) > 60:
            print("  ... y %d mas" % (len(incidencias) - 60))
    else:
        print("Sin incidencias detectadas.")


if __name__ == "__main__":
    main()
```
