# Actualizar — Exportaciones de Salta por rubro y destino (INDEC COMEX)

Regenera `Salta_exportaciones_INDEC_rubro_destino_desde_2021.csv`.
Metodología y verificaciones: `Metodologia_Salta_exportaciones_INDEC_rubro_destino.md`.

## 1. Descargar la base anual del último año publicado

El `.xlsb` con la apertura por provincia de origen viaja **dentro del paquete anual del último año
disponible**. La URL es directa (el formulario de <https://comex.indec.gob.ar/#/database> resuelve a
esto): reemplazar `2025` por el último año con base anual publicada.

```powershell
$dir = "$env:TEMP\comex"
New-Item -ItemType Directory -Force $dir | Out-Null
Invoke-WebRequest -Uri "https://comex.indec.gob.ar/files/zips/exports_2025_Y.zip" `
                  -OutFile "$dir\exports_2025_Y.zip" -UseBasicParsing
Expand-Archive "$dir\exports_2025_Y.zip" -DestinationPath "$dir\ex" -Force
```

Dentro queda `Datos_origen_2002_2025.xlsb` (el nombre cambia con el año final).

## 2. Requisito

```
pip install pyxlsb
```

## 3. Correr el script

Ajustar `PATH` (nombre del `.xlsb`) y, si corresponde, agregar la hoja nueva a `HOJAS`: el archivo
parte la serie en hojas por tramo de años (`datos origen_2002-2011`, `2012-2022`, `2023-2025`).

```python
import csv
from pyxlsb import open_workbook

PATH  = r"...\Datos_origen_2002_2025.xlsb"
OUT   = r"G:\Documents\CESS\Indicadores\datos-drive\Salta_exportaciones_INDEC_rubro_destino_desde_2021.csv"
HOJAS = ["datos origen_2012-2022", "datos origen_2023-2025"]
DESDE = 2021

GRAN_RUBRO = {"1": "Productos primarios",
              "2": "Manufacturas de origen agropecuario (MOA)",
              "3": "Manufacturas de origen industrial (MOI)",
              "4": "Combustibles y energía"}

filas = []
with open_workbook(PATH) as wb:
    for hoja in HOJAS:
        with wb.get_sheet(hoja) as sh:
            for i, row in enumerate(sh.rows()):
                if i == 0:
                    continue
                v = [c.v for c in row]
                if len(v) < 10:
                    continue
                anio, mes, pcia, dpcia, crub, drub, cpais, dpais, fob, kg = v[:10]
                if str(pcia).strip().upper() != "SA":
                    continue
                anio_i = int(str(anio).strip())
                if anio_i < DESDE:
                    continue
                cod = str(crub).strip()
                filas.append({
                    "provincia": "Salta", "anio": anio_i,
                    "gran_rubro": GRAN_RUBRO.get(cod[:1], ""),
                    "rubro_cod": cod, "rubro": str(drub).strip(),
                    "confidencial": "1" if cod.endswith("9899") else "0",
                    "pais_cod": str(cpais).strip(), "pais_destino": str(dpais).strip(),
                    "fob_usd": float(fob), "peso_neto_kg": float(kg),
                })

filas.sort(key=lambda f: (f["anio"], f["rubro_cod"], f["pais_cod"]))
campos = ["provincia", "anio", "gran_rubro", "rubro_cod", "rubro", "confidencial",
          "pais_cod", "pais_destino", "fob_usd", "peso_neto_kg"]
with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=campos)
    w.writeheader()
    w.writerows(filas)
print(len(filas), "filas")
```

## 4. Verificar antes de dar por buena la actualización

- **Control cruzado obligatorio:** sumar el FOB de **todas** las provincias del `.xlsb` para el año
  nuevo y comparar contra el `Total FOB(USD)` que declara `etotna{aa}.csv` (viene en el mismo `.zip`).
  Deben coincidir salvo redondeo. En 2025 la diferencia fue de 0,98 USD sobre 87.111 M.
- Que `CMES` valga `12` en todas las filas (base anual acumulada; si aparecen otros meses, se
  descargó la modalidad Mensual por error).
- Que ningún `rubro_cod` quede sin `gran_rubro` (código con primer dígito distinto de 1–4).
- Que las celdas FOB/KG lleguen todas como número (en la base provincial no debería aparecer el
  marcador `s` de secreto estadístico).
- Recalcular el **% confidencial** por año y actualizarlo en la metodología: viene creciendo
  (33,5 % en 2021 → 43,4 % en 2025) y condiciona cualquier lectura por producto.
