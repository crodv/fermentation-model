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
