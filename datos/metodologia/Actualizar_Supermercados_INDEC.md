# Actualización — Ventas y operaciones de supermercados por jurisdicción (INDEC)

Regenera la serie mensual de ventas y operaciones de supermercados a partir de la planilla única que
publica el INDEC en <https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-1-34>. Abre las 26
jurisdicciones del país —entre ellas Salta— desde enero de 2017, y agrega la serie en pesos
constantes deflactada con el IPC NOA, igual que el resto del sitio.

> **El INDEC pide expresamente que esto no se lea como consumo.** Sus palabras: *«Las ventas totales
> registradas mensualmente de los supermercados […] no se deben considerar aisladamente como un
> indicador macroeconómico del consumo.»* Es un canal comercial, no el gasto de los hogares; el
> consumo privado se mide en Cuentas Nacionales.

> **La cantidad de bocas no se publica, y no es un olvido.** La planilla la trae, pero es el tamaño
> del panel relevado, no el número de supermercados que hay en Salta. La encuesta es un *«panel no
> probabilístico»* de empresas *«que cuentan por lo menos con alguna boca de expendio cuya superficie
> en el salón de ventas sea igual o supere los 200 m2»*. Al lado de las ventas, esa columna se lee
> como un censo de bocas, que es lo que no es.

> **La encuesta de autoservicios mayoristas no está acá porque no abre por provincia.** Publica
> cuatro jurisdicciones —Total del país, CABA, 24 partidos del Gran Buenos Aires y «Resto del
> país»— y Salta queda adentro de la última. Verificado en los dos archivos que el INDEC
> publica: la palabra «Salta» no aparece una sola vez.

> **Los últimos 24 meses son provisorios**, por regla del propio INDEC, y van marcados en la columna
> `calidad`.

> **La base de los pesos constantes se mueve.** Es el último mes con IPC publicado, la misma que usa
> `adapters.py` en el sitio. Cuando se actualiza `ipc_noa_mensual.csv`, este CSV hay que
> regenerarlo.

Metodología y verificaciones: `Metodologia_Supermercados_INDEC.md`.

## Qué genera (en `datos-drive/`)

| Archivo | Base de origen | Período | Dimensiones propias |
|---|---|---|---|
| `Supermercados_INDEC_jurisdiccion_mensual.csv` | `serie_supermercados.xlsx`, Cuadro 6 (indec.gob.ar) | 2017-01 → 2026-08 | `jurisdiccion` (26), `metrica` (ventas corrientes, ventas constantes, operaciones) |

Cierra en `metrica, valor`, el esquema canónico del Monitor.

```
anio,n_mes,mes,periodo,jurisdiccion,metrica,valor,calidad
2026,7,2026-07-01,2026-07,Salta,ventas_corrientes_pesos,46149775811.14,PROVISORIO
2026,7,2026-07-01,2026-07,Salta,ventas_constantes_pesos,46149775811.14,PROVISORIO
2026,7,2026-07-01,2026-07,Salta,cantidad_operaciones,1166717,PROVISORIO
```

## 1. Requisitos

```
pip install openpyxl xlrd
```

`openpyxl` lee la planilla actual (`.xlsx`); `xlrd` lee la serie histórica 2017-2022, que es un
`.xls` viejo (BIFF) y se usa sólo como control cruzado —si falta, la corrida sigue y lo reporta—.
Nada más: la descarga usa sólo `urllib` de la biblioteca estándar.

## 2. Correr el script

```
python actualizar_supermercados_indec.py
```

| Argumento | Para qué |
|---|---|
| `--salida DIR` | Carpeta de salida. Por defecto, `datos-drive/` |
| `--fuentes DIR` | Caché de los archivos originales |
| `--ipc PATH` | CSV del deflactor. Por defecto, `sitio-indicadores/datos/ipc_noa_mensual.csv` |
| `--actualizar-ipc` | Refresca el IPC NOA desde datos.gob.ar |
| `--sin-historico` | Saltea el control cruzado contra la serie histórica |

**Cuidado con `--actualizar-ipc`.** `ipc_noa_mensual.csv` es un archivo **compartido por todo el
sitio**: al extenderlo se mueve la base de los pesos constantes de *todos* los tableros que
deflactan (Ejecución presupuestaria, Recursos, Recaudación), y las etiquetas «pesos constantes de
…» cambian en el próximo build. Por eso está apagado por defecto. Si se usa, hay que rehacer el
build del sitio y regenerar este CSV.

## 3. Cómo resuelve la descarga (y por qué así)

- **La URL es estable y el archivo se sobreescribe todos los meses.** `serie_supermercados.xlsx`
  siempre está en la misma dirección y el INDEC reemplaza su contenido al publicar cada informe.
  Cachear por nombre fijo escondería el cambio, así que la copia local va **fechada**:
  `fuentes/indec_supermercados/serie_supermercados_AAAA-MM-DD.xlsx`. Guardar el original permite
  explicar después por qué un número cambió. Dentro del mismo día no se vuelve a bajar.
- **La hoja se localiza por el título de la celda A1, no por su nombre.** Los nombres de hoja del
  archivo son inconsistentes —`Cuadro 2` sin punto, `Cuadro 6.` con punto— y el INDEC los cambia
  entre ediciones.
- **Las columnas se leen por encabezado.** Las jurisdicciones salen de la fila 3 y las variables de
  la fila 4, buscando las etiquetas literales `Ventas totales` y `Cantidad de operaciones` dentro
  del bloque de cada jurisdicción. **Si falta una, la corrida aborta** en vez de emitir un CSV
  corrido. Lo mismo con la unidad: si `Ventas totales` dejara de venir en «Miles de pesos», se
  corta.
- **Sólo se leen las filas con una fecha en la columna A**, lo que descarta encabezados, filas
  separadoras y la nota «Fuente: INDEC…» del pie.

## 4. Verificar antes de dar por buena la actualización

1. **La consola.** Tiene que cerrar con «Sin incidencias detectadas» o con una lista que se entienda.
   Hoy aparece una sola, esperada: el IPC NOA llega un mes menos que las ventas, así que el último
   mes sale sin pesos constantes.

2. **Las cuatro verificaciones automáticas**, que el script imprime y que tienen que dar todas en
   cero:

   | Control | Resultado esperado |
   |---|---|
   | Suma de las 25 jurisdicciones vs. Total del país | desvío relativo < `1e-9` (hoy `2,55e-13`) |
   | Cuadro por grupo de artículos vs. cuadro por boca de expendio | 3.016 valores, 0 discrepancias |
   | Cuadro nacional en millones vs. Total del país | 116 valores, 0 discrepancias |
   | Serie histórica 2017-2022 (otro archivo del INDEC) vs. la actual, Salta | 69 meses, 0 discrepancias |

3. **Cobertura.** 26 jurisdicciones × 116 meses consecutivos, de 2017-01 a 2026-08, sin huecos.
   9.022 filas.

4. **La base de los pesos constantes**, que el script imprime: hoy **2026-07**, IPC = 12.181,1952.
   En el mes base, corrientes y constantes tienen que dar **idénticos**.

5. **Los provisorios**: exactamente 24 meses, hoy de 2024-09 en adelante.

6. **Valores de control de Salta**, que tienen que salir clavados:

   | Mes | Ventas corrientes | Ventas constantes | Operaciones |
   |---|---|---|---|
   | 2017-01 | 529.248.073,00 | 63.452.610.755,73 | 1.527.981 |
   | 2020-04 | 1.448.956.560,54 | 55.644.356.724,50 | 1.011.235 |
   | 2026-07 | 46.149.775.811,14 | 46.149.775.811,14 | 1.166.717 |
   | 2026-08 | 45.374.496.988,81 | — (sin IPC) | 1.146.918 |

   Total del país de 2026-08: **2.616.930.121.204,41** pesos corrientes y **73.573.039**
   operaciones. Salta pesa el **1,73 %** de las ventas del país.

7. **Reproducibilidad.** Dos corridas seguidas tienen que dar el mismo md5, y el bloque `python` de
   abajo tiene que ser idéntico al `.py` en disco.

8. **Formato**, con la skill `datasets`: decimal `.`, sin separador de miles, sin mojibake (ojo con
   `Córdoba`, `Entre Ríos`, `Neuquén`, `Río Negro` y `Tucumán`, que llevan tildes), sin negativos y
   sin claves duplicadas.

---

## Script completo

Guardar el bloque de abajo como `actualizar_supermercados_indec.py` **dentro de `datos-drive/`**.

```python
# -*- coding: utf-8 -*-
"""
Ventas y operaciones de supermercados por jurisdiccion (INDEC) -- base mensual.

Genera `Supermercados_INDEC_jurisdiccion_mensual.csv` a partir de la Encuesta de Supermercados
del INDEC, que publica una unica planilla con toda la serie:

    https://www.indec.gob.ar/ftp/cuadros/economia/serie_supermercados.xlsx

Se lee el Cuadro 6, "Ventas totales a precios corrientes por boca de expendio, metro cuadro y por
operacion segun jurisdiccion", que abre 26 jurisdicciones (el total del pais, la Ciudad de Buenos
Aires, los 24 partidos del Gran Buenos Aires, el resto de Buenos Aires y las 22 provincias
restantes) desde enero de 2017.

POR QUE NO SE PUBLICAN LAS BOCAS
    El cuadro trae una columna "Cantidad de bocas" y no se emite. No es el numero de supermercados
    que hay en la jurisdiccion: es el tamanio del panel relevado. La encuesta es, en palabras del
    INDEC, un "panel no probabilistico" de empresas "que cuentan por lo menos con alguna boca de
    expendio cuya superficie en el salon de ventas sea igual o supere los 200 m2". Publicarla al
    lado de las ventas invita a leerla como un censo de bocas, que es lo que no es. Que se trata
    de un panel va en el copete del indicador.

POR QUE LA ENCUESTA DE AUTOSERVICIOS MAYORISTAS NO ESTA ACA
    Porque no abre por provincia. Publica cuatro jurisdicciones -- total del pais, Ciudad de Buenos
    Aires, 24 partidos del Gran Buenos Aires y "Resto del pais" -- y Salta queda adentro de la
    ultima, sin forma de separarla. Verificado en `serie_autoservicios_mayoristas.xlsx` y en los
    cuadros 8 y 9 del historico `sh_super_mayoristas.xls`: la palabra "Salta" no aparece una sola
    vez. Su panel es de 33 empresas y ~190 bocas en todo el pais.

PESOS CONSTANTES
    Se deflacta con el IPC Nivel General Region NOA (INDEC, base dic-2016=100), el mismo archivo
    `ipc_noa_mensual.csv` que usa `adapters.py` en el sitio, y con la misma regla: cada mes se
    deflacta con SU propio indice y la base es el ultimo mes con IPC publicado, para que los montos
    reales sean comparables con los de los demas tableros.

        constantes = corrientes * IPC_base / IPC_del_mes

    Un mes sin IPC no lleva fila de constantes; se reporta como incidencia. La base se mueve cuando
    se actualiza el IPC, asi que el CSV hay que regenerarlo junto con el.

Formato de salida (convencion del repo): decimal '.', sin separador de miles, CSV con ',',
UTF-8 con BOM.

Correr:  python actualizar_supermercados_indec.py [--salida DIR] [--fuentes DIR] [--ipc PATH]
                                                  [--actualizar-ipc] [--sin-historico]
"""

import argparse
import csv
import datetime
import io
import json
import os
import statistics
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.abspath(__file__))

URL_XLSX = "https://www.indec.gob.ar/ftp/cuadros/economia/serie_supermercados.xlsx"
URL_HIST = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_super_mayoristas.xls"
IPC_SERIE = "148.3_INIVELNOA_DICI_M_21"   # IPC Nivel General Region NOA, base dic-2016
IPC_API = ("https://apis.datos.gob.ar/series/api/series/?ids=%s&limit=5000&format=json"
           % IPC_SERIE)

UA = {"User-Agent": "CESS-Salta-indicadores/1.0 (indicadores PDES 2030)"}

# El INDEC: "los datos permanecen en estado provisorio hasta 24 meses posteriores a su
# publicacion". El archivo actual ya no los marca; el historico si, con un asterisco en el nombre
# del mes, y son exactamente los ultimos 24. Se aplica la regla por calculo.
MESES_PROVISORIOS = 24

SALIDA = "Supermercados_INDEC_jurisdiccion_mensual.csv"
CAMPOS = ["anio", "n_mes", "mes", "periodo", "jurisdiccion", "metrica", "valor", "calidad"]

# Orden de emision de las metricas dentro de cada mes y jurisdiccion.
ORDEN_METRICA = {"ventas_corrientes_pesos": 0, "ventas_constantes_pesos": 1,
                 "cantidad_operaciones": 2}

MESES_ES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
            "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
            "noviembre": 11, "diciembre": 12}

incidencias = []


def inc(msg):
    incidencias.append(msg)


# --------------------------------------------------------------------------- descarga y escritura

def bajar(url, dest, headers=None, refrescar=False):
    """Descarga con cache y escritura atomica. `refrescar` fuerza la re-descarga."""
    if os.path.exists(dest) and not refrescar:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("   bajando %s" % os.path.basename(dest))
    req = urllib.request.Request(url, headers=headers or {})
    tmp = dest + ".tmp"
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as fh:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    os.replace(tmp, dest)
    return dest


def escribir_csv(ruta, campos, filas):
    with io.open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print("   -> %s (%d filas)" % (os.path.basename(ruta), len(filas)))


# ------------------------------------------------------------------------------------------- IPC

def leer_ipc(path):
    """`ipc_noa_mensual.csv` -> {(anio, mes): indice}. Sin BOM y con CRLF, tal como esta en disco."""
    if not os.path.exists(path):
        raise SystemExit("No encuentro el IPC en %s (usar --ipc para indicar otra ruta)" % path)
    ipc = {}
    with io.open(path, encoding="utf-8-sig") as fh:
        for fila in csv.DictReader(fh):
            t = (fila.get("indice_tiempo") or "").strip()
            v = (fila.get("ipc_ng_noa") or "").strip()
            if len(t) >= 7 and v:
                ipc[(int(t[:4]), int(t[5:7]))] = float(v)
    if not ipc:
        raise SystemExit("El IPC de %s quedo vacio" % path)
    return ipc


def bajar_ipc(path):
    """Refresca `ipc_noa_mensual.csv` desde la API de datos.gob.ar.

    Es un archivo COMPARTIDO por todo el sitio, asi que solo se toca con --actualizar-ipc y solo
    si la respuesta trae al menos tantos meses como el archivo en disco: una API que contesta
    corto no debe truncar el deflactor de los demas tableros.
    """
    print("   actualizando el IPC NOA desde datos.gob.ar")
    req = urllib.request.Request(IPC_API, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))["data"]
    nuevos = [(str(f[0]), f[1]) for f in data if f[1] is not None]
    previos = leer_ipc(path) if os.path.exists(path) else {}
    if len(nuevos) < len(previos):
        inc("la API del IPC devolvio %d meses contra %d del archivo; no se actualizo"
            % (len(nuevos), len(previos)))
        return
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("indice_tiempo,ipc_ng_noa\n")
        for t, v in nuevos:
            fh.write("%s,%s\n" % (t[:10], ("%.4f" % float(v)).rstrip("0").rstrip(".")))
    os.replace(tmp, path)
    print("   IPC NOA actualizado: %d meses, hasta %s" % (len(nuevos), nuevos[-1][0][:7]))


# --------------------------------------------------------------------- lectura de la planilla

def abrir(path):
    import openpyxl
    return openpyxl.load_workbook(path, data_only=True)


def hoja_por_titulo(wb, *frases):
    """Localiza una hoja por el texto de A1, no por su nombre.

    Los nombres de hoja del archivo son inconsistentes ("Cuadro 2" sin punto, "Cuadro 6." con
    punto) y el INDEC los cambia entre ediciones. El titulo de A1, en cambio, describe el cuadro.
    """
    claves = [f.lower() for f in frases]
    for ws in wb.worksheets:
        t = ws.cell(row=1, column=1).value
        t = str(t).lower() if t is not None else ""
        if all(k in t for k in claves):
            return ws
    raise SystemExit("No encuentro la hoja cuyo titulo contenga: %s" % ", ".join(frases))


def filas(ws):
    return list(ws.iter_rows(values_only=True))


def bloques_jurisdiccion(fila_jur):
    """Fila de jurisdicciones -> [(orden, nombre, col_ini, col_fin)], saltando la columna Periodo."""
    marcas = [(j, str(c).strip()) for j, c in enumerate(fila_jur) if c not in (None, "")]
    # La primera marca es la columna del periodo (columna A); de ahi en adelante, jurisdicciones.
    if len(marcas) < 2 or marcas[0][0] != 0:
        raise SystemExit("La fila de jurisdicciones no arranca en la columna A")
    out = []
    for k in range(1, len(marcas)):
        ini = marcas[k][0]
        fin = marcas[k + 1][0] if k + 1 < len(marcas) else len(fila_jur)
        out.append((k - 1, marcas[k][1], ini, fin))
    return out


def col_de(fila_var, ini, fin, etiqueta, jur):
    """Columna de una variable dentro del bloque de una jurisdiccion. Aborta si no esta.

    Se lee por el nombre del encabezado, nunca por posicion: si el INDEC agrega o reordena una
    columna, es preferible que la corrida se caiga antes que emitir un CSV corrido.
    """
    for j in range(ini, fin):
        if str(fila_var[j]).strip() == etiqueta:
            return j
    raise SystemExit("No encuentro la columna '%s' de %s" % (etiqueta, jur))


def filas_de_datos(rows):
    """Solo las filas con una fecha en la columna A: descarta encabezados, separadores y la nota
    'Fuente: INDEC...' del pie."""
    return [r for r in rows if isinstance(r[0], datetime.datetime)]


# ------------------------------------------------------------------------------ verificaciones

def saltos_de_magnitud(pares, etiqueta, minimo=24):
    """Regla de la skill `datasets`: un valor >100x o <1/100 de la mediana de su serie. Se reporta
    CON los periodos y no se corrige: en esta fuente el candidato natural es la inflacion, que es
    dato real."""
    vals = [v for _, v in pares if v]
    if len(vals) < minimo:
        return
    med = statistics.median(vals)
    if not med:
        return
    raros = [(p, v) for p, v in pares if v and (v / med > 100 or v / med < 0.01)]
    if raros:
        inc("salto de orden de magnitud en %s: %d valores (ej. %s)"
            % (etiqueta, len(raros), ", ".join("%s=%.4g" % r for r in raros[:3])))


def verif_suma_pais(datos, jurs):
    """El Total del pais tiene que ser la suma de las otras 25 jurisdicciones."""
    nom_total = jurs[0]
    partes = jurs[1:]
    peor = 0.0
    for var in ("ventas", "operaciones"):
        for per in sorted({p for p, _ in datos}):
            t = datos.get((per, nom_total), {}).get(var)
            if not t:
                continue
            s = sum(datos.get((per, j), {}).get(var, 0.0) for j in partes)
            peor = max(peor, abs(s - t) / t)
    if peor > 1e-9:
        inc("la suma de las jurisdicciones no da el total del pais (desvio relativo %.2e)" % peor)
    print("   suma de jurisdicciones vs. total del pais: desvio relativo maximo %.2e" % peor)


def verif_cuadro5(wb, datos):
    """El 'Total' del cuadro de ventas por grupo de articulos tiene que dar lo mismo que el
    cuadro por boca de expendio. Son dos cuadros distintos del mismo archivo."""
    ws = hoja_por_titulo(wb, "grupo de art", "jurisdicci")
    rows = filas(ws)
    bl = bloques_jurisdiccion(rows[2])
    dif = 0
    comparados = 0
    for _, nom, ini, fin in bl:
        c = col_de(rows[3], ini, fin, "Total", nom)
        for r in filas_de_datos(rows):
            per = (r[0].year, r[0].month)
            esperado = datos.get((per, nom), {}).get("ventas")
            if esperado is None or r[c] is None:
                continue
            comparados += 1
            if abs(float(r[c]) * 1000.0 - esperado) > 0.01:
                dif += 1
    if dif:
        inc("el cuadro por grupo de articulos no cierra con el de bocas en %d de %d valores"
            % (dif, comparados))
    print("   cuadro por grupo de articulos: %d valores comparados, %d discrepancias"
          % (comparados, dif))


def verif_cuadro3(wb, datos, nom_total):
    """El cuadro nacional en millones de pesos tiene que dar el total del pais del cuadro 6."""
    ws = hoja_por_titulo(wb, "millones de pesos", "precios constantes")
    dif = 0
    comparados = 0
    for r in filas_de_datos(filas(ws)):
        per = (r[0].year, r[0].month)
        esperado = datos.get((per, nom_total), {}).get("ventas")
        if esperado is None or r[1] is None:
            continue
        comparados += 1
        if abs(float(r[1]) * 1e6 - esperado) > 0.01:
            dif += 1
    if dif:
        inc("el cuadro nacional en millones no cierra con el total del pais en %d de %d valores"
            % (dif, comparados))
    print("   cuadro nacional en millones: %d valores comparados, %d discrepancias"
          % (comparados, dif))


def verif_historico(path, datos, jur="Salta"):
    """Control cruzado contra OTRO archivo del INDEC: la serie historica 2017-2022, que es un .xls
    viejo (BIFF) y se lee con xlrd.

    No es fuente: el archivo actual la reemplaza y llega cuatro anios mas lejos. Sirve para
    confirmar que la lectura de la planilla nueva reproduce lo que el INDEC publicaba antes.
    """
    try:
        import xlrd
    except ImportError:
        inc("xlrd no esta instalado: no se pudo correr el control contra la serie historica")
        return
    wb = xlrd.open_workbook(path)
    sh = None
    for nm in wb.sheet_names():
        s = wb.sheet_by_name(nm)
        t = str(s.cell_value(0, 0)) if s.nrows else ""
        if "Supermercados" in t and "por boca de expendio" in t:
            sh = s
            break
    if sh is None:
        inc("no encontre el cuadro por boca de expendio en la serie historica")
        return
    cv = {}
    for j in range(sh.ncols):
        v = str(sh.cell_value(2, j)).strip()
        if v:
            cv[v] = j
    c_ven, c_ope = cv.get("Ventas totales"), cv.get("Cantidad de operaciones")
    if c_ven is None or c_ope is None:
        inc("la serie historica no trae las columnas esperadas")
        return
    ini = None
    for i in range(sh.nrows):
        if str(sh.cell_value(i, 0)).strip() == jur:
            ini = i
            break
    if ini is None:
        inc("no encontre %s en la serie historica" % jur)
        return
    anio = None
    dif = []
    comparados = 0
    for i in range(ini + 1, sh.nrows):
        if str(sh.cell_value(i, 0)).strip():
            break
        a = sh.cell_value(i, 1)
        if isinstance(a, float) and a > 2000:
            anio = int(a)
        m = MESES_ES.get(str(sh.cell_value(i, 2)).strip().rstrip("*").strip().lower())
        if not anio or not m or not isinstance(sh.cell_value(i, c_ven), float):
            continue
        d = datos.get(((anio, m), jur))
        if not d:
            continue
        comparados += 1
        if (abs(float(sh.cell_value(i, c_ven)) * 1000.0 - d["ventas"]) > 0.01
                or float(sh.cell_value(i, c_ope)) != d["operaciones"]):
            dif.append("%d-%02d" % (anio, m))
    if dif:
        inc("la serie historica no coincide con la actual en %s: %s"
            % (jur, ", ".join(dif[:6])))
    print("   serie historica (%s): %d meses comparados, %d discrepancias"
          % (jur, comparados, len(dif)))


# ------------------------------------------------------------------------------------- principal

def construir(ws):
    """Cuadro por boca de expendio -> ({(periodo, jurisdiccion): {...}}, [jurisdicciones])."""
    rows = filas(ws)
    bl = bloques_jurisdiccion(rows[2])
    datos = {}
    jurs = []
    for _, nom, ini, fin in bl:
        jurs.append(nom)
        c_ven = col_de(rows[3], ini, fin, "Ventas totales", nom)
        c_ope = col_de(rows[3], ini, fin, "Cantidad de operaciones", nom)
        u_ven = str(rows[4][c_ven]).strip()
        if u_ven != "Miles de pesos":
            raise SystemExit("Las ventas de %s no vienen en miles de pesos sino en '%s'"
                             % (nom, u_ven))
        for r in filas_de_datos(rows):
            per = (r[0].year, r[0].month)
            v, o = r[c_ven], r[c_ope]
            if v is None or o is None:
                inc("falta un valor de %s en %d-%02d" % (nom, per[0], per[1]))
                continue
            if not isinstance(v, (int, float)) or not isinstance(o, (int, float)):
                inc("valor no numerico en %s, %d-%02d" % (nom, per[0], per[1]))
                continue
            # Las ventas vienen en miles de pesos con mas de tres decimales, asi que x1000 da
            # pesos CON centavos, no pesos enteros. Se redondea a 2 decimales.
            datos[(per, nom)] = {"ventas": round(float(v) * 1000.0, 2),
                                 "operaciones": int(round(float(o)))}
    return datos, jurs


def armar_filas(datos, jurs, ipc):
    periodos = sorted({p for p, _ in datos})
    if not periodos:
        raise SystemExit("No se leyo ningun periodo")
    # Huecos en la serie.
    esperados = []
    y, m = periodos[0]
    while (y, m) <= periodos[-1]:
        esperados.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    faltan = [p for p in esperados if p not in periodos]
    if faltan:
        inc("faltan %d meses en la serie (ej. %s)"
            % (len(faltan), ", ".join("%d-%02d" % p for p in faltan[:4])))

    provisorios = set(periodos[-MESES_PROVISORIOS:])
    p_base = max(ipc)
    base = ipc[p_base]
    sin_ipc = [p for p in periodos if p not in ipc]
    if sin_ipc:
        inc("el IPC NOA no llega a %d %s de la serie (%s): %s sin pesos constantes"
            % (len(sin_ipc), "mes" if len(sin_ipc) == 1 else "meses",
               ", ".join("%d-%02d" % p for p in sin_ipc),
               "sale" if len(sin_ipc) == 1 else "salen"))

    orden_jur = {j: i for i, j in enumerate(jurs)}
    out = []
    for (per, jur), d in datos.items():
        anio, n_mes = per
        com = {"anio": anio, "n_mes": n_mes,
               "mes": "%d-%02d-01" % per, "periodo": "%d-%02d" % per,
               "jurisdiccion": jur,
               "calidad": "PROVISORIO" if per in provisorios else "DEFINITIVO"}
        vals = [("ventas_corrientes_pesos", d["ventas"]),
                ("cantidad_operaciones", d["operaciones"])]
        if per in ipc:
            vals.append(("ventas_constantes_pesos", round(d["ventas"] * base / ipc[per], 2)))
        for met, val in vals:
            f = dict(com)
            f["metrica"] = met
            f["valor"] = val
            out.append(f)
    out.sort(key=lambda f: (orden_jur[f["jurisdiccion"]], f["anio"], f["n_mes"],
                            ORDEN_METRICA[f["metrica"]]))

    # Saltos de orden de magnitud, por jurisdiccion y metrica.
    for jur in jurs:
        for met in ORDEN_METRICA:
            pares = [(f["periodo"], f["valor"]) for f in out
                     if f["jurisdiccion"] == jur and f["metrica"] == met]
            saltos_de_magnitud(pares, "%s / %s" % (jur, met))

    return out, p_base, base, periodos, provisorios


def main():
    ap = argparse.ArgumentParser(
        description="Ventas y operaciones de supermercados por jurisdiccion (INDEC)")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "indec_supermercados"),
                    help="Cache de los archivos originales")
    ap.add_argument("--ipc", default=os.path.join(os.path.dirname(RAIZ), "sitio-indicadores",
                                                  "datos", "ipc_noa_mensual.csv"),
                    help="CSV del IPC NOA que se usa como deflactor")
    ap.add_argument("--actualizar-ipc", action="store_true",
                    help="Refresca el IPC NOA desde datos.gob.ar (archivo compartido por el sitio)")
    ap.add_argument("--sin-historico", action="store_true",
                    help="Saltea el control cruzado contra la serie historica 2017-2022")
    args = ap.parse_args()

    hoy = datetime.date.today().isoformat()

    print("A. Fuente")
    # La URL es estable y el INDEC sobreescribe el archivo cada mes, asi que la cache va fechada:
    # guardar el original permite explicar despues por que un numero cambio.
    x = bajar(URL_XLSX, os.path.join(args.fuentes, "serie_supermercados_%s.xlsx" % hoy), UA)
    wb = abrir(x)
    ws = hoja_por_titulo(wb, "por boca de expendio", "jurisdicci")
    print("   hoja '%s': %s" % (ws.title, str(ws.cell(row=1, column=1).value)[:78]))

    print("B. Lectura")
    datos, jurs = construir(ws)
    periodos = sorted({p for p, _ in datos})
    print("   %d jurisdicciones x %d meses, de %d-%02d a %d-%02d"
          % (len(jurs), len(periodos), periodos[0][0], periodos[0][1],
             periodos[-1][0], periodos[-1][1]))

    print("C. Deflactor")
    if args.actualizar_ipc:
        bajar_ipc(args.ipc)
    ipc = leer_ipc(args.ipc)
    print("   IPC NOA: %d meses, hasta %d-%02d" % (len(ipc), max(ipc)[0], max(ipc)[1]))

    filas_out, p_base, base, periodos, provisorios = armar_filas(datos, jurs, ipc)
    print("   base de los pesos constantes: %d-%02d (IPC = %s)" % (p_base[0], p_base[1], base))
    print("   provisorios: %d meses, de %d-%02d en adelante"
          % (len(provisorios), min(provisorios)[0], min(provisorios)[1]))

    print("D. Verificaciones")
    verif_suma_pais(datos, jurs)
    verif_cuadro5(wb, datos)
    verif_cuadro3(wb, datos, jurs[0])
    if not args.sin_historico:
        h = bajar(URL_HIST, os.path.join(args.fuentes, "sh_super_mayoristas.xls"), UA)
        verif_historico(h, datos)

    print("E. Salida")
    escribir_csv(os.path.join(args.salida, SALIDA), CAMPOS, filas_out)

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
