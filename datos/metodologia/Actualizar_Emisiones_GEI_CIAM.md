# Actualización — Emisiones de GEI por jurisdicción, sector, subsector y gas (CIAM)

Genera dos CSV a partir de **«Emisiones anuales de GEI desagregadas por provincia»**, que publica
el Centro de Información Ambiental (CIAM) de la Subsecretaría de Ambiente:

| archivo | filas | contenido |
|---|---|---|
| `Emisiones_GEI_Salta_sector_subsector_gas_anual.csv` | 2.044 | Salta al máximo detalle: año, sector, subsector, gas, toneladas de gas, toneladas de CO2e y el potencial implícito |
| `Emisiones_GEI_jurisdiccion_sector_anual.csv` | 1.625 | las 25 jurisdicciones por año y sector, sólo CO2e |

El dato original es el **Primer Informe Bienal de Transparencia de la República Argentina a la
CMNUCC** (2024). Serie 2010–2022, actualizado el 22 de enero de 2025.

Lo que significa, sus límites y los hallazgos sobre la fuente están en
`Metodologia_Emisiones_GEI_CIAM.md`. Lo imprescindible: **es el inventario nacional
territorializado, no una medición provincial**, y el 12 % de las emisiones del país no está
asignado a ninguna jurisdicción.

## Lo que no se puede deducir mirando la página

La URL del repositorio —`repositorio.php?tid=9&stid=36&did=422`— **es una cáscara JavaScript: no
tiene ningún enlace de descarga**. Los endpoints reales están en su propio
`js/site.repositorio.js`, y el `did` de la URL es el id del dataset:

```
https://ciam.ambiente.gob.ar/dt_csv.php?dt_id=422               <- el CSV completo (4,4 MB)
https://ciam.ambiente.gob.ar/get_datasets.php?dt_id=422&mode=2  <- los metadatos en JSON
```

**Para traer otro dataset del CIAM alcanza con cambiar el `dt_id`**, que es el `did` de su URL. El
script tiene ese id en la constante `DATASET_ID`.

El archivo viene con separador `;`, campos entre comillas, decimal `.` y sin salto de línea final.

## 1. Requisitos

Sólo la biblioteca estándar de Python 3.

```powershell
python --version
```

## 2. Correr el script

```powershell
cd G:\Documents\CESS\Indicadores\datos-drive
```

```powershell
python actualizar_emisiones_gei_ciam.py --refrescar
```

Sin `--refrescar` reutiliza lo que ya está en `fuentes/emisiones_gei_ciam/`.

Opciones: `--salida DIR` (carpeta de salida), `--fuentes DIR` (caché), `--refrescar`.

## 3. Verificar antes de dar por buena la actualización

La corrida imprime todo lo que sigue. **Si algo no cierra, no se copia al sitio.**

1. **El potencial de calentamiento.** Es la verificación más importante de esta fuente y la razón
   por la que existe: el metadato oficial **se contradice** —afirma AR5 en el campo «Alcance» y
   SAR en el campo «Fórmula»—, y el cociente entre las dos columnas del dataset es el único
   árbitro. Tiene que decir **«15 gases coinciden con AR5»**. Si algún gas dejara de coincidir, la
   fuente cambió de potenciales y **toda la serie deja de ser comparable con la anterior**: hay
   que revisar la metodología antes de publicar nada.

2. **Formato numérico** — `0 valores sin parsear`.

3. **Reconciliación** — `0 desvíos en Salta, 0 por jurisdicción`. Es la comprobación de que las dos
   tablas de salida suman exactamente lo mismo que el archivo de origen, año por año.

4. **Negativos** — se informan y **no se recortan**: son absorciones. En la corrida de referencia
   son 1.005 en el país y 42 en Salta.

5. **Valores de control** — los quince tienen que dar `OK`:

| control | valor |
|---|---|
| Filas del origen · de Salta | 43.682 · 2.044 |
| Años · jurisdicciones · sectores · subsectores | 13 · 25 · 5 · 22 |
| Salta 2022, con · sin uso de la tierra | 12.923.057 · 6.923.010 t CO2e |
| País 2022, con · sin uso de la tierra | 400.920.592 · 349.515.942 t CO2e |
| Participación de Salta 2022 | 3,22 % |
| Puesto de Salta 2022, con · sin uso de la tierra | 9.º · 12.º |
| Filas con CO2e negativo, país · Salta | 1.005 · 42 |

   **Estos valores cambian cuando Argentina presenta un informe nuevo a la CMNUCC**, que es cuando
   se extiende la serie. Si cambian los años ya publicados, la fuente **recalculó el inventario
   hacia atrás** —pasa habitualmente entre informes— y eso es noticia: hay que comprobarlo y
   después actualizar la lista `CONTROLES` del script y las tablas de la metodología.

6. **Incidencias** — en la corrida de referencia son dos, las dos por el mismo hecho: la entrada de
   «2B. Industria química» al inventario de Salta en 2021. Cualquier incidencia nueva se analiza
   antes de publicar.

## 4. Copiar al sitio

```powershell
Copy-Item G:\Documents\CESS\Indicadores\datos-drive\Emisiones_GEI_Salta_sector_subsector_gas_anual.csv,G:\Documents\CESS\Indicadores\datos-drive\Emisiones_GEI_jurisdiccion_sector_anual.csv G:\Documents\CESS\Indicadores\sitio-indicadores\datos\ -Force
```

```powershell
Copy-Item G:\Documents\CESS\Indicadores\datos-drive\Metodologia_Emisiones_GEI_CIAM.md,G:\Documents\CESS\Indicadores\datos-drive\Actualizar_Emisiones_GEI_CIAM.md G:\Documents\CESS\Indicadores\sitio-indicadores\datos\metodologia\ -Force
```

Y reconstruir el sitio:

```powershell
cd G:\Documents\CESS\Indicadores\sitio-indicadores; python build.py
```

El tema del sitio es `emisiones-gei` (`adapters.emisiones_gei()` y la entrada en `catalog.TEMAS`).
Dos cosas conviene tener presentes al tocarlo:

- **El total se publica dos veces**, con y sin el sector `4. Uso de la tierra`. Si se agrega un
  sector nuevo al inventario, hay que revisar que la constante `GEI_SECTOR_USO_TIERRA` siga
  nombrando al correcto.
- **La métrica «Absorciones» existe porque el dato no se ve de otro modo**: adentro de cada
  subsector las absorciones quedan compensadas, y el motor de gráficos descarta los valores no
  positivos en los rankings de barras. Suma las filas negativas con el signo dado vuelta.

## Script completo

Es el mismo archivo que `datos-drive/actualizar_emisiones_gei_ciam.py`, copiado acá para que el
runbook se sostenga solo.

```python
# -*- coding: utf-8 -*-
"""
Emisiones de gases de efecto invernadero por jurisdiccion, sector, subsector y gas (CIAM).

Genera dos CSV:

    Emisiones_GEI_Salta_sector_subsector_gas_anual.csv   -- Salta, al maximo detalle
    Emisiones_GEI_jurisdiccion_sector_anual.csv          -- las 25 jurisdicciones, por sector

ORIGEN
    "Emisiones anuales de GEI desagregadas por provincia", publicado por el Centro de Informacion
    Ambiental (CIAM) de la Subsecretaria de Ambiente. El dato sale del PRIMER INFORME BIENAL DE
    TRANSPARENCIA de la Republica Argentina a la Convencion Marco de las Naciones Unidas sobre el
    Cambio Climatico (CMNUCC), 2024. Serie 2010-2022, actualizado el 23 de enero de 2025.

COMO SE LLEGA AL ARCHIVO
    La pagina del repositorio (repositorio.php?tid=9&stid=36&did=422) es una cascara JavaScript:
    no tiene ningun enlace de descarga. Los endpoints reales estan en su propio
    `js/site.repositorio.js`, y el `did` de la URL es el id del dataset:

        https://ciam.ambiente.gob.ar/dt_csv.php?dt_id=422              -> el CSV completo
        https://ciam.ambiente.gob.ar/get_datasets.php?dt_id=422&mode=2 -> los metadatos

    El CSV viene con separador ';', campos entre comillas y decimal '.'.

EL POTENCIAL DE CALENTAMIENTO: EL METADATO SE CONTRADICE Y EL DATO DECIDE
    El PDF de metadatos dice dos cosas incompatibles. En "Alcance": que el CO2 equivalente se
    calcula con los potenciales a 100 anios del QUINTO informe del IPCC (AR5). En "Formula": que
    se usa el SEGUNDO informe (SAR). No es menor: el metano vale 28 en AR5 y 21 en SAR.

    Como el dataset trae las dos columnas -toneladas de gas y toneladas de CO2e-, el cociente ES
    el potencial usado. Verificado en las 43.681 filas: CH4 da 28,0 y N2O da 265,0, que es AR5.
    Los quince gases coinciden con AR5 y ninguno con SAR. El script deja esa comprobacion
    corriendo en cada actualizacion.

QUE ES Y QUE NO ES ESTE DATO
    Es el inventario NACIONAL territorializado, no una medicion hecha en cada provincia: las
    emisiones se asignan segun los datos de actividad que uso el inventario del pais. Lo que no se
    puede asignar queda en "Jurisdiccion sin determinar", que en 2022 es el 12 % del total
    nacional. Los valores negativos son absorciones (sumideros), no errores.

Formato de salida (convencion del repo): separador ',', decimal '.', sin separador de miles,
UTF-8 con BOM.

Correr:  python actualizar_emisiones_gei_ciam.py [--salida DIR] [--fuentes DIR] [--refrescar]
"""

import argparse
import collections
import csv
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
UA = {"User-Agent": "Mozilla/5.0 (compatible; CESS-Indicadores/1.0)"}

CIAM = "https://ciam.ambiente.gob.ar"
DATASET_ID = "422"
CSV_URL = CIAM + "/dt_csv.php?dt_id=" + DATASET_ID
META_URL = CIAM + "/get_datasets.php?dt_id=" + DATASET_ID + "&mode=2"

SALIDA_SALTA = "Emisiones_GEI_Salta_sector_subsector_gas_anual.csv"
SALIDA_JUR = "Emisiones_GEI_jurisdiccion_sector_anual.csv"
CAMPOS_SALTA = ["anio", "sector", "subsector", "tipo_de_gas", "toneladas_gas", "toneladas_co2e",
                "gwp_implicito"]
CAMPOS_JUR = ["anio", "jurisdiccion", "sector", "toneladas_co2e"]

JUR_SALTA = "Salta"

# Los cinco sectores del IPCC, con su numero adelante: asi el orden alfabetico de las series en
# los graficos es el orden del inventario, y las etiquetas entran en una leyenda.
SECTORES = {
    "Energía": "1. Energía",
    "Procesos industriales y uso de productos": "2. Procesos industriales",
    "Agricultura y Ganaderia": "3. Agricultura y ganadería",
    "Usos de la Tierra, Cambios de Uso de la Tierra y Silvicultura": "4. Uso de la tierra",
    "Residuos": "5. Residuos",
}
SECTOR_USO_TIERRA = SECTORES["Usos de la Tierra, Cambios de Uso de la Tierra y Silvicultura"]

# Tres jurisdicciones con nombre inmanejable o fuera de convencion del repo.
JURISDICCIONES = {
    "Ciudad Autónoma de Buenos Aires": "CABA",
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur": "Tierra del Fuego",
    "Jurisdiccion sin determinar": "Jurisdicción sin determinar",
}
SIN_DETERMINAR = "Jurisdicción sin determinar"

# Potenciales de calentamiento global a 100 anios. AR5 es lo que dice el campo "Alcance" del
# metadato y lo que efectivamente se cumple en el dato; SAR es lo que dice el campo "Formula".
# Se guardan los dos para poder decir cual de las dos afirmaciones vale.
GWP_AR5 = {"CO2": 1, "CH4": 28, "N2O": 265, "HFC-134a": 1300, "HFC-23": 12400, "HFC-125": 3170,
           "HFC-143a": 4800, "HFC-32": 677, "HFC-152a": 138, "HFC-227ea": 3350, "HFC-245fa": 858,
           "HFC-365": 804, "HFC-236fa": 8060, "PFC-143 (CF4)": 6630, "PFC-116 (C2F6)": 11100}
GWP_SAR = {"CO2": 1, "CH4": 21, "N2O": 310, "HFC-134a": 1300, "HFC-23": 11700, "HFC-125": 2800,
           "HFC-143a": 3800, "HFC-32": 650, "HFC-152a": 140, "HFC-227ea": 2900,
           "HFC-236fa": 6300, "PFC-143 (CF4)": 6500, "PFC-116 (C2F6)": 9200}

incidencias = []


def inc(msg):
    incidencias.append(msg)


def sector(s):
    k = " ".join(str(s).split())
    if k not in SECTORES:
        inc("sector desconocido: %r" % s)
    return SECTORES.get(k, k)


def jurisdiccion(s):
    k = " ".join(str(s).split())
    return JURISDICCIONES.get(k, k)


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
        with urllib.request.urlopen(req, timeout=300) as r:
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


def numero(s, etiqueta, fila):
    """Texto -> float en configuracion inglesa. Audita lo que no parsea.

    El archivo trae separador de campo ';' y decimal '.': una coma adentro de un campo numerico
    seria configuracion latina y cambiaria el valor, asi que se reporta en vez de adivinar.
    """
    t = str(s).strip()
    if not t:
        return None
    if "," in t:
        inc("coma en un campo numerico (%s, %s): %r" % (etiqueta, fila, s))
        return None
    try:
        return float(t)
    except ValueError:
        inc("valor no numerico (%s, %s): %r" % (etiqueta, fila, s))
        return None


# ------------------------------------------------------------------------------------- lectura

def leer(datos):
    """[dict por fila] del CSV del CIAM, normalizado."""
    filas = []
    # `newline=""` porque el archivo viene con CRLF y csv tiene que ver los saltos crudos.
    flujo = io.StringIO(datos.decode("utf-8-sig"), newline="")
    for r in csv.DictReader(flujo, delimiter=";"):
        anio = (r.get("año") or r.get("ano") or "").strip()
        jur = jurisdiccion(r.get("provincia"))
        sec = sector(r.get("sector"))
        sub = " ".join((r.get("subsector") or "").split())
        gas = " ".join((r.get("tipo_de_gas") or "").split())
        ident = "%s %s %s %s" % (anio, jur, sub, gas)
        filas.append({
            "anio": int(anio) if anio.isdigit() else None,
            "jurisdiccion": jur,
            "sector": sec,
            "subsector": sub,
            "tipo_de_gas": gas,
            "toneladas_gas": numero(r.get("valor_toneladas_gas"), "valor_toneladas_gas", ident),
            "toneladas_co2e": numero(r.get("valor_toneladas_co2e"), "valor_toneladas_co2e", ident),
        })
    return filas


def leer_metadatos(datos, destino=None):
    """Titulo, fuente y fechas del dataset, para dejarlos impresos en la corrida.

    La respuesta de `get_datasets.php?mode=2` pesa 4,4 MB porque trae el dataset entero otra vez
    adentro de `tab_datos`, que es exactamente el mismo contenido que el CSV. Se cachea sólo el
    bloque de metadatos: el archivo de datos ya esta guardado aparte.
    """
    if not datos:
        return {}
    try:
        meta = json.loads(datos.decode("utf-8")).get("tab_metadatos", {}) or {}
    except Exception as e:
        inc("no se pudieron leer los metadatos del CIAM: %s" % e)
        return {}
    if destino and len(datos) > 100000:
        with open(os.path.join(destino, "metadatos.json"), "w", encoding="utf-8") as f:
            json.dump({"tab_metadatos": meta}, f, ensure_ascii=False, indent=1)
    return meta


# ------------------------------------------------------------------------------ verificaciones

def verif_gwp(filas):
    """El cociente CO2e/gas ES el potencial de calentamiento usado. Resuelve la contradiccion
    del metadato, que afirma AR5 en un campo y SAR en otro.

    El cociente se calcula sobre los AGREGADOS de cada gas y no como mediana de los cocientes
    fila a fila: la fuente publica las toneladas de gas redondeadas a dos decimales, asi que en
    los gases traza -que se miden en decimas de tonelada- el cociente de una fila suelta se
    desvia hasta un 3 % por puro redondeo. Agregando, ese ruido desaparece.
    """
    gas_t = collections.defaultdict(float)
    co2e_t = collections.defaultdict(float)
    disp = collections.defaultdict(list)
    for f in filas:
        g, c = f["toneladas_gas"], f["toneladas_co2e"]
        if g:
            gas_t[f["tipo_de_gas"]] += g
            co2e_t[f["tipo_de_gas"]] += c
            disp[f["tipo_de_gas"]].append(c / g)
    ar5 = sar = 0
    print("   potencial de calentamiento implicito (suma CO2e / suma gas):")
    print("      %-16s %7s %12s %9s %9s %10s"
          % ("gas", "filas", "implicito", "AR5", "SAR", "filas +-1%"))
    for gas in sorted(disp, key=lambda k: -len(disp[k])):
        imp = co2e_t[gas] / gas_t[gas]
        a, s_ = GWP_AR5.get(gas), GWP_SAR.get(gas)
        es_ar5 = a is not None and abs(imp - a) <= 0.01 * a
        es_sar = s_ is not None and abs(imp - s_) <= 0.01 * s_
        ar5 += es_ar5
        sar += es_sar
        if not es_ar5:
            inc("el gas %s da un potencial implicito de %.1f, que no es el de AR5 (%s)"
                % (gas, imp, a))
        # Cuantas filas caen a menos del 1 % del valor agregado: lo que queda afuera es
        # redondeo de la fuente, no otro potencial.
        cerca = sum(1 for x in disp[gas] if abs(x - imp) <= 0.01 * imp)
        print("      %-16s %7d %12.1f %9s %9s %9.0f%%"
              % (gas, len(disp[gas]), imp, ("OK" if es_ar5 else a),
                 ("OK" if es_sar else s_), 100.0 * cerca / len(disp[gas])))
    print("   -> %d gases coinciden con AR5 y %d con SAR, sobre %d. El metadato afirma AR5 en "
          "'Alcance' y SAR en 'Formula': vale AR5." % (ar5, sar, len(disp)))
    if ar5 == len(disp) and sar < ar5:
        print("      (la ultima columna es la proporcion de filas cuyo cociente propio cae a "
              "menos del 1 % del agregado; lo que queda afuera es el redondeo a dos "
              "decimales de la fuente en los gases traza)")


def verif_formato(filas):
    sin = sum(1 for f in filas if f["toneladas_co2e"] is None or f["toneladas_gas"] is None)
    if sin:
        inc("%d filas con valores que no parsearon" % sin)
    neg = [f for f in filas if (f["toneladas_co2e"] or 0) < 0]
    negs = [f for f in neg if f["jurisdiccion"] == JUR_SALTA]
    print("   formato numerico: %d valores sin parsear" % sin)
    print("   valores negativos (absorciones, NO se recortan): %d en el pais, %d en Salta"
          % (len(neg), len(negs)))
    c = collections.Counter(f["subsector"] for f in neg)
    print("      por subsector: %s" % ", ".join("%s (%d)" % (k, v) for k, v in c.most_common(4)))


def verif_panel(filas):
    anios = sorted({f["anio"] for f in filas})
    jur = sorted({f["jurisdiccion"] for f in filas})
    sec = sorted({f["sector"] for f in filas})
    sub = sorted({f["subsector"] for f in filas})
    sal = [f for f in filas if f["jurisdiccion"] == JUR_SALTA]
    print("   panel: %d anios (%d-%d), %d jurisdicciones, %d sectores, %d subsectores"
          % (len(anios), anios[0], anios[-1], len(jur), len(sec), len(sub)))
    print("   Salta: %d filas, %d subsectores de los %d del pais, gases %s"
          % (len(sal), len({f["subsector"] for f in sal}), len(sub),
             "/".join(sorted({f["tipo_de_gas"] for f in sal}))))
    faltan = [(a, j) for a in anios for j in jur
              if not any(f["anio"] == a and f["jurisdiccion"] == j for f in filas)]
    if faltan:
        inc("%d combinaciones anio x jurisdiccion sin ninguna fila" % len(faltan))
    return anios, jur


def verif_reconciliacion(filas, salta_rows, jur_rows):
    """Los dos CSV de salida tienen que cerrar contra el archivo de origen, anio por anio."""
    orig_sal = collections.defaultdict(float)
    orig_jur = collections.defaultdict(float)
    for f in filas:
        if f["jurisdiccion"] == JUR_SALTA:
            orig_sal[f["anio"]] += f["toneladas_co2e"] or 0
        orig_jur[(f["anio"], f["jurisdiccion"])] += f["toneladas_co2e"] or 0
    sal = collections.defaultdict(float)
    for r in salta_rows:
        sal[r["anio"]] += r["toneladas_co2e"]
    jur = collections.defaultdict(float)
    for r in jur_rows:
        jur[(r["anio"], r["jurisdiccion"])] += r["toneladas_co2e"]
    n = 0
    for k in orig_sal:
        if abs(orig_sal[k] - sal[k]) > 0.5:
            n += 1
            inc("el CSV de Salta no cierra en %s: %.2f contra %.2f" % (k, sal[k], orig_sal[k]))
    m = 0
    for k in orig_jur:
        if abs(orig_jur[k] - jur.get(k, 0)) > 0.5:
            m += 1
            inc("el CSV por jurisdiccion no cierra en %s" % (k,))
    print("   reconciliacion contra el origen: %d desvios en Salta, %d por jurisdiccion" % (n, m))


def saltos_de_magnitud(filas):
    """Serie (jurisdiccion, sector) contra su mediana. Marca entradas nuevas al inventario."""
    por = collections.defaultdict(lambda: collections.defaultdict(float))
    for f in filas:
        por[(f["jurisdiccion"], f["sector"])][f["anio"]] += f["toneladas_co2e"] or 0
    n = 0
    for (j, s), serie in sorted(por.items()):
        vals = [v for v in serie.values() if v > 0]
        if len(vals) < 3:
            continue
        med = statistics.median(vals)
        for a, v in sorted(serie.items()):
            if v > 0 and (v / med > 20 or v / med < 0.05):
                n += 1
                if j == JUR_SALTA:
                    inc("%s / %s en %d: %.0f t, a %.1fx de la mediana de su serie"
                        % (j, s, a, v, v / med))
    print("   saltos de orden de magnitud por jurisdiccion y sector: %d (los de Salta, listados)"
          % n)


def _tot(filas, anio, jur=None, sin_uso_tierra=False):
    s = 0.0
    for f in filas:
        if f["anio"] != anio:
            continue
        if jur is not None and f["jurisdiccion"] != jur:
            continue
        if sin_uso_tierra and f["sector"] == SECTOR_USO_TIERRA:
            continue
        s += f["toneladas_co2e"] or 0
    return s


def _puesto(filas, anio, sin_uso_tierra=False):
    por = collections.defaultdict(float)
    for f in filas:
        if f["anio"] == anio and not (sin_uso_tierra and f["sector"] == SECTOR_USO_TIERRA):
            por[f["jurisdiccion"]] += f["toneladas_co2e"] or 0
    orden = sorted(por.items(), key=lambda t: -t[1])
    return [i for i, (j, _v) in enumerate(orden, 1) if j == JUR_SALTA][0]


CONTROLES = [
    ("filas del origen", lambda f: len(f), 43682),
    ("filas de Salta", lambda f: sum(1 for x in f if x["jurisdiccion"] == JUR_SALTA), 2044),
    ("anios", lambda f: len({x["anio"] for x in f}), 13),
    ("jurisdicciones", lambda f: len({x["jurisdiccion"] for x in f}), 25),
    ("sectores", lambda f: len({x["sector"] for x in f}), 5),
    ("subsectores", lambda f: len({x["subsector"] for x in f}), 22),
    ("Salta 2022, con uso de la tierra",
     lambda f: round(_tot(f, 2022, JUR_SALTA)), 12923057),
    ("Salta 2022, sin uso de la tierra",
     lambda f: round(_tot(f, 2022, JUR_SALTA, True)), 6923010),
    ("pais 2022, con uso de la tierra", lambda f: round(_tot(f, 2022)), 400920592),
    ("pais 2022, sin uso de la tierra", lambda f: round(_tot(f, 2022, None, True)), 349515942),
    ("participacion de Salta 2022 (%)",
     lambda f: round(100 * _tot(f, 2022, JUR_SALTA) / _tot(f, 2022), 2), 3.22),
    ("puesto de Salta 2022, con uso de la tierra", lambda f: _puesto(f, 2022), 9),
    ("puesto de Salta 2022, sin uso de la tierra", lambda f: _puesto(f, 2022, True), 12),
    ("filas con CO2e negativo (pais)",
     lambda f: sum(1 for x in f if (x["toneladas_co2e"] or 0) < 0), 1005),
    ("filas con CO2e negativo (Salta)",
     lambda f: sum(1 for x in f if (x["toneladas_co2e"] or 0) < 0
                   and x["jurisdiccion"] == JUR_SALTA), 42),
]


def verif_control(filas):
    ok = 0
    for etiqueta, fn, esperado in CONTROLES:
        valor = fn(filas)
        if valor == esperado:
            ok += 1
            marca = "OK "
        else:
            marca = "!! "
            inc("control '%s': se esperaba %s y da %s" % (etiqueta, esperado, valor))
        print("      %s%-46s %14s  (esperado %s)" % (marca, etiqueta, valor, esperado))
    print("   valores de control: %d de %d" % (ok, len(CONTROLES)))


def resumen(filas):
    anios = sorted({f["anio"] for f in filas})
    print("\n   Salta: emisiones por anio (t CO2e)")
    print("      %-6s %14s %14s %10s" % ("anio", "con uso tierra", "sin uso tierra", "% del país"))
    for a in anios:
        con = _tot(filas, a, JUR_SALTA)
        sin = _tot(filas, a, JUR_SALTA, True)
        print("      %-6d %14.0f %14.0f %9.2f%%" % (a, con, sin, 100 * con / _tot(filas, a)))
    print("   Salta 2022 por sector (t CO2e):")
    por = collections.defaultdict(float)
    for f in filas:
        if f["anio"] == 2022 and f["jurisdiccion"] == JUR_SALTA:
            por[f["sector"]] += f["toneladas_co2e"] or 0
    for s, v in sorted(por.items()):
        print("      %14.0f  %s" % (v, s))


# ------------------------------------------------------------------------------------- principal

def armar_salidas(filas):
    """Las dos tablas: Salta al maximo detalle, y las 25 jurisdicciones por sector."""
    salta = []
    for f in filas:
        if f["jurisdiccion"] != JUR_SALTA:
            continue
        g, c = f["toneladas_gas"], f["toneladas_co2e"]
        salta.append({
            "anio": f["anio"], "sector": f["sector"], "subsector": f["subsector"],
            "tipo_de_gas": f["tipo_de_gas"],
            "toneladas_gas": round(g, 2) if g is not None else "",
            "toneladas_co2e": round(c, 2) if c is not None else "",
            # Deja a la vista con que potencial se convirtio cada fila, que es lo que el metadato
            # oficial no acierta a decir.
            "gwp_implicito": round(c / g, 2) if g else "",
        })
    salta.sort(key=lambda r: (r["anio"], r["sector"], r["subsector"], r["tipo_de_gas"]))

    agg = collections.defaultdict(float)
    for f in filas:
        agg[(f["anio"], f["jurisdiccion"], f["sector"])] += f["toneladas_co2e"] or 0
    jur = [{"anio": a, "jurisdiccion": j, "sector": s, "toneladas_co2e": round(v, 2)}
           for (a, j, s), v in sorted(agg.items())]
    return salta, jur


def main():
    ap = argparse.ArgumentParser(
        description="Emisiones de GEI por jurisdiccion, sector, subsector y gas (CIAM / CMNUCC)")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "emisiones_gei_ciam"),
                    help="Cache de los archivos originales")
    ap.add_argument("--refrescar", action="store_true",
                    help="Vuelve a bajar todo, incluso lo cacheado")
    args = ap.parse_args()

    print("A. El inventario de GEI en el repositorio del CIAM")
    meta = leer_metadatos(bajar(META_URL, args.fuentes, "metadatos.json", args.refrescar),
                          args.fuentes)
    if meta:
        print("   %s" % meta.get("titulo", ""))
        print("   fuente: %s" % " ".join(str(meta.get("fuente", "")).split())[:150])
        print("   serie: %s a %s | actualizado: %s"
              % (meta.get("fecha_desde"), meta.get("fecha_hasta"), meta.get("fecha_ultima_act")))
    datos = bajar(CSV_URL, args.fuentes, "emisiones_gei_provincia.csv", args.refrescar)
    if datos is None:
        raise SystemExit("no se pudo bajar el inventario de GEI del CIAM")

    print("B. Lectura y normalizacion")
    filas = leer(datos)
    if not filas:
        raise SystemExit("el inventario vino vacio")
    salta, jur = armar_salidas(filas)

    print("C. Verificaciones")
    verif_formato(filas)
    verif_panel(filas)
    verif_gwp(filas)
    verif_reconciliacion(filas, salta, jur)
    saltos_de_magnitud(filas)
    verif_control(filas)
    resumen(filas)

    print("\nD. Escritura")
    escribir_csv(os.path.join(args.salida, SALIDA_SALTA), CAMPOS_SALTA, salta)
    escribir_csv(os.path.join(args.salida, SALIDA_JUR), CAMPOS_JUR, jur)

    if incidencias:
        print("\nINCIDENCIAS (%d):" % len(incidencias))
        for i, m in enumerate(incidencias, 1):
            print("  %2d. %s" % (i, m))
    else:
        print("\nSin incidencias.")


if __name__ == "__main__":
    main()
```
