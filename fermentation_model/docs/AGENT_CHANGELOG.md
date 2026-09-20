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
