# Actualización — Padrón de empresas exportadoras de Salta (ArgentinaTradeNet)

Relevamiento del **Directorio de Exportadores** de ArgentinaTradeNet (Cancillería) quedándose con
las empresas de **Salta**, para poder contarlas y seguir su evolución tomando el registro cada 6 o
12 meses.

> Cuatro cosas que hay que saber antes de usar esto:
> 1. **La provincia sólo existe en la ficha, no en el listado.** No hay filtro por provincia en
>    ninguna parte del sitio. Por eso hay que abrir las **2.663** fichas del padrón nacional y
>    filtrar después. La corrida completa tarda unos 5 minutos.
> 2. **El directorio es de inscripción voluntaria.** Mide empresas *registradas* como exportadoras,
>    no empresas que efectivamente exportaron. No es un censo y su variación puede reflejar altas y
>    bajas administrativas antes que actividad real.
> 3. **El 17 % de las fichas del país no declara provincia.** El conteo de Salta es un **piso**,
>    no un valor exacto. Se recuperan las que se puede por ciudad/localidad.
> 4. **La fuente no tiene fecha.** Ni el directorio ni las fichas informan cuándo se actualizaron.
>    La única fecha del dataset es la del relevamiento, que pone este script.

Metodología y verificaciones: `Metodologia_Exportadores_Salta_ArgentinaTradeNet.md`.

## Qué genera (en `datos-drive/`)

**`Exportadores_Salta_ArgentinaTradeNet.csv`** — una fila por empresa y por relevamiento, en formato
ancho. Es **acumulativo**: cada corrida agrega su toma y conserva las anteriores.

| Columna | Contenido |
|---|---|
| `fecha_registro` | Fecha del relevamiento (AAAA-MM-DD). Junto con `empresa` forma la clave. |
| `empresa` | **Razón social** — el dato autoritativo y el que se cuenta. |
| `nombre_fantasia` | El nombre que muestra el encabezado de la ficha (ver incidencia 3). |
| `codigo_tradenet` | Identificador del registro (p. ej. `EXPCANCI7582`). |
| `provincia` | Siempre `Salta`. |
| `ciudad`, `localidad` | Tal como los carga la empresa; con frecuencia vacíos o iguales entre sí. |
| `departamento` | **Derivado** por cruce con el padrón de municipios; `Sin asignar` si no matchea. |
| `organicos` | `Sí` / `No`, según la ficha. |
| `certificaciones` | Lista declarada más las "otras certificaciones", separadas por `;`. |
| `n_posiciones` | Cantidad de posiciones arancelarias declaradas. |
| `Posición 1` … `Posición N` | Una columna por posición. **Son texto**, no números. |
| `criterio_salta` | `provincia` (la ficha lo declara) o `imputada` (se dedujo de ciudad/localidad). |
| `url_ficha` | Enlace a la ficha, para auditar cualquier fila contra la fuente. |

Separador `,`, codificación `utf-8-sig`.

> **Los códigos arancelarios son texto, no números.** Tienen ceros a la izquierda (`07102200`) y
> relleno con guiones (`07----`, `1005--`). Si se abre el CSV en Excel sin declarar la columna como
> texto, Excel destruye los ceros iniciales. Para analizar, leer con
> `pd.read_csv(..., dtype=str)`.

## 1. Requisitos

```bash
pip install pandas
```

El script usa sólo la biblioteca estándar para descargar (`urllib`); `pandas` se usa únicamente si
se quiere analizar la salida.

## 2. Correr el script

```bash
python actualizar_exportadores_salta.py
```

La primera corrida baja las 2.663 fichas a `datos-drive/fuentes/tradenet/` (~20 MB) y tarda unos
5 minutos. Las siguientes reutilizan la caché. **Para tomar un registro nuevo hay que vaciar esa
carpeta**, porque si no se re-lee la foto anterior:

```bash
rm -rf fuentes/tradenet
```

Variables de entorno opcionales: `EXPO_OUT` (carpeta de salida), `EXPO_FUENTES` (caché) y
`EXPO_FECHA` (fecha del relevamiento, por defecto hoy).

## 3. Cómo llega a los datos

La página de la Cancillería es sólo una cáscara: el directorio real vive en **dos iframes** contra
`exportaciones.cancilleria.gob.ar`, una aplicación CakePHP. El sitio expone dos interfaces sobre los
mismos datos y **la pública está mutilada**:

| | pública (la que se ve embebida) | la que usa este script |
|---|---|---|
| listado | `POST /sitios/exportadores_resultados` — tope de 100 filas, sin paginado | `POST /sitios/tabla_directorios_exportadores/1` — JSON paginado y completo |
| ficha | `/sitios/ficha_directorio_mobile/{id}` — **sin domicilio, certificaciones ni orgánicos** | `/sitios/ficha_directorio/{id}` — todos los campos |

De ahí que el script use la segunda. El listado devuelve un JSON con `total` (280 páginas),
`pageNo` y `result`, que es un fragmento de HTML del que se extraen los `ficha_directorio/{id}`.
El listado **no** trae provincia, domicilio, certificaciones ni orgánicos: sólo razón social,
sector, subsector y los códigos pelados. Por eso la segunda etapa es inevitable.

No requiere usuario ni sesión, pese a que la página promociona "Inicie sesión". No hay CAPTCHA ni
WAF. El script igual va con 4 hilos y una pausa entre pedidos: es un servidor público.

## 4. Verificar antes de dar por buena la actualización

1. **Conteo**: el script imprime cuántas empresas de Salta encontró y con qué criterio. Un salto
   brusco respecto de la toma anterior hay que mirarlo antes de publicarlo.
2. **Errores de descarga**: tiene que decir `errores 0`. Si no, volver a correr (la caché hace que
   sólo reintente lo que falta).
3. **Incidencias**: las imprime al final; hay que volcarlas a la metodología.
4. **Muestra**: abrir dos o tres `url_ficha` del CSV y comparar campo por campo.
5. **Acumulación**: correr dos veces el mismo día no debe duplicar filas; una fecha nueva debe
   sumar un bloque conservando el anterior.

**Actualizar cada 6 o 12 meses:** vaciar `fuentes/tradenet/` y correr. El CSV suma la toma nueva con
su `fecha_registro` y conserva las anteriores, de modo que el conteo por fecha es la serie.

---

## Script completo

```python
# -*- coding: utf-8 -*-
"""Padron de empresas exportadoras de Salta — ArgentinaTradeNet (Cancilleria).

Genera Exportadores_Salta_ArgentinaTradeNet.csv (acumulativo por fecha de relevamiento).

Dos etapas: (1) se recorren las paginas del listado para juntar los IDs de ficha;
(2) se baja cada ficha y se parsean los campos. La provincia SOLO existe en la ficha,
por eso hay que abrirlas todas y filtrar despues.
"""
import os, re, sys, ssl, time, json, html, csv, unicodedata, datetime
import urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('EXPO_OUT', HERE)
FUENTES = os.environ.get('EXPO_FUENTES', os.path.join(HERE, 'fuentes', 'tradenet'))
BASE = 'https://exportaciones.cancilleria.gob.ar'
LISTADO = BASE + '/sitios/tabla_directorios_exportadores/1'
FICHA = BASE + '/sitios/ficha_directorio/%s'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; CESS-Salta-Monitor/1.0; investigacion estadistica)',
      'Accept-Encoding': 'gzip'}
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
HILOS = 4            # cortesia: servidor publico
PAUSA = 0.15
NOTAS = []


def _get(url, data=None, intentos=4):
    """GET/POST con reintento y espera creciente. Devuelve texto UTF-8."""
    import gzip
    body = urllib.parse.urlencode(data).encode() if data else None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, data=body, headers=UA)
            with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
                raw = r.read()
                if r.headers.get('Content-Encoding') == 'gzip':
                    raw = gzip.decompress(raw)
                return raw.decode('utf-8', 'replace')
        except Exception as e:
            if i == intentos - 1:
                raise
            time.sleep(2 ** i)
    raise RuntimeError('inalcanzable: ' + url)


# ---------------------------------------------------------------- etapa 1: IDs
def harvest_ids():
    cache = os.path.join(FUENTES, '_ids.json')
    if os.path.exists(cache):
        return json.load(open(cache, encoding='utf-8'))
    first = json.loads(_get(LISTADO, {'pageNo': 1}))
    total = int(first['total'])
    print('  paginas de listado: %d' % total)
    ids, orden = set(), []

    def page(n):
        j = json.loads(_get(LISTADO, {'pageNo': n}))
        return re.findall(r'ficha_directorio/(\d+)', j.get('result', ''))

    with ThreadPoolExecutor(HILOS) as ex:
        for n, res in enumerate(ex.map(page, range(1, total + 1)), start=1):
            for i in res:
                if i not in ids:
                    ids.add(i); orden.append(i)
            if n % 50 == 0:
                print('    pagina %d/%d — %d ids' % (n, total, len(orden)))
    os.makedirs(FUENTES, exist_ok=True)
    json.dump(orden, open(cache, 'w', encoding='utf-8'))
    return orden


# ---------------------------------------------------------------- etapa 2: fichas
def bajar_ficha(fid):
    """Descarga con cache; atomica (.tmp -> replace) para poder cortar y retomar."""
    p = os.path.join(FUENTES, '%s.html' % fid)
    if os.path.exists(p):
        return open(p, encoding='utf-8').read()
    t = _get(FICHA % fid)
    tmp = p + '.tmp'
    open(tmp, 'w', encoding='utf-8').write(t)
    os.replace(tmp, p)
    time.sleep(PAUSA)
    return t


def _limpiar(s):
    s = re.sub(r'<br\s*/?>', '\n', s or '')
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    return re.sub(r'[ \t\xa0]+', ' ', s).strip()


def campo(txt, etiqueta):
    """Valor de <p><b>ETIQUETA:</b> valor</p>."""
    m = re.search(r'<b>\s*' + re.escape(etiqueta) + r'\s*:?\s*</b>(.*?)</p>', txt, re.S | re.I)
    return _limpiar(m.group(1)) if m else ''


def certificaciones(txt):
    """Lista controlada: <p>s hermanos tras la etiqueta, hasta el </select> huerfano
    que deja el template. Se suma 'Otras Certificaciones' (texto libre)."""
    out = []
    m = re.search(r'<b>\s*Certificaciones\s*:?\s*</b>(.*?)(?:</select>|<b>\s*Otras Certificaciones)',
                  txt, re.S | re.I)
    if m:
        bloque = m.group(1)
        for p in re.findall(r'<p[^>]*>(.*?)</p>', bloque, re.S):
            v = _limpiar(p)
            if v and v.lower() not in ('no informado',):
                out.append(v)
        if not out:
            v = _limpiar(bloque)
            if v:
                out.append(v)
    otras = campo(txt, 'Otras Certificaciones')
    for v in (otras.split('\n') if otras else []):
        v = v.strip()
        if v and v not in out:
            out.append(v)
    return '; '.join(dict.fromkeys([o for o in out if o]))


def posiciones(txt):
    """'NCM - descripcion' por linea. Se conserva el codigo COMO TEXTO: tiene ceros a la
    izquierda ('07102200') y relleno con guiones ('07----', '1005--')."""
    bruto = campo(txt, 'Posiciones Arancelarias')
    out = []
    for ln in bruto.split('\n'):
        ln = ln.strip()
        if not ln:
            continue
        m = re.match(r'^([0-9][0-9\-]{1,9})\s*-\s*(.*)$', ln)
        cod = m.group(1).strip() if m else ln.split(' ')[0].strip()
        if cod and cod not in out:
            out.append(cod)
    return out


def parse_ficha(fid, txt):
    nombre_h2 = ''
    m = re.search(r'<h2[^>]*>(.*?)</h2>', txt, re.S)
    if m:
        nombre_h2 = _limpiar(m.group(1))
    return {
        'id': fid,
        'codigo_tradenet': campo(txt, 'Código Tradenet'),
        'nombre': nombre_h2 or campo(txt, 'Razón Social'),
        'razon_social': campo(txt, 'Razón Social'),
        'provincia': campo(txt, 'Provincia'),
        'ciudad': campo(txt, 'Ciudad'),
        'localidad': campo(txt, 'Localidad'),
        'organicos': campo(txt, '¿Exporta productos orgánicos?'),
        'certificaciones': certificaciones(txt),
        'sectores': campo(txt, 'Sectores'),
        'subsectores': campo(txt, 'Subsectores'),
        'posiciones': posiciones(txt),
        'url_ficha': FICHA % fid,
    }


# ---------------------------------------------------------------- normalizacion
def uu(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s or ''))
                   if not unicodedata.combining(c)).upper().strip()


def es_salta(r):
    """Provincia == Salta; si viene vacia, se recupera por ciudad/localidad."""
    if uu(r['provincia']) == 'SALTA':
        return True, 'provincia'
    if r['provincia'].strip() == '':
        for c in (r['ciudad'], r['localidad']):
            if 'SALTA' in uu(c) or 'SLATA' in uu(c):   # typo real en la fuente
                return True, 'imputada'
    return False, ''


def relevar():
    os.makedirs(FUENTES, exist_ok=True)
    print('== etapa 1: listado ==')
    ids = harvest_ids()
    print('  ids unicos: %d' % len(ids))

    print('== etapa 2: fichas ==')
    regs, err = [], 0
    def uno(fid):
        try:
            return parse_ficha(fid, bajar_ficha(fid))
        except Exception as e:
            return {'id': fid, 'error': str(e)}
    with ThreadPoolExecutor(HILOS) as ex:
        for n, r in enumerate(ex.map(uno, ids), start=1):
            if 'error' in r:
                err += 1
            else:
                regs.append(r)
            if n % 400 == 0:
                print('    ficha %d/%d' % (n, len(ids)))
    if err:
        NOTAS.append('%d fichas no se pudieron descargar o parsear.' % err)
    print('  fichas parseadas: %d (errores %d)' % (len(regs), err))

    vacias = sum(1 for r in regs if not r['provincia'].strip())
    NOTAS.append('%d de %d fichas (%.1f%%) no declaran provincia; se intento recuperarlas '
                 'por ciudad/localidad.' % (vacias, len(regs), 100.0 * vacias / max(len(regs), 1)))

    salta = []
    for r in regs:
        ok, via = es_salta(r)
        if ok:
            r['criterio_salta'] = via
            salta.append(r)
    imput = sum(1 for r in salta if r['criterio_salta'] == 'imputada')
    print('  SALTA: %d (%d por provincia declarada, %d imputadas)'
          % (len(salta), len(salta) - imput, imput))
    if imput:
        NOTAS.append('%d empresas se asignaron a Salta por ciudad/localidad porque la ficha '
                     'no declara provincia.' % imput)

    return salta


# ======================= construccion del CSV =======================
PADRON_MUNI = r'G:\Documents\CESS\Indicadores\datos-drive\Salta_recursos_municipios_mensual.csv'
SALIDA = 'Exportadores_Salta_ArgentinaTradeNet.csv'


# --- crosswalk localidad/municipio -> departamento -------------------------
# Base: padron de municipios de la Contaduria (60 municipios -> los 23 departamentos).
# Alias: variantes y erratas observadas en las fichas del directorio.
ALIAS = {
    'SALTA CAPITAL': 'Capital', 'SLATA CAPITAL': 'Capital', 'CIUDAD DE SALTA': 'Capital',
    'SALTA': 'Capital',                      # "Ciudad de Salta" en el uso corriente
    'ROSARIO DE LAFRONTERA': 'Rosario de la Frontera',
    'GRAL GUEMES': 'General Güemes', 'GENERAL GUEMES': 'General Güemes',
    'SAN RAMON DE LA NUEVA ORAN': 'Orán', 'ORAN': 'Orán',
    'TARTAGAL': 'General José de San Martín', 'GENERAL MOSCONI': 'General José de San Martín',
    'EMBARCACION': 'General José de San Martín', 'AGUARAY': 'General José de San Martín',
    'SALVADOR MAZZA': 'General José de San Martín',
    'JOAQUIN V. GONZALEZ': 'Anta', 'JOAQUIN V GONZALEZ': 'Anta', 'LAS LAJITAS': 'Anta',
    'COLONIA SANTA ROSA': 'Orán', 'PICHANAL': 'Orán', 'HIPOLITO YRIGOYEN': 'Orán',
    'CAMPO QUIJANO': 'Rosario de Lerma', 'EL CARRIL': 'Chicoana',
    'SAN ANTONIO DE LOS COBRES': 'Los Andes', 'CORONEL MOLDES': 'La Viña',
}


def crosswalk():
    """{NOMBRE_NORMALIZADO: Departamento canonico}."""
    cw = {}
    try:
        with open(PADRON_MUNI, encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                m, d = (r.get('municipio') or '').strip(), (r.get('departamento') or '').strip()
                if m and d:
                    cw.setdefault(uu(m), d)
                    cw.setdefault(uu(d), d)          # el nombre del depto tambien matchea
    except FileNotFoundError:
        NOTAS.append('no se encontro el padron de municipios (%s); el departamento queda sin '
                     'asignar en todas las filas.' % os.path.basename(PADRON_MUNI))
    cw.update({uu(k): v for k, v in ALIAS.items()})
    return cw


def departamento(r, cw):
    """Se prueba localidad y despues ciudad. Sin match -> 'Sin asignar' (NO se inventa)."""
    for campo in ('localidad', 'ciudad'):
        v = uu(r.get(campo))
        if not v:
            continue
        if v in cw:
            return cw[v]
        for k, d in cw.items():                      # contencion: "SALTA CAPITAL, SALTA"
            if len(k) > 4 and k in v:
                return d
    return 'Sin asignar'


def construir(regs):
    hoy = os.environ.get('EXPO_FECHA', datetime.date.today().isoformat())
    cw = crosswalk()

    # dedupe: la fuente tiene la misma empresa con dos IDs (p. ej. MINERA SANTA RITA SRL)
    vistos, filas = {}, []
    for r in sorted(regs, key=lambda x: uu(x['nombre'])):
        clave = uu(r['razon_social'] or r['nombre'])
        if clave in vistos:
            vistos[clave].append(r['id'])
            continue
        vistos[clave] = [r['id']]
        filas.append(r)
    dups = {k: v for k, v in vistos.items() if len(v) > 1}
    if dups:
        NOTAS.append('%d empresa(s) figuran con mas de un ID en la fuente y se unificaron por '
                     'razon social: %s.' % (len(dups), '; '.join('%s (ids %s)' % (k, ', '.join(v))
                                                                 for k, v in dups.items())))

    sin_dep = 0
    for r in filas:
        r['departamento'] = departamento(r, cw)
        if r['departamento'] == 'Sin asignar':
            sin_dep += 1
    NOTAS.append('%d de %d empresas quedaron sin departamento asignado (la ficha no declara '
                 'ciudad ni localidad).' % (sin_dep, len(filas)))

    # El <h2> de la ficha es un nombre de fantasia que el propio inscripto carga libre: a veces
    # es una abreviatura, a veces el nombre de una persona y a veces otra empresa. La razon
    # social es el dato autoritativo y es la que se cuenta.
    import re as _re
    _n = lambda s: _re.sub(r'[^A-Z0-9]', '', uu(s))
    difnom = sum(1 for r in filas if r['razon_social'] and _n(r['nombre']) != _n(r['razon_social']))
    if difnom:
        NOTAS.append('%d de %d fichas traen un nombre de fantasia distinto de la razon social; '
                     'se conservan ambos y el conteo se hace por razon social.'
                     % (difnom, len(filas)))

    maxpos = max((len(r['posiciones']) for r in filas), default=0)
    cols = (['fecha_registro', 'empresa', 'nombre_fantasia', 'codigo_tradenet', 'provincia',
             'ciudad', 'localidad', 'departamento', 'organicos', 'certificaciones',
             'n_posiciones'] + ['Posición %d' % i for i in range(1, maxpos + 1)]
            + ['criterio_salta', 'url_ficha'])

    nuevas = []
    for r in filas:
        fila = {
            'fecha_registro': hoy,
            'empresa': r['razon_social'] or r['nombre'],      # razon social = dato autoritativo
            'nombre_fantasia': r['nombre'],
            'codigo_tradenet': r['codigo_tradenet'], 'provincia': 'Salta',
            'ciudad': r['ciudad'], 'localidad': r['localidad'],
            'departamento': r['departamento'], 'organicos': r['organicos'] or 'No informado',
            'certificaciones': r['certificaciones'], 'n_posiciones': len(r['posiciones']),
            'criterio_salta': r.get('criterio_salta', 'provincia'), 'url_ficha': r['url_ficha'],
        }
        for i, p in enumerate(r['posiciones'], start=1):
            fila['Posición %d' % i] = p
        nuevas.append(fila)

    # --- acumulacion: se conservan las tomas anteriores; re-correr hoy no duplica ---
    destino = os.path.join(OUT, SALIDA)
    previas = []
    if os.path.exists(destino):
        with open(destino, encoding='utf-8-sig', newline='') as f:
            previas = [x for x in csv.DictReader(f) if x.get('fecha_registro') != hoy]
        antes = set(c for x in previas for c in x)
        cols = list(dict.fromkeys(
            [c for c in cols if not c.startswith('Posición ')]
            + sorted([c for c in (antes | set().union(*[set(n) for n in nuevas]))
                      if c.startswith('Posición ')], key=lambda c: int(c.split()[1]))))
        cols = ([c for c in cols if c not in ('criterio_salta', 'url_ficha')]
                + ['criterio_salta', 'url_ficha'])
        NOTAS.append('archivo acumulativo: se conservaron %d filas de tomas anteriores.' % len(previas))

    with open(destino, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for x in previas + nuevas:
            w.writerow(x)

    print('escrito: %s' % destino)
    print('  empresas en esta toma (%s): %d | columnas: %d | max posiciones: %d'
          % (hoy, len(nuevas), len(cols), maxpos))
    print('  por departamento:')
    from collections import Counter
    for d, n in Counter(x['departamento'] for x in nuevas).most_common():
        print('    %-28s %d' % (d, n))
    print('\nIncidencias:')
    for n in NOTAS:
        print('  -', n)


def main():
    construir(relevar())


if __name__ == '__main__':
    main()
```
