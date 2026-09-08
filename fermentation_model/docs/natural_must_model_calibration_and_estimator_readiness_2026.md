# Modelo de mosto natural: calibración histórica, auditoría 2026 y preparación del estimador de estado

**Documento técnico de referencia — versión 2 (consolidada), 2026-09-08**

Alcance: consolidar todo lo verificado sobre (a) la calibración histórica del modelo cinético de mosto natural (LAB004–LAB012), (b) la capa de observación CO2, (c) los experimentos LAB013–LAB018, y (d) los diagnósticos estructurales recientes (dosis de nutrición, barrido de `pulse_activity_gain`, prueba transitoria rise-decay), como base para: terminar/revisar la calibración, diseñar 1–2 fermentaciones adicionales, e iniciar el desarrollo del estimador de estado.

Convención de etiquetas usada en todo el documento:

- **[HECHO VERIFICADO]** — verificado directamente en código o datos del repositorio (se cita archivo y función/línea).
- **[RESULTADO DIAGNÓSTICO]** — resultado de una simulación/prueba forward con parámetros congelados (sin fitting, sin optimizadores). No son parámetros calibrados.
- **[INTERPRETACIÓN]** — lectura razonada de hechos y diagnósticos; no es un hecho en sí.
- **[HIPÓTESIS PENDIENTE]** — pendiente de confirmación (con el colega que calibró, con el operador/laboratorio o con nuevos datos).

Archivos nucleares:

| Rol | Ruta |
|---|---|
| ODEs upstream, ajuste de parámetros | `fermentation_model/shared/run_new_must_glycerol_estimability_doe.py` (`base`) |
| Loader de datos históricos natural | `fermentation_model/shared/new_must_data_loader.py` |
| Calibración upstream natural 2026 | `fermentation_model/laboratory_2026/run_estimability_historical_by_medium.py` |
| Capa CO2 2026 (matrix cross-validation) | `fermentation_model/laboratory_2026/run_co2_matrix_cross_validation_2026.py` (`co2_cross`) |
| Módulo CO2 (qprod base, solubilidad) | `fermentation_model/pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py` (`co2_model`) |
| Tasas core / constante CO2–etanol | `fermentation_model/shared/run_secondary_joint_campaign_doe.py` (`joint`, `CO2_G_PER_G_ETHANOL`) |
| θ natural | `fermentation_model/laboratory_2026/results/estimability_historical_natural/theta.csv` |
| Parámetros capa CO2 | `fermentation_model/laboratory_2026/results/co2_matrix_cross_validation_2026/fit_parameters.csv` |
| Notebook holdout LAB016–018 | `fermentation_model/laboratory_2026/notebooks/lab016_018_natural_must_holdout.ipynb` |
| Notebook LAB013–015 | `fermentation_model/laboratory_2026/notebooks/lab013_015_natural_must_co2_model_analysis.ipynb` |
| Workbook maestro natural | `fermentation_model/data/Laboratorio 2026/Vendimia_2026/mosto_natural_xthiol.xlsx` |

---

## 1. Objetivo, arquitectura general y los cuatro fenómenos

### 1.1 Esquema

```
offline chemistry + biomass + T          (sensores + Y15 + Oculyze + densidad)
        ↓
ODE upstream  (base.simulate, LSODA, saltos exactos de pulsos)
X, Xd, N, G, F, E, Gly
        ↓
CO2 production   qprod_base = 0.4777 · dE/dt = 0.4777·(βG+βF)·X
        ↓
chemical activation A(t)                 (gate de encendido, bracket químico)
        ↓
pulse / nitrogen response                r(t), activity_multiplier, Δqprod_pulso
        ↓
dissolved CO2 pool                       (solubilidad Csat(T,E,G,F))
        ↓
continuous release                       qgas = min(k·C·release_fraction, disponible)
        ↓
gaseous CO2 measurement                  qobs = matrix_gain · qgas (SCCM→g/L/h)
```

### 1.2 Bloques

**A) Modelo cinético upstream natural [HECHO VERIFICADO]**
Estados: `X, Xd, N, G, F, E, Gly` (`base.STATE_NAMES`); canales de entrada discretos `INPUT_CHANNELS = ("N","G","F","E","X")`. La temperatura no es estado: es input exógeno interpolado de la serie medida (`base.temperature_at`). Ecuaciones en `base.rhs` (:445–468) y `base.kinetic_terms` (:387–442).

**B) Capa de observación/transferencia CO2 [HECHO VERIFICADO]**
`co2_cross.effective_qprod_grid` (:1668) + `co2_cross.raw_qgas_grid_prediction` (:1748). El O2 no es estado del upstream: existe solo dentro de la capa CO2 (pool inicial `O2_initial_scale·O2sat`, consumo Monod, gate anaeróbico `ferment_fraction = 0.08 + 0.92·φ_ana`).

**C) Datos offline [HECHO VERIFICADO]**
Workbook homologado (química G/F/YAN/Gly/E + biomasa Oculyze + Brix/densidad + DO + CO2 disuelto Carbodoseur). Para LAB013–018: `data/mem2026/LAB013-015/` y `data/mem2026/LAB016-018/`.

**D) Señales online [HECHO VERIFICADO]**
CO2 crudo y filtrado (SCCM) y temperatura por fermentador; canal binario `nutricion_activa` (ledger de pulsos de bomba).

### 1.3 Pertenencia de parámetros

| Grupo | Parámetros | Fuente |
|---|---|---|
| θ_natural (upstream) | mu0, qN, betaG0, betaF0, qEG, qEF, iG, iE, Kd0, gammaG0, gammaF0 (re-estimados) + sN, sG, sF, qXG, qXF, m0, Kn0/Kg0/Kf0/Kig0/Kie0 y bloque secundario/aroma fijos | `theta.csv` |
| Capa CO2 (natural) | kCO2_release_h, CO2sat_scale, O2_qmax_mg_gdw_h, O2_initial_scale, pulse_t_rise_h, pulse_activity_gain, chem_activation_start_fraction, chem_activation_duration_fraction, matrix_gain | `fit_parameters.csv` (calibration_matrix = natural) |
| Inputs/eventos experimentales | tiempos de pulso N y ΔN; series de temperatura; ICs por batch (X0, Xd0, N0, G0, F0, E0, Gly0) | datos/metadatos, no parámetros |

### 1.4 Los cuatro fenómenos — visión consolidada

| Fenómeno | Mecanismo histórico | Parámetros | Datos que lo determinaron | Comportamiento en LAB016–018 | Limitación detectada |
|---|---|---|---|---|---|
| 1. lag / onset | gate químico A(t) (smoothstep sobre bracket G/F/E) | chem_start=0.735, chem_dur=1.064 | química offline (Δ(G+F)≥5 o ΔE≥2 g/L) | gate mal posicionado sin química; re-posicionado diagnósticamente reduce RMSE 77–86 % | el bracket usa química **posterior** → no causal; se necesita mecanismo causal/predictivo |
| 2. peak principal | qprod_base ∝ (βG+βF)·X, f_ferm, matrix_gain | betaG0/betaF0/iE/…, gain=3.12 | perfiles completos CO2 + estados upstream | peak 43–49 h pred vs 41–47 h obs; amplitud 0.75–0.77 vs 0.79–0.81 g/L/h | funciona razonablemente; sin defecto mayor |
| 3. caída / terminación | Monod G/F + inhibición E + **atenuación post-pulso ×0.25** | kd (inerte), kG/kF/iE, pulse_gain=0.25, rise=64.7 h | estados offline + pseudo-obs de onset/peak | sin pulso declarado: qprod 33–66 % del peak a 100–150 h → cola larga; con pulso declarado la cola colapsa | terminación biológica débil dependiente del artefacto del pulso; N no limita β; kd inerte |
| 4. reactivación post-nutrición | salto N + rampa r(t) + gain permanente | t_pulse, ΔN, pulse_t_rise_h=64.7, pulse_activity_gain=0.25 | pseudo-obs **solo del timing** del peak post-pulso | LAB017: bump ~+33 % observado tras 2 pulsos (~56.9/57.1 h); LAB016 casi ninguno; LAB018 pequeño | una rampa de 65 h no representa un bump de horas; gain permanente no puede dar bump + buena cola simultáneamente |

**[INTERPRETACIÓN]** El hallazgo central de los diagnósticos recientes: lag, reactivación rápida y terminación ocurren en escalas temporales distintas (días-horas vs horas vs decenas de horas) y la arquitectura histórica las representa con un solo mecanismo post-pulso lento; la evidencia apunta a que deben separarse.

---

## 2. Calibración histórica upstream (θ_natural, LAB004–LAB012)

**[HECHO VERIFICADO] Batches utilizados:** LAB004–LAB012 (9 fermentaciones, incluida LAB009; LAB009 fue excluida después solo de la capa CO2). `batch_summary.csv` (`results/estimability_historical_natural/`).

**[HECHO VERIFICADO] Estados observados:** los 7 estados core entraron al ajuste con observaciones del workbook homologado: X y Xd derivados de Oculyze, N de YAN, G/F de Y15, E y Gly de química. `measurement_support()` en `run_estimability_historical_by_medium.py` marca `used_in_core_fit=True` para los 7.

**[HECHO VERIFICADO] Función objetivo:** `base.residual_vector` (:595) — WSSE de residuos por estado `(pred−obs)/σ`, concatenados por batch y estado. Fallo de integración penalizado con 1e6×1000.

**[HECHO VERIFICADO] Sigmas/pisos** (`base.MEASUREMENT_ERROR_FLOOR/REL`, :174–191), σ = max(piso, rel·max(|obs|, piso)):

| Estado | piso | rel |
|---|---|---|
| X | 0.06 kg/m³ | 8 % |
| Xd | 0.06 kg/m³ | 12 % |
| N | 0.012 kg/m³ | 8 % |
| G | 2.5 g/L | 2.5 % |
| F | 2.5 g/L | 2.5 % |
| E | 2.0 g/L | 2.5 % |
| Gly | 0.35 g/L | 5 % |

**X/Xd sí participaron fuertemente de la WSSE [HECHO VERIFICADO]:** con ~13 puntos Oculyze por LAB y pisos de 0.06 kg/m³, los residuos de biomasa son comparables en escala a los de G/F. La trayectoria de biomasa (plana, con Xd pequeño) es uno de los anclajes del ajuste.

**[HECHO VERIFICADO] Optimizador:** `base.fit_parameters` (:629) — `scipy.least_squares` (`trf`, log-espacio, `x_scale='jac'`, tolerancias 2e-5), con multistart determinista y pulido por profile-likelihood de 3 puntos para `Kd0` y `qN`.

**[HECHO VERIFICADO] Parámetros estimados (11):** mu0, qN, betaG0, betaF0, qEG, qEF, iG, iE, Kd0, gammaG0, gammaF0 (`theta.csv`, `reestimated_in_this_notebook=True`). El resto (sN, sG, sF, qXG, qXF, m0, constantes Arrhenius, bloque secundario/aroma) quedó fijo.

**[HECHO VERIFICADO] Condiciones iniciales:** por batch, primera observación finita de cada estado. Rango histórico: X0 0.099–1.066 kg/m³; Xd0 0.001–0.121; N0 0.220–0.239 kg/m³; G0 75.0–81.6 g/L; F0 70.8–88.0; E0 9.21–11.76 g/L; Gly0 0.75–1.27.

**[HECHO VERIFICADO] NaN:** enmascarados por `np.isfinite(obs)` — los faltantes no aportan residuo.

**[HECHO VERIFICADO] t=0 histórico:** la fila `t = 0` del workbook homologado (`load_natural_batch_metadata`, `run_estimability_historical_by_medium.py:140`). Es un t=0 *de muestreo/química homologada*, no un flanco de inoculación medido.

**[HECHO VERIFICADO] Pulsos usados en la calibración upstream:** `pulses = N:t@0.08 kg/m³` derivados de `pulso_nut` del workbook. **Discrepancia documentada:** la capa CO2 después *sobrescribe* por `ΔN = 0.14 kg/m³` con timing por densidad (`co2_cross.override_natural_nutrient_pulses` :452). θ_natural y la capa CO2 no usan la misma dosis de N.

**Papel real de la biomasa [INTERPRETACIÓN]:** X/Xd informan μ y la escala; la forma de la cola de X no está bien restringida porque kd≈0. **Papel del etanol [INTERPRETACIÓN]:** E informa β e iE; E0≈9–12 g/L deja la inhibición activa desde el inicio.

### 2.1 Oculyze: semántica y conversión [HECHO VERIFICADO]

Export Oculyze (método `Viability & Concentration`, azul de metileno, `Dilution Sample 1:0`). `Concentration` = concentración **total** en 10⁶ cél/mL; `Viability` = % viable. Conversión histórica (verificada en `Datos_originales` de `mosto_sintetico_vl3.xlsx`: `C_viable/C_total = Viability/100` exacta en 72/76 filas):

```
X_viable = Concentration × Viability/100          [Mcél/mL]
Xd       = Concentration × (1 − Viability/100)    [Mcél/mL]
X_kg_m3  = X_viable × 0.03 ;  Xd_kg_m3 = Xd × 0.03
```

`MILLION_CELLS_ML_TO_KG_M3 = 0.03` con `CELL_MASS_PG_PER_CELL = 30.0` (`new_must_data_loader.py:55–57`), es decir 30 pg/célula.

**[HIPÓTESIS PENDIENTE]** La procedencia física de la constante 30 pg/célula no está documentada en el repo. Confirmar con el colega.

**Trampa semántica [HECHO VERIFICADO]:** en las hojas homologadas históricas la columna `Viability` contiene la *concentración viable* (Mcél/mL), no el %. En los exports crudos Oculyze `Viability` sí es %. No mezclar.

---

## 3. Calibración histórica de la capa CO2

**[HECHO VERIFICADO] Batches de calibración natural:** LAB004, 005, 006, 007, 008, 010, 011 (7). Holdout dentro de matriz: **LAB012**. Excluidos de CO2: LAB001–003 y LAB009. Modelo nominal: `solubility_o2_nitrogen_boost_continuous_release`.

**[HECHO VERIFICADO] Parámetros ajustados (natural):**

| Parámetro | Valor | Cota activa |
|---|---|---|
| kCO2_release_h | 0.4246 h⁻¹ | no |
| CO2sat_scale | 0.3514 | **sí (inferior)** |
| O2_qmax_mg_gdw_h | 0.15 | **sí (inferior)** |
| O2_initial_scale | 0.1954 | no |
| pulse_t_rise_h | 64.66 h | casi (superior 72) |
| pulse_activity_gain | 0.25 | **sí (inferior)** |
| chem_activation_start_fraction | 0.7351 | no |
| chem_activation_duration_fraction | 1.0639 | no |
| matrix_gain | 3.1158 | perfilado analíticamente |

**[HECHO VERIFICADO] matrix_gain:** perfilado analíticamente por mínimos cuadrados de escala (`_profile_matrix_gain` :1909). Escala empírica de la cadena SCCM→g/L/h + sesgos de amplitud.

**[HECHO VERIFICADO] Observables de la capa:** perfil completo con `σ = max(0.04, 0.10·peak_batch)` y peso `1/√n`; pseudo-observable de onset sostenido (σ=12 h); pseudo-observable del **tiempo** del peak post-pulso (ventana 72 h, σ=12 h); censura LOD unilateral `max(pred−LOD, 0)/σ` con LOD=0.05 (0.10 frío <15.5 °C). No existía residual de amplitud del bump.

**[HECHO VERIFICADO — matiz importante]** LAB012 fue holdout de la capa CO2, pero **no un holdout end-to-end independiente**: su química participó antes en θ_natural.

---

## 4. Fenómeno 1 — lag / onset

**[HECHO VERIFICADO] Preprocessing de artefactos CO2:** corrección de cero por sensor (ventana 12 h, cuantil 10 %), máscara de artefactos de muestreo (ventana 3 h, ratio 0.65), Hampel + mediana 3 pts + Savitzky–Golay 5/2, protección de respuesta a pulso (4 h), LOD 0.05/0.10 (`filter_co2_sensor_artifacts`, constantes :88–128).

**[HECHO VERIFICADO] `_onset_threshold` (:1837):** `max(LOD_early, baseline + 0.10·(peak−baseline))`, baseline = mediana de los primeros 12 h. Umbral dinámico.

**[HECHO VERIFICADO] `_sustained_onset_h` (:1849):** primer instante con **3 puntos consecutivos** sobre el umbral (interpolado).

**[HECHO VERIFICADO] `_chemical_activity_bracket` (:1302):** usando solo química: `U` = primera muestra con `Δ(G+F) ≤ −5 g/L` **o** `ΔE ≥ +2 g/L` respecto a la primera muestra química; `L` = muestra química anterior.

**[HECHO VERIFICADO] `_bounded_smoothstep_activation` (:1360):**

```
t_s = L + s·(U−L);  D = max(d·(U−L), 0.25 h)
z(t) = clip((t−t_s)/D, 0, 1);  A(t) = z²(3−2z)
```

con s = 0.735, d = 1.064 (natural). Si `U ≤ L`: escalón en `U`. El release es continuous (§7) y **no genera lag por sí mismo**.

**[HECHO VERIFICADO] Chemical activation = ENCENDIDO, no APAGADO:** una vez `t ≥ t_s + D`, `A ≡ 1` para siempre. El descenso lo controlan la rama biológica (§7) y el pool.

**Tres conceptos a no confundir [INTERPRETACIÓN]:** (1) spike instrumental (artefacto del sensor, manejado por máscara); (2) onset observado (cruce sostenido del umbral dinámico del CO2 medido); (3) activación interna del modelo `A(t)` (anclada al bracket químico).

**[HECHO VERIFICADO] Resultado LAB016–018:** sin G/F/E post-inoculación no existe bracket real; `_chemical_activity_bracket` degrada a `[0,0]` → gate escalón en t=0 → onset predicho 5.7–6.2 h vs observado 22.2–24.2 h. El diagnóstico "onset-conditioned chemical activation" (notebook holdout §12, bracket `[0, t_onset_obs]` congelando s y d) reduce el RMSE **77–86 %** (0.376→0.053 LAB016; 0.312→0.072 LAB017; 0.326→0.071 LAB018) y deja el peak aproximadamente bien alineado (43–49 h vs 41–47 h).

**[INTERPRETACIÓN]** El posicionamiento del gate explica la fracción dominante del error de la capa CO2 en LAB016–018.

**⚠ Advertencia para el estimador [HECHO VERIFICADO en el diseño del bracket]:** el bracket histórico usa la muestra química que *evidencia* actividad (química **posterior** al lag). Constituye un anclaje a posteriori, no una ley causal utilizable online: en tiempo real, en t≈10 h no se conoce la muestra de t≈24 h.

**TAREA (antes del EKF/MHE):** desarrollar una representación **causal** de la activación/lag (p. ej. función de observación sobre variables disponibles online — densidad/Brix/CO2 temprano — o un estado de actividad dinámico, §14).

---

## 5. Fenómeno 2 — peak principal

**[HECHO VERIFICADO]** En LAB016–018 con el gate condicionado: peak predicho 43–49 h vs observado 41–47 h; amplitud 0.748–0.773 vs 0.792–0.814 g/L/h. Sin defecto mayor identificado en este fenómeno. **[INTERPRETACIÓN]** El peak queda bien cuando el gate está bien posicionado y la dosis de N no interfiere; su calidad es contingente al resto, no un logro independiente.

---

## 6. Fenómeno 3 — caída / terminación

### 6.1 Estructura de qprod [HECHO VERIFICADO]

```
qprod_base = CO2_G_PER_G_ETHANOL · dE/dt = 0.4777 · (βG + βF) · X
βG = betaG0 · aβ(T) · G/(G+kG) · 1/(1+iE·E)
βF = betaF0 · aβ(T) · F/(F+kF) · 1/(1+iG·G) · 1/(1+iE·E)
```

(`joint._core_rates`, `base.kinetic_terms`; `CO2_G_PER_G_ETHANOL = 44.01/(2·46.07)`.)

**[HECHO VERIFICADO] Efecto de cada variable:**

| Variable | Mecanismo | Efecto en qprod |
|---|---|---|
| G | Monod `G/(G+kG)` | directo, principal (se agota primero) |
| F | Monod `F/(F+kF)` | directo, **el más lento** (fructosa residual) |
| E | `1/(1+iE·E)`, iE=0.040 | directo, parcial |
| N | `n/(n+kn)` **solo en μ** | **no limita βG/βF** |
| X | `dX=(μ−kd)X` | indirecto; sin muerte X queda plana |
| Xd | `dXd=kd·X` | kd>0 solo si `T ≥ td(E)`; td(E)≈315.9−0.128·E K |
| T | Arrhenius aβ | escala, no apaga |

**[HECHO VERIFICADO] Muerte prácticamente inerte:** a 16–22 °C y E≤60 g/L, td(E) ≈ 305–310 K > T ⇒ kd = 0. Xd≈0 y X plana tras el crecimiento (en el forward de LAB016–018: X plana en 1.36 kg/m³, Xd=0).

### 6.2 Diagnóstico en LAB016–018 [RESULTADO DIAGNÓSTICO]

Con parámetros congelados, sin pulso N declarado (escenario gate-conditioned): a 100–150 h `effective_qprod` = 0.083–0.166 g/L/h ≈ **33–66 % del peak**; N=0 desde temprano no frena la fermentación; F = 17–27 g/L a 150 h. Observado: caída mucho más rápida (0.28→0.02 g/L/h entre 100 y 150 h; pred 0.53→0.28).

### 6.3 La cola NO viene del pool [HECHO VERIFICADO]

Continuous release con k=0.4246 h⁻¹: la tasa efectiva de vaciado es `k·(0.05 + 0.95·C/(C+C*))`, decreciente al vaciarse: τ ≈ 4.5 h (C=0.6 g/L), 12.6 h (0.1), 19 h (0.05), 36 h (0.01). Si `qprod→0`, qgas cae 70–90 % en 10–25 h y a ≈0 en <40 h. **El pool no puede sostener una cola de 90 h con amplitud 0.3–0.5 g/L/h; la cola es upstream (actividad/terminación), no release.**

### 6.4 La cola ya existía en el histórico [HECHO VERIFICADO]

En LAB004–012 calibrados: a peak+40 h la mediana pred/obs ≈ 0.8 (razonable), pero al final del registro la sobre-predicción mediana era **2.2×** (p. ej. LAB006 0.087 vs 0.026). En t>100 h: 570 puntos, **39 % censurados**, mediana obs 0.12 vs pred 0.205 g/L/h. La censura LOD es unilateral (`max(pred−LOD,0)`, `_fit_residual` :1971–1973) con σ≈0.08: sobrepasar el LOD en la cola costaba ~1σ por punto, barato frente al peak. **[INTERPRETACIÓN]** La cola larga era un defecto histórico tolerado, débilmente penalizado; hoy se amplifica al eliminar el pulso.

### 6.5 Mecanismo histórico real del apagado

Históricamente la caída dependía de: (i) agotamiento de G/F; (ii) inhibición por E; y (iii) **de forma muy importante, la atenuación post-pulso `pulse_activity_gain=0.25`** (§8). **[INTERPRETACIÓN]** Sin el término (iii), el upstream tiene una terminación biológica débil: eso es exactamente lo que expone el holdout sin pulso.

---

## 7. Release: threshold vs continuous (consolidado)

**[HECHO VERIFICADO] Threshold release:** `qgas = min(k·smoothplus(C−C*), disponible)` — sin emisión apreciable bajo C* (meseta cero artificial).

**[HECHO VERIFICADO] Continuous release (nominal):** `release_fraction = 0.05 + 0.95·C/(C+C*)`; `qgas = min(k·C·release_fraction, disponible)` (`CO2_CONTINUOUS_RELEASE_FLOOR = 0.05`, `raw_qgas_grid_prediction` :1782–1799). Terminó nominal porque eliminó la meseta cero y mejoró onset/correlación en holdout (LAB012: RMSE 0.361→0.318; correlación 0.36→0.78; onset −32→−11 h).

**[HECHO VERIFICADO] Continuous release NO genera la fase lag por sí mismo** (el lag proviene del gate y del O2 temprano). Mantener por ahora (§13, tabla de decisiones).

---

## 8. Fenómeno 4 — nutrición: arquitectura histórica

**[HECHO VERIFICADO] Salto de N:** `base.simulate` aplica pulsos como saltos exactos (`_pulse_events` :475): `N(t_pulse⁺) = N(t_pulse⁻) + ΔN`.

**[HECHO VERIFICADO] Respuesta en la capa CO2 (`effective_qprod_grid` :1691):**

```
r(t) = clip((t − t_pulse)/pulse_t_rise_h, 0, 1)          # rampa causal (estilo David et al.)
biomasa = X_sinpulso + r·ΔX_pulso
activity_multiplier(t) = 1 + (pulse_activity_gain − 1)·r(t)
qprod_bio = activity_multiplier · qprod_sinpulso + r · Δqprod_pulso
```

- `r(t)` sube linealmente durante `pulse_t_rise_h` y queda en 1 (sin caída propia).
- El gain multiplica la actividad del contrafactual sin pulso; no toca `ferment_fraction` ni el pool.
- Interacción con el gate: multiplicativa. Especificidad por batch: solo vía `t_pulse` y ΔN.

**[HECHO VERIFICADO] Valores ajustados (natural):** `pulse_activity_gain = 0.25` (cota inferior, `active_bound=True`) y `pulse_t_rise_h = 64.66 h` (cerca de la cota superior 72).

**[INTERPRETACIÓN]** El llamado "nitrogen boost" terminó funcionando en natural principalmente como una **ATENUACIÓN lenta post-pulso** (×0.25 a lo largo de ~65 h): era el apagado de facto de la curva histórica, no una reactivación. La reactivación emergía solo del término `r·Δqprod_pulso`.

**[HECHO VERIFICADO] Cómo se calibró la respuesta:** perfil completo + **timing** del peak post-pulso (σ=12 h). **No existía residual de amplitud del bump** — por eso la reactivación histórica ya se reproducía imperfectamente (LAB010/011/012: dirección y timing razonables, amplitud frecuentemente corta; ver §8.1).

### 8.1 Ejemplos históricos [HECHO VERIFICADO, `prediction_rows.csv`]

| LAB | pulso (h) | CO2 antes | respuesta observada | respuesta predicha |
|---|---|---|---|---|
| LAB012 | 91.0 | 0.86 (84 h) | sube a 1.115 @102 h (peak global) | 0.62→0.58 (sin subida) |
| LAB011 | 86.8 | 0.88 (78 h) | 1.28 @87 h | 0.25→0.50 @96 h (amplitud 2.6× corta) |
| LAB010 | 102.5 | 0.28 (96 h) | 0.37 @108 h (+30 %) | 0.30→0.41 (reproduce) |

Figuras: `results/co2_matrix_cross_validation_2026/figures/nutrient_pulse_response_comparison.png`, `calibration_overlays_natural.png`, `heldout_model_comparison.png`.

### 8.2 Efecto de declarar el pulso en LAB016–018 [RESULTADO DIAGNÓSTICO]

Declarando `pulses["N"]` con dosis diferenciada (F1/F3 = 0.14 kg/m³; F2 = 0.28 kg/m³, replicando el protocolo histórico supuesto 1.0 g SFX + 0.4 g FDA), con todo lo demás congelado y **sin reajustar parámetros**:

| qCO2 @150 h (g/L/h) | valor |
|---|---|
| sin pulso | ≈ 0.27–0.28 |
| con pulso | ≈ 0.005–0.023 |
| observado | ≈ 0.01–0.03 |

La cola del holdout se corrige esencialmente por completo solo con declarar el evento. También a 120 h: pred 0.41→0.14 vs obs 0.08–0.16.

---

## 9. Dosis de nutrición: histórico y LAB016–018 (corrección pendiente)

### 9.1 Protocolo histórico codificado [HECHO VERIFICADO]

`co2_cross` :104–108: `SPRINGFERM_XTREM_G = 1.00`, `FDA_G = 0.40`, `YAN_MG_PER_MG_PRODUCT = 0.20` → 280 mg YAN en 2 L → **ΔN = 0.14 kg/m³** para los 9 naturales. Timing: cruce de densidad 1040 g/L (fallback calendario ICS "Pulso nutricional 2"). **Esta dosis era de PROTOCOLO, no una medición de N real** (`composition_source = "user-specified common LAB protocol"`). El upstream usó otra distinta: 0.08 kg/m³ del workbook (§2).

### 9.2 Nueva información del operador [HIPÓTESIS PENDIENTE DE CONFIRMACIÓN]

La nutrición de LAB016–018 habría sido aproximadamente:

- **F1 (LAB016) y F3 (LAB018):** ≈ 0.8 g SFX + 0.4 g FDA;
- **F2 (LAB017):** ≈ el DOBLE (≈ 1.6 g SFX + 0.8 g FDA).

**No presentar como dato definitivo.** Es consistente con la duración del segundo pulso de bomba de F2 (7.8 min vs ~4 min en F1/F3), pero eso no lo prueba.

### 9.3 Traducción a ΔN bajo la simplificación histórica [HECHO VERIFICADO como aritmética; condicionado a la hipótesis]

**Si** se aplica el mismo factor histórico `YAN_MG_PER_MG_PRODUCT = 0.20` a esta formulación:

```
F1/F3: 0.8 + 0.4 = 1.2 g producto → 240 mg YAN → 120 mg/L en 2 L → ΔN = 0.12 kg/m³
F2:    doble → 2.4 g producto    → 480 mg YAN → 240 mg/L en 2 L → ΔN = 0.24 kg/m³
```

**[HIPÓTESIS PENDIENTE]** Esto solo es válido si el factor 20 % corresponde realmente a esta formulación. Confirmar por separado: (i) aporte YAN de SFX; (ii) aporte YAN de FDA; (iii) masas realmente pesadas; (iv) volumen real del fermentador.

**[INTERPRETACIÓN]** La prueba diagnóstica previa usó 0.14/0.28 (protocolo supuesto 1.0+0.4); con la dosis corregida del operador los valores pasarían a 0.12/0.24 (−14 %). Dado que el contrafactual ya corrige la cola con margen, el efecto de esta corrección debería ser menor, pero debe re-evaluarse una vez confirmada la dosis.

---

## 10. Sensibilidad de `pulse_activity_gain` [RESULTADO DIAGNÓSTICO]

Prueba manual (sin fitting), con `pulse_t_rise_h` congelado ≈ 64.7 h y el pulso declarado:

- gain = 0.25, 0.50, 1.00, 1.50, 2.00.

**Resultado:** aumentar gain genera una reactivación, pero aumenta **toda** la actividad posterior y destruye la caída/cola.

**Conclusión [HECHO VERIFICADO como resultado del barrido; INTERPRETACIÓN la generalización]:** NO es adecuado solucionar el bump aumentando un gain permanente:

```
gain bajo  → buena terminación, mala reactivación
gain alto  → mejor reactivación, mala terminación
```

**[INTERPRETACIÓN]** Esto demuestra una limitación de la forma funcional histórica: un multiplicador **permanente** no puede producir un transitorio (bump de horas que se disuelve) y a la vez preservar la terminación. Ambos efectos requieren dinámicas separadas (§11, §14).

---

## 11. Prueba transitoria rise-decay [RESULTADO DIAGNÓSTICO — NO PARÁMETROS CALIBRADOS]

Prueba estructural diagnóstica añadida (forward, sin fitting):

```
qprod_transient = qprod_historical · [1 + A·B(t)]

B(t) = rise rápido × decay exponencial      (B(t) → 0 después del pulso)
```

Barrido manual: `A ∈ {0.10, 0.20, 0.30}`; `tau_rise ∈ {1, 2, 4} h`; `tau_decay ∈ {4, 8, 12} h`.

**Resultado principal:**

- `A ≈ 0.30`, `tau_rise ≈ 2 h`, `tau_decay ≈ 4 h` reprodujo en **LAB017**:
  - reactivación predicha = **35.74 %** vs observada = **35.59 %**;
  - retorno correcto a la cola histórica después del transitorio: qCO2 @150 h ≈ **0.0054 g/L/h**.

**[RESULTADO DIAGNÓSTICO — NO PARÁMETROS CALIBRADOS]** Estos valores son exclusivamente diagnósticos: provienen de un barrido manual sobre un solo experimento, sin función objetivo ni incertidumbre. La forma rise-decay es, por ahora, **la principal hipótesis estructural** apoyada por el diagnóstico (§14), no un modelo definitivo.

---

## 12. Limitación de la respuesta transitoria universal [RESULTADO DIAGNÓSTICO]

Aplicando el **mismo** escenario transitorio (A≈0.30, τ_rise≈2 h, τ_decay≈4 h) a los tres fermentadores:

| LAB | reactivación predicha |
|---|---|
| LAB016 | ≈ 15.4 % |
| LAB017 | ≈ 35.7 % |
| LAB018 | ≈ 13.9 % |

**Conclusión:** reproduce muy bien amplitud, timing y cola de F2, pero **NO explica** por qué F1/F3 muestran una respuesta mucho menor. Un multiplicador transitorio universal y lineal con dosis es todavía insuficiente.

Posibles explicaciones **a INVESTIGAR, no afirmar** [HIPÓTESIS PENDIENTE]:

- dosis real diferente (hipótesis del operador: F1/F3 normales, F2 doble);
- composición real diferente (proporciones SFX/FDA distintas);
- respuesta no lineal a dosis;
- estado fisiológico diferente al momento del pulso (X, N residual, E, azúcar disponible);
- dependencia de N residual al pulso;
- dependencia de X;
- disponibilidad de azúcar;
- heterogeneidad experimental;
- diferencias en mezcla/aplicación.

**[INTERPRETACIÓN]** Con la dosis hipotetizada del operador, el contraste F2 vs F1/F3 (2× dosis → ~2.3× respuesta) es la primera evidencia de dose-response del pipeline; confirmar la dosis es el paso que convierte esta observación en dato.

---

## 13. Diferencias respecto a la calibración histórica

| Aspecto | Calibración histórica | Hallazgo actual | Cambio potencial |
|---|---|---|---|
| Onset | chemical bracket offline (química futura) | el bracket no es causal; re-posicionarlo corrige 77–86 % del RMSE | mecanismo causal/predictivo de activación (obligatorio antes del estimador) |
| Release | continuous release | mantiene onset/correlación; no genera lag; τ≤20 h; no causa la cola | mantener por ahora |
| Nutrición | salto N + rampa lenta (64.7 h) + gain permanente (0.25) | la respuesta real ocurre en horas y retorna; la rampa lenta+gain mezcla reactivación con terminación | separar respuesta rápida transitoria de terminación lenta |
| Termination | azúcar/E + atenuación post-pulso gain=0.25 | sin pulso, terminación biológica débil (qprod 33–66 % del peak a 100–150 h) | dar fundamento biológico independiente del pulso (revisar β(N), muerte/E) |
| N | afecta solo μ | N no frena la fermentación en el modelo aunque N=0 desde temprano | evaluar dependencia de β con N/estado metabólico |
| Muerte | prácticamente inerte (kd=0 a 16–22 °C) | Xd sin señal en LAB016–018; nuevos Oculyze X/Xd disponibles | revisar con los nuevos X/Xd Oculyze (LAB013–018) |
| Pulse response | rise ≈ 64.7 h (casi cota superior) | bump observado en pocas horas (~6 h hasta el máximo en LAB017) | transitorio rise-decay (τ_rise ≈ 2 h, τ_decay ≈ 4 h como referencia diagnóstica) |
| Amplitud del bump | sin residual propio (solo timing) | amplitud históricamente corta; transitorio la reproduce en F2 | añadir observable/residual de amplitud post-pulso en la próxima calibración |

---

## 14. Propuesta de arquitectura a evaluar (NO implementar todavía)

```
UPSTREAM
  ↓
chemical/metabolic activation        (causal, no bracket a posteriori)
  ↓
qprod_base
  ↓
evento nutricional conocido (input trazable: t_pulso, ΔN, composición)
  ├─ salto real de N en el estado
  ├─ respuesta metabólica rápida transitoria   (escala ~2–8 h; p. ej. rise-decay)
  └─ dinámica lenta de terminación             (escala decenas de horas)
  ↓
CO2 dissolved
  ↓
continuous release
  ↓
qgas
```

**[INTERPRETACIÓN]** Probablemente necesitamos separar:

- **A) respuesta rápida post-nutrición:** escala ~2–8 h (bump observable);
- **B) terminación:** escala decenas de horas.

y evitar que un solo `pulse_activity_gain` intente representar ambas (el barrido de §10 muestra el trade-off; el transitorio de §11 muestra que la separación funciona en F2). La forma rise-decay es la principal hipótesis estructural, pendiente de: confirmación de dosis, evaluación en F1/F3 (§12) y calibración formal con residual de amplitud.

---

## 15. Defectos estructurales identificados

| # | Defecto | Clasificación |
|---|---|---|
| 1 | onset depende de química offline (futura) para el bracket; no causal | estructural + datos |
| 2 | terminación upstream débil (qprod 33–66 % del peak a 100–150 h sin pulso) | estructural |
| 3 | N no limita directamente βG/βF (solo μ) | estructural (decisión de modelación) |
| 4 | muerte celular prácticamente inactiva (kd=0 a 16–22 °C) | estructural |
| 5 | fructosa residual mantiene qprod >100 h | estructural |
| 6 | apagado histórico dependía del término post-pulso gain=0.25 | parametrización |
| 7 | gain=0.25 en cota inferior (no identificado) | parametrización |
| 8 | pulse_t_rise_h≈64.7 h cerca de cota superior | parametrización |
| 9 | reactivación rápida (~6 h) no representable con rampa de 65 h | estructural (forma funcional) |
| 10 | un gain permanente no puede dar bump + buena cola simultáneamente (§10) | estructural (forma funcional) |
| 11 | respuesta transitoria universal no explica el contraste F1/F3 vs F2 (§12) | datos + estructural |
| 12 | cola histórica sobrepredicha (mediana 2.2×) | datos + parametrización |
| 13 | censura LOD reducía el peso de la cola (39 % en t>100 h) | metodología de ajuste |
| 14 | matrix_gain absorbe sesgos de amplitud | parametrización |
| 15 | microleaks posibles en CO2 histórico LAB013–015 | incertidumbre experimental [HIPÓTESIS PENDIENTE] |
| 16 | LAB016–018 sin química temporal completa (ICs heredadas) | datos |

---

## 16. Inventario actual LAB013–LAB018

### 16.1 LAB013–015 (triplicado, SP 16 °C)

**[HECHO VERIFICADO]**
- Química Y15: G, F, YAN (+ amonio/PAN), Gly — 7 muestras dinámicas + 1 pre-inóculo por LAB (`Y15_LAB013-015.csv`).
- Biomasa Oculyze: **9 muestras por LAB** (1, 2, 4–10), 10 imágenes/muestra; t0 proxy = muestra-1: 0 / 2.5 / 7 / 23 / 29 / 47.5 / 53 / 71.5 / 143.5 h. X 0.17–2.11 kg/m³, Xd 0.002–0.184.
- Brix/densidad/DO/CO2 disuelto en 10 muestras.
- CO2 gaseoso **no confiable** (documentado; nunca usado para estimación; hipótesis microleak §23 del notebook).
- t0 definitivo pendiente (`time_h` vacío en el CSV offline).

### 16.2 LAB016–018 (SP 20 °C, Sauvignon Blanc)

**[HECHO VERIFICADO]**
- CO2 gaseoso confiable (máscara de artefactos auditada, 2.5–3.6 %).
- Temperatura medida (input del modelo); Brix/densidad en 8 muestras.
- Biomasa Oculyze en **8.9, 10.9 y 56.2 h** (X 0.17–1.74 kg/m³; X@8.9 h = 0.27–0.43 vs fallback X0=0.45).
- ICs químicas heredadas (G0 74.05, F0 77.73, YAN0 244.33 mg/L, Gly0 1.14; `CondicionesIniciales`).
- t0 inequívoco: fin del pulso de inoculación del log `nutricion_activa` (2026-09-01 00:03:55 / 00:04:00 / 00:04:07).
- Evento(s) de nutrición ~56.9 h: LAB016 y LAB018 un pulso (3.8/4.1 min); **LAB017 dos pulsos** (4.0 y 7.8 min).
- **Dosis probable [HIPÓTESIS PENDIENTE]:** F1/F3 ≈ 0.8 g SFX + 0.4 g FDA; F2 ≈ doble (§9).

### 16.3 Semántica de muestras [HECHO VERIFICADO]

- El número 3 de LAB013–015 fue saltado en Oculyze (la muestra 3 existe offline); no es muestra faltante.
- El segundo `LAB015-1` del report corresponde a **LAB015-2** (match exacto por Density/Temperature).
- Cronología: usar `hora_muestreo` del offline (o el ledger del log para t0). `Description` de Oculyze NO es fuente temporal confiable (typos, desfases 30–120 min).

---

## 17. Qué hace falta para recalibrar (priorizado)

**IMPRESCINDIBLE:**
1. Tiempo exacto de inoculación (t0).
2. Tiempo exacto de nutrición.
3. Masa exacta SFX/FDA por fermentador.
4. Composición/YAN real de ambos productos (¿20 % aplica a ambos?).
5. G/F temporal (Y15) — bracket, terminación, β.
6. YAN temporal — qN, sN, validación de ΔN.
7. Biomasa viable/total (Oculyze) — μ, escala, X0.
8. CO2 gaseoso confiable.
9. Temperatura.

**MUY DESEABLE:**
10. Etanol (iE, balance C) — **no necesita medirse en todos los puntos si el Alcolyzer no está disponible** (§19).
11. Glicerol (γ; viene gratis con Y15).
12. Xd/viabilidad (único canal de muerte).

Qué informa cada medición: G/F → β, kG/kF, iG, iE, terminación; YAN → qN, sN, μ, ΔN; X → μ, escala, X0; Xd → Kd0 (hoy sin señal); E → iE, β, balance C; Gly → γ; CO2 → capa de observación completa; T → Arrhenius (input conocido).

---

## 18. Diseño de 1–2 fermentaciones nuevas

Objetivos de identificación: **onset** (0–36 h denso), **respuesta a nutrición** (ventana −1 a +24 h alrededor del pulso), **terminación** (cola >96 h). Ya disponemos de un contraste preliminar de dosis (F1/F3 normales, F2 doble, pendiente de confirmar).

### 18.1 Decisión estructural: ¿control sin nutrición + dosis conocida, o dosis normal + dosis doble?

**Recomendación [INTERPRETACIÓN]: control SIN nutrición + fermentación con nutrición de dosis conocida.** Justificación:

- El contraste de dosis ya existe (parcialmente) en LAB016–018 una vez confirmada la hipótesis del operador; repetirlo aporta poca información estructural nueva.
- Lo que **no existe en todo el dataset** es una observación de terminación **sin** el artefacto del pulso: el control sin nutrición es el único diseño que aísla la terminación biológica (el mecanismo más débil, §6) y permite decidir si necesita fundamento propio.
- La fermentación con dosis conocida y muestreo denso post-pulso ancla amplitud/timing/τ del transitorio con input trazable, y contrasta contra F2 (dosis doble) para dose-response.
- Alternativa "dosis normal + dosis doble": útil solo si la confirmación del operador fracasara y el contraste de dosis tuviera que reconstruirse; secundaria en prioridad.

### 18.2 Alternativa A — una sola fermentación

Con nutrición de dosis confirmada, muestreo denso en onset y ventana post-pulso; la terminación queda cubierta por los puntos tardíos (menos densidad que en B).

### 18.3 Alternativa B — dos fermentaciones (recomendado)

F-A: control **sin** nutrición. F-B: nutrición con dosis exacta pesada y registrada. Mismo mosto, misma cepa, SP 20 °C. La nutrición de F-B se aplica en el mismo estado de densidad (~1040 g/L) que el protocolo histórico.

### 18.4 Calendario de muestreo (por fermentador; nutrición solo en F-B)

| # | Instante | G/F (Y15) | YAN | Oculyze | Brix | Densidad | E | Gly |
|---|---|---|---|---|---|---|---|---|
| 0 | PI (pre-inoculación) | sí | sí | — | sí | sí | externo | sí |
| 1 | 0 h post-inoculación | — | — | sí | sí | sí | — | — |
| 2 | 6–8 h | sí | sí | sí | sí | sí | — | sí |
| 3 | 12 h | sí | sí | — | sí | sí | — | sí |
| 4 | 24 h | sí | sí | sí | sí | sí | — | sí |
| 5 | 36 h | sí | sí | sí | sí | sí | — | sí |
| 6 | 48 h | sí | sí | — | sí | sí | — | sí |
| 7 | −1 h antes de nutrición | sí | sí | sí | sí | sí | externo | sí |
| 8 | +2 h post-nutrición | sí | sí | — | sí | sí | — | sí |
| 9 | +4–6 h post-nutrición | sí | sí | sí | sí | sí | — | sí |
| 10 | +12 h post-nutrición | sí | sí | — | sí | sí | — | sí |
| 11 | +24 h post-nutrición | sí | sí | sí | sí | sí | externo | sí |
| 12 | 96 h (o +48 h post-pulso) | sí | — | sí | sí | sí | — | sí |
| 13 | final (declinación clara) | sí | sí | sí | sí | sí | externo | sí |

- **Plan mínimo:** puntos 0, 1, 2, 4, 5, 7, 8, 9, 11, 13 (10 por fermentador).
- **Plan recomendado:** los 14 (solo en F-B; en F-A, el bloque 7–11 se sustituye por un punto a la hora nominal del pulso +24 h).
- Con nutrición ~56 h, los puntos 8–12 caen en 58–104 h absolutas.
- Metadata obligatoria: producto/gramos/volumen/hora exactos de la nutrición, log `nutricion_activa` para t0, y réplicas Oculyze (≥2 preparaciones) en los puntos 1, 4, 7 y 11 para estimar R.

---

## 19. Estrategia etanol / Alcolyzer

El Alcolyzer no está disponible en el laboratorio. Pocas muestras estratégicas al servicio externo:

1. PI (E0 real — el histórico fue 9.2–11.8 g/L, no cero);
2. pre-nutrición (E al pulso: estado fisiológico + inhibición en el bump);
3. +8–12 h post-nutrición (E durante el máximo de reactivación);
4. fase tardía/final (ancla de iE en la terminación y balance C).

**¿Se pueden reducir aún más? [INTERPRETACIÓN]** A 3 muestras (eliminando la #3): se pierde la E en el máximo del bump — el punto que mejor informaría si la reactivación depende del estado de E; el resto de la información (G/F/YAN/X en ese instante) se mantiene. A 2 (PI + final): se pierde el ancla de E en el pulso y la terminación queda mal condicionada para iE. **Recomendación: mantener 4; aceptar 3 como mínimo.** El resto del perfil de E queda inferido por el balance CO2 (44 g CO2 por 46 g etanol) con la incertidumbre correspondiente.

---

## 20. Preguntas prioritarias para el colega que hizo la calibración

**Prioridad máxima (bloquean dosis/pulso y transitorio):**

1. ¿Cuál fue exactamente la formulación y masa de SFX/FDA en LAB004–LAB012?
2. ¿De dónde sale el supuesto 20 % de YAN?
3. ¿Ese 20 % aplica a ambos productos?
4. ¿Cuál fue exactamente la dosis de LAB016–LAB018?
5. ¿F2 recibió efectivamente el doble?
6. ¿Cuál era la interpretación física esperada de `pulse_activity_gain`?
7. ¿Por qué terminó en 0.25, cota inferior?
8. ¿Qué representaba físicamente `pulse_t_rise_h`?
9. ¿Por qué quedó en ~64.7 h si las respuestas observadas pueden ocurrir en pocas horas?
10. ¿El mecanismo post-pulso pretendía representar reactivación, terminación o ambas?
11. ¿Era conocida la sobrepredicción histórica de la cola?
12. ¿Por qué N no aparece directamente en beta_G/beta_F?
13. ¿Se contempló alguna variable de actividad metabólica?
14. ¿De dónde sale 30 pg/célula?
15. ¿Cómo definiría un t0 físicamente correcto para el modelo?

**Secundarias:**

16. ¿Por qué se eligieron Δ(G+F)=5 g/L y ΔE=2 g/L como umbrales del bracket? ¿Sensibilidad?
17. ¿Era consciente de que el gate químico necesitaba química futura (no causal)?
18. ¿`matrix_gain` (3.12) se interpreta físicamente o es escala empírica?
19. ¿Se sospechaban microleaks en los datos históricos de CO2?
20. ¿Por qué el upstream usó ΔN=0.08 kg/m³ del workbook y la capa CO2 0.14 kg/m³ del protocolo?
21. ¿Por qué LAB012 se consideró holdout de la capa CO2 si participó en θ_natural?
22. ¿El O2 de la capa (qmax en cota inferior 0.15) tiene interpretación física?
23. ¿Qué problemas del modelo sabía que quedaban abiertos?

---

## 21. Readiness para el estimador de estado (EKF/UKF/MHE)

### 21.1 Checklist

| Ítem | Estado | Notas |
|---|---|---|
| Modelo dinámico final | **parcial** | decidir arquitectura post-nutrición y terminación (§14) antes de congelar |
| Estados (7) | **sí** | X, Xd, N, G, F, E, Gly |
| Inputs conocidos | **sí** | T medida; pulsos N |
| Nutriciones como inputs | **parcial** | dosis LAB016–018 pendiente de confirmar (§9); trazabilidad exigida en fermentaciones nuevas |
| Observation functions | **parcial** | CO2 (capa completa), X/Xd Oculyze (×0.03), YAN→N, Y15→G/F/Gly; Brix/densidad sin función validada |
| Unidades consistentes | **sí, con cuidado** | kg/m³ vs g/L; Mcél/mL×0.03; SCCM→g/L/h oficial (24.16 L/mol, 44.0095 g/mol, 2 L, 0.74) |
| t0 inequívoco | **sí** (LAB016–018) | fin de inoculación del log; LAB013–015 pendiente |
| Inicialización | **parcial** | PI + 0 h dan X0/N0/G0/F0/E0 reales en el plan nuevo |
| Q (proceso) | **falta** | de residuos de recalibración |
| R (medición) | **parcial** | pisos/rel históricos como punto de partida |
| Ruido real Oculyze | **falta** | sin réplicas por muestra (10 imágenes = réplicas técnicas agregadas) |
| Ruido química Y15 | **parcial** | de triplicados LAB013–015 |
| Máscara CO2 event-aware | **sí** | Hampel + ventanas auditadas |
| Latencia causal del filtro | **parcial** | pipeline actual batch |
| Periodos inválidos | **sí (diseño)** | mask/NaN-aware ya existe |
| Observabilidad | **falta análisis formal** | Xd probablemente no observable (kd≈0) |
| Parámetros fijos | **sí** | tras recalibración sin cotas injustificadas |
| Parámetros aumentados | diseño | E0/bias-E, X0, eficiencia-N del pulso, parámetros del transitorio (A, τ_rise, τ_decay), drift de gain |
| Validación externa previa | **falta** | holdout end-to-end |

### 21.2 BLOQUEANTES antes de implementar un EKF/MHE serio

1. **mecanismo causal de onset** — el chemical bracket histórico usa química futura y **NO puede utilizarse directamente en tiempo real** (§4); necesario un predictor causal (proxy online: densidad/Brix/CO2 temprano) o un estado dinámico de activación;
2. inputs de nutrición conocidos y trazables (dosis/tiempo confirmados);
3. decidir arquitectura post-nutrición (transitorio separado de terminación, §14);
4. terminación razonablemente representada (control sin pulso §18);
5. observation functions validadas;
6. condiciones iniciales robustas (PI + 0 h);
7. ruido Q/R con base en datos (réplicas);
8. manejo event-aware de artefactos CO2 (existe; portar a causal);
9. validar con al menos un experimento no usado en la recalibración.

### 21.3 Estado adicional de actividad (consideración, NO implementar)

**[INTERPRETACIÓN]** Si se añade un estado de **actividad fermentativa/metabólica** (p. ej. `a(t)` que sigue lag → 1 → bump post-pulso → decaimiento), se podrían representar de manera causal lag + reactivación + decay dentro del filtro, en lugar de forzarlo con el gate no causal y el gain permanente. Evaluar identifiabilidad y costo antes de decidir (§14).

---

## 22. Decisiones antes de recalibrar

| Decisión | Evidencia actual | Dato que falta | Riesgo de cambiarlo ahora | Recomendación |
|---|---|---|---|---|
| Chemical activation (forma) | gate corrige onset (RMSE −77–86 %) pero necesita bracket químico | G/F 6–36 h (plan §18) | bajo | **mantener la forma**; hacer el bracket medible/causal |
| `pulse_activity_gain` | 0.25 en cota; apagado de facto; barrido: gain alto destruye la cola (§10) | amplitud del bump + cola con dosis confirmada | alto (reaparece cola) | **re-emplazar por transitorio + terminación**; no congelar en 0.25 |
| `pulse_t_rise_h` | 64.7 h casi cota sup.; bump real en ~6 h | ventana densa 2–12 h post-nutrición | medio | re-estimar; rise corto + decay (τ≈2/4 h como referencia diagnóstica) |
| Respuesta transitoria rise-decay | reproduce F2 (35.7 % vs 35.6 %) y cola; no explica F1/F3 (§12) | dosis confirmada; réplicas del pulso | medio (universalidad) | **candidata principal**; calibrar con residual de amplitud |
| β dependiente de N | N solo afecta μ | YAN pre/post pulso + G/F en el bump | medio | evaluar β(N) |
| Muerte celular | kd inerte; Xd≈0 | Xd con señal real (Oculyze LAB013–018) | medio | mantener; revisar con Xd nuevo |
| matrix_gain | escala empírica | calibración SCCM→g/L/h | medio | mantener; monitorear |
| E0 | histórico 9.2–11.8; sin medir en LAB016–018 | E en PI | bajo | medir E en PI |
| X0/Xd0 | fallback 0.45/0; Oculyze 8.9 h ≈ 0.27–0.43 | muestra 0 h | bajo | medir reales |
| CI químicas LAB016–018 | heredadas | Y15 PI + 0 h | bajo | medir directas |
| Nutriciones (declaración) | contrafactual con 0.14/0.28 corrige la cola (150 h: 0.005–0.023 vs obs 0.01–0.03) | dosis real (0.12/0.24 bajo hipótesis operador) | alto sin declarar | **declarar pulso** con dosis confirmada + sensibilidad ±2× |
| Continuous release | nominal; τ≤20 h; no causa cola | — | bajo | **mantener** |

---

## 23. Roadmap actualizado

| # | Etapa | Criterio de salida |
|---|---|---|
| 1 | Confirmar metadata/dosis con el colega (§20, preguntas 1–5, 14, 15) | dosis SFX/FDA + factor YAN + t0 documentados por escrito |
| 2 | Corregir inputs LAB016–018 (ΔN por fermentador; re-ejecutar contrafactual con 0.12/0.24) | cola del holdout corregida con la dosis confirmada; desviación documentada |
| 3 | Cerrar dataset Oculyze/química LAB013–018 (mapeo LAB015-2, t0, réplicas) | dataset único versionado, sin ambigüedades de identidad/tiempo |
| 4 | Realizar 1–2 fermentaciones informativas (§18: control + dosis conocida) | perfiles G/F/YAN/X/Xd/E con calendario cumplido y metadata de pulso completa |
| 5 | Seleccionar arquitectura mínima (§14: transitorio vs alternativas; actividad como estado) | lista cerrada de cambios estructurales, con criterios de rechazo |
| 6 | Recalibrar upstream si corresponde (θ_natural con datos nuevos) | sin cotas activas injustificadas; X/Xd/G/F/YAN con residuos aceptables |
| 7 | Recalibrar capa CO2/pulso (transitorio + terminación; residual de amplitud post-pulso) | cola y bump reproducidos en calibración; parámetros dentro de cotas con margen |
| 8 | Holdout externo (1 fermentación no usada) | métricas end-to-end (onset, peak, cola, reactivación) dentro de tolerancias pre-declaradas |
| 9 | Congelar modelo | versión etiquetada (θ + capa + eventos), hashes y changelog |
| 10 | Comenzar estimador de estado (§21 bloqueantes resueltos) | filtro causal validado contra el holdout de la etapa 8 |

---

## 24. Resumen ejecutivo

**Cómo funciona hoy el modelo [HECHO VERIFICADO].** ODE de 7 estados (X, Xd, N, G, F, E, Gly) con temperatura exógena y pulsos exactos; CO2 biológico `0.4777·(βG+βF)·X`, filtrado por un gate de encendido anclado a química (`_bounded_smoothstep_activation`), una respuesta post-pulso (rampa `r(t)` + gain permanente, `effective_qprod_grid`), un pool disuelto con solubilidad Csat(T,E,G,F) y liberación continua, escalado por `matrix_gain` = 3.12.

**Qué aprendimos [HECHO VERIFICADO / RESULTADO DIAGNÓSTICO].** (i) El gate químico es solo onset y explica la mayor parte del error LAB016–018 sin química (RMSE −77–86 % al re-posicionarlo). (ii) En natural, el "nitrogen boost" ajustó gain=0.25 (cota inferior) y rise=64.7 h: una atenuación lenta que hacía de apagado de facto. (iii) La terminación biológica es débil (kd inerte, N no limita β, fructosa sostiene qprod al 33–66 % del peak a 100–150 h); la cola no es del pool (τ≤20 h). (iv) Declarar el pulso con dosis de protocolo corrige la cola sin reajustar nada (150 h: 0.27–0.28 → 0.005–0.023 vs obs 0.01–0.03 g/L/h). (v) Un gain permanente no puede dar bump y buena cola a la vez; el transitorio rise-decay (A≈0.30, τ_rise≈2 h, τ_decay≈4 h) reproduce el bump de LAB017 (35.7 % vs 35.6 %) y retorna a la cola correcta — pero no explica el contraste F1/F3 (~14–15 %). (vi) La dosis de LAB016–018 probablemente fue 0.8+0.4 g (F1/F3) y doble (F2) → ΔN = 0.12/0.24 kg/m³ bajo el factor 20 % — [HIPÓTESIS PENDIENTE].

**Conclusión central:** *La calibración histórica utilizaba mecanismos data-assisted y una única dinámica post-pulso lenta que servía simultáneamente para respuesta a nutrición y terminación. Los nuevos experimentos muestran que lag, reactivación rápida y terminación ocurren en escalas temporales distintas y probablemente deben representarse mediante mecanismos separados.*

**Qué está funcionando [HECHO VERIFICADO].** Peak principal (tiempo/amplitud) y ascenso tras el gate condicionado; cadena de unidades verificada; t0 de LAB016–018 inequívoco; máscara de artefactos CO2 auditada; contrafactual de pulso corrigiendo la cola.

**Qué está fallando [HECHO VERIFICADO / INTERPRETACIÓN].** Onset no predictivo sin química (y no causal por diseño); terminación dependiente del artefacto del pulso; bump no representable con rampa de 65 h ni con gain permanente; transitorio universal insuficiente para F1/F3; gain y rise en cotas; microleaks [HIPÓTESIS PENDIENTE] en CO2 de LAB013–015.

**Qué datos faltan.** Confirmación de dosis/composición YAN; G/F/YAN/X/Xd/E/Gly temporales en fermentaciones nuevas; réplicas Oculyze para R; E0/X0 medidos; control sin nutrición para aislar la terminación.

**Qué medir en las próximas fermentaciones.** §18: control + dosis conocida; calendario denso en 0–36 h (onset) y −1/+2/+4–6/+12/+24 h alrededor del pulso; etanol externo solo en PI, pre-nutrición, +8–12 h post y final (§19).

**Qué preguntar al colega.** Las 15 preguntas de prioridad máxima de §20 (formulación/masas SFX-FDA, factor 20 %, dosis real LAB016–018, significado físico del gain y del rise, cola conocida, β sin N, actividad metabólica, 30 pg/célula, t0 físico).

**Qué debe quedar resuelto antes del estimador.** Los 9 bloqueantes de §21.2: mecanismo causal de onset, inputs de nutrición trazables, arquitectura post-nutrición decidida, terminación representada, observation functions validadas, ICs robustas, Q/R con datos, manejo event-aware causal de artefactos, y validación con un experimento no usado en la recalibración. Considerar un estado de actividad metabólica si permite representar causalmente lag + reactivación + decay (§21.3). Con kd≈0, Xd es probablemente no observable: proyectar el filtro sobre {X, N, G, F, E, Gly} + CO2.

---

*Documento v2 generado por auditoría y diagnósticos de solo lectura (2026-09-08). No se modificaron modelos, notebooks, datos ni resultados. Únicos archivos mantenidos: este `.md` y su equivalente `.tex`.*
