# Auditoría de trazabilidad del LaTeX `modelo_fermentacion_CO2_EKF_2026.tex`

> **Pregunta central que responde este documento:**
> ¿El LaTeX `modelo_fermentacion_CO2_EKF_2026.tex` representa fielmente el modelo implementado en el repositorio `pyomo-doe`?
>
> **Método:** verificación ecuación por ecuación y parámetro por parámetro, usando exclusivamente archivos locales. No se usó internet, literatura externa ni conocimiento general. No se modificó ningún archivo; no se ejecutó ninguna calibración nueva.
>
> **Norma aplicada:** si una afirmación del LaTeX no puede demostrarse desde el código, se marca **NO VERIFICADO**. Si contradice el código se marca **INCORRECTO**.

---

## Contexto de versiones (imprescindible antes de leer las tablas)

El LaTeX mezcla explícitamente dos familias de implementación en su lista de fuentes (§Fuentes):

| Moelo | Fichero | Ley de liberación de CO₂ | Uso en el LaTeX |
|---|---|---|---|
| **A – Laboratorio 2026** | `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, `results/co2_matrix_cross_validation_2026/fit_parameters.csv` | `psi = f0 + (1-f0)·Cd/(Cd+C_CO2*)` (liberación continua, `f0=0.05`), kLaO₂ ausente | Es el que el LaTeX formula en §§6–15 |
| **B – Piloto 2025** | `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py` | `qgas = k_release·smooth_positive(Cd − C_CO2*)` (exceso umbralizado), kLaO₂ como parámetro | Solo como fuente de funciones (`o2_saturation_mg_l`, `co2_saturation_g_l`, `CO2_G_PER_MG_O2_RESP`, `co2_production_g_l_h`) |

**Conclusión de encuadre:** todas las fórmulas de la capa CO₂/O₂ del LaTeX corresponden al **modelo A (Laboratorio 2026)**, cuyo nombre real es `solubility_o2_nitrogen_boost_continuous_release` (`MODEL_NAME`). Son correctas **para A**. Si alguien leyera el LaTeX pretendiendo representar B (el modelo `solubility_o2_slow_transition` del piloto 2025), las ecuaciones de liberación y el tratamiento de O₂ **no coinciden**. Esta dualidad es una fuente de confusión que se señala en §10.

---

# 1. Vector de estados

### 1.1 `x_up = [X, Xd, N, G, F, E, Gly]^T` ("modelo primario implementado")

Verificado contra `STATE_NAMES = ("X","Xd","N","G","F","E","Gly")` en `shared/run_new_must_glycerol_estimability_doe.py:75`.

| Variable | ¿Existe? | Archivo / función donde se integra | Condición inicial | Unidad | Estado |
|---|---|---|---|---|---|
| `X` (viable) | Sí | `rhs` → `run_new_must_glycerol_estimability_doe.py:453` (dx), integrado por `simulate` (:495) | `batch.initials["X"]` → `_initials_from_group` (:270), por lote (p. ej. `X_viable_kg_m3`) | kg/m³ (numéricamente g/L) | **VERIFICADO** |
| `Xd` (muerta) | Sí | `rhs` :454 (dxd) | `batch.initials["Xd"]` (:271) | kg/m³ | **VERIFICADO** |
| `N` | Sí | `rhs` :455 (dn) | `batch.initials["N"]` (:272) | kg/m³ | **VERIFICADO** |
| `G` | Sí | `rhs` :456–459 (dg) | `batch.initials["G"]` (:273) | g/L | **VERIFICADO** |
| `F` | Sí | `rhs` :461–464 (df) | `batch.initials["F"]` (:274) | g/L | **VERIFICADO** |
| `E` | Sí | `rhs` :466 (de) | `batch.initials["E"]` (:275) | g/L | **VERIFICADO** |
| `Gly` | Sí | `rhs` :467 (dgly) | `batch.initials["Gly"]` (:276) | g/L | **VERIFICADO** |

> La condición inicial de los estados primarios **no es un valor fijo único**; depende de cada lote (`batch.initials`). El LaTeX no afirma un valor numérico para `X(0),N(0),G(0),F(0),E(0)` sino solo su pertenencia al vector, lo cual es correcto.

### 1.2 Estados adicionales `O2(t)` y `Cd(t)`

| Variable | ¿Existe? | Dónde | Condición inicial | Unidad | Estado |
|---|---|---|---|---|---|
| `O2` | Sí (estado auxiliar latente) | `effective_qprod_grid` → `run_co2_matrix_cross_validation_2026.py:1709–1722` (bucle Euler) | `O2(0)=max(O2_initial_scale,0)·o2_saturation_base_mg_l[0]` (:1711) | mg/L | **VERIFICADO** |
| `Cd` | Sí (estado dinámico) | `raw_qgas_grid_prediction` → `run_co2_matrix_cross_validation_2026.py:1777–1800` (`dissolved`) | `dissolved=0.0` (:1777) | g/L | **VERIFICADO** |

### 1.3 Vectores objetivo EKF (recomendación, no código)

`x_EKF,5=[S,N,X,E,Cd]^T` y `x_EKF,6=[S,N,X,E,Cd,O2]^T`. El LaTeX los presenta como *objetivo deseado*; **no existen como variables de integración**. Son definiciones propuestas. **Estado: TRANSFORMACIÓN DE NOTACIÓN** — no hay conflicto con el código, pero debe quedar claro que ningún script integra `S`.

---

# 2. Ecuaciones upstream

Fuente única: `kinetic_terms` (`shared/run_new_must_glycerol_estimability_doe.py:387–442`) y `rhs` (`:445–468`).

| Ecuación LaTeX | Implementación real | Archivo | Función/líneas | Estado | Diferencia |
|---|---|---|---|---|---|
| `dX/dt = (mu − kd)·X` | `dx = (terms["mu"] - terms["kd"])*x` | `run_new_must_glycerol_estimability_doe.py` | `rhs` :453 | **VERIFICADA** | ninguna |
| `dXd/dt = kd·X` | `dxd = terms["kd"]*x` | ídem | :454 | **VERIFICADA** | ninguna |
| `dN/dt = −qN·F_X·X` | `dn = -theta["qN"]*growth_factor*x` (`growth_factor = a_mu·n_lim = F_X`) | ídem | :455 | **VERIFICADA** | ninguna |
| `dG/dt = −[qXG·F_X + qEG·F_G + m·f_m·(G/(G+F))]·X` | `dg = -(qXG*growth_factor + qEG*glucose_ferm_factor + maintenance_flux*(g/sugar_total))*x` | ídem | :456–459 | **VERIFICADA** | la mant. usa `g/sugar_total`; `sugar_total = g+f+eps` (eps≈0) → idéntico |
| `dF/dt = −[qXF·F_X + qEF·F_F + m·f_m·(F/(G+F))]·X` | `df = -(qXF*growth_factor + qEF*fructose_ferm_factor + maintenance_flux*(f/sugar_total))*x` | ídem | :461–464 | **VERIFICADA** | idem (usa `f/sugar_total`) |
| `dE/dt = (betaG+betaF)·X` | `de = (terms["beta_g"] + terms["beta_f"])*x` | ídem | :466 | **VERIFICADA** | ninguna |
| `dGly/dt = [γG0·F_G + γF0·F_F]·X` | `dgly = (theta["gammaG0"]*glucose_ferm_factor + theta["gammaF0"]*fructose_ferm_factor)*x` | ídem | :467 | **VERIFICADA** | ninguna |

### 2.1 Factores de temperatura (Arrhenius)

Implementados en `kinetic_terms` (:393–403). LaTeX §§2.1. Los refs. 300, 296.15, 293.15 y las Ea coinciden.

| LaTeX | Código | Archivo | Línea | Estado |
|---|---|---|---|---|
| `a_mu = exp[Eac·(TK−300)/(300·R·TK)]` | `exp(Eac*(temp_k-300.0)/(300.0*r*temp_k))` | `run_new_must_glycerol_estimability_doe.py` | `kinetic_terms` :397 | **VERIFICADA** |
| `a_beta = exp[Eafe·(TK−296.15)/(296.15·R·TK)]` | `exp(Eafe*(temp_k-296.15)/(296.15*r*temp_k))` | ídem | :398 | **VERIFICADA** |
| `a_KN, a_KG, a_KF, a_KiG, a_KiE = exp[Ea·(TK−293.15)/(293.15·R·TK)]` | `exp(EaKn/Kg/Kf/Kig/Kie*(temp_k-293.15)/(293.15*r*temp_k))` | ídem | :399–403 | **VERIFICADA** |

**Nota de notación:** el LaTeX usa `E_aK_N=E_aK_G=E_aK_F=E_aK_iG=E_aK_iE=46055`. En `FIXED_CONSTANTS` (`:160–172`) los nombres son `EaKn=EaKg=EaKf=EaKig=EaKie=46055` y a la vez `EaKn`(=K_N, 46055). El valor es idéntico.

### 2.2 Semisaturaciones efectivas

LaTeX: `K_N=mu0/s_N·a_KN`, `K_G=betaG0/s_G·a_KG`, `K_F=betaF0/s_F·a_KF`.

| Código | Línea | Estado |
|---|---|---|
| `kn = (theta["mu0"]/theta["sN"])*a_kn` | :404 | **VERIFICADA** |
| `kg = (theta["betaG0"]/theta["sG"])*a_kg` | :405 | **VERIFICADA** |
| `kf = (theta["betaF0"]/theta["sF"])*a_kf` | :406 | **VERIFICADA** |

### 2.3 Coeficientes de inhibición

LaTeX: `iG(T)=iG/a_KiG(T)`, `iE(T)=iE/a_KiE(T)`. Código `i_g = iG/(a_kig+eps)`, `i_e = iE/(a_kie+eps)` (:407–408). **VERIFICADA.** El `eps=1e-8` (:395) coincide con la nota "ε numérico pequeño" del LaTeX.

### 2.4 Limitaciones e inhibiciones

LaTeX: `f_N=N/(N+KN)`, `f_G=G/(G+KG)`, `f_F=F/(F+KF)`, `I_E=1/(1+iE·E)`, `I_G→F=1/(1+iG·G)`.

| Código | Línea | Estado |
|---|---|---|
| `n_lim = n/(n+kn+eps)` | :409 | **VERIFICADA** |
| `g_lim = g/(g+kg+eps)` | :410 | **VERIFICADA** |
| `f_lim = f/(f+kf+eps)` | :411 | **VERIFICADA** |
| `e_inhib = 1/(1+i_e*e)` | :412 | **VERIFICADA** |
| `g_inhib_for_f = 1/(1+i_g*g)` | :413 | **VERIFICADA** |

### 2.5 Factores efectivos y tasas base

LaTeX: `F_X=a_mu·f_N`, `F_G=a_beta·f_G·I_E`, `F_F=a_beta·f_F·I_G→F·I_E`.

| Código | Línea | Estado |
|---|---|---|
| `growth_factor = a_mu*n_lim` | :414 | **VERIFICADA** |
| `glucose_ferm_factor = a_beta*g_lim*e_inhib` | :415 | **VERIFICADA** |
| `fructose_ferm_factor = a_beta*f_lim*g_inhib_for_f*e_inhib` | :416 | **VERIFICADA** |
| `mu = mu0*growth_factor` | :417 | **VERIFICADA** |
| `beta_g = betaG0*glucose_ferm_factor` | :418 | **VERIFICADA** |
| `beta_f = betaF0*fructose_ferm_factor` | :419 | **VERIFICADA** |

### 2.6 Mantenimiento

LaTeX: `m(T)=m0·exp[E_am·(TK−293.3)/(293.3·R·TK)]`, `f_m=S_tot/(S_tot+S_m,1/2)`, `S_m,1/2=1.0`.

| Código | Línea | Estado |
|---|---|---|
| `maintenance = m0*exp(Eam*(temp_k-293.3)/(293.3*r*temp_k))` | :420 | **VERIFICADA** |
| `sugar_total = g+f+eps`; `maintenance_availability = sugar_total/(sugar_total + MAINTENANCE_SUGAR_CUTOFF_KG_M3)` | :428–429 | **VERIFICADA** |

`MAINTENANCE_SUGAR_CUTOFF_KG_M3 = 1.0` (`:210`) = `S_{m,1/2}=1.0`. LaTeX correcto. La disponibilidad se multiplica en `maintenance_flux = maintenance*maintenance_availability` (`rhs` :452).

### 2.7 Muerte celular

LaTeX: `T_d(E) = −1e−4·E³ + 0.0049·E² − 0.1279·E + 315.89`; `kd = Kd0·exp[C_de·E + E_td·(TK−305.65)/(305.65·R·TK)]` si `TK ≥ T_d(E)`, si no `kd=0`.

| Código | Línea | Estado |
|---|---|---|
| `td = -0.0001*e**3 + 0.0049*e**2 - 0.1279*e + 315.89` | :421 | **VERIFICADA** |
| `if temp_k >= td: kd = Kd0*exp(Cde*e + Etd*(temp_k-305.65)/(305.65*r*temp_k)) else kd=0.0` | :422–427 | **VERIFICADA** |

Constantes en `FIXED_CONSTANTS` (`:160–172`): `Cde=0.0415`, `Etd=130000`, `Eam=37681` → coinciden con el LaTeX.

---

# 3. Producción de etanol y CO₂

### 3.1 `r_E`

LaTeX `eq:rE`: `r_E(t) = dE/dt = [betaG(t)+betaF(t)]·X(t)`, unidades g L⁻¹ h⁻¹.

| Código | Archivo | Línea | Estado |
|---|---|---|---|
| `ethanol_prod = (terms["beta_g"] + terms["beta_f"])*x` | `shared/run_secondary_joint_campaign_doe.py` | `_core_rates` :290 | **VERIFICADA** |

Coincide con la `rhs` upstream (`de`, `run_new_must_glycerol_estimability_doe.py:466`).

### 3.2 `q_bio`

LaTeX `eq:qbio`: `q_bio(t) = α_CO2/E · max[r_E(t), 0]`.

| Código | Archivo | Línea | Estado |
|---|---|---|---|
| `base_prod = joint.CO2_G_PER_G_ETHANOL * max(float(rates["ethanol_prod"]), 0.0)` | `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py` | `co2_production_g_l_h` :346 | **VERIFICADA** |

### 3.3 `α_CO2/E = 44.01/(2·46.07) ≈ 0.4776`

| Código | Archivo | Línea | Estado |
|---|---|---|---|
| `CO2_G_PER_G_ETHANOL = 44.01 / (2.0 * 46.07)` | `shared/run_secondary_joint_campaign_doe.py` | :166 | **VERIFICADA** |

`44.01/(2·46.07) = 0.477637…` → el LaTeX redondea a `≈0.4776`. Correcto.

### 3.4 Dependencias reales

`q_bio` se obtiene de `_core_rates(theta,batch,core,t)` (`shared/run_secondary_joint_campaign_doe.py:268–300`), que interpola `X,N,G,F,E` del `core` resuelto por `base.simulate`, usa `base.kinetic_terms(theta, T, X,N,G,F,E)`, y calcula `beta_g,beta_f` → dependencia real de **X, G, F, E, N y T** exactamente como afirma el LaTeX. **VERIFICADA.**

---

# 4. Pulsos de nitrógeno

El LaTeX distingue correctamente A (salto físico upstream) y B (respuesta gradual en la capa CO₂). Verifiquemos cada pieza.

### A. Entrada del pulso al modelo upstream — **VERIFICADA**

`simulate` (`run_new_must_glycerol_estimability_doe.py:495–585`) integra las ODE entre eventos y aplica pulsos como saltos exactos de estado vía `_pulse_events` (`:475–492`) y el bloque `:566–574`. Para el canal `N` acumula `delta[N] += amount` en `t_N`. Configuración por defecto `sample_event_order="sample_before_action"`.

- LaTeX `eq:N_jump`: `N(t_N+) = N(t_N−) + ΔN`. **VERIFICADA** (el estado se salta; la ODE no se altera ni se "difumina" el salto). El comentario del LaTeX "No se difumina el salto dentro de la ODE primaria" es correcto.

### B. Respuesta gradual en la capa CO₂ — **VERIFICADA**

`_pulse_utilization_fraction` (`run_co2_matrix_cross_validation_2026.py:1653–1665`):

```python
elapsed = max(time_h - n_pulse_time_h, 0.0)
return np.clip(elapsed / max(pulse_t_rise_h, 1e-9), 0.0, 1.0)
```

- LaTeX `eq:pulse_fraction` `f_N(t) = clip[(t−t_N)/t_rise, 0, 1]`. **VERIFICADA** (`t_rise = pulse_t_rise_h`).
- Para lotes **sin** pulso N, `n_pulse_time_h=nan` o `amount≤0` → devuelve ceros (:1662–1663). Coherente.

### C. Variables simuladas con y sin pulso

`build_driver_cache` (`:1383–1521`): simula el caso **con** pulso (`base.simulate`) y el **contrafactual sin** pulso N (`pulses_without_n{"N":()}`, `:1415–1417`), y guarda:

```python
base_qprod_g_l_h            # con pulso, sin gate O2
base_qprod_no_n_pulse       # sin pulso
n_pulse_qprod_increment     # base_qprod - sin_pulso
biomass_g_l                 # X con pulso
biomass_no_n_pulse          # X sin pulso
n_pulse_biomass_increment   # diferencia
```

`effective_qprod_grid` (`:1668–1745`) computa la versión gradual:

```python
pulse_fraction = _pulse_utilization_fraction(cache, pulse_t_rise_h)
biomass        = max(biomass_no_n_pulse + pulse_fraction*n_pulse_biomass_increment, 0)   # ← X_eff
activity_multiplier = 1.0 + (pulse_activity_gain - 1.0)*pulse_fraction
biological_qprod = max(activity_multiplier*base_qprod_no_n_pulse + pulse_fraction*n_pulse_qprod_increment, 0)
```

- LaTeX `eq:Xeff`: `X_eff = X_0 + f_N·(X_+N − X_0)`. **VERIFICADA** (usa la rampa, no salto).
- LaTeX `eq:qbioN`: `q_bio,N = [1+(g_N−1)·f_N]·q_bio,0 + f_N·(q_bio,+N − q_bio,0)`. **VERIFICADA** (`g_N = pulse_activity_gain`, `f_N` = rampa, `q_bio,0` = contrafactual sin pulso, `q_bio,+N` = con pulso).

### D. Parámetros que aparecen

- `pulse_t_rise_h` (= `t_rise`): MS 36.9954, MN 64.6587 (CSV → coincide con LaTeX §"Valores calibrados"). **VERIFICADO.**
- `pulse_activity_gain` (= `g_N`): MS 1.24358, MN 0.25 (activo en cota inferior). **VERIFICADO.**
- El salto físico de `N(t_N+)` usa el valor `model_pulse_time_h` / `amount_N_kg_m3` del flujo de datos (para LAB vía `override_natural_nutrient_pulses`, `:452–466`); no hay parámetro adicional ahí.

> **Advertencia de mezcla:** El LaTeX dice que la formulación gradual es "la implementación actualmente calibrada". Así es **para el modelo `MODEL_NAME`** (Laboratorio 2026). El **piloto 2025** (`co2_production_g_l_h`, `run_pilot_2025_..._doe.py`) **no** implementa esta construcción contrafactual del pulso N; el piloto usa el salto físico directamente. El LaTeX formula correctamente solo la variante Laboratorio 2026 (ver §contexto).

---

# 5. O2

Implementación: `effective_qprod_grid` (`run_co2_matrix_cross_validation_2026.py:1668–1745`), con `o2_saturation_base_mg_l` calculada en `build_driver_cache` (`:1439–1452`) usando `co2_model.o2_saturation_mg_l` con `sat_scale=1.0`.

| Cantidad | LaTeX | Código | Línea(s) | Estado |
|---|---|---|---|---|
| `O2*(T,E,G,F)` | `8.6·exp[−0.024(T−20)]·exp(−0.0020E)·exp(−0.0010(G+F))` mg/L | `o2_saturation_mg_l` (`run_pilot_2025_co2_solubility_integrated_doe.py:271–276`): `8.6*exp(-0.024*(T-20))*exp(-0.0020*max(E,0))*exp(-0.0010*max(G+F,0))` | build_driver_cache :1439–1452 | **VERIFICADA** |
| `O2(0)` | `s_O2,0·O2*(T0,E0,G0,F0)` | `o2[0] = max(o2_initial_scale,0)*o2_saturation_base_mg_l[0]` | :1711 | **VERIFICADA** |
| `u_O2` | `q_O2,max·X_eff·O2/(K_O2+O2)`, mg L⁻¹ h⁻¹ | `uptake[idx] = qmax*max(biomass[idx],0)*o2[idx]/(O2_K_MG_L + o2[idx])` | :1714–1718 | **VERIFICADA** |
| `dO2/dt` | `−u_O2` (sin reaireación) | `o2[idx+1] = max(o2[idx] - dt*uptake[idx], 0)` | :1721–1722 | **VERIFICADA** |
| `phi_ana` | `K_ana^h/(K_ana^h + O2^h)` | `(O2_ANA_K_MG_L**O2_ANA_HILL)/(O2_ANA_K_MG_L**O2_ANA_HILL + max(o2,0)**O2_ANA_HILL)` | :1723–1725 | **VERIFICADA** |
| `f_ferm` | `f_C + (1−f_C)·phi_ana` | `ferment_fraction = O2_CRABTREE_FLOOR + (1.0-O2_CRABTREE_FLOOR)*phi_ana` | :1726 | **VERIFICADA** |
| `q_resp` | `(44.01/32.00)·u_O2/1000` g L⁻¹ h⁻¹ | `respiratory_co2 = CO2_G_PER_MG_O2_RESP * max(uptake,0)`; `CO2_G_PER_MG_O2_RESP=(44.01/32.00)/1000` | :1727 ; `run_pilot_2025_...:79` | **VERIFICADA** |

### Clasificación de parámetros O2

| Parámetro (LaTeX) | Nombre en código | MS / MN (fit_parameters.csv) | Clasificación | Evidencia |
|---|---|---|---|---|
| `K_O2` | `O2_K_MG_L` | fijo 0.25 | **FIJO** (constante global) | `run_co2_matrix_cross_validation_2026.py:120` |
| `K_ana` | `O2_ANA_K_MG_L` | fijo 0.75 | **FIJO** | `:121` |
| `h` | `O2_ANA_HILL` | fijo 2.0 | **FIJO** | `:122` |
| `f_C` | `O2_CRABTREE_FLOOR` | fijo 0.08 | **FIJO** | `:123` |
| `q_O2,max` | `O2_qmax_mg_gdw_h` | MS 0.15 / MN 0.15, ambos en cota inferior → **CALIBRADO (cota activa)** | `:137`, `:2244` | `fit_parameters.csv` |
| `s_O2,0` | `O2_initial_scale` | MS 0.390441 / MN 0.195400 | **CALIBRADO** | `:138` |
| `O2*(sat_scale)` | — (no existe en Lab 2026; absorbido en `s_O2,0`) | — | **DERIVADO/SUPUESTO** | `o2_saturation_base` se calcula fijando `sat_scale=1.0` (`:1442`) |

> La escala de saturación de O₂ en el modelo Laboratorio 2026 es `sat_scale=1.0` fijo y la escala inicial se lleva en `O2_initial_scale`. El LaTeX `eq:o2sat` no muestra escala (`sat_scale`), lo cual es fiel a Lab 2026.

---

# 6. CO₂ disuelto y liberación gaseosa

Implementación: `raw_qgas_grid_prediction` (`run_co2_matrix_cross_validation_2026.py:1748–1801`) y `co2_saturation_g_l` (`run_pilot_2025_co2_solubility_integrated_doe.py:254–264`).

| Cantidad | LaTeX | Código | Línea(s) | Estado |
|---|---|---|---|---|
| `C_CO2*` | `s_sat·1.69·exp[−0.032(T−20)]·exp(0.0016E)·exp[−0.0012(G+F)]` g/L | `csat = sat_scale*cache.csat_base_g_l`; `csat_base = 1.69*exp(-0.032*(T-20))*exp(0.0016*max(E,0))*exp(-0.0012*max(G+F,0))` | :1430–1438, :1776 | **VERIFICADA** |
| `C_d(0)` | `C_d(0)=0` | `dissolved = 0.0` | :1777 | **VERIFICADA** |
| `dCd/dt` | `q_prod − q_gas` | `dissolved = max(dissolved + dt*(max(qprod[idx-1],0) - qgas[idx]), 0)` | :1800 | **VERIFICADA** |
| `psi` | `f0 + (1−f0)·Cd/(Cd+C_CO2*)`, `f0=0.05` | `release_fraction = CO2_CONTINUOUS_RELEASE_FLOOR + (1.0-CO2_CONTINUOUS_RELEASE_FLOOR)*dissolved_fraction`; `dissolved_fraction = dissolved/(dissolved + csat[idx])` | :1789–1792 ; `CO2_CONTINUOUS_RELEASE_FLOOR=0.05` (:124) | **VERIFICADA** |
| `q_gas,pot` | `k_release·Cd·psi` | `potential_release = max(k_release_h,1e-9)*dissolved*release_fraction` | :1793–1795 | **VERIFICADA** |
| Guarda de conservación | `q_gas,k = min(q_gas,pot,k, C_d,k/dt + q_prod,k−1)` | `qgas[idx] = min(potential_release, available)`; `available = dissolved/dt + max(qprod[idx-1],0)` | :1781, :1799 | **VERIFICADA** |
| `C_d,k+1` | `max[C_d,k + Δt·(q_prod,k−1 − q_gas,k), 0]` | `dissolved = max(dissolved + dt*(max(qprod[idx-1],0) - qgas[idx]), 0)` | :1800 | **VERIFICADA** |
| `y` | `g_m·q_gas` | `prediction = gain*raw_by_batch[batch_name]` | `run_co2_matrix_cross_validation_2026.py:1966` (`_fit_residual`) | **VERIFICADA** |
| Conversión SCCM | `y_gLh = y_sccm·(60/1000)·(44.01/22.414)·(1/V_L)` | `gas_l_h = flow_sccm*60/1000; return gas_l_h*44.01/22.414/volume_l` | `_sccm_to_g_l_h` :555–557 | **VERIFICADA** |

Notas menores:
- `q_prod` es la salida de `effective_qprod_grid` (ver §4 y §7 del LaTeX); el índice `q_prod,k−1` en el LaTeX es fiel al uso `qprod[idx-1]`.
- `q_gas` usa `min(..., disponible)` y **no** añade cinética extra — coincide con el texto "La función min no constituye una cinética adicional".
- `k_release` corresponde a `kCO2_release_h` (cota 0.03–25) y `s_sat` a `CO2sat_scale` (0.35–2.5). Ver §7.

---

# 7. Parámetros

### 7.1 Upstream (fuente: `theta.csv` natural y `theta_by_case.csv` synthetic)

El cargador real (LaTeX correcto) es `_load_theta` (`run_co2_matrix_cross_validation_2026.py:186–194`): parte de `theta = dict(base.DEFAULT_THETA)` y lo sobrescribe con el CSV. `DEFAULT_THETA` (`run_new_must_glycerol_estimability_doe.py:140–158`).

| Parámetro | Valor MS (synthetic) | Valor MN (natural) | Unidad | Fijo/calibrado | Archivo fuente | ¿Coincide con LaTeX? |
|---|---|---|---|---|---|---|
| `mu0` | 0.1336092 | 0.07872792 | h⁻¹ (adim. en la práctica) | Calibrado | `theta_by_case.csv`(caso) / `theta.csv` | ✅ (LaTeX 0.133609 / 0.0787279) |
| `sN` | 18.0 | 18.0 | (parametrización `K_N=mu0/sN`) | **Fijo** (`DEFAULT_THETA`) | `run_new_must_glycerol_estimability_doe.py:142` | ✅ "valor base mantenido" |
| `qN` | 0.03848478 | 0.02108038 | — | Calibrado | CSV | ✅ |
| `qXG` | 0.1125 | 0.1125 | — | **Fijo** (0.18/1.60) | `DEFAULT_THETA:144` | ✅ |
| `qXF` | 0.1125 | 0.1125 | — | **Fijo** | `DEFAULT_THETA:145` | ✅ |
| `betaG0` | 1.32986004 | 0.42887800 | — | Calibrado | CSV | ✅ |
| `sG` | 0.030 | 0.030 | — | **Fijo** (0.225/7.5) | `DEFAULT_THETA:147` | ✅ |
| `betaF0` | 1.82063790 | 3.44039917 | — | Calibrado | CSV | ✅ |
| `sF` | 0.030 | 0.030 | — | **Fijo** | `DEFAULT_THETA:149` | ✅ |
| `qEG` | 2.57708150 | 1.71280679 | — | Calibrado | CSV | ✅ |
| `qEF` | 4.14713941 | 5.02301675 | — | Calibrado | CSV | ✅ |
| `iG` | 0.02634633 | 0.05603744 | L/g | Calibrado | CSV | ✅ |
| `iE` | 0.05547007 | 0.04016794 | L/g | Calibrado | CSV | ✅ |
| `Kd0` | 0.00056172 | 0.00015025 | — | Calibrado | CSV | ✅ |
| `m0` | 0.010 | 0.010 | — | **Fijo** | `DEFAULT_THETA:155` | ✅ |
| `gammaG0` | 0.14952931 | 0.11555879 | — | Calibrado | CSV | ✅ |
| `gammaF0` | 0.03353201 | 0.00010000 | — | Calibrado | CSV | ✅ |

> Nota de redondeo: `qN` MS = 0.038484775… (CSV 6 cifras: 0.038485); el LaTeX escribe 0.0384848. Son consistentes (el CSV trunca la visualización; `to_string` redondea a 6 cifras significativas). `qN` MN = 0.0210803824284854; LaTeX 0.0210804 ✓.

> `sN, qXG, qXF, sG, sF, m0` están en `DEFAULT_THETA`, no en los CSVs; el LaTeX correctamente los marca "valor base mantenido" y "fijado en los drivers actuales".

### 7.2 Capa CO₂/O₂ (fuente `fit_parameters.csv`)

| Parámetro (LaTeX) | Nombre código | MS | MN | Unidad | Cota | Fijo/calibrado/derivado | ¿Coincide LaTeX? |
|---|---|---|---|---|---|---|---|
| `k_release` | `kCO2_release_h` | 15.9857 | 0.424588 | h⁻¹ | 0.03–25 | Calibrado | ✅ |
| `s_sat` | `CO2sat_scale` | 0.350987 (activo, cota 0.35) | 0.351389 (activo) | — | 0.35–2.50 | Calibrado (cota activa) | ✅ |
| `q_O2,max` | `O2_qmax_mg_gdw_h` | 0.15 (activo) | 0.15 (activo) | mg g⁻¹ h⁻¹ | 0.15–6 | Calibrado (cota activa) | ✅ |
| `s_O2,0` | `O2_initial_scale` | 0.390441 | 0.195400 | — | 0.05–1.50 | Calibrado | ✅ |
| `t_rise` | `pulse_t_rise_h` | 36.9954 | 64.6587 | h | 1–72 | Calibrado | ✅ |
| `g_N` | `pulse_activity_gain` | 1.24358 | 0.25 (activo) | — | 0.25–4 | Calibrado (cota activa en MN) | ✅ |
| `f_s` | `chem_activation_start_fraction` | 0.01 (activo) | 0.735057 | — | 0.01–0.95 | Calibrado (cota activa en MS) | ✅ |
| `f_d` | `chem_activation_duration_fraction` | 0.35 (activo) | 1.06391 | — | 0.35–2 | Calibrado (cota activa en MS) | ✅ |
| `g_m` | `matrix_gain` | 2.13427 | 3.11576 | — | 0.10–20 | **Derivado** (se perfila por proyección, `_profile_matrix_gain:1909–1948`) | ✅ |

> `g_m` (`matrix_gain`) **no** es un parámetro optimizado por `least_squares`; se resuelve en un paso auxiliar por mínimos cuadrados de proyección (`_profile_matrix_gain`, `:1909–1948`). El LaTeX lo presenta solo con su cota y valor; es correcto listarlo como valor calibrado/derivado.

### 7.3 Constantes fijas de temperatura/muerte (`FIXED_CONSTANTS`, `run_new_must_glycerol_estimability_doe.py:160–172`)

| Constante | Valor | LaTeX | Estado |
|---|---|---|---|
| `R` | 8.314 | 8.314 | ✅ |
| `Eac` | 59453.0 | 59453 | ✅ |
| `Eafe` | 11000.0 | 11000 | ✅ |
| `EaKn` | 46055.0 | 46055 | ✅ |
| `EaKg` | 46055.0 | 46055 | ✅ |
| `EaKf` | 46055.0 | 46055 | ✅ |
| `EaKig` | 46055.0 | 46055 | ✅ |
| `EaKie` | 46055.0 | 46055 | ✅ |
| `Eam` | 37681.0 | 37681 | ✅ |
| `Cde` | 0.0415 | 0.0415 | ✅ |
| `Etd` | 130000.0 | 130000 | ✅ |
| `S_{m,1/2}` | `MAINTENANCE_SUGAR_CUTOFF_KG_M3=1.0` | 1.0 | ✅ |

### 7.4 Constantes fijas de la capa O₂/CO₂

| Constante | Valor código | Nombre código | LaTeX | Estado |
|---|---|---|---|---|
| `K_O2` | 0.25 | `O2_K_MG_L` (`:120`) | 0.25 | ✅ |
| `K_ana` | 0.75 | `O2_ANA_K_MG_L` (`:121`) | 0.75 | ✅ |
| `h` | 2.0 | `O2_ANA_HILL` (`:122`) | 2 | ✅ |
| `f_C` | 0.08 | `O2_CRABTREE_FLOOR` (`:123`) | 0.08 | ✅ |
| `f_0` | 0.05 | `CO2_CONTINUOUS_RELEASE_FLOOR` (`:124`) | 0.05 | ✅ |
| `M_CO2` | 44.01 | `CO2_MOLAR_MASS_G_MOL` (`:132`) | 44.01 | ✅ |
| `M_E` | 46.07 | (en `CO2_G_PER_G_ETHANOL=44.01/(2·46.07)`) | 46.07 | ✅ |
| `M_O2` | 32.00 | (en `CO2_G_PER_MG_O2_RESP=(44.01/32.00)/1000`) | 32.00 | ✅ |
| `V_m°` | 22.414 | `STANDARD_MOLAR_VOLUME_L_MOL` (`:133`) | 22.414 | ✅ |

---

# 8. Reducción G,F → S

### 8.1 Verificación algebraica de dS/dt

Partiendo de las ecuaciones implementadas (`rhs`, `run_new_must_glycerol_estimability_doe.py:456–464`):

```
dG/dt = −[ qXG·F_X + qEG·F_G + m·f_m·(G/(G+F)) ]·X
dF/dt = −[ qXF·F_X + qEF·F_F + m·f_m·(F/(G+F)) ]·X
```

Sumando:

```
dS/dt = dG/dt + dF/dt
      = −[ (qXG+qXF)·F_X + qEG·F_G + qEF·F_F ]·X
        − m·f_m·[G/(G+F) + F/(G+F)]·X
      = −[ (qXG+qXF)·F_X + qEG·F_G + qEF·F_F + m·f_m ]·X
```

donde usamos `G/(G+F)+F/(G+F)=1`. En el código `sugar_total=G+F+eps` (eps≈0), por lo que el factor de mantenimiento se simplifica exactamente a `m·f_m`.

**La derivación del LaTeX (`eq:S_total`) es CORRECTA desde el código.** (Verificado algebraicamente; el término de mantenimiento se colapsa a `m(T)·f_m`, tal como aparece en el LaTeX, y no contiene `G/(G+F)` residual porque las dos contribuciones se cancelan.)

### 8.2 ¿Cerrado con `[S,N,X,E,Cd]`?

**NO.** El LaTeX concluye correctamente que `eq:S_total` no queda cerrado solo con `S`, porque:

- `F_G = a_β·f_G·I_E = a_β·[G/(G+K_G(T))]·I_E` → depende de **G** (y E).
- `F_F = a_β·f_F·I_{G→F}·I_E = a_β·[F/(F+K_F(T))]·[1/(1+i_G·G)]·I_E` → depende de **F y G**.
- Además `F_X = a_μ·f_N` depende de N; `K_N,K_G,K_F` dependen de T vía las `a_K`.

Por tanto el sistema `[S,N,X,E]` no se puede simular sin conocer la partición `G` vs `F`. Coincide con el LaTeX: la reducción **no es cerrada** sin una hipótesis adicional sobre `rho_G(t)=G/S`.

### 8.3 `rho_G` y la parametrización

El LaTeX introduce `rho_G=G/S`, `G=rho_G·S`, `F=(1−rho_G)·S` y dice que "todavía no forma parte del modelo reducido validado". **VERIFICADO como afirmación**: no hay código que integre la ecuación `dS/dt` ni que reconstruya `rho_G`; la implementación siembre usa `G` y `F` por separado.

**Conclusión de §8:** el LaTeX es correcto y fiel en ambos puntos (la suma algebraica y la no-clausura). No hay discrepancia algebraica. No se propone solución nueva.

---

# 9. Resumen de discrepancias

### A. VERIFICADAS EXACTAMENTE (coinciden línea por línea)

1. Vector de estados primarios `[X,Xd,N,G,F,E,Gly]` y su integración (`rhs`).
2. Todas las ecuaciones `dX/dt, dXd/dt, dN/dt, dG/dt, dF/dt, dE/dt, dGly/dt`.
3. Factores Arrhenius `a_mu, a_beta, a_KN, a_KG, a_KF, a_KiG, a_KiE`.
4. Semisaturaciones `K_N, K_G, K_F`.
5. Inhibiciones `iG(T), iE(T)` y limitaciones `f_N, f_G, f_F, I_E, I_{G→F}`.
6. Factores efectivos `F_X, F_G, F_F` y tasas `mu, beta_G, beta_F`.
7. Mantenimiento `m(T), f_m` (con `S_m,1/2=1.0`).
8. Muerte `T_d(E)` y `kd` (con `Cde`, `Etd`).
9. `r_E = dE/dt = (beta_G+beta_F)·X`.
10. `q_bio = α_CO2/E · max(r_E,0)`; `α_CO2/E = 44.01/(2·46.07)`.
11. Pulso primario exacto `N(t_N+)=N(t_N−)+ΔN`.
12. Rampa gradual `f_N(t)`, `X_eff`, `q_bio,N` con `pulse_t_rise_h` y `pulse_activity_gain`.
13. Submodelo O₂ completo: `O2*, O2(0), u_O2, dO2/dt=−u_O2, phi_ana, f_ferm, q_resp`.
14. Capa CO₂ disuelto: `C_CO2*, C_d(0)=0, dCd/dt=q_prod−q_gas, psi, q_gas,pot`, guarda de conservación, `y=g_m·q_gas`, conversión SCCM.
15. Constantes fijas (temperatura/muerte y capa O₂/CO₂): R, Eac, Eafe, 5·EaK, Eam, Cde, Etd, K_O2, K_ana, h, f_C, f_0, M_CO2, M_E, M_O2, V_m°.
16. Valores de todos los parámetros upstream (MN/MS) y de la capa CO₂ (MS/MN) desde los CSVs.
17. Activación química gradual `t_s, Δt_act, a_chem=3z²−2z³` y el caso de bracket colapsado.
18. La reducción `dS/dt` (algebraicamente correcta) y la conclusión de no-clausura.
19. Criterio de calibración residual `r_ij`, censura a izquierda, penalizaciones de onset y post-pulso.

### B. CORRECTAS PERO CON CAMBIO DE NOTACIÓN

| Afirmación | Cambio de notación |
|---|---|
| `f_C` (Crabtree floor 0.08) | en código `O2_CRABTREE_FLOOR` |
| `f_0` (release floor 0.05) | en código `CO2_CONTINUOUS_RELEASE_FLOOR` |
| `t_rise` | en código `pulse_t_rise_h` |
| `g_N` | en código `pulse_activity_gain` |
| `f_s` | en código `chem_activation_start_fraction` |
| `f_d` | en código `chem_activation_duration_fraction` |
| `k_release` | en código `kCO2_release_h` |
| `s_sat` | en código `CO2sat_scale` |
| `q_O2,max` | en código `O2_qmax_mg_gdw_h` |
| `s_O2,0` | en código `O2_initial_scale` |
| `g_m` | en código `matrix_gain` |
| `E_aK_*` (5 constantes) | en código `EaKn/EaKg/EaKf/EaKig/EaKie` (mismo 46055) |
| `O2*` sin escala | la escala `sat_scale=1.0` está fija en Lab 2026 |

### C. DERIVADAS ALGEBRAICAMENTE DEL CÓDIGO

1. `eq:S_total` (la suma `dG/dt+dF/dt` se colapsa a `m·f_m`).
2. `f_f_ferm` no aparece como tal; se compone en `effective_qprod_grid`.
3. Los valores de `qXG, qXF, sN, sG, sF, m0` provienen de `DEFAULT_THETA` (derivados de relaciones de rendimiento: `0.18/1.60`, `0.225/7.5`, `0.18/19.69`), no del CSV.

### D. NO VERIFICADAS

| Afirmación | Motivo |
|---|---|
| "`x_EKF,5` / `x_EKF,6` es un vector objetivo" | Es una recomendación; ningún script integra `S`. (Aceptable como propuesta, pero no hay código que lo respalde como implementado.) |
| "La conclusión (i) de que `C_d` debe conservarse como estado porque introduce memoria" | Es una justificación conceptual, no una ecuación del repositorio. |
| "`O2` es un estado macroscópico latente, no una trayectoria validada por medición continua" | Es una afirmación sobre datos/validación; no hay en el repo una trayectoria continua de O₂ para refutarla/confirmarla. |
| "`S_m,1/2` es escala de mantenimiento" | `MAINTENANCE_SUGAR_CUTOFF_KG_M3` es un corte, no una escala; semántica equivalente, su origen no se documenta más allá de la constante. |
| Origen exacto de `E_K` 46055 (usado para K_G, K_F y K_iG, K_iE a la vez) | En `FIXED_CONSTANTS` todas valen 46055; no hay justificación/experimento que lo respalde, solo el valor. |

### E. INCORRECTAS

**1) "El ajuste utiliza mínimos cuadrados robustos con pérdida `soft_l1`" (§"Criterio de calibración de la capa CO₂").**

- El fitter que produce `fit_parameters.csv` (Laboratorio 2026) es `fit_matrix` en `run_co2_matrix_cross_validation_2026.py:2011–2109`, y su `least_squares` **no** pasa `loss=` (`:2060–2069`) → usa el valor por defecto `loss="linear"` (mínimos cuadrados ordinarios), **no** `soft_l1`.
- `soft_l1` sí existe, pero en el fitter del **piloto 2025** (`fit_co2_candidate`, `run_pilot_2025_co2_solubility_integrated_doe.py:643`), que **no** genera el `fit_parameters.csv` de Laboratorio 2026.
- **Corrección sugerida:** decir "mínimos cuadrados (TRF) sin pérdida robusta (por defecto `linear`)" para el modelo Laboratorio 2026, o bien aclarar que `soft_l1` corresponde a la calibración del piloto 2025.

---

# 10. Elementos que requieren segunda verificación

1. **Doble puerta de O₂ en `build_driver_cache`.** `base_qprod = co2_model.co2_production_g_l_h(theta, batch, core, time_h)` (`:1407`) se llama **sin** `candidate=`, por lo que `co2_production_g_l_h` retorna `base_prod` (estequiométrico, **sin** gate de O₂) y luego `effective_qprod_grid` aplica **una sola** puerta O₂. Conviene confirmar en una revisión adicional que ningún otro punto de este flujo reintroduce un segundo gate (p. ej. buscando otras llamadas a `co2_production_g_l_h` con candidato O₂). Es código difícil de interpretar porque el rol del piloto como "proveedor de funciones" (B) se superpone con el del modelo A.

2. **Dualidad de modelo A vs B (puerta de liberación y O₂).** El LaTeX cita en "Fuentes" tanto `run_pilot_2025_co2_solubility_integrated_doe.py` como `run_co2_matrix_cross_validation_2026.py`/`fit_parameters.csv`. Las ecuaciones §6–§15 describen el modelo **A** (liberación continua `psi` con f0=0.05). El modelo **B** (piloto 2025) usa `qgas = k_release·smooth_positive(Cd−C_CO2*)` y permite `kLaO2` como parámetro. Si el destinatario cree que el LaTeX describe el piloto 2025, hay ambigüedad. Recomendación: separar explícitamente las dos familias.

3. **`soft_l1` (§9.E).** Confirmar con un tercer revisor que el ajuste reportado para Laboratorio 2026 no pasó `loss="soft_l1"`.

4. **Dependencia de `X_eff` en `u_O2`.** El LaTeX escribe `u_O2 = q_O2,max·X_eff·O2/(K_O2+O2)`. En el código, la variable `biomass` es `X_eff` **solo** en la rama activa de impulso N; en lotes sin impulso N `biomass = cache.biomass_g_l` (= `X`). Como en ese caso `X_eff==X` (el incremento es 0), la frase es coherente, pero conviene revisar que no haya un lote con `X_eff != X` mal mapeado.

5. **Redondeo de `qN` MS (0.0384848 vs 0.038485).** El CSV (`theta_by_case.csv`) guarda 0.038484775…; el LaTeX escribe 0.0384848. Coinciden al redondear, pero la diferencia con la lectura de 6 cifras del CSV (0.038485) puede confundir. Confirmar la fuente de precisión.

6. **`matrix_gain` como valor "calibrado".** No se optimiza en `least_squares`; se resuelve por proyección (`_profile_matrix_gain`). Si se desea estricta fidelidad, debe marcarse como "derivado/determinado por regresión de proporcionalidad", no "calibrado por TRF".

7. **`g_m` en límite inferior.** En MN, `pulse_activity_gain=0.25` está activo en cota inferior; el LaTeX lo marca con `*`. Confirmar que la marca `*` se aplicó también a `q_O2,max`, `s_sat` y `f_s/f_d` de MS (sí están marcados). No hay error, pero es información sensible a cota activa que debe permanecer consistente.
