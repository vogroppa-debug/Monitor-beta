# Actualización — Concentración de las exportaciones de Salta (índice HHI)

Calcula el **índice de Herfindahl-Hirschman normalizado** de las exportaciones de Salta, por año,
en dos dimensiones: **rubro** (qué se exporta) y **país de destino** (a quién se le vende).

> **Este proceso es derivado: no descarga nada.** Lee el CSV que genera
> `Actualizar_Salta_exportaciones_INDEC.md`. El orden es siempre: primero ése, después éste.

> Tres cosas que hay que saber antes de usar esto:
> 1. **La serie por rubro está condicionada por el secreto estadístico**, que pasó del 20 % al 46 %
>    del valor exportado entre 2022 y 2024. En 2024 y 2025 la categoría más grande *es* el agregado
>    confidencial. Un movimiento de esa serie puede reflejar un cambio en la política de
>    confidencialidad del INDEC antes que un cambio real en la canasta exportadora.
> 2. **La serie por destino no tiene ese problema** y es la más sólida de las dos: las filas
>    confidenciales conservan el país.
> 3. **No es un capítulo NCM.** La apertura por capítulo no existe con desagregación provincial; el
>    máximo detalle de producto es el rubro del INDEC (ver la metodología).

Metodología y verificaciones: `Metodologia_Salta_exportaciones_HHI.md`.

## Qué genera (en `datos-drive/`)

**`Salta_exportaciones_HHI_rubro_destino_anual.csv`** — una fila por año y dimensión (10 filas para
2021–2025).

| Columna | Contenido |
|---|---|
| `provincia` | Siempre `Salta`. |
| `anio` | 2021–2025. |
| `dimension` | `Rubro` o `País de destino`. |
| `n_categorias` | Categorías con FOB > 0 ese año. **Varía entre años** (27→31 en rubro). |
| `hhi` | Σ sᵢ² sin normalizar. |
| `hhi_normalizado` | El índice pedido, escala **0–1**. |
| `hhi_normalizado_base100` | El mismo índice ×100. Es el que hay que graficar (ver abajo). |
| `top1_categoria` | Categoría líder del año — explica el movimiento de la serie. |
| `top1_share_pct` | Su participación en el FOB. |
| `fob_usd_total` | FOB total del año, denominador de las participaciones. Permite auditar la fila. |

Separador `,`, decimal `.`, codificación `utf-8-sig`.

> **Usar `hhi_normalizado_base100` para el tablero, no `hhi_normalizado`.** El front-end formatea
> los tooltips con `maximumFractionDigits: 0` (`assets/js/charts.js`), de modo que un valor como
> `0,1242` se muestra literalmente como **`0`**. Todos los índices del Monitor están en escala
> 0–100 por esta razón. La columna 0–1 se conserva porque es la fórmula tal como se pidió.

## La fórmula

```
HHI  = Σ sᵢ²                        sᵢ = participación de la categoría i en el FOB del año
HHI* = (HHI − 1/n) / (1 − 1/n)      n  = categorías con FOB > 0 en ese año
```

`HHI*` vale **0** si todas las categorías pesan lo mismo y tiende a **1** si una sola concentra
todo. `n` es el número de categorías **observadas cada año**, no una constante: es la definición
estándar y la que implica la fórmula, pero significa que el denominador de la normalización cambia
de un año a otro.

## 1. Requisitos

```bash
pip install pandas
```

## 2. Actualizar primero la base de origen

El índice se recalcula entero en cada corrida, así que alcanza con que
`Salta_exportaciones_INDEC_rubro_destino_desde_2021.csv` tenga el año nuevo. Ese paso está en
`Actualizar_Salta_exportaciones_INDEC.md` y es anual (el INDEC publica la base provincial una vez
por año).

## 3. Correr el script

Guardar el bloque de abajo como `actualizar_exportaciones_hhi.py` **dentro de `datos-drive/`**
(lee y escribe en su propia carpeta) y correr:

```bash
python actualizar_exportaciones_hhi.py
```

Tarda menos de un segundo. Imprime las dos series completas y las incidencias.

## 4. Verificar antes de dar por buena la actualización

1. **Los años ya publicados no deben moverse.** El índice se recalcula completo; si 2021–2025
   cambian respecto de la corrida anterior, cambió la base de origen y hay que entender por qué
   antes de publicar. Valores de referencia:

   | Año | Rubro n | Rubro HHI* | Destino n | Destino HHI* |
   |---|---|---|---|---|
   | 2021 | 27 | 0,124246 | 139 | 0,051047 |
   | 2022 | 31 | 0,107040 | 133 | 0,057906 |
   | 2023 | 31 | 0,108020 | 129 | 0,061758 |
   | 2024 | 29 | 0,106366 | 132 | 0,077121 |
   | 2025 | 29 | 0,109507 | 139 | 0,083964 |

2. **`fob_usd_total` debe coincidir** con los totales anuales que declara
   `Metodologia_Salta_exportaciones_INDEC_rubro_destino.md` (1.262.871.152 en 2021 …
   1.447.687.147 en 2025), y debe ser **idéntico entre las dos dimensiones** del mismo año: las dos
   reparten el mismo total.
3. **Recalcular el % confidencial del año nuevo** y actualizarlo en la metodología. Si volvió a
   subir, el salto de la serie por rubro hay que atribuirlo ahí antes que a la economía real.
4. **El script aborta solo** si las participaciones no suman 1, si el índice cae fuera de `[0, 1]`
   o si algún año queda con una sola categoría (la fórmula dividiría por cero). Que termine sin
   `ERROR:` ya es un control pasado.

## Cuando se arme el tablero (todavía no existe)

El Monitor **no descubre archivos solos**: hay que declarar el dataset. Notas para ese momento:

- Alta en `adapters.py` (función + registro en `ADAPTERS`) y en `catalog.py` (entrada en `TEMAS`).
- Conviene un **tema propio**, no colgarlo del adapter `exportaciones()`: sus filas tienen 7
  posiciones y sus `dims` se arman con `sorted({...})` sobre todas las filas, así que rellenar las
  dimensiones con `""` inyectaría una opción en blanco en los selects de ranking y en el buscador.
- La métrica se declara con **`agg: "mean"`**, nunca `"sum"`: es un índice, no un stock.
- `sentido: "menor_mejor"` es lo semánticamente correcto para una medida de concentración.
- Las fichas V.1–V.4 ya están tomadas; la nueva sería **V.5**, si no el control `qc_fichas` del
  build aborta.

---

## Script completo

```python
# -*- coding: utf-8 -*-
"""
Indice de concentracion Herfindahl-Hirschman (HHI) de las exportaciones de Salta.

DERIVADO: no descarga nada. Lee el CSV de exportaciones del INDEC que ya genera
`Actualizar_Salta_exportaciones_INDEC.md` y calcula, por anio, la concentracion de la
canasta exportadora por rubro y por pais de destino.

    HHI  = suma de s_i^2                    (s_i = participacion en el FOB del anio)
    HHI* = (HHI - 1/n) / (1 - 1/n)          (normalizado, 0 = equidistribucion, 1 = monopolio)

n = categorias con FOB > 0 en ese anio (no es fijo: varia entre anios).
"""
import os
import sys
import csv

import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(HERE, 'Salta_exportaciones_INDEC_rubro_destino_desde_2021.csv')
SALIDA = os.path.join(HERE, 'Salta_exportaciones_HHI_rubro_destino_anual.csv')

# (etiqueta de la dimension, columna de codigo, columna de descripcion)
# Se agrupa por CODIGO, no por descripcion: es la clave estable de la fuente.
DIMENSIONES = [
    ('Rubro', 'rubro_cod', 'rubro'),
    ('País de destino', 'pais_cod', 'pais_destino'),
]

COLUMNAS = ['provincia', 'anio', 'dimension', 'n_categorias', 'hhi', 'hhi_normalizado',
            'hhi_normalizado_base100', 'top1_categoria', 'top1_share_pct', 'fob_usd_total']

NOTAS = []


def hhi(participaciones):
    """Devuelve (HHI, HHI normalizado). `participaciones` suma 1."""
    n = len(participaciones)
    if n < 2:
        raise SystemExit('ERROR: una sola categoria con FOB > 0; la formula divide por 1 - 1/n '
                         '= 0. Revisar la base de origen antes de seguir.')
    h = float((participaciones ** 2).sum())
    hn = (h - 1.0 / n) / (1.0 - 1.0 / n)
    # Con categorias casi equidistribuidas el redondeo de punto flotante devuelve un negativo
    # minusculo (-1e-17): es cero, no un error. Se recorta antes de validar el rango.
    if -1e-9 < hn < 0.0:
        hn = 0.0
    return h, hn


def leer():
    if not os.path.exists(ENTRADA):
        raise SystemExit(
            'ERROR: no se encontro %s.\n'
            'Este script es derivado: primero hay que generar el dataset de exportaciones '
            'con Actualizar_Salta_exportaciones_INDEC.md.' % os.path.basename(ENTRADA))

    # rubro_cod es TEXTO ('104A', '106ZD'): leerlo como numero lo destruye.
    df = pd.read_csv(ENTRADA, encoding='utf-8-sig', dtype={'rubro_cod': str})
    for col in ('anio', 'pais_cod'):
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    df['fob_usd'] = pd.to_numeric(df['fob_usd'], errors='coerce')
    df = df.dropna(subset=['anio', 'pais_cod', 'fob_usd'])
    df['anio'] = df['anio'].astype(int)

    # Sin FOB positivo no hay participacion que calcular. Hoy no hay ceros ni negativos,
    # pero si la fuente los introduce el indice no debe romperse en silencio.
    descartadas = int((df['fob_usd'] <= 0).sum())
    if descartadas:
        NOTAS.append('se descartaron %d filas con fob_usd <= 0 antes de calcular '
                     'participaciones.' % descartadas)
    return df[df['fob_usd'] > 0].copy()


def calcular(df):
    filas = []
    for etiqueta, cod, desc in DIMENSIONES:
        # Una descripcion por codigo: se toma la primera y se avisa si hay mas de una.
        nombres = df.groupby(cod)[desc].agg(lambda s: s.iloc[0]).to_dict()
        ambiguos = df.groupby(cod)[desc].nunique()
        ambiguos = ambiguos[ambiguos > 1]
        if len(ambiguos):
            NOTAS.append('%s: %d codigo(s) con mas de una descripcion (%s); se usa la primera.'
                         % (etiqueta, len(ambiguos), ', '.join(map(str, ambiguos.index[:5]))))

        for anio, g in df.groupby('anio'):
            total = g.groupby(cod)['fob_usd'].sum().sort_values(ascending=False)
            fob_total = float(total.sum())
            s = total / fob_total

            if abs(float(s.sum()) - 1.0) > 1e-9:
                raise SystemExit('ERROR: las participaciones de %s %d suman %.12f, no 1.'
                                 % (etiqueta, anio, s.sum()))
            h, hn = hhi(s)
            if not (0.0 <= hn <= 1.0):
                raise SystemExit('ERROR: HHI normalizado fuera de [0, 1] en %s %d: %.6f'
                                 % (etiqueta, anio, hn))

            filas.append({
                'provincia': 'Salta',
                'anio': anio,
                'dimension': etiqueta,
                'n_categorias': len(total),
                'hhi': round(h, 6),
                'hhi_normalizado': round(hn, 6),
                'hhi_normalizado_base100': round(hn * 100, 4),
                'top1_categoria': nombres[total.index[0]],
                'top1_share_pct': round(100.0 * float(total.iloc[0]) / fob_total, 1),
                'fob_usd_total': round(fob_total, 2),
            })
    return filas


def escribir(filas):
    with open(SALIDA, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            w.writerow(fila)


def main():
    filas = calcular(leer())
    escribir(filas)

    # Relectura de control: mismas opciones que usa adapters.py.
    ctl = pd.read_csv(SALIDA, encoding='utf-8-sig')
    num = ['n_categorias', 'hhi', 'hhi_normalizado', 'hhi_normalizado_base100',
           'top1_share_pct', 'fob_usd_total']
    malas = [c for c in num if not pd.api.types.is_numeric_dtype(ctl[c])]
    if malas:
        raise SystemExit('ERROR: columnas que no releen como numero: %s' % ', '.join(malas))
    if int(ctl.isna().sum().sum()):
        raise SystemExit('ERROR: el CSV escrito tiene celdas vacias.')

    print('escrito: %s' % SALIDA)
    print('  %d filas | %d columnas\n' % (len(ctl), len(COLUMNAS)))
    for etiqueta, _, _ in DIMENSIONES:
        sub = ctl[ctl['dimension'] == etiqueta]
        print('  %s' % etiqueta)
        print('    %-6s %5s %9s %9s  %s' % ('anio', 'n', 'HHI', 'HHI*', 'categoria principal'))
        for r in sub.itertuples(index=False):
            print('    %-6d %5d %9.4f %9.4f  %s (%.1f%%)'
                  % (r.anio, r.n_categorias, r.hhi, r.hhi_normalizado,
                     r.top1_categoria, r.top1_share_pct))
        print()

    if NOTAS:
        print('Incidencias:')
        for n in NOTAS:
            print('  -', n)
    else:
        print('Incidencias: ninguna.')


if __name__ == '__main__':
    main()
```
