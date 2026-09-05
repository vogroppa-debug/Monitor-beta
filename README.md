# Monitor de Indicadores CESS — sitio web

Sitio **estático** con tableros interactivos para el seguimiento del Plan de Desarrollo
Estratégico de Salta (PDES 2050), pensado para consulta de decisores no especialistas.

- **Portada** con buscador (por tema, indicador o departamento) y navegación por eje del PDES.
- **Una página por tema** con KPIs, gráficos interactivos (ECharts) y filtros.
- Todo **autocontenido y offline** (librerías vendorizadas; sin CDN).

Esta primera entrega incluye el andamiaje completo + **3 tableros modelo**: Educación,
Vitivinicultura y Producción de petróleo y gas.

## Cómo verlo en local

Requisitos (una sola vez):

```bash
pip install pandas jinja2
```

1. Generar el sitio a partir de los CSV tidy de la carpeta padre:

```bash
python build.py
```

2. Levantar un servidor local (los gráficos cargan datos por `fetch`, así que **no** alcanza
   con abrir el HTML como archivo):

```bash
python -m http.server 8000
```

3. Abrir <http://localhost:8000/> en el navegador.

## Cómo se actualizan los datos

1. Correr el script del indicador correspondiente (`../Actualizar_*.md` → regenera su CSV tidy,
   descargando de la fuente oficial).
2. Volver a correr `python build.py` (segundos, offline). El sitio queda actualizado.

El build **no** re-descarga nada: lee los CSV ya generados. Ver `BUILD_NOTES.md` (se regenera en
cada corrida) para la metodología y las incidencias detectadas.

## Estructura

```
build.py          Orquesta: CSV -> JSON + render de HTML. Resuelve años y controles.
catalog.py        Metadatos de cada tema + palabras clave (buscador) + specs de gráficos/KPIs.
adapters.py       Normaliza cada CSV al esquema canónico largo (geografía × tiempo × métrica × valor).
templates/        Jinja2: base / index (portada) / tema.
assets/css/       Sistema de diseño (paleta validada, claro/oscuro, responsive).
assets/js/        app.js (nav+tema) · search.js (buscador) · charts.js (fábrica de gráficos).
assets/vendor/    echarts.min.js · minisearch.min.js (vendorizados, offline).
data/             SALIDA del build: <tema>.json + catalog.json.
index.html        SALIDA del build (portada).
tema/<id>.html    SALIDA del build (una por tema).
```

## Cómo agregar un tema nuevo (fase 2)

1. **Adapter** en `adapters.py`: una función que lea el/los CSV del tema y devuelva
   `{fields, rows, dims, metricas, notas}` en esquema largo (`… , metrica , valor`).
   Registrala en `ADAPTERS`.
2. **Catálogo** en `catalog.py`: agregá una entrada a `TEMAS` con `area`, `title`, `resumen`
   (lenguaje llano), `fuente`/`fuente_url`, `cobertura`, `keywords` (sinónimos en español para
   el buscador), `kpis` y `charts`.
3. `python build.py`. El menú, la portada y el buscador se actualizan solos.

Temas pendientes (sus `.md` ya existen; varios requieren generar el CSV corriendo su script):
ejecución presupuestaria, finalidad-función, transferencias, empleo/remuneraciones (OEDE),
ganadería bovina, CAMMESA (generación/demanda eléctrica), turismo (EOH), permisos de
construcción, BCRA (inclusión financiera / depósitos-préstamos), recursos a municipios.

## Publicación futura

Al ser estático, se publica copiando la carpeta a cualquier hosting (GitHub Pages, Netlify) o al
sitio institucional (cessalta.org.ar). No requiere servidor de aplicaciones.
