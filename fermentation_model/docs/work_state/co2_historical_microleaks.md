# WORK_STATE — Diagnóstico CO2 histórico: variabilidad vs microfugas (LAB004–LAB012)

**Qué es**: estado operativo compacto de esta línea para handoff entre sesiones. El informe científico
detallado y permanente es `docs/diagnostics/co2_historical_variability_microleaks_2026.md` (v2) —
ese archivo NO debe simplificarse ni moverse; este no lo reemplaza ni duplica.

## Estado

- **Tema**: ¿la variabilidad de amplitud del CO2 gaseoso entre LAB004–LAB012 es térmica/biológica o
  compatible con microfugas/instrumentación? (diagnóstico retrospectivo, cerrado en v2 a nivel
  descriptivo; sin recalibrar nada).
- **Branch**: `analysis/co2-historical-variability`. **Commit base**: `9769543` (experimento SCCM
  corregido; HEAD seguía ese commit al cerrar v2). Trabajo v1+v2 sin commitear (archivos nuevos, `??`).
- **Artefactos**:
  - Informe: `docs/diagnostics/co2_historical_variability_microleaks_2026.md` (v2, permanente).
  - SOURCE: `laboratory_2026/notebooks/diagnostics/co2_historical_variability_microleaks_2026.ipynb`.
  - EXECUTED: `...co2_historical_variability_microleaks_2026.executed.ipynb` (0 errores; 17 figuras,
    16 tablas; código/markdown idénticos al SOURCE).
  - Resultados: `laboratory_2026/results/co2_historical_variability_microleaks_2026/` (7 CSVs:
    master_table, final_classification, discontinuity_events, tail_decomposition,
    prediction_decomposition, counterfactuals_frozen_model, lab016_018_prenutrition_reference).

## Hallazgos actuales (verificados contra el informe v2)

- `int_obs`/`int_pred` del artefacto canónico se integran sobre la **misma grilla horaria** (caso A;
  sin NaN; cálculo homogéneo, no corregido porque no lo necesitaba).
- **`ratio_int = int_obs/int_pred < 1` NO es evidencia de microfuga**: el upstream produce integrales
  casi uniformes (26–31 g/L); la discrepancia nace en la capa efectiva del modelo (gate químico no
  causal recorta 1–15% en abril y 47–69% en mayo; cola predicha demasiado larga; respuesta a pulso
  atenuada).
- **LAB006**: su déficit obs/pred se explica esencialmente por la cola del modelo (ratio_peak 1.00,
  tail_excess +8.4 g/L ≈ déficit). **Sospecha de fuga retirada** — cinética fría real (16 °C, ancho 80 h).
- **LAB010**: anomalía principal. Recuperación gaseosa anormalmente baja (R_rel ≈ 0.47) con química
  final igual al resto (Δ(G+F), ΔE comparables); sin ancho compensatorio. El modelo NO corrobora (su
  predicción baja es artefacto del gate anclado a la química lenta del propio batch; ni T ni X0 ni ICs
  ajenas la cambian). **Causa no identificable**: posible pérdida de gas o lectura instrumental baja;
  fermentador vs sensor NO separable (sensor_id = canal = fermentador, sin permutas documentadas).
- **LAB011/LAB012**: actividad gaseosa MAYOR que la predicha (ratio_peak 2.6/1.9); ningún contrafactual
  de X0/T la reproduce → causa no identificada / limitación estructural. Dirección opuesta a una fuga.
- **LAB016–018** (referencia independiente, mejor estanqueidad, ~20 °C, mismo mosto, t0 físico;
  solo contexto, NO training): pre-nutrición (onset→+56.93 h) **CV(qmax) ≈ 2.3%, CV(integral) ≈
  8.5%, formas correlacionadas ≈ 0.97–0.99**; sin química G/F/E durante fermentación (sin balance de
  carbono equivalente; no inventarlo).
- **Reproducibilidad histórica**: los históricos cálidos replicados (grupo A: LAB004/005/008) tienen
  CV integral ~3% — comparable a la referencia. Solo LAB010 (y débilmente LAB006) exceden la banda
  0.88–1.04 de referencia.
- **Conclusión general**: NO hay evidencia suficiente para afirmar retrospectivamente microfugas como
  causa principal de la variabilidad; temperatura tiene asociación fuerte con qmax/velocidad
  (r ≈ +0.90/+0.93 sin LAB010) pero r(integral, T) ≈ +0.94 NO se interpreta como fisiología ni
  causalidad (el total debería ser ~independiente de T a química igual).
- **`matrix_gain` NO representa eficiencia física de recuperación de CO2** (parámetro empírico de la
  función de observación). **`R_sugar` = integral/Δ(G+F) sirve solo como comparación relativa
  batch-to-batch**; el balance absoluto de carbono no puede cerrarse (mediana 0.206 vs ideal 0.4886:
  diferencia sin causa única identificable).

## Decisiones que condicionan trabajo futuro

1. Cualquier relectura de CO2 de LAB004–012 debe partir de los artefactos SCCM corregidos (no LEGACY).
2. LAB010 es el único batch cuya señal no debe usarse ciegamente como referencia de amplitud; si se
   recalibra, decidir primero su tratamiento (p. ej. sensibilidad con/sin LAB010).
3. La evidencia de que el gate (no causal) genera las discrepancias obs/pred refuerza la prioridad del
   **mecanismo causal de onset** antes de recalibrar amplitudes de la capa CO2 (ver roadmap del doc
   maestro §17).
4. LAB016–018 siguen siendo holdout/referencia; este diagnóstico NO los convirtió en training y no debe
   reinterpretarse como holdout oficial de la capa.

## Pendientes específicos (si se continúa esta línea)

- Blancos/calibración de caudalímetro por canal y prueba de hermeticidad (ventana de mayo y campañas
  futuras) — solo obtenibles experimentalmente.
- Repetir 15 °C isotermo en F2/F3 para replicar el contraste de LAB010.
- Metadata que separe sensor de fermentador (permutas, calibraciones, volumen real por batch).
- Opcional (modelado, requiere decisión del usuario): cuantificar el efecto del gate re-anclado a onset
  observado como diagnóstico adicional (ya existe precedente en el notebook holdout §8.4).

## Qué NO hacer al continuar esta línea

- NO recalibrar θ, capa CO2, bounds ni ΔN a partir de este diagnóstico (es descriptivo; los ratios del
  modelo congelado son línea auxiliar, no objetivo de fit).
- NO etiquetar LAB010 (ni ninguno) como "con fuga" en documentos: la categoría correcta es
  "recuperación anormalmente baja, causa no identificable".
- NO usar LAB009 ni LAB001–003 en estadísticas de la capa CO2 (excluidos por QC).
- NO reinterpretar la comparación por onset de LAB016–018 como holdout oficial.
- NO anexar historia a este archivo: reescribir/compactar al cerrar cada fase (ver PROJECT_CONTEXT.md).

## Cómo usar este archivo (agente nuevo)

1. Leer primero `docs/work_state/PROJECT_CONTEXT.md`.
2. Leer este archivo (estado actual del tema).
3. Abrir el informe v2 (`docs/diagnostics/...2026.md`) solo si necesitas las tablas completas por LAB,
   metodología o figuras; los números finos están en el EXECUTED y los CSVs de `results/`.
4. Al terminar tu fase: reescribe este archivo compactado (estado, no historia) y no toques el informe
   científico salvo error factual evidente.
