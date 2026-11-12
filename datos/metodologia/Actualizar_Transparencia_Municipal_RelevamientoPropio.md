# Actualización — Transparencia municipal de Salta, relevamiento propio sobre canales oficiales

Índice de transparencia de los municipios de Salta relevado **por el CESS directamente en los
canales oficiales de cada municipio** (su sitio web, su boletín, el sitio de su Concejo Deliberante y
el Boletín Oficial de la Provincia). Usa 10 criterios valorados sí / parcial / no, y cada puntaje se
apoya en una URL oficial que cualquiera puede abrir.

> **Dónde está lo que no entra al build.** En `datos/` sólo viven los CSV derivados que lee
> `build.py`. La planilla fuente que se edita a mano, el script y la carpeta `fuentes/` quedaron
> en `Indicadores/datos-drive/`, fuera del repositorio del sitio: no son entrada del build y
> algunos pesan de más para versionarlos acá.

> **Primera toma: 2026-11-04, los 60 municipios.** Se relevaron primero 14 (los que tenían algún
> canal identificado) y luego los 46 restantes con el mismo protocolo.

> **Este proceso no es enteramente automático, y no puede serlo.** Los 10 criterios requieren
> juicio humano: distinguir un presupuesto sancionado de un proyecto, una adjudicación de un
> llamado, un boletín oficial de una categoría de noticias con ese nombre. El script **no
> decide**: valida la planilla que se carga a mano y calcula el índice. Las herramientas de apoyo
> proponen evidencia candidata, pero la decisión es siempre de quien releva.

Metodología, reglas de decisión y resultados:
`Metodologia_Transparencia_Municipal_RelevamientoPropio.md`.

## Qué genera (en `datos-drive/`)

**`Relevamiento_Transparencia_Municipal_Salta_planilla.csv`** — **la fuente de verdad, que se edita a
mano.** Una fila por municipio × criterio × fecha de relevamiento (11 por municipio: los 10 criterios
más una fila `(sitio)` con el canal oficial usado). Es acumulativa: cada relevamiento agrega su bloque
con otra `fecha_verificacion`.

| Columna | Contenido |
|---|---|
| `fecha_verificacion` | Fecha del relevamiento (AAAA-MM-DD). |
| `municipio` | Nombre oficial. |
| `criterio` | Uno de los 10 criterios, o `(sitio)`. |
| `valor` | `si` · `parcial` · `no` · `no_verificado`. Vacío en la fila `(sitio)`. |
| `url_evidencia` | URL oficial donde se verificó. **Obligatoria si el valor es `si` o `parcial`.** |
| `nota` | Qué se encontró o qué se buscó y no apareció. **Obligatoria en todas las filas.** |

La planilla puede estar separada por `,` o por `;` (así la guarda Excel en español): el script detecta el separador. Tiene que estar en UTF-8.

**`Transparencia_Municipal_Salta_RelevamientoPropio.csv`** — derivado de la planilla por el script;
**no se edita**. Una fila por municipio × fecha, formato ancho.

| Columna | Contenido |
|---|---|
| `fecha_verificacion`, `provincia`, `municipio` | Clave. |
| `departamento` | Del padrón oficial de la Contaduría (`Salta_recursos_municipios_mensual.csv`). |
| `sitio_oficial` | Canal oficial usado para relevar. Vacío si no se halló ninguno. |
| `transparencia` | **El índice**, 0-100: promedio de los 10 criterios (sí = 1, parcial = 0,5, no y no verificado = 0) × 100. |
| `transparencia_sobre_verificado` | El mismo cálculo solo sobre los criterios que se pudieron verificar. Vacío si no se verificó ninguno. |
| `criterios_no_verificados` | Cuántos de los 10 no se pudieron leer. **Leer siempre junto con el índice.** |
| `n_si`, `n_parcial`, `n_no` | Conteos. |
| `crit_*` (10) y `crit_*_url` (10) | Valor y evidencia de cada criterio. |

Separador `,`, decimal `.`, `utf-8-sig`.

## `no` y `no_verificado` no son lo mismo

La base separa dos situaciones que en el puntaje valen lo mismo:

- `no` = se buscó en el canal oficial y no está (o no se halló ningún canal oficial tras buscarlo).
- `no_verificado` = el canal oficial existe pero **no se pudo leer en la fecha**: sitio caído,
  certificado TLS inválido, enlace roto, documento que exige login.

En el índice ambos valen 0. Pero
`criterios_no_verificados` y `transparencia_sobre_verificado` dejan a la vista cuánto del cero es
ausencia comprobada y cuánto es falta de acceso.

## 1. Requisitos

```bash
pip install pypdfium2
```

`pypdfium2` lo usan solo las herramientas de apoyo, para leer boletines y ordenanzas en PDF. El script
principal usa solo la biblioteca estándar.

## 2. Relevar (manual, con herramientas de apoyo)

Las reglas de decisión de cada criterio están en la metodología y en
`fuentes/relevamiento_transparencia/reglas_de_decision.md`. **Leerlas antes de empezar**: deciden casos
como «el presupuesto es solo un proyecto» o «los recibos de sueldo están detrás de un login».

Protocolo por municipio, en este orden:

1. **Identificar el canal oficial** y confirmar que es el municipio correcto **por su domicilio**:
   hay homónimos en otras provincias. En la primera toma, `hipolitoyrigoyen.gob.ar` resultó ser de
   Buenos Aires y `hipolitoyrigoyen.net` de Misiones, y `concejosantarosa.gob.ar` es de La Pampa.
   Para descubrir sitios sirve una búsqueda web en el navegador; dominios adivinados no.
2. **Revisar el sitio del Concejo Deliberante** si existe: en Rosario de la Frontera, el presupuesto
   2026 estaba ahí y no en el sitio del Ejecutivo.
3. **Usar el buscador interno del sitio**, no solo el menú: en Orán, la nómina de personal no
   aparecía en la sección de Recursos Humanos y sí en la búsqueda.
4. **Abrir los boletines y las ordenanzas**, aunque el título no diga nada: en Cerrillos, el
   presupuesto 2026 era un PDF escaneado titulado solo «Ordenanza Municipal N° 659/2025».
5. **Consultar el apartado Municipios del Boletín Oficial provincial.** Las Cartas Municipales que
   aparecen allí son leyes provinciales y **no cuentan** como publicación del municipio.
6. Cargar las 11 filas en la planilla, con URL y nota.

Herramientas de apoyo, en `fuentes/relevamiento_transparencia/herramientas/`:

```bash
python boletin_provincial.py
```

Baja el apartado Municipios del Boletín Oficial de Salta para **los 60 municipios** y lista sus normas
con fecha.

```bash
python rastrear_sitios.py "San Lorenzo"
```

Recorre un sitio municipal (respeta `robots.txt`, con pausa entre pedidos) y propone enlaces candidatos
por criterio. Hay que editar el diccionario `SITIOS` para agregar municipios.

```bash
python buscar_en_pdfs.py cerrillos lista.json
```

Baja una lista de PDFs y busca presupuesto, ejecución, compras, adjudicaciones, planta, DDJJ y acceso
en su texto. Avisa cuáles están **escaneados** (sin texto): esos hay que mirarlos a ojo.

```bash
python verificar_candidatos.py candidatos.json
```

Abre la portada de cada sitio candidato (lista de pares `[municipio, url]`) y muestra título, provincias
que menciona, pie de página y enlaces relacionados con transparencia. Sirve para descartar rápido
homónimos y sitios que no son municipales. Los sitios que se cargan con JavaScript aparecen casi vacíos:
esos hay que abrirlos en el navegador. La búsqueda de candidatos (Bing) se hace en el navegador.

La planilla es el registro de esta toma; las herramientas solo ayudan a llenarla y no se necesitan para
recalcular.

## 3. Calcular

Guardar el bloque de abajo como `actualizar_transparencia_propia.py` **dentro de `datos-drive/`** y
correr:

```bash
python actualizar_transparencia_propia.py
```

Valida la planilla —criterios completos, valores permitidos, URL obligatoria en `si`/`parcial`, nota
obligatoria— y **aborta listando todos los errores** si algo no cumple. Si pasa, regenera el CSV ancho e
imprime el resumen por municipio y por criterio.

## 4. Verificar antes de dar por buena la actualización

1. **El script no debe abortar.** Si lo hace, corregir la planilla, no el script.
2. **Muestra cruzada**: que una segunda persona abra 3 URLs de evidencia al azar y confirme el valor.
   Es el único control posible sobre el juicio humano.
3. **Comparar criterio por criterio con la toma anterior**, no solo el total. Un cambio puede venir
   de que el municipio publicó algo, o de que esta vez se buscó mejor. La nota tiene que permitir
   distinguirlo.
4. **Revisar los `no_verificado`**: volver a intentar en otro día antes de cerrar. Un sitio caído un
   día puede no estarlo al siguiente.
5. **Departamento**: el script avisa si algún municipio no aparece en el padrón de la Contaduría (hay
   un diccionario `ALIAS` para nombres largos y cortos).

## Cómo hacer la próxima toma

**El cuello de botella es encontrar el canal oficial, no evaluarlo.** Para cada toma:

1. Correr `boletin_provincial.py`: es la **lista oficial de los 60** y el primer canal a revisar.
   Mirar qué normas propias (no leyes) publicó cada municipio en los últimos 12 meses y **abrirlas**:
   una puede ser el presupuesto.
2. **Volver a buscar el sitio de los municipios que hoy no tienen**: «Municipalidad de X Salta» y
   «Concejo Deliberante de X» en el navegador (Bing funciona; DuckDuckGo bloquea las consultas
   automáticas). En la primera toma 43 municipios no tenían sitio web oficial identificado: es donde más
   puede cambiar la serie.
3. **Descartar homónimos por domicilio o característica telefónica.** En la primera toma aparecieron de
   Buenos Aires, Misiones, La Pampa, Córdoba, Mendoza y San Juan.
4. **Descartar lo que no es canal de publicación**: portales turísticos (hay una plataforma, Itinere,
   que aloja los de varios municipios de los Valles), accesos con login (sistemas de gestión, recibos,
   pago de tasas), blogs y sitios de particulares, páginas por defecto del hosting.
5. **Revisar las páginas que existen aunque no estén en el menú** (en Mosconi, «Transparencia» y
   «Presupuesto anual» existen pero están vacías: son `no`).
6. Para los municipios con canal, aplicar el protocolo del paso 2. Si no hay canal, cargar los 10
   criterios como `no`, con la nota de qué se buscó.

El esfuerzo es muy desigual: un municipio sin canal se resuelve con un par de búsquedas, mientras que
uno con boletín activo exige leer decenas de PDF (en Cerrillos se revisaron 43, uno de ellos escaneado
de 20 páginas).

---

## Script completo

```python
# -*- coding: utf-8 -*-
"""
Transparencia municipal de Salta - RELEVAMIENTO PROPIO del CESS sobre canales oficiales.

Lee la planilla de relevamiento (una fila por municipio x criterio x fecha, cargada a mano
siguiendo las reglas de decision de la metodologia), la valida y calcula el indice.

    transparencia = promedio de 10 criterios (si = 1, parcial = 0,5, no = 0, no_verificado = 0) x 100

`no_verificado` (canal oficial existente pero ilegible en la fecha) puntua 0 como en la formula
original, pero se cuenta aparte y se informa el puntaje sobre lo verificado, para no confundir
"no publica" con "no se pudo leer".

La planilla es acumulativa: cada relevamiento agrega su bloque con otra `fecha_verificacion`.
El CSV de salida se regenera completo desde la planilla.
"""
import io
import os
import sys
import csv
import unicodedata

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, 'reconfigure'):
        _s.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
PLANILLA = os.path.join(HERE, 'Relevamiento_Transparencia_Municipal_Salta_planilla.csv')
PADRON = os.path.join(HERE, 'Salta_recursos_municipios_mensual.csv')     # Contaduria: municipio -> departamento
SALIDA = os.path.join(HERE, 'Transparencia_Municipal_Salta_RelevamientoPropio.csv')

CRITERIOS = ['presupuesto_vigente', 'ejecucion_presupuestaria', 'planta_personal_sueldos',
             'compras_contrataciones', 'declaraciones_juradas', 'boletin_oficial',
             'canal_acceso_informacion', 'datos_abiertos', 'publica_adjudicaciones',
             'declara_empleados']
PUNTOS = {'si': 1.0, 'parcial': 0.5, 'no': 0.0, 'no_verificado': 0.0}
# Nombres que difieren entre la planilla y el padron de la Contaduria
ALIAS = {'SAN JOSE DE LOS CERRILLOS': 'CERRILLOS', 'SAN JOSE DE METAN': 'METAN',
         'PROFESOR SALVADOR MAZZA': 'PROF. SALVADOR MAZZA'}

NOTAS = []


def uu(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s or ''))
                   if not unicodedata.combining(c)).upper().strip()


def departamentos():
    if not os.path.exists(PADRON):
        NOTAS.append('no se encontro %s: departamento queda vacio.' % os.path.basename(PADRON))
        return {}
    out = {}
    with open(PADRON, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            out.setdefault(uu(r['municipio']), r['departamento'])
    return out


def leer_planilla():
    if not os.path.exists(PLANILLA):
        raise SystemExit('ERROR: no se encontro la planilla %s' % os.path.basename(PLANILLA))
    with open(PLANILLA, encoding='utf-8-sig', newline='') as f:
        texto = f.read()
    # Excel en español guarda los CSV separados por ';': se aceptan los dos separadores.
    cab = texto.split('\n', 1)[0]
    sep = ';' if cab.count(';') > cab.count(',') else ','
    filas = list(csv.DictReader(io.StringIO(texto, newline=''), delimiter=sep))
    errores, bloques = [], {}
    for i, r in enumerate(filas, start=2):
        clave = (r['fecha_verificacion'].strip(), r['municipio'].strip())
        b = bloques.setdefault(clave, {'sitio': '', 'nota_sitio': '', 'crit': {}})
        c = r['criterio'].strip()
        if c == '(sitio)':
            b['sitio'], b['nota_sitio'] = r['url_evidencia'].strip(), r['nota'].strip()
            continue
        v = r['valor'].strip()
        if c not in CRITERIOS:
            errores.append('fila %d: criterio desconocido %r' % (i, c))
        elif v not in PUNTOS:
            errores.append('fila %d: valor invalido %r (%s, %s)' % (i, v, clave[1], c))
        elif c in b['crit']:
            errores.append('fila %d: criterio repetido %s para %s %s' % (i, c, clave[1], clave[0]))
        else:
            if v in ('si', 'parcial') and not r['url_evidencia'].strip():
                errores.append('fila %d: %s %s es %r sin URL de evidencia' % (i, clave[1], c, v))
            if not r['nota'].strip():
                errores.append('fila %d: %s %s sin nota' % (i, clave[1], c))
            b['crit'][c] = (v, r['url_evidencia'].strip())
    for (fecha, muni), b in bloques.items():
        faltan = [c for c in CRITERIOS if c not in b['crit']]
        if faltan:
            errores.append('%s %s: faltan criterios %s' % (fecha, muni, ', '.join(faltan)))
    if errores:
        raise SystemExit('ERROR en la planilla (%d):\n  ' % len(errores) + '\n  '.join(errores[:30]))
    return bloques


def main():
    bloques = leer_planilla()
    dep = departamentos()
    filas = []
    for (fecha, muni), b in sorted(bloques.items()):
        vals = [b['crit'][c][0] for c in CRITERIOS]
        pts = sum(PUNTOS[v] for v in vals)
        n_nv = vals.count('no_verificado')
        verif = 10 - n_nv
        d = dep.get(ALIAS.get(uu(muni), uu(muni)), '')
        if not d:
            NOTAS.append('%s: sin departamento en el padron de la Contaduria.' % muni)
        fila = {
            'fecha_verificacion': fecha, 'provincia': 'Salta', 'municipio': muni, 'departamento': d,
            'sitio_oficial': b['sitio'],
            'transparencia': round(pts / 10 * 100, 1),
            'transparencia_sobre_verificado': round(pts / verif * 100, 1) if verif else '',
            'criterios_no_verificados': n_nv,
            'n_si': vals.count('si'), 'n_parcial': vals.count('parcial'), 'n_no': vals.count('no'),
        }
        for c in CRITERIOS:
            fila['crit_' + c] = b['crit'][c][0]
        for c in CRITERIOS:
            fila['crit_%s_url' % c] = b['crit'][c][1]
        filas.append(fila)

    cols = (['fecha_verificacion', 'provincia', 'municipio', 'departamento', 'sitio_oficial',
             'transparencia', 'transparencia_sobre_verificado', 'criterios_no_verificados',
             'n_si', 'n_parcial', 'n_no']
            + ['crit_' + c for c in CRITERIOS] + ['crit_%s_url' % c for c in CRITERIOS])
    with open(SALIDA, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)

    print('escrito: %s' % SALIDA)
    for fecha in sorted({f['fecha_verificacion'] for f in filas}):
        sub = [f for f in filas if f['fecha_verificacion'] == fecha]
        prom = sum(f['transparencia'] for f in sub) / len(sub)
        print('\n  relevamiento %s: %d municipios | promedio %.1f | en cero %d | con criterios no verificados %d'
              % (fecha, len(sub), prom, sum(1 for f in sub if f['transparencia'] == 0),
                 sum(1 for f in sub if f['criterios_no_verificados'])))
        for f in sorted(sub, key=lambda x: -x['transparencia']):
            print('    %-28s %-26s %5.1f  (si %d, parcial %d, no %d, no verif. %d)'
                  % (f['municipio'], f['departamento'], f['transparencia'], f['n_si'],
                     f['n_parcial'], f['n_no'], f['criterios_no_verificados']))
        print('\n    %-28s %4s %8s %4s %8s' % ('criterio', 'si', 'parcial', 'no', 'no verif'))
        for c in CRITERIOS:
            v = [f['crit_' + c] for f in sub]
            print('    %-28s %4d %8d %4d %8d' % (c, v.count('si'), v.count('parcial'), v.count('no'),
                                               v.count('no_verificado')))
    print('\nIncidencias:')
    for n in NOTAS or ['ninguna.']:
        print('  -', n)


if __name__ == '__main__':
    main()
```
