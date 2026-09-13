# Diagnóstico retrospectivo: variabilidad de CO2 gaseoso en LAB004–LAB012 (¿temperatura/biología o microfugas?) — v2

**Documento técnico de conclusiones y trazabilidad. Fecha: 2026-09-10 (v2, extendido y revisado críticamente).**

- Rama: `analysis/co2-historical-variability` | HEAD: `9769543` (commit base del experimento SCCM corregido; verificado ancestro/HEAD; estado limpio al partir).
- **SOURCE (canónico, sin outputs):** `fermentation_model/laboratory_2026/notebooks/diagnostics/co2_historical_variability_microleaks_2026.ipynb`
- **EXECUTED (kernel limpio; 0 errores; 17 figuras y 16 tablas inline; código/markdown idénticos al SOURCE):** `...co2_historical_variability_microleaks_2026.executed.ipynb`
- Artefactos: `laboratory_2026/results/co2_historical_variability_microleaks_2026/` (`master_table_by_batch.csv`, `final_classification_by_lab.csv` v2, `discontinuity_events.csv`, `tail_decomposition_by_lab.csv`, `prediction_decomposition_by_lab.csv`, `counterfactuals_frozen_model.csv`, `lab016_018_prenutrition_reference.csv`).
- Sin recalibración de ningún tipo: θ, capa CO2, bounds, SCCM, raw data, LAB016–018, notebook holdout, resultados históricos y ΔN intactos. El modelo congelado se usó solo en modo forward/diagnóstico (reconstrucción verificada bit-exacta contra `prediction_rows.csv`, dif. máx. 1.1e-16).

**Cambios v2 respecto de v1 (obligados por nueva evidencia, no por inercia):** LAB006 pierde la sospecha de pérdida de gas (su déficit obs-vs-pred es cola del modelo); LAB010 pierde la presunta "corroboración" del modelo (su predicción baja es artefacto del gate) y queda como recuperación anormalmente baja sin atribución entre pérdida e instrumentación; LAB011/012 dejan de atribuirse a "biología/ICs" (los contrafactuales no reproducen su exceso) y quedan como actividad mayor que la predicha, causa no identificada.

## Pregunta científica

(1) ¿De dónde proviene realmente la diferencia entre CO2 observado y predicho acumulado en LAB004–LAB012? (2) ¿Sirven LAB016–018 (mejor estanqueidad, CO2 de alta calidad) como referencia independiente para estimar cuánta variabilidad histórica es normal y cuánta compatible con pérdidas/instrumentación?

## Datasets

| Dataset | Uso |
| --- | --- |
| `results/co2_matrix_cross_validation_2026_sccm_corrected/` | señal horaria QC canónica (SCCM corregido 0.0404392 g·L⁻¹·h⁻¹·SCCM⁻¹), censuras, `sensor_id`/`acquisition_channel`, T medida, métricas y predicciones del modelo congelado |
| `run_co2_matrix_cross_validation_2026.py` (solo lectura) | `build_driver_cache` / `raw_qgas_grid_prediction` para descomponer la cadena y construir contrafactuales |
| `mosto_natural_xthiol.xlsx` (hojas LAB004–LAB012) | química inicial/final |
| `batch_summary.csv` (θ_natural) | X0/N0 |
| `raw_data/*.csv` + `Desktop_CyT_Tablero_Proceso` | partes del logger, huecos, LAB009 contexto |
| `data/mem2026/LAB016-018/*_inoculation_aligned.csv` | CO2 (filtrado, alineado a t0 físico) y T de LAB016–018 |

## Limitaciones

1. n=8 aceptados; solo el programa A replicado; correlación ≠ causalidad.
2. `sensor_id` = canal = fermentador, sin permutas documentadas: **no separable**.
3. R_sugar/R_eth aparentes; **el balance absoluto de carbono no puede cerrarse** con estos datos (convención/volumen, error analítico, partición de carbono).
4. Modelo congelado con defectos estructurales conocidos (gate no causal, cola lenta, respuesta a pulso atenuada): solo línea auxiliar; `ratio_int < 1` **no** es evidencia de microfuga.
5. LAB016–018 sin química G/F/E/YAN durante la fermentación: sin balance químico equivalente (no se inventa); su comparación con el modelo se limita a lo documentado (onset predicho 16–18 h antes del observado por el gate), sin reinterpretar el holdout.

## Metodología (v2)

Se mantienen las métricas v1 (qmax, t_peak, integral, onset canónico, duración activa, ancho efectivo, T en ventana activa, R_sugar/R_eth relativos, discontinuidades, réplicas, modelo congelado) y se añaden: auditoría de ventanas de integración; descomposición peak/cola (terminación = primer instante con q < 5% del máximo sostenida; cola = integral post-peak); descomposición de la cadena `qprod_base → qprod_O2(sin gate) → qprod_efectiva(gate+pulso) → qgas → qpred` y su cotejo con `int_qobs`; contrafactuales forward (swap de T, X0, ICs); LAB016–018 pre-nutrición (onset → +56.93 h desde t0; mediana 61 pts, cero pre-onset cuantil 10%, bin horario, onset sostenido 3 puntos) como referencia de reproducibilidad; comparación de dispersión (CV, ratio a mediana, formas).

## Auditoría de las ventanas de integración

**Veredicto (caso A):** observación y predicción se integran sobre exactamente la misma ventana y grilla horaria (mismos timestamps de `prediction_rows`, sin interpolación ni extrapolación; 0 NaN en ambas series). El cálculo existente es matemáticamente homogéneo y no se modifica. La grilla interna del driver (0.25 h) solo alimenta la interpolación a los timestamps de observación.

## Descomposición de la discrepancia integral (LAB004–LAB012)

| LAB | int_qprod_base | int_O2 (sin gate) | int_efectiva (gate+pulso) | int_qgas | int_qpred | int_qobs | gate_cut |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LAB004 | 26.59 | 16.51 | 14.09 | 13.97 | 29.89 | 31.24 | 14.7% |
| LAB005 | 30.90 | 19.32 | 16.71 | 16.55 | 35.40 | 32.39 | 13.5% |
| LAB006 | 26.19 | 14.74 | 14.55 | 14.31 | 30.62 | 22.49 | 1.3% |
| LAB007 | 25.94 | 15.84 | 15.08 | 14.87 | 31.80 | 35.23 | 4.8% |
| LAB008 | 26.02 | 15.79 | 15.13 | 14.92 | 31.92 | 29.96 | 4.2% |
| LAB010 | 31.13 | 25.99 | 8.02 | 7.92 | 16.94 | 14.69 | 69.2% |
| LAB011 | 30.57 | 25.70 | 7.87 | 7.77 | 16.63 | 35.68 | 69.4% |
| LAB012 | 30.37 | 24.95 | 13.22 | 13.07 | 27.96 | 41.84 | 47.0% |

- **El upstream es uniforme** (26–31 g/L, química igual): la discrepancia NO nace en `qprod_base`.
- El **gate químico** recorta 1–15% en abril y 47–69% en mayo (arranques fríos/química lenta → bracket tardío → activación tardía): es el que hace que el modelo "espere" poca señal en LAB010/011/012.
- El pool/release apenas cambia el total; `matrix_gain` escala linealmente.

## Cola del modelo (peak vs terminación)

| LAB | ratio_peak | t_end_obs | t_end_pred | post_peak_obs | post_peak_pred | tail_excess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LAB004 | 1.39 | 125.0 | 162.8 | 27.2 | 25.9 | −1.4 |
| LAB005 | 1.10 | 149.0 | 162.8 | 23.9 | 30.5 | +6.6 |
| LAB006 | 1.00 | 210.8 | 210.8 | 15.7 | 24.1 | +8.4 |
| LAB007 | 1.55 | 139.0 | 159.7 | 25.6 | 26.2 | +0.6 |
| LAB008 | 1.23 | 146.0 | 159.7 | 21.3 | 25.6 | +4.4 |
| LAB010 | 0.91 | 179.0 | 186.8 | 10.0 | 9.7 | −0.2 |
| LAB011 | 2.56 | 142.0 | 161.0 | 24.0 | 10.3 | −13.6 |
| LAB012 | 1.94 | 153.0 | 162.8 | 24.4 | 17.4 | −6.9 |

- **LAB006**: `ratio_peak` = 1.00 y el déficit integral (8.1 g/L) coincide con el exceso de cola (+8.4): todo el déficit obs-vs-pred es **cola del modelo**.
- LAB005/008: exceso de cola (+6.6/+4.4) que incluso supera su déficit total (sus picos observados exceden al predicho y compensan pre-peak).
- LAB011/012: signo invertido (la observación tiene más área post-peak: reactivación que el modelo atenúa).

## Contrafactuales (forward puro, modelo congelado)

- **LAB010**: base qpred peak 0.28 / integral 16.9. Con T de LAB011: 0.28/16.4; con X0 de LAB004: 0.26/18.5; con ICs completas de LAB004: 0.25/17.4. **Ni T ni X0 ni ICs cambian materialmente la predicción**: la predicción baja es el gate anclado a la química lenta del propio batch — circular, no corrobora la señal baja del sensor.
- **LAB011**: base 0.34/16.6 (obs 0.88/35.7). X0(LAB008): 0.30/18.9; T(LAB008): 0.32/15.4; T+X0: 0.30/18.2. **Ningún swap se acerca a lo observado** → actividad mayor que la predicha, causa no identificada (limitación estructural o factor no modelado); no se atribuye a biología/ICs.
- **LAB012**: base 0.43/28.0 (obs 0.84/41.8); X0(LAB008): 0.33/26.4 → mismo veredicto.

## LAB016–LAB018 como referencia independiente (pre-nutrición)

| LAB | onset [h] | T_mean | qmax_preN | t_peak_rel | integral_preN | width | ratio_int/mediana |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LAB016 | 25.5 | 20.04 | 0.773 | 22.0 | 17.51 | 22.7 | 0.883 |
| LAB017 | 23.5 | 20.03 | 0.808 | 18.0 | 20.67 | 25.6 | 1.043 |
| LAB018 | 24.5 | 19.97 | 0.788 | 20.0 | 19.83 | 25.2 | 1.000 |

**CV(qmax) = 2.3% | CV(integral) = 8.5% | CV(t_peak) = 10% | máx/mín integral = 1.18 | formas normalizadas correlacionadas 0.97–0.99 | sub-LOD pre-N = 0%.** Registro completo (contexto): 47.5/52.9/48.6 g/L (LAB017 con doble pulso tardío; no se interpreta post-nutrición como fuga). Sin comparación modelo-obs cuantitativa aquí: el gate predice onsets 16–18 h antes (documentado) y condicionar por onset no debe reinterpretarse como holdout.

## Comparación de reproducibilidad: históricos vs referencia

| Conjunto | n | CV qmax | CV integral |
| --- | ---: | ---: | ---: |
| LAB016–018 pre-N (referencia) | 3 | 2.3% | 8.5% |
| Grupo A histórico (004/005/008) | 3 | 8.9% | 3.3% |
| Históricos cálidos (004/005/007/008) | 4 | 11% | 7% |
| Todos los históricos aceptados | 8 | 42% | 28% |

**Respuesta:** la variabilidad de los históricos cálidos es comparable a la referencia (grupo A incluso más estrecho en integral): esa parte es normal. La dispersión de la campaña completa excede la referencia y está dominada por LAB010 (R_rel 0.47) y LAB006 (0.69), fuera de la banda de referencia 0.88–1.04; el resto (0.95–1.31) es compatible.

## R_sugar y matrix_gain (interpretación corregida)

- (A) Magnitud experimental: R_sugar = integral/Δ(G+F) (mediana 0.206; rango 0.096–0.270).
- (B) Referencia estequiométrica ideal: 0.4886 g CO2/g azúcar (solo física).
- (C) `matrix_gain` (2.139) es un **parámetro empírico de la función de observación del modelo**: NO representa eficiencia de recuperación física, ni porcentaje perdido, ni corrige microfugas, ni "absorbe" físicamente la diferencia contra la estequiometría.
- La diferencia absoluta (A) vs (B) no tiene causa única identificable y **el balance absoluto de carbono no puede cerrarse** con estos datos. R_sugar se usa exclusivamente **relativo** entre batches.

## Temperatura (grado de conclusión corregido)

- Evidencia **fuerte de asociación** T↔velocidad/qmax (r = +0.90; +0.93 sin LAB010) y coherencia de tiempos/duraciones (LAB006 ancho y lento).
- Evidencia **mucho menos clara** de que T explique el CO2 **total recuperado**: r(integral, T) = +0.94 no tiene explicación fisiológica directa (a química igual el total debería ser ~constante) y refleja que los batches fríos son los de baja recuperación; no se atribuye a fisiología ni se convierte en causalidad. n=8, un programa replicado.

## Reinterpretación por batch

- **LAB006**: cinética fría real (peak bajo/tardío, ancho 80 h) + cola del modelo sobrepredicha (+8.4 g/L, ratio_peak 1.00). La evidencia de pérdida de gas resulta **insuficiente** y se retira.
- **LAB010**: el modelo NO corrobora la señal baja (predicción baja = artefacto del gate; ni T ni X0 la explican). La anomalía robusta es química-vs-sensor: R_rel 0.47 con dGF/dE iguales a los demás, sin ancho compensatorio, 55% de puntos censurados y LOD frío duplicado (posible sesgo de piso de medición). Queda como **recuperación gaseosa anormalmente baja: posible pérdida de gas o lectura instrumental baja; fermentador vs sensor no separable**.
- **LAB011/LAB012**: actividad gaseosa mayor que la predicha por el modelo congelado; **causa no identificada** (limitación estructural: gate + respuesta a pulso atenuada; o factor no modelado). Dirección opuesta a una fuga; no se atribuye a "biología/ICs" sin evidencia.

## Clasificación final (v2)

| LAB | Conclusión | Confianza |
| --- | --- | --- |
| LAB004 | compatible con cinética normal (réplica A consistente) | alta |
| LAB005 | compatible con cinética normal | alta |
| LAB006 | mixto: cinética fría real + cola del modelo sobrepredicha; evidencia de pérdida de gas INSUFICIENTE | media |
| LAB007 | compatible con cinética normal | alta |
| LAB008 | compatible con cinética normal | alta |
| LAB010 | recuperación gaseosa anormalmente baja: posible pérdida de gas o lectura instrumental (F1, mayo); sin corroboración del modelo; fermentador vs sensor no separable | media-alta |
| LAB011 | actividad mayor que la predicha; causa no identificada (limitación estructural); no compatible con pérdida | media |
| LAB012 | ídem LAB011; recuperación alta (R_rel 1.31) | media |

## Conclusión revisada (temperatura vs microfugas)

- **Puede afirmarse:** la discrepancia obs-pred de integrales nace en la capa efectiva del modelo (gate no causal + terminación lenta), no en el upstream ni es prueba de fuga; LAB006 queda explicado; la referencia LAB016–018 acota la reproducibilidad normal (CV qmax 2.3%, CV integral 8.5%); los históricos cálidos operan a ese nivel; LAB010 presenta una recuperación gaseosa anormalmente baja frente a química idéntica y fuera de la banda de referencia.
- **NO puede afirmarse:** que existieron microfugas (ni como causa principal, ni en LAB006); la atribución reactor-vs-sensor en LAB010; causalidad térmica del CO2 total; que el exceso de LAB011/012 sea "solo biología".
- La evidencia de pérdida gaseosa adicional más allá de temperatura/cinética se reduce a **LAB010 como compatibilidad** (no demostración) y desaparece para LAB006.

## Datos que faltan

Blanco/calibración de caudalímetro por canal (ventana de mayo); prueba de hermeticidad; volumen real por batch; repetición del programa D en otro canal; CO2 disuelto para balance de carbono; bitácora del 13-05; metadata que separe sensor de fermentador; para LAB011/012, un mecanismo causal de activación/reactivación que el modelo no tiene.

## Acciones recomendadas (sin implementar)

1. Blancos de caudalímetro por canal + hermeticidad + volumen real antes de la próxima campaña.
2. Repetir 15 °C isotermo en F2/F3 (contraste LAB010).
3. Registrar permutas/calibraciones sensor-canal como metadata de campaña.
4. Antes de recalibrar amplitudes: resolver el mecanismo causal de onset/activación y la respuesta a pulso (el gate explica la mayoría de las discrepancias obs-pred actuales).
5. Mantener SCCM corregido y la interpretación relativa de R_sugar.
