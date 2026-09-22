# Historial de modificaciones realizadas por agentes

Registro breve de cambios implementados por agentes en el repositorio.

### 2026-09-19 01:07 HSP

- Archivos: `docs/current_model_equations_audit_2026/`, `docs/modelo_fermentacion_CO2_EKF_2026/`, `docs/natural_must_model_calibration_and_estimator_readiness_2026/`, `docs/planning/proximos_lotes_mosto_natural_2026/`
- Cambio: reorganización de `docs/`: cada `.tex` se movió a su propia carpeta junto con su PDF y auxiliares de compilación (`current_model_equations_audit_2026.tex` + `current_model_equations_090926.pdf`; `modelo_fermentacion_CO2_EKF_2026.tex` solo; `natural_must_..._2026.tex` + `.pdf` + `.synctex.gz`; `proximos_lotes_mosto_natural_2026.tex`). Los `.md`/`.xlsx` homónimos se mantuvieron en su ubicación original por estar referenciados por ruta desde notebooks y otros documentos.

### 2026-09-14 16:48 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_pulse_inconsistency_review.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_pulse_inconsistency_review.executed.ipynb`
- Cambio: nuevo notebook de diagnóstico (SOURCE + EXECUTED) que audita la inconsistencia del pulso de N entre el modelo cinético upstream (fila `pulso_nut` del workbook, 0.08 kg/m³) y la capa CO2 (cruce de densidad 1040 + dosis de protocolo 0.14 kg/m³) para LAB004–LAB012, incluido LAB009. Verifica origen t=0 común, reproduce `natural_nutrient_pulse_schedule` contra `effective_nutrient_pulses.csv`, y entrega tabla resumen por lote y 3 figuras multipanel (CO2+N combinado, CO2 global, N global). Solo diagnóstico: sin recalibración ni cambios de tiempos/dosis; sin artefactos CSV/PNG adicionales.

### 2026-09-14 21:48 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.executed.ipynb` (movidos desde `laboratory_2026/notebooks/`, que antes existía como archivo único con outputs)
- Cambio: se reorganizó el análisis de retardo del filtro CO2 al esquema SOURCE (sin outputs) / EXECUTED y se movió a `notebooks/diagnostics/`. Se agregaron a las figuras RAW vs FILT las líneas verticales del pulso 2 de N según ambas convenciones — `Pulso_nut planilla (upstream)` (verde continua, desde la columna `pulso_nut` del workbook) y `Cruce densidad 1040 (capa CO2)` (roja discontinua, desde `effective_nutrient_pulses.csv` de la corrida congelada) — llevadas al eje temporal vía el t=0 del lote; LAB001–003 sin registro de pulso quedan sin líneas. No se modificó el cálculo de retardos ni se corrigió el delay en la calibración.

### 2026-09-14 22:03 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.executed.ipynb`
- Cambio: se agregó al final de la sección 4.1 una figura global multipanel (LAB004–LAB012) con RAW original, RAW robust/suavizado y FILT **sin compensar**, convertidos a g/L/h con la conversión definitiva `SCCM_CORRECTED` (0.0404391928807947 g/L/h por sccm a 2 L, leída de `analysis_manifest.json`), incluyendo las líneas del pulso 2 de N de ambas convenciones (`Pulso_nut planilla (upstream)` y `Cruce densidad 1040 (capa CO2)`) y el Δt por lote en los títulos. Ejecución completa regenerada: 19/19 celdas de código, cero errores.

### 2026-09-14 22:20 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.executed.ipynb`
- Cambio: se agregó la sección 4.3 con la figura de temperaturas de LAB004–LAB012 (mismo estilo que los perfiles del cross-matrix, sin DOE): T medida (mediana 30 min, input del modelo) y setpoint desde `process_temperature_30min.csv`, con ambas líneas de pulso de N. Documentado en el notebook que la temperatura no lleva filtro Hampel/Butterworth ni corrección de offset — solo remuestreo por mediana a 30 min y posterior interpolación lineal al grid del modelo con fallback nominal. Ejecución regenerada: 20/20 celdas de código, cero errores.

### 2026-09-20 20:33 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `docs/planning/planificacion_LAB019_021_replica_lote2_2026.tex`, `docs/planning/planificacion_LAB019_021_replica_lote2_2026.pdf` (PDF compilado del .tex); eliminados los planes previos `planificacion_proximas_fermentaciones_natural_2026.xlsx`, `proximos_lotes_mosto_natural_2026.xlsx` y `proximos_lotes_mosto_natural_2026/`
- Cambio: nueva planificación de la réplica del Lote 2 (LAB019=F1/A, LAB020=F2/A, LAB021=F3/C) con inicio lunes 21/09/2026 16:00 (t0 = fin de inoculación automatizada), construida desde los parámetros ejecutados reales de LAB004–006 (`Eventos_operacion`/`Perfiles_temperatura`: pulsos 2 a t=51/75 h, setpoints a t=99/171/123/219 h) y la cinética original (A seca t≈122–146 h, C t≈170–194 h). Cronograma con ventanas laborales (lun–jue 8:30–12:30/14:30–16:45, vie 8:30–11:30), muestreo con separación ≥6.5 h intra-día (PI + 15 eventos), eventos automáticos por bomba, criterios de término y contingencias. Excel validado (audit/scan/validate sin hallazgos, sin fórmulas); LaTeX compilado sin errores/overfull y aceptado visualmente (5/5 páginas).

### 2026-09-20 21:29 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `.tex`, `.pdf` (actualizados); `docs/planning/registro_muestras_LAB019_021_2026.xlsx`, `.tex`, `.pdf` (nuevos)
- Cambio: planificación v2 — (a) visitas de muestreo de tarde movidas de 15:00 a 14:30 porque cada visita demora ~1.5–2 h de procesamiento (término ~16:30, margen antes de la limpieza de 17:00); (b) DO agregado a todas las muestras; (c) Carbodoseur (CO2 disuelto, ~100 mL/lectura) en 7 eventos fijos (PI, -01, -02, -05, -06, -09, -14) + -15 condicional, elegidos para observar el pool de CO2 disuelto: IC real (≠0), discriminación threshold vs continuous release y validación de Csat(T) en los cambios de setpoint; (d) presupuesto de volumen documentado (~0.7–0.8 L/reactor en Carbodoseur). Nueva planilla de registro (Excel + LaTeX/PDF): 16 bloques (uno por muestra) con hora real, filas F1/F2/F3 y columnas Brix/densidad/T/OD/volumen remanente Carbodoseur/CO2 disuelto de tabla/notas; Oculyze excluido (queda en su software). Validación: ambos Excel passed (audit/scan/validate), ambos PDF sin errores/overfull y aceptados visualmente (plan 6/6, registro 6/6 tras corregir cortes de bloque entre páginas con minipage).

### 2026-09-20 21:52 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `.tex`, `.pdf`; `docs/planning/registro_muestras_LAB019_021_2026.xlsx`, `.tex`, `.pdf`
- Cambio: planificación v3 — se agregó MINI-MUESTRA -02B el martes 22/09 11:45 (t=19.75 h; solo Carbodoseur + densidad/Brix/DO, sin Y15/Oculyze/Alcolyzer, ~15-20 min) para tener tres puntos del pool de CO2 disuelto el día del onset (16.5/19.75/22.5 h); con ello el conteo de lecturas Carbodoseur pasa a 8 fijas + -15 condicional (~0.8-0.9 L/reactor, ~65-75% del batch) y la planilla de registro pasa a 17 bloques. Corregido además el horario de MUESTRA -03 (15:00→14:30) para restaurar la coherencia de las visitas de tarde con el diseño v2. Validación: ambos Excel passed (audit/scan/validate); ambos PDF sin errores/overfull y aceptados visualmente (plan 6/6 tras corregir errata en pág. 3; registro 6/6 tras eliminar rellenos grises que tapaban las reglas horizontales).

### 2026-09-21 11:05 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `.tex`, `.pdf`; `docs/planning/registro_muestras_LAB019_021_2026.xlsx`, `.tex`, `.pdf`
- Cambio: rediseño de la réplica por decisión del laboratorio — ya no replica el Lote 2 completo (LAB004-006) sino LAB004 (Protocolo A, F1), LAB006 (Protocolo C, F2) y LAB009 (Protocolo A, F3, grupo 17/04 sin registro Maestro). Eventos automáticos por fermentador según su original: pulsos 2 a t=48 h (F3, vía ICS; sin registro en workbook; densidad cruzó 1040 ~t=44 h), 51 h (F1) y 75 h (F2); setpoints F3 21 °C@96 h y 16 °C@168 h (inferido en original), F1 99/171 h, F2 123/219 h. Muestreo rediseñado a 22 eventos: t0 hoy lunes (PI + -01), mar-jue 4 muestreos/día (08:30 y 14:30 completas + minis 11:15/16:40 solo instrumental), vie 2 (08:30 + mini 11:00), semana siguiente cola liviana (lun ×2, mar ×1, mié ×2, jue condicional). Carbodoseur: 11 lecturas fijas + 1 condicional (~1.0-1.1 L/reactor; presupuesto 75-85% del batch con orden de suspensión documentado); 4 puntos el martes (16.5/19.25/22.5/24.7 h) cubren la trayectoria del pool hasta el onset esperado de A (24-30 h según loggers de abril, 22-24 h en LAB016-018). Planilla de registro a 22 bloques. Validación: ambos Excel passed (audit/scan/validate); planificación 7/7 páginas y registro 8/8 aceptadas visualmente (corregidas columna de la condicional -21 a F2, nota al pie -15→-21 y paginación final).

### 2026-09-22 10:47 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_v2_2026.xlsx`, `.tex`, `.pdf`; `docs/planning/registro_muestras_LAB019_021_v2_2026.xlsx`, `.tex`, `.pdf`
- Cambio: nueva versión v2 de la planificación y de la planilla de registro (archivos `_v2` nuevos, sin borrar los anteriores) con el horario de muestreo redefinido por el laboratorio: mar-jue 09:00 / 12:00 (mini instrumental) / 15:00 + intermedia opcional martes 16:45 (t=24.75 h, discrimina threshold vs continuous), viernes 09:00 + 11:00, lunes PI 15:30 + t0 16:10 (20 eventos; Carbodoseur 10 fijas + 1 condicional). Setpoints y pulsos 2 en múltiplos de 12 h desde t0, de modo que todos los eventos automáticos caen a las 16:00: F1 (A) 48/96/168 h, F2 (C) 72/120/216 h, F3 (B) 48/72 h con inicio 21 °C→18 °C y segundo cambio omitido (perfil real del logger de LAB009); se incluyó nota de auditoría homologación-vs-logger de LAB009 (perfil invertido usado por θ_natural, etiquetas LAB007/LAB009 intercambiadas). Validación: ambos Excel passed (audit/scan/validate); ambos PDF sin errores ni overfull y aceptados visualmente (planificación 8/8 tras corregir el anclaje de tablas con [h]/[H]+needspace; registro 7/7).

### 2026-09-22 11:19 -03

- Archivos: `README.md`, `REPOSITORY_MAP.md`, `docs/work_state/PROJECT_CONTEXT.md`
- Cambio: se documentó la trazabilidad de theta y se actualizaron los endpoints principales para distinguir la variante full-theta corregida (17/17 parámetros) del baseline histórico que reconstruye los subsets `theta.csv`/`theta_by_case.csv` sobre `DEFAULT_THETA`; también se clasificaron los notebooks aún incompletos y los usos intencionales o seguros de los artefactos parciales.

### 2026-09-22 11:20 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_v2_2026.xlsx`/`.tex`/`.pdf`; `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`/`.tex`/`.pdf`; `docs/planning/registro_muestras_LAB019_021_v2_2026.xlsx`/`.tex`/`.pdf`; `docs/planning/registro_muestras_LAB019_021_2026.xlsx`/`.tex`/`.pdf`
- Cambio: corrección del balance de volumen en las cuatro versiones de los documentos (es general del muestreo, no de una versión): la alícuota del Carbodoseur (~100 mL) SE DEVUELVE al reactor, por lo que se eliminó el presupuesto apretado 75-85% y la orden de suspensión de lecturas; el único volumen perdido por reactor es Alcolyzer 50 mL/muestra (F1/F3 ≈3 muestras = 150 mL; F2 ≈5 = 250 mL) + Y15 1 mL y Oculyze 1 mL por visita completa + ~2 mL/visita de mangueras (también minis) → pérdida total ≈0.2 L (F1/F3) y ≈0.3 L (F2), volumen final ≈1.7-1.8 L de 2.0 L. En las planillas de registro se agregó en cada bloque la columna «mL no retornados (ledger)» con el desglose por defecto en la instrucción de cabecera, y el bloque condicional solo-F2 marca F1/F3 con «—» también en el PDF v2. Planificaciones: ediciones in situ en las filas de Resumen/Restricciones; registros: reconstruidos con el mismo formato. Validación: 4 Excel passed (audit/scan/validate); 4 PDF sin errores ni overfull (columna Notas ajustada a 3.5 cm) y aceptados visualmente (planificaciones 15/15; registros 15/15 tras corrección del bloque 19).

### 2026-09-22 11:52 -03

- Archivos: `docs/current_model_equations_audit_2026.md`, `docs/current_model_equations_audit_2026/current_model_equations_audit_2026.tex`, `docs/current_model_equations_audit_2026/current_model_equations_audit_2026.pdf`
- Cambio: se actualizó la auditoría integral del modelo para distinguir el baseline histórico A (`theta.csv` + `DEFAULT_THETA`) de B/C con theta completo 17/17, incorporar la conversión SCCM corregida y los parámetros/objetivos A-B-C, mantener como abierto el conflicto de dosis y calendario de N, y clasificar `modelo_ecuaciones_2026` como descripción del estado B. Se generó un PDF actual sincronizado y se conservó intacto `current_model_equations_090926.pdf` como snapshot histórico.

### 2026-09-22 13:13 HSP

- Archivos: `docs/planning/registro_muestras_LAB019_021_v3_2026.tex`, `.pdf`
- Cambio: nueva versión v3 de la planilla de registro, solo PDF (el v2 editado a mano por el laboratorio y su xlsx quedan intactos): papel carta explícito (letterpaper landscape), formato compactado para reducir de 7 a 4 páginas (margen 1.0 cm, arraystretch 1.15, filas de 0.55 cm, menos espaciado entre bloques, 5 bloques/página) y corrección de las muestras de las 12:00 (03/07/10), que sí son visita completa con Y15/Oculyze/Alcolyzer — se quitó su etiqueta "(mini: sin ...)"; las mini 05 (mar 16:45 opcional) y 13 (vie 11:00) conservan su marca. Se preservaron las ediciones manuales del v2 (sin título ni párrafos de instrucciones ni pie). Validación: PDF sin errores ni overfull, tamaño carta verificado (792×612 pt) y aceptado visualmente 4/4.
