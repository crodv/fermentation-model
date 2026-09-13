# work_state: consistencia de theta y recalibración de la capa CO₂

Estado operativo compacto. Los resultados detallados están en los CSV/notebooks enlazados; este
archivo no es una bitácora.

## Estado actual

La variante full-theta de la calibración cross-matrix quedó implementada y ejecutada con
`SCCM_CORRECTED = 0.0404391928807947 g L⁻¹ h⁻¹ SCCM⁻¹`. Conserva datos, exclusiones, holdouts,
preprocesamiento, objetivo, pesos, bounds, multistart, gate, O₂, pulso, comparadores,
identificabilidad, perfiles, LOO, filtro y transferencia del SOURCE histórico.

El baseline A se reproduce sobre el soporte SCCM-corregido previo (diferencia máxima de predicción
`5.6e-16`). Esto permite que A→B cambie únicamente theta; los artefactos LEGACY y SCCM-corregidos
previos permanecen inmutables.

## Theta canónicos y uso

Los tres CSV se cargan explícitamente y pasan validación exacta 17/17 antes de simular; no hay
relleno desde `DEFAULT_THETA` en B/C.

| Rol | CSV | Uso |
| --- | --- | --- |
| Natural | `laboratory_2026/results/estimability_historical_natural/theta_natural_full.csv` | Drivers de batches naturales |
| Sintético | `laboratory_2026/results/estimability_historical_synthetic_plus_lot2/theta_synthetic_full.csv` | Drivers de batches sintéticos |
| Conjunto | `shared/results/new_must_glycerol_overnight_validation/theta_multistart_07.csv` | Referencia validada; no reemplaza el theta de la matriz objetivo en la lógica cross-matrix original |

Inconsistencia histórica: `_load_theta()` iniciaba desde `base.DEFAULT_THETA` y sobreescribía las 11
filas de `theta.csv`/`theta_by_case.csv`; `sN`, `qXG`, `qXF`, `sG`, `sF` y `m0` quedaban en defaults
en vez de tomar los valores congelados de `multistart_07`.

## Artefactos nuevos

- Runner: `laboratory_2026/run_co2_matrix_cross_validation_2026_full_theta.py`
- SOURCE: `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026_full_theta.ipynb`
- EXECUTED: `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026_full_theta.executed.ipynb`
- Resultados: `laboratory_2026/results/co2_matrix_cross_validation_2026_full_theta_sccm_corrected/`

Verificación: SOURCE sin outputs/counts; EXECUTED con 12/12 celdas de código ejecutadas, 0 errores;
código y Markdown idénticos; 81 artefactos (16 figuras).

## Comparación de estados — hechos numéricos

WSSE con todos los parámetros CO₂ congelados al evaluar cada estado:

| Matriz | A histórico | B full theta, sin refit | C full theta, refit | A→B | B→C | A→C |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sintético | 19.516 | 27.810 | 18.909 | +42.5% | −32.0% | −3.1% |
| Natural | 27.952 | 54.473 | 29.342 | +94.9% | −46.1% | +5.0% |
| Total | 47.468 | 82.283 | 48.251 | +73.3% | −41.4% | +1.7% |

El cambio A→B es mayormente multiplicativo en sintético (93–97% del cambio cuadrático explicado
por escala; correlación de forma 0.993–0.998). En natural es mixto: LAB004/005/007/008 conservan
correlación 0.956–0.967, pero LAB010/011 cambian integral a 0.79/0.71 de A y desplazan el peak
−10/−9 h; LAB012 solo explica 25% por escala. Batches más sensibles por RMSE entre predicciones:
DOE-F06 0.168, LAB012 0.130, LAB005 0.128, LAB004 0.116, LAB007 0.115 y LAB008 0.115 g/L/h.

## Cambios CO₂ y matrix_gain — hechos numéricos

`matrix_gain` es escala empírica de observación, no recuperación física de gas.

| Matriz | A/B | C | Cambio | Diagnóstico de compensación |
| --- | ---: | ---: | ---: | --- |
| Sintético | 1.4599 | 1.1496 | −0.3103 (−21.3%) | Compensa casi exactamente el aumento upstream: ratio integral gain-only 1.007; final C/A 1.010 |
| Natural | 2.1390 | 1.5423 | −0.5967 (−27.9%) | Compensación parcial: gain-only 0.855; final C/A 0.888 |

Otros cambios A→C: sintético `kCO2_release_h` +57.6% y `CO2sat_scale` +42.5%; los parámetros de
O₂, pulso y gate cambian <6% y se mantienen tres límites activos. Natural cambia
`kCO2_release_h` −31.9%, `CO2sat_scale` +614% (límite superior), `O2_qmax_mg_gdw_h` +1934%,
`O2_initial_scale` +660% (cerca del superior) y duración de activación −24.7%; `pulse_t_rise_h`
permanece casi igual y `pulse_activity_gain` sigue en el límite inferior.

## Holdouts, transferencia e identificabilidad

- Holdout sintético DOE-F06: RMSE A/B/C = 0.168/0.188/0.152; C mejora A 9.6%.
- Holdout natural LAB012: 0.219/0.278/0.267; C queda 22.3% peor que A, aunque el error de onset
  mejora de −10.6 a −8.9 h.
- Transferencia natural→sintético: 0.224/0.120/0.223; la mejora accidental de B no persiste tras
  refit y C queda casi igual a A.
- Transferencia sintético→natural: 0.263/0.336/0.345; C empeora A 31.1% y la correlación cae
  0.391→0.082.
- Jacobiano sintético: ya era mal condicionado y pasa de `2.9e7` a `9.1e10`; inicio/duración
  permanecen en límites y perfectamente correlacionados localmente.
- Jacobiano natural: pasa de condición `1.3e2` a `1.4e7`; aparecen correlaciones casi singulares
  O₂ (`−1.000`) y `CO2sat_scale`–`kCO2_release_h` (`0.994`). LOO mejora la estabilidad de duración
  (rango relativo 0.689→0.137), pero empeora la de inicio (0.124→0.278).

## Problemas abiertos y siguiente paso

- C recupera el WSSE agregado histórico (+1.7%), pero no el comportamiento natural ni su holdout;
  no adoptar sus parámetros naturales como estimaciones físicas resueltas mientras persistan bounds
  activos y mala condición.
- La suite original no define una métrica operacional de tail; no se inventó una en esta fase.
- Siguen fuera de alcance: ΔN 0.08/0.14, timing 1040, nueva dinámica del boost, gate/O₂ nuevos,
  ecuaciones nuevas y LAB016–018.
- Siguiente paso recomendado: revisar la compensación estructural natural (`CO2sat_scale`, release y
  par O₂) usando estos perfiles/LOO y el holdout LAB012 antes de mezclar cualquiera de las
  correcciones upstream pendientes.
