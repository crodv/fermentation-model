# Historial de modificaciones realizadas por agentes

Registro breve de cambios implementados por agentes en el repositorio.

### 2026-09-14 16:48 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_pulse_inconsistency_review.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_pulse_inconsistency_review.executed.ipynb`
- Cambio: nuevo notebook de diagnóstico (SOURCE + EXECUTED) que audita la inconsistencia del pulso de N entre el modelo cinético upstream (fila `pulso_nut` del workbook, 0.08 kg/m³) y la capa CO2 (cruce de densidad 1040 + dosis de protocolo 0.14 kg/m³) para LAB004–LAB012, incluido LAB009. Verifica origen t=0 común, reproduce `natural_nutrient_pulse_schedule` contra `effective_nutrient_pulses.csv`, y entrega tabla resumen por lote y 3 figuras multipanel (CO2+N combinado, CO2 global, N global). Solo diagnóstico: sin recalibración ni cambios de tiempos/dosis; sin artefactos CSV/PNG adicionales.
