# Actualización — Transparencia del Gobierno provincial de Salta, relevamiento propio sobre canales oficiales

Índice de transparencia del **Poder Ejecutivo de la Provincia de Salta**. El CESS lo releva
directamente en los canales oficiales del Gobierno provincial, con **los mismos 10 criterios, los
mismos valores y la misma fórmula** que el relevamiento propio de los 60 municipios
(`Actualizar_Transparencia_Municipal_RelevamientoPropio.md`). Así, el puntaje de la provincia y el de
sus municipios se leen en la misma escala.

> **Dónde está lo que no entra al build.** En `datos/` sólo viven los CSV derivados que lee
> `build.py`. La planilla fuente que se edita a mano, el script y la carpeta `fuentes/` quedaron
> en `Indicadores/datos-drive/`, fuera del repositorio del sitio: no son entrada del build y
> algunos pesan de más para versionarlos acá.

> **Primera toma: 2026-11-07, sólo Salta.** El diseño admite sumar otras provincias, por ejemplo las
> del NOA, como comparación: basta agregarlas a la lista `PROVINCIAS` del script y cargar sus filas.

> **El proceso no es automático.** Los criterios exigen juicio humano, por ejemplo para distinguir
> una ley sancionada de un proyecto, o una adjudicación de un llamado. El script **no decide**: valida
> la planilla, que se carga a mano, y calcula el índice.

La metodología, las reglas, el resultado y la comparación con los municipios están en
`Metodologia_Transparencia_Provincial_RelevamientoPropio.md`. Las reglas de decisión, en tabla,
están en `fuentes/relevamiento_transparencia/reglas_de_decision_provincial.md`.

## Qué genera (en `datos-drive/`)

**`Relevamiento_Transparencia_Provincial_planilla.csv`** es **la fuente de verdad y se edita a mano**.
- Tiene una fila por provincia × criterio × fecha de relevamiento.
- Cada toma suma 11 filas: los 10 criterios más una fila `(sitio)`, que lista los canales usados y los que no se pudieron leer.
- Es acumulativa: cada toma agrega su bloque.
- Columnas: `fecha_verificacion, provincia, criterio, valor, url_evidencia, nota`.
- La URL es obligatoria si el valor es `si` o `parcial`.
- La nota es obligatoria en todas las filas.
- Puede estar separada por `,` o por `;` (así la guarda Excel en español): el script detecta el separador. Tiene que estar en UTF-8.

**`Transparencia_Provincial_RelevamientoPropio.csv`** se deriva de la planilla con el script y
**no se edita**. Tiene una fila por provincia × fecha, en formato ancho.

| Columna | Contenido |
|---|---|
| `fecha_verificacion`, `provincia` | Clave. |
| `poder` | `Ejecutivo`. La Legislatura y la Justicia no se relevan. |
| `sitio_oficial` | Portal principal del Gobierno. |
| `transparencia` | **El índice**, de 0 a 100: el promedio de los 10 criterios (sí = 1, parcial = 0,5, no y no verificado = 0) × 100. |
| `transparencia_sobre_verificado` | El mismo cálculo, sólo sobre los criterios que se pudieron verificar. |
| `criterios_no_verificados` | Cuántos criterios no se pudieron leer. |
| `n_si`, `n_parcial`, `n_no` | Conteos. |
| `crit_*` (10) y `crit_*_url` (10) | Valor y evidencia de cada criterio. |

Las columnas son las del archivo municipal, sin `municipio` ni `departamento` y con `poder`
agregada, de modo que los dos se pueden apilar en un mismo gráfico. El archivo usa separador `,`,
decimal `.` y codificación `utf-8-sig`.

## 1. Requisitos

```bash
pip install pypdfium2
```

Sólo lo usa la herramienta de apoyo para leer PDF. El script principal usa únicamente la biblioteca
estándar.

## 2. Relevar (manual)

Leer antes las reglas de decisión. **Canales del Ejecutivo a recorrer**, todos verificados en la
primera toma:

| Canal | Qué hay | Criterio |
|---|---|---|
| `presupuesto.salta.gob.ar` → Presupuestos Aprobados | Ley de presupuesto (PDF escaneado), planillas anexas, decreto de distribución, mensaje | Presupuesto; planta de cargos (artículo «Fíjase la planta de personal») |
| `presupuesto.salta.gob.ar` → Ejecución | Esquema Ahorro-Inversión mensual y ejecución por rubro, objeto y finalidad (PDF) | Ejecución |
| `economiasalta.gob.ar/contaduria/cuenta-general/` | Cuenta General del Ejercicio (mayormente escaneada) | Ejecución; buscar la dotación ocupada |
| `saltacompra.gob.ar` → «Procesos de los últimos 30 días» | Llamados con pliego | Compras |
| `boletinoficialsalta.gob.ar` → Avisos | Actos de adjudicación (buscar «adjudicacion» con fechas) y la edición diaria | Adjudicaciones; boletín |
| `escribaniadegobierno.salta.gob.ar` → DD JJ | Depositaria de las DDJJ | Declaraciones juradas |
| `idesa.salta.gob.ar/geoservicios/` | WFS de `geoportal.salta.gob.ar`: **probar la descarga** en GeoJSON o CSV | Datos abiertos |
| `www.salta.gob.ar` (pie de página) | Escala salarial, nómina de autoridades, enlaces a organismos | Planta y sueldos |
| `empleadopublico.salta.gob.ar`, `estadisticas.salta.gov.ar` | **Certificado TLS vencido el 2026-11-07.** Volver a intentar: pueden tener escalas y dotación | Planta; empleados; datos |
| `atencionciudadana.salta.gob.ar` | Guía de trámites: buscar un procedimiento de acceso a la información | Acceso |

Pasos:

1. Para cada criterio, **abrir el documento**, no sólo el menú. La Ley 8518 era un PDF escaneado: el
   presupuesto y la planta de cargos se leyeron en la imagen.
2. **No forzar sitios con certificado inválido.** Lo que esté sólo allí no se puede verificar; si
   el criterio no se puede decidir con otra evidencia, va `no_verificado`.
3. Cargar las 11 filas con URL y nota. La nota tiene que permitir, en la toma siguiente, distinguir
   si el Gobierno publicó algo nuevo o si esta vez se buscó mejor.

Herramienta de apoyo: `fuentes/relevamiento_transparencia/herramientas/buscar_en_pdfs.py`, para buscar
texto en los PDF y detectar los escaneados.

## 3. Calcular

Guardar el bloque de abajo como `actualizar_transparencia_provincial.py` **dentro de `datos-drive/`**
y correr:

```bash
python actualizar_transparencia_provincial.py
```

El script valida la planilla y **aborta, listando todos los errores**, ante cualquiera de estos casos:
- un criterio que falta, desconocido o repetido;
- un valor inválido;
- un `si` o `parcial` sin URL;
- una nota vacía;
- una provincia fuera de `PROVINCIAS`, o una de la lista que falta en una toma.

Si la planilla pasa, regenera el CSV ancho e imprime el resultado.

## 4. Verificar antes de dar por buena la actualización

1. **El script no debe abortar.** Si aborta, se corrige la planilla, no el script.
2. **Segunda pasada:** volver a abrir todas las URL que respaldan un `si` o un `parcial` y confirmar
   el valor. Lo ideal es que la haga otra persona.
3. **Comparar con la toma anterior criterio por criterio**, no sólo el total.
4. **Volver a intentar los sitios con certificado vencido** antes de cerrar la toma.
5. **Comparar con los municipios:** el resultado se lee junto al promedio municipal de la misma
   fecha (ver la metodología).

---

## Script completo

```python
# -*- coding: utf-8 -*-
"""
Transparencia del Gobierno provincial (Poder Ejecutivo) - RELEVAMIENTO PROPIO del CESS sobre
canales oficiales. Mismos 10 criterios y misma formula que el relevamiento municipal, para que
ambos indices sean comparables.

Lee la planilla de relevamiento (una fila por provincia x criterio x fecha, cargada a mano
siguiendo las reglas de decision de la metodologia), la valida y calcula el indice.

    transparencia = promedio de 10 criterios (si = 1, parcial = 0,5, no = 0, no_verificado = 0) x 100

`no_verificado` (canal oficial existente pero ilegible en la fecha) puntua 0, pero se cuenta
aparte y se informa el puntaje sobre lo verificado.

La planilla es acumulativa: cada relevamiento agrega su bloque con otra `fecha_verificacion`.
Para sumar provincias basta agregarlas a PROVINCIAS y cargar sus filas.
"""
import io
import os
import sys
import csv

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, 'reconfigure'):
        _s.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
PLANILLA = os.path.join(HERE, 'Relevamiento_Transparencia_Provincial_planilla.csv')
SALIDA = os.path.join(HERE, 'Transparencia_Provincial_RelevamientoPropio.csv')

PROVINCIAS = ['Salta']          # provincias que debe traer cada relevamiento
PODER = 'Ejecutivo'
CRITERIOS = ['presupuesto_vigente', 'ejecucion_presupuestaria', 'planta_personal_sueldos',
             'compras_contrataciones', 'declaraciones_juradas', 'boletin_oficial',
             'canal_acceso_informacion', 'datos_abiertos', 'publica_adjudicaciones',
             'declara_empleados']
PUNTOS = {'si': 1.0, 'parcial': 0.5, 'no': 0.0, 'no_verificado': 0.0}


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
        clave = (r['fecha_verificacion'].strip(), r['provincia'].strip())
        if clave[1] not in PROVINCIAS:
            errores.append('fila %d: provincia %r no figura en PROVINCIAS' % (i, clave[1]))
            continue
        b = bloques.setdefault(clave, {'sitio': '', 'crit': {}})
        c = r['criterio'].strip()
        if c == '(sitio)':
            b['sitio'] = r['url_evidencia'].strip()
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
    for (fecha, prov), b in bloques.items():
        faltan = [c for c in CRITERIOS if c not in b['crit']]
        if faltan:
            errores.append('%s %s: faltan criterios %s' % (fecha, prov, ', '.join(faltan)))
    for fecha in sorted({k[0] for k in bloques}):
        ausentes = [p for p in PROVINCIAS if (fecha, p) not in bloques]
        if ausentes:
            errores.append('%s: faltan provincias %s' % (fecha, ', '.join(ausentes)))
    if errores:
        raise SystemExit('ERROR en la planilla (%d):\n  ' % len(errores) + '\n  '.join(errores[:30]))
    return bloques


def main():
    bloques = leer_planilla()
    filas = []
    for (fecha, prov), b in sorted(bloques.items()):
        vals = [b['crit'][c][0] for c in CRITERIOS]
        pts = sum(PUNTOS[v] for v in vals)
        n_nv = vals.count('no_verificado')
        verif = 10 - n_nv
        fila = {
            'fecha_verificacion': fecha, 'provincia': prov, 'poder': PODER, 'sitio_oficial': b['sitio'],
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

    cols = (['fecha_verificacion', 'provincia', 'poder', 'sitio_oficial',
             'transparencia', 'transparencia_sobre_verificado', 'criterios_no_verificados',
             'n_si', 'n_parcial', 'n_no']
            + ['crit_' + c for c in CRITERIOS] + ['crit_%s_url' % c for c in CRITERIOS])
    with open(SALIDA, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)

    print('escrito: %s' % SALIDA)
    for f in filas:
        print('\n  %s | %s (%s) | transparencia %.1f | sobre verificado %s | si %d, parcial %d, no %d, no verif. %d'
              % (f['fecha_verificacion'], f['provincia'], f['poder'], f['transparencia'],
                 f['transparencia_sobre_verificado'], f['n_si'], f['n_parcial'], f['n_no'],
                 f['criterios_no_verificados']))
        for c in CRITERIOS:
            print('    %-28s %s' % (c, f['crit_' + c]))


if __name__ == '__main__':
    main()
```
