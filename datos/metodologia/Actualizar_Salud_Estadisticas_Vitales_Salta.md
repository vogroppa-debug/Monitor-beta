# Actualización — Estadísticas vitales y de servicios de salud (Provincia de Salta), Ministerio de Salud Pública

Este script construye los cuatro datasets tidy del tablero **Salud** del Monitor CESS a partir de
los documentos que el **Programa de Estadísticas de Información en Salud** (Subsecretaría de Gestión
de Salud, MSP Salta) remite anualmente al Consejo Económico y Social.

La fuente no es un dataset descargable: son tablas tipeadas dentro de un `.docx` y un listado por
establecimiento dentro de un `.pdf`. Por eso el script **parsea los documentos originales** en lugar
de llevar los números escritos a mano: el año que viene se corre contra el documento nuevo y, si el
Ministerio cambia la estructura, falla ruidosamente en vez de publicar cualquier cosa.

> ## Leer esto antes de usar la salida
>
> 1. **Las tablas del documento se contradicen entre sí.** Tres tablas distintas publican las mismas
>    series con valores distintos (defunciones 2021/2024/2025, nacidos vivos 2025). El criterio
>    adoptado, y el detalle de cada discrepancia, están en
>    `Metodologia_Salud_Estadisticas_Vitales_Salta.md`, sección *Incidencias*. **No compares estos
>    CSV contra el docx sin leer esa sección antes.**
> 2. **La apertura territorial de nacimientos NO es departamental.** La fuente la publica por **Área
>    Operativa de residencia** —la circunscripción sanitaria de un hospital cabecera—, aunque la
>    columna del docx se titule "Departamento". El pasaje a departamento lo hace este script y es una
>    aproximación: los límites de las AO no coinciden exactamente con los departamentales.
> 3. **El detalle departamental de internación existe sólo para 2025.** La serie 2021–2025 de
>    internación es provincial. No hay variación interanual por departamento.
> 4. **2025 es provisorio** en toda la fuente.

## Qué genera (en `datos-drive/`)

- **`Salud_Hechos_Vitales_Salta_provincia_2020-2025.csv`** — tidy: `anio, desagregacion, metrica, valor`.
  Defunciones (totales y por grupo de edad), defunciones infantiles (neonatal/posneonatal), maternas,
  fetales, nacidos vivos (totales y por peso al nacer), matrimonios y las cuatro tasas vitales.
- **`Salud_Nacidos_Vivos_Salta_area_operativa_2021-2025.csv`** — tidy:
  `anio, cod_ao, area_operativa, departamento, metrica, valor`. Nacidos vivos por Área Operativa de
  residencia (47 AO) y el total provincial.
- **`Salud_Servicios_Salta_provincia_2021-2025.csv`** — tidy: `anio, metrica, valor`. Consultas
  médicas, población, consultas por habitante y los siete indicadores de internación provinciales.
- **`Salud_Internacion_Salta_departamento_2025.csv`** — tidy: `anio, departamento, metrica, valor`.
  Los 53 establecimientos del PDF agregados a los 23 departamentos.

## 1. Descargar las fuentes

Ambos archivos viven en la carpeta **Datos Salud** del Drive del CESS. Bajarlos a
`datos-drive/fuentes/` **sin renombrarlos**:

| Archivo | Origen |
|---|---|
| `INDICADORES  PROVINCIAL DE ESTADISTICAS DE SALUD  PARA CONSEJO ECONOMICO SOCIAL 2026.docx` | Drive → Datos Salud |
| `Resumen provisorio de internación año 2.025.pdf` | Drive → Datos Salud |

El script los busca por *glob*, así que el nombre exacto no importa: alcanza con que sea el único
`.docx` de la carpeta y que el PDF tenga `internaci` en el nombre.

## 2. Requisitos

```bash
pip install pandas python-docx pdfplumber
```

## 3. Correr el script

El script vive en este documento. Para ejecutarlo sin copiar y pegar —y garantizar que lo que corre
es exactamente lo que está documentado acá— extraer el bloque y ejecutarlo:

```bash
python -c "import re,pathlib;p=pathlib.Path('Actualizar_Salud_Estadisticas_Vitales_Salta.md');open('_salud.py','w',encoding='utf-8').write(re.search(r'```python\n(.*?)```',p.read_text(encoding='utf-8'),re.S).group(1))" && python _salud.py
```

## 4. Verificar antes de dar por buena la actualización

El script aborta solo si falla cualquiera de estos controles, pero conviene leer la salida:

- **47 Áreas Operativas** parseadas y **53 establecimientos** en el PDF.
- `Total Defunciones == Def. mayores + Def. < 1 año + Def. 1 a 4 años`, los cinco años.
- `Def. < 1 año == neonatal + posneonatal`, los seis años.
- **Suma de las 47 AO == nacidos vivos provinciales**, los cinco años, diferencia 0.
- Tasa de mortalidad infantil y materna recalculadas == las publicadas (a la centésima).
- Internación: `altas + defunciones == egresos` en las 53 filas, y la suma de los 53 establecimientos
  == `TOTAL ZONA` del PDF.
- Los cuatro CSV se releen con `pd.read_csv(..., encoding="utf-8-sig")` —las mismas opciones que usa
  `sitio-indicadores/adapters.py`— sin `NaN`.

**Actualizar cada año:** cambiar `ANIO_INTERNACION_DEPTO` si el Ministerio remite el detalle por
establecimiento de un año nuevo, y actualizar el mismo valor en el `fixed` del gráfico
`sal-internacion-depto` de `sitio-indicadores/catalog.py`. Si aparecen Áreas Operativas o
establecimientos nuevos, el script falla indicando cuáles: agregarlos a `AO_DEPTO` / `EST_DEPTO`.

---

## Script completo

```python
# -*- coding: utf-8 -*-
"""Construye los datasets de Salud del Monitor CESS desde los documentos del MSP Salta.

Entrada : datos-drive/fuentes/*.docx  (estadisticas vitales y de servicios)
          datos-drive/fuentes/*.pdf   (rendimiento de internacion por establecimiento)
Salida  : los cuatro CSV tidy descritos en el encabezado del runbook.

Formato numerico: el .docx viene en configuracion LATINA (miles '.', decimal ',') y el .pdf en
configuracion INGLESA (decimal '.'). Todo se emite en INGLESA, que es el contrato del sitio.
"""
import glob
import os
import re
import unicodedata

import docx
import pandas as pd
import pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(HERE, "fuentes")
ANIO_INTERNACION_DEPTO = 2025

# --------------------------------------------------------------------------
# Departamentos: nombres canonicos, iguales a los de sitio-indicadores/adapters.py
# --------------------------------------------------------------------------
ANTA, CACHI, CAFAYATE, CAPITAL = "Anta", "Cachi", "Cafayate", "Capital"
CERRILLOS, CHICOANA, GUEMES = "Cerrillos", "Chicoana", "General Güemes"
SANMARTIN, GUACHIPAS, IRUYA = "General José de San Martín", "Guachipas", "Iruya"
CALDERA, CANDELARIA, POMA, VINA = "La Caldera", "La Candelaria", "La Poma", "La Viña"
ANDES, METAN, MOLINOS, ORAN = "Los Andes", "Metán", "Molinos", "Orán"
RIVADAVIA, RFRONTERA, RLERMA = "Rivadavia", "Rosario de la Frontera", "Rosario de Lerma"
SANCARLOS, SVICTORIA = "San Carlos", "Santa Victoria"

DEPTOS = {ANTA, CACHI, CAFAYATE, CAPITAL, CERRILLOS, CHICOANA, GUEMES, SANMARTIN, GUACHIPAS,
          IRUYA, CALDERA, CANDELARIA, POMA, VINA, ANDES, METAN, MOLINOS, ORAN, RIVADAVIA,
          RFRONTERA, RLERMA, SANCARLOS, SVICTORIA}

# Area Operativa de residencia -> departamento. Clave: nombre normalizado (sin acentos, minusculas).
AO_DEPTO = {
    "colonia sta rosa": ORAN, "pichanal": ORAN, "hipolito yrigoyen": ORAN, "urundel": ORAN,
    "oran": ORAN,
    "aguaray": SANMARTIN, "salvador mazza": SANMARTIN, "embarcacion": SANMARTIN,
    "tartagal": SANMARTIN, "gral mosconi": SANMARTIN,
    "morillo": RIVADAVIA, "sta victoria este": RIVADAVIA, "rivadavia banda sur": RIVADAVIA,
    "alto la sierra": RIVADAVIA, "la union": RIVADAVIA,
    "sta victoria oeste": SVICTORIA, "nazareno": SVICTORIA,
    "iruya": IRUYA,
    "las lajitas": ANTA, "j. v. gonzalez": ANTA, "el quebrachal": ANTA, "apolinario saravia": ANTA,
    "el galpon": METAN, "metan": METAN,
    "rosario de la frontera": RFRONTERA, "el potrero": RFRONTERA,
    "el tala": CANDELARIA,
    "gral guemes": GUEMES,
    "cafayate": CAFAYATE,
    "san carlos": SANCARLOS, "angastaco": SANCARLOS,
    "molinos": MOLINOS, "seclantas": MOLINOS,
    "cachi": CACHI,
    "s. a. de los cobres": ANDES,
    "cerrillos": CERRILLOS, "la merced": CERRILLOS,
    "rosario de lerma": RLERMA, "campo quijano": RLERMA,
    "chicoana": CHICOANA, "el carril": CHICOANA,
    "coronel moldes": VINA, "la vina": VINA,
    "guachipas": GUACHIPAS,
    "la caldera": CALDERA,
    "capital": CAPITAL,
    "la poma": POMA,
}

# Codigo de establecimiento del PDF de internacion -> departamento.
EST_DEPTO = {
    "00010": ANTA, "00070": ANTA, "00140": ANTA, "00170": ANTA,
    "00420": CACHI, "00650": CAFAYATE, "00870": CALDERA, "01090": CANDELARIA,
    "01530": CAPITAL, "01624": CAPITAL, "01643": CAPITAL, "01680": CAPITAL, "01782": CAPITAL,
    "73678": CAPITAL, "85500": CAPITAL,
    "01970": CERRILLOS, "01990": CERRILLOS,
    "02200": CHICOANA, "02220": CHICOANA,
    "02470": SANMARTIN, "02520": SANMARTIN, "02570": SANMARTIN, "02620": SANMARTIN,
    "02680": SANMARTIN,
    "03020": GUEMES, "03280": GUACHIPAS, "03520": IRUYA, "03780": POMA,
    "03990": VINA, "04000": VINA,
    "04240": ANDES, "04490": METAN, "04550": METAN,
    "04800": MOLINOS, "04810": MOLINOS,
    "05040": ORAN, "05060": ORAN, "05100": ORAN, "05120": ORAN, "05150": ORAN,
    "05360": RIVADAVIA, "05400": RIVADAVIA, "05440": RIVADAVIA, "05460": RIVADAVIA,
    "05490": RIVADAVIA,
    "05730": RFRONTERA, "05780": RFRONTERA,
    "05990": RLERMA, "06060": RLERMA,
    "06300": SANCARLOS, "06350": SANCARLOS,
    "06580": SVICTORIA, "06600": SVICTORIA,
}


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def norm(s):
    """Minusculas sin acentos, espacios colapsados. Para comparar etiquetas de la fuente."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


_NUM_RE = re.compile(r"^-?[\d.,]+$")


def is_num(s):
    s = str(s).strip()
    return bool(s) and bool(_NUM_RE.match(s)) and any(c.isdigit() for c in s)


def parse_num(s):
    """Numero en configuracion latina o inglesa -> float. Ver 'Formato numerico' en la metodologia.

    Reglas, en orden:
      '1.234,56' (ambos)      -> el ultimo separador es el decimal      -> latina
      '1,85'     (solo coma)  -> decimal coma                           -> latina
      '2.672.823'(varios '.') -> puntos de miles                        -> latina
      '110.749'  (un '.', exactamente 3 digitos detras) -> punto de miles
      '8.7'      (un '.', otro largo)                   -> punto decimal
    """
    s = str(s).strip().replace(" ", " ").replace(" ", "")
    if not is_num(s):
        raise ValueError("no numerico: %r" % s)
    neg = s.startswith("-")
    s = s.lstrip("-")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if s.count(",") == 1 else s.replace(",", "")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    elif s.count(".") == 1 and len(s.split(".")[1]) == 3:
        s = s.replace(".", "")
    v = float(s)
    return -v if neg else v


def _f(v):
    return "%d" % v if float(v).is_integer() else "%s" % v


def grid(table):
    """Tabla de python-docx -> lista de filas de texto, sin repetir celdas combinadas."""
    out = []
    for row in table.rows:
        cells, seen = [], set()
        for c in row.cells:
            if id(c._tc) in seen:
                continue
            seen.add(id(c._tc))
            cells.append(re.sub(r"\s+", " ", c.text).strip())
        out.append(cells)
    return out


def find_table(grids, *signatures):
    """Primera tabla cuyo texto contiene todas las firmas (normalizadas)."""
    for g in grids:
        blob = norm(" ".join(" ".join(r) for r in g))
        if all(norm(sig) in blob for sig in signatures):
            return g
    raise SystemExit("ERROR: no se encontro la tabla con las firmas %r. "
                     "El documento cambio de estructura: revisar el runbook." % (signatures,))


def year_row(g):
    """Indice y lista de anios de la fila de encabezado de anios."""
    for i, row in enumerate(g):
        yrs = [int(c) for c in row if re.fullmatch(r"(19|20)\d{2}", c.strip())]
        if len(yrs) >= 3:
            return i, yrs
    raise SystemExit("ERROR: la tabla no tiene fila de anios.")


def wide_series(g, skip_prefixes=("fuente",)):
    """Tabla con anios en columnas -> (anios, [(etiqueta, [valores])]).

    Los valores se alinean por ORDEN de aparicion, no por indice de columna: en la Tabla 1 la
    celda 'HECHOS VITALES' esta combinada verticalmente y corre los anios una columna a la
    izquierda respecto de las filas de datos.

    Una fila con etiqueta y SIN numeros es continuacion de la etiqueta anterior: asi viene la
    tabla 'Estadisticas vitales 2020-2025', donde 'Defunciones' / 'Generales' ocupan dos filas.
    """
    i0, years = year_row(g)
    out = []
    for row in g[i0 + 1:]:
        if not row or not row[0]:
            continue
        label = row[0]
        if any(norm(label).startswith(p) for p in skip_prefixes):
            continue
        vals = [parse_num(c) for c in row if is_num(c)]
        if not vals:
            if out:
                out[-1] = (out[-1][0] + " " + label, out[-1][1])
            continue
        if len(vals) != len(years):
            raise SystemExit("ERROR: fila %r tiene %d valores para %d anios."
                             % (label, len(vals), len(years)))
        out.append((label, vals))
    return years, out


def long_table(g):
    """Tabla con anios en la primera columna -> (encabezados, {anio: [valores]})."""
    head, data = None, {}
    for row in g:
        if not row or not row[0]:
            continue
        if re.match(r"^(19|20)\d{2}", row[0].strip()):
            data[int(row[0].strip()[:4])] = [parse_num(c) if is_num(c) else None for c in row[1:]]
        elif head is None and norm(row[0]).startswith("ano"):
            head = row[1:]
    if head is None or not data:
        raise SystemExit("ERROR: tabla anio-en-filas mal interpretada.")
    return head, data


# --------------------------------------------------------------------------
# 1. Hechos vitales provinciales
# --------------------------------------------------------------------------
# Tabla 1 (Resumen Quinquenal): etiqueta de la fuente -> (metrica, desagregacion).
T1_MAP = {
    "total def. mayores": ("defunciones", "1 año y más"),
    "total def. < 1 ano": ("defunciones", "Menores de 1 año"),
    "total def. 1 a 4 anos": ("defunciones", "De 1 a 4 años"),
    "total defunciones": ("defunciones", "Total"),
    "otras defunciones": ("otras_defunciones", "Total"),
    "defunciones fetales": ("defunciones_fetales", "Total"),
    "total def. maternas": ("defunciones_maternas", "Total"),
    "nacidos vivos": ("nacidos_vivos", "Total"),
    "matrimonios": ("matrimonios", "Total"),
}
# Tabla 'Estadisticas vitales 2020-2025', en orden de aparicion. `solo_2020` marca las series que
# ya vienen -y mejor- de la Tabla 1: de esas solo se toma el anio 2020.
T2_ORDEN = [
    ("defunciones generales", "defunciones", "Total", True),
    ("defunciones < 1 ano", "defunciones_infantiles", "Total", False),
    ("defunciones menor 28 dias", "defunciones_infantiles", "Neonatal (< 28 días)", False),
    ("defunciones mayor 28 dias", "defunciones_infantiles", "Posneonatal (28 días y más)", False),
    ("defunciones maternas", "defunciones_maternas", "Total", True),
    ("defuncion fetal", "defunciones_fetales", "Total", True),
    ("nacidos vivos", "nacidos_vivos", "Total", True),
    ("nacidos vivos menor 2.500 grs.", "nacidos_vivos", "Menos de 2.500 g", False),
    ("nacidos vivos mayor 2.500 grs.", "nacidos_vivos", "2.500 g y más", False),
    ("nacidos vivos peso s/e", "nacidos_vivos", "Peso sin especificar", False),
    ("matrimonios", "matrimonios", "Total", True),
]


def hechos_vitales(grids, notas):
    rec = {}  # (anio, metrica, desagregacion) -> valor

    # -- Tabla 1: manda para 2021-2025 --------------------------------------
    years1, filas1 = wide_series(find_table(grids, "HECHOS VITALES"))
    tmi_pub = None
    for label, vals in filas1:
        key = norm(label)
        if key == "tmi":
            tmi_pub = dict(zip(years1, vals))
            continue
        if key not in T1_MAP:
            raise SystemExit("ERROR: etiqueta desconocida en la Tabla 1: %r" % label)
        met, des = T1_MAP[key]
        for a, v in zip(years1, vals):
            rec[(a, met, des)] = v
    faltan = set(T1_MAP) - {norm(l) for l, _ in filas1}
    if faltan:
        raise SystemExit("ERROR: faltan filas en la Tabla 1: %s" % sorted(faltan))

    # control: Total = mayores + <1 + 1a4
    for a in years1:
        tot = rec[(a, "defunciones", "Total")]
        partes = sum(rec[(a, "defunciones", d)]
                     for d in ("1 año y más", "Menores de 1 año", "De 1 a 4 años"))
        if tot != partes:
            raise SystemExit("ERROR: %d defunciones %s != suma de componentes %s" % (a, tot, partes))

    # -- Tabla 2020-2025: solo el anio 2020 y las aperturas ------------------
    years2, filas2 = wide_series(find_table(grids, "Menor 28"))
    if len(filas2) != len(T2_ORDEN):
        raise SystemExit("ERROR: la tabla 2020-2025 trae %d filas, se esperaban %d: %s"
                         % (len(filas2), len(T2_ORDEN), [l for l, _ in filas2]))
    for (label, vals), (esperado, met, des, solo_2020) in zip(filas2, T2_ORDEN):
        if norm(label) != esperado:
            raise SystemExit("ERROR: la tabla 2020-2025 cambio de orden: %r != %r"
                             % (norm(label), esperado))
        for a, v in zip(years2, vals):
            if solo_2020 and a in years1:
                if rec.get((a, met, des)) != v:
                    notas.append("descartado de la tabla 2020-2025: %s (%s) %d = %s; se publica %s, "
                                 "de la Tabla 1 (Resumen Quinquenal)"
                                 % (met, des, a, _f(v), _f(rec[(a, met, des)])))
                continue
            rec[(a, met, des)] = v
    # el total de def. infantiles del anio 2020 no esta en la Tabla 1
    rec.setdefault((min(years2), "defunciones", "Menores de 1 año"),
                   rec[(min(years2), "defunciones_infantiles", "Total")])

    anios = sorted({a for a, _, _ in rec})

    # control: def. < 1 anio = neonatal + posneonatal
    for a in anios:
        tot = rec.get((a, "defunciones_infantiles", "Total"))
        neo = rec.get((a, "defunciones_infantiles", "Neonatal (< 28 días)"))
        pos = rec.get((a, "defunciones_infantiles", "Posneonatal (28 días y más)"))
        if None in (tot, neo, pos):
            continue
        if neo + pos != tot:
            raise SystemExit("ERROR: %d def. <1 anio %s != %s + %s" % (a, tot, neo, pos))
        if neo < pos:
            notas.append("%d: las defunciones neonatales (%s) quedan por debajo de las posneonatales "
                         "(%s), invirtiendo el patron de los demas anios (neonatal 61-75%%); "
                         "posible intercambio en la fuente." % (a, _f(neo), _f(pos)))

    # control: nacidos vivos = suma de las categorias de peso
    for a in anios:
        tot = rec.get((a, "nacidos_vivos", "Total"))
        partes = [rec.get((a, "nacidos_vivos", d))
                  for d in ("Menos de 2.500 g", "2.500 g y más", "Peso sin especificar")]
        if tot is None or None in partes:
            continue
        if sum(partes) != tot:
            notas.append("%d: los nacidos vivos por peso al nacer suman %s contra %s del total "
                         "publicado (diferencia %+d); se emiten tal cual los publica la fuente."
                         % (a, _f(sum(partes)), _f(tot), int(sum(partes) - tot)))

    # -- Tasas ---------------------------------------------------------------
    head7, data7 = long_table(find_table(grids, "Tasa Natalidad"))
    col7 = {norm(h): i for i, h in enumerate(head7)}
    for a, vals in sorted(data7.items()):
        rec[(a, "tasa_natalidad", "Total")] = vals[col7["tasa natalidad"]]
        rec[(a, "tasa_mortalidad_general", "Total")] = vals[col7["tasa mortalidad general"]]
        rec[(a, "tasa_mortalidad_infantil", "Total")] = vals[col7["tasa mortalidad infantil"]]
        # control: la TMI publicada tiene que salir de def.<1 / nacidos vivos
        nv, d1 = rec[(a, "nacidos_vivos", "Total")], rec[(a, "defunciones", "Menores de 1 año")]
        calc = round(d1 / nv * 1000, 2)
        if abs(calc - vals[col7["tasa mortalidad infantil"]]) > 0.011:
            raise SystemExit("ERROR: TMI %d publicada %s != recalculada %s"
                             % (a, vals[col7["tasa mortalidad infantil"]], calc))
        # las defunciones de esta tabla pueden diferir de la Tabla 1
        dpub = vals[col7["defunciones"]]
        if dpub != rec[(a, "defunciones", "Total")]:
            notas.append("descartado de la tabla de tasas: defunciones %d = %s; se publica %s, "
                         "de la Tabla 1 (Resumen Quinquenal)"
                         % (a, _f(dpub), _f(rec[(a, "defunciones", "Total")])))
    # TMI de los anios que la fuente no tabula (2020), con la misma formula ya validada arriba
    for a in anios:
        d1 = rec.get((a, "defunciones", "Menores de 1 año"))
        nv = rec.get((a, "nacidos_vivos", "Total"))
        if (a, "tasa_mortalidad_infantil", "Total") not in rec and d1 is not None and nv:
            rec[(a, "tasa_mortalidad_infantil", "Total")] = round(d1 / nv * 1000, 2)

    if tmi_pub:  # la Tabla 1 publica la TMI redondeada a un decimal
        for a, v in tmi_pub.items():
            if abs(round(rec[(a, "tasa_mortalidad_infantil", "Total")], 1) - v) > 0.051:
                raise SystemExit("ERROR: la TMI de la Tabla 1 (%s) no coincide en %d" % (v, a))

    # tasa de mortalidad materna: por 10.000 nacidos vivos, validada contra su propio cuadro
    pub = [parse_num(c) for r in find_table(grids, "T.M.M.") for c in r if is_num(c)]
    for a in anios:
        dm = rec.get((a, "defunciones_maternas", "Total"))
        nv = rec.get((a, "nacidos_vivos", "Total"))
        if dm is None or not nv:
            continue
        rec[(a, "tasa_mortalidad_materna", "Total")] = round(dm / nv * 10000, 2)
    for dm, nv, tmm in (pub[:3], pub[3:6]):
        if abs(round(dm / nv * 10000, 2) - tmm) > 0.011:
            raise SystemExit("ERROR: la TMM publicada (%s) no se reproduce desde %s/%s" % (tmm, dm, nv))

    filas = [{"anio": a, "desagregacion": d, "metrica": m, "valor": v}
             for (a, m, d), v in sorted(rec.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0]))]
    return pd.DataFrame(filas)[["anio", "desagregacion", "metrica", "valor"]], anios


# --------------------------------------------------------------------------
# 2. Nacidos vivos por Area Operativa de residencia
# --------------------------------------------------------------------------
def nacidos_por_ao(grids, hv, notas):
    g = find_table(grids, "A. O.", "Total Provincial")
    _, years = year_row(g)
    filas, total_pub = [], None
    for row in g:
        if not row or not row[0]:
            continue
        if norm(row[0]).startswith("total provincial"):
            total_pub = dict(zip(years, [parse_num(c) for c in row if is_num(c)]))
            continue
        if not re.fullmatch(r"\d+", row[0].strip()):
            continue
        cod, nombre = int(row[0]), row[1]
        vals = [parse_num(c) for c in row[2:] if is_num(c)]
        if len(vals) != len(years):
            raise SystemExit("ERROR: el AO %r trae %d valores para %d anios."
                             % (nombre, len(vals), len(years)))
        dep = AO_DEPTO.get(norm(nombre))
        if dep is None:
            raise SystemExit("ERROR: Area Operativa sin departamento asignado: %r. "
                             "Agregarla a AO_DEPTO en el runbook." % nombre)
        for a, v in zip(years, vals):
            filas.append({"anio": a, "cod_ao": cod, "area_operativa": nombre,
                          "departamento": dep, "metrica": "nacidos_vivos_res", "valor": v})

    if total_pub is None:
        raise SystemExit("ERROR: la tabla por Area Operativa no trae fila 'Total Provincial'.")
    n_ao = len({f["cod_ao"] for f in filas})
    cubiertos = {f["departamento"] for f in filas}
    if cubiertos != DEPTOS:
        raise SystemExit("ERROR: departamentos sin cubrir: %s" % sorted(DEPTOS - cubiertos))

    # control decisivo: la suma de las AO tiene que dar el total provincial y el de la Tabla 1
    for a in years:
        suma = sum(f["valor"] for f in filas if f["anio"] == a)
        nv_t1 = float(hv[(hv.anio == a) & (hv.metrica == "nacidos_vivos")
                         & (hv.desagregacion == "Total")].valor.iloc[0])
        if suma != total_pub[a] or suma != nv_t1:
            raise SystemExit("ERROR: %d suma de AO %s, total publicado %s, Tabla 1 %s"
                             % (a, suma, total_pub[a], nv_t1))
        filas.append({"anio": a, "cod_ao": 0, "area_operativa": "Total",
                      "departamento": "Salta", "metrica": "nacidos_vivos_res", "valor": suma})

    notas.append("nacidos vivos por Area Operativa de residencia: %d AO agrupadas en %d "
                 "departamentos; la suma coincide exactamente con el total provincial en los %d anios."
                 % (n_ao, len(cubiertos), len(years)))
    df = pd.DataFrame(filas).sort_values(["metrica", "anio", "cod_ao"])
    return df[["anio", "cod_ao", "area_operativa", "departamento", "metrica", "valor"]], n_ao


# --------------------------------------------------------------------------
# 3. Servicios provinciales: consultas e internacion
# --------------------------------------------------------------------------
METS_RENDIMIENTO = ["camas_disponibles", "pacientes_dia", "ocupacion_camas",
                    "permanencia_promedio", "giro_camas", "egresos",
                    "tasa_mortalidad_hospitalaria"]


def servicios(grids, hv, notas):
    filas = []

    _, data5 = long_table(find_table(grids, "Consulta", "habit"))
    for a, v in sorted(data5.items()):
        filas += [{"anio": a, "metrica": "consultas_medicas", "valor": v[0]},
                  {"anio": a, "metrica": "poblacion", "valor": v[1]},
                  {"anio": a, "metrica": "consultas_por_habitante", "valor": v[2]}]
        if abs(v[0] / v[1] - v[2]) > 0.011:
            raise SystemExit("ERROR: consultas por habitante %d no cierra: %s/%s != %s"
                             % (a, v[0], v[1], v[2]))

    head6, data6 = long_table(find_table(grids, "Giro Cama"))
    if len(head6) != len(METS_RENDIMIENTO):
        raise SystemExit("ERROR: la tabla de rendimiento trae %d columnas, se esperaban %d."
                         % (len(head6), len(METS_RENDIMIENTO)))
    for a, v in sorted(data6.items()):
        for met, val in zip(METS_RENDIMIENTO, v):
            filas.append({"anio": a, "metrica": met, "valor": val})
        if abs(v[1] / v[0] * 100 - v[2]) > 0.051:
            raise SystemExit("ERROR: la ocupacion de camas de %d no cierra." % a)
        if abs(v[5] / v[0] - v[4]) > 0.051:
            raise SystemExit("ERROR: el giro de camas de %d no cierra." % a)

    # control: la tasa de mortalidad general publicada tiene que salir de defunciones/poblacion
    for a, v in sorted(data5.items()):
        sel = hv[(hv.anio == a) & (hv.metrica == "tasa_mortalidad_general")]
        d = hv[(hv.anio == a) & (hv.metrica == "defunciones") & (hv.desagregacion == "Total")]
        if not len(sel) or not len(d):
            continue
        calc = round(float(d.valor.iloc[0]) / v[1] * 1000, 2)
        if abs(calc - float(sel.valor.iloc[0])) > 0.011:
            notas.append("%d: la tasa de mortalidad general publicada (%s) no se reproduce con la "
                         "poblacion que publica el propio documento (%s da %.2f); la fuente uso una "
                         "proyeccion de poblacion anterior. Se publica la tasa tal como la emitio el "
                         "MSP." % (a, _f(sel.valor.iloc[0]), _f(v[1]), calc))

    df = pd.DataFrame(filas).sort_values(["metrica", "anio"])
    return df[["anio", "metrica", "valor"]]


# --------------------------------------------------------------------------
# 4. Internacion por departamento (del PDF por establecimiento)
# --------------------------------------------------------------------------
EST_RE = re.compile(
    r"(\d{5})\s+([^\d]+?)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"
    r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)")
TOT_RE = re.compile(
    r"TOTAL\s+ZONA\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"
    r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)")


def internacion_depto(pdf_path, notas):
    with pdfplumber.open(pdf_path) as pdf:
        texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
    texto = re.sub(r"\s+", " ", texto)

    ests = []
    for m in EST_RE.finditer(texto):
        cod, nombre = m.group(1), m.group(2).strip()
        camas, pacdia = float(m.group(3)), float(m.group(4))
        altas, defs, egr, pases = (int(m.group(i)) for i in (8, 9, 10, 11))
        if altas + defs != egr:
            raise SystemExit("ERROR: %s %s: altas %d + defunciones %d != egresos %d"
                             % (cod, nombre, altas, defs, egr))
        dep = EST_DEPTO.get(cod)
        if dep is None:
            raise SystemExit("ERROR: establecimiento sin departamento asignado: %s %r. "
                             "Agregarlo a EST_DEPTO en el runbook." % (cod, nombre))
        ests.append((cod, nombre, dep, camas, pacdia, altas, defs, egr, pases))

    if len({e[0] for e in ests}) != len(EST_DEPTO):
        raise SystemExit("ERROR: se parsearon %d establecimientos distintos, el mapa tiene %d."
                         % (len({e[0] for e in ests}), len(EST_DEPTO)))
    ests = list({e[0]: e for e in ests}.values())

    mt = TOT_RE.search(texto)
    if not mt:
        raise SystemExit("ERROR: no se encontro la fila TOTAL ZONA en el PDF.")
    t_camas, t_pacdia = float(mt.group(1)), float(mt.group(2))
    t_ocup, t_perm, t_giro = float(mt.group(3)), float(mt.group(4)), float(mt.group(5))
    t_altas, t_defs, t_egr, t_pases = (int(mt.group(i)) for i in (6, 7, 8, 9))
    t_tasa = float(mt.group(10))

    # control cruzado: la suma de los establecimientos tiene que dar el TOTAL ZONA
    s = lambda i: sum(e[i] for e in ests)
    for lbl, got, exp, tol in [("camas", s(3), t_camas, 0.1), ("pacientes-dia", s(4), t_pacdia, 0.1),
                               ("altas", s(5), t_altas, 0), ("defunciones", s(6), t_defs, 0),
                               ("egresos", s(7), t_egr, 0), ("pases", s(8), t_pases, 0)]:
        if abs(got - exp) > tol:
            raise SystemExit("ERROR: %s suman %s contra %s del TOTAL ZONA." % (lbl, got, exp))
    if (abs(s(4) / s(3) * 100 - t_ocup) > 0.051 or abs(s(4) * 365 / s(7) - t_perm) > 0.051
            or abs(s(7) / s(3) - t_giro) > 0.051 or abs(s(6) / s(7) * 100 - t_tasa) > 0.051):
        raise SystemExit("ERROR: los derivados recalculados no reproducen el TOTAL ZONA.")

    # Agregacion a departamento: se suman los aditivos y se RECALCULAN los cocientes.
    # Promediar ocupacion, permanencia, giro o tasa entre establecimientos daria mal: son
    # cocientes con denominadores de tamano muy distinto (San Bernardo pesa 250 veces La Poma).
    agg = {}
    for cod, nom, dep, camas, pacdia, altas, defs, egr, pases in ests:
        a = agg.setdefault(dep, dict(camas=0.0, pacdia=0.0, altas=0, defs=0, egr=0, pases=0, n=0))
        a["camas"] += camas
        a["pacdia"] += pacdia
        a["altas"] += altas
        a["defs"] += defs
        a["egr"] += egr
        a["pases"] += pases
        a["n"] += 1

    filas = []
    for dep, a in sorted(agg.items()):
        vals = {
            "camas_disponibles": round(a["camas"], 2),
            "pacientes_dia": round(a["pacdia"], 2),
            "altas": float(a["altas"]),
            "defunciones_hosp": float(a["defs"]),
            "egresos": float(a["egr"]),
            "pases": float(a["pases"]),
            "establecimientos": float(a["n"]),
            "ocupacion_camas": round(a["pacdia"] / a["camas"] * 100, 2),
            "permanencia_promedio": round(a["pacdia"] * 365 / a["egr"], 2),
            "giro_camas": round(a["egr"] / a["camas"], 2),
            "tasa_mortalidad_hospitalaria": round(a["defs"] / a["egr"] * 100, 2),
        }
        for met, v in vals.items():
            filas.append({"anio": ANIO_INTERNACION_DEPTO, "departamento": dep,
                          "metrica": met, "valor": v})

    if set(agg) != DEPTOS:
        raise SystemExit("ERROR: internacion, departamentos sin cubrir: %s" % sorted(DEPTOS - set(agg)))
    notas.append("internacion %d: %d establecimientos agregados a %d departamentos; los cocientes "
                 "(ocupacion, permanencia, giro, mortalidad) se recalculan sobre los totales sumados, "
                 "no se promedian entre establecimientos."
                 % (ANIO_INTERNACION_DEPTO, len(ests), len(agg)))
    df = pd.DataFrame(filas).sort_values(["metrica", "departamento"])
    return df[["anio", "departamento", "metrica", "valor"]], len(ests), t_egr


# --------------------------------------------------------------------------
def main():
    docs = glob.glob(os.path.join(FUENTES, "*.docx"))
    pdfs = [p for p in glob.glob(os.path.join(FUENTES, "*.pdf")) if "internaci" in norm(p)]
    if len(docs) != 1:
        raise SystemExit("ERROR: se esperaba 1 .docx en %s, hay %d." % (FUENTES, len(docs)))
    if len(pdfs) != 1:
        raise SystemExit("ERROR: se esperaba 1 PDF de internacion en %s, hay %d." % (FUENTES, len(pdfs)))

    notas = []
    grids = [grid(t) for t in docx.Document(docs[0]).tables]
    print("tablas encontradas en el .docx: %d" % len(grids))

    hv, anios = hechos_vitales(grids, notas)
    ao, n_ao = nacidos_por_ao(grids, hv, notas)
    sv = servicios(grids, hv, notas)
    it, n_est, egr_pdf = internacion_depto(pdfs[0], notas)

    # el docx y el PDF publican egresos distintos para el mismo anio
    egr_docx = sv[(sv.anio == ANIO_INTERNACION_DEPTO) & (sv.metrica == "egresos")].valor
    if len(egr_docx) and int(egr_docx.iloc[0]) != egr_pdf:
        notas.append("egresos %d: el docx publica %d y el PDF por establecimiento %d (diferencia "
                     "%+d); la serie provincial usa el docx y el detalle departamental el PDF."
                     % (ANIO_INTERNACION_DEPTO, int(egr_docx.iloc[0]), egr_pdf,
                        egr_pdf - int(egr_docx.iloc[0])))

    salidas = [
        ("Salud_Hechos_Vitales_Salta_provincia_%d-%d.csv" % (min(anios), max(anios)), hv),
        ("Salud_Nacidos_Vivos_Salta_area_operativa_%d-%d.csv"
         % (int(ao.anio.min()), int(ao.anio.max())), ao),
        ("Salud_Servicios_Salta_provincia_%d-%d.csv" % (int(sv.anio.min()), int(sv.anio.max())), sv),
        ("Salud_Internacion_Salta_departamento_%d.csv" % ANIO_INTERNACION_DEPTO, it),
    ]
    for nombre, df in salidas:
        df.to_csv(os.path.join(HERE, nombre), index=False, encoding="utf-8-sig")

    # -- relectura de control, con las mismas opciones que usa adapters.py --
    print("\n%-58s %7s %5s" % ("archivo", "filas", "NaN"))
    for nombre, _ in salidas:
        chk = pd.read_csv(os.path.join(HERE, nombre), encoding="utf-8-sig")
        chk["valor"] = pd.to_numeric(chk["valor"], errors="coerce")
        nan = int(chk["valor"].isna().sum())
        if nan:
            raise SystemExit("ERROR: %s tiene %d valores que no parsean como numero." % (nombre, nan))
        print("%-58s %7d %5d" % (nombre, len(chk), nan))

    print("\nAreas Operativas: %d | establecimientos: %d | anios: %d-%d"
          % (n_ao, n_est, min(anios), max(anios)))
    print("\nIncidencias detectadas (van a la metodologia):")
    for n in notas:
        print("  - %s" % n)
    print("\nOK")


if __name__ == "__main__":
    main()
```
