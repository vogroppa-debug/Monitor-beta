# Metodología — Indicadores socioculturales del PDES 2030 por departamento y región

**Origen:** planillas que acompañan el informe «Área Sociocultural del PDES 2030. Objetivos,
indicadores y brechas territoriales (informe de avance)», de Jorge Paz (2026). Carpeta de Drive
`1WC5BLXL9Y0ZlcTqmdgTpvGCcLUcKeH4Y`, compartida al CESS el 18 de noviembre de 2026. El informe
(`Informe_Nro_3_PAZ_version_integrada.pdf`, 46 páginas) queda en esa carpeta; no se versiona acá
por su tamaño (4,4 MB).

**Uso en el Monitor:** cinco tableros del eje sociocultural (`pdes-privacion`, `pdes-salud`,
`pdes-educacion`, `pdes-trabajo`, `pdes-delitos`), leídos por los adapters `pdes_*` de
`adapters.py`.

## Planillas

| Archivo | Fuente | Períodos | Indicadores que publica el Monitor |
|---|---|---|---|
| `Indicadores_sociocultural_Salta_2010_2022.xlsx` | INDEC, CNPV 2010 y 2022 (microdatos) | 2010, 2022 | % de personas en hogares con NBI; sin agua de red pública; NBI en población indígena |
| `Indicadores_salud_Salta_2018_2023_regiones.xlsx` | DEIS, estadísticas vitales | trienios 2018-2020, 2021-2023 | mortalidad infantil; bajo peso al nacer; fecundidad 15-19; natalidad; NV sin peso |
| `Indicadores_educativos_Salta_2018_2025_regiones.xlsx` | DiNIEE: Relevamiento Anual y Aprender Matemática 6.º | 2018, 2025 | matrícula, repitencia, sobreedad, secciones; niveles de Aprender, jardín, libros, educación de la madre |
| `Indicadores_trabajo_Salta_2010_2022.xlsx` | INDEC, CNPV 2010 y 2022 (microdatos) | 2010, 2022 | desocupación; informalidad; actividad y brecha por sexo |
| `Indicadores_seguridad_Salta_2013_2023.xlsx` | SNIC, Ministerio de Seguridad de la Nación | trienios 2013-2015, 2021-2023 | homicidio doloso; robos; lesiones dolosas; abuso sexual con acceso carnal |

No se incorporan `Tabla 1.xlsx` (matriz de planificación, sin datos) ni
`Indicadores_dimensiones_Salta_departamentos.xlsx` (índice sintético exploratorio del informe):
el índice «¿Cómo vamos?» del Monitor se define en reunión del CESS.

## Lectura

- Se leen sólo las hojas de cada período, por **nombre de columna** (en Aprender la misma columna
  cambia de lugar entre 2018 y 2025). Las hojas de variación no se usan: vienen como texto
  («−11.0 p.p.») y la variación la calcula el Monitor.
- **Formato numérico** (skill `datasets`): todas las celdas son numéricas, decimal con punto. En
  salud, los porcentajes están guardados como proporción con formato % de Excel; el lector común
  (`_soc_celda`) los multiplica por 100. Verificado contra los totales provinciales del informe.
- El encabezado de la matrícula usa el ordinal «º» (1.º–7.º), no el signo de grado «°».
- Se descartan las filas «Departamento sin especificar», «Departamento sin determinar» y «Celdas
  enmascaradas»: como en la fuente, sólo cuentan en el total provincial.
- Los trienios se guardan con su último año (2020, 2023; 2015, 2023) y se muestran como
  «2018-20», «2021-23».
- La variación se calcula contra el **período anterior con dato** (`var: "anterior"`); los
  porcentajes, en puntos porcentuales. La frecuencia de la tabla dice qué se compara:
  «Intercensal», «Entre trienios», «Entre 2018 y 2025».

## Regiones del PDES

El informe aproxima las ocho regiones asignando cada departamento completo a una sola región:

| Región | Departamentos |
|---|---|
| Puna | Los Andes |
| Pre-Puna | Iruya, Santa Victoria |
| Valles Calchaquíes | Cachi, Cafayate, La Poma, Molinos, San Carlos |
| AMVL | Capital, Cerrillos, La Caldera, Rosario de Lerma |
| Valle de Lerma | Chicoana, Guachipas, La Viña |
| Valles Centrales | General Güemes, La Candelaria, Metán, Rosario de la Frontera |
| Chaco | Anta, General José de San Martín, Rivadavia |
| Yungas | Orán |

La regionalización original parte algunos departamentos; por eso Puna equivale sólo a Los Andes
y Yungas sólo a Orán. Las regiones son sumas de conteos departamentales con el indicador
recalculado, no promedios. Las planillas escriben «Prepuna» o «Pre-Puna» y «Valles de Lerma»; el
Monitor usa los nombres del informe.

## Advertencias

1. **Censos:** 2010 sale del cuestionario ampliado (muestra expandida, con error muestral en
   departamentos chicos y grupos pequeños); 2022, del censo completo.
2. **NBI indígena:** la pregunta cambia (por hogar en 2010, autorreconocimiento individual en
   2022). La variación no es la de una misma población.
3. **Personas, no hogares:** la NBI se determina por hogar y se asigna a todas sus personas. El
   Monitor conserva además la NBI de hogares (Censo 2022), que tiene su propia meta en el PDES.
4. **Agua:** «sin agua de red» no significa «sin agua apta».
5. **Salud:** la TMI departamental es inestable en La Poma, Los Andes, Guachipas, La Caldera y
   Molinos aun por trienio. La fecundidad adolescente no es el % de adolescentes madres y excluye
   a las menores de 15. Los denominadores son proyecciones INDEC base 2010, que el INDEC
   recomienda usar con reservas para Salta.
6. **Educación:** la matrícula departamental está subestimada por el enmascaramiento de la
   fuente. Aprender compara cohortes distintas; pocos evaluados en Guachipas, La Poma y Cachi.
7. **Trabajo:** la informalidad mide sólo la falta de protección contributiva.
8. **Delitos:** son registrados, por lugar del hecho, y dependen de la denuncia y de la presencia
   policial; el homicidio es el indicador más robusto.
9. **No causal:** el informe es descriptivo; no evalúa políticas ni cumplimiento de metas.

## Reemplazos en el Monitor

Seis indicadores que venían de las «Dimensiones» II y III pasan a estas planillas, conservando
su código de ficha: II.8 mortalidad infantil, II.10 bajo peso, II.18 fecundidad adolescente,
III.1 matrícula de primaria y secundaria, III.2 repitencia en secundaria y III.8 Aprender
Matemática. La meta de agua de red del PDES (93 % de cobertura al Censo 2030) pasa del indicador
«hogares sin agua por cañería» al de personas sin agua de red pública, y se carga la meta de
«NBI población» (12 %) en el indicador de personas con NBI.
