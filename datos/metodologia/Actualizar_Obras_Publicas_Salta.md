# Actualización — Padrón de obras públicas de Salta, reclasificado

Genera `Obras_Publicas_Salta_padron_clasificado.csv` a partir del **Padrón Georreferenciado de
Obras Públicas de la Provincia de Salta (2020–2026)** que publica la Jefatura de Gabinete de
Ministros en `datospublicos.salta.gob.ar` bajo CC-BY 4.0.

El padrón trae 2.947 obras con área responsable, tipo, etapa, avance físico, monto de contrato,
financiamiento, departamento, municipio y coordenadas. **2.389 están al 100 %.**

Además de normalizar, el script agrega **dos clasificaciones propias del CESS** sobre el texto de
cada obra, porque el campo `tipo` de la fuente tiene nueve valores y «OTRAS» se lleva el 35 % del
padrón:

- `categoria` — qué se intervino (31 etiquetas: cordón cuneta, red de agua potable,
  establecimientos educativos, defensas y encauzamiento, …)
- `accion` — qué se hizo (construcción, ampliación, refacción y puesta en valor, mantenimiento y
  limpieza, provisión e instalación)

El detalle de las reglas, su orden de prioridad y los defectos de la fuente están en
`Metodologia_Obras_Publicas_Salta.md`.

## Lo único frágil de esta actualización, ya resuelto

**La URL de descarga cambia cuando el organismo republica el archivo**: el `resource_id` es nuevo
cada vez. Por eso el script **no la hardcodea**: pide `package_show` a la API de CKAN del portal
con el `dataset_id`, que sí es estable, y toma el primer recurso en formato CSV. Queda una URL de
respaldo por si la API no responde, y en ese caso el script lo dice como incidencia.

Si alguna vez cambia también el `dataset_id`, se busca el padrón en el portal y se reemplaza la
constante `DATASET`.

## Qué genera (en `datos-drive/`)

| archivo | filas | contenido |
|---|---|---|
| `Obras_Publicas_Salta_padron_clasificado.csv` | 2.947 | una fila por obra, con `categoria`, `accion`, `etiquetas`, `regla` y la geografía canónica |

Caché de los originales en `datos-drive/fuentes/obras_publicas_salta/`:
`package_show.json` y `padron_obras_publicas.csv`.

## 1. Requisitos

Sólo la biblioteca estándar de Python 3. No usa pandas ni openpyxl.

```powershell
python --version
```

## 2. Correr el script

```powershell
cd G:\Documents\CESS\Indicadores\datos-drive
```

```powershell
python actualizar_obras_publicas_salta.py --refrescar
```

Sin `--refrescar` reutiliza lo que ya está en `fuentes/obras_publicas_salta/`, que es lo que
conviene cuando sólo se tocaron las reglas de clasificación y no hace falta volver a bajar nada.

Para ver una por una las obras que ninguna regla alcanza:

```powershell
python actualizar_obras_publicas_salta.py --detalle-reglas
```

Opciones: `--salida DIR` (carpeta de salida), `--fuentes DIR` (caché), `--refrescar`,
`--detalle-reglas`.

## 3. Verificar antes de dar por buena la actualización

La corrida imprime todo lo que sigue. **Si algo no cierra, no se copia al sitio.**

1. **Formato numérico** — tiene que decir `0 sin parsear, 0 montos en cero, 0 avances fuera de
   rango`.
2. **Cobertura del clasificador** — el residuo `sin regla` tiene que quedar por debajo del 10 %.
   En la corrida de referencia es **4,1 %** (98 obras de 2.389). Si sube mucho, la fuente cambió la
   forma de nombrar las obras y hay que revisar las reglas.
3. **Reconciliación** — los siete cortes (categoría, acción, departamento, municipio, tipo de la
   fuente, área y financiamiento) tienen que sumar el total del padrón y el de las finalizadas.
4. **Geografía** — 23 departamentos, 60 municipios y **0 desvíos** en el cotejo municipio →
   departamento contra `Salta_recursos_municipios_mensual.csv`. Un municipio o departamento
   desconocido sale como incidencia: hay que agregar el alias en `MUNI_ALIAS`.
5. **Valores de control** — los ocho tienen que dar `OK`:

| control | valor |
|---|---|
| Filas del padrón | 2.947 |
| Obras al 100 % | 2.389 |
| Obras que la fuente rotula `OTRAS` | 1.048 |
| Departamentos · municipios | 23 · 60 |
| Obras al 100 % en General José de San Martín | 426 |
| Obras al 100 % en Capital | 381 |
| Coordenadas inválidas | 3 |

   **Estos valores cambian cuando el organismo actualiza el padrón.** Si cambian, hay que
   comprobar que el cambio tenga sentido —obras nuevas, obras que pasaron a finalizadas— y
   actualizar la lista `CONTROLES` del script y la tabla de la metodología.

6. **Incidencias** — en la corrida de referencia son nueve y todas conocidas: las tres
   coordenadas con la longitud repetida de la latitud (ids 255, 852, 853) y los seis pares de
   filas idénticas. Cualquier incidencia nueva se analiza antes de publicar.

## 4. Copiar al sitio

```powershell
Copy-Item G:\Documents\CESS\Indicadores\datos-drive\Obras_Publicas_Salta_padron_clasificado.csv G:\Documents\CESS\Indicadores\sitio-indicadores\datos\ -Force
```

```powershell
Copy-Item G:\Documents\CESS\Indicadores\datos-drive\Metodologia_Obras_Publicas_Salta.md,G:\Documents\CESS\Indicadores\datos-drive\Actualizar_Obras_Publicas_Salta.md G:\Documents\CESS\Indicadores\sitio-indicadores\datos\metodologia\ -Force
```

Y reconstruir el sitio:

```powershell
cd G:\Documents\CESS\Indicadores\sitio-indicadores; python build.py
```

El tema del sitio es `obras-publicas` (`adapters.obras_publicas()` y la entrada en
`catalog.TEMAS`). El adaptador usa **sólo las obras con `finalizada = 1`** y publica el padrón como
un corte con un único año, no como serie: el único año que trae la fuente es el de finalización
**prevista**, y el monto está en pesos corrientes sin fecha de precio.

## Script completo

Es el mismo archivo que `datos-drive/actualizar_obras_publicas_salta.py`, copiado acá para que el
runbook se sostenga solo.

```python
# -*- coding: utf-8 -*-
"""
Padron georreferenciado de obras publicas de Salta, reclasificado -- una fila por obra.

Genera:

    Obras_Publicas_Salta_padron_clasificado.csv

ORIGEN
    "Padron Georreferenciado de Obras Publicas de la Provincia de Salta (2020-2026)", publicado
    por la Jefatura de Gabinete de Ministros en datospublicos.salta.gob.ar bajo CC-BY 4.0.
    Son 2.947 obras con area responsable, tipo, etapa, avance fisico, monto de contrato,
    financiamiento, departamento, municipio y coordenadas.

POR QUE HAY QUE RECLASIFICAR
    El campo `tipo` que publica la fuente tiene nueve valores y "OTRAS" se lleva 1.048 obras,
    el 35 % del padron. Adentro de esa bolsa conviven defensas de rio, refacciones de escuela,
    terminales de omnibus y limpieza de canales. Con el padron tal cual no se puede contestar
    cuantas obras de cordon cuneta se hicieron ni cuanto se intervino en escuelas.

    Este script agrega dos clasificaciones propias, construidas sobre el texto de `nombre` y
    `descripcion`:

        categoria -- QUE se intervino (31 etiquetas: cordon cuneta, red de agua potable,
                     establecimientos educativos, ...)
        accion    -- QUE se hizo con eso (construccion, ampliacion, refaccion y puesta en
                     valor, mantenimiento y limpieza, provision e instalacion)

    Son dos ejes separados a proposito: "refacciones varias en escuela" es una escuela en el
    primero y una refaccion en el segundo, y asi se puede cruzar.

COMO CLASIFICA
    Lista ORDENADA de (etiqueta, expresion regular) evaluada sobre nombre + descripcion
    normalizados (minusculas, sin acentos, sin puntuacion). Gana la primera que matchea: el
    orden ES la prioridad, y va de lo especifico a lo generico (cordon cuneta antes que
    pavimento, nucleos humedos antes que red de agua, escuela antes que edificio). La columna
    `etiquetas` conserva TODAS las reglas que matchearon, no solo la ganadora, y la columna
    `regla` dice de donde salio la asignacion, asi cada fila queda auditable.

    Si ninguna regla matchea, cae a un respaldo por el `tipo` de la fuente. Si el tipo es
    "OTRAS" y tampoco hay regla, la obra queda en "Otras obras".

NO SE INVENTA NADA SOBRE EL MONTO
    `monto_contrato` son pesos corrientes SIN fecha de precio: `licitacion_anio` esta en cero
    en el 82 % de las filas, y entre las que si lo traen la brecha mediana hasta el fin
    previsto es de cuatro anios. Por eso el monto se publica tal cual, sin deflactar, y no se
    debe sumar entre anios. La metrica util del padron es la CANTIDAD de obras.

EL ANIO NO ES EL DE FINALIZACION REAL
    `fecha_fin_inicial` es la fecha de fin PREVISTA, no la efectiva: hay obras con avance
    100 % y fin previsto en 2026. Se publica como `anio_fin_previsto`, con ese nombre.

Formato de salida (convencion del repo): decimal '.', sin separador de miles, CSV con ',',
UTF-8 con BOM.

Correr:  python actualizar_obras_publicas_salta.py [--salida DIR] [--fuentes DIR] [--refrescar]
                                                   [--detalle-reglas]
"""

import argparse
import collections
import csv
import io
import json
import os
import re
import statistics
import sys
import unicodedata
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (compatible; CESS-Indicadores/1.0)"}

# El portal es un CKAN: el dataset tiene id estable y el recurso puede cambiar de id cuando
# republican el archivo. Se resuelve el recurso por la API en vez de hardcodear la descarga.
PORTAL = "https://datospublicos.salta.gob.ar"
DATASET = "a3ac6004-0430-42e3-ac16-50c9c5956083"
API = PORTAL + "/api/3/action/package_show?id=" + DATASET
# Respaldo por si la API no responde: la URL directa del recurso al 17-nov-2026.
RESPALDO = (PORTAL + "/dataset/" + DATASET + "/resource/6f0fb723-fafa-4fd3-a3a3-6c3e05dd209a"
            "/download/01_obras_publicas_salta_base_normalizada.csv")

SALIDA = "Obras_Publicas_Salta_padron_clasificado.csv"
CAMPOS = ["id", "nombre", "descripcion", "area_responsable", "tipo_fuente", "categoria",
          "accion", "etiquetas", "regla", "etapa", "finalizada", "porcentaje_avance",
          "monto_contrato", "financiamiento", "departamento", "municipio", "lat", "lng",
          "coord_valida", "anio_fin_previsto", "licitacion_anio"]

# Caja envolvente de Salta, generosa: sirve para detectar coordenadas rotas, no para validar
# la ubicacion exacta de cada obra.
LAT_MIN, LAT_MAX = -27.5, -21.0
LNG_MIN, LNG_MAX = -69.0, -61.0

incidencias = []


def inc(msg):
    incidencias.append(msg)


def norm(s):
    """Minusculas, sin acentos, sin puntuacion, espacios colapsados."""
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


# --------------------------------------------------------------------- la clasificacion propia
# ORDEN = PRIORIDAD. La primera que matchea gana. De lo especifico a lo generico.
CATEGORIAS = [
    # -- vialidad urbana ----------------------------------------------------------------
    ("Cordón cuneta",
     r"cordon ?cuneta|cordon y cuneta|cordones cuneta"),
    ("Veredas y peatonales",
     r"vereda|peatonal|senda peatona"),
    ("Adoquinado",
     r"adoquin"),
    ("Bacheo y mantenimiento vial",
     r"bacheo|bachear|\bbaches\b|perfilado|mantenimiento de calle|reparacion de calle"),
    ("Pavimento y calzadas",
     r"pavim|carpeta asfaltica|asfalt|hormigon simple|hormigon articulado|enripiado|\bripio\b|"
     r"estabilizado granular|calzada"),
    # -- conectividad vial --------------------------------------------------------------
    ("Puentes y alcantarillas",
     r"puente|alcantarill|\bbadeo\b|\bvado\b|pasarela"),
    ("Caminos y accesos",
     r"camino|acceso vial|\bruta\b|apertura de calle|senaletica|senalizacion|portal de acceso|"
     r"terminal de omnibus|estacion terminal|complejo fronterizo|paso fronterizo"),
    # -- agua y saneamiento -------------------------------------------------------------
    ("Núcleos húmedos y conexiones domiciliarias",
     r"nucleo ?s? ?humedo|conexion(es)? domiciliaria|modulo sanitario|sistema sanitario|"
     r"\bletrina"),
    ("Cloacas y saneamiento",
     r"cloacal|cloaca|saneamiento|efluente|colectora|planta de tratamiento|liquidos residuales|"
     r"desagote|\bbarros\b"),
    ("Red de agua potable",
     r"agua potable|red(es)? de agua|acueducto|cisterna|tanque de agua|distribucion de agua|"
     r"provision de agua|potabiliza|acceso al agua|agua corriente|agua para consumo|"
     r"\bpead\b|optimizacion de redes|recambio (general )?de red|electrobomba|"
     r"canerias? de impulsion|impulsion|\bbombeo\b|red municipal"),
    ("Pozos y perforaciones",
     r"\bpozo|perforacion"),
    # -- hidraulica ---------------------------------------------------------------------
    ("Defensas y encauzamiento",
     r"encauz|encauce|\bdefensa|margen|gavion|terraplen|erosion|\bcauce\b|rectificacion|"
     r"\bazud\b|\brepresa\b|\bdique\b|crecida"),
    ("Canales y desagües",
     r"\bcanal|desague|pluvial|drenaje|\bzanja"),
    ("Otras obras hidráulicas",
     r"hidraulic|hidric|\bcuenca"),
    # -- energia ------------------------------------------------------------------------
    ("Alumbrado público y luminarias",
     r"luminaria|alumbrado|iluminacion"),
    ("Red eléctrica y suministro de energía",
     r"electrific|electric|\benergia|media tension|baja tension|transformador|tendido|"
     r"interconexion|fotovoltaic|\bsolar\b|subestacion"),
    ("Gas",
     r"\bgas\b|gasoducto|gasificacion|odorizacion"),
    # -- vivienda -----------------------------------------------------------------------
    ("Viviendas y soluciones habitacionales",
     r"vivienda|habitacional|urbanizacion|lote con servicio|\bloteo\b"),
    # -- equipamiento social ------------------------------------------------------------
    ("Centros infantiles y comunitarios",
     r"desarrollo infantil|centro infantil|integrador comunitario|\bcic\b|merendero|comedor|"
     r"centro comunitario|club de dia|\bhogar\b"),
    ("Establecimientos educativos",
     r"escuela|\besc\b|colegio|educativ|\baula|jardin de infantes|nivel inicial|albergue|"
     r"universidad|profesorado|bachillerato|\bu\.? ?c\.? n\b"),
    ("Establecimientos de salud",
     r"hospital|centro de salud|puesto sanitario|\bcaps\b|primeros auxilios|\bsalud\b|"
     r"\bsanitaria\b|\bmaternidad\b"),
    ("Deporte y recreación",
     r"deportiv|playon|polideportivo|cancha|gimnasio|natatorio|estadio|recreativ|\bpileta\b|"
     r"\bpiscina\b"),
    ("Cultura, patrimonio y turismo",
     r"museo|cultural|patrimoni|iglesia|capilla|turist|centro de interpretacion|biblioteca|"
     r"teatro|\bhotel\b|\btermas\b|centro de convenciones|\bferia\b"),
    ("Seguridad y justicia",
     r"comisaria|policia|bombero|destacamento|\bpenal\b|juzgado|tribunal|\bcarcel\b"),
    ("Edificios públicos y administrativos",
     r"centro civico|ministerio|municipalidad|\boficina|\bsede\b|delegacion|\bblock\b|"
     r"\bedificio\b|secretaria"),
    # -- espacio publico ----------------------------------------------------------------
    ("Plazas y espacios públicos",
     r"\bplaza|\bparque\b|\bpaseo\b|anfiteatro|espacio publico|arbolado|plazoleta|costanera|"
     r"\bmonumento\b|\bcartel"),
    # -- residual por obra menor --------------------------------------------------------
    ("Otras construcciones menores",
     r"tinglado|\bcerco\b|cerramiento|\bmuro\b|baranda|galeria|\bcubierta|\blosa\b|\btecho|"
     r"mobiliario|impermeabiliza|termomecanic|\bplatea\b|\bpasillo\b|fundacion"),
]

# Respaldo cuando ninguna regla matchea: el tipo que publica la fuente. "OTRAS" no aporta nada.
RESPALDO_TIPO = {
    "OBRAS VIALES": "Otras obras viales",
    "AGUA Y SANEAMIENTO": "Otras obras de agua y saneamiento",
    "OBRAS HÍDRICAS": "Otras obras hidráulicas",
    "CONECTIVIDAD ELÉCTRICA": "Red eléctrica y suministro de energía",
    "ALUMBRADO PUBLICO": "Alumbrado público y luminarias",
    "VIVIENDAS": "Viviendas y soluciones habitacionales",
    "GAS": "Gas",
    "ARQUITECTURA": "Otras obras de arquitectura",
    "OTRAS": None,
}
SIN_REGLA = "Otras obras"

# El segundo eje. Mismo mecanismo, lista aparte.
ACCIONES = [
    ("Construcción",
     r"construccion|construir|ejecucion de obra|\bobra nueva\b|\bnuev[oa]s?\b|dotacion"),
    ("Refacción y puesta en valor",
     r"refaccion|remodelacion|readecuacion|refuncionaliza|puesta en valor|restauracion|"
     r"reacondicionamiento|reparacion|recambio|\bcambio\b|reemplazo|sustitucion|renovacion|"
     r"revitalizacion|\bmejora|optimizacion|reconstruccion|terminacion|finalizacion|\barreglo|"
     r"acondicionamiento|impermeabiliza"),
    ("Ampliación",
     r"ampliacion|ampliar|\banexo\b|\bextension\b|repotenciacion|habilitacion"),
    ("Mantenimiento y limpieza",
     r"mantenimiento|limpieza|desmaleza|conservacion|bacheo|perfilado|desobstruccion|"
     r"liberacion de cauce"),
    ("Provisión e instalación",
     r"provision|suministro|adquisicion|instalacion|equipamiento|colocacion|\bprovee"),
]
SIN_ACCION = "Sin especificar"


# ------------------------------------------------------------------- geografia canonica
# Los 60 municipios de Salta con la grafia que ya usa el repo (misma que
# Salta_recursos_municipios_mensual.csv), indexados por su clave sin acentos.
MUNICIPIOS = {
    "AGUARAY":                     "Aguaray",
    "AGUAS BLANCAS":               "Aguas Blancas",
    "ANGASTACO":                   "Angastaco",
    "ANIMANA":                     "Animaná",
    "APOLINARIO SARAVIA":          "Apolinario Saravia",
    "CACHI":                       "Cachi",
    "CAFAYATE":                    "Cafayate",
    "CAMPO QUIJANO":               "Campo Quijano",
    "CAMPO SANTO":                 "Campo Santo",
    "CERRILLOS":                   "Cerrillos",
    "CHICOANA":                    "Chicoana",
    "COLONIA SANTA ROSA":          "Colonia Santa Rosa",
    "CORONEL MOLDES":              "Coronel Moldes",
    "EL BORDO":                    "El Bordo",
    "EL CARRIL":                   "El Carril",
    "EL GALPON":                   "El Galpón",
    "EL JARDIN":                   "El Jardín",
    "EL POTRERO":                  "El Potrero",
    "EL QUEBRACHAL":               "El Quebrachal",
    "EL TALA":                     "El Tala",
    "EMBARCACION":                 "Embarcación",
    "GENERAL BALLIVIAN":           "General Ballivián",
    "GENERAL GUEMES":              "General Güemes",
    "GENERAL MOSCONI":             "General Mosconi",
    "GENERAL PIZARRO":             "General Pizarro",
    "GUACHIPAS":                   "Guachipas",
    "HIPOLITO YRIGOYEN":           "Hipólito Yrigoyen",
    "IRUYA":                       "Iruya",
    "ISLA DE CANAS":               "Isla de Cañas",
    "JOAQUIN V. GONZALEZ":         "Joaquín V. González",
    "LA CALDERA":                  "La Caldera",
    "LA CANDELARIA":               "La Candelaria",
    "LA MERCED":                   "La Merced",
    "LA POMA":                     "La Poma",
    "LA VINA":                     "La Viña",
    "LAS LAJITAS":                 "Las Lajitas",
    "LOS TOLDOS":                  "Los Toldos",
    "METAN":                       "Metán",
    "MOLINOS":                     "Molinos",
    "NAZARENO":                    "Nazareno",
    "PAYOGASTA":                   "Payogasta",
    "PICHANAL":                    "Pichanal",
    "PROF. SALVADOR MAZZA":        "Prof. Salvador Mazza",
    "RIVADAVIA BANDA NORTE":       "Rivadavia Banda Norte",
    "RIVADAVIA BANDA SUR":         "Rivadavia Banda Sur",
    "ROSARIO DE LERMA":            "Rosario de Lerma",
    "ROSARIO DE LA FRONTERA":      "Rosario de la Frontera",
    "RIO PIEDRAS":                 "Río Piedras",
    "SALTA":                       "Salta",
    "SAN ANTONIO DE LOS COBRES":   "San Antonio de los Cobres",
    "SAN CARLOS":                  "San Carlos",
    "SAN LORENZO":                 "San Lorenzo",
    "SAN RAMON DE LA NUEVA ORAN":  "San Ramón de la Nueva Orán",
    "SANTA VICTORIA ESTE":         "Santa Victoria Este",
    "SANTA VICTORIA OESTE":        "Santa Victoria Oeste",
    "SECLANTAS":                   "Seclantás",
    "TARTAGAL":                    "Tartagal",
    "TOLAR GRANDE":                "Tolar Grande",
    "URUNDEL":                     "Urundel",
    "VAQUEROS":                    "Vaqueros",
}
# El padron rotula seis municipios distinto del resto del repo.
MUNI_ALIAS = {
    "CAPITAL":               "SALTA",
    "GRAL.BALLIVIAN":        "GENERAL BALLIVIAN",
    "JOAQUIN V.GONZALEZ":    "JOAQUIN V. GONZALEZ",
    "QUEBRACHAL":            "EL QUEBRACHAL",
    "SALVADOR MAZZA":        "PROF. SALVADOR MAZZA",
    "SAN JOSE DE METAN":     "METAN",
}

# Los 23 departamentos, con la grafia del repo. El padron ya los trae asi, pero se normaliza
# igual para que un cambio de casing en la fuente no abra un departamento nuevo.
DEPARTAMENTOS = {
    "ANTA": "Anta", "CACHI": "Cachi", "CAFAYATE": "Cafayate", "CAPITAL": "Capital",
    "CERRILLOS": "Cerrillos", "CHICOANA": "Chicoana", "GENERAL GUEMES": "General Güemes",
    "GENERAL JOSE DE SAN MARTIN": "General José de San Martín", "GUACHIPAS": "Guachipas",
    "IRUYA": "Iruya", "LA CALDERA": "La Caldera", "LA CANDELARIA": "La Candelaria",
    "LA POMA": "La Poma", "LA VINA": "La Viña", "LOS ANDES": "Los Andes", "METAN": "Metán",
    "MOLINOS": "Molinos", "ORAN": "Orán", "RIVADAVIA": "Rivadavia",
    "ROSARIO DE LA FRONTERA": "Rosario de la Frontera", "ROSARIO DE LERMA": "Rosario de Lerma",
    "SAN CARLOS": "San Carlos", "SANTA VICTORIA": "Santa Victoria",
}


def clave(s):
    """Clave de comparacion geografica: sin acentos, en mayusculas."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c)).upper().strip()


def departamento(s):
    k = clave(s)
    if k not in DEPARTAMENTOS:
        inc("departamento desconocido: %r" % s)
    return DEPARTAMENTOS.get(k, str(s).strip())


def municipio(s):
    k = clave(s)
    k = MUNI_ALIAS.get(k, k)
    if k not in MUNICIPIOS:
        inc("municipio desconocido: %r" % s)
    return MUNICIPIOS.get(k, str(s).strip())


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


def url_del_recurso(destino, refrescar=False):
    """URL del CSV del padron, resuelta por la API de CKAN. Cae al respaldo si no responde."""
    crudo = bajar(API, destino, "package_show.json", refrescar)
    if crudo:
        try:
            paquete = json.loads(crudo.decode("utf-8"))["result"]
            for r in paquete.get("resources", []):
                if (r.get("format") or "").upper() == "CSV" and r.get("url"):
                    print("   recurso: %s (%s)" % (r.get("name"), r.get("last_modified") or "s/f"))
                    return r["url"]
        except Exception as e:
            inc("no se pudo leer la respuesta de la API de CKAN: %s" % e)
    inc("se usa la URL de respaldo del recurso: la API de CKAN no sirvio una")
    return RESPALDO


def escribir_csv(ruta, campos, filas):
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print("   %s  (%d filas)" % (ruta, len(filas)))


def numero(s, etiqueta, fila):
    """Texto -> float en configuracion inglesa. Audita lo que no parsea."""
    t = str(s).strip()
    if not t:
        return None
    if "," in t:
        inc("coma en un campo numerico (%s, id %s): %r" % (etiqueta, fila, s))
    try:
        return float(t)
    except ValueError:
        inc("valor no numerico (%s, id %s): %r" % (etiqueta, fila, s))
        return None


# ------------------------------------------------------------------------------- clasificacion

def aplicar(texto, reglas):
    """(etiqueta ganadora, patron que la disparo, [todas las que matchearon])."""
    hits = [(lab, rx) for lab, rx in reglas if re.search(rx, texto)]
    todas = [lab for lab, _ in hits]
    return (hits[0][0], hits[0][1], todas) if hits else (None, None, todas)


def fin_etiqueta(s):
    """El padron codifica la ausencia de financiamiento como el texto "0"."""
    t = (s or "").strip()
    return "Sin dato" if t in ("", "0") else t


def clasificar(fila):
    """Devuelve (categoria, accion, etiquetas, regla) para una obra del padron."""
    texto = norm(fila["nombre"]) + " | " + norm(fila["descripcion"])
    cat, patron, todas = aplicar(texto, CATEGORIAS)
    if cat is not None:
        origen = "regla: " + patron
    else:
        cat = RESPALDO_TIPO.get(fila["tipo"].strip())
        origen = "tipo: " + fila["tipo"].strip() if cat else "sin regla"
        if cat is None:
            cat = SIN_REGLA
    acc, _, _ = aplicar(texto, ACCIONES)
    return cat, acc or SIN_ACCION, "|".join(todas), origen


# ------------------------------------------------------------------------------- lectura

def leer_padron(datos):
    """[dict por obra] del CSV original, ya clasificado y con la geografia canonica."""
    texto = datos.decode("utf-8-sig")
    filas = []
    for r in csv.DictReader(io.StringIO(texto)):
        ident = (r.get("id") or "").strip()
        cat, acc, etiquetas, regla = clasificar(r)
        avance = numero(r.get("porcentaje_avance"), "porcentaje_avance", ident)
        monto = numero(r.get("monto_contrato"), "monto_contrato", ident)
        lat = numero(r.get("lat"), "lat", ident)
        lng = numero(r.get("lng"), "lng", ident)
        ok = (lat is not None and lng is not None
              and LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX)
        fin = (r.get("fecha_fin_inicial") or "").strip()[:4]
        lic = (r.get("licitacion_anio") or "").strip()
        filas.append({
            "id": ident,
            "nombre": " ".join((r.get("nombre") or "").split()),
            "descripcion": " ".join((r.get("descripcion") or "").split()),
            "area_responsable": (r.get("area_responsable") or "").strip(),
            "tipo_fuente": (r.get("tipo") or "").strip(),
            "categoria": cat,
            "accion": acc,
            "etiquetas": etiquetas,
            "regla": regla,
            "etapa": (r.get("etapa") or "").strip(),
            "finalizada": 1 if avance == 100 else 0,
            "porcentaje_avance": avance,
            "monto_contrato": monto,
            # El padron codifica "sin dato" como el texto "0" en financiamiento.
            "financiamiento": fin_etiqueta(r.get("financiamiento")),
            "departamento": departamento(r.get("jurisdiccion")),
            "municipio": municipio(r.get("comuna")),
            "lat": lat, "lng": lng,
            "coord_valida": 1 if ok else 0,
            "anio_fin_previsto": int(fin) if fin.isdigit() else "",
            # licitacion_anio viene en 0 cuando no se conoce: se deja vacio, no cero.
            "licitacion_anio": int(lic) if lic.isdigit() and lic != "0" else "",
        })
    return filas


# ------------------------------------------------------------------------------ verificaciones

def verif_cobertura(filas, detalle=False):
    """De donde salio cada etiqueta de categoria. El residuo es el dato a vigilar."""
    fin = [f for f in filas if f["finalizada"]]
    origen = collections.Counter(f["regla"].split(":")[0] for f in fin)
    sin = [f for f in fin if f["regla"] == "sin regla"]
    print("   cobertura sobre %d obras al 100 %%: regla %d, tipo de la fuente %d, sin regla %d "
          "(%.1f %%)" % (len(fin), origen.get("regla", 0), origen.get("tipo", 0),
                         len(sin), 100.0 * len(sin) / max(len(fin), 1)))
    if len(sin) > 0.10 * max(len(fin), 1):
        inc("mas del 10 %% de las obras finalizadas quedo sin regla (%d)" % len(sin))
    if detalle:
        for f in sin:
            print("      sin regla  [%s]  %s" % (f["tipo_fuente"], f["nombre"][:90]))
    multi = collections.Counter(len(f["etiquetas"].split("|")) if f["etiquetas"] else 0
                                for f in fin)
    print("   reglas que matchean por obra: %s" % dict(sorted(multi.items())))


def verif_reconciliacion(filas):
    """Cada corte tiene que sumar el total del padron y el total de las finalizadas."""
    fin = [f for f in filas if f["finalizada"]]
    for etiqueta, universo in (("padron", filas), ("finalizadas", fin)):
        for campo in ("categoria", "accion", "departamento", "municipio", "tipo_fuente",
                      "area_responsable", "financiamiento"):
            suma = sum(collections.Counter(f[campo] for f in universo).values())
            if suma != len(universo):
                inc("el corte por %s no reconcilia en %s: %d contra %d"
                    % (campo, etiqueta, suma, len(universo)))
    print("   reconciliacion: %d filas del padron, %d al 100 %%, los 7 cortes cierran"
          % (len(filas), len(fin)))


def verif_geografia(filas):
    """Los 23 departamentos y el cotejo municipio -> departamento contra el crosswalk del repo."""
    deps = sorted(set(f["departamento"] for f in filas))
    munis = sorted(set(f["municipio"] for f in filas))
    print("   geografia: %d departamentos, %d municipios" % (len(deps), len(munis)))
    if len(deps) != 23:
        inc("se esperaban 23 departamentos y hay %d: %s" % (len(deps), deps))
    cw = os.path.join(RAIZ, "Salta_recursos_municipios_mensual.csv")
    if not os.path.exists(cw):
        print("   (sin crosswalk municipal en el repo: no se coteja el departamento)")
        return
    pares = {}
    with open(cw, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pares.setdefault(r["municipio"], set()).add(r["departamento"])
    malos = sorted({(f["municipio"], f["departamento"]) for f in filas
                    if f["municipio"] in pares and f["departamento"] not in pares[f["municipio"]]})
    for m, d in malos:
        inc("el padron pone %s en %s y el crosswalk del repo en %s"
            % (m, d, "/".join(sorted(pares[m]))))
    print("   cotejo municipio -> departamento contra el crosswalk: %d desvios" % len(malos))


def verif_coordenadas(filas):
    malas = [f for f in filas if not f["coord_valida"]]
    for f in malas:
        inc("coordenada fuera de Salta (id %s, %s): lat %s lng %s -- %s"
            % (f["id"], f["municipio"], f["lat"], f["lng"], f["nombre"][:60]))
    print("   coordenadas: %d de %d dentro de Salta, %d invalidas"
          % (len(filas) - len(malas), len(filas), len(malas)))


def verif_formato(filas):
    """Cumplimiento del formato numerico ingles y rangos imposibles."""
    sin_monto = [f for f in filas if f["monto_contrato"] is None]
    cero = [f for f in filas if f["monto_contrato"] == 0]
    neg = [f for f in filas if (f["monto_contrato"] or 0) < 0]
    fuera = [f for f in filas if f["porcentaje_avance"] is None
             or not 0 <= f["porcentaje_avance"] <= 100]
    for etiqueta, lista in (("sin monto", sin_monto), ("monto en cero", cero),
                            ("monto negativo", neg), ("avance fuera de 0-100", fuera)):
        if lista:
            inc("%d obras con %s (ids %s)"
                % (len(lista), etiqueta, ",".join(f["id"] for f in lista[:10])))
    print("   formato numerico: %d sin parsear, %d montos en cero, %d avances fuera de rango"
          % (len(sin_monto), len(cero), len(fuera)))


def verif_duplicados(filas):
    c = collections.Counter((f["nombre"], f["municipio"], f["monto_contrato"]) for f in filas)
    dups = [(k, v) for k, v in c.items() if v > 1]
    for (nombre, muni, monto), v in sorted(dups, key=lambda x: -x[1])[:10]:
        inc("%d filas identicas en nombre+municipio+monto: %s (%s, %s)"
            % (v, nombre[:70], muni, monto))
    print("   duplicados exactos: %d grupos, %d filas de mas"
          % (len(dups), sum(v - 1 for _, v in dups)))


def saltos_de_magnitud(filas):
    """Montos a mas de 1000x de la mediana de su categoria: firma de un separador mal leido."""
    por_cat = collections.defaultdict(list)
    for f in filas:
        if f["monto_contrato"]:
            por_cat[f["categoria"]].append(f)
    n = 0
    for cat, lista in sorted(por_cat.items()):
        med = statistics.median(x["monto_contrato"] for x in lista)
        if not med:
            continue
        for f in lista:
            r = f["monto_contrato"] / med
            if r > 1000 or r < 0.001:
                n += 1
                inc("monto a %.0fx de la mediana de %s (id %s): %s -- %s"
                    % (r, cat, f["id"], f["monto_contrato"], f["nombre"][:60]))
    print("   saltos de orden de magnitud en el monto: %d" % n)


CONTROLES = [
    ("filas del padron", lambda f: len(f), 2947),
    ("obras al 100 %", lambda f: sum(x["finalizada"] for x in f), 2389),
    ("obras que la fuente rotula OTRAS", lambda f: sum(x["tipo_fuente"] == "OTRAS" for x in f),
     1048),
    ("departamentos", lambda f: len({x["departamento"] for x in f}), 23),
    ("municipios", lambda f: len({x["municipio"] for x in f}), 60),
    ("obras al 100 % en General José de San Martín",
     lambda f: sum(x["finalizada"] and x["departamento"] == "General José de San Martín"
                   for x in f), 426),
    ("obras al 100 % en Capital",
     lambda f: sum(x["finalizada"] and x["departamento"] == "Capital" for x in f), 381),
    ("coordenadas invalidas", lambda f: sum(not x["coord_valida"] for x in f), 3),
]


def verif_control(filas):
    ok = 0
    for etiqueta, fn, esperado in CONTROLES:
        valor = fn(filas)
        marca = "OK " if valor == esperado else "!! "
        if valor == esperado:
            ok += 1
        else:
            inc("control '%s': se esperaba %s y da %s" % (etiqueta, esperado, valor))
        print("      %s%-46s %12s  (esperado %s)" % (marca, etiqueta, valor, esperado))
    print("   valores de control: %d de %d" % (ok, len(CONTROLES)))


def resumen_clasificacion(filas):
    """Lo que compra la reclasificacion: como queda repartido lo que la fuente llama OTRAS."""
    fin = [f for f in filas if f["finalizada"]]
    print("\n   categorias (obras al 100 %):")
    for cat, n in collections.Counter(f["categoria"] for f in fin).most_common():
        print("      %5d  %s" % (n, cat))
    print("   acciones:")
    for acc, n in collections.Counter(f["accion"] for f in fin).most_common():
        print("      %5d  %s" % (n, acc))
    otras = [f for f in fin if f["tipo_fuente"] == "OTRAS"]
    print("   adentro de OTRAS (%d obras al 100 %%):" % len(otras))
    for cat, n in collections.Counter(f["categoria"] for f in otras).most_common(12):
        print("      %5d  %s" % (n, cat))


# ------------------------------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(
        description="Padron de obras publicas de Salta, reclasificado por tipo de obra y accion")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "obras_publicas_salta"),
                    help="Cache de los archivos originales")
    ap.add_argument("--refrescar", action="store_true",
                    help="Vuelve a bajar todo, incluso lo cacheado")
    ap.add_argument("--detalle-reglas", action="store_true",
                    help="Lista una por una las obras que ninguna regla alcanza")
    args = ap.parse_args()

    print("A. El padron del portal de datos de Salta")
    url = url_del_recurso(args.fuentes, args.refrescar)
    datos = bajar(url, args.fuentes, "padron_obras_publicas.csv", args.refrescar)
    if datos is None:
        raise SystemExit("no se pudo bajar el padron de obras publicas")

    print("B. Lectura y clasificacion")
    filas = leer_padron(datos)
    if not filas:
        raise SystemExit("el padron vino vacio")

    print("C. Verificaciones")
    verif_formato(filas)
    verif_cobertura(filas, args.detalle_reglas)
    verif_reconciliacion(filas)
    verif_geografia(filas)
    verif_coordenadas(filas)
    verif_duplicados(filas)
    saltos_de_magnitud(filas)
    verif_control(filas)
    resumen_clasificacion(filas)

    print("\nD. Escritura")
    filas.sort(key=lambda f: (f["departamento"], f["municipio"], f["categoria"], f["id"]))
    escribir_csv(os.path.join(args.salida, SALIDA), CAMPOS, filas)

    if incidencias:
        print("\nINCIDENCIAS (%d):" % len(incidencias))
        for i, m in enumerate(incidencias, 1):
            print("  %2d. %s" % (i, m))
    else:
        print("\nSin incidencias.")


if __name__ == "__main__":
    main()
```
