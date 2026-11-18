# Actualización — Siniestralidad vial por jurisdicción (ANSV)

Regenera la serie anual de siniestralidad vial para las 24 jurisdicciones argentinas, más el total
del país y el NOA, a partir de los anuarios estadísticos y los informes preliminares del
Observatorio Vial Nacional de la Agencia Nacional de Seguridad Vial:

- <https://www.argentina.gob.ar/seguridadvial/observatoriovialnacional/anuarios> (2016 a 2022)
- <https://www.argentina.gob.ar/seguridadvial/observatoriovialnacional/ano-2026> (2023 a 2026)

> **Todo es PDF.** La ANSV no publica CSV, ni XLSX, ni datos abiertos, y no tiene ficha en
> datos.gob.ar. Pero son PDF de texto nativo, no escaneos: las tablas se leen con `pdfplumber` sin
> OCR. Es la única dependencia fuera de la biblioteca estándar.

> **Las tablas se buscan por título, nunca por número.** La numeración cambia todos los años: la
> tabla de tipo de usuario es la 8 en 2017, la 10 en 2018, la 49 en 2019, la 19 en 2020 y 2021 y la
> 15 en 2022. Si la ANSV renumera, el script sigue funcionando; si **retitula**, avisa con una
> incidencia «no se encontró la tabla» en vez de leer cualquier cosa.

> **La cobertura es desigual y eso es lo primero que hay que mirar.** La única serie sin huecos es
> víctimas fatales con su tasa de mortalidad, 2016–2025. Los siniestros fatales no están abiertos
> por jurisdicción en 2025, y el tipo de usuario por provincia se corta en 2022. La sección E de la
> salida imprime la matriz de cobertura completa.

> **El parcial 2026 es enero–septiembre y le falta CABA.** Entra al CSV marcado `calidad=parcial`;
> el tablero del Monitor lo excluye de los gráficos.

> **`Capital Federal` se emite como `CABA`.** La ANSV ya usa CABA, pero el diccionario contempla la
> denominación vieja por si reaparece.

Metodología y verificaciones: `Metodologia_Seguridad_Vial_ANSV.md`.

## Qué genera (en `datos-drive/`)

| Archivo | Base de origen | Período | Dimensiones propias |
|---|---|---|---|
| `Siniestralidad_vial_ANSV_jurisdiccion_anual.csv` | 10 PDF del Observatorio Vial Nacional | 2016 → 2026 | `jurisdiccion` (26), `tipo_usuario` (7), `metrica` (11) |

Cierra en `metrica, valor`, el esquema canónico del Monitor, más dos columnas de trazabilidad.

```
anio,jurisdiccion,tipo_usuario,metrica,valor,calidad,fuente_doc
2022,Salta,Total,victimas_fatales,151,definitivo,a2022 p40; a2022 p43
2022,Salta,Total,tasa_mortalidad_100mil,10.3,definitivo,a2022 p40
2022,Salta,Motociclista,victimas_fatales,63,definitivo,a2022 p47
```

`tipo_usuario` es un **margen**: la fila `Total` es la suma de las otras seis, no una categoría más.
Todo gráfico tiene que fijar esta dimensión o va a duplicar el total.

## 1. Requisitos

```
pip install pdfplumber
```

Nada más. La descarga usa `urllib` de la biblioteca estándar. No hace falta `pandas`, ni `openpyxl`,
ni `poppler`.

## 2. Correr el script

```
python actualizar_seguridad_vial_ansv.py
```

| Argumento | Para qué |
|---|---|
| `--salida DIR` | Carpeta de salida. Por defecto, `datos-drive/` |
| `--fuentes DIR` | Caché de los PDF originales. Por defecto, `datos-drive/fuentes/ansv_seguridad_vial/` |
| `--refrescar` | Vuelve a bajar los 10 PDF, incluso los cacheados |

La primera corrida baja unos 20 MB. Las siguientes leen de la caché y tardan menos de un minuto.

## 3. Cuándo hay que tocar el script

Esta fuente no se actualiza sola: cada año aparece **un documento nuevo, con otro nombre de
archivo**. Hay que agregarlo a mano en dos lugares.

1. **`DOCS`** — la clave, la URL y la calidad (`definitivo` para un anuario, `preliminar` para un
   informe de siniestralidad fatal, `parcial` para un acumulado de meses).
2. **`SPECS`** — una línea por tabla, con el título exacto y el significado de cada columna.

Para escribir las columnas conviene mirar antes la tabla nueva: el encabezado de estos PDF viene
partido en tres renglones y **no se puede leer de forma confiable**. Lo que fija el orden de las
columnas es el **control de cierre**, que exige que la suma de los componentes dé la columna TOTAL.
Si el orden declarado está mal, la corrida lo dice.

Dos cambios de la fuente que ya ocurrieron y que conviene esperar de nuevo:

- **El informe preliminar adelgaza cada año.** 27 páginas en 2023, 21 en 2024, 13 en 2025. El de
  2024 dejó de publicar la tasa cada 10 mil vehículos, y el de 2025 dejó de abrir los siniestros
  fatales por jurisdicción. Si una tabla desaparece, hay que sacar su línea de `SPECS`.
- **La taxonomía de tipo de usuario cambió en 2019**, de seis categorías a nueve. Por eso hay dos
  constructores, `usuario_viejo` y `usuario_nuevo`, que mapean a la misma taxonomía común de seis.
  Un tercer cambio necesitaría un tercer constructor, no tocar el resto.

## 4. Verificar antes de dar por buena la actualización

La salida está dividida en secciones. Lo que hay que mirar, en orden:

**C. Verificaciones.**

- **`celdas leidas en mas de un documento: N; discrepancias: 0`.** Es el control más fuerte que
  tiene esta fuente: el anuario 2022 trae la serie 2017-2022, el 2019 trae 2008-2019 y el 2018 trae
  2016-2018, así que cientos de celdas se leen dos veces en documentos distintos. Hoy son **349
  celdas con 0 discrepancias**. Una discrepancia significa que el script se corrió una columna en
  alguna tabla.
- **`suma de jurisdicciones vs. total publicado`.** Hoy, desvío máximo 10 sobre 6 casos, en series
  de miles. Es el redondeo que la propia ANSV declara por los factores de ajuste.
- **`despejado vs. publicado`**, una línea por denominador. Los denominadores del NOA se despejan
  de las tasas provinciales publicadas, no se toman de la tabla; esta comparación dice cuánto ruido
  mete despejar y, de paso, detecta cuándo la ANSV calculó sus tasas con una edición del
  denominador distinta de la que tabula. Hoy: población 0,15 % sobre el agregado del NOA (ruido de
  redondeo), parque vehicular 3,00 %, concentrado en **2020**, que sale como incidencia nominada.
  Cualquier año que se separe más de 2 % se reporta.

**B. Tablas.** Las 42 tablas tienen que leer **25 filas** (24 jurisdicciones y el total). Las trece
que declaran cierre tienen que decir `cierra`, nunca `CIERRE MAL`. Ese control es el que fija el
orden de las columnas: el encabezado de estos PDF no es confiable y el anuario 2019 llega a poner
el total en la primera columna donde los demás lo ponen en la última.

**D. Agregados.** `NOA contra la tabla por region publicada` compara el NOA calculado con el que la
ANSV publica por región: **2019 = 935 y 2022 = 887**.

**E. Cobertura.** La matriz por métrica y año. Un año que desaparece de una fila es una tabla que
dejó de encontrarse.

**Incidencias.** Hoy son **cinco**: los heridos del total del país en 2017 (Buenos Aires y CABA no
abren su total), el parque vehicular de 2020 (la ANSV publica una tabla que no reproduce sus
propias tasas de ese año) y tres saltos de magnitud, abajo. Las cinco están explicadas en la
metodología; una sexta hay que investigarla antes de publicar.

**F. Saltos de magnitud.** Hoy hay **tres, y los tres son reales** (Córdoba en siniestros con
víctimas 2019-2020, Mendoza y Santa Cruz en personas heridas): son cambios de cobertura del
organismo provincial que reporta, no errores de parseo. Están explicados en la metodología. Uno
nuevo hay que investigarlo antes de publicar.

**Valores de control.** Salta: 212 víctimas fatales en 2016 (tasa 15,7); 219 en 2018, con 97
motociclistas y 11 ciclistas; 151 en 2022, con 136 siniestros fatales, 63 motociclistas y 13
ciclistas; 173 en 2023 con 154 siniestros fatales; 130 en 2025. Total del país: 4.711 víctimas
fatales en 2022 y 4.060 en 2025.

## 5. Copiar al sitio

El adapter del Monitor lee de `sitio-indicadores/datos/`, no de `datos-drive/`:

```
copy datos-drive\Siniestralidad_vial_ANSV_jurisdiccion_anual.csv sitio-indicadores\datos\
```

Después, `python build.py` en `sitio-indicadores/`.

## Script completo

`actualizar_seguridad_vial_ansv.py`, md5 `eeb14661d7cce66bc42a780425c40be7`.

```python
# -*- coding: utf-8 -*-
"""
Siniestralidad vial por jurisdiccion (ANSV) -- base anual.

Genera `Siniestralidad_vial_ANSV_jurisdiccion_anual.csv` a partir de los anuarios estadisticos y
los informes preliminares de siniestralidad fatal que publica el Observatorio Vial Nacional de la
Agencia Nacional de Seguridad Vial:

    https://www.argentina.gob.ar/seguridadvial/observatoriovialnacional/anuarios
    https://www.argentina.gob.ar/seguridadvial/observatoriovialnacional/ano-2026

TODO ES PDF
    La ANSV no publica CSV, ni XLSX, ni datos abiertos: no hay ficha en datos.gob.ar y las paginas
    del Observatorio solo ofrecen PDF. Pero son PDF de texto nativo, no escaneos, asi que las
    tablas se leen con `pdfplumber` sin OCR.

POR QUE HAY UN EXTRACTOR POR TABLA Y NO UNO GENERICO
    Los once documentos tienen cuatro layouts distintos y la numeracion de las tablas cambia todos
    los anios. Por eso cada tabla se declara en SPECS con su titulo exacto y el significado de cada
    columna, y se la localiza POR TITULO, nunca por numero de tabla ni por numero de pagina.

    De ese catalogo salen dos controles que son los que sostienen al dataset:
      1. CIERRE DE FILA. En las tablas con apertura (tipo de usuario, gravedad) la suma de los
         componentes tiene que dar la columna TOTAL. Es lo que confirma el orden de las columnas,
         que en varios PDF viene con el encabezado partido en tres renglones y no se puede leer de
         forma confiable.
      2. RELECTURA. Las mismas celdas aparecen en documentos distintos: el anuario 2022 trae la
         serie 2017-2022 de siniestros y victimas fatales, que repite lo que ya publicaron los
         anuarios de cada anio; el anuario 2019 trae la serie 2008-2019. Cada celda leida dos
         veces se compara, y una discrepancia es incidencia.

QUE SE EMITE Y QUE NO
    Se emite lo que la ANSV publica por jurisdiccion. NO se emiten tasas que el propio dataset
    permite derivar (morbilidad, siniestralidad con lesionados), entre otras cosas porque el
    anuario 2020 publica la de lesionados corrida un factor 10 -- ver Metodologia, seccion de
    incidencias de la fuente. Tampoco se emite la serie 2008-2015, que el anuario 2019 marca como
    provisoria o parcial en seis jurisdicciones.

AGREGADOS QUE CALCULA EL SCRIPT
    `Total del pais` se TOMA de la fila publicada, nunca se suma; la suma se usa solo para
    verificar. `NOA` se calcula: en absolutos como suma de las seis provincias, y en tasas como
    cociente de agregados (suma de numeradores sobre suma de poblaciones), nunca como promedio de
    las seis tasas provinciales.

Formato de salida (convencion del repo): decimal '.', sin separador de miles, CSV con ',',
UTF-8 con BOM.

Correr:  python actualizar_seguridad_vial_ansv.py [--salida DIR] [--fuentes DIR] [--refrescar]
"""

import argparse
import collections
import csv
import datetime
import os
import re
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import pdfplumber
except ImportError:
    raise SystemExit("falta pdfplumber:  pip install pdfplumber")

RAIZ = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "CESS-Salta-indicadores/1.0 (indicadores PDES 2030)"}

SALIDA = "Siniestralidad_vial_ANSV_jurisdiccion_anual.csv"
CAMPOS = ["anio", "jurisdiccion", "tipo_usuario", "metrica", "valor", "calidad", "fuente_doc"]

SITIO = "https://www.argentina.gob.ar/sites/default/files/"

# clave -> (url, calidad). La calidad viaja a cada celda que sale del documento.
DOCS = {
    "a2017": (SITIO + "ansv_anuario_obs_2017.pdf", "definitivo"),
    "a2018": (SITIO + "ansv_anuario2018_v3.pdf", "definitivo"),
    "a2019": (SITIO + "2018/12/ansv_ov_anuario_estadistico_2019_actualizado_mayo_2022.pdf",
              "definitivo"),
    "a2020": (SITIO + "2018/12/anuario_estadistico_2020.pdf", "definitivo"),
    "a2021": (SITIO + "2018/12/anuario_estadistico_2021.pdf", "definitivo"),
    "a2022": (SITIO + "2025/06/anuario_de_siniestralidad_vial_2022.pdf", "definitivo"),
    "p2023": (SITIO + "2025/06/informe_preliminar_de_siniestralidad_fatal_2023_abril_2026.pdf",
              "preliminar"),
    "p2024": (SITIO + "2025/06/informe_preliminar_de_siniestralidad_fatal_2024_abril_2026.pdf",
              "preliminar"),
    "p2025": (SITIO + "2025/06/informe_preliminar_de_siniestralidad_fatal_2025_abril_2026.pdf",
              "preliminar"),
    "p2026": (SITIO + "informe_preliminar_de_siniestralidad_fatal_enero-septiembre_2026.pdf",
              "parcial"),
}

# Variantes con que cada documento escribe el nombre de la jurisdiccion. Una etiqueta que no este
# aca no se lee: si aparece con numeros al lado, es incidencia. "Capital Federal" sale como CABA,
# que es la denominacion vigente.
JURISDICCIONES = [
    ("Buenos Aires", "Buenos Aires"),
    ("CABA", "CABA"),
    ("Capital Federal", "CABA"),
    ("Ciudad Autónoma de Buenos Aires", "CABA"),
    ("Catamarca", "Catamarca"),
    ("Chaco", "Chaco"),
    ("Chubut", "Chubut"),
    ("Córdoba", "Córdoba"),
    ("Corrientes", "Corrientes"),
    ("Entre Ríos", "Entre Ríos"),
    ("Formosa", "Formosa"),
    ("Jujuy", "Jujuy"),
    ("La Pampa", "La Pampa"),
    ("La Rioja", "La Rioja"),
    ("Mendoza", "Mendoza"),
    ("Misiones", "Misiones"),
    ("Neuquén", "Neuquén"),
    ("Río Negro", "Río Negro"),
    ("Salta", "Salta"),
    ("San Juan", "San Juan"),
    ("San Luis", "San Luis"),
    ("Santa Cruz", "Santa Cruz"),
    ("Santa Fe", "Santa Fe"),
    ("Santiago del Estero", "Santiago del Estero"),
    ("S. del Estero", "Santiago del Estero"),
    ("Sgo. del Estero", "Santiago del Estero"),
    ("Tierra del Fuego", "Tierra del Fuego"),
    ("T. del Fuego", "Tierra del Fuego"),
    ("Tucumán", "Tucumán"),
    ("TOTAL PAÍS", "Total del país"),
    ("TOTAL PAIS", "Total del país"),
    ("Total país", "Total del país"),
    ("Total pais", "Total del país"),
    ("Totales", "Total del país"),
    ("TOTAL", "Total del país"),
    ("Total", "Total del país"),
]
# Primero las mas largas, para que "Santiago del Estero" gane sobre "Santiago" y "Total país"
# sobre "Total".
JURISDICCIONES.sort(key=lambda kv: -len(kv[0]))

TOTAL_PAIS = "Total del país"
PROVINCIAS = sorted({c for _, c in JURISDICCIONES} - {TOTAL_PAIS})

# La ANSV agrupa en Centro / Cuyo / NEA / NOA / Patagonia. Su NOA son estas seis, verificado
# contra las tablas de victimas fatales por region del anuario 2019 (2008-2019) y del 2022
# (2017-2022). Coincide con la agrupacion que ya usa el tema `gobierno` del Monitor.
NOA = ["Catamarca", "Jujuy", "La Rioja", "Salta", "Santiago del Estero", "Tucumán"]

TOTAL_USUARIO = "Total"
USUARIOS = ["Motociclista", "Automóvil", "Peatón", "Ciclista", "Otros vehículos", "Sin dato"]

METRICAS = [
    "victimas_fatales",
    "siniestros_fatales",
    "siniestros_con_victimas",
    "siniestros_con_lesionados",
    "personas_heridas",
    "tasa_mortalidad_100mil",
    "tasa_fatalidad_10mil_veh",
    "tasa_siniestralidad_fatal_100mil",
    "tasa_siniestralidad_fatal_10mil_veh",
    "poblacion",
    "parque_vehicular",
]
ORDEN_METRICA = {m: i for i, m in enumerate(METRICAS)}
ES_TASA = {m for m in METRICAS if m.startswith("tasa_")}

# Signos convencionales, identicos en todos los anuarios (Tabla "Signos utilizados"):
#   .    dato no registrado          -> faltante
#   ...  dato no disponible          -> faltante
#   ///  dato que no corresponde     -> faltante
#   -    CERO ABSOLUTO               -> 0
#   *    dato provisorio (sufijo)
# El guion es cero y no faltante: confundirlos ya nos costo un error en la serie de cemento.
CERO = {"-"}
FALTANTE = {".", "..", "...", "…", "///", "//", "ND", "N/D", "nd", "s/d", "S/D",
            "–", "—", "No", "disponible", "S"}

RE_NUM = re.compile(r"^-?\d{1,3}(?:\.\d{3})*(?:,\d+)?%?$|^-?\d+(?:,\d+)?%?$")
RE_MARCA_PEGADA = re.compile(r"^(?:\*+|\(\d+\)|\d(?![\d.,]))")
RE_SOLO_MARCA = re.compile(r"^(?:\*+|\(\d+\))$")

incidencias = []
signos = collections.Counter()


def inc(msg):
    incidencias.append(msg)


# --------------------------------------------------------------------------- descarga de los PDF

def pdf_local(clave, destino, refrescar=False):
    """Ruta al PDF de `clave`, con cache permanente.

    Los documentos no se reescriben (los preliminares se reemplazan por una edicion nueva, con
    otro nombre de archivo), asi que un PDF ya bajado no se vuelve a pedir. Guardar el original es
    lo que permite explicar despues de donde salio cada celda.
    """
    url, _ = DOCS[clave]
    os.makedirs(destino, exist_ok=True)
    ruta = os.path.join(destino, url.rsplit("/", 1)[-1])
    if os.path.exists(ruta) and not refrescar:
        return ruta
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            datos = r.read()
    except Exception as e:
        inc("no se pudo bajar %s (%s): %s" % (clave, url, e))
        return None
    if not datos.startswith(b"%PDF"):
        inc("%s no devolvio un PDF" % clave)
        return None
    with open(ruta, "wb") as f:
        f.write(datos)
    return ruta


_PAGINAS = {}


def paginas(clave, destino, refrescar=False):
    """Texto de cada pagina del documento, cacheado en memoria."""
    if clave not in _PAGINAS:
        ruta = pdf_local(clave, destino, refrescar)
        if ruta is None:
            _PAGINAS[clave] = []
        else:
            with pdfplumber.open(ruta) as pdf:
                _PAGINAS[clave] = [p.extract_text() or "" for p in pdf.pages]
    return _PAGINAS[clave]


# ------------------------------------------------------------------------------ lectura de tablas

def parse_num(tok):
    """(valor, ok). `ok` es False cuando el token no es un numero ni un signo convencional."""
    t = tok.strip()
    if t in CERO:
        signos["- (cero absoluto)"] += 1
        return 0.0, True
    if t in FALTANTE:
        signos["%s (faltante)" % t] += 1
        return None, True
    t = t.rstrip("*")
    if not RE_NUM.match(t):
        return None, False
    t = t.rstrip("%").replace(".", "").replace(",", ".")
    try:
        return float(t), True
    except ValueError:
        return None, False


def partir_fila(linea):
    """(jurisdiccion, [tokens]) o (None, None) si la linea no abre con una jurisdiccion."""
    s = linea.strip()
    for var, canon in JURISDICCIONES:
        if not s.startswith(var):
            continue
        resto = s[len(var):]
        m = RE_MARCA_PEGADA.match(resto)         # "CABA1", "Córdoba*", "Total(3)"
        if m:
            resto = resto[m.end():]
        elif resto and not resto[0].isspace():   # "Salteño" no es "Salta"
            continue
        toks = [t for t in resto.split() if not RE_SOLO_MARCA.match(t)]
        return canon, toks
    return None, None


def leer_tabla(clave, titulo, n_cols, destino, refrescar=False):
    """{jurisdiccion: [valores]} de la tabla cuyo titulo empieza con `titulo`.

    Entre todas las paginas que mencionan el titulo elige la que mas filas de jurisdiccion tiene:
    asi se saltea el indice, que en el anuario 2018 repite todos los titulos en una sola pagina.
    """
    mejor, mejor_pag, mejor_n = None, None, -1
    for i, texto in enumerate(paginas(clave, destino, refrescar), 1):
        if titulo.lower() not in texto.lower():
            continue
        filas, sueltas = {}, []
        for linea in texto.split("\n"):
            jur, toks = partir_fila(linea)
            if jur is None:
                continue
            if len(toks) != n_cols:
                # Renglon de encabezado que arranca con la misma palabra ("Total siniestros ...")
                # o fila partida. Si TODOS los tokens son numeros, es una fila rota de verdad.
                if toks and all(parse_num(t)[1] for t in toks):
                    sueltas.append((jur, toks))
                continue
            vals = []
            ok = True
            for t in toks:
                v, bien = parse_num(t)
                if not bien:
                    ok = False
                    break
                vals.append(v)
            if ok and jur not in filas:
                filas[jur] = vals
        # En los informes preliminares el total del pais no es una fila: es una anotacion suelta
        # en el medio del grafico, un renglon de numeros sin etiqueta. Se adopta solo si estan las
        # 24 jurisdicciones, falta el total y el renglon tiene exactamente las columnas esperadas.
        if len(filas) == 24 and TOTAL_PAIS not in filas:
            sueltos = [t for t in sueltas if t[0] == TOTAL_PAIS]
            crudas = [l.split() for l in texto.splitlines()
                      if l.strip() and not any(c.isalpha() for c in l)]
            cand = [c for c in crudas if len(c) == n_cols and all(parse_num(t)[1] for t in c)]
            if len(cand) == 1:
                filas[TOTAL_PAIS] = [parse_num(t)[0] for t in cand[0]]
                sueltas = [t for t in sueltas if t[0] != TOTAL_PAIS]
            elif sueltos:
                sueltas = [t for t in sueltas if t[0] != TOTAL_PAIS]
        if len(filas) > mejor_n:
            mejor, mejor_pag, mejor_n = filas, i, len(filas)
            for jur, toks in sueltas:
                if jur not in filas:
                    inc("%s / %s: fila de %s con %d columnas, se esperaban %d"
                        % (clave, titulo[:40], jur, len(toks), n_cols))
    if mejor is None:
        inc("%s: no se encontro la tabla «%s»" % (clave, titulo[:60]))
        return {}, None
    return mejor, mejor_pag


# -------------------------------------------------------------------------------------- catalogo

def C(metrica, anio, usuario=TOTAL_USUARIO):
    return (metrica, anio, usuario)


def serie(metrica, anios):
    return [C(metrica, a) for a in anios]


# Columnas de las tablas de tipo de usuario. Cambian de taxonomia en 2019: hasta 2018 son seis
# categorias con el total al final, desde 2019 son nueve con el total adelante y la camioneta, el
# transporte de carga y el de pasajeros abiertos. Se mapean a una taxonomia comun de seis que
# preserva exactamente moto y bicicleta, que es lo que interesa seguir.
def usuario_viejo(anio):                 # anuarios 2017 y 2018
    return [C("victimas_fatales", anio, u) for u in
            ["Peatón", "Automóvil", "Motociclista", "Ciclista", "Otros vehículos", "Sin dato"]] + \
           [C("victimas_fatales", anio)]


def usuario_nuevo(anio):                 # anuarios 2019 a 2022
    return [C("victimas_fatales", anio)] + \
           [C("victimas_fatales", anio, u) for u in
            ["Motociclista", "Automóvil", "Peatón", "Otros vehículos", "Ciclista",
             "Otros vehículos", "Otros vehículos", "Otros vehículos", "Sin dato"]]


# doc, titulo, columnas, (idx_total, [idx_partes]) o None
SPECS = [
    # ---------------------------------------------------------------- anuario 2017 (datos 2017)
    ("a2017", "Tabla 2: Víctimas fatales totales hasta los 30 días por jurisdicción",
     [C("poblacion", 2017), C("parque_vehicular", 2017), C("victimas_fatales", 2017),
      C("tasa_mortalidad_100mil", 2017), C("tasa_fatalidad_10mil_veh", 2017)], None),
    ("a2017", "Tabla 8: Víctimas fatales hasta los 30 días según tipo de usuario",
     usuario_viejo(2017), (6, [0, 1, 2, 3, 4, 5])),
    ("a2017", "Tabla 12: Características de los siniestros viales. Siniestros según gravedad",
     [None, C("siniestros_con_lesionados", 2017), C("siniestros_fatales", 2017), None, None],
     (4, [0, 1, 2, 3])),
    ("a2017", "Tabla 11: Heridos según gravedad",
     [None, None, C("personas_heridas", 2017)], (2, [0, 1])),

    # ---------------------------------------------------------------- anuario 2018 (2016 a 2018)
    ("a2018", "Tabla 3: Evolución de las víctimas fatales hasta los 30 días",
     serie("victimas_fatales", [2016, 2017, 2018]), None),
    ("a2018", "Tabla 4: Evolución de la tasa de mortalidad por jurisdicción",
     serie("tasa_mortalidad_100mil", [2016, 2017, 2018]), None),
    ("a2018", "Tabla 5: Evolución de la tasa de fatalidad por jurisdicción",
     serie("tasa_fatalidad_10mil_veh", [2016, 2017, 2018]), None),
    ("a2018", "Tabla 2: Víctimas fatales totales hasta los 30 días por jurisdicción",
     [C("poblacion", 2018), C("parque_vehicular", 2018), C("victimas_fatales", 2018),
      C("tasa_mortalidad_100mil", 2018), C("tasa_fatalidad_10mil_veh", 2018)], None),
    ("a2018", "Tabla 10: Víctimas fatales hasta los 30 días según tipo de usuario",
     usuario_viejo(2018), (6, [0, 1, 2, 3, 4, 5])),
    ("a2018", "Tabla 17: Características de los siniestros. Siniestros según gravedad",
     [None, C("siniestros_con_lesionados", 2018), C("siniestros_fatales", 2018), None, None,
      None], (4, [0, 1, 2, 3])),
    ("a2018", "Tabla 14: Heridos según gravedad",
     [None, None, None, C("personas_heridas", 2018)], (3, [0, 1, 2])),

    # ---------------------------------------------------------------- anuario 2019 (2016 a 2019)
    ("a2019", "Tabla 36. Víctimas fatales según jurisdicción",
     [None] * 8 + serie("victimas_fatales", [2016, 2017, 2018, 2019]) + [None], None),
    ("a2019", "Tabla 35. Víctimas fatales totales y tasas de mortalidad",
     [C("poblacion", 2019), C("parque_vehicular", 2019), C("victimas_fatales", 2019),
      C("tasa_mortalidad_100mil", 2019), C("tasa_fatalidad_10mil_veh", 2019), None], None),
    ("a2019", "Tabla 22. Distribución de los siniestros con víctimas",
     [C("siniestros_con_victimas", 2019), None], None),
    ("a2019", "Tabla 49. Distribución de las VF según tipo de usuario",
     usuario_nuevo(2019), (0, [1, 2, 3, 4, 5, 6, 7, 8, 9])),
    ("a2019", "Tabla 56. Heridos según gravedad",   # acá el total va PRIMERO, no último
     [C("personas_heridas", 2019), None, None, None], (0, [1, 2, 3])),

    # ------------------------------------------------------------------------- anuario 2020
    ("a2020", "Tabla 5. Población proyectada según jurisdicción",
     [C("poblacion", 2020)], None),
    ("a2020", "Tabla 6. Parque vehicular en condiciones registrales",
     [C("parque_vehicular", 2020), None, None, None, None], None),
    ("a2020", "Tabla 8. Distribución de los siniestros fatales",
     [C("siniestros_fatales", 2020), C("tasa_siniestralidad_fatal_100mil", 2020),
      C("tasa_siniestralidad_fatal_10mil_veh", 2020)], None),
    ("a2020", "Tabla 13. Distribución de los siniestros con víctimas según gravedad",
     [C("siniestros_con_victimas", 2020), C("siniestros_fatales", 2020),
      C("siniestros_con_lesionados", 2020), None], (0, [1, 2])),
    ("a2020", "Tabla 15. Distribución de las víctimas fatales",
     [C("victimas_fatales", 2020), C("tasa_mortalidad_100mil", 2020),
      C("tasa_fatalidad_10mil_veh", 2020)], None),
    ("a2020", "Tabla 19. Distribución de las VF según tipo de usuario",
     usuario_nuevo(2020), (0, [1, 2, 3, 4, 5, 6, 7, 8, 9])),
    ("a2020", "Tabla 21. Distribución de las personas heridas",
     [C("personas_heridas", 2020), None, None], None),

    # ------------------------------------------------------------------------- anuario 2021
    ("a2021", "Tabla 6. Población proyectada según jurisdicción",
     [C("poblacion", 2021)], None),
    ("a2021", "Tabla 9. Distribución de los siniestros fatales",
     [C("siniestros_fatales", 2021), C("tasa_siniestralidad_fatal_100mil", 2021),
      C("tasa_siniestralidad_fatal_10mil_veh", 2021)], None),
    ("a2021", "Tabla 15. Distribución de las víctimas fatales",
     [C("victimas_fatales", 2021), C("tasa_mortalidad_100mil", 2021),
      C("tasa_fatalidad_10mil_veh", 2021)], None),
    ("a2021", "Tabla 19. Distribución de las VF según tipo de usuario",
     usuario_nuevo(2021), (0, [1, 2, 3, 4, 5, 6, 7, 8, 9])),
    ("a2021", "Tabla 21. Distribución de las personas heridas",
     [C("personas_heridas", 2021), None, None], None),

    # ------------------------------------------------------------------- anuario 2022 (2017-2022)
    ("a2022", "TABLA 3. SINIESTRALIDAD CON VÍCTIMAS SEGÚN CATEGORÍA DE SINIESTRO",
     [C("siniestros_con_victimas", 2022), C("siniestros_fatales", 2022),
      C("siniestros_con_lesionados", 2022), None], (0, [1, 2])),
    ("a2022", "TABLA 6. SINIESTRALIDAD FATAL SEGÚN JURISDICCIÓN",
     [C("siniestros_fatales", 2022), C("tasa_siniestralidad_fatal_100mil", 2022),
      C("tasa_siniestralidad_fatal_10mil_veh", 2022)], None),
    ("a2022", "TABLA 7. SINIESTRALIDAD FATAL SEGÚN JURISDICCIÓN Y AÑO",
     serie("siniestros_fatales", [2017, 2018, 2019, 2020, 2021, 2022]) + [None], None),
    ("a2022", "TABLA 12. VÍCTIMAS FATALES SEGÚN JURISDICCIÓN",
     [C("victimas_fatales", 2022), C("tasa_mortalidad_100mil", 2022),
      C("tasa_fatalidad_10mil_veh", 2022)], None),
    ("a2022", "TABLA 13. VÍCTIMAS FATALES SEGÚN JURISDICCIÓN Y AÑO",
     serie("victimas_fatales", [2017, 2018, 2019, 2020, 2021, 2022]) + [None], None),
    ("a2022", "TABLA 15. VÍCTIMAS FATALES SEGÚN JURISDICCIÓN Y TIPO DE USUARIO",
     usuario_nuevo(2022), (0, [1, 2, 3, 4, 5, 6, 7, 8, 9])),
    ("a2022", "TABLA 16. PERSONAS HERIDAS SEGÚN JURISDICCIÓN",
     [C("personas_heridas", 2022), None, None], None),
    ("a2022", "TABLA 21. POBLACIÓN PROYECTADA",
     [C("poblacion", 2022), None], None),
    ("a2022", "TABLA 22. COMPOSICIÓN DEL PARQUE VEHICULAR",
     [C("parque_vehicular", 2022), None, None, None], None),

    # ----------------------------------------------------- informes preliminares 2023, 2024, 2026
    ("p2023", "Siniestros fatales según jurisdicción: tasas",
     [C("siniestros_fatales", 2023), C("tasa_siniestralidad_fatal_100mil", 2023),
      C("tasa_siniestralidad_fatal_10mil_veh", 2023)], None),
    ("p2023", "Víctimas fatales según jurisdicción: tasas",
     [C("victimas_fatales", 2023), C("tasa_mortalidad_100mil", 2023),
      C("tasa_fatalidad_10mil_veh", 2023)], None),
    ("p2024", "Siniestros fatales según jurisdicción: tasas",
     [C("siniestros_fatales", 2024), C("tasa_siniestralidad_fatal_100mil", 2024)], None),
    ("p2024", "Víctimas fatales según jurisdicción: tasas",
     [C("victimas_fatales", 2024), C("tasa_mortalidad_100mil", 2024)], None),
    ("p2026", "Siniestros fatales según jurisdicción y mes",
     [C("siniestros_fatales", 2026)] + [None] * 9, None),
    ("p2026", "Víctimas fatales según jurisdicción y mes",
     [C("victimas_fatales", 2026)] + [None] * 9, None),
]

# El preliminar 2025 no es una tabla: son dos graficos de barras lado a lado, con la etiqueta de
# cada barra ubicada donde termina la barra. No hay columnas que leer, asi que se parsea por
# posicion de palabra. Ver `leer_barras_2025`.
P2025_TITULO = "Víctimas fatales según jurisdicción"


def leer_barras_2025(destino, refrescar=False):
    """{(metrica, jurisdiccion): valor} de la pagina de barras del preliminar 2025.

    La pagina tiene dos paneles de barras lado a lado -- victimas fatales a la izquierda, tasa de
    mortalidad a la derecha -- y cada barra lleva su etiqueta al final, asi que la posicion
    HORIZONTAL del numero no dice nada: lo que lo ata a su jurisdiccion es el renglon. Y el
    renglon tampoco viene dado: pdfplumber devuelve "Santiago", "del" y "Estero" como palabras
    sueltas, a veces con medio punto de diferencia vertical entre el nombre y su valor. Por eso se
    reconstruyen los renglones agrupando por coordenada vertical con tolerancia, y dentro de cada
    renglon se recorre de izquierda a derecha: la primera jurisdiccion que aparece es la del panel
    de victimas y la segunda la del panel de tasas.

    El total del pais no cuelga de ninguna barra: esta debajo de la palabra "Total", y se
    identifica por eso antes de recorrer los renglones, para que no se lo lleve una jurisdiccion.
    """
    ruta = pdf_local("p2025", destino, refrescar)
    if ruta is None:
        return {}
    with pdfplumber.open(ruta) as pdf:
        pag = None
        for p in pdf.pages:
            t = p.extract_text() or ""
            if P2025_TITULO.lower() in t.lower() and "Buenos Aires" in t:
                pag = p
                break
        if pag is None:
            inc("p2025: no se encontro la pagina de victimas fatales por jurisdiccion")
            return {}
        palabras = pag.extract_words()

    metricas = ["victimas_fatales", "tasa_mortalidad_100mil"]
    es_num = lambda w: bool(RE_NUM.match(w["text"]))
    nums = [w for w in palabras if es_num(w)]
    out, usados = {}, set()

    # El total de cada panel: el numero mas cercano por debajo de su rotulo "Total".
    for i, t in enumerate(sorted((w for w in palabras if w["text"] == "Total"),
                                 key=lambda w: w["x0"])):
        if i >= len(metricas):
            break
        cand = [w for w in nums if w["top"] > t["top"] - 2 and abs(w["x0"] - t["x0"]) < 30
                and id(w) not in usados]
        if cand:
            w = min(cand, key=lambda w: w["top"])
            usados.add(id(w))
            out[(metricas[i], TOTAL_PAIS)] = parse_num(w["text"])[0]

    # Los renglones se cortan por HUECO vertical, no por distancia a la primera palabra: dentro de
    # un renglon las palabras se desplazan hasta 6 puntos (el numero de la barra queda mas abajo
    # que el nombre), mientras que entre renglones nunca hay menos de 10.
    renglones, actual, prev = [], [], None
    for w in sorted(palabras, key=lambda w: w["top"]):
        if prev is not None and w["top"] - prev > 8:
            renglones.append(actual)
            actual = []
        actual.append(w)
        prev = w["top"]
    if actual:
        renglones.append(actual)

    for grupo in renglones:
        panel, pend = 0, []
        for w in sorted(grupo, key=lambda w: w["x0"]):
            if id(w) in usados:
                continue
            if not es_num(w):
                pend.append(w["text"])
                continue
            jur = None
            for k in range(1, len(pend) + 1):       # sufijo mas corto que matchee
                cand = partir_fila(" ".join(pend[-k:]))[0]
                if cand and cand != TOTAL_PAIS:
                    jur = cand
                    break
            pend = []
            if jur is None or jur == TOTAL_PAIS or panel >= len(metricas):
                continue
            out[(metricas[panel], jur)] = parse_num(w["text"])[0]
            panel += 1

    for metrica in metricas:
        faltan = sorted(set(PROVINCIAS) - {j for (m, j) in out if m == metrica})
        if faltan:
            inc("p2025 / %s: sin valor para %s" % (metrica, ", ".join(faltan)))
    return out


# ------------------------------------------------------------------------------- verificaciones

def verif_cierre(clave, titulo, filas, control):
    """La suma de los componentes tiene que dar la columna TOTAL.

    La ANSV avisa que los factores de ajuste que aplica a algunas jurisdicciones hacen que la suma
    de los componentes difiera del total en +/- 1. Ese desvio se cuenta y no se reporta uno por
    uno; cualquier cosa mayor es un error de lectura de columnas y si es incidencia.
    """
    it, partes = control
    malas = redondeo = sin_abrir = 0
    for jur, vals in filas.items():
        tot = vals[it]
        comp = [vals[i] for i in partes]
        if tot is None or any(v is None for v in comp):
            continue
        # Hay jurisdicciones que reportan el total y no lo abren, y la fuente escribe el guion de
        # "cero absoluto" donde correspondia el punto de "dato no registrado" (Buenos Aires y CABA
        # en los heridos de 2017). El total sigue siendo bueno, que es lo unico que se emite. Esto
        # NO tapa una lectura corrida de columnas: ahi los componentes no dan todos cero.
        if tot and not any(comp):
            sin_abrir += 1
            continue
        d = abs(sum(comp) - tot)
        if d > 1.0:
            malas += 1
            inc("%s / %s: la fila de %s no cierra (%g componentes vs %g total)"
                % (clave, titulo[:40], jur, sum(comp), tot))
        elif d > 0:
            redondeo += 1
    return malas, redondeo, sin_abrir


def verif_relectura(lecturas):
    """Celdas leidas en mas de un documento: tienen que coincidir."""
    repetidas = discrepantes = 0
    for k, obs in sorted(lecturas.items()):
        vistos = {v for v, _ in obs if v is not None}
        if len(obs) < 2:
            continue
        repetidas += 1
        if len(vistos) > 1:
            discrepantes += 1
            inc("relectura discrepante en %s %s %s %s: %s"
                % (k[0], k[1], k[3], k[2], ", ".join("%s=%s" % (o, v) for v, o in obs)))
    print("   celdas leidas en mas de un documento: %d; discrepancias: %d"
          % (repetidas, discrepantes))
    return repetidas, discrepantes


def verif_suma_pais(datos):
    """El total del pais publicado contra la suma de las 24 jurisdicciones."""
    peor, n = 0.0, 0
    for (anio, usuario, metrica), _ in sorted(
            {(a, u, m): 1 for (a, j, u, m) in datos if j == TOTAL_PAIS}.items()):
        if metrica in ES_TASA:
            continue
        tot = datos.get((anio, TOTAL_PAIS, usuario, metrica))
        comp = [datos[(anio, p, usuario, metrica)] for p in PROVINCIAS
                if (anio, p, usuario, metrica) in datos]
        if tot is None or len(comp) < 24:
            continue
        d = abs(sum(comp) - tot)
        if d > peor:
            peor = d
        n += (d > 0)
    print("   suma de jurisdicciones vs. total publicado: desvio maximo %g, %d casos con desvio"
          % (peor, n))
    if peor > 40:
        inc("la suma de las jurisdicciones se aparta del total del pais en hasta %g" % peor)
    return peor


DENOMINADORES = {
    # metrica del denominador -> (metrica base, metrica de la tasa, factor de la tasa)
    "poblacion":        ("victimas_fatales", "tasa_mortalidad_100mil", 1e5),
    "parque_vehicular": ("victimas_fatales", "tasa_fatalidad_10mil_veh", 1e4),
}
# Tasas del NOA que se calculan: metrica -> (numerador, denominador, factor)
TASAS_NOA = {
    "tasa_mortalidad_100mil":              ("victimas_fatales", "poblacion", 1e5),
    "tasa_siniestralidad_fatal_100mil":    ("siniestros_fatales", "poblacion", 1e5),
    "tasa_fatalidad_10mil_veh":            ("victimas_fatales", "parque_vehicular", 1e4),
    "tasa_siniestralidad_fatal_10mil_veh": ("siniestros_fatales", "parque_vehicular", 1e4),
}


def _despejar(datos, anio, jur, denom):
    """Denominador implicito en el par (numerador, tasa) que publica la ANSV."""
    base, tasa, factor = DENOMINADORES[denom]
    n = datos.get((anio, jur, TOTAL_USUARIO, base))
    t = datos.get((anio, jur, TOTAL_USUARIO, tasa))
    return factor * n / t if n and t else None


def verif_denominadores(datos):
    """Denominador publicado contra el que se despeja del par (numerador, tasa).

    Para agregar el NOA se usa el denominador DESPEJADO, no el publicado: el que hay que sumar es
    el que esta implicito en las tasas provinciales con las que el NOA se va a comparar en el mismo
    grafico. Usar la tabla publicada haria al NOA incomparable con Salta.

    Esta verificacion contrasta uno contra otro y avisa cuando se separan mas de 2%% sobre el
    agregado del NOA, que es como se detecta que la ANSV calculo sus tasas con una edicion del
    denominador distinta de la que tabula (le pasa al parque vehicular en 2020). El maximo por
    jurisdiccion se informa como contexto: la tasa viene redondeada a un decimal, asi que despejar
    el denominador de una jurisdiccion con pocas victimas fatales arrastra un error que al sumar
    las seis se compensa.
    """
    out = {}
    for denom in DENOMINADORES:
        peor_prov, n = 0.0, 0
        for (anio, jur, usuario, metrica), pub in sorted(datos.items()):
            if metrica != denom or usuario != TOTAL_USUARIO or not pub:
                continue
            d = _despejar(datos, anio, jur, denom)
            if d is None:
                continue
            peor_prov = max(peor_prov, abs(d - pub) / pub * 100)
            n += 1
        peor_noa, m = 0.0, 0
        for anio in sorted({a for (a, _, _, _) in datos}):
            pubs = [datos.get((anio, j, TOTAL_USUARIO, denom)) for j in NOA]
            desp = [_despejar(datos, anio, j, denom) for j in NOA]
            if not all(pubs) or not all(desp):
                continue
            err = abs(sum(desp) - sum(pubs)) / sum(pubs) * 100
            if err > 2.0:
                inc("%s de %d: el que publica la ANSV y el que esta implicito en sus propias "
                    "tasas difieren %.1f%% en el NOA" % (denom, anio, err))
            peor_noa = max(peor_noa, err)
            m += 1
        print("   %-17s despejado vs. publicado: %3d pares; peor jurisdiccion %.2f%%, "
              "agregado del NOA %.2f%% (%d anios)" % (denom, n, peor_prov, peor_noa, m))
        out[denom] = (peor_noa, m)
    return out


def denominador_por_anio(datos, anios, denom):
    """{(anio, jurisdiccion): (valor, origen)}. Despejado de la tasa publicada; publicado si no se
    puede despejar. Ver verif_denominadores: por que se prefiere el despejado."""
    out = {}
    for anio in anios:
        for jur in PROVINCIAS + [TOTAL_PAIS]:
            d = _despejar(datos, anio, jur, denom)
            if d:
                out[(anio, jur)] = (d, "despejado")
                continue
            v = datos.get((anio, jur, TOTAL_USUARIO, denom))
            if v:
                out[(anio, jur)] = (v, "publicado")
    return out


def agregar_noa(datos, denoms, con_tasa):
    """Agrega las filas del NOA. Absolutos por suma; tasas por cociente de agregados."""
    nuevos = {}
    anios = sorted({a for (a, _, _, _) in datos})
    usuarios = sorted({u for (_, _, u, _) in datos})
    for anio in anios:
        for usuario in usuarios:
            for metrica in METRICAS:
                if metrica in ES_TASA or metrica in DENOMINADORES:
                    continue
                vals = [datos.get((anio, p, usuario, metrica)) for p in NOA]
                if any(v is None for v in vals):
                    continue
                nuevos[(anio, "NOA", usuario, metrica)] = sum(vals)
        for denom, tabla in denoms.items():
            v = [tabla.get((anio, j)) for j in NOA]
            if all(v):
                nuevos[(anio, "NOA", TOTAL_USUARIO, denom)] = round(sum(x for x, _ in v))
    for anio in anios:
        for metrica, (num_m, den_m, factor) in TASAS_NOA.items():
            if not con_tasa.get(den_m):
                continue
            num = nuevos.get((anio, "NOA", TOTAL_USUARIO, num_m))
            den = nuevos.get((anio, "NOA", TOTAL_USUARIO, den_m))
            # Una tasa del NOA solo se publica si TODAS las provincias tienen el numerador ese
            # anio: si falta una, el cociente mezcla seis denominadores con cinco numeradores.
            if num is None or not den:
                continue
            if any(datos.get((anio, j, TOTAL_USUARIO, num_m)) is None for j in NOA):
                continue
            nuevos[(anio, "NOA", TOTAL_USUARIO, metrica)] = round(factor * num / den, 1)
    return nuevos


def saltos_de_magnitud(pares, etiqueta):
    """Un salto de orden de magnitud entre anios consecutivos es la firma de un separador mal
    leido. Se reporta, no se corrige."""
    ser = [(a, v) for a, v in sorted(pares) if v]
    for (a0, v0), (a1, v1) in zip(ser, ser[1:]):
        r = max(v0, v1) / min(v0, v1)
        if r >= 9.5 and a1 == a0 + 1:
            inc("salto de orden de magnitud en %s: %d=%g -> %d=%g" % (etiqueta, a0, v0, a1, v1))


def escribir_csv(ruta, campos, filas):
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print("   %s  (%d filas)" % (ruta, len(filas)))


def fmt(v):
    if v is None:
        return ""
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return ("%.4f" % v).rstrip("0").rstrip(".")


# ------------------------------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(
        description="Siniestralidad vial por jurisdiccion (ANSV)")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "ansv_seguridad_vial"),
                    help="Cache de los PDF originales")
    ap.add_argument("--refrescar", action="store_true",
                    help="Vuelve a bajar todos los PDF, incluso los cacheados")
    args = ap.parse_args()

    print("A. Documentos de la ANSV")
    for clave in DOCS:
        pg = paginas(clave, args.fuentes, args.refrescar)
        print("   %-6s %3d paginas  %s" % (clave, len(pg), DOCS[clave][0].rsplit("/", 1)[-1]))

    print("B. Tablas")
    lecturas = collections.defaultdict(list)   # (anio,jur,usuario,metrica) -> [(valor, origen)]
    calidad = {}
    for clave, titulo, cols, control in SPECS:
        filas, pag = leer_tabla(clave, titulo, len(cols), args.fuentes, args.refrescar)
        if not filas:
            continue
        if len(filas) < 25:
            inc("%s / %s: %d filas, se esperaban 25 (24 jurisdicciones y el total)"
                % (clave, titulo[:40], len(filas)))
        malas, redond, sabrir = (verif_cierre(clave, titulo, filas, control) if control
                                  else (0, 0, 0))
        origen = "%s p%s" % (clave, pag)
        # Una tabla que la propia ANSV rotula parcial no puede salir como definitiva.
        cal = DOCS[clave][1]
        texto_pag = paginas(clave, args.fuentes)[pag - 1] if pag else ""
        if "PARCIALES Y PRELIMINARES" in texto_pag.upper() and cal == "definitivo":
            cal = "preliminar"
        for jur, vals in filas.items():
            for col, v in zip(cols, vals):
                if col is None or v is None:
                    continue
                metrica, anio, usuario = col
                k = (anio, jur, usuario, metrica)
                # La taxonomia nueva manda tres columnas a "Otros vehiculos": se suman.
                prev = [x for x in lecturas[k] if x[1] == origen]
                if prev:
                    lecturas[k] = [x for x in lecturas[k] if x[1] != origen]
                    v += prev[0][0]
                lecturas[k].append((v, origen))
                calidad[k] = cal
        print("   %-6s p%-4s %-55s %2d filas  %s"
              % (clave, pag, titulo[:55], len(filas),
                 ("CIERRE MAL x%d" % malas) if malas else
                 ("cierra (%d con +/-1 de redondeo, %d sin abrir)" % (redond, sabrir))
                 if control else ""))

    barras = leer_barras_2025(args.fuentes, args.refrescar)
    for (metrica, jur), v in barras.items():
        if v is None:
            continue
        k = (2025, jur, TOTAL_USUARIO, metrica)
        lecturas[k].append((v, "p2025"))
        calidad[k] = DOCS["p2025"][1]
    print("   %-6s %-61s %2d valores" % ("p2025", P2025_TITULO, len(barras)))

    print("C. Verificaciones")
    verif_relectura(lecturas)
    datos = {}
    for k, obs in lecturas.items():
        vals = [v for v, _ in obs if v is not None]
        if vals:
            datos[k] = vals[0]
    verif_suma_pais(datos)
    errores = verif_denominadores(datos)
    con_tasa = {d: True for d in errores}

    print("D. Agregados")
    anios = sorted({a for (a, _, _, _) in datos})
    denoms = {d: denominador_por_anio(datos, anios, d) for d in DENOMINADORES}
    for d, tabla in denoms.items():
        print("   %-17s %d pares jurisdiccion-anio, %d despejados"
              % (d, len(tabla), sum(1 for v in tabla.values() if v[1] == "despejado")))
    noa = agregar_noa(datos, denoms, con_tasa)
    for k, v in noa.items():
        datos[k] = v
        calidad[k] = "derivado"
    print("   NOA: %d celdas (tasas publicadas: %s)"
          % (len(noa), ", ".join(d for d, ok in con_tasa.items() if ok) or "ninguna"))

    # Control gratis: las victimas fatales del NOA las publica la propia ANSV por region.
    for anio, esperado in ((2019, 935), (2022, 887)):
        got = datos.get((anio, "NOA", TOTAL_USUARIO, "victimas_fatales"))
        if got is None or abs(got - esperado) > 0.5:
            inc("NOA %d: victimas fatales dan %s, la ANSV publica %d" % (anio, got, esperado))
    print("   NOA contra la tabla por region publicada: 2019=%s (935), 2022=%s (887)"
          % (datos.get((2019, "NOA", TOTAL_USUARIO, "victimas_fatales")),
             datos.get((2022, "NOA", TOTAL_USUARIO, "victimas_fatales"))))

    print("E. Cobertura")
    jur_ok = sorted({j for (_, j, _, _) in datos})
    print("   %d jurisdicciones, %d anios (%d a %d)"
          % (len(jur_ok), len(anios), anios[0], anios[-1]))
    for metrica in METRICAS:
        ays = sorted({a for (a, j, u, m) in datos
                      if m == metrica and u == TOTAL_USUARIO and j == "Salta"})
        print("   %-36s %s" % (metrica, ", ".join(str(a) for a in ays) or "sin datos"))
    us = sorted({(a, u) for (a, j, u, m) in datos if u != TOTAL_USUARIO and j == "Salta"})
    print("   %-36s %s" % ("victimas_fatales por tipo de usuario",
                           ", ".join(str(a) for a in sorted({a for a, _ in us})) or "sin datos"))

    print("F. Saltos de magnitud")
    for metrica in METRICAS:
        for jur in jur_ok:
            saltos_de_magnitud([(a, datos[(a, j, u, m)]) for (a, j, u, m) in datos
                                if j == jur and m == metrica and u == TOTAL_USUARIO],
                               "%s / %s" % (jur, metrica))
    print("   revisadas %d series" % (len(METRICAS) * len(jur_ok)))

    print("G. Salida")
    orden_jur = {j: i for i, j in enumerate(PROVINCIAS + [TOTAL_PAIS, "NOA"])}
    orden_usr = {u: i for i, u in enumerate([TOTAL_USUARIO] + USUARIOS)}
    filas = []
    for (anio, jur, usuario, metrica), v in datos.items():
        filas.append({"anio": anio, "jurisdiccion": jur, "tipo_usuario": usuario,
                      "metrica": metrica, "valor": fmt(v),
                      "calidad": calidad.get((anio, jur, usuario, metrica), ""),
                      "fuente_doc": "; ".join(sorted({o for _, o in lecturas.get(
                          (anio, jur, usuario, metrica), [])})) or "calculado"})
    filas.sort(key=lambda f: (orden_jur.get(f["jurisdiccion"], 99), f["anio"],
                              ORDEN_METRICA[f["metrica"]], orden_usr.get(f["tipo_usuario"], 99)))
    escribir_csv(os.path.join(args.salida, SALIDA), CAMPOS, filas)

    print()
    print("Signos convencionales leidos:")
    for s, n in signos.most_common():
        print("   %-28s %d" % (s, n))
    print()
    if incidencias:
        print("Incidencias (%d):" % len(incidencias))
        for x in incidencias:
            print("  -", x)
    else:
        print("Sin incidencias detectadas.")


if __name__ == "__main__":
    main()
```
