# Actualización — Consumo eléctrico no residencial por departamento (ENRESP)

Genera `Electricidad_No_Residencial_Salta_departamento_mensual.csv` a partir de la **Matriz de
Indicadores de Consumo, Cobertura y Estructura Tarifaria del Servicio Eléctrico** que publica el
Ente Regulador de los Servicios Públicos de Salta (ENRESP) en `datospublicos.salta.gob.ar` bajo
CC-BY 4.0.

Es un panel mensual completo: **23 departamentos × 33 meses**, de enero de 2024 a septiembre de
2026, sin un solo hueco. El detalle de qué mide, qué no mide y los defectos de la fuente está en
`Metodologia_Electricidad_No_Residencial_Salta.md`.

## Lo único frágil de esta actualización, ya resuelto

**El nombre del archivo lleva el largo de la serie** —`..._maestro_33m.csv`— así que la URL de
descarga cambia en cada actualización. El script no la hardcodea: pide `package_show` a la API de
CKAN del portal con el `dataset_id`, que sí es estable, y toma el primer recurso CSV. Queda una URL
de respaldo por si la API no responde, y en ese caso el script lo dice como incidencia.

## Las dos cosas que hay que mirar sí o sí

1. **El padrón de usuarios.** La fuente arrastra el último padrón conocido cuando deja de
   actualizarlo: al 28-oct-2026, los meses de julio, agosto y septiembre repiten el de junio en los
   23 departamentos a la vez. El script lo detecta solo, lo marca en la columna
   `usuarios_arrastrados` y lo informa. **El tablero corta ahí la serie de usuarios**, y el corte
   lo lee de esa columna, así que se mueve solo cuando la fuente retome la actualización.
2. **El separador es `;`, no `,`.** El decimal sí es `.`. Si alguna vez aparece una coma dentro de
   un campo numérico, la configuración cambió a latina y el script lo reporta en vez de adivinar.

## Qué genera (en `datos-drive/`)

| archivo | filas | contenido |
|---|---|---|
| `Electricidad_No_Residencial_Salta_departamento_mensual.csv` | 759 | una fila por departamento y mes, con usuarios, consumo, factura, composición tarifaria y la marca de padrón arrastrado |

Caché de los originales en `datos-drive/fuentes/electricidad_enresp/`: `package_show.json` y
`no_residencial_departamental.csv`.

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
python actualizar_electricidad_no_residencial_salta.py --refrescar
```

Sin `--refrescar` reutiliza lo que ya está en `fuentes/electricidad_enresp/`.

Opciones: `--salida DIR` (carpeta de salida), `--fuentes DIR` (caché), `--refrescar`.

## 3. Verificar antes de dar por buena la actualización

La corrida imprime todo lo que sigue. **Si algo no cierra, no se copia al sitio.**

1. **Formato numérico** — tiene que decir `0 valores sin parsear, 0 filas no positivas, 0 con
   % != 100`.
2. **Panel completo** — `23 departamentos x N meses`, con `0 faltantes, 0 repetidas`. Un hueco
   significa que la fuente dejó de publicar un departamento y hay que mirarlo antes de seguir.
3. **Identidad de la fuente** — `0 desvíos en consumo, 0 en facturación`. Es la comprobación de
   que el total sigue siendo usuarios × promedio. Si aparecen desvíos, la fuente cambió la forma
   de calcularlo y hay que revisar la metodología.
4. **Padrón arrastrado** — informa cuántos meses y cuáles. Al 28-oct-2026 son tres: 2026-07,
   2026-08 y 2026-09. **Si la fuente retoma la actualización, este número baja y hay que ajustar
   el control correspondiente.**
5. **Valores de control** — los once tienen que dar `OK`:

| control | valor |
|---|---|
| Filas · departamentos · meses | 759 · 23 · 33 |
| Primer · último período | 2024-01 · 2026-09 |
| Usuarios, total provincial 2024-01 | 33.421 |
| Usuarios, total provincial 2026-05 | 32.162 |
| Meses con padrón arrastrado | 3 |
| Consumo 2024 · 2025 | 803.431 · 787.142 MWh |
| Consumo de Capital 2025 | 392.490 MWh |

   **Estos valores cambian cuando el ENRESP publica meses nuevos.** Al actualizar hay que
   comprobar que los años ya cerrados sigan dando lo mismo —si 2024 o 2025 se movieron, la fuente
   revisó la serie y eso es noticia— y después actualizar la lista `CONTROLES` del script y las
   tablas de la metodología.

6. **Incidencias** — en la corrida de referencia hay una sola, el padrón arrastrado. Cualquier
   incidencia nueva se analiza antes de publicar.

## 4. Copiar al sitio

```powershell
Copy-Item G:\Documents\CESS\Indicadores\datos-drive\Electricidad_No_Residencial_Salta_departamento_mensual.csv G:\Documents\CESS\Indicadores\sitio-indicadores\datos\ -Force
```

```powershell
Copy-Item G:\Documents\CESS\Indicadores\datos-drive\Metodologia_Electricidad_No_Residencial_Salta.md,G:\Documents\CESS\Indicadores\datos-drive\Actualizar_Electricidad_No_Residencial_Salta.md G:\Documents\CESS\Indicadores\sitio-indicadores\datos\metodologia\ -Force
```

Y reconstruir el sitio:

```powershell
cd G:\Documents\CESS\Indicadores\sitio-indicadores; python build.py
```

El tema del sitio es `consumo-electrico` (`adapters.consumo_electrico()` y la entrada en
`catalog.TEMAS`). Dos cosas del adaptador conviene tener presentes al tocarlo:

- **`usuarios` es un stock**: se suma entre departamentos pero se promedia entre meses. La primera
  mitad la resuelve el adaptador al armar el total provincial; la segunda, el `"agg": "mean"` de
  `ELEC_METRICAS`. Una comprobación rápida en el navegador: al poner el gráfico de usuarios en
  «Anual», el valor tiene que quedar en el orden de 32.000, no de 390.000.
- **El corte de la serie de usuarios sale del dato**, de la columna `usuarios_arrastrados`. No hay
  ninguna fecha escrita en el código.

## Script completo

Es el mismo archivo que `datos-drive/actualizar_electricidad_no_residencial_salta.py`, copiado acá
para que el runbook se sostenga solo.

```python
# -*- coding: utf-8 -*-
"""
Consumo electrico NO RESIDENCIAL por departamento (ENRESP Salta) -- base mensual.

Genera:

    Electricidad_No_Residencial_Salta_departamento_mensual.csv

ORIGEN
    "Matriz de Indicadores de Consumo, Cobertura y Estructura Tarifaria del Servicio Electrico",
    publicada por el Ente Regulador de los Servicios Publicos de Salta (ENRESP) en
    datospublicos.salta.gob.ar bajo CC-BY 4.0. Es un panel mensual COMPLETO: 23 departamentos
    por 33 meses, de enero de 2024 a septiembre de 2026, sin un solo hueco.

QUE MIDE Y QUE NO
    Solo el segmento NO RESIDENCIAL. No es la demanda electrica total de la provincia y no se
    compara con la generacion de CAMMESA que publica el tema `energia-electrica`. La fuente
    tampoco abre por categoria tarifaria: comercial, industrial y alumbrado publico van juntos.

EL CONSUMO TOTAL ES UNA ESTIMACION, NO UNA MEDICION
    Se verifico fila por fila que `consumo_total_estimado_kwh` es exactamente
    `usuarios * consumo_kwh_ponderado`: no es la suma de los medidores sino el padron por un
    consumo medio. El script comprueba esa identidad en cada corrida.

EL PADRON DE USUARIOS SE CONGELA DESDE JUNIO DE 2026
    En los 23 departamentos a la vez, el valor de junio de 2026 se repite identico en julio,
    agosto y septiembre, mientras el consumo por usuario sigue moviendose: la fuente arrastro el
    ultimo padron conocido y siguio estimando sobre el. En el resto de la serie las rachas de
    valores repetidos nunca pasan de 4 departamentos simultaneos. El script detecta esos meses y
    los marca con `usuarios_arrastrados = 1`; el tablero corta la serie de usuarios ahi.

UNIDAD
    Usuarios: cantidad de usuarios no residenciales con servicio, a fin de mes. Es un STOCK: no
    se suma entre meses. Consumo: kWh del mes.

Formato de salida (convencion del repo): separador ',', decimal '.', sin separador de miles,
UTF-8 con BOM. El archivo de origen viene con separador ';'.

Correr:  python actualizar_electricidad_no_residencial_salta.py [--salida DIR] [--fuentes DIR]
                                                                [--refrescar]
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

# El portal es un CKAN. El nombre del archivo lleva el largo de la serie
# (`1_no_residencial_departamental_maestro_33m.csv`), asi que cambia en cada actualizacion: por
# eso el recurso se resuelve por la API y no se hardcodea la URL de descarga.
PORTAL = "https://datospublicos.salta.gob.ar"
DATASET = "02134503-89a3-49e6-8ceb-4a74d3d50b5f"
API = PORTAL + "/api/3/action/package_show?id=" + DATASET
# Respaldo por si la API no responde: la URL vigente al 28-oct-2026.
RESPALDO = (PORTAL + "/dataset/" + DATASET + "/resource/97ce1be1-2dbe-4883-8f69-735dd86d925c"
            "/download/1_no_residencial_departamental_maestro_33m.csv")

SALIDA = "Electricidad_No_Residencial_Salta_departamento_mensual.csv"
CAMPOS = ["anio", "mes", "periodo", "departamento", "usuarios", "consumo_kwh_por_usuario",
          "consumo_total_kwh", "factura_promedio_pesos", "facturacion_total_estimada_pesos",
          "porc_energia", "porc_impuestos", "porc_vad", "usuarios_arrastrados"]

# Los 23 departamentos de Salta, con la grafia del repo. La fuente trae "Rosario De La Frontera"
# y "Rosario De Lerma" con la preposicion en mayuscula; la clave sin acentos las resuelve.
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

incidencias = []


def inc(msg):
    incidencias.append(msg)


def clave(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c)).upper().strip()


def departamento(s):
    k = clave(s)
    if k not in DEPARTAMENTOS:
        inc("departamento desconocido: %r" % s)
    return DEPARTAMENTOS.get(k, str(s).strip())


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
    """URL del CSV, resuelta por la API de CKAN. Cae al respaldo si no responde."""
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


def entero(v):
    """Los conteos se publican enteros."""
    return None if v is None else int(round(v))


def numero(s, etiqueta, fila):
    """Texto -> float en configuracion inglesa. Audita lo que no parsea.

    El archivo viene con separador de campo ';' pero decimal '.', asi que una coma adentro de un
    campo numerico seria configuracion latina y cambiaria el valor: se reporta, no se adivina.
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
    """[dict por fila] del CSV del ENRESP, normalizado."""
    texto = datos.decode("utf-8-sig")
    filas = []
    for r in csv.DictReader(io.StringIO(texto), delimiter=";"):
        # La cabecera trae 'año' con tilde y dos columnas vacias al final.
        anio = (r.get("año") or r.get("ano") or "").strip()
        periodo = (r.get("periodo") or "").strip()
        dep = departamento(r.get("departamento"))
        ident = "%s %s" % (dep, periodo)
        filas.append({
            "anio": int(anio) if anio.isdigit() else None,
            "mes": int((r.get("mes_num") or "0").strip() or 0),
            "periodo": periodo,
            "departamento": dep,
            # Es una cuenta de usuarios: se escribe entera, no con decimal flotante.
            "usuarios": entero(numero(r.get("usuarios"), "usuarios", ident)),
            "consumo_kwh_por_usuario": numero(r.get("consumo_kwh_ponderado"),
                                              "consumo_kwh_ponderado", ident),
            "consumo_total_kwh": numero(r.get("consumo_total_estimado_kwh"),
                                        "consumo_total_estimado_kwh", ident),
            "factura_promedio_pesos": numero(r.get("factura_promedio_pesos"),
                                             "factura_promedio_pesos", ident),
            "facturacion_total_estimada_pesos": numero(r.get("facturacion_total_estimada_pesos"),
                                                       "facturacion_total_estimada_pesos", ident),
            "porc_energia": numero(r.get("porc_energia"), "porc_energia", ident),
            "porc_impuestos": numero(r.get("porc_impuestos"), "porc_impuestos", ident),
            "porc_vad": numero(r.get("porc_vad"), "porc_vad", ident),
            "usuarios_arrastrados": 0,
        })
    return filas


def marcar_arrastrados(filas):
    """Marca los meses en que los 23 departamentos repiten a la vez el padron del mes anterior.

    Un departamento suelto que repite usuarios es ruido normal de un padron chico; los 23 juntos
    es la fuente arrastrando el ultimo valor conocido. Devuelve la lista de periodos marcados.
    """
    per = sorted({f["periodo"] for f in filas})
    por = {(f["departamento"], f["periodo"]): f for f in filas}
    deps = sorted({f["departamento"] for f in filas})
    marcados = []
    for a, b in zip(per, per[1:]):
        iguales = [d for d in deps
                   if (d, a) in por and (d, b) in por
                   and por[(d, a)]["usuarios"] == por[(d, b)]["usuarios"]]
        if len(iguales) == len(deps):
            marcados.append(b)
            for d in deps:
                por[(d, b)]["usuarios_arrastrados"] = 1
    return marcados


# ------------------------------------------------------------------------------ verificaciones

def verif_formato(filas):
    """Cumplimiento del formato numerico y rangos imposibles."""
    faltan = collections.Counter()
    for f in filas:
        for c in CAMPOS:
            if c in ("anio", "mes", "periodo", "departamento", "usuarios_arrastrados"):
                continue
            if f[c] is None:
                faltan[c] += 1
    neg = [f for f in filas if (f["usuarios"] or 0) <= 0 or (f["consumo_total_kwh"] or 0) <= 0]
    for f in neg:
        inc("usuarios o consumo no positivos (%s %s)" % (f["departamento"], f["periodo"]))
    mal_pct = []
    for f in filas:
        s = (f["porc_energia"] or 0) + (f["porc_impuestos"] or 0) + (f["porc_vad"] or 0)
        if abs(s - 100) > 0.05:
            mal_pct.append(f)
    if mal_pct:
        inc("%d filas donde energia + impuestos + VAD no suma 100 (p. ej. %s %s: %.2f)"
            % (len(mal_pct), mal_pct[0]["departamento"], mal_pct[0]["periodo"],
               (mal_pct[0]["porc_energia"] or 0) + (mal_pct[0]["porc_impuestos"] or 0)
               + (mal_pct[0]["porc_vad"] or 0)))
    vad0 = sum(1 for f in filas if f["porc_vad"] == 0)
    print("   formato numerico: %d valores sin parsear, %d filas no positivas, %d con %% != 100"
          % (sum(faltan.values()), len(neg), len(mal_pct)))
    print("   porc_vad en cero: %d filas (la fuente no lo informa en los primeros meses)" % vad0)


def verif_panel(filas):
    """El panel tiene que ser completo: cada departamento en cada mes, una sola vez."""
    deps = sorted({f["departamento"] for f in filas})
    per = sorted({f["periodo"] for f in filas})
    c = collections.Counter((f["departamento"], f["periodo"]) for f in filas)
    faltan = [(d, p) for d in deps for p in per if (d, p) not in c]
    dobles = [k for k, v in c.items() if v > 1]
    for d, p in faltan[:10]:
        inc("falta la fila de %s en %s" % (d, p))
    for d, p in dobles[:10]:
        inc("fila repetida de %s en %s" % (d, p))
    print("   panel: %d departamentos x %d meses = %d filas esperadas, %d leidas, %d faltantes, "
          "%d repetidas" % (len(deps), len(per), len(deps) * len(per), len(filas),
                            len(faltan), len(dobles)))
    print("   periodo: %s a %s" % (per[0], per[-1]))
    return deps, per


def verif_identidad(filas):
    """`consumo_total = usuarios * consumo_por_usuario` y lo mismo con la facturacion.

    Es la comprobacion que muestra que el total no es una medicion sino una reconstruccion.
    """
    def chequear(a, b, c, etiqueta):
        malas = [f for f in filas
                 if None not in (f[a], f[b], f[c]) and abs(f[a] * f[b] - f[c]) > 0.05]
        for f in malas[:5]:
            inc("%s no cierra en %s %s: %.2f x %.2f = %.2f, la fuente dice %.2f"
                % (etiqueta, f["departamento"], f["periodo"], f[a], f[b], f[a] * f[b], f[c]))
        return len(malas)

    n1 = chequear("usuarios", "consumo_kwh_por_usuario", "consumo_total_kwh", "el consumo total")
    n2 = chequear("usuarios", "factura_promedio_pesos", "facturacion_total_estimada_pesos",
                  "la facturacion total")
    print("   identidad usuarios x promedio = total: %d desvios en consumo, %d en facturacion"
          % (n1, n2))


def verif_arrastre(filas, marcados):
    if marcados:
        inc("la fuente repite el padron de usuarios en %d mes(es) y en los 23 departamentos a la "
            "vez: %s. Son estimaciones sobre un padron viejo, no altas y bajas reales."
            % (len(marcados), ", ".join(marcados)))
    print("   padron de usuarios arrastrado: %d mes(es) %s"
          % (len(marcados), ("(%s)" % ", ".join(marcados)) if marcados else ""))
    return marcados


def saltos_de_magnitud(filas):
    """Valores a mas de 1000x de la mediana de su departamento: firma de un separador mal leido."""
    n = 0
    for met in ("consumo_total_kwh", "usuarios"):
        por = collections.defaultdict(list)
        for f in filas:
            if f[met]:
                por[f["departamento"]].append(f)
        for dep, lista in sorted(por.items()):
            med = statistics.median(x[met] for x in lista)
            if not med:
                continue
            for f in lista:
                r = f[met] / med
                if r > 1000 or r < 0.001:
                    n += 1
                    inc("%s a %.0fx de la mediana de %s (%s): %s"
                        % (met, r, dep, f["periodo"], f[met]))
    print("   saltos de orden de magnitud: %d" % n)


def resumen(filas):
    print("\n   consumo y usuarios por anio:")
    por = collections.defaultdict(list)
    for f in filas:
        por[f["anio"]].append(f)
    for a in sorted(por):
        sub = por[a]
        meses = sorted({x["periodo"] for x in sub})
        cons = sum(x["consumo_total_kwh"] or 0 for x in sub) / 1000.0
        usu = sum(x["usuarios"] or 0 for x in sub) / len(meses)
        print("      %d  consumo %10.0f MWh   usuarios (promedio mensual) %8.0f   %2d meses"
              % (a, cons, usu, len(meses)))
    ult = sorted({f["periodo"] for f in filas})[-12:]
    rk = collections.Counter()
    for f in filas:
        if f["periodo"] in ult:
            rk[f["departamento"]] += (f["consumo_total_kwh"] or 0) / 1000.0
    print("   ranking por consumo, ultimos 12 meses (MWh):")
    for d, v in rk.most_common(6):
        print("      %10.0f  %s" % (v, d))


CONTROLES = [
    ("filas", lambda f, d, p, m: len(f), 759),
    ("departamentos", lambda f, d, p, m: len(d), 23),
    ("meses", lambda f, d, p, m: len(p), 33),
    ("primer periodo", lambda f, d, p, m: p[0], "2024-01"),
    ("ultimo periodo", lambda f, d, p, m: p[-1], "2026-09"),
    ("usuarios, total provincial 2024-01",
     lambda f, d, p, m: int(sum(x["usuarios"] for x in f if x["periodo"] == "2024-01")), 33421),
    ("usuarios, total provincial 2026-05",
     lambda f, d, p, m: int(sum(x["usuarios"] for x in f if x["periodo"] == "2026-05")), 32162),
    ("meses con padron arrastrado", lambda f, d, p, m: len(m), 3),
    ("consumo 2024 (MWh)",
     lambda f, d, p, m: round(sum(x["consumo_total_kwh"] for x in f if x["anio"] == 2024) / 1000),
     803431),
    ("consumo 2025 (MWh)",
     lambda f, d, p, m: round(sum(x["consumo_total_kwh"] for x in f if x["anio"] == 2025) / 1000),
     787142),
    ("consumo de Capital 2025 (MWh)",
     lambda f, d, p, m: round(sum(x["consumo_total_kwh"] for x in f
                                  if x["anio"] == 2025 and x["departamento"] == "Capital") / 1000),
     392490),
]


def verif_control(filas, deps, per, marcados):
    ok = 0
    for etiqueta, fn, esperado in CONTROLES:
        valor = fn(filas, deps, per, marcados)
        if valor == esperado:
            ok += 1
            marca = "OK "
        else:
            marca = "!! "
            inc("control '%s': se esperaba %s y da %s" % (etiqueta, esperado, valor))
        print("      %s%-40s %12s  (esperado %s)" % (marca, etiqueta, valor, esperado))
    print("   valores de control: %d de %d" % (ok, len(CONTROLES)))


# ------------------------------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(
        description="Consumo electrico no residencial por departamento (ENRESP Salta)")
    ap.add_argument("--salida", default=RAIZ, help="Carpeta de salida (por defecto, datos-drive/)")
    ap.add_argument("--fuentes", default=os.path.join(RAIZ, "fuentes", "electricidad_enresp"),
                    help="Cache de los archivos originales")
    ap.add_argument("--refrescar", action="store_true",
                    help="Vuelve a bajar todo, incluso lo cacheado")
    args = ap.parse_args()

    print("A. La matriz del ENRESP en el portal de datos de Salta")
    url = url_del_recurso(args.fuentes, args.refrescar)
    datos = bajar(url, args.fuentes, "no_residencial_departamental.csv", args.refrescar)
    if datos is None:
        raise SystemExit("no se pudo bajar la matriz del ENRESP")

    print("B. Lectura y normalizacion")
    filas = leer(datos)
    if not filas:
        raise SystemExit("la matriz vino vacia")
    marcados = marcar_arrastrados(filas)

    print("C. Verificaciones")
    verif_formato(filas)
    deps, per = verif_panel(filas)
    verif_identidad(filas)
    verif_arrastre(filas, marcados)
    saltos_de_magnitud(filas)
    verif_control(filas, deps, per, marcados)
    resumen(filas)

    print("\nD. Escritura")
    filas.sort(key=lambda f: (f["departamento"], f["periodo"]))
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
