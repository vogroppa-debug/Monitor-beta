# Actualización — Movimientos y pasajeros del aeropuerto de Salta (ANAC)

Regenera las dos series mensuales del aeropuerto Martín Miguel de Güemes a partir de los dos
productos que publica la Administración Nacional de Aviación Civil. Los dos salen del mismo
sistema de origen —el SIAC— pero están agregados con criterios distintos, cubren períodos
distintos y **no cierran entre sí**.

> **La columna `PAX` de la fuente no se publica, y no es un olvido.** No son los pasajeros de un
> tramo. Un vuelo de cabotaje aparece **dos veces** en los microdatos —despegue en el aeropuerto de
> origen, aterrizaje en el de destino— y las dos filas llevan el mismo `Pasajeros`; `PAX` es la
> mitad, el reparto entre los dos aeropuertos para que el total del país no cuente dos veces a la
> misma persona. En internacional, `PAX = Pasajeros`. Lo dice la propia nota de ANAC: *«Un vuelo de
> cabotaje implica 2 movimientos; uno internacional, 1 movimiento»*. Sumada sobre los aterrizajes
> de **un solo** aeropuerto, deja los domésticos a la mitad y los internacionales enteros: dos
> escalas en la misma columna. **El dataset B emite `vuelos` y `pasajeros`.** La columna igual se
> lee, para verificar el invariante; esa verificación es la que respalda la decisión.

> **Los dos datasets no se suman ni se empalman.** El A mide «movimientos» (aterrizajes +
> despegues) de vuelos regulares y no regulares; el B mide aterrizajes de todas las clases. En
> ene–sep 2026 el A da 9.019 movimientos y el B, llevado a la misma definición, da ~11.422. La
> brecha se publica, no se concilia.

> **El A corta el mes en hora local y el B en la fecha que publica el archivo** (rotulada «UTC»).
> Son dos relojes distintos, así que los meses no empiezan en el mismo instante.

> **Los últimos tres meses son provisorios**, por regla de ANAC, y van marcados en la columna
> `calidad`.

Metodología y verificaciones: `Metodologia_Salta_aeropuerto_ANAC.md`.

## Qué genera (en `datos-drive/`)

| Archivo | Base de origen | Período | Dimensiones propias |
|---|---|---|---|
| `Salta_aeropuerto_ANAC_series_mensual.csv` | `series-historicas-*.xlsx` (docs.anac.gob.ar) | 2001-01 → 2026-09 | `serie` (aeropuerto / ruta), `clasificacion` (Cabotaje / Internacional / Total) |
| `Salta_aeropuerto_ANAC_aterrizajes_mensual.csv` | microdatos anuales (datos.transporte.gob.ar) | 2019-01 → 2026-09 | `clasificacion`, `clase_vuelo` (9 valores), `aerolinea` |

Los dos cierran en `metrica, valor`, el esquema canónico del Monitor. El A trae `pasajeros`,
`movimientos` y `vuelos`; el B, `vuelos` y `pasajeros`.

El dataset A incluye, además de la fila del aeropuerto, **las rutas que nombran a Salta** en las
tablas por ruta: Aeroparque, Córdoba, Ezeiza, El Palomar, Iguazú, Jujuy, Mendoza, Neuquén, Rosario
y Tucumán en cabotaje, y Asunción, Iquique, Lima, Panamá, Punta Cana y Santa Cruz de la Sierra en
internacional. Se distinguen por la columna `serie`.

## 1. Requisitos

```
pip install openpyxl
```

Nada más: la descarga usa sólo `urllib` de la biblioteca estándar.

## 2. Correr el script

```bash
python actualizar_aeropuerto_anac.py
```

Desde `datos-drive/`. La primera corrida baja **unos 350 MB** a `datos-drive/fuentes/anac/` (ocho
CSV anuales de ~45 MB más los dos XLSX) y tarda varios minutos; las siguientes reutilizan la caché
y sólo vuelven a bajar lo que se mueve.

Para refrescar nada más que la serie larga, que pesa 1,6 MB:

```bash
python actualizar_aeropuerto_anac.py --sin-microdatos
```

Otros parámetros: `--salida DIR` (por defecto, la propia `datos-drive/`) y `--fuentes DIR` (la
caché).

## 3. Cómo resuelve la descarga (y por qué así)

**Las series históricas** viven en un share público de Nextcloud (`docs.anac.gob.ar`), no en un
portal de datos. El script entra por **WebDAV con el token del share como usuario de basic auth** y
contraseña vacía (`https://docs.anac.gob.ar/public.php/webdav/`). No es sólo para bajar: el
PROPFIND **lista la carpeta**, así que si ANAC agrega un archivo —cuando abra el tramo 2027, por
ejemplo— el script lo toma solo y lo informa por consola. Si alguna vez devuelve cero `.xlsx`, la
corrida aborta en vez de escribir un CSV truncado.

**Los microdatos** son ocho CSV anuales con id de recurso distinto cada uno, así que las URLs van a
mano en el diccionario `MICRODATOS`. Para sumar 2027 hay que agregar una línea con su id, que sale
de la página del dataset.

**Qué se re-descarga.** ANAC **revisa los archivos hacia atrás**: los recursos de 2019 a 2025
figuran actualizados en abril de 2026. El script vuelve a bajar siempre el año en curso y el
anterior, y el XLSX del tramo vigente; el resto sale de la caché. Si hace falta rehacer todo, basta
borrar `datos-drive/fuentes/anac/`.

**Por qué la caché es parte del entregable.** Los dos productos se reescriben: el XLSX del tramo en
curso cambia cada mes y los CSV anuales se corrigen hacia atrás. Guardar el original permite
explicar después por qué un número cambió.

**Tres cosas que el script no da por sentadas**, porque en esta fuente cambian:

- **Las columnas.** Los CSV de 2019 a 2025 traen 12 y el de 2026 agrega `Matrícula`. Se lee
  **por nombre de encabezado**, nunca por posición.
- **El formato numérico.** De 2019 a 2025 viene en configuración latina (`140,00`) y en 2026 en
  enteros. Lo resuelve un único `parse_num` con la regla del último separador.
- **Las etiquetas.** Sólo 2019 usa `Domestico` sin tilde y `ATERRIZAJE` en mayúsculas. Se normaliza
  a la forma de 2020 en adelante y se informa cuántas filas se tocaron por año.

En los XLSX tampoco se asume posición fija: los bloques se localizan por el marcador `TABLA n` de
la columna A y las columnas de datos, por el nombre del mes en la segunda fila. El archivo
2001–2022 tiene 267 columnas y el 2023–2026, 47.

## 4. Verificar antes de dar por buena la actualización

1. **La consola tiene que cerrar** con «Sin incidencias detectadas» o con una lista en la que
   reconozcas cada línea. Las esperables son el desplome de 2020, el `PAX` redondeado de 2026, la
   franja horaria y la brecha de conciliación.

2. **Cobertura del dataset A.** La línea `serie del aeropuerto: N meses` tiene que dar **309 o
   más**, arrancando en `2001-01`, y sin que aparezca ninguna incidencia de meses faltantes.

3. **Los valores de control del dataset A** (de la corrida del 2026-11-18):

   | Período | Clasificación | Movimientos | Pasajeros |
   |---|---|---|---|
   | 2001-01 | Cabotaje | 603 | 21.941 |
   | 2026-09 | Cabotaje | 994 | 136.043 |

   Y los totales de 2026 (ene–sep): **cabotaje 7.686, internacional 1.333, total 9.019**
   movimientos. Si cambian, ANAC revisó la serie: anotar el cambio antes de pisar el CSV.

4. **Los valores de control del dataset B** (aterrizajes en SAL, todas las clases, 2026):

   | Mes | Vuelos | Pasajeros |
   |---|---|---|
   | 2026-01 | 980 | 69.924 |
   | 2026-09 | 986 | 76.872 |

   Total ene–sep 2026: **7.991 aterrizajes y 572.661 pasajeros**. El archivo tiene **3.830 filas**
   y 93 meses, de 2019-01 a 2026-09, sin huecos.

5. **El invariante de `PAX`**, que se verifica aunque la columna no se publique: es lo que
   respalda haber elegido `pasajeros`. La única violación conocida en toda la serie es **una fila
   de 2022** (17/01, aeropuerto `IGU`, destino `2463`, `Pas=3 PAX=3`), que es un defecto de origen
   y no toca a Salta. Las filas con `PAX` redondeado de 2026 se cuentan aparte y no son
   violaciones. Si aparecen violaciones nuevas, ANAC cambió el criterio y hay que revisar la
   decisión antes de publicar.

6. **El espejo.** La línea `espejo 2026: de N aterrizajes domésticos...` tiene que dar alrededor
   de **dos tercios con despegue hallado** y **~70 % de esos con el mismo `Pasajeros`**. Es la
   confirmación empírica de que un vuelo de cabotaje deja dos filas y de que `pax` es un reparto,
   no una medición. Si se desploma, cambió la identificación de la matrícula o el criterio de
   carga.

7. **La conciliación entre los dos productos.** El cabotaje tiene que cerrar: la línea
   `brecha Cabotaje regular + no regular` da **mediana +0,4 %** sobre 93 meses. **Esa es la
   validación de punta a punta del pipeline**; si se despega, hay un error propio. El
   internacional **no cierra y no tiene que cerrar**: la cifra oficial queda entre las dos
   lecturas (−56,4 % con sólo regulares, +143,0 % con regulares y no regulares). Lo que importa
   ahí es que la brecha sea estable mes a mes, no que sea chica.

8. **Formato**, con la skill `datasets`: decimal `.`, sin separador de miles, sin mojibake (ojo con
   `COMPAÑÍA DE AVIACIÓN PARAGUAYA S.A.`, que lleva `Ñ` y tildes), sin negativos y sin claves
   duplicadas.

---

## Script completo

Guardar el bloque de abajo como `actualizar_aeropuerto_anac.py` **dentro de `datos-drive/`**.

```python
# -*- coding: utf-8 -*-
"""
Movimientos y pasajeros del aeropuerto de Salta — ANAC.

Genera dos series mensuales tidy, de DOS productos distintos de ANAC que no son sustitutos:

  A. Salta_aeropuerto_ANAC_series_mensual.csv       (2001-2026)
     De las "series historicas" que ANAC publica en docs.anac.gob.ar: tablas ya agregadas.
     Da 18 anios mas de profundidad, pero solo abre por cabotaje/internacional. No tiene
     aerolinea por aeropuerto, no tiene clase de vuelo, y publica "movimientos" (= aterrizajes
     + despegues), asi que no se pueden separar los dos sentidos.

  B. Salta_aeropuerto_ANAC_aterrizajes_mensual.csv  (2019-2026)
     De los microdatos vuelo por vuelo de datos.gob.ar. Arranca recien en 2019, pero es el
     unico que permite abrir los ATERRIZAJES en Salta por clase de vuelo, clasificacion y
     aerolinea.

LOS DOS NO CIERRAN ENTRE SI y no hay que sumarlos ni empalmarlos. Son definiciones distintas:
ene-sep 2026 da 9.019 movimientos por la serie oficial y ~11.422 por los microdatos agregados a
la misma definicion. El script mide la brecha y la reporta; no la fuerza.

POR QUE NO SE PUBLICA "PAX". La columna PAX de los microdatos NO son los pasajeros de un tramo.
Un vuelo de cabotaje aparece DOS veces -despegue en el origen, aterrizaje en el destino- y las dos
filas llevan el mismo `Pasajeros`; PAX es la mitad, el reparto entre los dos aeropuertos para que
el total nacional no duplique. En internacional PAX = Pasajeros. La nota metodologica de ANAC lo
dice asi: "Un vuelo de cabotaje implica 2 movimientos; uno internacional, 1 movimiento". Sumada
sobre los aterrizajes de UN aeropuerto, PAX deja los domesticos a la mitad y los internacionales
enteros: dos escalas en la misma columna. No sirve como nivel para Salta, asi que el dataset B
emite `vuelos` y `pasajeros` y NO emite `pax`.

La columna igual se LEE, para verificar el invariante (PAX = Pasajeros en internacional, la mitad
en domestico). Esa verificacion es la evidencia de que `pasajeros` es la columna correcta, y
avisaria si ANAC cambiara el criterio.

Formato de salida (convencion del repo): decimal '.', sin separador de miles, CSV con ',',
UTF-8 con BOM.

Correr:  python actualizar_aeropuerto_anac.py [--salida DIR] [--fuentes DIR] [--sin-microdatos]
"""

import argparse
import collections
import csv
import io
import os
import re
import sys
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.abspath(__file__))

# ===========================================================================
# Fuentes
# ===========================================================================

# A. Series historicas: share publico de Nextcloud de ANAC. Se entra por WebDAV con el token del
#    share como usuario de basic auth y contrasenia vacia: ademas de bajar, LISTA la carpeta, asi
#    que el script se entera solo si ANAC agrega o renombra un archivo.
NEXTCLOUD_TOKEN = "4ptegdXanm2rWJG"
NEXTCLOUD_DAV = "https://docs.anac.gob.ar/public.php/webdav/"

# B. Microdatos: un CSV por anio en datos.transporte.gob.ar. El id del recurso cambia por anio y
#    el nombre del archivo tambien, asi que van a mano.
BASE_MD = "https://datos.transporte.gob.ar/dataset/21038a1a-c3c7-4494-b76a-3a2a8fbb83b5/resource"
MICRODATOS = {
    2019: "d39e99eb-f170-4d92-889a-4088b90c7678/download/201912-informe-ministerio-actualizado-dic-final.csv",
    2020: "d0e75e7d-e416-470f-bedb-ef2a877cbae3/download/202012-informe-ministerio-actualizado-dic-final.csv",
    2021: "1b4f569a-cab0-4560-993c-5bf96c3e7cf0/download/202112-informe-ministerio-actualizado-dic-final.csv",
    2022: "11894a35-de36-4579-b084-d1191f551fbe/download/202212-informe-ministerio-actualizado-dic-final.csv",
    2023: "e910fead-ade3-40ce-ae8f-cad2017aa007/download/202312-informe-ministerio-actualizado-dic.csv",
    2024: "6004191c-83ca-4a0a-a687-c059bb0a8c8e/download/202412-informe-ministerio-actualizado-dic-final.csv",
    2025: "0706775f-bed9-46e7-aac5-726d7e72e429/download/202512-informe-ministerio-actualizado-dic-final.csv",
    2026: "7b6d0103-0a69-4c67-aed9-33cb58ae12f5/download/202609-informe-ministerio-vf-matricula.csv",
}

# Codigo local de ANAC para el aeropuerto Martin Miguel de Guemes. No es IATA (SLA) ni OACI
# (SASA). Es el unico aeropuerto salteno del dataset: entre los 50 codigos presentes no hay Oran,
# Tartagal ni Cafayate.
SALTA_MD = "SAL"
SALTA_SERIES = "Salta"

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MES_N = {m: i + 1 for i, m in enumerate(MESES)}

# Tablas de los XLSX que abren POR AEROPUERTO (las 9 a 14). Las seis consideran unicamente
# vuelos regulares y no regulares: excluyen privados, escuela, adiestramiento y trabajo aereo.
#   tabla -> (metrica, clasificacion, factor)
# El factor 1000 es porque los pasajeros vienen en miles con tres decimales (21.941 = 21941).
TABLAS_AEROPUERTO = {
    9:  ("pasajeros",   "Cabotaje",      1000),
    10: ("pasajeros",   "Internacional", 1000),
    11: ("pasajeros",   "Total",         1000),
    12: ("movimientos", "Cabotaje",         1),
    13: ("movimientos", "Internacional",    1),
    14: ("movimientos", "Total",            1),
}
# Tablas por RUTA (top 61 nacional). Solo entran las filas que nombren a Salta.
TABLAS_RUTA = {
    19: ("pasajeros", "Cabotaje",      1000),
    20: ("pasajeros", "Internacional", 1000),
    21: ("vuelos",    "Cabotaje",         1),
    22: ("vuelos",    "Internacional",    1),
}

incidencias = []


def inc(msg):
    incidencias.append(msg)


# ===========================================================================
# Utilidades
# ===========================================================================

def bajar(url, dest, headers=None, refrescar=False):
    """Descarga con cache y escritura atomica. `refrescar` fuerza la re-descarga."""
    if os.path.exists(dest) and not refrescar:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("   bajando %s" % os.path.basename(dest))
    req = urllib.request.Request(url, headers=headers or {})
    tmp = dest + ".tmp"
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as fh:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    os.replace(tmp, dest)
    return dest


def leer_texto(path):
    """Decodifica en estricto probando utf-8-sig, cp1252 y latin-1. Nunca errors='replace',
    que enmascara el problema en vez de mostrarlo."""
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError("no se pudo decodificar %s" % path)


_RE_NUM = re.compile(r"^-?[0-9][0-9.,]*$")


def parse_num(s):
    """Latina o inglesa -> float. Regla del ultimo separador: si hay '.' y ',', el que aparece
    mas a la derecha es el decimal. Si hay uno solo, es de miles cuando lo siguen exactamente
    3 digitos. Los microdatos vienen en LATINA hasta 2025 (`140,00`) y en enteros en 2026."""
    if s is None:
        return None
    t = str(s).strip()
    if t == "" or not _RE_NUM.match(t):
        return None
    neg = t.startswith("-")
    t = t.lstrip("-")
    ult_p, ult_c = t.rfind("."), t.rfind(",")
    if ult_p >= 0 and ult_c >= 0:
        dec = "." if ult_p > ult_c else ","
        mil = "," if dec == "." else "."
        t = t.replace(mil, "").replace(dec, ".")
    elif ult_p >= 0 or ult_c >= 0:
        sep = "." if ult_p >= 0 else ","
        cola = t.split(sep)[-1]
        if len(cola) == 3 and t.count(sep) >= 1:
            # Ambiguo: tres digitos detras del separador. En esta fuente no deberia pasar
            # (los decimales son ',00' y 2026 viene entero), asi que se anota si pasa.
            inc("valor numerico ambiguo '%s': separador seguido de 3 digitos, se leyo como miles" % s)
            t = t.replace(sep, "")
        else:
            t = t.replace(sep, ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def escribir_csv(ruta, campos, filas):
    with io.open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print("   -> %s (%d filas)" % (os.path.basename(ruta), len(filas)))


def saltos_de_magnitud(pares, etiqueta, minimo=50):
    """Regla de la skill `datasets`: un valor >100x o <1/100 de la mediana de su serie. Se
    reporta CON los periodos y no se corrige: el desplome de 2020 por la pandemia cae justo
    en esta regla y es dato real, no un separador mal leido.

    `pares` es [(periodo, valor)].
    """
    vals = sorted(v for _, v in pares if v is not None and v > 0)
    if len(vals) < 12:
        return
    med = vals[len(vals) // 2]
    if med < minimo:
        return
    raros = [(p, v) for p, v in pares
             if v is not None and v > 0 and (v / med > 100 or v / med < 0.01)]
    if raros:
        inc("%s: %d valor(es) a mas de 100x de la mediana (%.0f): %s. Son los meses de cierre "
            "de aeropuertos por la pandemia; dato real, no se corrige."
            % (etiqueta, len(raros), med,
               ", ".join("%s=%.0f" % (p, v) for p, v in sorted(raros)[:10])))


# ===========================================================================
# A. Series historicas (XLSX de docs.anac.gob.ar)
# ===========================================================================

def listar_nextcloud():
    """PROPFIND sobre el share publico. Devuelve [(nombre, bytes)]."""
    import base64
    auth = base64.b64encode(("%s:" % NEXTCLOUD_TOKEN).encode()).decode()
    req = urllib.request.Request(NEXTCLOUD_DAV, method="PROPFIND",
                                 headers={"Authorization": "Basic " + auth, "Depth": "1"})
    xml = urllib.request.urlopen(req, timeout=120).read().decode("utf-8")
    out = []
    for href, cuerpo in re.findall(r"<d:href>([^<]+)</d:href>(.*?)</d:response>", xml, re.S):
        nombre = urllib.parse.unquote(href.rsplit("/", 1)[-1])
        if not nombre.lower().endswith(".xlsx"):
            continue
        m = re.search(r"<d:getcontentlength>(\d+)</d:getcontentlength>", cuerpo)
        out.append((nombre, int(m.group(1)) if m else 0))
    return sorted(out)


def bajar_series(fuentes):
    import base64
    import urllib.parse as up
    auth = base64.b64encode(("%s:" % NEXTCLOUD_TOKEN).encode()).decode()
    archivos = listar_nextcloud()
    if not archivos:
        raise RuntimeError("el share de ANAC no devolvio ningun .xlsx")
    print("   share ANAC: %s" % ", ".join(n for n, _ in archivos))
    locales = []
    for nombre, _ in archivos:
        dest = os.path.join(fuentes, nombre)
        # El archivo del tramo en curso se re-descarga siempre: es el que se mueve cada mes.
        refrescar = bool(re.search(r"20(2[3-9]|[3-9][0-9])", nombre))
        bajar(NEXTCLOUD_DAV + up.quote(nombre), dest,
              headers={"Authorization": "Basic " + auth}, refrescar=refrescar)
        locales.append(dest)
    return locales


def bloques_xlsx(path):
    """Devuelve {n_tabla: (filas_del_bloque, cols, periodos)} de la hoja OUT.

    Estructura de la hoja: la fila del marcador 'TABLA n' lleva los anios, la siguiente los
    meses (y en la columna A, la unidad), y desde ahi bajan las categorias. La primera columna
    con datos NO es fija -el archivo 2001-2022 tiene 267 columnas y el 2023-2026, 47-, asi que
    se detecta por el nombre del mes.
    """
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    hoja = "OUT" if "OUT" in wb.sheetnames else wb.sheetnames[0]
    filas = list(wb[hoja].iter_rows(values_only=True))
    wb.close()

    marcas = []
    for i, r in enumerate(filas):
        a = str(r[0]).strip() if r and r[0] is not None else ""
        m = re.match(r"^TABLA\s+(\d+)$", a, re.I)
        if m:
            marcas.append((int(m.group(1)), i))

    out = {}
    for k, (n, i) in enumerate(marcas):
        fin = marcas[k + 1][1] if k + 1 < len(marcas) else len(filas)
        anios, meses = filas[i], filas[i + 1]
        periodos = []
        for c in range(len(meses)):
            mes = str(meses[c]).strip() if meses[c] is not None else ""
            if mes in MES_N and c < len(anios) and anios[c] is not None:
                try:
                    periodos.append((c, int(str(anios[c]).strip()[:4]), MES_N[mes]))
                except ValueError:
                    pass
        out[n] = (filas[i + 2:fin], periodos, str(filas[i + 1][0] or "").strip())
    return out


def construir_series(paths):
    """Dataset A: fila de Salta de las tablas por aeropuerto + las rutas que la nombran."""
    datos = {}        # (anio, mes, etiqueta, serie, clasificacion, metrica) -> valor
    vistos_tabla = collections.Counter()
    unidades = {}

    for path in sorted(paths):
        bl = bloques_xlsx(path)
        print("   %s: %d tablas" % (os.path.basename(path), len(bl)))
        for n, (filas, periodos, unidad) in bl.items():
            if n in TABLAS_AEROPUERTO:
                metrica, clasif, factor = TABLAS_AEROPUERTO[n]
                serie, objetivo = "aeropuerto", lambda e: e == SALTA_SERIES
            elif n in TABLAS_RUTA:
                metrica, clasif, factor = TABLAS_RUTA[n]
                serie, objetivo = "ruta", lambda e: SALTA_SERIES.lower() in e.lower()
            else:
                continue
            unidades[n] = unidad
            for fila in filas:
                etiqueta = str(fila[0]).strip() if fila and fila[0] is not None else ""
                if not etiqueta or not objetivo(etiqueta):
                    continue
                vistos_tabla[n] += 1
                for c, anio, mes in periodos:
                    if c >= len(fila):
                        continue
                    v = fila[c]
                    if not isinstance(v, (int, float)):
                        v = parse_num(v)
                    if v is None:
                        continue
                    k = (anio, mes, etiqueta, serie, clasif, metrica)
                    nuevo = round(float(v) * factor)
                    if k in datos and datos[k] != nuevo:
                        inc("series: %s %04d-%02d %s/%s aparece en dos archivos con valores "
                            "distintos (%s vs %s); manda el mas reciente."
                            % (etiqueta, anio, mes, clasif, metrica, datos[k], nuevo))
                    datos[k] = nuevo

    for n in sorted(set(TABLAS_AEROPUERTO) | set(TABLAS_RUTA)):
        if not vistos_tabla[n]:
            inc("series: la tabla %d no trajo ninguna fila de Salta" % n)

    # Provisorio: los ultimos 3 meses, segun la propia nota de ANAC.
    periodos = sorted({(a, m) for a, m, _, _, _, _ in datos})
    provisorios = set(periodos[-3:])

    filas = []
    for (anio, mes, etiqueta, serie, clasif, metrica), v in sorted(datos.items()):
        filas.append({
            "anio": anio, "n_mes": mes,
            "mes": "%04d-%02d-01" % (anio, mes), "periodo": "%04d-%02d" % (anio, mes),
            "aeropuerto": etiqueta, "serie": serie, "clasificacion": clasif,
            "metrica": metrica, "valor": v,
            "calidad": "PROVISORIO" if (anio, mes) in provisorios else "DEFINITIVO",
        })

    # Huecos en la serie del aeropuerto
    meses_aero = sorted({(a, m) for a, m, e, s, _, _ in datos if s == "aeropuerto"})
    if meses_aero:
        a0, m0 = meses_aero[0]
        a1, m1 = meses_aero[-1]
        esperado = [(a, m) for a in range(a0, a1 + 1) for m in range(1, 13)
                    if (a, m) >= (a0, m0) and (a, m) <= (a1, m1)]
        faltan = sorted(set(esperado) - set(meses_aero))
        if faltan:
            inc("series: faltan %d mes(es) en la serie del aeropuerto: %s"
                % (len(faltan), ", ".join("%04d-%02d" % x for x in faltan[:12])))
        print("   serie del aeropuerto: %d meses, de %04d-%02d a %04d-%02d"
              % (len(meses_aero), a0, m0, a1, m1))

    for metrica in ("pasajeros", "movimientos"):
        serie = [("%04d-%02d" % (a, m), v) for (a, m, e, s, c, me), v in datos.items()
                 if s == "aeropuerto" and c == "Total" and me == metrica]
        saltos_de_magnitud(serie, "series/%s" % metrica)

    return filas, datos


# ===========================================================================
# B. Microdatos (CSV anuales de datos.transporte.gob.ar)
# ===========================================================================

COL = {
    "fecha": "Fecha UTC", "hora": "Hora UTC",
    "clase": "Clase de Vuelo (todos los vuelos)", "clasif": "Clasificación Vuelo",
    "mov": "Tipo de Movimiento", "aero": "Aeropuerto", "od": "Origen / Destino",
    "linea": "Aerolinea Nombre", "aeronave": "Aeronave", "matricula": "Matrícula",
    "pas": "Pasajeros", "pax": "PAX", "calidad": "Calidad dato",
}

# Solo 2019 usa 'Domestico' sin tilde y los movimientos en MAYUSCULAS. De 2020 en adelante la
# fuente ya viene en la forma de abajo; se normaliza todo a esa.
NORM_CLASIF = {"domestico": "Doméstico", "doméstico": "Doméstico", "internacional": "Internacional"}
NORM_MOV = {"aterrizaje": "Aterrizaje", "despegue": "Despegue"}


def bajar_microdatos(fuentes, anios):
    out = {}
    ultimo = max(MICRODATOS)
    for anio in anios:
        url = "%s/%s" % (BASE_MD, MICRODATOS[anio])
        dest = os.path.join(fuentes, "anac_microdatos_%d.csv" % anio)
        # ANAC revisa hacia atras: los recursos 2019-2025 figuran actualizados en 2026. Se
        # re-descargan el anio en curso y el anterior.
        bajar(url, dest, refrescar=anio >= ultimo - 1)
        out[anio] = dest
    return out


def leer_microdatos(path, anio):
    """Itera dicts del CSV. Lee POR NOMBRE de encabezado: 2026 agrega la columna `Matrícula`
    y leer por posicion romperia."""
    txt, enc = leer_texto(path)
    if enc != "utf-8-sig":
        inc("microdatos %d: el archivo no es UTF-8, se leyo como %s" % (anio, enc))
    r = csv.reader(io.StringIO(txt), delimiter=";")
    hdr = next(r)
    hdr = [h.lstrip("﻿").strip() for h in hdr]
    falta = [v for k, v in COL.items() if k != "matricula" and v not in hdr]
    if falta:
        raise RuntimeError("microdatos %d: faltan columnas %s" % (anio, falta))
    ix = {k: hdr.index(v) for k, v in COL.items() if v in hdr}
    ancho = len(hdr)
    for fila in r:
        if len(fila) != ancho:
            continue
        yield ix, fila


def construir_aterrizajes(paths):
    """Dataset B: aterrizajes en SAL por mes x clasificacion x clase x aerolinea."""
    agg = collections.defaultdict(lambda: [0, 0.0])        # -> [vuelos, pasajeros]
    calidad = collections.defaultdict(set)
    normalizadas = collections.Counter()
    viola_pax = collections.Counter()
    redondeo_pax = collections.Counter()
    ejemplos_pax = []
    franja_utc = collections.Counter()
    espejo = {}
    # Movimientos de SAL contando los dos sentidos, solo regular + no regular: es la definicion
    # de la serie oficial, y sirve para conciliar un producto contra el otro.
    movimientos = collections.Counter()
    COMERCIAL = ("Regular", "No Regular")

    for anio in sorted(paths):
        n_sal = n_ate = 0
        arribos, salidas = [], []
        for ix, fila in leer_microdatos(paths[anio], anio):
            clasif_raw = fila[ix["clasif"]].strip()
            mov_raw = fila[ix["mov"]].strip()
            clasif = NORM_CLASIF.get(clasif_raw.lower(), clasif_raw)
            mov = NORM_MOV.get(mov_raw.lower(), mov_raw)
            if clasif != clasif_raw or mov != mov_raw:
                normalizadas[anio] += 1

            pas = parse_num(fila[ix["pas"]]) or 0.0
            pax = parse_num(fila[ix["pax"]]) or 0.0

            aero = fila[ix["aero"]].strip()
            od = fila[ix["od"]].strip()
            mat = fila[ix["matricula"]].strip() if "matricula" in ix else ""

            # Invariante de PAX, sobre TODO el archivo (no solo Salta).
            if clasif == "Internacional":
                if abs(pax - pas) > 0.01:
                    viola_pax[anio] += 1
                    if len(ejemplos_pax) < 6:
                        ejemplos_pax.append((anio, fila[ix["fecha"]].strip(), clasif, aero, od, pas, pax))
            elif clasif == "Doméstico":
                if abs(pax - pas / 2.0) > 0.01:
                    # Hasta 2025 PAX trae el medio punto (`64,50`); en 2026 la fuente lo redondea
                    # a entero. Redondeo HACIA ARRIBA, no el de Python, que va al par mas cercano
                    # (round(78.5) da 78) y marcaria como violacion media docena de miles de filas.
                    if abs(pax - int(pas / 2.0 + 0.5)) <= 0.01:
                        redondeo_pax[anio] += 1
                    else:
                        viola_pax[anio] += 1
                        if len(ejemplos_pax) < 6:
                            ejemplos_pax.append((anio, fila[ix["fecha"]].strip(), clasif, aero, od, pas, pax))

            clase = fila[ix["clase"]].strip()
            if aero == SALTA_MD and clase in COMERCIAL:
                f = fila[ix["fecha"]].strip()
                try:
                    k = (int(f[6:10]), int(f[3:5]),
                         "Cabotaje" if clasif == "Doméstico" else "Internacional")
                    movimientos[k + ("reg+nreg",)] += 1
                    if clase == "Regular":
                        movimientos[k + ("reg",)] += 1
                except ValueError:
                    pass

            # Control cruzado del espejo. Un vuelo de cabotaje X->SAL deja DOS filas: el despegue
            # en X (con od=SAL) y el aterrizaje en SAL (con od=X). Si la hipotesis es correcta,
            # las dos traen el mismo `Pasajeros`. Hay que mirar el despegue en el OTRO aeropuerto,
            # no los despegues desde Salta: esos son el vuelo de vuelta, otro vuelo.
            if clasif == "Doméstico" and mat:
                if mov == "Aterrizaje" and aero == SALTA_MD:
                    arribos.append(((fila[ix["fecha"]].strip(), mat, od), pas))
                elif mov == "Despegue" and od == SALTA_MD:
                    salidas.append(((fila[ix["fecha"]].strip(), mat, aero), pas))

            if aero != SALTA_MD:
                continue
            n_sal += 1
            if mov != "Aterrizaje":
                continue
            n_ate += 1

            f = fila[ix["fecha"]].strip()
            try:
                d, m, a = int(f[0:2]), int(f[3:5]), int(f[6:10])
            except ValueError:
                inc("microdatos %d: fecha ilegible %r" % (anio, f))
                continue
            if a != anio:
                inc("microdatos %d: una fila trae fecha de %d" % (anio, a))

            hora = fila[ix["hora"]].strip()
            if hora[:1].isdigit() and int(hora.split(":")[0]) < 3:
                franja_utc["%04d-%02d" % (a, m)] += 1

            linea = fila[ix["linea"]].strip()
            # '0' es el centinela de dato faltante de la fuente, no una aerolinea. Son vuelos de
            # aviacion general sin explotador declarado: se etiquetan, no se borran.
            if linea in ("0", ""):
                linea = "Sin informar"

            k = (a, m, clasif, fila[ix["clase"]].strip(), linea)
            v = agg[k]
            v[0] += 1
            v[1] += pas
            calidad[(a, m)].add(fila[ix["calidad"]].strip())

        if arribos or salidas:
            idx = collections.defaultdict(list)
            for clave, pas in salidas:
                idx[clave].append(pas)
            ok = hallado = tot = 0
            for clave, pas in arribos:
                tot += 1
                ps = idx.get(clave)
                if not ps:
                    continue
                hallado += 1
                if any(abs(p - pas) <= 0.01 for p in ps):
                    ok += 1
            espejo[anio] = (ok, hallado, tot)
        print("   %d: %d filas SAL, %d aterrizajes" % (anio, n_sal, n_ate))

    for anio in sorted(normalizadas):
        print("   %d: %d filas con etiquetas normalizadas" % (anio, normalizadas[anio]))
    for anio in sorted(viola_pax):
        inc("microdatos %d: %d fila(s) violan el invariante de PAX (de %s)"
            % (anio, viola_pax[anio],
               "; ".join("%s %s %s-%s Pas=%g PAX=%g" % (f, c, a, o, p, x)
                         for (an, f, c, a, o, p, x) in ejemplos_pax if an == anio) or "sin ejemplo"))
    for anio in sorted(redondeo_pax):
        print("   %d: %d filas con PAX redondeado (no exactamente Pasajeros/2)"
              % (anio, redondeo_pax[anio]))

    filas = []
    for (a, m, clasif, clase, linea), (nv, pas) in sorted(agg.items()):
        # La calidad es atributo del MES: si en el mes conviven las dos, se dice MIXTO en vez de
        # elegir una. Hoy no pasa (ANAC marca meses enteros), pero si pasara habria que verlo.
        cal = calidad[(a, m)]
        cal_mes = cal.copy().pop() if len(cal) == 1 else "MIXTO"
        base = {"anio": a, "n_mes": m, "mes": "%04d-%02d-01" % (a, m),
                "periodo": "%04d-%02d" % (a, m), "aeropuerto": SALTA_MD,
                "clasificacion": clasif, "clase_vuelo": clase, "aerolinea": linea,
                "calidad": cal_mes}
        # `pax` no se emite: es el reparto de ANAC entre los dos aeropuertos del vuelo, no un
        # nivel de este aeropuerto. Se lee y se verifica, pero no se publica.
        for metrica, valor in (("vuelos", nv), ("pasajeros", pas)):
            f = dict(base)
            f["metrica"] = metrica
            f["valor"] = int(round(valor))
            filas.append(f)

    return filas, agg, espejo, franja_utc, movimientos


# ===========================================================================
# Conciliacion entre los dos productos
# ===========================================================================

def conciliar(datos_series, md):
    """Compara los movimientos de la serie oficial contra los microdatos llevados a la MISMA
    definicion: vuelos regulares y no regulares, contando aterrizajes y despegues en Salta.

    NO se espera que cierren: son dos agregaciones distintas del mismo sistema, y encima cortan
    el mes con relojes distintos (la oficial en hora local, los microdatos en la fecha publicada).
    Lo util es que la brecha sea ESTABLE: un salto brusco de un mes a otro delata un error del
    pipeline, no de la fuente.
    """
    print()
    print("   Conciliacion (movimientos en Salta), dos lecturas de 'comercial':")
    print("   %-9s %8s %8s %7s %8s %7s | %8s %8s %7s %8s %7s" %
          ("periodo", "of.cab", "r+nr", "brecha", "solo r", "brecha",
           "of.int", "r+nr", "brecha", "solo r", "brecha"))
    brechas = collections.defaultdict(list)
    periodos = sorted({(a, m) for (a, m, _, _, _, _) in datos_series})
    for (a, m) in periodos:
        linea = ["%04d-%02d" % (a, m)]
        hay = False
        for clasif in ("Cabotaje", "Internacional"):
            of = datos_series.get((a, m, SALTA_SERIES, "aeropuerto", clasif, "movimientos"))
            # Los meses de cierre de aeropuertos de 2020 traen 0 movimientos: no hay brecha
            # relativa que calcular, y meterlos rompe la mediana.
            if not of:
                linea += ["%8s" % "-"] * 5
                continue
            linea.append("%8d" % of)
            for variante in ("reg+nreg", "reg"):
                mv = md.get((a, m, clasif, variante), 0)
                if not mv:
                    linea += ["%8s" % "-", "%7s" % "-"]
                    continue
                hay = True
                br = (mv - of) / of * 100.0
                brechas[(clasif, variante)].append(br)
                linea += ["%8d" % mv, "%6.1f%%" % br]
        if hay and a >= 2026:
            print("   %-9s %s" % (linea[0], " ".join(linea[1:])))
    etiq = {"reg+nreg": "regular + no regular", "reg": "solo regular"}
    for (clasif, variante), bs in sorted(brechas.items()):
        bs2 = sorted(bs)
        med = bs2[len(bs2) // 2]
        print("   brecha %-14s %-21s sobre %d meses: mediana %7.1f%%, min %7.1f%%, max %7.1f%%"
              % (clasif, etiq[variante], len(bs), med, bs2[0], bs2[-1]))
    # Solo se anota como incidencia la lectura que mejor cierra, con su alternativa al lado.
    for clasif in ("Cabotaje", "Internacional"):
        cands = [(abs(sorted(bs)[len(bs) // 2]), v, sorted(bs)[len(bs) // 2], len(bs))
                 for (c, v), bs in brechas.items() if c == clasif and bs]
        if not cands:
            continue
        cands.sort()
        _, v, med, n = cands[0]
        inc("conciliacion %s: contra la serie oficial, los microdatos cierran mejor tomando "
            "'%s' (mediana %.1f%% sobre %d meses). Las otras lecturas: %s. Son agregaciones "
            "distintas del mismo sistema y cortan el mes con relojes distintos; se publica la "
            "brecha, no se fuerza."
            % (clasif, etiq[v], med, n,
               "; ".join("%s %.1f%%" % (etiq[vv], mm) for _, vv, mm, _ in cands[1:]) or "ninguna"))


# ===========================================================================
# main
# ===========================================================================

def main():
    ap = argparse.ArgumentParser(description="Movimientos del aeropuerto de Salta (ANAC)")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "anac"),
                    help="Cache de los archivos originales")
    ap.add_argument("--sin-microdatos", action="store_true",
                    help="Solo el dataset A (evita bajar ~350 MB)")
    args = ap.parse_args()
    os.makedirs(args.fuentes, exist_ok=True)

    print("A. Series historicas (docs.anac.gob.ar)")
    paths_a = bajar_series(args.fuentes)
    filas_a, datos_a = construir_series(paths_a)
    escribir_csv(os.path.join(args.salida, "Salta_aeropuerto_ANAC_series_mensual.csv"),
                 ["anio", "n_mes", "mes", "periodo", "aeropuerto", "serie", "clasificacion",
                  "metrica", "valor", "calidad"], filas_a)

    if not args.sin_microdatos:
        print()
        print("B. Microdatos (datos.transporte.gob.ar)")
        paths_b = bajar_microdatos(args.fuentes, sorted(MICRODATOS))
        filas_b, agg_b, espejo, franja, movs_b = construir_aterrizajes(paths_b)
        escribir_csv(os.path.join(args.salida, "Salta_aeropuerto_ANAC_aterrizajes_mensual.csv"),
                     ["anio", "n_mes", "mes", "periodo", "aeropuerto", "clasificacion",
                      "clase_vuelo", "aerolinea", "calidad", "metrica", "valor"], filas_b)

        print()
        for anio in sorted(espejo):
            ok, hallado, tot = espejo[anio]
            print("   espejo %d: de %d aterrizajes domesticos en SAL, %d tienen su despegue en el "
                  "aeropuerto de origen (%.0f%%) y %d de esos traen el MISMO Pasajeros (%.1f%%)"
                  % (anio, tot, hallado, 100.0 * hallado / tot if tot else 0,
                     ok, 100.0 * ok / hallado if hallado else 0))
        tot_franja = sum(franja.values())
        tot_ate = sum(v[0] for v in agg_b.values())
        print("   franja 00:00-02:59 UTC: %d de %d aterrizajes (%.1f%%) cambiarian de dia "
              "al pasar a hora local UTC-3"
              % (tot_franja, tot_ate, 100.0 * tot_franja / tot_ate if tot_ate else 0.0))
        inc("microdatos: %d aterrizajes en SAL caen entre las 00:00 y las 02:59 UTC y cambiarian "
            "de dia -y a veces de mes- al pasarlos a hora local (UTC-3). La serie oficial de ANAC "
            "usa hora local; este dataset usa la fecha tal como la publica la fuente."
            % tot_franja)

        conciliar(datos_a, movs_b)

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
