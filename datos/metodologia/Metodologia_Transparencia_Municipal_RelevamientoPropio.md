# Metodología — Transparencia municipal de Salta, relevamiento propio sobre canales oficiales

Datasets: `Transparencia_Municipal_Salta_RelevamientoPropio.csv` (derivado) y
`Relevamiento_Transparencia_Municipal_Salta_planilla.csv` (fuente de verdad, con evidencia y notas).
Fecha de relevamiento: **2026-11-04**. Cobertura: **los 60 municipios de Salta**.

## Por qué existe

El Monitor no tenía ningún indicador de transparencia de los gobiernos locales, y no hay una
medición oficial que cubra a los 60 municipios de Salta. Este relevamiento la construye con 10
criterios valorados sí / parcial / no, **apoyando cada puntaje en una URL oficial** que cualquiera
puede abrir, y separando lo que no se publica de lo que no se pudo leer.

**Qué es y qué no es.** La evidencia es oficial: sitios municipales, boletines, Concejos
Deliberantes y el Boletín Oficial de la Provincia. **El índice es propio del CESS**, no un dato
oficial: las reglas de decisión, el relevamiento y los puntajes son nuestros. La grilla de 10 criterios
sigue la del semáforo de transparencia de `municipiosargentinos.net`; de ese sitio no se usa ninguna
medición. Debe citarse como «relevamiento propio del CESS sobre canales oficiales municipales».

## Canales relevados

Se consideran canales oficiales del municipio, en este orden:

1. **El sitio web del municipio** (Departamento Ejecutivo), incluidos sus subdominios.
2. **Su boletín oficial**, propio o alojado en el sitio.
3. **El sitio del Concejo Deliberante**, que es órgano del municipio.
4. **El Boletín Oficial de la Provincia de Salta**, apartado Municipios
   (<https://boletinoficialsalta.gob.ar/Municipios.php>), que lista a los 60 municipios con las normas
   que publicaron allí. **Es también la lista oficial de municipios** que usa el relevamiento.

**No cuentan** como canal de publicación:

- **Redes sociales**: no son repositorios consultables ni estables.
- **Portales turísticos**: en los Valles Calchaquíes una plataforma privada (Itinere) aloja los sitios de
  turismo de Seclantás, Cachi, Molinos, Angastaco, La Poma, Chicoana, San Antonio de los Cobres, San
  Carlos y Tolar Grande. No traen información de gestión.
- **Accesos con login**: el Sistema Integral de Gestión Municipal de General Güemes y de Metán (solo
  pantalla de ingreso, «versión para testing»), portales de recibos de sueldo, el portal de pago de
  tasas de Rentas provincial (`municipios.dgrsalta.gov.ar`).
- **Sitios de particulares** sobre la localidad: blogs, sitios personales, proyectos en GitHub Pages.
- **Leyes provinciales** sobre el municipio publicadas en el Boletín provincial: las Cartas Municipales
  sancionadas en 2026 son actos de la Legislatura, no publicaciones del municipio.

## Cómo se relevó

1. **Primero 14 municipios** (los que tenían algún canal identificado de antemano), revisados a fondo:
   menú, buscador interno, sitio del Concejo, boletines y ordenanzas abiertos uno por uno, incluidos
   los PDF escaneados.
2. **Luego los 46 restantes**: búsqueda del sitio oficial y del Concejo Deliberante en el navegador
   (Bing), descarte de homónimos y de sitios no municipales, revisión de los que resultaron oficiales, y
   lectura de toda norma propia que hubieran publicado en el Boletín provincial en los últimos 12
   meses.

## Reglas de decisión

Valores: `si` (1) · `parcial` (0,5) · `no` (0) · `no_verificado` (0, contado aparte).
Ventana de vigencia: **12 meses** antes de la fecha de relevamiento (desde 2025-11-04).

| Criterio | sí | parcial | no |
|---|---|---|---|
| Presupuesto vigente | Presupuesto 2026 (ordenanza o anexos) publicado | Solo proyecto 2026; o presupuesto 2025 o anterior; o resumen **con cifras** sin el documento | Nada hallado. Una nota de prensa sin cifras no cuenta |
| Ejecución presupuestaria | Ejecución 2026 (parcial del año) o cierre 2025, con recursos **y** gastos | Ejecución anterior a 2025; o solo recursos o solo gastos; o agregado sin detalle | Nada hallado. La resolución que aprueba la Cuenta General, sin la cuenta, no cuenta |
| Planta de personal y sueldos | Nómina o planta **y** escalas o sueldos | Solo una de las dos; o solo funcionarios; o solo la planta de cargos del presupuesto | Nada hallado. Un portal de recibos con login no es publicación |
| Compras y contrataciones | Sección, llamados o actos de contratación publicados con regularidad, al menos uno en 12 meses (vale el boletín) | Llamados sueltos como noticia, sin sección; o todos con más de 12 meses | Nada hallado |
| Declaraciones juradas | DDJJ patrimoniales de funcionarios (al menos el intendente), de 2024 en adelante | Desactualizadas, de algunos, o sección sin documentos legibles | Nada hallado. Un formulario en blanco no cuenta |
| Boletín oficial | Boletín propio con ediciones de los últimos 12 meses | Boletín desactualizado; o normas sueltas; o normas **del municipio** en el BO provincial en los últimos 12 meses | Nada hallado. Una sección llamada «boletín» que es una noticia no cuenta |
| Canal de acceso a la información | Formulario o procedimiento específico para pedir información pública | Normativa o sección de acceso, sin canal de pedido operativo | Nada. Un formulario de contacto genérico o informes de gestión no cuentan |
| Datos abiertos | Conjuntos descargables y funcionales en formato reutilizable (CSV, XLS, JSON, GeoJSON) | Sección de datos abiertos solo con PDF, visores o descargas que no funcionan | Nada hallado |
| Publica adjudicaciones | Resultados de adjudicación (actos que adjudican a un proveedor) de los últimos 12 meses | Solo antiguos o aislados | Nada hallado. Los llamados del procedimiento «Adjudicación Simple» no son resultados |
| Declara cuántos empleados tiene | Cantidad de agentes ocupados, o nómina que permita contarlos | Solo cargos presupuestados (planta con vacantes) | Nada hallado |

`no_verificado`: el canal oficial existe pero no se pudo leer en la fecha (sitio caído, certificado
TLS inválido, enlace roto, login, página por defecto del hosting). **No se forzó el acceso** en ningún
caso.

Una sección vacía **es `no`**, no `no_verificado`: Aguas Blancas tiene un «Portal de Transparencia»
con categorías que dicen «Sin documentos publicados», y Mosconi páginas «Transparencia» y «Presupuesto
anual» que solo tienen el título. El canal se leyó; lo que no hay es contenido.

Las reglas se precisaron durante los primeros 14 municipios, en tres puntos (nota de prensa sin cifras,
leyes provinciales en el Boletín provincial, actos de contratación en boletines). Cada precisión se
volvió a aplicar sobre los ya relevados; ninguno cambió de valor.

## Resultados (2026-11-04)

### Provincia

| | |
|---|---|
| Municipios | 60 |
| Con sitio web oficial identificado | 17 |
| **Con índice 0** | **49** (577.131 habitantes, el 40 % de la población) |
| Con algún criterio no verificado | 3 (Aguaray, Animaná, Rosario de la Frontera) |
| Promedio simple | **4,0** |
| Promedio ponderado por población (Censo 2022) | **29,3** (lo empuja la Capital: 594.772 habitantes con 55 puntos) |

### Los 11 municipios con puntaje

| Municipio | Departamento | Índice | sí | parcial | no | no verif. |
|---|---|---|---|---|---|---|
| San Ramón de la Nueva Orán | Orán | **65** | 5 | 3 | 2 | 0 |
| Salta | Capital | **55** | 4 | 3 | 3 | 0 |
| San José de los Cerrillos | Cerrillos | **45** | 4 | 1 | 5 | 0 |
| Rosario de la Frontera | Rosario de la Frontera | **30** | 1 | 4 | 0 | 5 |
| Cafayate | Cafayate | 10 | 0 | 2 | 8 | 0 |
| San Lorenzo | Capital | 10 | 1 | 0 | 9 | 0 |
| Aguas Blancas | Orán | 5 | 0 | 1 | 9 | 0 |
| Coronel Moldes | La Viña | 5 | 0 | 1 | 9 | 0 |
| La Caldera | La Caldera | 5 | 0 | 1 | 9 | 0 |
| La Merced | Cerrillos | 5 | 0 | 1 | 9 | 0 |
| Profesor Salvador Mazza | General José de San Martín | 5 | 0 | 1 | 9 | 0 |

Los cinco con 5 puntos lo obtienen solo por el boletín: La Caldera, por un boletín propio que se cortó
en 2022; los otros cuatro, por normas sueltas recientes en su sitio o en el Boletín provincial. Los
otros 49 tienen 0.

### Por criterio, sobre los 60

| Criterio | sí | parcial | no | no verif. |
|---|---|---|---|---|
| Boletín oficial | 2 | 7 | 49 | 2 |
| Compras y contrataciones | 4 | 1 | 52 | 3 |
| Presupuesto vigente | 3 | 1 | 54 | 2 |
| Publica adjudicaciones | 2 | 1 | 54 | 3 |
| Canal de acceso a la información | 1 | 2 | 55 | 2 |
| Planta de personal y sueldos | 1 | 2 | 55 | 2 |
| Declara cuántos empleados tiene | 1 | 2 | 55 | 2 |
| Ejecución presupuestaria | 1 | 0 | 56 | 3 |
| Datos abiertos | 0 | 2 | 55 | 3 |
| Declaraciones juradas | **0** | 0 | 57 | 3 |

Solo 3 de los 60 municipios publican su presupuesto 2026 completo (Salta, Cerrillos y Rosario de la
Frontera, este último en el sitio del Concejo). Solo Orán publica la ejecución del último ejercicio y
solo Orán tiene un formulario de acceso a la información. Ninguno publica declaraciones juradas
patrimoniales ni datos abiertos descargables que funcionen.

## Homónimos y sitios descartados

El problema más frecuente al buscar sitios fue dar con **otro municipio del mismo nombre**. Se
descartaron por domicilio o característica telefónica:

| Municipio de Salta | Sitio hallado | Es de |
|---|---|---|
| Hipólito Yrigoyen | `hipolitoyrigoyen.gob.ar` · `hipolitoyrigoyen.net` | Buenos Aires · Misiones |
| Colonia Santa Rosa | `concejosantarosa.gob.ar` · `santarosactes.gob.ar` | La Pampa · Corrientes |
| Coronel Moldes | `cmoldes.com.ar` | Córdoba (característica 03582) |
| San Carlos | `sancarlos.gob.ar` | Mendoza |
| La Candelaria | `candelaria.gob.ar` · `municipdecandelaria.com` | Misiones |
| Rivadavia Banda Norte y Sur | `munirivadavia.gob.ar`, `hcdrivadavia.gob.ar` · `rivadavia.gob.ar` | Buenos Aires · San Juan |

## Verificación

1. **Validación de la planilla**: el script aborta si falta un criterio, si hay uno repetido, si un
   valor no es de los permitidos, si un `si`/`parcial` no tiene URL o si una fila no tiene nota.
   Probado con cinco corrupciones deliberadas: las cinco abortan señalando fila, municipio y criterio.
2. **Cobertura**: los 60 municipios del padrón (660 filas en la planilla, 11 por municipio). Los 60
   cruzan con la lista del Boletín provincial y con el padrón de la Contaduría, del que se toma el
   **departamento**: 60 de 60 asignados.
3. **Contenido abierto, no títulos**: los documentos decisivos se leyeron, incluidos los escaneados
   (ejecución de Orán, presupuestos de Cerrillos y Rosario de la Frontera). Las cinco normas propias
   publicadas en el Boletín provincial en los últimos 12 meses por municipios sin sitio se abrieron una
   por una para descartar que alguna fuera el presupuesto (eran un reglamento de juicio político, dos
   ordenanzas tributarias, una de disposición de inmuebles municipales y la promulgación de una ordenanza
   de 2022).
4. **Funcionamiento**: las 10 descargas de datos abiertos de Salta Capital se probaron una por una
   (fallan todas).
5. **Identidad del municipio**: cada sitio se confirmó por domicilio o referencias locales.
6. **Reproducibilidad**: el bloque `python` del runbook regenera el CSV derivado **md5-idéntico**
   (`47108555dc9ac40fed47781b3dd3302f`).

## Incidencias

| Incidencia | Veredicto |
|---|---|
| Rosario de la Frontera (`munirfrontera.com`): certificado TLS inválido | 5 criterios `no_verificado`; el resto se resolvió con el sitio del Concejo. |
| Aguaray (`aguaray.gob.ar`): sin respuesta (timeout) | 10 criterios `no_verificado`. |
| Animaná (`animanasalta.com.ar`): la prensa informó su lanzamiento como sitio oficial, pero muestra la página por defecto del hosting | 10 criterios `no_verificado`. |
| Datos abiertos de Salta (IDEMSa): las 10 capas devuelven «Feature type unknown» | `parcial`. |
| Mosconi: páginas de transparencia, presupuesto, licitaciones y ordenanzas creadas pero vacías | `no`: el canal se leyó y no tiene contenido. |
| Aguas Blancas: «Portal de Transparencia» con cinco de seis categorías vacías | `no` en esas cinco; `parcial` en boletín por dos ordenanzas recientes. |
| General Güemes y Metán: solo un acceso con login a un sistema de gestión | `no`: no es un canal de publicación. |
| El Carril: el único canal propio es un blog municipal sin publicaciones desde 2015 | `no`. |
| Directorio de municipios de Edusalta: enlaza solo 8 municipios, con datos desactualizados (Embarcación apunta a un blog no municipal) | No se usó como fuente; dejó de permitir el acceso durante el relevamiento. |
| Orán: la nómina solo aparece por el buscador; «Adjudicaciones Públicas» son llamados, no resultados | Protocolo: usar siempre el buscador; `no` en adjudicaciones. |
| Rosario de Lerma: última ordenanza en el BO provincial del 30/10/2025, cinco días fuera de la ventana | `no` en boletín, por la regla. |

## Supuestos y limitaciones

- **El relevamiento lo hizo un asistente de IA con navegador** (Claude, de Anthropic), con cada
  decisión documentada en la planilla. **No hubo un segundo codificador humano.** Antes de publicar
  conviene que una persona del CESS verifique una muestra de URLs de evidencia, y en especial los
  **11 municipios con puntaje**, donde están las decisiones de juicio.
- **La revisión no fue igual de profunda en todos los municipios.** Los 14 primeros se revisaron
  abriendo boletines y ordenanzas; en los 46 restantes, la mayoría sin sitio, el relevamiento consistió
  en buscar canales y leer las normas recientes del Boletín provincial. Un municipio sin sitio que
  publique en un canal que la búsqueda no encontró queda con `no`.
- **Es una foto de un día.** Los `no_verificado` pueden ser fallas pasajeras.
- **Mide publicación en canales oficiales en línea, no cumplimiento legal.** Un municipio que entrega
  información a pedido, en papel o en el Concejo, puntúa 0. En Salta, eso describe a la mayoría.
- **Las reglas de decisión son del CESS.** Otras reglas razonables darían otros números en los
  municipios con puntaje; en los que no tienen ningún canal, cualquier regla da 0.
- **El índice da el mismo peso a los 10 criterios.**
- **Efecto piso**: con 49 municipios en 0, el índice discrimina poco entre los chicos. Para comparar,
  sirven más el conteo por criterio y la presencia o no de un sitio oficial que el puntaje.
