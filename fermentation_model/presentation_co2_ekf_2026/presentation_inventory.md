# Inventario trazable para la presentación CO2–EKF 2026

## Alcance y reglas de lectura

- Este paquete no recalibra modelos ni modifica datos. Las nueve figuras experimentales son copias binarias de resultados ya guardados.
- **MS** significa medio sintético y **MN** significa medio natural.
- En laboratorio 2026, DOE-F06 (`lot2_F3`) es el holdout MS y LAB012 es el holdout MN. Los ajustes MS y MN se hicieron por separado y luego se cruzaron sin reajustar CO2.
- El bloque de CO2 se evaluó condicionado a trayectorias upstream ya disponibles; no es todavía una calibración end-to-end de fermentación + observación. Fuente: `laboratory_2026/results/co2_matrix_cross_validation_2026/analysis_manifest.json`.
- La línea del 5 % en los perfiles de identificabilidad es una heurística de sensibilidad, no un intervalo de confianza. Fuente: el mismo manifiesto.

## 1. `co2_state_model_diagram.png`

- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/co2_state_model_diagram.png`.
- **Tipo:** diagrama conceptual nuevo; no contiene ni transforma datos experimentales.
- **Fuentes conceptuales exactas:**
  - `pilot_2025/pilot_2025_co2_solubility_integrated_doe.ipynb`, sección 3: estado disuelto, balance `dC/dt = producción - liberación`, fuente ligada a `r_E` y correlación de solubilidad.
  - `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, funciones `effective_qprod_grid` (líneas 1668–1745) y `raw_qgas_grid_prediction` (líneas 1748–1801): activación, O2, pulso N, liberación continua y balance discreto de masa.
  - `laboratory_2026/results/co2_matrix_cross_validation_2026/analysis_manifest.json`: alcance, formulación vigente y variables estimadas.
- **Modelos representados:** estados upstream `[S,N,X,E]`, fuente biológica, modulación O2/activación/pulso N, estado disuelto `C_d`, flujo gaseoso `q_gas` y observación del sensor.
- **Qué demuestra:** la hipótesis de integración propuesta y la separación entre producción biológica, almacenamiento/liberación y medición.
- **Qué NO permite concluir:** no demuestra observabilidad, estabilidad del EKF, identificabilidad conjunta ni validez universal de los parámetros.
- **Slide recomendada:** 2 y 7.
- **Mensaje principal:** el sensor no mide directamente los estados ni `q_prod`; mide una transformación del flujo liberado desde un estado disuelto.

## 2. `co2_benchmark_25170.png`

- **Ruta original exacta:** `pilot_2025/results/co2_solubility_integrated_doe/plots/co2_benchmark/co2_benchmark_25170.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/co2_benchmark_25170.png`.
- **Notebook:** `pilot_2025/pilot_2025_co2_solubility_integrated_doe.executed.ipynb`.
- **Script generador:** `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py`, `plot_co2_benchmark` (líneas 1449–1466).
- **Datos/resultados usados:** `co2_predictions_all.csv`, `co2_metrics_all.csv`, `co2_model_selection_summary.csv` y observaciones curadas en `co2_downsampled.csv`, todos bajo `pilot_2025/results/co2_solubility_integrated_doe/`.
- **Modelos mostrados:** `instant`, `old_lag_threshold`, `solubility_fixed`, `solubility_scaled`, `solubility_o2_literature`, `solubility_o2_qfit` y `solubility_o2_slow_transition`.
- **Qué demuestra:** en el lote 25170, la formulación seleccionada con reservorio disuelto y transición O2 reproduce mucho mejor el ascenso tardío que el proxy instantáneo; para ese lote, RMSE cambia de 0.384 a 0.240 L/min y la correlación de 0.328 a 0.843.
- **Qué NO permite concluir:** no es un holdout, no compara MS/MN y no valida por sí sola los parámetros en otra campaña o escala.
- **Slide recomendada:** 3.
- **Mensaje principal:** una relación algebraica instantánea entre `r_E` y el sensor no explica el retardo ni la forma temporal; hace falta memoria dinámica entre producción y salida gaseosa.

## 3. `initial_gradual_release_comparison.png`

- **Ruta original exacta:** `laboratory_2026/results/co2_matrix_cross_validation_2026/figures/initial_gradual_release_comparison.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/initial_gradual_release_comparison.png`.
- **Notebook:** `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.executed.ipynb`.
- **Script generador:** `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, `plot_initial_release_comparison` (líneas 3309–3406).
- **Datos/resultados usados:** `prediction_rows.csv`, `threshold_release_prediction_rows.csv`, `batch_metrics.csv` y `threshold_release_batch_metrics.csv`.
- **Modelos mostrados:** `solubility_o2_nitrogen_boost_threshold_release` frente a `solubility_o2_nitrogen_boost_continuous_release`, ambos junto a la curva observada.
- **Qué demuestra:** el umbral rígido produce una meseta de emisión exactamente nula y una salida abrupta; la vía continua permite flujo desde que existe CO2 disuelto y suaviza el ascenso inicial.
- **Qué NO permite concluir:** no mide `C_d`, no separa experimentalmente activación biológica de transferencia y la mejora de onset/RMSE no es uniforme en todos los holdouts.
- **Slide recomendada:** 3.
- **Mensaje principal:** el reservorio dinámico debe conservarse, pero la liberación debe ser continua y no activarse mediante un corte rígido en `C_d-C*`.

## 4. `nutrient_pulse_response_comparison.png`

- **Ruta original exacta:** `laboratory_2026/results/co2_matrix_cross_validation_2026/figures/nutrient_pulse_response_comparison.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/nutrient_pulse_response_comparison.png`.
- **Notebook:** `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.executed.ipynb`.
- **Script generador:** `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, `plot_pulse_response_comparison` (líneas 3219–3305).
- **Datos/resultados usados:** `prediction_rows.csv`, `threshold_release_prediction_rows.csv`, `batch_metrics.csv`, `threshold_release_batch_metrics.csv`, `source_transition_diagnostics.csv` y `effective_nutrient_pulses.csv`.
- **Modelos mostrados:** liberación continua actual y comparador por umbral, con instante del pulso N y término de la respuesta ajustada.
- **Qué demuestra:** el pulso se incorpora causalmente como diferencia entre trayectorias upstream con/sin N, con una disponibilidad gradual; es la mejor figura de laboratorio 2026 para mostrar el pulso y la respuesta posterior de CO2.
- **Qué NO permite concluir:** la cercanía temporal no prueba causalidad, varios paneles son ajustes en muestra y el tiempo de pulso MN puede depender de cruces de densidad con intervalos de 16–72 h.
- **Slide recomendada:** 4.
- **Mensaje principal:** la respuesta a N no es un salto instantáneo: MS ajusta `t_rise=37.0 h`, ganancia 1.244; MN ajusta `t_rise=64.7 h`, ganancia 0.25 en la cota inferior.

## 5. `calibration_overlays_synthetic.png`

- **Ruta original exacta:** `laboratory_2026/results/co2_matrix_cross_validation_2026/figures/calibration_overlays_synthetic.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/calibration_overlays_synthetic.png`.
- **Notebook:** `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.executed.ipynb`.
- **Script generador:** `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, `plot_calibration_overlays` (líneas 2856–2923).
- **Datos/resultados usados:** `prediction_rows.csv`, `batch_metrics.csv`, `co2_observations_hourly.csv` y `effective_nutrient_pulses.csv`.
- **Modelos mostrados:** ajuste del modelo vigente sobre las cuatro fermentaciones MS de calibración: DOE-F01, DOE-F03, DOE-F04 y DOE-F05.
- **Qué demuestra:** calidad y heterogeneidad del ajuste en MS; RMSE por lote 0.124, 0.123, 0.098 y 0.316 g L^-1 h^-1.
- **Qué NO permite concluir:** no contiene DOE-F06 como calibración, no es evidencia holdout y no demuestra transferencia a MN.
- **Slide recomendada:** 4 como alternativa o respaldo.
- **Mensaje principal:** el bloque reproduce bien tres ensayos MS, pero DOE-F05 conserva una discrepancia de amplitud importante.

## 6. `calibration_overlays_natural.png`

- **Ruta original exacta:** `laboratory_2026/results/co2_matrix_cross_validation_2026/figures/calibration_overlays_natural.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/calibration_overlays_natural.png`.
- **Notebook:** `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.executed.ipynb`.
- **Script generador:** el mismo `plot_calibration_overlays` (líneas 2856–2923).
- **Datos/resultados usados:** `prediction_rows.csv`, `batch_metrics.csv`, `co2_observations_hourly.csv`, `natural_nutrient_pulse_details.csv` y `effective_nutrient_pulses.csv`.
- **Modelos mostrados:** ajuste del modelo vigente sobre siete fermentaciones MN de calibración: LAB004–008, LAB010 y LAB011.
- **Qué demuestra:** buena reproducción en LAB005, LAB006, LAB008 y LAB010, con fallas visibles en forma/amplitud en otros ensayos; RMSE abarca 0.052–0.443 g L^-1 h^-1.
- **Qué NO permite concluir:** no contiene LAB012 como calibración y no valida transferencia fuera de MN.
- **Slide recomendada:** 4 como alternativa o respaldo junto con la figura MS.
- **Mensaje principal:** MN no se comporta como una matriz homogénea; LAB011 domina la limitación del ajuste nativo.

## 7. `heldout_cross_matrix_validation.png`

- **Ruta original exacta:** `laboratory_2026/results/co2_matrix_cross_validation_2026/figures/heldout_cross_matrix_validation.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/heldout_cross_matrix_validation.png`.
- **Notebook:** `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.executed.ipynb`.
- **Script generador:** `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, `plot_validation` (líneas 2927–2990).
- **Datos/resultados usados:** `prediction_rows.csv` y `validation_summary.csv`; DOE-F06 y LAB012 nunca se usan en los ajustes correspondientes.
- **Modelos mostrados:** parámetros MS y MN aplicados dentro de matriz y cruzados MS→MN/MN→MS sin reajuste.
- **Qué demuestra:** RMSE holdout MS→MS 0.245, MN→MN 0.318, MS→MN 0.382 y MN→MS 0.326 g L^-1 h^-1; la transferencia es asimétrica y el ajuste de forma puede mantenerse aun con sesgo de amplitud.
- **Qué NO permite concluir:** hay un solo holdout por matriz, no estima incertidumbre poblacional y no prueba universalidad entre escalas.
- **Slide recomendada:** 5.
- **Mensaje principal:** la estructura transfiere parcialmente, pero los parámetros no son todavía comunes a MS y MN.

## 8. `activation_identifiability_profiles.png`

- **Ruta original exacta:** `laboratory_2026/results/co2_matrix_cross_validation_2026/figures/activation_identifiability_profiles.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/activation_identifiability_profiles.png`.
- **Notebook:** `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.executed.ipynb`.
- **Script generador:** `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, `plot_activation_identifiability` (líneas 3462–3516).
- **Datos/resultados usados:** `activation_objective_profiles.csv`, `activation_leave_one_batch_out_summary.csv`, `activation_jacobian_identifiability.csv`, `activation_jacobian_singular_values.csv` y `activation_local_parameter_correlations.csv`.
- **Modelos mostrados:** perfiles reoptimizados de fracción de inicio y duración de activación, separados para MS y MN.
- **Qué demuestra:** MS queda esencialmente plano y ambos parámetros permanecen en cotas inferiores; su Jacobiano de ocho parámetros tiene condición 2.36e11. MN tiene condición 129.9, pero la duración cambia 69 % respecto del estimado completo al omitir lotes.
- **Qué NO permite concluir:** el umbral del 5 % no es un intervalo de confianza y el diagnóstico es local/condicionado a drivers upstream fijos.
- **Slide recomendada:** 6.
- **Mensaje principal:** una curva online de CO2 puede informar algunas combinaciones, pero no separar de manera robusta los ocho parámetros de forma, especialmente en MS.

## 9. `co2_o2_current_relative_eigenvalues.png`

- **Ruta original exacta:** `pilot_2025/results/co2_solubility_integrated_doe/plots/fim/co2_o2_current_relative_eigenvalues.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/co2_o2_current_relative_eigenvalues.png`.
- **Notebook:** `pilot_2025/pilot_2025_co2_solubility_integrated_doe.executed.ipynb`, sección 5.
- **Script generador:** `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py`, `plot_eigen_spectrum` (líneas 1546–1557).
- **Datos/resultados usados:** `co2_o2_eigen_spectrum_current.csv`, `co2_o2_fim_current.csv`, `co2_o2_fim_metrics_current.json` y `co2_o2_parameter_estimability_current.csv`.
- **Modelos mostrados:** FIM enfocado solo en `kCO2_release_h` y `CO2sat_scale` del modelo piloto 2025 seleccionado.
- **Qué demuestra:** para ese bloque reducido de dos parámetros, condición FIM 3.26; `kCO2_release_h` se clasifica bien estimado y `CO2sat_scale` moderado.
- **Qué NO permite concluir:** no evalúa los ocho parámetros del modelo 2026 ni la observabilidad conjunta de `[S,N,X,E,C_d]`; tampoco representa una FIM completa del EKF.
- **Slide recomendada:** 6 como contraste histórico/auxiliar.
- **Mensaje principal:** el bloque de dos parámetros era manejable; la identificabilidad se deteriora al ampliar la formulación 2026 sin agregar mediciones independientes.

## 10. `pilot_2026_cross_scale_transfer.png`

- **Ruta original exacta:** `pilot_2026/results/co2_solubility_cross_lot_validation_2026/figures/cross_scale_transfer.png`.
- **Ruta en el paquete:** `presentation_co2_ekf_2026/figures/pilot_2026_cross_scale_transfer.png`.
- **Notebook:** `pilot_2026/notebooks/pilot_2026_co2_solubility_cross_lot_validation.executed.ipynb`.
- **Script generador:** `pilot_2026/run_co2_solubility_cross_lot_validation_2026.py`, `plot_cross_scale_transfer` (líneas 1116–1142).
- **Datos/resultados usados:** `cross_scale_prediction_rows.csv`, `cross_scale_validation.csv` y los ajustes de laboratorio registrados por el análisis piloto.
- **Modelos mostrados:** parámetros de laboratorio MS/MN transferidos a piloto y ajuste piloto agrupado transferido a los holdouts de laboratorio.
- **Qué demuestra:** la estructura puede conservar forma en algunos cruces, pero la magnitud y el onset no son estables; por ejemplo, el ajuste piloto agrupado sobre el holdout MS de laboratorio obtiene RMSE 0.270 y R2 0.528, mientras sobre LAB012 obtiene RMSE 0.390 y R2 -0.244.
- **Qué NO permite concluir:** no es una calibración conjunta multi-escala y mezcla diferencias de reactor, sensor, lote y matriz.
- **Slide recomendada:** 5 como respaldo si se necesita discutir escala además de MS/MN.
- **Mensaje principal:** transferir la estructura es razonable; congelar un único vector de parámetros entre laboratorio y piloto todavía no está respaldado.

## Archivos numéricos centrales

- Laboratorio 2026: `laboratory_2026/results/co2_matrix_cross_validation_2026/{fit_parameters.csv,validation_summary.csv,batch_metrics.csv,model_comparison_validation.csv,effective_nutrient_pulses.csv,activation_jacobian_identifiability.csv,activation_leave_one_batch_out_summary.csv,activation_objective_profiles.csv}`.
- Piloto 2025: `pilot_2025/results/co2_solubility_integrated_doe/{co2_model_selection_summary.csv,co2_metrics_selected.csv,co2_o2_parameter_estimability_current.csv,co2_o2_fim_metrics_current.json}`.
- Piloto 2026: `pilot_2026/results/co2_solubility_cross_lot_validation_2026/{validation_summary.csv,cross_scale_validation.csv,fit_parameters.csv,activation_jacobian_identifiability.csv}`.

