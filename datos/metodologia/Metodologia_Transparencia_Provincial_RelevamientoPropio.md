# Metodología — Transparencia del Gobierno provincial de Salta (relevamiento propio)

**Archivo:** `Transparencia_Provincial_RelevamientoPropio.csv`. Se deriva de
`Relevamiento_Transparencia_Provincial_planilla.csv`, la fuente de verdad, que se edita a mano.
**Fecha de verificación:** 2026-11-07.
**Alcance:** el Poder Ejecutivo de la Provincia de Salta, incluidos sus organismos (Oficina Provincial
de Presupuesto, Contaduría General, Subsecretaría de Contrataciones, Boletín Oficial, Escribanía de
Gobierno, IDESA y Estadísticas).
**Cómo actualizarlo:** `Actualizar_Transparencia_Provincial_RelevamientoPropio.md`.

## Qué mide

Este índice responde una pregunta concreta: si se aplica al Gobierno provincial la misma vara que a
los municipios, ¿qué puntaje obtiene?

Para eso se usan **los mismos 10 criterios, los mismos valores** (sí = 1, parcial = 0,5, no y no
verificado = 0) **y la misma fórmula** que en el relevamiento propio de los 60 municipios
(`Metodologia_Transparencia_Municipal_RelevamientoPropio.md`). Así, los dos índices quedan en la misma
escala de 0 a 100.

Lo que mide es la **publicación activa en canales oficiales**, en una fecha dada. **No** mide el
cumplimiento de la ley, ni la calidad o la veracidad de lo publicado, ni la información que se entrega
a pedido.

## Canales y reglas

**Valen** los sitios oficiales del Gobierno (`salta.gob.ar` y sus subdominios), los de sus organismos
del Ejecutivo y el Boletín Oficial provincial.

**No cuentan:**
- los sitios nacionales (DNAP, CFI, INDEC), porque no son publicación de la provincia;
- los de la Legislatura, el Poder Judicial y el Ministerio Público, que quedan fuera del alcance;
- las redes sociales y los sistemas con login.

Las reglas de decisión son las municipales, con los objetos traducidos al nivel provincial: ley de
presupuesto en lugar de ordenanza, planta de cargos de la ley y otros equivalentes. Están completas en
`fuentes/relevamiento_transparencia/reglas_de_decision_provincial.md`. La ventana de vigencia es de 12
meses.

## Resultado (2026-11-07)

**Transparencia: 70 / 100**, con 6 criterios en sí, 2 en parcial y 2 en no. Ningún criterio quedó
sin verificar.

| Criterio | Valor | Evidencia principal |
|---|---|---|
| Presupuesto vigente | sí | Ley 8518, Presupuesto 2026, con planillas anexas, decreto de distribución y mensaje. |
| Ejecución presupuestaria | sí | Esquema Ahorro-Inversión mensual, acumulado al 31/07/2026, más la Cuenta General 2025. |
| Planta de personal y sueldos | parcial | La planta de cargos sí está (Art. 8 de la Ley 8518: 61.495 cargos). La única escala salarial publicada es de 2023. |
| Compras y contrataciones | sí | SaltaCompra: 376 procesos con apertura en los últimos 30 días. |
| Declaraciones juradas | **no** | La Escribanía de Gobierno las recibe, pero sólo publica instructivos e informes de cumplimiento (el último, de 2020). |
| Boletín oficial | sí | Edición diaria. |
| Canal de acceso a la información | **no** | No hay formulario ni procedimiento en los sitios del Ejecutivo, sólo un buzón de sugerencias. |
| Datos abiertos | sí | WFS de IDESA: 31 capas, con descarga verificada en GeoJSON y CSV. |
| Publica adjudicaciones | sí | El Boletín Oficial publica los actos de adjudicación con firma y monto: 2.715 avisos en 12 meses. |
| Declara cuántos empleados tiene | parcial | Sólo cargos presupuestados: 61.495 más 6.626 en entes no consolidados. |

La URL y la nota de cada juicio están en la planilla.

## Comparación con los municipios de Salta

Los dos relevamientos usan la misma vara, pero no son de la misma fecha: los municipios se relevaron
el 2026-11-04 y la provincia, el 2026-11-07.

| | Transparencia |
|---|---|
| **Gobierno provincial (Ejecutivo)** | **70** |
| Municipio mejor ubicado (San Ramón de la Nueva Orán) | 65 |
| Salta Capital | 55 |
| Promedio de los 60 municipios, ponderado por población (Censo 2022) | 29,3 |
| Promedio simple de los 60 municipios | 4,0 |

Por criterio: el Gobierno provincial frente a la cantidad de municipios, de 60, que obtienen sí o
parcial.

| Criterio | Provincia | Municipios con sí | con parcial |
|---|---|---|---|
| Presupuesto vigente | sí | 3 | 1 |
| Ejecución presupuestaria | sí | 1 | 0 |
| Planta de personal y sueldos | parcial | 1 | 2 |
| Compras y contrataciones | sí | 4 | 1 |
| Declaraciones juradas | no | 0 | 0 |
| Boletín oficial | sí | 2 | 7 |
| Canal de acceso a la información | no | 1 | 2 |
| Datos abiertos | sí | 0 | 2 |
| Publica adjudicaciones | sí | 2 | 1 |
| Declara cuántos empleados tiene | parcial | 1 | 2 |

Lectura:
- **La brecha entre niveles de gobierno es grande.** El Ejecutivo provincial cumple lo que cumplen,
  como mucho, cuatro de los 60 municipios. En ejecución presupuestaria, sólo Orán alcanza lo que
  publica la provincia. En datos abiertos no lo alcanza ninguno: Salta Capital y Orán quedan en
  parcial.
- **Dos debilidades compartidas.** Ni la provincia ni ningún municipio publica declaraciones juradas.
  En acceso a la información, la provincia está **detrás** de tres municipios: Orán, que tiene
  formulario, y Cerrillos y Rosario de la Frontera, que tienen normativa o sección propia.
- **El 70 no equivale a datos reutilizables.** El sí en datos abiertos se apoya sólo en información
  geográfica. Presupuesto, ejecución y Cuenta General se publican únicamente en PDF, y en buena parte
  escaneados.

## Casos de juicio

Estos casos conviene que los revise una persona:

1. **Datos abiertos = sí.** La regla pide conjuntos descargables en formato reutilizable, y el WFS de
   IDESA lo cumple: se verificó la descarga de 5 capas. Pero son sólo datos geográficos. Con una lectura
   más exigente, que pidiera datos de gestión, el criterio sería parcial y el índice bajaría a 65.
2. **Acceso a la información = no.** El Decreto 1574/02 («Estándar mínimo de acceso a la información
   de la Administración Pública») existe y debe de estar en una edición del Boletín Oficial de 2002.
   Esas ediciones están escaneadas y no se lo localizó, y ningún sitio del Ejecutivo lo presenta. Si se
   lo encuentra publicado en un canal oficial, el criterio pasaría a parcial y el índice a 75.
3. **Planta y empleados = parcial.** La Cuenta General 2025 tiene 185 de sus 249 páginas escaneadas y
   no se revisó entera. Además, el Portal del Empleado Público, donde podrían estar las escalas
   vigentes, tenía el certificado vencido. Cualquiera de los dos podría subir estos criterios a sí.

## Incidencias de la toma

- **Certificados TLS vencidos o inválidos** el 2026-11-07 en `empleadopublico.salta.gob.ar` y
  `estadisticas.salta.gov.ar`. Se aplicó la regla del relevamiento municipal: no se fuerza el acceso.
  Los criterios afectados se decidieron con otra evidencia, por eso no hay `no_verificado`. Lo
  publicado sólo en esos sitios no se tuvo en cuenta.
- **El portal de compras está en transición.** `compras.salta.gob.ar` anuncia su cierre al 31/10/2026
  en favor de SaltaCompra, pero seguía publicando el 2026-11-07. El cartel da como contacto una
  dirección de Gmail y un formulario alojado en Vercel, fuera del dominio oficial. No se usaron como
  evidencia.
- **El buscador avanzado de SaltaCompra** no devolvió resultados al filtrar por estado «Adjudicado»
  ni «Con Documento Contractual». Las adjudicaciones se verificaron en el Boletín Oficial.
- **Documentos escaneados:** la Ley 8518 (16 páginas) y la mayor parte de la Cuenta General 2025. La
  ley se leyó en la imagen; de la Cuenta General sólo se leyeron las páginas con texto.

## Limitaciones

- **Una sola unidad.** Con una provincia, el índice no tiene varianza propia: se lee contra los
  municipios o contra otras provincias, cuando se agreguen.
- **El relevamiento lo hizo un asistente de IA**, sin un segundo codificador humano. El runbook pide
  que una persona revise todas las evidencias.
- **La vara municipal le queda chica al nivel provincial.** Criterios propios de una provincia, como
  la deuda, las transferencias a municipios o el presupuesto ciudadano, no se miden; se dejaron
  afuera a propósito para mantener la comparabilidad.
- **Sólo el Poder Ejecutivo.**
- **Fechas distintas:** municipios el 2026-11-04 y provincia el 2026-11-07. En tomas futuras conviene
  relevar los dos niveles en la misma semana.

## Verificación hecha

1. El script valida la planilla. Se probaron 6 corrupciones y las 6 abortan: criterio faltante, valor
   inválido, sí sin URL, nota vacía, criterio duplicado y provincia no listada.
2. Reproducibilidad: el bloque python del runbook, corrido sobre la planilla, regenera el CSV con md5
   `71aed783bab44f176f4a6ff2470012e3`.
3. Segunda pasada: se reabrieron las 9 URL de evidencia y todas respondieron (HTTP 200). La descarga
   WFS se verificó aparte.
4. Formato: separador `,`, decimal `.`, sin valores con coma decimal, `utf-8-sig`.
5. Columnas: son las del archivo municipal menos `municipio` y `departamento`, más `poder`.
