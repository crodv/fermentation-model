# Modelo de mosto natural: calibración histórica, auditoría 2026 y preparación del estimador de estado

**Documento técnico de referencia — versión 3 (reestructurada), 2026-09-08.**

Alcance: referencia técnica del estado actual del proyecto de modelado de mosto natural: (a) arquitectura real del modelo tal como la consumen los notebooks/runners actuales, (b) qué está calibrado y qué está congelado, (c) trazabilidad del input CO2 y del calendario nutricional, (d) inventario y rol de LAB013–LAB018, (e) resultados/validaciones vigentes, (f) problemas estructurales confirmados, (g) qué (no) recalibrar y en qué orden, (h) prerequisitos del estimador de estados. Base de la auditoría: el repositorio real (código, datos, resultados versionados), no memoria ni nombres de archivo.

Convención de etiquetas:

- **[HECHO VERIFICADO]** — respaldado directamente por código, datos o resultados del repositorio (se cita ruta y función/línea).
- **[RESULTADO DIAGNÓSTICO]** — simulación/prueba forward con parámetros congelados (sin fitting). No son parámetros calibrados.
- **[INTERPRETACIÓN]** — lectura razonada de hechos/diagnósticos.
- **[PENDIENTE]** — dato, decisión o hipótesis sin respaldo suficiente.

Archivos nucleares:

| Rol | Ruta |
|---|---|
| ODEs upstream, ajuste de parámetros | `fermentation_model/shared/run_new_must_glycerol_estimability_doe.py` (`base`) |
| Loader de datos históricos natural | `fermentation_model/shared/new_must_data_loader.py` |
| Calibración upstream natural 2026 | `fermentation_model/laboratory_2026/run_estimability_historical_by_medium.py` |
| Capa CO2 2026 (matrix cross-validation) | `fermentation_model/laboratory_2026/run_co2_matrix_cross_validation_2026.py` (`co2_cross`) |
| Módulo CO2 (qprod base, solubilidad) | `fermentation_model/pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py` (`co2_model`) |
| Tasas core / constante CO2–etanol | `fermentation_model/shared/run_secondary_joint_campaign_doe.py` (`joint`, `CO2_G_PER_G_ETHANOL` :166) |
| θ natural | `fermentation_model/laboratory_2026/results/estimability_historical_natural/theta.csv` |
| Parámetros capa CO2 | `fermentation_model/laboratory_2026/results/co2_matrix_cross_validation_2026/fit_parameters.csv` |
| Notebook holdout LAB016–018 | `fermentation_model/laboratory_2026/notebooks/lab016_018_natural_must_holdout.ipynb` |
| Notebook LAB013–015 | `fermentation_model/laboratory_2026/notebooks/lab013_015_natural_must_co2_model_analysis.ipynb` |
| Calendario nutricional versionado | `fermentation_model/data/Laboratorio 2026/raw_data/Fernanda Folch.ics` |
| Workbook maestro natural | `fermentation_model/data/Laboratorio 2026/Vendimia_2026/mosto_natural_xthiol.xlsx` |

---

## 1. Alcance y objetivo

El objetivo final del proyecto es un **estimador de estados** (previsiblemente EKF/UKF/MHE) del fermentador de mosto natural con **CO2 gaseoso como sensor online principal**, estimando principalmente `X` y `N` (y potencialmente el resto de los estados), con la química offline como validación y no como información futura operativa. Este documento no diseña el estimador: documenta qué partes de la arquitectura actual son compatibles con ese objetivo, cuáles no, y qué falta.

Regla de lectura: la calibración de la **capa CO2** (observación/transferencia) **no** recalibra el **modelo cinético central**. Son dos etapas distintas con artefactos distintos; el holdout de LAB016–018 congela ambos y no llama a ningún optimizador [HECHO VERIFICADO: notebook holdout, celdas de validación "optimizer/fitting calls executed: 0"].

---

## 2. Arquitectura actual del modelo

### 2.1 Esquema real consumido por el notebook LAB016–018

```
datos (T medida, ICs, eventos de bomba)
        ↓
ODE upstream (base.simulate, LSODA, saltos exactos de pulsos)
estados: X, Xd, N, G, F, E, Gly
        ↓
CO2 biológico: qprod_base = 0.4777 · (βG+βF) · X      (co2_model.co2_production_g_l_h)
        ↓
gate de activación química A(t)                         (_chemical_activity_bracket + _bounded_smoothstep_activation)
        ↓
respuesta post-pulso: r(t), activity_multiplier, Δqprod_pulso   (effective_qprod_grid)
   + O2 (pool inicial Monod, fracción anaeróbica) — SOLO dentro de la capa CO2
        ↓
pool CO2 disuelto (solubilidad Csat(T,E,G,F) = s·1.69·e^(−0.032(T−20))·e^(0.0016E)·e^(−0.0012(G+F)))
        ↓
release continuo: qgas = min(k·C·(0.05+0.95·C/(C+C*)), disponible)
        ↓
señal gaseosa: qobs = matrix_gain · qgas
```

**[HECHO VERIFICADO]** Estados del modelo central: `STATE_NAMES = ("X","Xd","N","G","F","E","Gly")` (`base` :75); canales de entrada discretos `INPUT_CHANNELS = ("N","G","F","E","X")` (:76). La **temperatura no es estado**: input exógeno interpolado (`base.temperature_at` :358). Ecuaciones: `base.rhs` (:445), `base.kinetic_terms` (:387).

**Distinguir estados vs. no-estados [HECHO VERIFICADO]:**

| Cantidad | Categoría |
|---|---|
| X, Xd, N, G, F, E, Gly | estados ODE del modelo central |
| O2 disuelto, φ_anaeróbica, pool de CO2 disuelto, A(t), r(t) | variables internas de la **capa CO2** (no estados del central) |
| temperatura | driver exógeno medido |
| SCCM→g/L/h, matrix_gain | observación/escala |
| "estado de actividad metabólica a(t)" | **hipótesis propuesta, no implementada** (§16) |
| CO2 disuelto como estado del central | **no implementado** (existe solo como pool interno de la capa; el Carbodoseur histórico es dato offline) |

### 2.2 Pertenencia de parámetros

| Grupo | Parámetros | Fuente |
|---|---|---|
| θ_natural (upstream) | mu0, qN, betaG0, betaF0, qEG, qEF, iG, iE, Kd0, gammaG0, gammaF0 (re-estimados) + sN, sG, sF, qXG, qXF, m0, Arrhenius, bloque secundario/aroma fijos | `theta.csv` |
| Capa CO2 (natural) | kCO2_release_h, CO2sat_scale, O2_qmax_mg_gdw_h, O2_initial_scale, pulse_t_rise_h, pulse_activity_gain, chem_activation_start_fraction, chem_activation_duration_fraction, matrix_gain | `fit_parameters.csv` (`calibration_matrix=natural`) |
| Inputs/eventos | tiempos de pulso N, ΔN, series de T, ICs por batch | datos/metadatos |

### 2.3 Estructura de qprod y terminación [HECHO VERIFICADO]

```
βG = betaG0·aβ(T)·G/(G+kG)·1/(1+iE·E)
βF = betaF0·aβ(T)·F/(F+kF)·1/(1+iG·G)·1/(1+iE·E)
qprod_base = 0.4777·(βG+βF)·X          (CO2_G_PER_G_ETHANOL = 44.01/(2·46.07), joint :166)
```

- **N entra solo en μ** (`n/(n+kn)`): no limita βG/βF [HECHO VERIFICADO].
- **Muerte celular**: `dXd = kd·X` con `kd>0` solo si `T ≥ td(E)`, `td(E) = −0e−4·E³+0.0049·E²−0.1279·E+315.89 K` (`base` :421). A 16–22 °C y E≤60 g/L, td ≈ 305–310 K > T ⇒ **kd = 0**: muerte inerte, Xd≈0, X plana tras el crecimiento [HECHO VERIFICADO].
- **Pulsos**: `base.simulate` aplica saltos exactos (`_pulse_events` :475): `N(t⁺)=N(t⁻)+ΔN`.

### 2.4 Respuesta nutricional en la capa CO2 [HECHO VERIFICADO, `effective_qprod_grid` :1668]

```
r(t) = clip((t−t_pulse)/pulse_t_rise_h, 0, 1)            # rampa causal, sin caída propia
biomasa = X_sinpulso + r·ΔX_pulso
activity_multiplier = 1 + (pulse_activity_gain − 1)·r(t)
qprod_bio = multiplier·qprod_sinpulso + r·Δqprod_pulso
```

Valores naturales ajustados: `pulse_activity_gain = 0.25` (cota inferior activa) y `pulse_t_rise_h = 64.66 h` (cerca de la cota superior 72). **[INTERPRETACIÓN]** En natural, el "nitrogen boost" funcionó de facto como **atenuación lenta post-pulso** (×0.25 en ~65 h): era el apagado histórico de la curva, no una reactivación.

### 2.5 O2 en la capa [HECHO VERIFICADO]

Pool inicial `O2_initial_scale·O2sat(T,E,G,F)`, consumo Monod `O2_qmax_mg_gdw_h`, fracción fermentativa `f_ferm = 0.08+0.92·φ_ana`. El O2 **no** es estado del central y no se compara contra mediciones en LAB016–018 (no existen).

---

## 3. Datasets y experimentos disponibles

| Dataset | Rol actual | Estado |
|---|---|---|
| LAB004–LAB012 (naturales históricos, workbook homologado) | calibración θ_natural + capa CO2 (con holdout LAB012) | versionados, inmutables |
| LAB001–LAB003 | CO2 excluido por QC (`EXCLUDED_BATCHES` :81) | contexto solo |
| LAB013–LAB015 (`data/mem2026/LAB013-015/`) | química + biomasa nueva; CO2 no confiable | §7 |
| LAB016–LAB018 (`data/mem2026/LAB016-018/`) | holdout externo CO2 + diagnósticos | §8 |
| LAB290226 (`data/mem2026/LAB290226/`) | contexto térmico secundario (medio no documentado) | §8.7 |
| Calendario `Fernanda Folch.ics` | input versionado del análisis histórico | §3.1 |

Los datos históricos **no** son "legacy desechable": `legacy/` congela código superseded, nunca datos experimentales.

### 3.1 Calendario nutricional [HECHO VERIFICADO]

`NUTRIENT_CALENDAR_PATH = RAW_NATURAL_DIR / "Fernanda Folch.ics"` (`co2_cross` :65–66): ruta **relativa al repositorio**, versionada en `data/Laboratorio 2026/raw_data/`. Proporciona los eventos "Pulso nutricional 2" de **LAB004–LAB012 (9 eventos, sin faltantes ni duplicados** — validado por `_calendar_nutrient_pulse_events` :260). Ya no existe dependencia operativa de carpetas personales (Downloads/OneDrive); aquellas rutas solo subsisten como antecedente histórico en `docs/history/`.

### 3.2 Política Oculyze [HECHO VERIFICADO]

Las imágenes crudas JPEG de Oculyze (subdirectorios hash) fueron retiradas del árbol el 2026-09-08; se conservan los `report.csv` (uno por LAB013–LAB018). El pipeline consume exclusivamente `report.csv`; ninguna documentación exige las imágenes crudas.

---

## 4. Calibración del modelo cinético upstream (θ_natural, LAB004–LAB012)

**[HECHO VERIFICADO]** Batches: LAB004–LAB012 (9), incluida LAB009 (excluida después solo de la capa CO2). Runner: `run_estimability_historical_by_medium.py`; artefacto `results/estimability_historical_natural/`.

- **Estados observados:** los 7 estados core entraron al ajuste (X/Xd de Oculyze, N de YAN, G/F de Y15, E/Gly de química; `measurement_support()` marca `used_in_core_fit=True` para los 7).
- **Objetivo:** `base.residual_vector` (:595): WSSE de `(pred−obs)/σ` por estado/batch; fallo de integración penalizado 1e6×1000.
- **Sigmas** (`MEASUREMENT_ERROR_FLOOR/REL` :174–191): X 0.06/8 %; Xd 0.06/12 %; N 0.012/8 %; G 2.5/2.5 %; F 2.5/2.5 %; E 2.0/2.5 %; Gly 0.35/5 %.
- **Optimizador:** `base.fit_parameters` (:629) — `least_squares` TRF log-espacio, multistart determinista, pulido profile-likelihood (Kd0, qN).
- **Re-estimados (11):** mu0, qN, betaG0, betaF0, qEG, qEF, iG, iE, Kd0, gammaG0, gammaF0 (`theta.csv`, `reestimated_in_this_notebook=True`). El resto fijo.
- **ICs por batch** (primera observación finita; `batch_summary.csv`): X0 0.099–1.066; Xd0 0.001–0.121; N0 0.220–0.239 kg/m³; G0 75.0–81.6; F0 70.8–88.0; E0 9.21–11.76; Gly0 0.75–1.27 g/L.
- **t=0 histórico:** fila `t = 0` del workbook homologado (`load_natural_batch_metadata` :142): t0 de muestreo/química, **no** flanco de inoculación medido (a diferencia de LAB016–018).
- **Pulsos en el ajuste upstream:** ΔN = `pulso_nut` del workbook (`new_must_data_loader` :246 → `N_pulse_kg_m3`, ≈0.08 kg/m³). **Discrepancia documentada:** la capa CO2 después *sobrescribe* con ΔN = 0.14 kg/m³ de protocolo (`override_natural_nutrient_pulses` :452). θ_natural y la capa CO2 **no usan la misma dosis de N** [HECHO VERIFICADO].

**Semántica Oculyze [HECHO VERIFICADO]:** `X = Concentration·Viability/100·0.03 kg/m³` (30 pg/célula, `MILLION_CELLS_ML_TO_KG_M3=0.03`, loader :55–57). En hojas homologadas históricas `Viability` es concentración viable (Mcél/mL); en exports crudos es % — no mezclar. [PENDIENTE] procedencia física de 30 pg/célula.

**Al ejecutar el notebook LAB016–018, θ completo queda congelado** (cargado con `_load_theta` :186 y verificado por hash SHA256 antes/después) [HECHO VERIFICADO].

---

## 5. Calibración de la capa CO2

**Runner:** `run_co2_matrix_cross_validation_2026.py`. Notebook: `co2_solubility_o2_cross_matrix_2026.ipynb` (ejecutado con seed 20260812, n_starts=5, max_nfev=300; el `.executed.ipynb` conserva la evidencia). Resultados: `results/co2_matrix_cross_validation_2026/` (adoptados en commit `0b86664`).

**Batches (matriz natural) [HECHO VERIFICADO]:** calibración LAB004, 005, 006, 007, 008, 010, 011 (7); **holdout de matriz: LAB012** (`HOLDOUTS` :72); excluidos de CO2: LAB001–003 y LAB009 (`EXCLUDED_BATCHES` :81). Matriz sintética: lot1_F1/F3 + lot2_F1/F2 (lot1_F2 excluido), holdout lot2_F3. Modelo nominal: `solubility_o2_nitrogen_boost_continuous_release`.

**Matiz importante [HECHO VERIFICADO]:** LAB012 fue holdout de la capa CO2 pero **no holdout end-to-end independiente**: su química participó antes en θ_natural.

**Parámetros ajustados por matriz (valores actuales versionados, `fit_parameters.csv`) [HECHO VERIFICADO]:**

| Parámetro | natural | cota activa | sintético (adoptado) | cota activa |
|---|---|---|---|---|
| kCO2_release_h | 0.4246 h⁻¹ | no | **3.8837 h⁻¹** | no |
| CO2sat_scale | 0.3514 | **sí (inferior 0.35)** | 0.4254 | no |
| O2_qmax_mg_gdw_h | 0.1500 | **sí (inferior 0.15)** | 0.15016 | casi |
| O2_initial_scale | 0.1954 | no | 0.3804 | no |
| pulse_t_rise_h | 64.66 | casi (sup. 72) | 36.50 | no |
| pulse_activity_gain | 0.2500 | **sí (inferior 0.25)** | 1.2333 | no |
| chem_activation_start_fraction | 0.7351 | no | 0.010004 | **sí (inferior)** |
| chem_activation_duration_fraction | 1.0639 | no | 0.35000 | **sí (inferior)** |
| matrix_gain | 3.1158 | perfilado | 2.1266 | perfilado |

`matrix_gain` se perfila analíticamente por escala LS (`_profile_matrix_gain` :1909): es la escala empírica de la cadena SCCM→g/L/h y absorbe sesgos de amplitud.

**Observables/residuos de la capa [HECHO VERIFICADO]:** perfil completo con σ = max(0.04, 0.10·peak_batch) y peso 1/√n; pseudo-observable de onset sostenido (σ=12 h); pseudo-observable del **tiempo** del peak post-pulso (σ=12 h); censura LOD unilateral `max(pred−LOD,0)/σ` con LOD 0.05 (0.10 frío <15.5 °C) (`_fit_residual` :1951). **No existía residual de amplitud del bump** — la reactivación histórica se reproducía imperfectamente (§10).

**Preprocesamiento CO2 [HECHO VERIFICADO]:** corrección de cero por sensor (12 h, cuantil 10 %), máscara de artefactos de muestreo (3 h, ratio 0.65), Hampel+mediana+SavGol, protección de respuesta a pulso (4 h), LOD (`filter_co2_sensor_artifacts`, constantes :88–128). Onset: umbral dinámico `max(LOD, baseline+0.10·(peak−baseline))` (`_onset_threshold` :1837) con 3 puntos consecutivos (`_sustained_onset_h` :1849).

**Gate químico [HECHO VERIFICADO]:** `_chemical_activity_bracket` (:1302): `U` = primera muestra con Δ(G+F) ≤ −5 g/L (`CHEMISTRY_SUGAR_DROP_G_L` :112) o ΔE ≥ +2 g/L; `L` = muestra química anterior. `_bounded_smoothstep_activation` (:1360): rampa `t_s = L+s·(U−L)`, `D = max(d·(U−L), 0.25 h)`, smoothstep; con s=0.7351, d=1.0639 (natural). Si `U≤L`: escalón en U. Es **encendido** (A≡1 después), no apagado.

---

## 6. Estado y trazabilidad del input CO2 (asunto cerrado)

**Cadena de carga LOT2 [HECHO VERIFICADO]:** el constructor busca primero `CO2_FILT_*`; usa los filtrados cuando son legibles; usa raw **solo** como fallback para intervalos no cubiertos, aplicándole una mediana móvil centrada de 61 puntos, etiquetado `raw_rolling_median_fallback` en las tablas QC.

**Prueba causal A/B controlada (ya ejecutada, no repetir) [HECHO VERIFICADO]:**

- **A** (histórico, raw fallback para lot2_F1 porque `CO2_FILT_F1_pt2.csv` era ilegible por una ruta absoluta externa rota): `kCO2_release_h = 15.985681`.
- **B** (canónico actual, `CO2_FILT_F1_pt2.csv` cargado): `kCO2_release_h = 3.883700205` — reproduce exactamente los resultados versionados actuales; A reproduce el histórico con tolerancias <1e-5.

Conclusiones demostradas: el salto se explica **exclusivamente** por la recuperación del input filtrado canónico; Python/SciPy no lo explica materialmente; **los parámetros naturales fueron idénticos A/B**; las métricas de validación cambian poco pese al gran cambio de dos parámetros sintéticos. Los resultados actuales versionados son coherentes con el input canónico. **Este tema está cerrado**; la identificabilidad sintética queda solo como observación histórica menor. El foco actual es mosto natural.

**Limitación de convención de unidades documentada [HECHO VERIFICADO]:** la señal LAB016–018 se convierte con la convención oficial del logger (24.16 L/mol, factor 0.74, 2 L), mientras la cadena del artefacto CO2 congelado (`co2_cross` :133, `run_lot2_data_preview` :82) usa 22.414 L/mol sin ese factor. El notebook holdout respetó ambas implementaciones sin renormalizar `matrix_gain`; esta incompatibilidad puede contribuir al sesgo y debe resolverse **antes** de cualquier recalibración futura.

---

## 7. LAB013–LAB015 (triplicado, mosto natural, SP 16 °C)

**[HECHO VERIFICADO contra archivos]** SP = 16 °C (T mediana 16.0–16.2 °C en los tres). Contenido:

- **Química Y15:** G, F, YAN (+amonio/PAN), Gly — 7 muestras dinámicas + 1 pre-inóculo por LAB (`Y15_LAB013-015.csv`).
- **Biomasa Oculyze:** **9 muestras por LAB** (`report.csv`), t0 proxy = muestra-1: 0 / 2.5 / 7 / 23 / 29 / 47.5 / 53 / 71.5 / 143.5 h; X 0.17–2.11 kg/m³, Xd 0.002–0.184.
- **Brix/densidad/DO/CO2 disuelto** (Carbodoseur) en 10 muestras (`LAB013-LAB015-offline-combined.csv`, `-offline-measurements.csv`).
- **CO2 gaseoso no confiable** (documentado; nunca usado para estimación; hipótesis microleak [PENDIENTE]).
- **t0 definitivo pendiente** (`time_h` vacío en el CSV offline).
- Con `nutricion_activa` = 0 en toda la serie (verificado en el notebook §11.3): sin eventos de bomba → sin nutrición declarada en estos LABs.

**Uso actual [HECHO VERIFICADO]:** el notebook holdout usa LAB013–015 solo para (i) brackets químicos diagnósticos (`G+F drop ≥5 g/L`; E no disponible) — LAB013 solapa el rango de onsets observados de LAB016–018 (22.3–24.3 h), LAB014 es más temprano y LAB015 más tardío; (ii) comparación de X congelado contra Oculyze (con ICs del pre-inóculo y T medida). **Todavía no usa** su química temporal para calibración ni su CO2 disuelto/DO.

**Valor relativo [INTERPRETACIÓN]:** por el problema del CO2 gaseoso, su valor inmediato está en estados/química/biomasa (16 °C) más que en calibrar la capa gaseosa.

---

## 8. LAB016–LAB018 y holdout (mosto natural, SP 20 °C)

**[HECHO VERIFICADO contra archivos]** SP = 20 °C (T mediana 19.9–20.1 °C). Sauvignon Blanc. Contenido real:

- **CO2 gaseoso confiable** (crudo + `CO2_FILT_*`), máscara de artefactos auditada (~2.5–3.6 % excluido).
- **Temperatura medida** (input del modelo) + canal binario `nutricion_activa`.
- **Offline:** Brix/densidad/temp de muestra/volumen residual en 8 muestras por LAB (`LAB016-018-offline-measurements.xlsx/.csv`). **Sin mediciones de X, Xd, N/YAN, G, F, E, Gly u O2** durante la fermentación.
- **Biomasa Oculyze:** **3 muestras por LAB** (≈8.9, 10.9, 56.2 h; X 0.17–1.74 kg/m³) — menos puntos que LAB013–015.
- **ICs químicas heredadas** del mismo mosto (LAB013-2/014-2/015-2, sin PI): G0 74.05, F0 77.73, YAN0 244.33 mg/L → N0 0.24433 kg/m³, Gly0 1.14 (`CondicionesIniciales`).
- **t0 inequívoco:** fin del pulso de inoculación según el log (2026-09-01 00:03:55 / 00:04:00 / 00:04:07) — verificado contra el flanco de caída de `nutricion_activa`.
- **Nutrición:** eventos tardíos a **+56.93 h** (LAB016, 3.8 min; LAB018, 4.1 min) y **+56.93/+57.13 h** (LAB017, dos pulsos: 4.0 y **7.8 min**). Dosis/composición **no documentadas** [PENDIENTE] (§11). Además existen pulsos cortos de muestreo ~8.8–9.3 h (LAB016: tres de 1.3–2.5 min) clasificados como eventos de proceso/muestreo no modelados.
- **Fallbacks declarados en el notebook:** `X0 = 0.45 kg/m³`, `Xd0 = 0` (fallback del pipeline natural, sin ensayo de biomasa t≈0 homologado); E0 por escenarios pre-declarados (A: 0 g/L físico; B: mediana histórica). **No presentar estos valores como condiciones medidas.**

### 8.1 Qué hace el notebook holdout (protocolo congelado)

Carga θ_natural + capa CO2 natural (hashes verificados), simula forward sin optimizadores y compara solo CO2 (la Tabla 2 de estados core reporta honestamente `n=0`: Brix/densidad no se convierten en azúcar sin función de observación validada). Dos dominios: `pre_nutrition_clean` (holdout causal primario, hasta el primer evento tardío) y `full_record_context` (descriptivo). Conversión oficial 24.16/0.74/2 L; `matrix_gain` sin renormalizar (§6).

### 8.2 Resultado del holdout estricto [RESULTADO DIAGNÓSTICO]

Onset observado 22.30–24.25 h vs predicción (gate degenerado a escalón t=0 por falta de química) 5.7–6.2 h: **16.10–18.53 h demasiado temprano**. RMSE pre-nutrición alto; el veredicto descriptivo del notebook: la cadena CO2 **no** generaliza razonablemente con este protocolo congelado sin ancla de activación. Reparto del error entre upstream y capa: **no identificable** con estos datos.

### 8.3 Diagnóstico time-shift [RESULTADO DIAGNÓSTICO]

Traslación pura por Δonset observado−predicho: reduce el RMSE sustancialmente; queda retraso residual ~1.1–5.0 h. Atribución: el error es **principalmente lag/activación**, con residuo de amplitud/forma.

### 8.4 Diagnóstico onset-conditioned activation [RESULTADO DIAGNÓSTICO]

Reposicionar el gate histórico (pseudo-bracket `[0, t_onset_obs]`, s/d congelados) sin tocar upstream: error de onset 16.10–18.53 h temprano → **2.86–3.13 h tarde**; RMSE −77 a −86 % (0.376→0.053; 0.312→0.072; 0.326→0.071); peak 43–49 h vs 41–47 h; amplitud 0.75–0.77 vs 0.79–0.81 g/L/h. No es evidencia química ni solución final (usa CO2 observado para ubicar el gate).

### 8.5 Diagnóstico con pulso N presumido [RESULTADO DIAGNÓSTICO]

Dosis de protocolo 1.0 g SFX + 0.4 g FDA → ΔN = 0.14 kg/m³ (LAB016/018: 1 evento; LAB017: 0.14+0.14). La implementación respeta la dosis (saltos exactos verificados; máximo transitorio de N 0.27/0.31/0.27 kg/m³). Resultados: la cola se corrige casi por completo (qCO2@150 h sin pulso 0.27–0.28 → con pulso 0.005–0.023 vs observado 0.01–0.03 g/L/h); F1/F3 razonables; **F2 no reproduce la reactivación rápida** (bump ~+35 % observado en LAB017; el mecanismo congelado solo atenúa). Limitación de API documentada: `build_driver_cache` soporta **un solo** pulso N in-process; dos saltos vs uno equivalente 0.28 resultan indistinguibles (<1e-8 en qgas).

### 8.6 Barridos estructurales [RESULTADO DIAGNÓSTICO]

- **`pulse_activity_gain`** (0.25→2.0, rise congelado 64.7 h): gain alto genera reactivación visible pero destruye la cola y no corrige el retraso impuesto por `pulse_t_rise_h` (peaks predichos 88–90 h vs observados ~63 h). Un gain permanente no puede dar bump + buena cola.
- **Transitorio rise-decay** (multiplicador causal `1+A·B(t)` sobre qprod efectivo; A∈{0.1,0.2,0.3}, τ_rise∈{1,2,4} h, τ_decay∈{4,8,12} h): `A≈0.30, τ_rise≈2 h, τ_decay≈4 h` reproduce LAB017 (35.74 % vs 35.59 %; peak +4.82 h vs +5.71 h) y retorna a la cola histórica (0.0054 g/L/h @150 h) — pero genera respuestas ~14–16 % en LAB016/018 (observadas ~9.6/20.2 %): **no explica la selectividad por fermentador**. Valores diagnósticos, no calibrados.

### 8.7 Comparación histórica ~20 °C [RESULTADO DIAGNÓSTICO, exploratorio]

LAB016–018 son la referencia isotérmica de mosto natural a 20 °C. Contexto: **LAB002** (SP 21 °C, mejor candidata térmica, pero CO2 excluido por QC); **LAB001** (SP 18→21 °C, no isotérmica, CO2 QC-excluido); **LAB290226** (23→20 °C desde ~media campaña, medio no documentado). Solo lectura exploratoria; las anclas temporales de LAB001/002/290226 no están homologadas.

---

## 9. Resultados y validaciones actuales (resumen)

| Resultado | Estado |
|---|---|
| θ_natural (11 parámetros, LAB004–012, 7 estados) | versionado, congelado |
| Capa CO2 natural (9 parámetros; LAB012 holdout de matriz) | versionada, adoptada (commit 0b86664) |
| Capa CO2 sintética (input canónico CO2_FILT) | versionada, adoptada; asunto 15.99→3.88 cerrado (§6) |
| Holdout externo LAB016–018 (CO2, todo congelado) | ejecutado; onset muy temprano sin química; error dominado por posicionamiento del gate |
| Diagnósticos onset/pulso/gain/transitorio | ejecutados, sin fitting; conclusiones §8 |
| Holdout end-to-end independiente | **no existe todavía** (LAB012 participó de θ_natural) |

**Funciona razonablemente [HECHO VERIFICADO/RESULTADO DIAGNÓSTICO]:** peak principal (tiempo/amplitud) con gate bien posicionado; cadena de unidades (auditoría Oculyze 72/76); t0 LAB016–018 inequívoco; máscara CO2 event-aware auditada (90 min reproducidos); contrafactual de pulso corrigiendo la cola; hashes/integridad de artefactos.

---

## 10. Problemas estructurales identificados (verificados)

| # | Defecto | Clasificación |
|---|---|---|
| A1 | **onset depende de química offline futura** (bracket usa la muestra que evidencia actividad) → no causal para un estimador online | estructural + datos |
| A2 | sin química post-inoculación el bracket degenera a `[0,0]` → gate escalón en t=0 (LAB016–018) | datos + estructural |
| B | **terminación upstream débil**: sin pulso, qprod 33–66 % del peak a 100–150 h; cola histórica sobrepredicha (mediana 2.2× al final del registro) | estructural |
| C | **N no limita βG/βF** (solo μ); sin separación PAN/amoniacal en el estado N | estructural (decisión) |
| C2 | pulso N entra como salto de estado + términos post-pulso **en la capa CO2** (r(t), gain) — no como dinámica del central | estructural |
| D | **muerte celular inerte** a 16–22 °C (kd=0; td(E)≈305–310 K) vs Oculyze LAB013–015 con Xd 0.002–0.184 kg/m³ (señal real) | discrepancia estructural |
| E | **fructosa residual** (F 17–27 g/L a 150 h) mantiene qprod alta en la cola | estructural |
| F | **respuesta al pulso**: un solo término (rampa 64.7 h + gain permanente 0.25) intenta representar a la vez respuesta rápida, efecto sostenido y terminación lenta | estructural (forma funcional) |
| G | **cola de CO2 histórica sobrepredicha** (39 % de puntos censurados en t>100 h) | datos + metodología |
| H | **censura LOD unilateral** barata (~1σ/punto) reducía el peso de la cola en el ajuste | metodología de ajuste |
| I | **matrix_gain** (3.12) escala empírica que absorbe sesgos de amplitud y de convención de unidades | parametrización |
| J | convención SCCM→g/L/h inconsistente entre cadenas (24.16+0.74 vs 22.414) | datos/metodología |
| K | gain y rise en/near cotas (no identificados); LAB016–018 sin química temporal (ICs heredadas) | parametrización + datos |

**La cola no es del pool [HECHO VERIFICADO]:** con k=0.4246 h⁻¹ y release continuo, τ de vaciado ≤ ~20 h en el rango operativo; el pool no puede sostener una cola de 90 h con amplitud 0.3–0.5 g/L/h — la cola es upstream.

---

## 11. Nutrición y N: hechos vs incertidumbres

### 11.1 Lo que usa el código hoy [HECHO VERIFICADO]

- **Capa CO2 (histórico):** ΔN = 0.14 kg/m³ para los 9 naturales, derivado de `SPRINGFERM_XTREM_G=1.00`, `FDA_G=0.40`, `YAN_MG_PER_MG_PRODUCT=0.20` (:106–108) en 2 L (timing: cruce de densidad 1040 g/L, fallback calendario ICS). **Dosis de PROTOCOLO, no medición** (`composition_source="user-specified common LAB protocol"`).
- **Upstream (histórico):** ΔN ≈ 0.08 kg/m³ del workbook (`pulso_nut`, loader :246). Inconsistencia 0.08 vs 0.14 documentada.
- **LAB016–018 (diagnóstico):** tiempos de los eventos del log; dosis presumida de protocolo 0.14/0.28 solo como forward diagnóstico.
- **Mecanismo:** salto exacto de N en el estado + respuesta en la capa (§2.4). N limita μ vía `n/(n+kn)`; no hay término adicional post-pulso en el central más allá del salto.

### 11.2 Formulación real [PENDIENTE]

Información del operador (~90 % de confianza, sin confirmar): F1/F3 ≈ **0.8 g SFX + 0.4 g FDA**; F2 ≈ **doble** (≈1.6 + 0.8). Consistente con la duración del segundo pulso de F2 (7.8 vs ~4 min), pero **no probado**. Bajo el factor histórico 20 %, equivaldría a ΔN = 0.12/0.24 kg/m³ (vs 0.14/0.28 de protocolo). **Separar implementación actual de formulación experimental real; no cambiar unidades ni parámetros hasta confirmar** (masas, aporte YAN de cada producto, volumen real).

### 11.3 Semántica YAN/PAN/ammonia — deuda de datos [HECHO VERIFICADO de la implementación]

En datasets naturales/piloto la relación esperada es `YAN = PAN + 0.82·AMMONIA` cuando AMMONIA está en mg NH3/L. El repo reconstruye componentes como `YAN_components_mg_l = PAN_mg_l + NH4_mg_l` **sin** el factor 0.82 (`new_must_data_loader.py:252`; `run_secondary_metabolite_data_review.py:134`). El estado N usa el YAN medido (no la reconstrucción), por lo que el impacto directo en θ_natural es nulo o indirecto, pero **cualquier uso futuro de componentes PAN/NH4 para inference de nutrición hereda esta ambigüedad**. Deuda científica documentada; no corregir en esta fase ni mezclar con el cierre de CO2.

---

## 12. Implicaciones para el estimador de estados

**Compatibilidad de la arquitectura actual:**

| Componente | Causal online | Madurez |
|---|---|---|
| ODE central + pulsos como inputs conocidos | ✅ compatible | maduro (congelado) |
| temperatura como input | ✅ | maduro |
| máscara CO2 event-aware (existe; portar a causal) | ✅ con porting | madura |
| pool disuelto + release continuo (τ corta) | ✅ | maduro |
| **gate químico por bracket offline** | ❌ usa información futura | **bloqueante** |
| respuesta post-pulso (rampa 65 h + gain permanente) | ✅ causal pero estructuralmente inadecuada (§8.6) | a rediseñar |
| matrix_gain / convención de unidades | ⚠️ inconsistencia 24.16 vs 22.414 | a unificar |
| θ_natural | ✅ | maduro; recalibrable con datos nuevos |
| capas Xd (kd=0) | Xd probablemente **no observable** | proyectar el filtro sobre {X,N,G,F,E,Gly}+CO2 |

**Prerequisitos antes de implementar el EKF/MHE seriamente [bloqueantes]:**

1. **mecanismo causal de onset** (proxy online: densidad/Brix/CO2 temprano, o estado dinámico de activación);
2. inputs de nutrición trazables (dosis/tiempo confirmados por escrito);
3. arquitectura post-nutrición decidida (transitorio separado de terminación, §16);
4. terminación representada sin depender del artefacto del pulso (control sin nutrición, §15);
5. observation functions validadas (CO2 completa; Oculyze X ×0.03; YAN→N; Y15→G/F/Gly; Brix/densidad sin función validada);
6. ICs robustas (PI + 0 h reales);
7. Q/R con base en datos (réplicas Oculyze; triplicados Y15);
8. manejo causal de artefactos (portar la máscara);
9. validación con un experimento no usado en la recalibración.

**[INTERPRETACIÓN]** Un estado de actividad fermentativa `a(t)` (lag→1→bump→decay) representaría causalmente lo que hoy fuerzan el gate a posteriori y el gain permanente; evaluar identificabilidad antes de decidir.

---

## 13. Qué tendría sentido recalibrar y en qué orden

**PRIORIDAD ALTA** (datos ya existen o se obtienen con el experimento de §15):

1. **Parámetros de la respuesta nutricional separada** (transitorio rise-decay: A, τ_rise, τ_decay + terminación lenta propia) — soportado por: LAB016–018 (bump/cola con CO2 confiable) **una vez confirmada la dosis**, más las fermentaciones nuevas con dosis trazable. Requiere añadir residual de amplitud post-pulso (hoy inexistente).
2. **Ganancia/gate de activación natural** (chem_start/dur o su reemplazo causal) — soportado por LAB016–018 onset + LAB013–015 brackets químicos + LAB002 (si se rehabilita su CO2, improbable).
3. **θ_natural (total o parcial)** — solo tras incorporar LAB013–015 (química 16 °C + Oculyze 9 puntos/LAB) y las fermentaciones nuevas; los datos existen en el repo pero aún no participan del ajuste.

**PRIORIDAD MEDIA:**

4. **kCO2_release_h / CO2sat_scale naturales** — con la convención de unidades unificada (§6) y CO2 de nuevas campañas; hoy kCO2 natural está razonablemente interior (0.42).
5. **Bloque de consumo G/F (kG/kF/iG/iE)** — requiere G/F temporal denso (LAB013–015 + fermentaciones nuevas con calendario §15).
6. **Parámetros de N (qN, sN)** — requiere YAN temporal pre/post pulso.
7. **Kd0 / muerte** — solo si Xd muestra señal sistemática en Oculyze (LAB013–015 la tiene: Xd hasta 0.184 kg/m³); hoy kd sin señal a 20 °C.
8. **Condiciones iniciales** (X0, E0) — con mediciones PI/0 h reales del plan nuevo; hoy son fallback/escenario.

**NO HACER TODAVÍA** — ver §14.

---

## 14. Qué NO conviene recalibrar todavía

1. **Nada contra LAB016–018 como training** sin decidir antes, por escrito, su rol: hoy son el **holdout externo**; absorberlos al fit sin dejar otro holdout destruye la separación calibración/validación.
2. **`pulse_activity_gain` / `pulse_t_rise_h`** en su forma actual: el barrido demostró el trade-off (gain alto destruye la cola; rise de 65 h impone el retraso); recalibrarlos compensaría un defecto de forma funcional.
3. **Cualquier parámetro que compense el gate no causal**: primero el mecanismo causal de onset; si no, la recalibración absorbería el error de posicionamiento.
4. **Dosis de nutrición**: sin confirmación documentada (masas/composición), cualquier ΔN ajustado sería tuning contra una hipótesis.
5. **matrix_gain** antes de unificar la convención SCCM→g/L/h (24.16+0.74 vs 22.414): re-ajustarlo ahora consolidaría el sesgo de convención en la ganancia.
6. **Bloque secundario/aroma y constantes fijas**: sin nuevas observaciones de esos estados.
7. **Capa CO2 sintética**: asunto cerrado (§6); el foco es natural.
8. **Kd0 solo con datos de 20 °C** (donde el modelo predice kd=0): usar LAB013–015 (16 °C) + validación de viabilidad.

---

## 15. Experimentos adicionales recomendados (propuesta, no realizada)

**Diseño recomendado [INTERPRETACIÓN]: control SIN nutrición + fermentación con nutrición de dosis conocida**, mismo mosto/cepa/SP 20 °C, nutrición en el mismo estado de densidad (~1040 g/L) que el protocolo histórico. Justificación: el contraste de dosis ya existe (parcialmente) en LAB016–018 pendiente de confirmar; lo que **no existe en todo el dataset** es terminación observada sin el artefacto del pulso. Hipótesis que discriminaría:

- **terminación natural** (control) vs **efecto real del pulso** (tratado): separa efecto nutricional del comportamiento basal;
- **amplitud y dinámica rápida post-pulso** (ventana −1/+2/+4–6/+12/+24 h densa): ancla A, τ_rise, τ_decay con input trazable;
- **dose-response** contra F2 (dosis doble) una vez confirmadas las dosis.

Calendario de muestreo por fermentador (nutrición solo en F-B): PI; 0 h; 6–8 h; 12 h; 24 h; 36 h; 48 h; −1 h pre-nutrición; +2 h; +4–6 h; +12 h; +24 h post; 96 h; final. G/F/YAN/Oculyze/Brix/densidad/Gly según tabla; etanol solo externo en PI, pre-nutrición, +8–12 h post y final (Alcolyzer no disponible; mínimo aceptable 3 de esas 4). Metadata obligatoria: gramos/producto/volumen/hora exactos, log `nutricion_activa` para t0, réplicas Oculyze ≥2 en puntos clave (para R). Además: **un futuro holdout a ~18 °C** sería más informativo que seguir ajustando sobre los mismos datos (interpola el rango 16–20 °C y testea Arrhenius).

---

## 16. Arquitectura futura propuesta (NO implementar todavía)

```
UPSTREAM
  ↓
activación química/metabólica CAUSAL      (hoy: bracket offline a posteriori)
  ↓
qprod_base
  ↓
evento nutricional conocido (t_pulso, ΔN, composición trazables)
  ├─ salto real de N en el estado                    [implementado]
  ├─ respuesta metabólica rápida transitoria         [SOLO PROPUESTA; τ~2–8 h]
  └─ dinámica lenta de terminación propia            [SOLO PROPUESTA; decenas de h]
  ↓
CO2 disuelto
  ↓
continuous release                                  [implementado; mantener]
  ↓
qgas
```

Estado de las partes: implementado (salto N, release continuo, pool, gate smoothstep — pero no causal); parcialmente implementado (respuesta post-pulso como rampa+gain — existe pero con la forma inadecuada); solo propuestos (activación causal, transitorio rise-decay, terminación independiente, estado de actividad `a(t)`, unificación de convención de unidades). La separación A (respuesta rápida, ~horas) vs B (terminación, ~decenas de horas) es la hipótesis estructural principal, apoyada por los barridos de §8.6 y pendiente de: confirmación de dosis, evaluación en F1/F3 y calibración formal con residual de amplitud.

---

## 17. Prioridades de trabajo (roadmap)

| # | Etapa | Criterio de salida |
|---|---|---|
| 1 | Confirmar metadata/dosis con el operador/colega (§11.2, §18) | dosis SFX/FDA + factor YAN + t0 LAB013–015 por escrito |
| 2 | Corregir inputs LAB016–018 (ΔN por fermentador; re-ejecutar contrafactual) | cola corregida con dosis confirmada; desviación documentada |
| 3 | Cerrar dataset Oculyze/química LAB013–018 (t0 de LAB013–015, réplicas) | dataset único versionado sin ambigüedades |
| 4 | Unificar convención SCCM→g/L/h (24.16/0.74 vs 22.414) y decidir matrix_gain | una sola convención documentada en código y docs |
| 5 | 1–2 fermentaciones informativas (§15: control + dosis conocida) | perfiles con calendario cumplido y metadata completa |
| 6 | Seleccionar arquitectura mínima (§16) | lista cerrada de cambios estructurales con criterios de rechazo |
| 7 | Recalibrar upstream si corresponde (θ con datos nuevos) | sin cotas activas injustificadas; residuos aceptables |
| 8 | Recalibrar capa CO2 (transitorio + terminación + residual de amplitud) | cola y bump reproducidos en calibración |
| 9 | Holdout externo (fermentación no usada; idealmente ~18 °C) | métricas end-to-end dentro de tolerancias pre-declaradas |
| 10 | Congelar modelo y comenzar estimador (bloqueantes §12 resueltos) | filtro causal validado contra el holdout de #9 |

---

## 18. Hechos pendientes de confirmar

1. **Dosis real LAB016–018** (¿0.8+0.4 / doble?) y del histórico LAB004–012 (¿1.0+0.4?); masas pesadas y volúmenes.
2. **Aporte YAN de SFX y FDA** (¿el 20 % aplica a ambos productos?).
3. **Procedencia de 30 pg/célula** (constante Oculyze→kg/m³).
4. **t0 físico de LAB013–015** (`time_h` vacío en el CSV offline).
5. **Microleaks** en CO2 de LAB013–015 (hipótesis).
6. Significado físico pretendido de `pulse_activity_gain`/`pulse_t_rise_h` y consciencia del gate no causal y de la cola histórica (preguntas al colega que calibró).
7. Por qué el upstream usó ΔN=0.08 y la capa 0.14; por qué LAB012 fue holdout de capa habiendo participado de θ.
8. Rehabilitación o no de LAB002 como referencia térmica (CO2 QC-excluido).
9. Sincronización pendiente de documentos espejo: `CO2_MODEL_EXPLANATION.md` aún cita el `kCO2_release_h` sintético pre-adopción (15.986) y el `.tex` homónimo de este documento requiere la misma actualización.

---

## Tabla de prioridades

| Tema | Estado actual | Evidencia | Riesgo | Acción siguiente |
|---|---|---|---|---|
| θ natural (upstream) | congelado, 11 parámetros, LAB004–012 | `theta.csv`; §4 | bajo | mantener; recalibrar solo con datos nuevos (LAB013-015 + fermentaciones §15) |
| Capa CO2 natural | congelada, 9 parámetros (3 en cota) | `fit_parameters.csv`; §5 | medio (cotas activas) | re-estimar tras unificar convención y dosis |
| Capa CO2 sintética | adoptada, asunto cerrado | A/B causal (§6) | bajo | nada (no investigar más) |
| Input CO2 lot2 | canónico `CO2_FILT_*`, raw fallback | §6, cerrado | bajo | documentar (hecho) |
| Onset causal | **no existe**; bracket a posteriori | §8.2–8.4, §10-A | **alto** (bloquea estimador) | mecanismo causal o estado de actividad |
| Terminación | débil; dependía del gain del pulso | §8.5, §10-B | alto | control sin nutrición (§15) |
| Respuesta nutricional | rampa 65 h + gain 0.25 inadecuados | barridos §8.6 | alto | transitorio rise-decay separado; residual de amplitud |
| N / YAN | N solo en μ; dosis inconsistente 0.08/0.14; deuda PAN+0.82 | §11 | medio | confirmar dosis; documentar 0.82; evaluar β(N) |
| Muerte celular (Xd) | inerte a 16–22 °C; Oculyze con señal a 16 °C | §2.3, §7 | medio | revisar con Xd de LAB013–015 |
| LAB013–015 | química+biomasa nuevas sin usar en fit; CO2 no confiable | §7 | medio | incorporar tras t0; no usar su CO2 gaseoso |
| LAB016–018 | holdout externo ejecutado; diagnósticos completos | §8 | alto si se convierten en training | mantener como holdout hasta decisión escrita |
| Oculyze | report.csv versionado (6 LAB); imágenes retiradas | §3.2 | bajo | réplicas para R en futuras campañas |
| CO2 disuelto | pool interno de la capa; Carbodoseur solo histórico | §2.1 | bajo | opcional: estado del central solo si el estimador lo necesita |
| Convención de unidades | inconsistente 24.16/0.74 vs 22.414 | §6 | medio | unificar antes de recalibrar ganancias |
| EKF/estimador | no iniciado; 9 bloqueantes | §12 | alto | resolver bloqueantes 1–4 primero |

---

*Documento v3 (2026-09-08), reestructurado desde la v2 tras auditoría de solo lectura del repositorio (código, datos y resultados verificados contra el árbol real; líneas citadas verificadas). No se modificaron modelos, notebooks, datos ni resultados. Único archivo modificado: este `.md`. Su espejo `.tex` y `CO2_MODEL_EXPLANATION.md` requieren sincronización posterior (§18.9).*
