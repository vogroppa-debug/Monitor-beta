# Actualización — Educación (bases nacionales «agregada»), Provincia de Salta

Serie **2021–2025** de educación en Salta **por departamento**, reconstruida desde las bases
abiertas «agregada» de la Secretaría de Educación de la Nación (Relevamiento Anual + APRENDER).

> Cuatro cosas que hay que saber antes de usar esto:
> 1. **La granularidad más fina de la fuente es el DEPARTAMENTO.** No hay localidad en ninguna
>    de estas bases. Tampoco hay códigos INDEC: el departamento viene sólo como texto.
> 2. **`Enmascarado` NO se puede borrar.** Es un departamento ficticio donde la fuente funde,
>    por secreto estadístico (Ley 17.622), a los departamentos con ≤3 establecimientos en una
>    combinación sector-ámbito-nivel. Si se lo descarta, los totales provinciales dejan de cerrar.
> 3. **El esquema cambia de año en año.** 2024 escribe `Departamento`/`Grado` con mayúscula;
>    2025 agrega África y Oceanía; APRENDER 2021 trae el nombre de La Viña con un carácter
>    corrupto. El script mapea **por nombre de columna** y de forma insensible a mayúsculas.
> 4. **APRENDER rota de nivel por año** (primaria 6° en 2021/2023/2025, secundaria 5°-6° en
>    2022/2024) y sus valores ya vienen **ponderados** por la fuente.

Metodología y verificaciones: `Metodologia_Educacion_Nacion_Salta.md`.

## Qué genera (en `datos-drive/`)

| Archivo | Base de origen | Dimensiones propias |
|---|---|---|
| `Educacion_Matricula_Salta_departamento_2021-2025.csv` | Matrícula (usuaria 2) | `nivel` |
| `Educacion_MatriculaEdad_Salta_departamento_2021-2025.csv` | Matrícula por edad (usuaria 7) | `nivel`, `edad` |
| `Educacion_Trayectoria_Salta_departamento_2021-2025.csv` | Trayectoria (usuaria 3) | `nivel`, `sexo` |
| `Educacion_Cargos_Salta_departamento_2021-2025.csv` | Cargos (usuaria 4) | `nivel`, `funcion`, `estado` |
| `Educacion_CargosPlanta_Salta_departamento_2021-2025.csv` | Cargos Bis (usuaria 4bis) | `nivel`, `tipo`, `categoria`, `planta_tipo` |
| `Educacion_Establecimientos_Salta_departamento_2021-2025.csv` | Características (usuaria 5) | `grupo`, `detalle` |
| `Educacion_PoblacionEscolar_Salta_departamento_2021-2025.csv` | Población (usuaria 6) | `nivel`, `grupo`, `detalle` |
| `Educacion_APRENDER_Salta_departamento_2021-2025.csv` | APRENDER censal | `nivel_evaluado`, `area`, `nivel_desempeno` |

Todos comparten el prefijo `anio, departamento, sector, ambito` y terminan en `metrica, valor`
(esquema canónico del Monitor). Separador `,`, decimal `.`, sin separador de miles, `utf-8-sig`.

## 1. Requisitos

```bash
pip install pandas
```

El script usa sólo `urllib` de la biblioteca estándar para descargar (`pandas` se usa recién en
la verificación posterior, no en la construcción).

## 2. Correr el script

```bash
python actualizar_educacion_nacion_salta.py
```

La primera corrida baja ~180 MB a `datos-drive/fuentes/` (45 archivos) y tarda varios minutos;
las siguientes reutilizan la caché. Para regenerar sólo los CSV, borrar los `Educacion_*.csv`
y volver a correr (las fuentes quedan cacheadas).

Variables de entorno opcionales: `EDU_OUT` (carpeta de salida) y `EDU_FUENTES` (caché de fuentes).

## 3. Cómo resuelve la descarga (y por qué así)

La página de datos abiertos **no tiene enlaces**: es un widget que lee un **Google Sheet**
público, y ese Sheet apunta a archivos alojados en el **OneDrive** del Ministerio. El script:

1. Baja el catálogo del Sheet (`gviz/tq?tqx=out:csv`) — **es la autoridad**, no se hardcodean URLs.
2. De cada fila saca `user` y `token` del enlace y lo reescribe a la forma de descarga anónima
   `/_layouts/15/download.aspx?share=<token>`.
3. Aborta si la respuesta redirige a `login.microsoftonline.com` o devuelve HTML: **un token
   revocado responde HTTP 200**, así que hay que mirar la URL final y el `Content-Type`, no el
   status code.

**Riesgo de durabilidad:** los archivos cuelgan del OneDrive personal de un agente del
Ministerio. Si esa cuenta se da de baja, se rompen todas las URLs a la vez. Por eso la caché
local en `fuentes/` es parte del entregable, no un descarte.

## 4. Verificar antes de dar por buena la actualización

1. **Cobertura**: los 8 CSV deben traer los 5 años (o los que haya publicado la fuente).
2. **Cierre contra la fuente**: Σ `matricula` del CSV == Σ de las columnas de grado de la base
   de matrícula, año por año (el script lo deja listo para chequear; ver metodología).
3. **Departamentos**: exactamente los 23 canónicos + `Enmascarado` (+ `Sin datos` en Cargos).
   Cualquier nombre nuevo es señal de un departamento no mapeado.
4. **Incidencias**: el script las imprime al final; hay que volcarlas a la metodología.

**Actualizar cada año:** agregar el año a `ANIOS` y correr. Si la fuente vuelve a cambiar la
capitalización o agrega columnas nuevas, el script lo tolera (mapea por nombre) pero conviene
revisar las incidencias que imprime.

---

## Script completo

```python
# -*- coding: utf-8 -*-
"""Educacion (bases nacionales 'agregada') -> CSVs tidy por departamento de Salta,
2021-2025. Fuente: catalogo publico de la Secretaria de Educacion (Google Sheet) ->
archivos en OneDrive del Ministerio. Ver Metodologia_Educacion_Nacion_Salta.md."""
import os, re, io, csv, sys, ssl, math, urllib.request, unicodedata
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('EDU_OUT', HERE)
FUENTES = os.environ.get('EDU_FUENTES', os.path.join(HERE, 'fuentes'))
SHEET = ("https://docs.google.com/spreadsheets/d/"
         "1XaSz7AJ-EkpLqj_qjx3TPdBfJaQvqEZwg3sOYagtOsI/gviz/tq?tqx=out:csv&headers=1")
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36'}
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
ANIOS = [2021, 2022, 2023, 2024, 2025]
NOTAS = []

# ---------------------------------------------------------------- departamentos
_DEPT_CANON = {
    "ANTA": "Anta", "CACHI": "Cachi", "CAFAYATE": "Cafayate", "CAPITAL": "Capital",
    "CERRILLOS": "Cerrillos", "CHICOANA": "Chicoana", "GENERAL GUEMES": "General Güemes",
    "GENERAL JOSE DE SAN MARTIN": "General José de San Martín", "GUACHIPAS": "Guachipas",
    "IRUYA": "Iruya", "LA CALDERA": "La Caldera", "LA CANDELARIA": "La Candelaria",
    "LA POMA": "La Poma", "LA VINA": "La Viña", "LOS ANDES": "Los Andes", "METAN": "Metán",
    "MOLINOS": "Molinos", "ORAN": "Orán", "RIVADAVIA": "Rivadavia",
    "ROSARIO DE LA FRONTERA": "Rosario de la Frontera", "ROSARIO DE LERMA": "Rosario de Lerma",
    "SAN CARLOS": "San Carlos", "SANTA VICTORIA": "Santa Victoria",
}
DEPTOS_23 = sorted(set(_DEPT_CANON.values()))
NO_GEO = {"Enmascarado", "Sin datos"}


def _uu(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c)).upper().strip()


# El .csv de APRENDER 2021 trae 'LA VIï¿½A': la fuente guardo un caracter de reemplazo
# (U+FFFD) donde iba la Ñ y despues lo volvio a codificar. Se repara sustituyendo la
# secuencia por 'N' y reintentando el match; queda registrado como incidencia.
_MOJI = re.compile('(?:�|ï¿½)+')
MOJIBAKE = set()


def norm_dept(s):
    raw = (s or '').strip()
    if not raw:
        return "Sin datos"
    k = _uu(raw)
    if k in ("ENMASCARADO",):
        return "Enmascarado"
    if k in ("SIN DATOS", "SINDATOS"):
        return "Sin datos"
    if k in _DEPT_CANON:
        return _DEPT_CANON[k]
    k2 = _uu(_MOJI.sub('N', raw))
    if k2 in _DEPT_CANON:
        MOJIBAKE.add(raw)
        return _DEPT_CANON[k2]
    return raw.title()


def norm(s):
    if s is None:
        return ''
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip().lower()


# ---------------------------------------------------------------- numeros
def parse_num(s):
    """Latina o inglesa -> float. Regla del ultimo separador; agrupamiento de 3.
    Las bases 'agregada' vienen en LATINA (decimal coma, sin separador de miles);
    APRENDER trae flotantes ponderados. Se emite todo en INGLESA."""
    s = str(s).strip().replace(" ", " ").replace(" ", "")
    if s in ('', '-', 'NULL', 'null'):
        return None
    neg = s.startswith('-'); s = s.lstrip('-')
    if not re.fullmatch(r'[\d.,]+', s):
        return None
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.') if s.rfind(',') > s.rfind('.') else s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.') if s.count(',') == 1 else s.replace(',', '')
    elif s.count('.') > 1:
        s = s.replace('.', '')
    elif s.count('.') == 1 and len(s.split('.')[1]) == 3:
        s = s.replace('.', '')
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def val(r, c):
    v = parse_num(r.get(c))
    return 0.0 if v is None else v


def has(cols, c):
    return c in cols


def suma(r, cols_present, names):
    return sum(val(r, c) for c in names if c in cols_present)


# ---------------------------------------------------------------- descarga
def _open(url, timeout=300):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout, context=CTX)


def catalogo():
    raw = _open(SHEET, 90).read()
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig', errors='replace'))))
    out = []
    for r in rows:
        nombre = (r.get('nombre') or '').strip()
        url = (r.get('btn-consultar') or '').strip()
        m = re.search(r'/personal/([^/]+)/([^/?]+)', url) if url.startswith('http') else None
        if nombre and m:
            out.append({'anio': (r.get('ano') or '').strip(), 'nombre': nombre,
                        'user': m.group(1), 'token': m.group(2)})
    return out


def download(item, dest):
    if os.path.exists(dest):
        return dest
    u = ("https://ministeriodeeducaciondelanacion-my.sharepoint.com/personal/"
         f"{item['user']}/_layouts/15/download.aspx?share={item['token']}")
    with _open(u) as resp:
        if 'login.microsoftonline' in resp.geturl() or 'text/html' in (resp.headers.get('Content-Type') or ''):
            raise RuntimeError('token revocado (redirige a login): %s' % item['nombre'])
        data = resp.read()
    if data[:200].lower().lstrip().startswith(b'<html'):
        raise RuntimeError('descarga no-CSV (HTML): %s' % item['nombre'])
    tmp = dest + '.tmp'
    open(tmp, 'wb').write(data)
    os.replace(tmp, dest)
    return dest


RA_BASES = [('matricula', 'matricula - agregada'), ('matriedad', 'matricula por edad - agregada'),
            ('poblacion', 'poblacion - agregada'), ('trayectoria', 'trayectoria - agregada'),
            ('cargos', 'cargos - agregada'), ('cargosbis', 'cargos bis - agregada'),
            ('caracteristicas', 'caracteristicas - agregada')]


def fuente(anio, clave):
    """Ruta local de la base; la baja si falta. Devuelve None si la fuente no la publica."""
    fname = '%d_%s.csv' % (anio, clave)
    dest = os.path.join(FUENTES, fname)
    if os.path.exists(dest):
        return dest
    needle = dict(RA_BASES).get(clave)
    cat = _CAT[0] if _CAT else None
    if cat is None:
        _CAT.append(catalogo()); cat = _CAT[0]
    hit = [c for c in cat if c['anio'] == str(anio) and needle in norm(c['nombre'])]
    if not hit:
        NOTAS.append('%d %s: no está en el catálogo de la fuente.' % (anio, clave))
        return None
    os.makedirs(FUENTES, exist_ok=True)
    return download(hit[0], dest)


_CAT = []


ENCODINGS = []


def leer(path):
    """Las bases RA vienen en UTF-8 con BOM, pero algunas de APRENDER vienen en
    cp1252 (LA VIÑA salia como 'La Vi<?>A'). Se decodifica en estricto y se cae a
    cp1252/latin-1; nunca con errors='replace', que enmascara el problema."""
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            txt = raw.decode(enc)
            ENCODINGS.append((os.path.basename(path), enc))
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError('no se pudo decodificar %s' % path)
    rows = list(csv.DictReader(io.StringIO(txt), delimiter=';'))
    return rows, (set(rows[0].keys()) if rows else set())


def gv(r, name):
    """Lectura de columna INSENSIBLE A MAYUSCULAS: en 2024 la fuente escribe
    `Departamento` (con mayuscula) en poblacion y caracteristicas, y con acceso
    exacto todas esas filas caian en 'Sin datos'."""
    v = r.get(name)
    if v is not None:
        return v
    tgt = name.lower()
    for k in r:
        if k and k.lower() == tgt:
            return r[k]
    return None


def salta(rows, key='provincia'):
    return [r for r in rows if norm(gv(r, key)) == 'salta']


def keys3(r):
    return (norm_dept(gv(r, 'departamento')), (gv(r, 'sector') or '').strip(),
            (gv(r, 'ambito') or '').strip())


# Columnas que son CLAVE (no medidas), en cualquier capitalizacion.
CLAVES = {'provincia', 'departamento', 'sector', 'ambito', 'jurisdiccion', 'grado'}


def es_clave(c):
    return (c or '').strip().lower() in CLAVES


# ---------------------------------------------------------------- grado -> nivel
INI = ['lactantes', 'deambulantes', 's2', 's3', 's4', 's5']
PRI = [str(i) for i in range(1, 8)]
SEC = [str(i) for i in range(8, 13)] + ['1314']
NIVELES = [('inicial', INI), ('primaria', PRI), ('secundaria', SEC),
           ('snu', ['snu']), ('no_graduada', ['20'])]


def nivel_de_grado(g):
    """Etiqueta de `grado` de la base de matricula por edad -> nivel."""
    n = norm(g)
    if not n:
        return None
    if any(t in n for t in ('lactante', 'deambul', 'sala', 'jardin', 'inicial')):
        return 'inicial'
    m = re.search(r'(\d+)', n)
    if 'snu' in n or 'superior' in n:
        return 'snu'
    if m:
        d = m.group(1)
        if d == '1314':
            return 'secundaria'
        i = int(d)
        if i == 20:
            return 'no_graduada'
        if 1 <= i <= 7:
            return 'primaria'
        if 8 <= i <= 13:
            return 'secundaria'
    return None

def _c_mat(t):
    return t if t in INI else '_' + t


def _c_sec(t):
    return {'lactantes': '_seclactantes', 'deambulantes': '_secdeambu'}.get(t, '_sec' + t)


def b_matricula():
    """usuaria 2 -> matricula, varones, repitentes, sobreedad, secciones por nivel."""
    out = []
    for a in ANIOS:
        p = fuente(a, 'matricula')
        if not p:
            continue
        rows, cols = leer(p)
        for r in salta(rows):
            d, sec, amb = keys3(r)
            for nivel, toks in NIVELES:
                for met, names in (
                        ('matricula', [_c_mat(t) for t in toks]),
                        ('varones', ['v_' + t for t in toks]),
                        ('repitentes', ['r_' + t for t in toks]),
                        ('sobreedad', ['s_' + t for t in toks]),
                        ('secciones', [_c_sec(t) for t in toks])):
                    if any(c in cols for c in names):
                        out.append([a, d, sec, amb, nivel, met, round(suma(r, cols, names), 2)])
            for nivel, c in (('inicial', 'multi_ini'), ('primaria', 'multi_pri'),
                             ('secundaria', 'multi_sec'), ('multinivel', 'multinivel')):
                if c in cols:
                    out.append([a, d, sec, amb, nivel, 'secciones_multigrado', round(val(r, c), 2)])
    return (['anio', 'departamento', 'sector', 'ambito', 'nivel', 'metrica', 'valor'], out)


EDADES = ['0años', '1año'] + ['%daños' % i for i in range(2, 30)] + ['30añosymás']


def _edad_label(e):
    if e == '30añosymás':
        return '30 y más'
    return re.sub(r'años?$', '', e)


def b_matriedad():
    """usuaria 7 -> matricula por nivel x edad. Se descartan las columnas agregadas
    (Menosde18años, 6añosymás, ...) porque se solapan con las edades simples."""
    out = []
    for a in ANIOS:
        p = fuente(a, 'matriedad')
        if not p:
            continue
        rows, cols = leer(p)
        acc, sin_nivel = {}, 0
        for r in salta(rows):
            nivel = nivel_de_grado(gv(r, 'grado'))
            if nivel is None:
                sin_nivel += 1
                continue
            d, sec, amb = keys3(r)
            for e in EDADES:
                if e in cols:
                    k = (d, sec, amb, nivel, _edad_label(e))
                    acc[k] = acc.get(k, 0.0) + val(r, e)
        if sin_nivel:
            NOTAS.append('%d matricula por edad: %d filas con `grado` vacío o no mapeable '
                         '(se descartan).' % (a, sin_nivel))
        for (d, sec, amb, nivel, e), v in acc.items():
            out.append([a, d, sec, amb, nivel, e, 'matricula', round(v, 2)])
    return (['anio', 'departamento', 'sector', 'ambito', 'nivel', 'edad', 'metrica', 'valor'], out)


TRA_FAM = [('inicial', 'matricula_inicial'), ('entrados', 'entrados'),
           ('scp', 'salidos_con_pase'), ('ssp', 'salidos_sin_pase'),
           ('ultimo', 'matricula_final'), ('promovidos', 'promovidos'),
           ('promovidos_ex', 'promovidos_examen'), ('nopromo', 'no_promovidos'),
           ('regulares', 'regulares'), ('otros', 'otros')]
TRA_TOKS = [str(i) for i in range(1, 13)] + ['1314', '20']


def b_trayectoria():
    """usuaria 3 -> flujo de alumnos por nivel x sexo (no cubre nivel inicial)."""
    out = []
    for a in ANIOS:
        p = fuente(a, 'trayectoria')
        if not p:
            continue
        rows, cols = leer(p)
        for r in salta(rows):
            d, sec, amb = keys3(r)
            for nivel, toks in NIVELES:
                tk = [t for t in toks if t in TRA_TOKS]
                if not tk:
                    continue
                for fam, met in TRA_FAM:
                    for sexo, pre in (('Total', ''), ('Mujeres', 'm_')):
                        cs = ['%s%s_%s' % (pre, fam, t) for t in tk]
                        if any(c in cols for c in cs):
                            out.append([a, d, sec, amb, nivel, sexo, met,
                                        round(suma(r, cols, cs), 2)])
            for nivel in ('primaria', 'secundaria'):
                for sexo, c in (('Total', '%s_egresados' % nivel),
                                ('Mujeres', '%s_m_egresados' % nivel)):
                    if c in cols:
                        out.append([a, d, sec, amb, nivel, sexo, 'egresados', round(val(r, c), 2)])
    return (['anio', 'departamento', 'sector', 'ambito', 'nivel', 'sexo', 'metrica', 'valor'], out)


FUNC = {'dir': 'Dirección', 'fte': 'Frente a alumnos', 'apo': 'Apoyo', 'pu': 'Personal único'}
EST = {'cub': 'Cubierto', 'ncub': 'No cubierto'}
HS_FUNC = {'pro': 'Profesor', 'docente': 'Docente', 'otros': 'Otros', 'dic': 'Dictado',
           'cap': 'Capacitación', 'com': 'Comunidad', 'inv': 'Investigación', 'otr': 'Otros'}
NIV_PRE = [('ini', 'inicial'), ('pri', 'primaria'), ('sec', 'secundaria'), ('snu', 'snu')]


def b_cargos():
    """usuaria 4 -> cargos y horas por nivel x funcion x estado.
    `nopof`/`fuera` se emiten como funcion+estado 'Fuera de planta', de modo que la suma
    sobre funcion x estado da el total del nivel sin doble conteo."""
    out = []
    for a in ANIOS:
        p = fuente(a, 'cargos')
        if not p:
            continue
        rows, cols = leer(p)
        for r in salta(rows):
            d, sec, amb = keys3(r)
            for pre, nivel in NIV_PRE:
                em = lambda f, e, m, c: out.append(
                    [a, d, sec, amb, nivel, f, e, m, round(val(r, c), 2)])
                for f, fl in FUNC.items():
                    for e, el in EST.items():
                        c = '%s_%s_%s' % (pre, f, e)
                        if c in cols:
                            em(fl, el, 'cargos', c)
                if '%s_nopof' % pre in cols:
                    em('Fuera de planta', 'Fuera de planta', 'cargos', '%s_nopof' % pre)
                for e, el in EST.items():
                    c = '%s_hs_%s' % (pre, e)
                    if c in cols:
                        em('Sin desagregar', el, 'horas', c)
                if '%s_hs_nopof' % pre in cols:
                    em('Fuera de planta', 'Fuera de planta', 'horas', '%s_hs_nopof' % pre)
                for hf, hfl in HS_FUNC.items():
                    for e, el in EST.items():
                        c = '%s_hs_%s_%s' % (pre, hf, e)
                        if c in cols:
                            em(hfl, el, 'horas', c)
                if '%s_hs_fuera' % pre in cols:
                    em('Fuera de planta', 'Fuera de planta', 'horas', '%s_hs_fuera' % pre)
    return (['anio', 'departamento', 'sector', 'ambito', 'nivel', 'funcion', 'estado',
             'metrica', 'valor'], out)


def b_cargosbis():
    """usuaria 4bis -> ya viene largo: nivel x tipo x categoria x tipo de planta."""
    out, SE = [], 'Sin especificar'
    for a in ANIOS:
        p = fuente(a, 'cargosbis')
        if not p:
            continue
        rows, cols = leer(p)
        for r in salta(rows):
            d, sec, amb = keys3(r)
            v = parse_num(gv(r, 'total'))
            if v is None:
                continue
            g = lambda k: (((gv(r, k) or '').strip()) or SE)
            gg = lambda k: (SE if g(k) == 'NULL' else g(k))
            out.append([a, d, sec, amb, gg('nivel'), gg('tipo'), gg('categoria'),
                        gg('planta_tipo'), 'cargos', round(v, 2)])
    return (['anio', 'departamento', 'sector', 'ambito', 'nivel', 'tipo', 'categoria',
             'planta_tipo', 'metrica', 'valor'], out)


# --- caracteristicas del establecimiento (usuaria 5) ---------------------------
CAR_PREF = [
    ('EquipamientoEstablecimiento', 'Equipamiento del establecimiento'),
    ('EquipamientoBiblioteca', 'Equipamiento de biblioteca'),
    ('InternetTipodeservicio', 'Internet — tipo de servicio'),
    ('InternetTipodeconexión', 'Internet — tipo de conexión'),
    ('Espaciosconconexión', 'Espacios con conexión'),
    ('SistemadeGestiónEscolar', 'Sistema de gestión escolar'),
    ('Disponedesalaolaboratoriodeinformática', 'Laboratorio de informática'),
    ('LaboratorioFuncionaesespacioexclusivo', 'Laboratorio de informática'),
    ('BibliotecaDisponedealmenosuna', 'Biblioteca'),
    ('BibliotecaFuncionaesespacioexclusivo', 'Biblioteca'),
    ('SubvenciónEstatal', 'Subvención estatal'),
    ('Cooperadora', 'Cooperadora'),
    ('Electricidad', 'Electricidad'),
]


def _split_pref(c, tabla):
    for pre, lab in sorted(tabla, key=lambda x: -len(x[0])):
        if c.startswith(pre):
            return lab, (c[len(pre):] or lab)
    return None, None


def b_caracteristicas():
    """usuaria 5 -> conteo de LOCALIZACIONES por grupo/detalle de caracteristica."""
    out, sin = [], set()
    for a in ANIOS:
        p = fuente(a, 'caracteristicas')
        if not p:
            continue
        rows, cols = leer(p)
        for r in salta(rows):
            d, sec, amb = keys3(r)
            for c in cols:
                if es_clave(c):
                    continue
                if c == 'Localizacion':
                    out.append([a, d, sec, amb, 'Total', 'Localizaciones',
                                'localizaciones', round(val(r, c), 2)])
                    continue
                grupo, det = _split_pref(c, CAR_PREF)
                if grupo is None:
                    sin.add(c)
                    continue
                det = re.sub(r'^(Si)$', 'Sí', det)
                out.append([a, d, sec, amb, grupo, det, 'localizaciones', round(val(r, c), 2)])
    if sin:
        NOTAS.append('caracteristicas: %d columnas sin grupo asignado (se descartan): %s'
                     % (len(sin), ', '.join(sorted(sin))[:200]))
    return (['anio', 'departamento', 'sector', 'ambito', 'grupo', 'detalle', 'metrica',
             'valor'], out)


# --- poblacion escolar (usuaria 6) -------------------------------------------
NIV_TOK = [('Inicial', 'inicial'), ('Primaria', 'primaria'),
           ('Secundaria', 'secundaria'), ('SNU', 'snu')]
PAISES = ['Bolivia', 'Brasil', 'Chile', 'Colombia', 'Ecuador', 'Paraguay', 'Perú',
          'Uruguay', 'Venezuela', 'OtrospaísesdeAmérica', 'Europa', 'Asia',
          'África', 'Oceanía', 'Otros']
POB_PREF = [
    ('PoblaciónIndigena', 'Población indígena'),
    ('Idiomas', 'Idiomas que se enseñan'),
    ('Beneficiariosdealimentacióngrauita', 'Alimentación gratuita'),
    ('Tenenciadecomputadora', 'Tenencia de computadora'),
    ('Alumnosquenuncaasistieronasalade5años', 'Nunca asistió a sala de 5'),
    ('AlumnosconPromociónasistidaacompañada', 'Promoción asistida/acompañada'),
    ('Alumnosenjornadacompleta', 'Jornada completa'),
    ('Alumnosenjornadaextendida', 'Jornada extendida'),
    ('Turno', 'Turno'),
    ('Discapacidad', 'Discapacidad'),
]


def _pob_parse(c):
    """columna -> (grupo, detalle, nivel). El nivel viene embebido en el nombre."""
    nivel = ''
    rest = c
    for tok, lab in NIV_TOK:
        if rest.endswith(tok):
            nivel, rest = lab, rest[:-len(tok)]
            break
    else:
        for tok, lab in NIV_TOK:
            if tok in rest:
                nivel, rest = lab, rest.replace(tok, '', 1)
                break
    if rest in PAISES:
        return 'País de origen', ('Otros países de América'
                                  if rest == 'OtrospaísesdeAmérica' else rest), nivel
    grupo, det = _split_pref(rest, POB_PREF)
    if grupo is None:
        return None, None, nivel
    return grupo, det, nivel


def b_poblacion():
    """usuaria 6 -> caracteristicas de la POBLACION ESCOLAR (alumnos) por nivel."""
    out, sin = [], set()
    for a in ANIOS:
        p = fuente(a, 'poblacion')
        if not p:
            continue
        rows, cols = leer(p)
        for r in salta(rows):
            d, sec, amb = keys3(r)
            for c in cols:
                if es_clave(c):
                    continue
                if c == 'Localizacion':
                    out.append([a, d, sec, amb, '', 'Total', 'Localizaciones',
                                'localizaciones', round(val(r, c), 2)])
                    continue
                grupo, det, nivel = _pob_parse(c)
                if grupo is None:
                    sin.add(c)
                    continue
                out.append([a, d, sec, amb, nivel, grupo, det, 'alumnos', round(val(r, c), 2)])
    if sin:
        NOTAS.append('poblacion: %d columnas sin grupo asignado (se descartan): %s'
                     % (len(sin), ', '.join(sorted(sin))[:300]))
    return (['anio', 'departamento', 'sector', 'ambito', 'nivel', 'grupo', 'detalle',
             'metrica', 'valor'], out)


# --- APRENDER ----------------------------------------------------------------
DESEMP = [('Por_debajo_del_nivel_básico', 'Por debajo del nivel básico'),
          ('Básico', 'Básico'), ('Satisfactorio', 'Satisfactorio'), ('Avanzado', 'Avanzado')]
APR_NIV = {'pri6': 'Primaria 6° grado', 'sec56': 'Secundaria 5°/6° año'}


def b_aprender():
    """APRENDER censal agregada -> alumnos ponderados por nivel de desempeño.
    Valores YA ponderados por la fuente (flotantes); no se re-ponderan."""
    out = []
    cat = _CAT[0] if _CAT else None
    if cat is None:
        _CAT.append(catalogo()); cat = _CAT[0]
    for a in ANIOS:
        for area, pre, needle in (('Lengua', 'l', 'desempenos de lengua'),
                                  ('Matemática', 'm', 'desempenos de matematica')):
            hit = [c for c in cat if c['anio'] == str(a) and 'aprender' in norm(c['nombre'])
                   and 'censal' in norm(c['nombre']) and needle in norm(c['nombre'])]
            if not hit:
                continue
            nm = norm(hit[0]['nombre'])
            niv = 'pri6' if 'primaria 6' in nm else ('sec56' if 'secundaria 5-6' in nm else None)
            if niv is None:
                NOTAS.append('%d APRENDER %s: nivel evaluado no reconocido (%s).'
                             % (a, area, hit[0]['nombre'][:60]))
                continue
            dest = os.path.join(FUENTES, '%d_apr_%s_%s.csv' % (a, 'len' if pre == 'l' else 'mat', niv))
            try:
                download(hit[0], dest)
            except Exception as e:
                NOTAS.append('%d APRENDER %s: no se pudo descargar (%s).' % (a, area, e))
                continue
            rows, cols = leer(dest)
            for r in salta(rows, key='jurisdiccion'):
                d, sec, amb = keys3(r)
                for suf, lab in DESEMP:
                    c = '%sdesemp_%s' % (pre, suf)
                    if c in cols:
                        out.append([a, d, sec, amb, APR_NIV[niv], area, lab,
                                    'alumnos_ponderados', round(val(r, c), 2)])
    return (['anio', 'departamento', 'sector', 'ambito', 'nivel_evaluado', 'area',
             'nivel_desempeno', 'metrica', 'valor'], out)


# ---------------------------------------------------------------- main
SALIDAS = [
    ('Educacion_Matricula_Salta_departamento_2021-2025.csv', b_matricula),
    ('Educacion_MatriculaEdad_Salta_departamento_2021-2025.csv', b_matriedad),
    ('Educacion_Trayectoria_Salta_departamento_2021-2025.csv', b_trayectoria),
    ('Educacion_Cargos_Salta_departamento_2021-2025.csv', b_cargos),
    ('Educacion_CargosPlanta_Salta_departamento_2021-2025.csv', b_cargosbis),
    ('Educacion_Establecimientos_Salta_departamento_2021-2025.csv', b_caracteristicas),
    ('Educacion_PoblacionEscolar_Salta_departamento_2021-2025.csv', b_poblacion),
    ('Educacion_APRENDER_Salta_departamento_2021-2025.csv', b_aprender),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    print('== construyendo (fuentes en %s) ==' % FUENTES)
    for nombre, fn in SALIDAS:
        cols, rows = fn()
        rows.sort(key=lambda r: [str(x) for x in r])
        p = os.path.join(OUT, nombre)
        with open(p, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        print('  %-58s %7d filas  %d cols' % (nombre, len(rows), len(cols)))
    if MOJIBAKE:
        NOTAS.append('APRENDER 2021: la fuente trae el departamento con un caracter de '
                     'reemplazo en lugar de la N-tilde (%s); se reasigno al departamento '
                     'canonico sustituyendo la secuencia.' % ', '.join(sorted(MOJIBAKE)))
    if NOTAS:
        print('\nIncidencias (van a la metodologia):')
        for n in NOTAS:
            print('  - %s' % n)
    print('\nOK')


if __name__ == '__main__':
    main()
```
