# Plan de presentación: integración CO2 y preparación del EKF

Exactamente 8 slides. **MS:** medio sintético. **MN:** medio natural. Las cifras citadas también están consolidadas en `presentation_metrics.csv`.

## Slide 1 — Objetivo y problema

- **Pregunta que responde:** ¿por qué el CO2 gaseoso no puede conectarse directamente a un estimador de estados biológicos?
- **Mensajes clave (máximo 3):**
  1. El sensor observa la salida gaseosa, no directamente producción biológica, biomasa, nitrógeno, azúcar ni etanol.
  2. Entre el modelo upstream y el sensor existen activación metabólica, almacenamiento disuelto, transferencia gas–líquido y ganancia del sensor.
  3. El resultado 2026 calibra esta capa condicionado a drivers upstream fijos; todavía no es una calibración end-to-end ni un EKF validado.
- **Figura recomendada:** `figures/co2_state_model_diagram.png`, usando solo la mitad inferior si se necesita más espacio para el planteamiento.
- **Números importantes:** 13 fermentaciones calibrables en laboratorio 2026; 5 experimentos excluidos por perfiles de CO2 no confiables; 2 holdouts completos (DOE-F06 para MS y LAB012 para MN).
- **Ecuaciones mínimas:** `y_CO2 != q_prod`; `y_CO2 ≈ g_m q_gas`.
- **Fuente de cifras y alcance:** `laboratory_2026/results/co2_matrix_cross_validation_2026/{experiment_inventory.csv,analysis_manifest.json}`.
- **Conclusión en una frase:** antes de estimar estados hay que representar explícitamente la dinámica que transforma producción biológica en la señal gaseosa medida.

## Slide 2 — Estructura actual del modelo CO2

- **Pregunta que responde:** ¿cómo se conecta hoy el modelo dinámico de fermentación con el CO2 observado?
- **Mensajes clave (máximo 3):**
  1. El modelo upstream entrega `r_E`, biomasa y respuesta a N; la fuente base de CO2 se obtiene estequiométricamente desde etanol, pero la capa de observación es fenomenológica/dinámica.
  2. O2, la activación química y el pulso N modulan `q_prod`; `C*_CO2(T,E,azúcares)` modula la liberación desde `C_d`.
  3. La formulación vigente es `solubility_o2_nitrogen_boost_continuous_release`; O2 es una variable interna/efectiva, no una medición online exigida al EKF.
- **Figura recomendada:** `figures/co2_state_model_diagram.png` completa.
- **Números importantes:** 9 parámetros ajustados por matriz; piso fijo de liberación continua `f0=0.05`; grilla dinámica de drivers `0.25 h`; observaciones de ajuste agregadas a `1 h`.
- **Ecuaciones mínimas:**
  - `q_bio = [44.01/(2·46.07)] r_E`.
  - `q_prod = a_chem(t)[q_bio f_ferm(O2,N) + q_resp]`.
  - `C* = s_CO2·1.69·exp[-0.032(T-20)]·exp(0.0016E)·exp[-0.0012(G+F)]`.
  - `q_gas = k_release C_d[f0+(1-f0)C_d/(C_d+C*)]`.
- **Fuentes:** `pilot_2025/pilot_2025_co2_solubility_integrated_doe.ipynb`, sección 3; `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, líneas 1668–1801; `laboratory_2026/results/co2_matrix_cross_validation_2026/analysis_manifest.json`.
- **Conclusión en una frase:** el vínculo final es híbrido: fuente biológica con base estequiométrica más una capa fenomenológica de activación, almacenamiento, transferencia y medición.

## Slide 3 — qCO2 algebraico versus CO2 disuelto dinámico

- **Pregunta que responde:** ¿la memoria dinámica en `C_d` está respaldada por los resultados guardados?
- **Mensajes clave (máximo 3):**
  1. En piloto 2025, el proxy instantáneo anticipa la emisión de 25170 y no reproduce su ascenso tardío.
  2. El reservorio disuelto + transición O2 reduce fuertemente el error conjunto y mejora la forma de 25170.
  3. En laboratorio 2026, la liberación continua elimina la meseta exactamente nula del comparador por umbral, aunque la mejora holdout no es uniforme en todos los escenarios.
- **Figuras recomendadas:** principal `figures/co2_benchmark_25170.png`; apoyo `figures/initial_gradual_release_comparison.png`.
- **Números importantes:** WSSE `240.79 → 124.65`; BIC `246.50 → 136.07`; en 25170 RMSE `0.384 → 0.240 L/min`; correlación `0.328 → 0.843`.
- **Ecuaciones mínimas:** algebraico `q_sensor ∝ r_E`; dinámico `dC_d/dt=q_prod-q_gas` y `q_gas=k_release C_d φ(C_d,C*)`.
- **Fuentes:** `pilot_2025/results/co2_solubility_integrated_doe/{co2_model_selection_summary.csv,initial_fit_metrics.csv,co2_metrics_selected.csv}`; comparación continua/umbral en `laboratory_2026/results/co2_matrix_cross_validation_2026/model_comparison_validation.csv`.
- **Conclusión en una frase:** la evidencia favorece conservar `C_d` como memoria dinámica y usar liberación continua en vez de un proxy algebraico o un umbral rígido.

## Slide 4 — Calibración 2026 e integración de pulsos de N

- **Pregunta que responde:** ¿cómo se calibró el bloque 2026 y qué efecto de N está realmente incluido?
- **Mensajes clave (máximo 3):**
  1. Los parámetros se ajustaron por separado con 4 fermentaciones MS y 7 MN; DOE-F06 y LAB012 quedaron fuera del ajuste.
  2. El pulso usa la diferencia causal entre simulaciones upstream con/sin N; su disponibilidad sigue una rampa y la actividad puede cambiar sin exigir crecimiento de biomasa.
  3. Los parámetros de pulso difieren fuertemente entre matrices y la ganancia MN queda en la cota inferior, por lo que el mecanismo no está identificado como universal.
- **Figura recomendada:** `figures/nutrient_pulse_response_comparison.png`; respaldo de ajuste en `figures/calibration_overlays_synthetic.png` y `figures/calibration_overlays_natural.png`.
- **Números importantes:** MS `t_rise=36.995 h`, `gain=1.244`; MN `t_rise=64.659 h`, `gain=0.250` en cota inferior; pulsos modelados de hasta `0.05 kg m^-3` en MS y `0.14 kg m^-3` en MN.
- **Ecuaciones mínimas:** `f_Npulse=clip[(t-t_pulse)/t_rise,0,1]`; `m_activity=1+(gain-1)f_Npulse`.
- **Fuentes:** `laboratory_2026/results/co2_matrix_cross_validation_2026/{fit_parameters.csv,effective_nutrient_pulses.csv,natural_nutrient_pulse_details.csv,source_transition_diagnostics.csv}`; implementación en `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, líneas 1653–1705.
- **Conclusión en una frase:** el pulso de N está integrado de forma causal y gradual, pero sus parámetros siguen siendo específicos de matriz y parcialmente confundidos.

## Slide 5 — Replicabilidad y transferencia MS/MN

- **Pregunta que responde:** ¿un parámetro calibrado en una matriz reproduce la curva de la otra sin reajuste?
- **Mensajes clave (máximo 3):**
  1. La validación es estricta: DOE-F06 y LAB012 no participan en los ajustes correspondientes.
  2. Dentro de dominio se conserva mejor la amplitud; el cruce MN→MS mantiene alta correlación pero con sesgo, mientras MS→MN pierde forma y onset.
  3. La estructura puede transferirse como hipótesis, pero un único vector de parámetros MS/MN no está respaldado.
- **Figura recomendada:** `figures/heldout_cross_matrix_validation.png`; evidencia adicional de escala en `figures/pilot_2026_cross_scale_transfer.png`.
- **Números importantes:** RMSE MS→MS `0.245`; MN→MN `0.318`; MS→MN `0.382`; MN→MS `0.326 g L^-1 h^-1`.
- **Ecuaciones mínimas:** no agregar una ecuación; mostrar la matriz 2×2 de transferencia con filas = calibración y columnas = objetivo.
- **Fuente:** `laboratory_2026/results/co2_matrix_cross_validation_2026/validation_summary.csv`. Respaldo de escala: `pilot_2026/results/co2_solubility_cross_lot_validation_2026/cross_scale_validation.csv`.
- **Conclusión en una frase:** la transferencia entre MS y MN es parcial y asimétrica, así que el EKF debe admitir parámetros de observación por dominio o incertidumbre paramétrica explícita.

## Slide 6 — Identificabilidad con datos 2026 y solo CO2 online

- **Pregunta que responde:** ¿la curva online de CO2 permite identificar simultáneamente todos los parámetros de la capa?
- **Mensajes clave (máximo 3):**
  1. El Jacobiano MS tiene rango numérico completo, pero una dirección prácticamente nula: rango completo no equivale a identificabilidad útil.
  2. En MS cuatro parámetros quedan activos en cotas; en MN tres quedan en cotas y la duración de activación cambia mucho al omitir lotes.
  3. El FIM piloto 2025 de solo dos parámetros era manejable; ampliar a ocho parámetros de forma sin mediciones independientes introduce confusión severa.
- **Figura recomendada:** `figures/activation_identifiability_profiles.png`; apoyo `figures/co2_o2_current_relative_eigenvalues.png`.
- **Números importantes:** `cond(J)_MS=2.36×10^11`; `cond(J)_MN=129.9`; menor singular MS `3.36×10^-11`; rango LOO relativo de duración MN `0.689`.
- **Ecuaciones mínimas:** `J_ij=∂r_i/∂log(theta_j)`; `F=J^T J`.
- **Fuentes:** `laboratory_2026/results/co2_matrix_cross_validation_2026/{activation_jacobian_identifiability.csv,activation_jacobian_singular_values.csv,activation_leave_one_batch_out_summary.csv,fit_parameters.csv}`; contraste de dos parámetros en `pilot_2025/results/co2_solubility_integrated_doe/{co2_o2_fim_metrics_current.json,co2_o2_parameter_estimability_current.csv}`.
- **Conclusión en una frase:** con CO2 como única medición online no es prudente estimar simultáneamente los estados y los ocho parámetros de forma del bloque 2026.

## Slide 7 — Propuesta de modelo de estados `[S,N,X,E,C_d]`

- **Pregunta que responde:** ¿qué modelo mínimo debería linealizar el EKF y qué señales serían entradas/mediciones?
- **Mensajes clave (máximo 3):**
  1. Proponer `x=[S,N,X,E,C_d]^T`; temperatura y adiciones son entradas conocidas, no estados.
  2. `C_d` desacopla producción biológica de salida gaseosa y aporta la memoria exigida por el benchmark.
  3. La única medición online requerida es CO2 gaseoso; `S,N,X,E` offline se reservan para validar estados y CO2 disuelto/O2 serían diagnósticos opcionales.
- **Figura recomendada:** `figures/co2_state_model_diagram.png`.
- **Números importantes:** 5 estados propuestos; 1 canal online principal de medición; 4 variables offline independientes para validación; 2 variables físicas opcionales (`C_d` medido y O2) para discriminar mecanismos.
- **Ecuaciones mínimas:** `x_dot=f(x,u,T;theta)`; `dC_d/dt=q_prod(x,u,T)-q_gas(C_d,T,E,S)`; `y_CO2=g_m q_gas+v`.
- **Fuentes:** estructura upstream en `pilot_2025/pilot_2025_co2_solubility_integrated_doe.ipynb`, sección 1; dinámica CO2 en la sección 3 y en `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, líneas 1668–1801; propuesta ya documentada en `laboratory_2026/notebooks/presentation_model_co2_progress.ipynb`, secciones 6–7.
- **Conclusión en una frase:** el EKF exploratorio debe estimar cinco estados y tratar el bloque gaseoso como una observación dinámica, no como una ecuación algebraica directa.

## Slide 8 — Decisiones pendientes y plan exploratorio EKF

- **Pregunta que responde:** ¿qué debe resolverse antes de interpretar un EKF como estimador confiable?
- **Mensajes clave (máximo 3):**
  1. Fijar o regularizar los parámetros débiles y validar primero el modelo abierto en holdouts MS, MN y piloto con referencias offline sincronizadas.
  2. Definir `Q`, `R`, estado inicial y tratamiento del retardo/preprocesamiento; después revisar observabilidad local a lo largo de trayectorias reales.
  3. Ejecutar un EKF exploratorio por etapas: `C_d/E` primero, luego añadir `S/N/X` solo si innovaciones y errores offline permanecen consistentes.
- **Figura recomendada:** repetir `figures/activation_identifiability_profiles.png` en miniatura o cerrar sin figura con una lista de decisiones tipo semáforo.
- **Números importantes:** 3 dominios mínimos de validación (MS, MN, piloto); 2 holdouts estrictos ya disponibles en laboratorio; 8 parámetros de forma frente a 1 medición online; condición piloto lote 3 `3.92×10^11` como advertencia de transferencia/identificación.
- **Ecuaciones mínimas:** predicción `P^- = A P A^T + Q`; actualización `K=P^-H^T(HP^-H^T+R)^-1`; innovación `nu=y-h(x^-)`.
- **Fuentes:** holdouts e identificabilidad en `laboratory_2026/results/co2_matrix_cross_validation_2026/{validation_summary.csv,activation_jacobian_identifiability.csv}`; piloto en `pilot_2026/results/co2_solubility_cross_lot_validation_2026/{validation_summary.csv,activation_jacobian_identifiability.csv}`; pendientes de arquitectura en `laboratory_2026/notebooks/presentation_model_co2_progress.ipynb`, sección 7.
- **Conclusión en una frase:** el próximo hito no es aumentar complejidad, sino demostrar observabilidad y validación independiente con un subconjunto de parámetros suficientemente estable.

## Orden oral sugerido

1. El sensor es indirecto.
2. Mostrar la cadena física/efectiva.
3. Justificar `C_d` con el benchmark.
4. Explicar qué añadió N y cómo se calibró.
5. Mostrar dónde transfiere y dónde falla.
6. Convertir esas fallas en una conclusión de identificabilidad.
7. Presentar el estado aumentado mínimo.
8. Cerrar con criterios concretos de avance hacia el EKF.

