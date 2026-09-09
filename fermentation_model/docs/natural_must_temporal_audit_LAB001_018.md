# Auditoría temporal y de condiciones iniciales — mosto natural LAB001–LAB018 (campaña 2026)

**Documento de auditoría de solo lectura. Versión 1, 2026-09-09.**

Alcance: reconstrucción de la historia temporal del mosto natural a través de los experimentos
de laboratorio LAB001–LAB018 del repositorio, con foco en (a) trazabilidad temporal real
(fechas de experimento, inoculación, primera química), (b) condiciones iniciales (ICs) medidas
vs. usadas por el pipeline, (c) semántica de t=0 por grupo, (d) evidencia de deriva temporal
del mosto (G, F, YAN/N, E, Gly), y (e) procedencia de las ICs en el código.

Esta auditoría **no recalibra nada, no modifica modelos, notebooks, datasets ni resultados**.
Único artefacto creado: este archivo. Base de la auditoría: contenido verificado de archivos
del repositorio (workbooks, CSVs, ICS, logs de sensores, código, resultados versionados),
no nombres de archivo ni memoria.

Convención de evidencia (sección transversal, FASE 9):

- **[HECHO VERIFICADO]** — demostrado directamente por archivo/código/dato del repositorio (se cita fuente).
- **[INFERENCIA FUERTE]** — no escrito directamente, pero apoyado por ≥2 fuentes independientes del repositorio.
- **[INTERPRETACIÓN]** — lectura razonada de los datos; no es medición.
- **[NO DOCUMENTADO]** — no existe respaldo suficiente en el repositorio.
- **[CONFLICTO]** — dos fuentes del repositorio dan información incompatible.

Clasificación de ICs: **MEDIDO** (existe medición en la fuente primaria), **DERIVADO**
calculado desde mediciones con regla documentada), **HEREDADO** (toma la medición de otro
LAB), **FALLBACK** (constante por defecto del código), **ESCENARIO** (valor pre-declarado de
sensibilidad), **NO DOCUMENTADO** (sin trazabilidad en el repositorio).

Premisa externa declarada por el solicitante (no verificable contra el repositorio; ver §1.4):
todos los LAB de mosto natural provienen del **mismo mosto madre**. El repositorio solo
documenta explícitamente el vínculo "mismo mosto" entre LAB013–LAB015 (triplicado) y entre
LAB016–LAB018 y LAB013–LAB015 (ICs heredadas). Para LAB001–LAB012 el repositorio usa etiquetas
de lote distintas (Lote 1, Lote 2, Mayo T1) **sin** declaración de mosto madre común
[NO DOCUMENTADO en el repo; la premisa externa es consistente con la química inicial similar,
ver TABLA C, pero no trazable].

---

## 0. Resumen ejecutivo

1. **Los 18 LAB existen y fueron auditados**: LAB001–LAB003 (marzo), LAB004–LAB012 (abril–mayo),
   LAB013–LAB015 (agosto), LAB016–LAB018 (septiembre). Química inicial medida existe para 15 de
   18; LAB016–LAB018 no tienen química Y15 alguna (ICs heredadas de LAB013/014/015).
2. **La química inicial es notablemente estacionaria en ~5 meses**: G0+F0 ≈ 152±5 g/L,
   YAN0 ≈ 220–249 mg/L, E0 ≈ 1.1–1.5 % v/v (9.0–11.8 g/L), Gly0 ≈ 0.75–1.27 g/L. **No se
   encuentra deriva temporal monotónica convincente** dentro de la dispersión analítica
   (§4). El mayor scatter está dentro de triplicados simultáneos (LAB004–006: GF 145.9–165.7),
   es decir, es variabilidad analítica/muestreo, no temporal.
3. **E0 ≠ 0 está medido, no asumido**: todas las fermentaciones con Alcolyzer en t≈0
   (LAB001–LAB012) muestran alcohol pre-existente ~1.2 % v/v. **No hay evidencia de aumento
   progresivo de E0 con el tiempo** (marzo 1.14–1.26 → mayo 1.18–1.19 % v/v): el alcohol
   preexistente es una propiedad estable del mosto, no una fermentación espontánea acumulativa
   observable entre marzo y mayo [INTERPRETACIÓN].
4. **Semántica de t0 heterogénea** (TABLA D): LAB004–LAB006 t0 = siembra del workbook
   (hora interna conflictiva); LAB007–LAB009 t0 = primera muestra (coincide con siembra según
   ICS); LAB010–LAB012 t0 = primera muestra en las hojas que consume el modelo (pero t0 =
   siembra en `Datos_homologados` — conflicto de 5 h dentro del mismo workbook); LAB013–LAB015
   t0 = proxy primera muestra (hora de inoculación no documentada); LAB016–LAB018 t0 = fin del
   pulso de inoculación medido en log [el único t0 físicamente anclado].
5. **Conflictos documentados** (§2.6): hora de siembra de LAB004–006 (3 fuentes, 10:00/13:00/15:30),
   siembra de LAB007–009 desalineada 23 días entre workbook e ICS, doble grilla temporal para
   LAB010–012, E0 de LAB010–012 presente solo en hojas LAB* sin fuente en `Resultados_primarios`,
   y E0=0 forzado para LAB013–018 pese al valor medido ~1.2 % v/v del mismo mosto en LAB001–012.
6. **No existe documentación del mosto madre**: ni fecha de vendimia, ni método/T de
   conservación, ni tratamiento (SO2 etc.), ni tiempo de almacenamiento desde obtención
   [NO DOCUMENTADO]. Solo pueden calcularse intervalos *entre* experimentos bajo la premisa
   externa de mosto único.

---

## 1. FASE 1 — Inventario

### 1.1 Universo auditado y clasificación

| Grupo | LAB | Medio | Fuente de datos química | Estado en el pipeline |
|---|---|---|---|---|
| Vendimia 2026, Lote 1 | LAB001–LAB003 | mosto natural Sauvignon blanc | `data/Piloto 2026/Lotes1a3/raw/Planilla_Maestra_ID_2026_14_07_26.xlsx`, hoja `06_Resultados_primarios` [HECHO VERIFICADO] | **Excluidos del modelo** (`EXCLUDED_BATCHES`, `run_co2_matrix_cross_validation_2026.py:81–85`: "discarded: unreliable CO2 implementation/profile"); sin dataset homologado |
| Transferibilidad, Lote 2 | LAB004–LAB006 | mosto natural | `data/Laboratorio 2026/Vendimia_2026/mosto_natural_xthiol.xlsx` (hojas `LAB004..LAB006`, `Resultados_primarios`, `Eventos_operacion`) | Calibración θ_natural + capa CO2 |
| Transferibilidad, sin registro Maestro | LAB007–LAB009 | mosto natural | ídem (hojas `LAB007..LAB009`) | θ_natural sí; excluidos de capa CO2 (LAB009) o usados (LAB007/008) |
| Transferibilidad, Mayo T1 | LAB010–LAB012 | mosto natural | ídem (hojas `LAB010..LAB012`) | θ_natural + capa CO2 (LAB012 = holdout de matriz) |
| mem2026, triplicado 16 °C | LAB013–LAB015 | mosto natural | `data/mem2026/LAB013-015/` (Y15, OCULYZE, offline) | Sin calibración; diagnóstico (notebook lab013_015) |
| mem2026, triplicado 20 °C | LAB016–LAB018 | mosto natural | `data/mem2026/LAB016-018/` (offline **sin química**; CO2/T confiables) | Holdout externo congelado |

Otros "LAB" presentes en `data/mem2026/` y **fuera del alcance principal** (reportados, no
auditados en profundidad): `LAB090226` (pruebas de agua/ruido del sistema de sensores, carpeta
`prueba_agua_noise`), `LAB290226` (contexto térmico secundario, "medio no documentado" según
`docs/natural_must_model_calibration_and_estimator_readiness_2026.md` §8.7). Ambos usan la
misma familia de loggers pero no son fermentaciones del mosto madre o su medio no está
documentado. `MULT_F1–F3.csv` (julio 2026, `data/Multiplicador 2026/`) es una campaña
"Multiplicador" separada. Advertencia de namespace: los `DOE26-LAB001/002/003` de junio 2026
(`MBDoE_2026/DOE_Lote_1`) son **sintéticos** y no corresponden a los LAB001–003 de marzo.

### 1.2 Inventario de archivos con contenido temporal/químico por LAB

Fuentes primarias (verificadas por contenido, no por nombre):

| Tipo | Archivo | Contenido | LABs |
|---|---|---|---|
| Química marzo | `data/Piloto 2026/Lotes1a3/raw/Planilla_Maestra_ID_2026_14_07_26.xlsx` (`02_Maestro_ensayos`, `03_Eventos_operacion`, `04_Muestreo_MEF`, `06/07_Resultados_*`) | fechas inoculación/siembra; muestras L-01..L-15; G/F/PAN/amonio/Gly/Alcolyzer/Oculyze/densidad/Brix | 001–003 |
| Química abril–mayo | `data/Laboratorio 2026/Vendimia_2026/mosto_natural_xthiol.xlsx` (`00_Resumen`, `Maestro_ensayos`, `Eventos_operacion`, `Muestreo_MEF`, `Resultados_primarios`, `Resultados_extendidos`, `LAB004..LAB012`, `Datos_homologados`, `Perfiles_temperatura`, `Diccionario_mapeo`) | siembras, pulsos, química completa homologada, t por muestra, YAN calculado | 004–012 |
| Calendario | `data/Laboratorio 2026/raw_data/Fernanda Folch.ics` (115 eventos) | siembras/pulsos/muestreos con fecha-hora UTC (TZ America/Santiago) | 001–012 (DOE26 sintéticos también) |
| Loggers marzo | `raw_data/ing26_lab00{1,2,3}.csv`, `lab00{1,2,3}_{T,co2,co2f}_pt2.csv`, `CO2_lab00{1,2,3}_*_1700.csv`, `{CO2_FILT_,CO2_,Temp_F*}_lab00{1,2,3}*pt3.csv`, `Desktop_CyT_Tablero_Proceso/*lab00{1,2,3}*` | T/SP/nutricion_activa (desde 2026-03-25 18:35); CO2 (recuperable solo desde 2026-03-28/29) | 001–003 |
| Loggers abril–mayo | `raw_data/{CO2,Temp}_F*_LAB00{4,5,6}_PT2.csv` + `Desktop_CyT_Tablero_Proceso/{CO2,Temp}_F*_lab00{4,5,6}.csv` (parte 1) y `raw_data/*lab00{7,8,9}*.csv`, `raw_data/*lab0{10,11,12}*.csv` (+`_PT2`) | CO2 + T con `nutricion_activa` | 004–012 |
| Química agosto | `data/mem2026/LAB013-015/`: `Y15_LAB013-015.csv/.txt`, `LAB013-LAB015-offline-measurements.csv/.xlsx`, `LAB013-LAB015-offline-combined.csv`, `LAB01{3,4,5}_OCULYZE/report.csv`, `Temp/CO2_F*_LAB01{3,4,5}*.csv`, `backup_global_ph_rtd.csv` | Y15 con fecha-hora absoluta (PI + muestras 2–8); offline (Brix/dens/DO/CO2 disuelto, 10 muestras); Oculyze 9/LAB; loggers desde 2026-08-18 11:20 | 013–015 |
| Offline septiembre | `data/mem2026/LAB016-018/`: `LAB016-018-offline-measurements.csv/.xlsx` (hojas `MedicionesOffline`, `Experimentos`, `CondicionesIniciales`), `LAB01{6,7,8}_OCULYZE/report.csv`, `{Temp,CO2}*.csv`, `*_inoculation_aligned.csv` | Brix/dens/T/volumen (8 muestras/LAB, sin química); t0 en `Experimentos.Notas`; ICs heredadas en `CondicionesIniciales` | 016–018 |
| ICs usadas por el ajuste | `laboratory_2026/results/estimability_historical_natural/batch_summary.csv` | X0/Xd0/N0/G0/F0/E0/Gly0 por batch LAB004–012 | 004–012 |
| Documentación | `docs/natural_must_model_calibration_and_estimator_readiness_2026.md` (v3 2026-09-08); `laboratory_2026/notebooks/lab013_015_*.ipynb`, `lab016_018_natural_must_holdout.ipynb`, `lab016_018_co2_temperature_visualization.ipynb` | t0, ICs, herencias, fallbacks | todos |

### 1.3 Zona horaria de los loggers

[INFERENCIA FUERTE] Los timestamps de los loggers son **hora local de Santiago**: (a) el
evento de nutrición de LAB016–018 a +56.93 h de t0 = 2026-09-01 00:03:55 cae en 2026-09-03
~08:59 local (horario laboral plausible), no así bajo interpretación UTC (≈04:59); (b) los
nombres `CO2_lab001_28_03_26_1700.csv` coinciden con descargas al final de jornada; (c) el ICS
(UTC) al convertir a local alinea muestreos 11:00Z/19:00Z con 08:00/16:00 locales, coherente
con la grilla de muestreo del workbook. Se usa hora local en todo este documento; el ICS se
cita convertido.

### 1.4 Mosto madre y su conservación

- [HECHO VERIFICADO] Variedad documentada: Sauvignon blanc (`Maestro_ensayos` LAB004+;
  `Experimentos.Variedad_Mosto` LAB016–018). Cepa: *S. cerevisiae* Zymaflore X5 (LAB001–012);
  LAB016–018 registran solo "Saccharomyces cerevisiae".
- [HECHO VERIFICADO] "Mismo mosto" explícito solo en: README del xlsx LAB013–015 ("un
  triplicado realizado con mosto natural") y en la hoja `CondicionesIniciales` de LAB016–018
  ("Condición inicial heredada del mismo mosto: promedio de las primeras muestras de reactor
  LAB013-2, LAB014-2 y LAB015-2; ... Las muestras PI corresponden al pre-inóculo y fueron
  excluidas").
- [NO DOCUMENTADO] Vínculo de mosto entre {LAB001–003}, {LAB004–012} y {LAB013–018}: el repo
  usa lotes con nombre distinto (Lote 1 / Lote 2 / sin nombre / Mayo T1 / vacío) y no declara
  un mosto madre común. La premisa externa del solicitante es compatible con la TABLA C pero
  no trazable desde el repositorio.
- [NO DOCUMENTADO] Fecha de vendimia/obtención del mosto madre; método de conservación
  (congelado/refrigerado/estabilizado); temperatura de almacenamiento; tratamientos previos
  (p. ej. SO2). Búsquedas en docs/history/código de `congel|freez|SO2|sulfit|refrig|almacen`
  aplicadas al mosto: sin resultados ("congelado" aparece solo referido a
  modelo/parámetros/protocolos; el único SO2 medido es `LAB013-7-SO2 FREE SULFITE 7,20 mg/L`
  el 20-08, intra-fermentación). Los "Freezer −20/−80 °C" de `Resultados_extendidos` se
  refieren a conservación de **muestras** post-experimento, no del mosto.
- [NO DOCUMENTADO] `Lote_Mosto` y `Volumen_Inicial_L` en el xlsx LAB016–018: columnas vacías.

---

## 2. FASE 2 — Reconstrucción temporal por LAB

### 2.1 LAB001–LAB003 (Lote 1, marzo)

[HECHO VERIFICADO] Inoculación (siembra) ejecutada **2026-03-25 18:00**:
`03_Eventos_operacion` registra el evento "Siembra" con fecha-hora planificada
2026-03-25 16:00 y "Fecha de ejecución" 2026-03-25 18:00; `02_Maestro_ensayos` declara
"Fecha inoculación 2026-03-25", "Hora inoculación 6:00 PM". Coherente con el inicio del log
térmico (2026-03-25 18:35:24/18:40:56/18:41:11 para F1/F2/F3) y con que la muestra L-01
(16:00) tenga hito "Pre-inóculo" en `04_Muestreo_MEF`. El ICS no tiene evento de siembra para
LAB001–003; sus "Muestreo corta" comienzan 2026-03-26 08:00 local (L-02).

- Primera química: **L-01 2026-03-25 16:00** (= 2 h **antes** de la inoculación).
  Δt_química−inoculación = **−2 h** [HECHO VERIFICADO].
- CO2: registros útiles solo desde 2026-03-28/29 (~71+ h post-inoculación); calificado de no
  confiable y excluido (`excluded_experiments.csv`: "discarded: unreliable CO2
  implementation/profile").
- Loggers térmicos: 2026-03-25 18:35 → 2026-04-01 09:16 (en 3 partes).

### 2.2 LAB004–LAB006 (Lote 2, abril)

[HECHO VERIFICADO] Fecha de siembra **2026-04-06** en tres fuentes independientes
(`Eventos_operacion` serial Excel 46120; ICS "Siembra" 2026-04-06 19:30Z; primera química
04-06). [CONFLICTO] la **hora**: (a) columna `Hora` = 0.4167 → 10:00; (b) columna
`Fecha-hora` = 13:00 (la usada por la homologación, t=0); (c) ICS 19:30Z = 15:30 local.
[INFERENCIA FUERTE] el logger contradice (a) y (c): la parte 1 del tablero
(`Desktop_CyT_Tablero_Proceso/Temp_F1_lab004.csv`) arranca 2026-04-06 14:46:13 con
`nutricion_activa=1` en F1 (pulso de inoculación ya activo o recién hecho) y F2 evoluciona un
transitorio de CO2 (6.0 sccm a las 14:47, decayendo a 0.85 en 30 min). La siembra real quedó
acotada entre ~13:00 y 14:46 local.

- Primera química: muestra `-01` fechada 2026-04-06 13:00, asignada a **t=0** por la
  homologación (regla "t = horas desde siembra"; hito de plan "Pre-inóculo"). Δt_química−
  inoculación = **0 h por construcción** (incertidumbre real ±2 h dada la conflictiva de hora).
  Nota: `Muestreo_MEF` había **planificado** `-01` a las 15:00 (t=2); el registro de resultados
  la sitúa en 13:00 (t=0) [CONFLICTO menor, plan vs. registro].
- Corrección de fechas documentada: `00_Resumen` — "Se corrigieron fechas serializadas como
  mm/dd a dd/mm para mantener la cinética abril 2026 y t coherente con siembra" (p. ej. la
  fila original "2026-06-04 13:00" = 06/04 dd/mm ↔ mm/dd).
- Loggers: parte 1 (Desktop) 2026-04-06 14:46 → 04-07 07:13; parte 2 (`*_PT2`) 04-07 08:22 →
  04-14/15. Es decir, la serie completa de logger **comienza 1.8–2 h después de la siembra**
  y no registra la ventana pre-inoculación (hueco 07:13→08:22 de ~1.2 h).
- Nutrición: pulso 1 (Springferm Xtrem 1.00 g + FDA 0.40 g) **en la inoculación** (t=0,
  "aplicar 50% del suplemento total al inóculo"); pulso 2 a densidad 1040 (t=51/51/75 h).

### 2.3 LAB007–LAB009 (abril, sin registro en Maestro/Muestreo_MEF)

[CONFLICTO mayor] `Eventos_operacion` fecha la siembra de LAB007–009 el **2026-03-25 16:00**
(= 23 días antes), lo cual la propia homologación declara desalineado (`00_Resumen`: "siembra
de Eventos está desalineada, por lo que t=0 se fija en primer muestreo"). El ICS registra
"Siembra" para los tres el **2026-04-17 20:00Z = 16:00 local**, con pulso nutricional 1
simultáneo y pulso 2 el 19-04. Las "Fechas de ejecución" de las filas de eventos de LAB007–009
(abril 19–20) y la química completa (16:00 del 17-04 → 08:00 del 24-04) confirman la ejecución
en abril [INFERENCIA FUERTE: ejecución real 2026-04-17; la fecha de marzo de Eventos es
espuria].

- Primera química: `L-01` **2026-04-17 16:00 = t=0** (regla primer muestreo). Si la siembra
  fue 16:00 (ICS), Δt_química−inoculación ≈ **0 h** [INFERENCIA FUERTE].
- Loggers: 2026-04-17 11:20–11:21 → 04-24 09:37, es decir **~4.6 h antes** de la
  inoculación. [HECHO OBSERVADO] en esa ventana pre-inoculación F1 = 0.0000 sccm pero F2 =
  0.88 y F3 = 0.86 sccm, planos (sin crecimiento) hasta ~8 h post-inoculación (F2 LAB008:
  0.75–0.92 sccm entre 11:21 y 23:00 del 17-04).
- Sin registro en `Maestro_ensayos` ni `Muestreo_MEF` [HECHO VERIFICADO, `00_Resumen`].

### 2.4 LAB010–LAB012 (Mayo T1, 12 de mayo)

[HECHO VERIFICADO] Fecha de siembra **2026-05-12** (`Maestro_ensayos`: "Fecha inoculación
2026-05-12"; `Eventos_operacion` serial 46154; ICS "Siembra" 2026-05-12). [CONFLICTO] hora:
(a) workbook 10:00 (Hora 0.4167 y Fecha-hora 10:00; grilla de `Datos_homologados` anclada
ahí, L-01 a t=5 h); (b) ICS 18:45Z/19:15Z/19:45Z = **14:45/15:15/15:45 local** para
LAB010/011/012. [INFERENCIA FUERTE] favorece la ventana ~15:00: la primera química es del
12-05 15:00 y los loggers parte 1 arrancan 16:13–16:15 (0.5–1.5 h después del ICS, 6 h
después del workbook, lo que dejaría 6 h de fermentación sin logging); además los perfiles SP
de la parte 1 coinciden con los protocolos (15/18/15 °C).

- Primera química: `L-01` **2026-05-12 15:00**. Δt_química−inoculación = **0 h** en la
  grilla de las hojas `LAB010..LAB012` (que anclan t=0 en esa muestra; L-01 t=0) pero
  **+5 h** en `Datos_homologados`/`00_Resumen` (t0 = siembra 10:00). [CONFLICTO interno del
  workbook; el modelo consume las hojas LAB* — ver FASE 5/6].
- [HECHO OBSERVADO] a pocos minutos de iniciado el logger (0.5–1.5 h post-inoculación ICS):
  F1 0.087, F2 0.98, F3 0.59 sccm — CO2 medible casi inmediato (inóculo de biomasa alta,
  X0 ≈ 0.85–1.07 kg/m³, y/o desgasificación).
- Nutrición: "Viniliquid (Fermentis) 4 mL — Aportamos 80 ppm YAN" **en la inoculación**
  ("Corrección inicial", t=0) y de nuevo a "Corrección 1040" (t=72–84 h).
- Loggers: parte 1 05-12 16:13 → 05-13 11:59; parte 2 05-13 14:38 → 05-22 09:20 (hueco 2.7 h).

### 2.5 LAB013–LAB015 (agosto, SP 16 °C)

[HECHO VERIFICADO] Ventana de ejecución 18–26 agosto 2026 (sensores 2026-08-18 11:20 →
08-26 10:00; muestreo offline 18–24 agosto). [NO DOCUMENTADO] la **hora de inoculación**: el
CSV offline declara `time_h` vacío "porque el t=0 exacto aún no está definido en este
archivo" (README del xlsx); el doc oficial la declara pendiente.

- Cronología del 18-08 [HECHO VERIFICADO]: muestra offline `-1` a las 10:00 (Brix/dens/DO/CO2
  disuelto); **muestra PI (pre-inóculo) Y15 a las 11:05–11:08**; loggers desde 11:20–11:22
  (`nutricion_activa`=0 en toda la serie → sin eventos de bomba); primera química dinámica
  (muestra `-2`) a las 13:12–13:16. La inoculación quedó entre ~11:08 y ~13:13 (después del
  PI por definición; los sensores parten ~11:20). t0 proxy del notebook lab013_015 =
  **muestra `-1` 10:00**, es decir, probablemente 1–3 h **antes** de la inoculación real.
- Primera química relevante para ICs: **PI 11:05** (pre-inóculo) y dinámica 13:13.
  Δt_química(PI)−inoculación ≈ −0…−2 h [INFERENCIA FUERTE].
- Anomalía de datos: LAB013-PI→LAB013-2 cae G 75.62→71.13 y GF 154.65→146.6 en ~2.1 h
  (LAB014/015 ±1 g/L); se reporta como outlier de muestreo/medición sin explicación
  documentada.

### 2.6 LAB016–LAB018 (septiembre, SP 20 °C)

[HECHO VERIFICADO] **t0 = fin del pulso de inoculación según el log**:
`LAB016-018-offline-measurements.xlsx` → hoja `Experimentos`, campo `Notas`: "Inoculación
(log nutricion_activa): inicio 2026-09-01 00:00:03, fin (t0) 2026-09-01 00:03:55" (LAB017:
00:00:04→00:04:00; LAB018: 00:00:01→00:04:07). Verificado contra el flanco de caída de
`nutricion_activa` (notebook de visualización: "inoculation start/end (t0)/duration 232/236/246 s").
Los archivos `*_inoculation_aligned.csv` reanclan CO2/T a ese t0 (el logging arranca
2026-08-31 17:16–17:17, ~6.8 h **antes** de t0; first CO2 0.227 sccm).

- **No existe química Y15** (G/F/YAN/Gly/E) de LAB016–018 en el repositorio [HECHO
  VERIFICADO]; offline = Brix/densidad/temperatura/volumen en 8 muestras (primera
  2026-09-01 09:00 = +8.9 h post-t0). Por tanto no hay "primera química" propia: las ICs
  químicas se **heredan** de LAB013-2/014-2/015-2 (2026-08-18 13:13, 14 días antes).
- Nutrición: eventos de bomba a +56.93 h (LAB016/018) y +56.93/+57.13 h (LAB017);
  dosis/composición no documentadas [PENDIENTE según doc oficial].

### 2.7 TABLA A — Trazabilidad temporal por LAB

Δt_q−i = t_primera_química − t_inoculación (negativo = química anterior a inoculación).
"Días" = desde LAB001 (2026-03-25), computable solo bajo premisa de mosto único.

| LAB | Fecha experimento | Inoculación (fecha-hora local) | Fuente inoculación | Primera química (fecha-hora) | Δt_q−i | Almacenamiento conocido | Conservación | T alm. | Confianza | Observaciones |
|---|---|---|---|---|---|---|---|---|---|---|
| 001 | 2026-03-25→04-01 | 2026-03-25 18:00 | Planilla Maestra `03_Eventos_operacion` ("Fecha de ejecución"); Maestro hora 18:00 | L-01 2026-03-25 16:00 | −2 h | 0 d (referencia) | NO DOCUMENTADO | NO DOCUMENTADO | Alta (fecha/hora); media (química pre-inóculo) | L-01 es pre-inóculo; CO2 no confiable |
| 002 | 2026-03-25→04-01 | 2026-03-25 18:00 | ídem | L-01 2026-03-25 16:00 | −2 h | 0 d | NO DOCUMENTADO | NO DOCUMENTADO | Alta | ídem |
| 003 | 2026-03-25→04-01 | 2026-03-25 18:00 | ídem | L-01 2026-03-25 16:00 | −2 h | 0 d | NO DOCUMENTADO | NO DOCUMENTADO | Alta | ídem |
| 004 | 2026-04-06→04-14 | 2026-04-06, hora en conflicto (10:00/13:00/15:30); probable 13:00–14:46 | `Eventos_operacion` (13:00); ICS 15:30; logger acota ≤14:46 | `-01` 2026-04-06 13:00 (t=0) | 0 h (por construcción; ±2 h real) | +12 d | NO DOCUMENTADO | NO DOCUMENTADO | Media (hora) / alta (fecha) | Muestra t=0 con hito "Pre-inóculo"; pulso N en inoculación |
| 005 | 2026-04-06→04-14 | ídem LAB004 | ídem | `-01` 2026-04-06 13:00 (t=0) | 0 h (±2 h) | +12 d | NO DOCUMENTADO | NO DOCUMENTADO | Media | F2 con transitorio 6→0.85 sccm a la hora de siembra |
| 006 | 2026-04-06→04-15 | ídem LAB004 | ídem | `-01` 2026-04-06 13:00 (t=0) | 0 h (±2 h) | +12 d | NO DOCUMENTADO | NO DOCUMENTADO | Media | — |
| 007 | 2026-04-17→04-24 | 2026-04-17 16:00 | ICS 20:00Z=16:00 local; workbook Eventos dice 03-25 (desalineada, descartada por homologación) | `L-01` 2026-04-17 16:00 (t=0) | ≈0 h | +23 d | NO DOCUMENTADO | NO DOCUMENTADO | Media-alta (vía ICS + química) | t0 definido como primer muestreo; F2/F3 con ~0.87 sccm planos 4.6 h pre-inoculación |
| 008 | 2026-04-17→04-24 | 2026-04-17 16:00 | ídem | `L-01` 2026-04-17 16:00 (t=0) | ≈0 h | +23 d | NO DOCUMENTADO | NO DOCUMENTADO | Media-alta | ídem |
| 009 | 2026-04-17→04-24 | 2026-04-17 16:00 | ídem | `L-01` 2026-04-17 16:00 (t=0) | ≈0 h | +23 d | NO DOCUMENTADO | NO DOCUMENTADO | Media-alta | ídem |
| 010 | 2026-05-12→05-20 | 2026-05-12, conflicto 10:00 (workbook) vs 14:45 (ICS); logger 16:13 | `Eventos_operacion` 10:00; ICS 14:45 | `L-01` 2026-05-12 15:00 | 0 h (hojas LAB*) / +5 h (Datos_homologados) | +48 d | NO DOCUMENTADO | NO DOCUMENTADO | Media | Doble anclaje t0 dentro del workbook; E0 solo en hoja LAB010 |
| 011 | 2026-05-12→05-19 | 2026-05-12 10:00 vs 15:15 (ICS) | ídem | `L-01` 2026-05-12 15:00 | 0 / +5 h | +48 d | NO DOCUMENTADO | NO DOCUMENTADO | Media | ídem |
| 012 | 2026-05-12→05-19 | 2026-05-12 10:00 vs 15:45 (ICS) | ídem | `L-01` 2026-05-12 15:00 | 0 / +5 h | +48 d | NO DOCUMENTADO | NO DOCUMENTADO | Media | ídem |
| 013 | 2026-08-18→08-26 | No documentada (entre ~11:08 y ~13:13 del 18-08) | Inferencia (PI 11:05 pre-inóculo; sensores 11:20; química dinámica 13:13) | PI 2026-08-18 11:05 (pre-inóculo); dinámica 13:12 | ≈ −0…−2 h (PI) | +146 d | NO DOCUMENTADO | NO DOCUMENTADO | Baja (t0) / alta (química PI) | t0 proxy = muestra `-1` 10:00 (anterior a la inoculación); time_h vacío por diseño |
| 014 | 2026-08-18→08-26 | ídem | ídem | PI 11:06; dinámica 13:13 | ≈ −0…−2 h | +146 d | NO DOCUMENTADO | NO DOCUMENTADO | Baja (t0) | ídem |
| 015 | 2026-08-18→08-26 | ídem | ídem | PI 11:08; dinámica 13:16 | ≈ −0…−2 h | +146 d | NO DOCUMENTADO | NO DOCUMENTADO | Baja (t0) | ídem |
| 016 | 2026-09-01→09-07 | **2026-09-01 00:03:55** (fin pulso; inicio 00:00:03) | xlsx `Experimentos.Notas` + flanco `nutricion_activa` + notebooks | **Sin química**; offline (Brix/dens) 09:00 (+8.9 h); ICs heredadas de LAB013/14/15-2 (14 d antes) | n/a | +160 d | NO DOCUMENTADO | NO DOCUMENTADO | Alta (t0); n/a (química) | Primer y único grupo con t0 físicamente medido |
| 017 | 2026-09-01→09-07 | **2026-09-01 00:04:00** (inicio 00:00:04) | ídem | ídem | n/a | +160 d | NO DOCUMENTADO | NO DOCUMENTADO | Alta (t0) | ídem |
| 018 | 2026-09-01→09-07 | **2026-09-01 00:04:07** (inicio 00:00:01) | ídem | ídem | n/a | +160 d | NO DOCUMENTADO | NO DOCUMENTADO | Alta (t0) | ídem |

---

## 3. FASE 3 — Condiciones iniciales por LAB

### 3.1 Fuente de cada valor

- **LAB001–003**: `Planilla_Maestra_ID_2026_14_07_26.xlsx` → `06_Resultados_primarios`, filas
  `ING26-LAB00x-L-01` (16:00, pre-inóculo). YAN0 calculado aquí como PAN + 0.82×Amonio
  (fórmula documentada en el workbook xthiol; no es columna de la Planilla). E0 = `Cf
  Alcolyzer Real`. X0: no hay conversión homologada para marzo (semántica de la columna
  Viability de la Planilla no homologada) → se listan los proxies crudos Oculyze.
- **LAB004–012**: workbook xthiol → hoja `LABxxx` fila t=0 (química Y15/Alcolyzer/Oculyze
  homologadas; `Diccionario_mapeo`: YAN = PAN + 0.82×Amonio; ETANOL = Alcolyzer Real). E0 en
  g/L = %v/v × 7.8924 (`ETHANOL_G_L_PER_PERCENT_VV`, loader :53–54) — reproducido exactamente
  en `batch_summary.csv`. X0 = concentración viable Oculyze (Mcél/mL) × 0.03 kg/m³
  (`MILLION_CELLS_ML_TO_KG_M3`, 30 pg/célula, loader :55–57).
- **LAB013–015**: `Y15_LAB013-015.csv` fila `-PI` (el Y15 reporta YAN directo; verificado
  PAN + 0.82×ammonia ≈ YAN). ICs usadas en notebook lab013_015 (celda 16): N/G/F/Gly del PI;
  X=0.45, Xd=0, E=0 fijos.
- **LAB016–018**: xlsx → hoja `CondicionesIniciales`: G0/F0/YAN0/Gly0 heredados = promedio de
  LAB013-2/014-2/015-2 (verificado aritméticamente: 71.13/75.67/75.36 → 74.05;
  75.47/80.13/77.58 → 77.73; 237/246/250 → 244.33; 1.13/1.15/1.14 → 1.14); X0=0.45, Xd0=0
  fallback; E0 por escenario (A: 0; B: mediana histórica 9.707652 g/L).

### 3.2 TABLA B — Condiciones iniciales (mejor dato disponible y tipo de fuente)

E0 en g/L (factor 7.8924). YAN0/N0: YAN [mg N/L] → N [kg/m³] = YAN×10⁻³ (regla del pipeline).
"Modelo" = valor que consume el pipeline actual (LAB004–012: batch_summary; LAB013–015:
notebook lab013_015; LAB016–018: notebook holdout).

| LAB | G0 [g/L] | F0 [g/L] | YAN0 [mg/L] | N0 [kg/m³] | E0 [% v/v] | E0 [g/L] | Gly0 [g/L] | X0 [kg/m³] | Xd0 [kg/m³] | Tipos de fuente (G/F/YAN/E/Gly/X/Xd) |
|---|---|---|---|---|---|---|---|---|---|---|
| 001 | 81.17 | 78.97 | 232.22* | 0.23222* | 1.14 | 9.00 | 0.93 | n/h (proxy Oculyze Conc 15.71, Viab 11.29) | n/h | MEDIDO/MEDIDO/DERIVADO*/MEDIDO/MEDIDO/NO DOCUMENTADO/NO DOCUMENTADO (*cálculo auditoría, fórmula 0.82 documentada en repo) |
| 002 | 81.18 | 76.95 | 241.32* | 0.24132* | 1.26 | 9.94 | 0.96 | n/h (14.44/10.71) | n/h | ídem |
| 003 | 78.44 | 77.12 | 238.86* | 0.23886* | 1.17 | 9.23 | 0.97 | n/h (17.17/12.44) | n/h | ídem |
| 004 | 75.04 | 70.81 | 230.76 | 0.23076 | 1.23 | 9.71 | 0.99 | 0.394 | 0.009 | MEDIDO (Y15, t=0)/MEDIDO/MEDIDO (YAN wb)/MEDIDO (Alcolyzer Real t=0)/MEDIDO/MEDIDO (Oculyze)/MEDIDO (Oculyze resta) |
| 005 | 77.71 | 87.95 | 227.30 | 0.22730 | 1.24 | 9.79 | 1.09 | 0.493 | 0.016 | ídem |
| 006 | 81.63 | 75.81 | 229.12 | 0.22912 | 1.25 | 9.87 | 1.17 | 0.099 | 0.028 | ídem |
| 007 | 77.52 | 74.55 | 239.04 | 0.23904 | 1.49 | 11.76 | 0.89 | 0.292 | 0.001 | ídem |
| 008 | 76.21 | 74.89 | 239.22 | 0.23922 | 1.17 | 9.23 | 0.85 | 0.254 | 0.003 | ídem |
| 009 | 75.75 | 76.68 | 237.40 | 0.23740 | 1.23 | 9.71 | 0.75 | 0.360 | 0.001 | ídem |
| 010 | 78.49 | 77.05 | 225.70 | 0.22570 | 1.18 | 9.31 | 1.25 | 0.961 | 0.113 | MEDIDO/MEDIDO/MEDIDO/**NO DOCUMENTADO** (solo hoja LAB010, sin fuente en Resultados_primarios)/MEDIDO/MEDIDO/MEDIDO |
| 011 | 75.61 | 76.67 | 220.24 | 0.22024 | 1.18 | 9.31 | 1.25 | 1.066 | 0.038 | ídem |
| 012 | 75.00 | 79.88 | 222.06 | 0.22206 | 1.19 | 9.39 | 1.27 | 0.851 | 0.121 | ídem |
| 013 | 75.62 (PI) | 79.03 (PI) | 249 (PI) | 0.249 (modelo) | — no medido | 0.0 (modelo, E=0 forzado) | 1.15 (PI) | 0.45 (modelo; Oculyze −1 ≈ 0.41) | 0.0 (modelo) | MEDIDO/MEDIDO/MEDIDO (Y15 PI)/**ESCENARIO/FALLBACK** (E=0)/MEDIDO/**FALLBACK** (X=0.45; medición ≈0.41 no usada) |
| 014 | 76.54 (PI) | 80.38 (PI) | 247 (PI) | 0.247 | — | 0.0 | 1.12 | 0.45 (Oculyze ≈0.44) | 0.0 | ídem |
| 015 | 75.32 (PI) | 79.45 (PI) | 246 (PI) | 0.246 | — | 0.0 | 1.12 | 0.45 (Oculyze ≈0.48) | 0.0 | ídem |
| 016 | 74.05 | 77.73 | 244.33 | 0.24433 | — no medido | 0.0 (esc. A) / 9.71 (esc. B) | 1.14 | 0.45 (Oculyze +8.9 h ≈ 0.43) | 0.0 | HEREDADO (promedio LAB013/14/15-2)/HEREDADO/HEREDADO/**ESCENARIO** (A/B)/HEREDADO/**FALLBACK** |
| 017 | 74.05 | 77.73 | 244.33 | 0.24433 | — | 0.0 / 9.71 | 1.14 | 0.45 (Oculyze +8.9 h ≈ 0.24) | 0.0 | ídem |
| 018 | 74.05 | 77.73 | 244.33 | 0.24433 | — | 0.0 / 9.71 | 1.14 | 0.45 (Oculyze +8.9 h ≈ 0.26) | 0.0 | ídem |

Notas TABLA B:
- LAB001–003: valores no consumidos por ningún pipeline (excluidos); X0 no homologado para
  marzo (`n/h`). La semántica Viability→X del loader está definida para el workbook xthiol.
- LAB010–012 E0: la serie ETANOL (1.18/1.18/1.19 % v/v en t=0; 1.28–2.45 % v/v intermedios)
  existe **solo** en las hojas `LAB010..LAB012`; las columnas Alcolyzer de
  `Resultados_primarios`/`Datos_homologados` están vacías para esos LABs → el número entra al
  modelo pero su medición origen no es trazable dentro del workbook [NO DOCUMENTADO].
- LAB013–015: las ICs del notebook usan el PI (pre-inóculo), no la muestra `-1`/`-2`; E=0 es
  asunción del notebook declarada en markdown ("X=0.45 kg/m³, Xd=0, E=0").
- LAB016–018: E0 escenario B = mediana de E0 de LAB004–012 = 9.707652 g/L (notebook holdout,
  celda 9; valores históricos listados allí mismo).

### 3.3 E0 — hecho observado vs interpretación

[HECHO OBSERVADO] El mosto contenía alcohol medible inmediatamente antes/en el instante de
inoculación en **todas** las fermentaciones con Alcolyzer disponible (LAB001–LAB012, marzo a
mayo): 1.14–1.49 % v/v (bruto 1.44–1.79; "Real" corregido ≈ ×0.80–0.83 sistemático, factor de
corrección propio del método). El valor no es cero en ningún caso.

[HECHO OBSERVADO] La señal gaseosa de varios fermentadores F2/F3 es ≠0 horas antes o en el
instante de la inoculación, plana (sin crecimiento): LAB008/009 0.86–0.88 sccm ≥4.6 h
pre-inoculación; LAB005 0.7–0.9 sccm sostenido desde ~1 h post-siembra (tras transitorio
6.0→0.85); LAB011/012 0.5–1.0 sccm a los 0.5–1.5 h post-inoculación. F1 sistemáticamente
≈0 en los mismos instantes.

[INTERPRETACIÓN] El alcohol preexistente y el CO2 pre-inoculación son compatibles con (i)
fermentación espontánea mínima durante el almacenamiento del mosto, (ii) desgasificación de
CO2 disuelto (los CO2 disueltos medidos en agosto son 476–527 mg/L en muestra 1) combinada
con alcohol formado **antes** del primer experimento, o (iii) interferencias/offsets
instrumentales (la asimetría F1=0 vs F2/F3≈0.87 sccm apunta a offsets por sensor). **No
puede distinguirse** con la evidencia del repositorio. Lo que sí acota la evidencia: entre
marzo (E0 1.14–1.26 % v/v) y mayo (1.18–1.19 % v/v) **no hay crecimiento acumulativo de
E0**, y las señales pre-inoculación son planas (no activas): si hubo fermentación espontánea
mínima, no dejó una deriva de E0 medible entre experimentos sucesivos (§4).

---

## 4. FASE 4 — Serie longitudinal del (presunto) mismo mosto madre

### 4.1 TABLA C — Evolución cronológica

Bajo la premisa externa de mosto único (el repositorio no la documenta para todos los grupos,
§1.4). "Días" desde el primer LAB natural (LAB001–003, 2026-03-25). Se usa la **mejor química
cercana a inoculación** de cada LAB (pre-inóculo si existe; t=0 si no). Para LAB016–018 se
muestra la IC heredada (fuente 14 días anterior) entre paréntesis.

| Orden | Fecha | LAB | Días | G0 | F0 | G0+F0 | YAN0 | E0 [% v/v] | Gly0 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-03-25 | 001 | 0 | 81.17 | 78.97 | 160.14 | 232.2 | 1.14 | 0.93 |
| 2 | 2026-03-25 | 002 | 0 | 81.18 | 76.95 | 158.13 | 241.3 | 1.26 | 0.96 |
| 3 | 2026-03-25 | 003 | 0 | 78.44 | 77.12 | 155.56 | 238.9 | 1.17 | 0.97 |
| 4 | 2026-04-06 | 004 | 12 | 75.04 | 70.81 | 145.85 | 230.8 | 1.23 | 0.99 |
| 5 | 2026-04-06 | 005 | 12 | 77.71 | 87.95 | 165.66 | 227.3 | 1.24 | 1.09 |
| 6 | 2026-04-06 | 006 | 12 | 81.63 | 75.81 | 157.44 | 229.1 | 1.25 | 1.17 |
| 7 | 2026-04-17 | 007 | 23 | 77.52 | 74.55 | 152.07 | 239.0 | 1.49 | 0.89 |
| 8 | 2026-04-17 | 008 | 23 | 76.21 | 74.89 | 151.10 | 239.2 | 1.17 | 0.85 |
| 9 | 2026-04-17 | 009 | 23 | 75.75 | 76.68 | 152.43 | 237.4 | 1.23 | 0.75 |
| 10 | 2026-05-12 | 010 | 48 | 78.49 | 77.05 | 155.54 | 225.7 | 1.18 | 1.25 |
| 11 | 2026-05-12 | 011 | 48 | 75.61 | 76.67 | 152.28 | 220.2 | 1.18 | 1.25 |
| 12 | 2026-05-12 | 012 | 48 | 75.00 | 79.88 | 154.88 | 222.1 | 1.19 | 1.27 |
| 13 | 2026-08-18 | 013 | 146 | 75.62 | 79.03 | 154.65 | 249 | — (no medido) | 1.15 |
| 14 | 2026-08-18 | 014 | 146 | 76.54 | 80.38 | 156.92 | 247 | — | 1.12 |
| 15 | 2026-08-18 | 015 | 146 | 75.32 | 79.45 | 154.77 | 246 | — | 1.12 |
| 16 | 2026-09-01 | 016 | 160 | (74.05) | (77.73) | (151.78) | (244.3) | — | (1.14) |
| 17 | 2026-09-01 | 017 | 160 | (74.05) | (77.73) | (151.78) | (244.3) | — | (1.14) |
| 18 | 2026-09-01 | 018 | 160 | (74.05) | (77.73) | (151.78) | (244.3) | — | (1.14) |

Fuente de la química inicial por fila: LAB001–003 → Planilla Maestra (pre-inóculo, −2 h);
LAB004–009 → xthiol t=0 (siembra/primer muestreo); LAB010–012 → xthiol L-01 15:00 (t=0 hojas);
LAB013–015 → Y15 PI (pre-inóculo); LAB016–018 → herencia promedio LAB013/14/15 muestra-2
(13:13 del 18-08). Δt química−inoculación: ver TABLA A.

### 4.2 Análisis de deriva (sin forzar tendencias)

- **G0+F0**: rango total 145.9–165.7 g/L. Excluyendo los outliers del triplicado del 06-04
  (LAB004 145.9, LAB005 165.7 — mismo mosto, misma hora), el resto vive en 151.1–160.1 con
  centro ~153, sin pendiente temporal resolvable (marzo 155.6–160.1; abril-17 151.1–152.4;
  mayo 152.3–155.5; agosto 154.7–156.9; heredado 151.8). [INTERPRETACIÓN] estacionario;
  el scatter entre réplicas simultáneas (hasta ±10 g/L el 06-04) domina cualquier posible
  deriva.
- **YAN0**: 220.2–249.4 mg/L, no monótono (marzo 232–241; 06-04 227–231; 17-04 237–239;
  12-05 220–226; PI agosto 246–249; heredado 244). [INTERPRETACIÓN] sin deriva sistemática;
  oscilación ±6% compatible con variabilidad Y15 (PAN/ammonio) y con el hecho de que abril y
  mayo añadieron nutriente **en** la inoculación (Springferm/FDA el 06-04; "80 ppm YAN"
  Viniliquid el 12-05) — las muestras t=0 con hito "Pre-inóculo"/toma simultánea parecen
  preceder a la mezcla del aporte (los niveles YAN de marzo, sin pulso, son iguales), pero el
  orden exacto muestra-dosis no está documentado [NO DOCUMENTADO].
- **E0**: 1.14–1.49 % v/v (marzo→mayo), sin tendencia temporal (§3.3). No medido agosto–septiembre.
- **Gly0**: 0.75–1.27 g/L. Único patrón direccional sugerente: 17-04 (0.75–0.89) → 12-05
  (1.25–1.27) → agosto (1.12–1.15). [INTERPRETACIÓN] subida de ~0.3–0.4 g/L entre abril y
  mayo que no se consolida en agosto; del mismo orden que la dispersión entre réplicas de
  abril (0.75–0.89 dentro de un mismo día) → evidencia insuficiente para declarar deriva real.
- **X0/Xd0**: 0.099–1.07 / 0.001–0.121 kg/m³ en LAB004–012 — tres órdenes de contraste entre
  días con protocolo de inoculación distinto (abril: 0.1–0.5; mayo: 0.85–1.07). No es
  propiedad del mosto: refleja protocolo de inoculación y semántica Oculyze [INTERPRETACIÓN].
- **Relaciones entre variables**: no se observan correlaciones consistentes (p. ej., los
  días con GF bajo no tienen E0 alto: LAB004 GF 145.9 con E0 1.23 vs LAB005 GF 165.7 con E0
  1.24), lo que además sugiere que el scatter GF de abril es analítico y no por consumo
  diferencial.

**Conclusión de la fase**: [INTERPRETACIÓN] la evidencia es **compatible con una composición
inicial común estacionaria** (con E0 ≈ 1.2 % v/v como propiedad del mosto) y **no muestra
deriva temporal estadísticamente distinguible de la variabilidad analítica**. Con n=5 fechas
y dispersión inter-réplica del tamaño de cualquier tendencia plausible, el poder de
discriminación es bajo: la ausencia de deriva demostrada ≠ demostración de ausencia de deriva.

---

## 5. FASE 5 — Semántica de t0

### 5.1 TABLA D — Semántica de t0 por LAB

| LAB | t0 actual (pipeline) | Qué representa físicamente | Evidencia | Confianza |
|---|---|---|---|---|
| 001–003 | sin t0 de modelo (excluidos); en código descriptivo t0 = primer timestamp del logger (18:35) | inicio del log térmico | `run_co2_matrix_cross_validation_2026.py:973–977` (solo QC); química no homologada | Baja (no usada) |
| 004–006 | t=0 = siembra 2026-04-06 13:00 (`Fecha-hora` de `Eventos_operacion`); muestra `-01` fijada a t=0 | hora de siembra según workbook (hora dudosa; plan decía muestra a t=2) | `Diccionario_mapeo` ("Horas desde siembra"); `00_Resumen` base_t="Siembra eventos_operacion"; `load_natural_batch_metadata` (:142–155, fila t=0) | Media (fecha alta, hora conflictiva 10:00/13:00/15:30, logger acota ≤14:46) |
| 007–009 | t=0 = primer muestreo 2026-04-17 16:00 | primera muestra química; según ICS coincide con la hora de siembra real | `00_Resumen`/`Diccionario_mapeo` ("t=0 se fija en primer muestreo porque la siembra en Eventos está desalineada"); ICS siembra 16:00 local | Media-alta |
| 010–012 | hojas `LAB010..LAB012` (consumidas por el modelo): t=0 = L-01 2026-05-12 15:00; `Datos_homologados`/`00_Resumen`: t=0 = siembra 10:00 (L-01 a t=5) | doble semántica en el mismo workbook: primera muestra vs. siembra (workbook); la hora ICS de siembra (~15:00) coincide con la primera muestra | hojas LAB010–012 (L-01 t=0, renumeración y reanclaje verificados) vs. `Datos_homologados` (L-01 t=5) [CONFLICTO]; ICS 14:45–15:45 | Media (el t0 del modelo ≈ inoculación real si el ICS es correcto) |
| 013–015 | t0 proxy = muestra `-1` 2026-08-18 10:00 | primera muestra offline (probablemente 1–3 h ANTES de la inoculación real) | notebook lab013_015 celda 10 (`sample_id endswith "-1"`); `time_h` vacío a propósito; PI 11:05 pre-inóculo | Baja (proxy declarado pendiente) |
| 016–018 | t0 = fin del pulso de inoculación 2026-09-01 00:03:55/00:04:00/00:04:07 | instante físico de fin de inoculación (flanco de `nutricion_activa`) | xlsx `Experimentos.Notas`; verificación de flanco en notebooks; `*_inoculation_aligned.csv` (time_h puede ser negativo) | Alta (única ancla física medida) |

### 5.2 Impacto de la semántica de t0 sobre las ICs actuales

- LAB004–009: la primera química ES el t=0 del modelo (Δt≈0 por construcción) → las ICs
  usadas corresponden al estado en torno a la inoculación (±2 h). El riesgo es el opuesto al
  esperado: no es que la química esté lejos de t0, sino que el "t=0" es la química.
- LAB010–012: con la grilla de las hojas (modelo), L-01 = t=0 → ICs ≈ estado en
  inoculación (si ICS correcto). Con la grilla de `Datos_homologados` (t0=siembra 10:00),
  las mismas mediciones quedarían a t=+5 h y las ICs sobre-representarían 5 h de fermentación
  temprana (a X0≈1 la biomasa ya consume apreciablemente en 5 h). [CONFLICTO] ambas grillas
  coexisten en el workbook; el loader consume las hojas LAB*.
- LAB013–015: t0 proxy (muestra 10:00) probablemente anterior a la inoculación → las ICs del
  PI (11:05) quedan "en el futuro" respecto de t0 en ~1 h; impacto menor frente a X=0.45/E=0
  fallback.
- LAB016–018: t0 físico exacto, pero **sin química propia**: las ICs químicas no describen
  el mosto el 01-09 sino el 18-08 (muestra-2 de LAB013–015, 14 días antes). Si el mosto
  derivara, las ICs de LAB016–018 heredarían el estado de hace 14 días — bajo §4, esa deriva
  no es medible, pero es estructuralmente indetectable aquí.
- El doc oficial ya marca esta distinción: "t=0 histórico: fila t = 0 del workbook
  homologado ... t0 de muestreo/química, no flanco de inoculación medido (a diferencia de
  LAB016–018)" (`natural_must_model_calibration_and_estimator_readiness_2026.md` §4).

---

## 6. FASE 6 — Condiciones iniciales en el código

### 6.1 Cadena de carga (LAB004–012)

[HECHO VERIFICADO] Ruta: `run_co2_matrix_cross_validation_2026.py` →
`run_estimability_historical_by_medium.make_medium_batches("natural")` →
`run_secondary_joint_campaign_doe.make_secondary_batches` →
`run_new_must_glycerol_estimability_doe.make_batches` → `_initials_from_group`.
El loader base es `shared/new_must_data_loader.py` (workbook xthiol, hojas que empiezan con
"LAB"), cacheado en `shared/results/new_must_data_loading/new_must_normalized_long.csv`.

Regla central de ICs — `run_new_must_glycerol_estimability_doe.py:266–277`: para cada estado,
`_first_finite(serie, default)` = **primer valor finito de la serie** (ni interpolación a t=0
ni exigencia de fila t=0). Defaults si la serie está vacía: X=0.45, Xd=0, N=0.18, G=80, F=80,
E=0, Gly=0 (g/L; X/Xd/N kg/m³).

Conversiones en el loader: E %v/v→g/L ×7.8924 (:53–54); YAN mg/L→N kg/m³ ×10⁻³ (:58, :245);
X = concentración viable (Mcél/mL) ×0.03 (:55–57); Xd = (Conc_total − viable interp.)×0.03
recortado a ≥0 (:224–227); temperatura interpolada con fallback 18 °C (:287 del runner);
negativos clampeados a 0 (:253–255).

t0/timestamp: `load_natural_batch_metadata` (:142–168) toma la fila `t == 0.0` de cada hoja
como t0 absoluto y `Volumen inicial (L)` con default 2.0 L.

### 6.2 LAB013–018 (notebooks, fuera del loader)

- lab013_015 (celda 16): ICs = PI del Y15 para N (YAN×10⁻³)/G/F/Gly; **X=0.45, Xd=0, E=0
  fijos** (declarado en markdown). Sin pulsos.
- lab016_018 (celda 9): ICs = hoja `CondicionesIniciales` (G/F/YAN/Gly heredados;
  X=0.45/Xd=0); E0 escenarios A (0) / B (mediana E0 histórica 9.707652 g/L) aplicados en
  celda 11. Pulso N de diagnóstico 0.14 kg/m³ (protocolo 1.0 g SFX + 0.4 g FDA × 20% YAN en
  2 L; celda 49).
- La capa CO2 (`run_co2_matrix_cross_validation_2026.py`) **sobrescribe** el pulso del
  workbook (ΔN≈0.08) por ΔN=0.14 kg/m³ de protocolo (`override_natural_nutrient_pulses`
  :452–466); omite el pulso de inoculación ("su YAN ya está en la química t=0", :391–392).

### 6.3 TABLA E — Procedencia de ICs en el modelo

| Estado | Loader/función | Fuente de datos | Regla | Fallback | Riesgo |
|---|---|---|---|---|---|
| X | `_initials_from_group` :270 ← loader :222–235 | Oculyze viable (hojas LAB*) | primera obs. ×0.03 | 0.45 | Semántica Viability distinta entre hojas homologadas (conc. viable) y exports crudos (%); LAB013–018 usan 0.45 pese a existir Oculyze ≈0.41–0.48 (LAB013–015) |
| Xd | :271 ← loader :224–227 | Conc_total − viable (interp.) | primera obs. | 0 | Xd0 LAB010–012 (0.11–0.12) 10–100× el de abril; kd=0 en el modelo los hace inobservables |
| N | :272 ← loader :244–245 | columna YAN del workbook (=PAN+0.82×Amonio) | primera obs. ×10⁻³ | 0.18 | YAN de abril/mayo podría incluir aporte del nutriente de inoculación según orden muestra-dosis [NO DOCUMENTADO] |
| G | :267 ← loader :237–239 | Y15 Glucosa | primera obs. | 80.0 | LAB004–006 scatter ±10 g/L en t=0 |
| F | :268 | Y15 Fructosa | primera obs. | 80.0 | LAB005 F0=87.95 outlier del triplicado |
| E | :275 ← loader :133–166 | columna ETANOL (hoja LAB*) con fallback Alcolyzer | primera obs. (×7.8924 si %v/v) | **0.0** | LAB010–012: ETANOL solo en hoja, sin fuente primaria; LAB013–018: sin medición → 0/escenario; E0=0 contradice el nivel medido ~9.2–11.8 g/L del mismo mosto |
| Gly | :276 | Y15 Glicerol | primera obs. | 0.0 | — |
| (t0 abs.) | `load_natural_batch_metadata` :142–155 | fila t=0 de la hoja | fecha_hora de esa fila | — | Para LAB010–012 la fila t=0 es la primera muestra (15:00), no la siembra (10:00) de Datos_homologados |

Diferencias "valor usado por el modelo" vs "mejor medición disponible":
1. LAB013–015: modelo X0=0.45 vs Oculyze muestra-1 ≈ 0.41/0.44/0.48 (diferencia 0–8%);
   modelo E0=0 vs E0 medido del mismo mosto ≈ 9–11.8 g/L en LAB001–012 (LAB013–015 no
   midieron E).
2. LAB016–018: ICs químicas = herencia del 18-08 (muestra-2), no medición del 01-09; X0=0.45
   vs Oculyze +8.9 h ≈ 0.43/0.24/0.26 (LAB017/018 difieren ~2× del fallback).
3. LAB010–012: E0 entra al ajuste desde hoja sin trazabilidad primaria.
4. LAB001–003: mejor química pre-inóculo existe (Planilla Maestra) pero el pipeline no los
   consume (excluidos por CO2); ninguna IC del modelo proviene de marzo.

---

## 7. FASE 7 — YAN/N

[HECHO VERIFICADO]
- YAN del workbook (LAB004–012): `YAN = PAN + 0.82 × Amonio` (`00_Resumen`, `Diccionario_mapeo`;
  verificado numéricamente p. ej. LAB004: 93+0.82×168=230.76). El 0.82 corresponde a la
  conversión NH3→N (14/17 ≈ 0.824): el amonio Y15 está en mg NH3/L y el YAN en mg N/L.
- Y15 de agosto reporta YAN directo; verificado `PAN + 0.82×ammonia ≈ YAN` (LAB013-PI:
  110+0.82×170=249.4 ≈ 249).
- Conversión a estado: `N_kg_m3 = YAN_mg_l × 10⁻³` (loader :58, :245; notebooks ×10⁻³).
  Dimensionalmente correcta (1 mg/L = 1 g/m³ = 10⁻³ kg/m³).
- Pulso N del workbook → ΔN≈0.08 kg/m³ (loader :246–247) vs 0.14 kg/m³ de protocolo en la
  capa CO2 (:442, :452–466): inconsistencia documentada en el doc oficial §11.1.
- **Deuda documentada**: la reconstrucción por componentes `YAN_components_mg_l = PAN + NH4`
  **sin** el factor 0.82 (loader :252–253; `run_secondary_metabolite_data_review.py:130–137`).
  El estado N usa el YAN medido, no la reconstrucción, por lo que el impacto directo en
  θ_natural es nulo, pero cualquier uso futuro de componentes PAN/NH4 hereda la ambigüedad
  (doc §11.3). No se corrige en esta auditoría.

---

## 8. FASE 8 (TABLA F) — Datos faltantes críticos

| Dato | LAB afectados | Por qué importa | ¿Reconstruible desde el repo? | Evidencia externa necesaria |
|---|---|---|---|---|
| Hora exacta de inoculación | 004–006 (conflicto 10:00/13:00/15:30) | desplazaría toda la grilla t y el Δt de la química t=0 (±2 h) | Parcial: logger la acota a ≤14:46 el 06-04 | Hora real de siembra anotada por el operador |
| Hora exacta de inoculación | 013–015 | t0 proxy actual puede preceder a la inoculación 1–3 h | No (time_h vacío por diseño) | Log/hora de inoculación del 18-08 |
| Hora real de siembra vs. grilla | 010–012 | doble anclaje (hojas vs Datos_homologados) cambia ICs de t=0 a t=5 | Parcial (ICS + logger acotan ~15:00) | Confirmación operativa de 10:00 vs ~15:00 |
| E0 medido | 013–018 | E0=0/escenario contradice el nivel ~1.2 % v/v medido en el mismo mosto (marzo–mayo) | No (no existe medición) | Alcolyzer de PI/t=0 de agosto–septiembre |
| Origen de ETANOL 1.18/1.18/1.19 | 010–012 | E0 entra al ajuste θ_natural sin fuente primaria | No | Registro Alcolyzer de mayo |
| Química t=0 propia | 016–018 | ICs describen el mosto del 18-08, no del 01-09 | No | Y15 de PI del 01-09 |
| X0 t≈0 | 013–018 | X0=0.45 fallback vs Oculyze 0.24–0.48 | Parcial (Oculyze a ~1.5–9 h ya existe; no es t=0) | Oculyze de PI/0 h |
| Método/T/duración de conservación del mosto madre; fecha de vendimia; tratamientos (SO2) | todos | determinar si la deriva podría existir y sobre qué escala | No (cero documentación) | Registro de bodega/vendimia |
| Vínculo mosto madre entre Lote 1 / Lote 2 / Mayo T1 / LAB013–018 | todos | la premisa "mismo mosto" no es trazable en el repo | No | Confirmación del laboratorio |
| Orden muestra-vs-dosis del nutriente de inoculación (Springferm/Viniliquid) | 004–012 | define si YAN0/G0 medidos incluyen el aporte | No | Protocolo operativo escrito |
| Identidad de la muestra Y15 `#1` del 14-08 (GLU-FRU −0.25, YAN 69) | 013–015 (contexto) | posible control de mosto pre-experimento | No | Nota de laboratorio |
| Dosis/composición de nutrición LAB016–018 (+56.9 h) | 016–018 | ΔN de diagnóstico 0.14/0.28 es presunción de protocolo | No | Masas/producto reales |
| Lote/volumen inicial | 016–018 (`Lote_Mosto`, `Volumen_Inicial_L` vacíos) | trazabilidad de mosto y balance | No | Registro del experimento |

---

## 9. FASE 9 — Registro de conflictos encontrados

1. [CONFLICTO] Hora de siembra LAB004–006: Hora=10:00 vs Fecha-hora=13:00 (workbook) vs
   15:30 (ICS) vs ≤14:46 (logger, nutricion_activa=1 en F1 y F2 activo).
2. [CONFLICTO] Siembra LAB007–009: workbook 2026-03-25 16:00 vs ICS 2026-04-17 16:00
   (23 días); la homologación lo reconoce y define t0=primer muestreo (17-04 16:00).
3. [CONFLICTO] LAB010–012: doble grilla t dentro del mismo workbook — hojas LAB* ancladas a
   la primera muestra (15:00, L-01 t=0, muestras renumeradas) vs `Datos_homologados`/
   `00_Resumen` ancladas a siembra (10:00, L-01 t=5). El modelo consume las hojas.
   Además siembra workbook 10:00 vs ICS 14:45–15:45.
4. [CONFLICTO] E0 LAB010–012: 1.18/1.18/1.19 % v/v existen solo en hojas LAB*; columnas
   Alcolyzer de `Resultados_primarios`/`Datos_homologados` vacías para esos LABs.
5. [CONFLICTO] E0 modelo vs medición: E=0 forzado (LAB013–015; escenario A LAB016–018) frente
   a E0 medido 9.0–11.8 g/L en el mismo mosto (LAB001–012).
6. [CONFLICTO] Plan vs registro `-01` LAB004–006: Muestreo_MEF planifica 15:00 (t=2),
   Resultados_primarios registra 13:00 (t=0).
7. [CONFLICTO menor] YAN por componentes: fórmula 0.82 (workbook) vs reconstrucción PAN+NH4
   sin factor (código) — deuda documentada.
8. [CONFLICTO menor] ΔN de pulso: 0.08 (workbook/upstream) vs 0.14 kg/m³ (capa CO2).
9. Anomalías de datos: Oculyze LAB015 con etiqueta duplicada "LAB015-1" (la 2.ª es la
   muestra 2); `Description "19/01/26"` en LAB018-1 (typo de 01/09/26); discrepancia
   526/527 mg/L CO2 disuelto LAB015-1 entre hoja F3 y CSV; `backup_global_ph_rtd.csv`
   (julio 2026) archivado dentro de `LAB013-015/` pese a no cubrir su ventana (agosto);
   LAB013-PI→LAB013-2 cae 8 g/L de GF en ~2 h (LAB014/015 ±1).

---

## 10. FASE 10 — Análisis final (preguntas explícitas)

1. **¿Evidencia de cambio sistemático de G0/F0/YAN0/E0/Gly0 entre LAB001–LAB018?**
   No concluyente. La serie (TABLA C) es estacionaria dentro de la dispersión analítica:
   GF 151–160 (outliers 06-04: 145.9/165.7 **dentro** de un mismo triplicado simultáneo),
   YAN0 220–249 sin monotonicidad, E0 1.14–1.49 % v/v plano, Gly0 0.75–1.27 con única subida
   direccional (abril→mayo ~+0.35) que no persiste en agosto. El scatter entre réplicas del
   mismo día es del mismo tamaño que cualquier tendencia plausible → no se puede separar
   deriva real de variabilidad [INTERPRETACIÓN].

2. **¿Evidencia compatible con fermentación espontánea mínima pre-inoculación?**
   Compatible pero no demostrativa. Hechos: E0 ≈ 1.2 % v/v en todas las mediciones t≈0
   (marzo–mayo); CO2 plano de 0.5–1.0 sccm horas antes de inoculación en F2/F3 (abril/mayo);
   CO2 disuelto 476–527 mg/L en agosto. Interpretaciones alternativas no excluidas: alcohol
   formado antes del primer experimento + desgasificación, offsets por sensor (F1≈0 vs
   F2/F3≈0.87 en los mismos instantes). Lo que la evidencia sí acota: **no hay acumulación
   progresiva** de E0 entre marzo y mayo, y las señales pre-inoculación no crecen.

3. **¿Composición inicial común para una futura recalibración?**
   Razonable como hipótesis de trabajo para G0+F0 (~153 g/L), YAN0 (~235 mg/L), E0 (~9.5 g/L)
   y Gly0 (~1.05 g/L), con la advertencia de que (i) el repositorio no documenta el mosto
   madre común fuera de LAB013–018, (ii) los outliers analíticos del 06-04 piden un esquema
   robusto (errores por réplica, no un valor único de facto), y (iii) X0/Xd0 NO son comunes.

4. **Clasificación de variables:**
   - Comunes al mosto (candidatas): G0+F0 total (mejor que G0/F0 separados: la relación
     G/F oscila 0.92–1.28 entre réplicas simultáneas), YAN0, E0, Gly0 (esta última con
     dispersión relativa mayor).
   - Específicas por LAB: X0, Xd0 (protocolo de inoculación + Oculyze; difieren por diseño),
     y los pulsos/tiempos de nutrición.
   - Comunes con pequeña desviación experimental: G0 y F0 individuales alrededor de la
     proporción media del mosto; YAN0 (±6%).

5. **¿Es razonable imponer E0=0?**
   **No.** E0 medido en el instante de inoculación: 1.14–1.49 % v/v (9.0–11.8 g/L) en las 12
   fermentaciones con Alcolyzer (LAB001–012), sin excepción y sin tendencia temporal.
   E0=0 solo se justifica como escenario de sensibilidad (como hace el notebook holdout), no
   como condición física del mosto. Nota: mantener E0 medido como IC es distinto de
   recalibrar cinética; esta auditoría no propone cambios de modelo.

6. **¿Las ICs actuales corresponden al momento de inoculación?**
   Parcialmente. LAB004–009: sí en la práctica (la química t=0 es el t=0 del modelo, ±2 h).
   LAB010–012: sí bajo la grilla de las hojas (t0=15:00 ≈ siembra ICS); no bajo
   `Datos_homologados` (química a t=+5). LAB013–015: ICs del PI (≈ inoculación), pero t0 del
   notebook (10:00) la precede; E=0/X=0.45 no son mediciones. LAB016–018: t0 exacto pero ICs
   químicas de hace 14 días (heredadas) y E0/X0 por escenario/fallback. En síntesis: el
   pipeline nunca usa una IC química *lejos* de la inoculación, pero solo LAB004–009 tienen
   ICs químicas verdaderamente medidas en su propio t0.

7. **¿LABs con ICs confiables vs proxies/fallbacks?**
   Confiables (medidas en t≈0 propio): LAB004–009 (G/F/YAN/Gly/E/X/Xd), con la salvedad del
   scatter del 06-04. Intermedias: LAB010–012 (química Y15 sólida; E0 sin trazabilidad
   primaria; t0 con doble anclaje). Dependientes de proxy/herencia/fallback: LAB001–003
   (excelente PI pero fuera del pipeline), LAB013–015 (N/G/F/Gly del PI medidos; X/E
   fallback; t0 proxy), LAB016–018 (todo químico heredado; X/E fallback/escenario; t0
   excelente).

8. **¿Deriva suficientemente fuerte para modelar ICs en función de la fecha?**
   No. Con 5 fechas y dispersión inter-réplica ≥ cualquier pendiente plausible, un modelo de
   ICs(t) no sería identificable y riesgaría ajustar ruido (el patrón YAN0, p. ej., baja de
   abril a mayo y sube en agosto). Recomendación implícita: ICs comunes + término de error,
   no ICs fecha-dependientes [INTERPRETACIÓN].

9. **¿Qué falta antes de una recalibración?**
   (a) Confirmar por escrito el mosto madre común y su historia de conservación (vendimia,
   método, T, tratamientos); (b) hora real de inoculación de LAB013–015 (y de 004–006/010–012
   si se quiere cuadrar Δt); (c) medición E0 de agosto–septiembre (o aceptar explícitamente
   el nivel histórico ~9.5 g/L); (d) origen del ETANOL 1.18/1.19 de LAB010–012; (e) dosis
   reales de nutrición (0.08/0.14/0.28 actuales son presunciones); (f) decisión sobre el
   doble anclaje t de LAB010–012; (g) química PI/t=0 para futuros experimentos (ya está en el
   plan NM26: puntos −1/0.25 h); (h) resolver la convención SCCM→g/L/h antes de tocar la capa
   CO2 (prerrequisito ya documentado en el doc oficial).

10. **Recomendaciones para la estrategia futura de ICs (sin implementar):**
    1. Tratar G0+F0, YAN0, E0, Gly0 como **comunes al mosto** con error experimental estimado
       desde las réplicas simultáneas (triplicados 06-04, 17-04, 12-05, 18-08 son réplicas
       genuinas: usarlas para σ de ICs).
    2. Eliminar E0=0 como supuesto operativo; usar E0 medido o, en su defecto, el nivel
       histórico ~9.5 g/L con incertidumbre declarada (los escenarios A/B del holdout ya
       bracketean el efecto).
    3. Declarar X0/Xd0 por experimento (medición Oculyze/BIOMASA en t≈0) y no compartirlos;
       registrar el protocolo de inoculación con cada X0.
    4. Homologar una sola definición de t0 por LAB (preferir ancla física: flanco de
       inoculación como en LAB016–018; en su defecto primera muestra, declarándolo) y
       conciliar las grillas hojas-LAB vs Datos_homologados de LAB010–012.
    5. Registrar siempre muestra PI (pre-inóculo) + t=0 con fecha-hora, y el orden
       muestra-dosis respecto del nutriente de inoculación.
    6. Para el próximo lote (NM26-A/B, plan 21-09-2026): el calendario ya incluye PI y
       t=0.25 h complejos — mantenerlo y añadir Alcolyzer PI/t0 para cerrar la deuda de E0.
    7. Documentar el mosto madre (origen, conservación, T, duración) como metadata de
       campaña en `campaigns/` — hoy es [NO DOCUMENTADO].
    8. No introducir ICs fecha-dependientes con la evidencia actual (ver pregunta 8).

---

## 11. Control de calidad de esta auditoría

- Los 18 LAB (LAB001–LAB018) fueron revisados individualmente (TABLA A/B/C/D los cubre).
- Ninguna ausencia fue rellenada con suposiciones: los huecos aparecen como [NO DOCUMENTADO],
  FALLBACK, ESCENARIO o "no medido".
- Cada cifra cita su fuente (hoja/columna o archivo). Conversiones usadas (7.8924 g/L por
  %v/v; 10⁻³ kg/m³ por mg/L; 0.82 NH3→N) son las del repositorio y fueron reproducidas
  numéricamente contra `batch_summary.csv` (E0 g/L exacto para los 9 batches) y contra la
  hoja `CondicionesIniciales` de LAB016–018 (herencia 74.05/77.73/244.33/1.14 reproducida
  desde LAB013/014/015 muestra-2).
- Unidades: G/F/E/Gly en g/L; YAN en mg N/L; N en kg/m³; X/Xd en kg/m³; E0 también expresado
  en % v/v (unidades del Alcolyzer).
- Contradicciones código/notebooks/datasets recopiladas en §9.
- Archivos modificados: **ninguno** salvo este documento (nuevo).

*Auditoría de solo lectura, 2026-09-09. Fuentes citadas verificadas contra el árbol del
repositorio en la fecha indicada.*

---

## Análisis cuantitativo de condiciones iniciales

*(Sección añadida 2026-09-09. Análisis reproducible, estrictamente descriptivo — sin fitting ni
optimizadores — ejecutado en
`fermentation_model/laboratory_2026/notebooks/natural_must_initial_conditions_analysis.ipynb`,
que relee cada valor desde la fuente primaria y lo verifica contra
`results/estimability_historical_natural/batch_summary.csv`. Artefactos:
`laboratory_2026/results/natural_must_initial_conditions_analysis/`
→ `initial_conditions_lineage.csv` (144 filas = 18 LAB × 8 variables, con status
MEASURED/DERIVED/INHERITED/FALLBACK/SCENARIO/NOT_AVAILABLE, fuente por cifra y
`potential_outlier`), `measured_initial_conditions.csv` (solo observaciones independientes),
`initial_conditions_statistics.csv`, `initial_conditions_by_batch.csv`.)*

**Cobertura real [HECHO VERIFICADO contra fuentes]:**

- LAB con ICs **químicas realmente medidas** (G0/F0/Gly0): **LAB001–LAB015** (15). YAN0 medido
  (columna directa del Y15) en LAB013–015; derivado (PAN + 0.82·NH4, misma muestra) en
  LAB001–012. N0 siempre DERIVED (YAN·10⁻³; no es observación adicional). E0 derivado de
  Alcolyzer medido en LAB001–012 (en LAB010–012 con procedencia primaria no trazable, §3.2).
- LAB con ICs **INHERITED**: **LAB016–LAB018** (G0/F0/YAN0/N0/Gly0 = promedio LAB013/014/015
  muestra-2; verificado aritméticamente). **No constituyen observaciones independientes**.
- FALLBACK: E0=0 en LAB013–015; X0=0.45/Xd0=0 en LAB013–018. SCENARIO: E0 A/B en LAB016–018.
- Observaciones independientes: G0 **15**, F0 **15**, GF0 **15**, YAN0 **15**, Gly0 **15**,
  E0 **12** (n=9 con procedencia primaria plenamente trazable + LAB010–012 con salvedad).

**Estadísticas globales (observaciones independientes) [RESULTADO DESCRIPTIVO]:**

| Variable | n | media | std | CV | mín–máx |
|---|---|---|---|---|---|
| G0 [g/L] | 15 | 77.42 | 2.33 | 3.0 % | 75.00–81.63 |
| F0 [g/L] | 15 | 77.75 | 3.74 | 4.8 % | 70.81–87.95 |
| G0+F0 [g/L] | 15 | 155.16 | 4.48 | 2.9 % | 145.85–165.66 |
| YAN0 [mg/L] | 15 | 235.0 | 9.1 | 3.9 % | 220.2–249.0 |
| N0 [kg/m³] | 15 | 0.235 | 0.009 | 3.9 % | 0.220–0.249 (idéntico a YAN0 por construcción) |
| E0 [g/L] | 12 | 9.69 (1.23 % v/v) | 0.72 | 7.4 % | 9.00–11.76 (1.14–1.49 % v/v) |
| Gly0 [g/L] | 15 | 1.05 | 0.16 | 15.1 % | 0.75–1.27 |

**Intra-grupo vs entre-grupos (std entre medias / std intra promediada):** G0 1.09, F0 0.57,
GF0 0.72, E0 0.85 → **la réplica intra-grupo domina** (variabilidad analítica; el scatter del
06-04 es el mayor: GF0 145.9–165.7 dentro de un mismo triplicado simultáneo). YAN0 **4.03** y
Gly0 **3.88** → **el desplazamiento entre grupos supera ~4× la dispersión de réplicas**, pero
las medias grupales **no son monótonas en el tiempo**: YAN0 237.5 → 229.1 → 238.6 → 222.7 →
247.3 mg/L (mar→ago) y Gly0 0.95 → 1.08 → 0.83 → 1.26 → 1.13 g/L. E0 por grupo: 9.39 / 9.79 /
10.23 / 9.34 g/L (plano).

**Outliers IQR (marcados, no eliminados):** LAB004 F0 70.81 y LAB005 F0 87.95 g/L (el par
extremo del triplicado 06-04; su GF0 145.9/165.7 sale del rango típico pero LAB005 GF0 roza el
umbral), LAB007 E0 11.76 g/L (1.49 % v/v), y LAB010/LAB012 Xd0 (0.11–0.12 kg/m³; protocolo de
inoculación, no química del mosto).

**Resultado por variable:**

- **G/F/GF**: suficientemente similares entre grupos (CV ~3–5%; intra-grupo domina). GF0 ≈
  155 ± 4.5 g/L como propiedad común razonable. El outlier F0 de LAB005 recomienda errores por
  réplica y no un valor único de facto.
- **YAN**: CV total bajo (3.9%) pero con estructura entre grupos (222.7–247.3 mg/L, ±5%
  respecto de la media) no atribuible a deriva temporal; compatible con efectos de
  manejo/lote/análisis (y con el nutriente aplicado en la inoculación de abril–mayo, cuyo orden
  muestra-dosis no está documentado). Valor común admisible solo con desviación ±5% declarada.
- **E0**: medido ≠0 en las 12 fermentaciones con Alcolyzer (9.0–11.8 g/L; 1.14–1.49 % v/v);
  plano en el tiempo (sin acumulación marzo→mayo); sin LAB010–012 la media es 9.80 ± 0.80 g/L
  (sin cambio de conclusión). **E0=0 no es compatible con las mediciones** (solo como escenario
  límite de sensibilidad, como lo usa el holdout). La causa del alcohol preexistente sigue sin
  demostrarse (§3.3).
- **Gly**: variación importante (CV 15%; medias grupales 0.83–1.26 g/L, ±20% de la media) no
  monótona → no deriva temporal, pero es la variable menos "común"; si se usa valor común, la
  desviación experimental debe declararse explícitamente.

**Deriva temporal:** ninguna variable muestra progresión monótona compatible con tiempo de
almacenamiento; en GF0/G0/F0/E0 la variabilidad de réplicas iguala o supera la entre-grupos, y
en YAN0/Gly0 el patrón entre-grupos es no-monótono. **No hay evidencia descriptiva de deriva
temporal del mosto** (marzo–agosto).

**Conclusión:** las ICs químicas del mosto madre **pueden considerarse aproximadamente comunes**
para GF0 (~155 g/L) y E0 (~9.7 g/L ≈ 1.2 % v/v), y comunes con desviación experimental declarada
para YAN0 (235 ± 10 mg/L) y Gly0 (1.05 g/L, dispersión entre grupos 0.83–1.26). X0/Xd0 son por
experimento (medidos solo en LAB004–012; 0.099–1.066 kg/m³ según protocolo de inoculación).
Antes de recalibrar siguen faltando (§8, TABLA F): hora de inoculación de LAB013–015, E0 de
agosto–septiembre, origen del ETANOL 1.18/1.19 % v/v de LAB010–012, metadata del mosto madre y
dosis de nutrición de LAB016–018.
