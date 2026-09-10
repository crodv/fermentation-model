# Bitácora — corrección SCCM de CO₂ 2026

## Identificación y artefactos

- Rama: `experiment/co2-sccm-correction`.
- Commit base verificado: `bdbae79a38f2331751fd785a2701b8d679b7e91a`.
- El commit base se conserva como trazabilidad histórica; el notebook informa el `HEAD` actual por separado y no exige que continúe siendo igual después de futuros commits.
- Estado inicial: limpio.
- Fecha de ejecución: 2026-09-10.
- Objetivo: aislar el efecto de corregir SCCM → g L⁻¹ h⁻¹ en la capa de CO₂.
- Notebook histórico: `fermentation_model/laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.ipynb` y su snapshot `.executed.ipynb`.
- Único cambio histórico: una primera celda Markdown que identifica la calibración como LEGACY y prohíbe migrarla a la conversión nueva. No se ejecutó nuevamente.
- **ARTEFACTO CANÓNICO:** `fermentation_model/laboratory_2026/notebooks/co2_sccm_correction_experiment_2026.ipynb`.
- **SNAPSHOT DE EJECUCIÓN:** `fermentation_model/laboratory_2026/notebooks/co2_sccm_correction_experiment_2026.executed.ipynb`.
- Resultados secundarios: `fermentation_model/laboratory_2026/results/co2_matrix_cross_validation_2026_sccm_corrected/`.
- Código reutilizado/refactorizado: `fermentation_model/laboratory_2026/run_co2_matrix_cross_validation_2026.py`.
- Limpieza arquitectónica posterior: el generador, ejecutor, rutas de notebook y CLI específicos de SCCM se retiraron del runner. El `.ipynb` SOURCE quedó como única fuente canónica de presentación y ejecución.

El notebook canónico es la fuente de verdad. Esta bitácora no lo sustituye.

## Alcance

Se mantuvieron los mismos batches, theta upstream, estructura de modelo, parámetros ajustables, bounds, starts, semilla y optimizador. OLD se leyó de los resultados históricos guardados y no se reoptimizó. NEW sí se optimizó con cinco starts por matriz y profiling analítico libre de `matrix_gain`.

Quedaron fuera `sN`, `qXG`, `qXF`, `sG`, `sF`, `m0`, ΔN, theta upstream, estructura nutricional, condiciones iniciales, LAB013–018 y cualquier cambio de ecuaciones. La misma conversión es compartida por natural y sintético; sintético se preservó como resultado secundario y el análisis principal es natural.

## Conversión y cadena real encontrada

La ruta calibrable histórica fue:

`sensor_flow_sccm` → soporte químico → `apply_sensor_zero_correction` (offset nativo) → SCCM a g/L/h + clipping → filtro de artefactos → bin horario → mediana/Savitzky–Golay → LOD/censura → sigma/pesos → `_fit_residual`/`fit_matrix` → `_profile_matrix_gain` → `predict_and_score`.

La fórmula legacy estaba duplicada en el baseline limpio:

1. `apply_sensor_zero_correction`: ruta realmente usada por el fitting.
2. `_sccm_to_g_l_h`: usada sólo por `_natural_early_sensor_rows`, cargador descriptivo de LAB001–003 que no participa en calibración y no era llamado por `load_co2_data`.

El refactor eliminó la duplicación matemática haciendo que la ruta calibrable llame a `_sccm_to_g_l_h` con una `SCCMConversion` explícita. LEGACY sigue siendo el default, por lo que el comportamiento histórico no se reemplazó.

| magnitud | LEGACY | SCCM_CORRECTED |
| --- | ---: | ---: |
| MW CO₂ [g/mol] | 44.01 | 44.0095 |
| Vm [L/mol] | 22.414 | 24.16 |
| K_CO₂ | 1.0 implícito | 0.74 |
| factor a 2 L [g L⁻¹ h⁻¹ SCCM⁻¹] | 0.0589051485678594 | 0.0404391928807947 |
| NEW/OLD | 1.0 | 0.686513723570501 |
| reducción | 0 % | 31.3486276429499 % |

## Máscara, thresholds, sigma y pesos

La comparación primaria transforma la observación histórica ya corregida de cero, filtrada, agregada y suavizada por el ratio 0.686513723570501. Conserva exactamente cada `(matrix, batch, t_h)` y el booleano `left_censored`. Los límites numéricos de detección se escalan por el ratio para representar el mismo SCCM equivalente.

| batch natural | N raw | N total | N usado OLD | N usado NEW frozen | diferencias de máscara | timestamps distintos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LAB004 | 962 | 162 | 97 | 97 | 0 | 0 |
| LAB005 | 962 | 162 | 119 | 119 | 0 | 0 |
| LAB006 | 1250 | 210 | 139 | 139 | 0 | 0 |
| LAB007 | 960 | 161 | 101 | 101 | 0 | 0 |
| LAB008 | 960 | 161 | 114 | 114 | 0 | 0 |
| LAB010 | 1100 | 185 | 84 | 84 | 0 | 0 |
| LAB011 | 955 | 161 | 76 | 76 | 0 | 0 |
| LAB012 | 955 | 161 | 98 | 98 | 0 | 0 |

Los umbrales absolutos históricos encontrados fueron: gates de artefacto 0.04 y 0.05 g L⁻¹ h⁻¹, caída mínima 0.05, spike mínimo 0.08, LOD estándar 0.05, LOD frío 0.10, floor de sigma 0.04 y umbral diagnóstico de primera emisión 0.005. Su origen histórico en g/L/h versus SCCM no está documentado inequívocamente, por lo que se clasificaron C. Para aislar la conversión se congelaron las decisiones de artefacto/censura y se escalaron LOD, floor de sigma y umbral diagnóstico. Los ratios, el 10 % del peak, el setpoint frío y los floors adimensionales del modelo se mantuvieron.

La pasada descriptiva *native-corrected*, que reaplica literalmente los thresholds históricos a la señal corregida, mantuvo todos los timestamps pero cambió 76 estados de censura y 7 estados horarios de artefacto en los ocho batches naturales. No se usó para el fit principal.

El objetivo conserva `sigma = max(floor, 0.10 × peak)`. El floor ambiguo se escaló a 0.0274605489428200 g L⁻¹ h⁻¹; la normalización por `sqrt(N_batch)`, los términos temporales y los pesos restantes permanecieron iguales. Así el objetivo queda dimensionalmente comparable sin inventar una justificación física independiente para 0.04.

## Check pre-fit LAB004

El peak y la integral NEW/OLD fueron 0.686513723570501; el peak time, los 162 timestamps y la forma normalizada se conservaron. La máxima diferencia temporal fue 0 y la correlación entre formas normalizadas fue 1.0.

## Parámetros naturales OLD vs NEW

| parámetro | OLD histórico | SCCM_CORRECTED | Δ abs | Δ % | LB | UB | cota OLD | cota NEW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| kCO2_release_h | 0.424588271353232 | 0.424382003527665 | -0.000206267825567 | -0.0485806697 | 0.03 | 25 | no | no |
| CO2sat_scale | 0.351389541106575 | 0.350040148560741 | -0.001349392545834 | -0.3840161382 | 0.35 | 2.5 | sí | sí |
| O2_qmax_mg_gdw_h | 0.150000000000000 | 0.150000000000010 | 1.03e-14 | 6.85e-12 | 0.15 | 6 | sí | sí |
| O2_initial_scale | 0.195399665650891 | 0.195483596863756 | 0.000083931212865 | 0.0429536113 | 0.05 | 1.5 | no | no |
| pulse_t_rise_h | 64.6587037463382 | 64.6592211849181 | 0.000517438579891 | 0.0008002613 | 1 | 72 | no | no |
| pulse_activity_gain | 0.250000000000000 | 0.250000000000000 | 0 | 0 | 0.25 | 4 | sí | sí |
| chem_activation_start_fraction | 0.735056695858678 | 0.735179321542847 | 0.000122625684169 | 0.0166824797 | 0.01 | 0.95 | no | no |
| chem_activation_duration_fraction | 1.06390986813574 | 1.06378309356724 | -0.000126774568503 | -0.0119159125 | 0.35 | 2 | no | no |
| matrix_gain | 3.11575694437827 | 2.13901091312015 | -0.976746031258114 | -31.3485951791 | 0.1 | 20 | no | no |

`matrix_gain` esperado por puro scaling fue 2.13900990162577. El valor reestimado difirió en +1.01149438e-6 (+0.00004728797 %) y absorbió 99.9998964425 % del descenso esperado. No se impuso el esperado al optimizador.

El mayor movimiento dinámico fue `CO2sat_scale` (-0.3840 %), seguido por `kCO2_release_h` (-0.0486 %) y `O2_initial_scale` (+0.0430 %). Son movimientos pequeños, aunque `CO2sat_scale`, `O2_qmax_mg_gdw_h` y `pulse_activity_gain` permanecen en cota; esto y el Jacobiano mal condicionado requieren cautela por correlación/no-identificabilidad.

## Métricas naturales

| batch | rol | RMSE OLD | RMSE NEW | Δ RMSE % | NRMSE OLD | NRMSE NEW | Δ NRMSE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LAB004 | calibration | 0.15729060 | 0.10798850 | -31.3446 | 0.19494766 | 0.19495911 | +1.1449e-5 |
| LAB005 | calibration | 0.07545255 | 0.05181014 | -31.3341 | 0.10687112 | 0.10689368 | +2.2559e-5 |
| LAB006 | calibration | 0.08767194 | 0.06018740 | -31.3493 | 0.21414131 | 0.21413920 | -2.1150e-6 |
| LAB007 | calibration | 0.17283243 | 0.11865277 | -31.3481 | 0.20901629 | 0.20901793 | +1.6381e-6 |
| LAB008 | calibration | 0.09061603 | 0.06220945 | -31.3483 | 0.13379977 | 0.13380043 | +6.5145e-7 |
| LAB010 | calibration | 0.05216077 | 0.03580395 | -31.3585 | 0.13920887 | 0.13918891 | -1.9963e-5 |
| LAB011 | calibration | 0.44302370 | 0.30414674 | -31.3475 | 0.34660681 | 0.34661238 | +5.5722e-6 |
| LAB012 | internal holdout | 0.31833531 | 0.21854640 | -31.3471 | 0.26158138 | 0.26158717 | +5.7950e-6 |

Resumen de los siete batches naturales de calibración (730 observaciones cuantificables): RMSE medio 0.1541497173 → 0.1058284205 y MAE medio 0.1240082079 → 0.0851349983, cambios dominados por la nueva unidad. Las métricas relativas quedaron prácticamente iguales: NRMSE medio 0.1920845485 → 0.1920873760, correlación media 0.8353432954 → 0.8353234816, R² medio 0.4183100036 → 0.4182975250 e integral pred/obs media 0.9994715417 → 0.9994529364. El objetivo global fue 27.9520959262 → 27.9520951910.

Por ΔNRMSE, LAB005 tuvo el mayor deterioro relativo (+2.2559e-5) y LAB010 el mejor cambio relativo (-1.9963e-5). Las magnitudes son numéricamente despreciables; no respaldan una mejora o deterioro de forma.

## Anomalías, interpretación y conclusión

- El efecto directo fue una reducción física de escala de 31.3486 %.
- `matrix_gain` absorbió prácticamente toda esa reducción (99.9999 %).
- Con máscara fija, los parámetros dinámicos persistieron esencialmente iguales; el máximo cambio fue 0.3840 %.
- El descenso del RMSE/MAE absoluto no se interpreta como mejora porque ambos dependen de la unidad.
- Las métricas de forma y relativas quedaron prácticamente iguales.
- La variante native-corrected confirma que reaplicar thresholds absolutos habría mezclado el cambio de conversión con cambios de máscara; por eso quedó sólo como diagnóstico.
- La corrección física no se rechaza por la calidad estadística: corrige unidades, mientras la calidad relativa del fit quedó esencialmente igual.
- No hay evidencia en este experimento aislado de una nueva dinámica biológica.

## Limitaciones y pendientes

- PENDIENTE — parámetros upstream: `sN`, `qXG`, `qXF`, `sG`, `sF`, `m0`.
- PENDIENTE — discrepancia nutricional: ΔN = 0.08 kg/m³ vs ΔN = 0.14 kg/m³.
- PENDIENTE — theta upstream completo y canónico.
- PENDIENTE — recalibración integral consistente upstream → CO₂.
- PENDIENTE — holdout formal LAB016–018.
- PENDIENTE — estructura causal de respuesta a nutrición.
- PENDIENTE — evaluación upstream incorporando LAB013–015.

LAB016–018, sus datos, notebooks, parámetros y replay no fueron tocados.
