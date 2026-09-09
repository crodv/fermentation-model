# Auditoría de las ecuaciones realmente ejecutadas del modelo de fermentación

**Fecha de auditoría:** 2026-09-09  
**Alcance:** reconstrucción de solo lectura de las ecuaciones que produjeron los resultados versionados y las evaluaciones actuales. No se recalibró, no se ejecutó ningún optimizador y no se usó literatura externa.  
**Inventario:** 75 ecuaciones/relaciones matemáticas únicas del modelo, sus entradas, discretizaciones y funciones de observación; 36 entradas de contraste notebook--código.

## 1. Dictamen ejecutivo

La forma dinámica central es un sistema de siete estados,

\[
y=(X,X_d,N,G,F,E,Gly),
\]

integrado por `base.simulate` con LSODA entre eventos y saltos exactos en los canales `N`, `G`, `F`, `E` y `X`. La señal de CO2 no es un estado de ese ODE. Se calcula en una capa posterior que: (i) deriva producción biológica desde la tasa de etanol; (ii) interpone una activación química no causal; (iii) integra un pool interno de O2; (iv) reemplaza el efecto instantáneo de un pulso N por una rampa contrafactual; (v) integra por Euler un pool interno de CO2 disuelto; y (vi) multiplica la liberación gaseosa por `matrix_gain`.

No existe un único modelo canónico numéricamente consistente en todas las ramas activas. La **forma de las ecuaciones** sí es común, pero hay tres incompatibilidades activas:

1. **[CONFLICT] Vector upstream incompleto.** El runner que generó `theta.csv` fijó `sN`, `qXG`, `qXF`, `sG`, `sF` y `m0` en valores heredados de `theta_multistart_07.csv`. Esos seis nombres no se guardaron en `theta.csv`. `co2_cross._load_theta` y los notebooks LAB013--015/LAB016--018 rellenan los ausentes con `base.DEFAULT_THETA`, que contiene valores distintos.
2. **[CONFLICT] Dosis de N.** La calibración upstream usó `N:...@0.08 kg m^-3`; la calibración CO2 reemplazó los pulsos naturales por `0.14 kg m^-3` y tiempos derivados del cruce de densidad 1040 g/L. Los resultados upstream y CO2 no usan la misma entrada N.
3. **[CONFLICT] Conversión SCCM.** La calibración/artefacto CO2 usa 22.414 L mol^-1 sin factor 0.74; el holdout LAB016--018 convierte la observación con 24.16 L mol^-1 y factor 0.74, pero conserva el `matrix_gain` ajustado con la primera convención.

Las ecuaciones Markdown del notebook CO2 están **mayoritariamente actualizadas, pero no son una especificación exacta**: omiten el mínimo `DRIVER_GRID_H=0.25 h` en la duración del smoothstep y no muestran los índices/recortes de las integraciones Euler de O2 y CO2. Resultado del contraste de 36 entradas: **23 MATCH, 1 MISMATCH, 3 PARTIAL_MATCH, 1 DOCUMENTATION_ONLY y 8 CODE_ONLY**.

## 2. Fuentes de verdad y cadena real

### 2.1 Notebooks auditados

| Notebook | Evidencia de ejecución | Acción real |
|---|---:|---|
| `laboratory_2026/notebooks/fermentation_estimability_historical_natural.ipynb` | versión `.executed.ipynb`, celdas de código 1--13 ejecutadas; fuentes idénticas al notebook fuente | llama `analysis.run_medium_analysis("natural", ..., fit_nfev=300)` y genera `theta.csv` |
| `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.ipynb` | versión `.executed.ipynb`, celdas de código 1--10 ejecutadas; fuentes idénticas | llama `analysis.run_analysis(n_starts=5,max_nfev=300,seed=20260812)`; modelo declarado: `solubility_o2_nitrogen_boost_continuous_release` |
| `laboratory_2026/notebooks/lab013_015_natural_must_co2_model_analysis.ipynb` | 32 celdas de código con contador | carga `theta_A`; define `theta_B` congelado en código; simula el ODE y reproduce la capa CO2; el notebook actual no optimiza |
| `laboratory_2026/notebooks/lab016_018_natural_must_holdout.ipynb` | 43 celdas de código con contador, más una celda exploratoria posterior | carga ambos artefactos congelados; simula escenarios de IC y diagnósticos; no ajusta parámetros |

Sí existe, por tanto, un notebook específico que generó la calibración upstream: `fermentation_estimability_historical_natural.ipynb`, creado y ejecutado por `run_estimability_historical_by_medium.py:1011-1171`. No se inventa un notebook ni se atribuye la calibración a un runner sin notebook.

### 2.2 Grafo de dependencias ejecutado

```text
fermentation_estimability_historical_natural.executed.ipynb, cell 3
  -> run_estimability_historical_by_medium.run_medium_analysis
     -> make_medium_batches
        -> new_must_data_loader / secondary_metabolite_long.csv
        -> run_secondary_joint_campaign_doe.make_secondary_batches
        -> run_new_must_glycerol_estimability_doe.make_batches
     -> run_final_operational_doe_v2.load_theta_final       [semilla completa]
     -> run_estimability_old_vs_lot1.fit_core_case          [multistart]
     -> run_new_must_glycerol_estimability_doe.fit_parameters
        -> residual_vector -> simulate -> rhs -> kinetic_terms
     -> results/estimability_historical_natural/theta.csv   [solo subset]

co2_solubility_o2_cross_matrix_2026.executed.ipynb, cell 4
  -> run_co2_matrix_cross_validation_2026.run_analysis
     -> load_batches
        -> run_estimability_historical_by_medium.make_medium_batches
        -> override_natural_nutrient_pulses                 [0.14 kg m^-3]
        -> _load_theta(theta.csv)                            [rellena DEFAULT_THETA]
     -> build_driver_cache
        -> base.simulate (con pulso / sin pulso)
        -> pilot_2025.co2_production_g_l_h
           -> run_secondary_joint_campaign_doe._core_rates
     -> effective_qprod_grid
     -> raw_qgas_grid_prediction
     -> _profile_matrix_gain / fit_matrix
     -> fit_parameters.csv, prediction_rows.csv, etc.

lab013_015..., cells 8, 16, 18, 20, 23
  -> theta_A = DEFAULT_THETA + theta.csv
  -> theta_B = theta_A + 11 valores literales congelados
  -> base.simulate + co2_layer.build_driver_cache
  -> co2_layer.raw_qgas_grid_prediction

lab016_018..., cells 3, 9, 11, 17
  -> theta_frozen = co2_cross._load_theta(theta.csv)
  -> CO2 natural = fit_parameters.csv
  -> base.simulate + build_driver_cache + raw_qgas_grid_prediction
  -> q_pred = matrix_gain q_gas
```

### 2.3 Clasificación de cantidades

| Cantidad | Clasificación exacta | Unidad |
|---|---|---|
| `X` | estado ODE central, biomasa viable | kg m^-3 (numéricamente g L^-1) |
| `Xd` | estado ODE central, biomasa muerta | kg m^-3 |
| `N` | estado ODE central, nitrógeno asimilable | kg m^-3 |
| `G`, `F`, `E`, `Gly` | estados ODE centrales | g L^-1 |
| `T` | input exógeno interpolado, no estado | degC; se convierte a K internamente |
| `O2` | estado interno discreto de la capa CO2, no del ODE central | mg L^-1 |
| `C_CO2` | pool interno integrado separadamente por Euler, no del ODE central | g L^-1 |
| `A(t)`, `phi_ana`, `f_ferm`, `r(t)` | variables algebraicas de la capa CO2 | adimensional |
| `qprod`, `qgas`, `qobs` | tasas algebraicas/discretizadas | g L^-1 h^-1 |
| `matrix_gain` | función de observación/escala perfilada | adimensional |

## 3. Modelo upstream ejecutado

Convención previa a toda evaluación: `kinetic_terms` reemplaza `X,N,G,F,E` por `max(valor,0)` y `rhs` hace lo mismo con los siete estados. Después de integrar, `simulate` recorta cada columna a `STATE_BOUNDS`. Estas operaciones son parte del resultado numérico ejecutado.

### 3.1 Temperatura, Arrhenius y auxiliares (R01--R25)

\[
T_K=T_C+273.15. \tag{R01}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `shared/run_new_must_glycerol_estimability_doe.py`, `kinetic_terms`, líneas 387--397; notebooks upstream celda 3, CO2 celda 4 y holdout celda 11 por la cadena de llamadas.

\[
a_\mu=\exp\!\left[\frac{E_{ac}(T_K-300)}{300RT_K}\right],\qquad
a_\beta=\exp\!\left[\frac{E_{afe}(T_K-296.15)}{296.15RT_K}\right]. \tag{R02--R03}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 397--398.

Para \(j\in\{Kn,Kg,Kf,Kig,Kie\}\), con referencia 293.15 K,

\[
a_j=\exp\!\left[\frac{E_{aj}(T_K-293.15)}{293.15RT_K}\right]. \tag{R04--R08}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 399--403. El código evalúa cinco expresiones separadas, no una sola función vectorial.

\[
K_N=\frac{\mu_0}{s_N}a_{Kn},\quad
K_G=\frac{\beta_{G0}}{s_G}a_{Kg},\quad
K_F=\frac{\beta_{F0}}{s_F}a_{Kf}. \tag{R09--R11}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 404--406.

\[
i_G(T)=\frac{i_G}{a_{Kig}+10^{-8}},\qquad
i_E(T)=\frac{i_E}{a_{Kie}+10^{-8}}. \tag{R12--R13}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 395, 407--408.

\[
L_N=\frac{N}{N+K_N+10^{-8}},\quad
L_G=\frac{G}{G+K_G+10^{-8}},\quad
L_F=\frac{F}{F+K_F+10^{-8}}. \tag{R14--R16}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 409--411.

\[
I_E=\frac{1}{1+i_E(T)E},\qquad I_{G\to F}=\frac{1}{1+i_G(T)G}. \tag{R17--R18}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 412--413.

\[
\mu=\mu_0a_\mu L_N,\qquad
\beta_G=\beta_{G0}a_\beta L_GI_E,\qquad
\beta_F=\beta_{F0}a_\beta L_FI_{G\to F}I_E. \tag{R19--R21}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 414--419. **N no aparece directamente en `beta_g` ni `beta_f`; aparece solo en `mu`/`growth_factor`.**

\[
m(T)=m_0\exp\!\left[\frac{E_{am}(T_K-293.3)}{293.3RT_K}\right]. \tag{R22}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, línea 420.

\[
T_d(E)=-10^{-4}E^3+0.0049E^2-0.1279E+315.89, \tag{R23}
\]

\[
k_d=\begin{cases}
K_{d0}\exp\!\left[C_{de}E+\dfrac{E_{td}(T_K-305.65)}{305.65RT_K}\right],&T_K\ge T_d(E),\\
0,&T_K<T_d(E).
\end{cases} \tag{R24}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms`, líneas 421--427. La desigualdad y la rama exactamente nula son ejecutadas.

\[
S=G+F+10^{-8},\qquad M_S=\frac{S}{S+1.0},\qquad J_m=m(T)M_S. \tag{R25}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `kinetic_terms` y `rhs`, líneas 428--452. `1.0` es `MAINTENANCE_SUGAR_CUTOFF_KG_M3`; el nombre de unidad es histórico aunque G y F están en g L^-1.

### 3.2 Las siete ODE (R26--R32)

\[
\frac{dX}{dt}=(\mu-k_d)X. \tag{R26}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `shared/run_new_must_glycerol_estimability_doe.py`, `rhs`, líneas 445--454.

\[
\frac{dX_d}{dt}=k_dX. \tag{R27}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `rhs`, línea 454.

\[
\frac{dN}{dt}=-q_N(a_\mu L_N)X. \tag{R28}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `rhs`, línea 455. El código usa `growth_factor=a_mu*n_lim`, no `mu`; por ello no debe añadirse otro factor `mu0`.

\[
\frac{dG}{dt}=-\left[q_{XG}(a_\mu L_N)+q_{EG}(a_\beta L_GI_E)+J_m\frac{G}{S}\right]X. \tag{R29}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `rhs`, líneas 456--460.

\[
\frac{dF}{dt}=-\left[q_{XF}(a_\mu L_N)+q_{EF}(a_\beta L_FI_{G\to F}I_E)+J_m\frac{F}{S}\right]X. \tag{R30}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `rhs`, líneas 461--465.

\[
\frac{dE}{dt}=(\beta_G+\beta_F)X. \tag{R31}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `rhs`, línea 466.

\[
\frac{dGly}{dt}=\left[\gamma_{G0}(a_\beta L_GI_E)+\gamma_{F0}(a_\beta L_FI_{G\to F}I_E)\right]X. \tag{R32}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `rhs`, línea 467.

### 3.3 Integración, recortes y eventos (R33)

Entre eventos, LSODA usa `rtol=1e-6`, `atol=1e-8`, `max_step=2 h`. En un evento del canal \(j\in\{N,G,F,E,X\}\),

\[
y_j(t_p^+)=y_j(t_p^-)+\Delta y_j,\qquad y_{k\ne j}(t_p^+)=y_k(t_p^-). \tag{R33}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `base._pulse_events`, líneas 475--492, y `base.simulate`, líneas 495--585. La convención predeterminada es `sample_before_action`: una muestra coincidente ve el estado pre-salto y la dosis se aplica inmediatamente después.

- Upstream natural: `batch_summary.csv` registra 0.08 kg m^-3 en LAB004--LAB012, en los tiempos 68, 68, 99, 65, 65, 41, 79, 72 y 72 h.
- Capa CO2 natural: `override_natural_nutrient_pulses` reemplaza lo anterior por un pulso de 0.14 kg m^-3 por batch; tiempos 56.0917, 55.0866, 74, 56.2462, 56.75, 41.8462, 102.4945, 86.8367 y 91.0417 h. Fuente: `run_co2_matrix_cross_validation_2026.py:382-466` y `natural_nutrient_pulse_details.csv`.
- LAB016--018 estricto: no aplica salto porque la dosis tardía era desconocida (notebook celdas 7, 9 y 11). El diagnóstico posterior aplica 0.14/0.28, pero está etiquetado como no holdout.

## 4. Producción biológica de CO2 (R34--R36)

La tasa de etanol reconstruida por `_core_rates` es

\[
q_E=(\beta_G+\beta_F)X. \tag{R34}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `shared/run_secondary_joint_campaign_doe.py`, `_core_rates`, líneas 268--300.

\[
\chi_{CO2/E}=\frac{44.01}{2(46.07)}=0.4776427176\ \mathrm{g\ CO_2\,g^{-1}\ ethanol}. \tag{R35}
\]

Fuente inmediata: **[FIXED] [EXECUTED] [IMPORTED]** `run_secondary_joint_campaign_doe.py:164-166`.

\[
q_{bio,\,+N}=q_{prod,base}=\chi_{CO2/E}\max(q_E,0). \tag{R36}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py`, `co2_production_g_l_h`, líneas 335--349. N no aparece directamente en R34--R36; solo puede modificar X y `mu` a través del ODE.

## 5. Bloque O2 ejecutado (R37--R43)

La saturación base de O2 es

\[
O_2^*(T,E,G,F)=\max\left[8.6e^{-0.024(T-20)}e^{-0.0020\max(E,0)}e^{-0.0010\max(G+F,0)},10^{-6}\right]. \tag{R37}
\]

Fuente inmediata: **[EXECUTED] [IMPORTED]** `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py`, `o2_saturation_mg_l`, líneas 271--276; `build_driver_cache`, líneas 1439--1452, siempre pasa escala 1.0.

\[
O_{2,0}=\max(s_{O2,0},0)O_2^*(T_0,E_0,G_0,F_0). \tag{R38}
\]

Fuente inmediata: **[EXECUTED]** `run_co2_matrix_cross_validation_2026.py`, `effective_qprod_grid`, líneas 1709--1712. `s_O2,0` es `O2_initial_scale`, no `CO2sat_scale`.

\[
u_i=q_{O2,max}\max(X_i^{eff},0)\frac{O_{2,i}}{K_{O2}+O_{2,i}}, \tag{R39}
\]

\[
O_{2,i+1}=\max(O_{2,i}-\Delta t_i u_i,0). \tag{R40}
\]

Fuente inmediata: **[EXECUTED]** `effective_qprod_grid`, líneas 1713--1722. Es Euler explícito; en esta rama no hay reaeración ni término `kLa`.

\[
\phi_{ana,i}=\frac{K_{ana}^{h}}{K_{ana}^{h}+\max(O_{2,i},0)^h}, \tag{R41}
\]

\[
f_{ferm,i}=f_C+(1-f_C)\phi_{ana,i},\qquad f_C=0.08, \tag{R42}
\]

\[
q_{resp,i}=\frac{44.01/32.00}{1000}\max(u_i,0). \tag{R43}
\]

Fuente inmediata: **[EXECUTED] [FIXED]** `effective_qprod_grid`, líneas 1723--1727; coeficiente en `pilot_2025/...py:79`.

## 6. Respuesta ejecutada a nutrición (R44--R49)

Para el único pulso N admitido por `build_driver_cache`, se simula una trayectoria con pulso y otra sin pulso. Se forman

\[
r_i=\begin{cases}0,&\text{sin pulso o }\Delta N\le0,\\
\operatorname{clip}\!\left(\dfrac{t_i-t_N}{t_{rise}},0,1\right),&\text{con pulso},
\end{cases} \tag{R44}
\]

Fuente inmediata: **[EXECUTED]** `_pulse_utilization_fraction`, líneas 1653--1665.

\[
\Delta X_i=X_{+N,i}-X_{0,i},\qquad
\Delta q_i=q_{bio,+N,i}-q_{bio,0,i}. \tag{R45--R46}
\]

Fuente inmediata: **[EXECUTED]** `build_driver_cache`, líneas 1414--1476.

\[
X_i^{eff}=\max(X_{0,i}+r_i\Delta X_i,0), \tag{R47}
\]

\[
M_{act,i}=1+(g_N-1)r_i, \tag{R48}
\]

\[
q_{bio,i}=\max(M_{act,i}q_{bio,0,i}+r_i\Delta q_i,0). \tag{R49}
\]

Fuente inmediata: **[EXECUTED]** `effective_qprod_grid`, líneas 1690--1708. Con el fit natural actual, `g_N=0.25`; por tanto el multiplicador atenúa gradualmente la actividad sin pulso hasta 0.25, no es un boost mayor que uno.

## 7. Activación/onset (R50--R55)

Sea \(S_k=G_k+F_k\). El primer índice activo satisface

\[
S_k\le S_{first}-5\ \mathrm{g\,L^{-1}}\quad\lor\quad E_k\ge E_{first}+2\ \mathrm{g\,L^{-1}}. \tag{R50}
\]

Fuente inmediata: **[EXECUTED]** `_chemical_activity_bracket`, líneas 1302--1332.

\[
U=t_{k,first\ active},\qquad L=\max\{t_j:j<k,\ j\text{ es muestra química}\}. \tag{R51}
\]

Si no hay evidencia activa, `L=U=primera muestra química`; si no hay ninguna química, `L=U=0`. Fuente inmediata: **[EXECUTED]** `_chemical_activity_bracket`, líneas 1316--1352.

Para \(U>L\),

\[
t_s=L+s(U-L),\qquad D=\max[d(U-L),0.25\ \mathrm{h}], \tag{R52}
\]

\[
z_i=\operatorname{clip}\!\left(\frac{t_i-t_s}{D},0,1\right),\qquad A_i=z_i^2(3-2z_i). \tag{R53--R54}
\]

Para \(U\le L\), \(A_i=\mathbf 1(t_i\ge U)\). Fuente inmediata: **[EXECUTED]** `_bounded_smoothstep_activation`, líneas 1360--1380; `DRIVER_GRID_H=0.25` en línea 89.

La producción efectiva final es

\[
q_{prod,i}=\max\{A_i[q_{bio,i}f_{ferm,i}+q_{resp,i}],0\}. \tag{R55}
\]

Fuente inmediata: **[EXECUTED]** `effective_qprod_grid`, líneas 1728--1745.

**Causalidad:** R50--R54 requieren la primera muestra futura que evidencia caída de azúcar/aumento de etanol y la muestra anterior. Son no causales para operación online. Los parámetros `s` y `d` son compartidos por matriz, pero L y U son batch-específicos y se obtienen mirando la trayectoria química completa.

## 8. Solubilidad, pool disuelto y liberación (R56--R61)

\[
C_i^*=s_{sat}\,1.69e^{-0.032(T_i-20)}e^{0.0016\max(E_i,0)}e^{-0.0012\max(G_i+F_i,0)}. \tag{R56}
\]

Fuente inmediata: **[EXECUTED]** `build_driver_cache`, líneas 1429--1438, y `raw_qgas_grid_prediction`, línea 1776. Unidad: g CO2 L^-1. La forma importada equivalente está en `pilot_2025/...py:254-264`.

Con \(C_0=0\), para \(i\ge1\), el código usa el pool anterior y la solubilidad del punto actual:

\[
\rho_i=\frac{C_{i-1}}{\max(C_{i-1}+C_i^*,10^{-12})},\qquad
f_i=0.05+0.95\rho_i, \tag{R57}
\]

\[
q_{pot,i}=\max(k_{release},10^{-9})C_{i-1}f_i, \tag{R58}
\]

\[
q_{avail,i}=\frac{C_{i-1}}{\Delta t_i}+\max(q_{prod,i-1},0), \tag{R59}
\]

\[
q_{gas,0}=0,\qquad q_{gas,i}=\min(q_{pot,i},q_{avail,i}), \tag{R60}
\]

\[
C_i=\max\{C_{i-1}+\Delta t_i[\max(q_{prod,i-1},0)-q_{gas,i}],0\}. \tag{R61}
\]

Fuente inmediata: **[EXECUTED]** `raw_qgas_grid_prediction`, líneas 1748--1801. `C_CO2` es una variable integrada en una segunda pasada Euler sobre la malla de 0.25 h, no un estado de `base.rhs`, y se inicializa siempre en cero.

La rama comparadora activa, pero no nominal, usa `softplus(C-C*)` en vez de R57--R58. La rama nominal queda determinada por `MODEL_NAME` y `_uses_continuous_release`, líneas 68 y 1645--1650.

## 9. Función de observación CO2 y conversiones (R62--R65)

\[
q_{obs}=g_{matrix}q_{gas}. \tag{R62}
\]

Fuente inmediata: **[EXECUTED] [PROFILED]** `predict_and_score`, líneas 2450--2482; holdout LAB016--018, celda 11. `matrix_gain` se perfila por mínimos cuadrados acotados, no integra el balance físico.

En calibración/artefacto CO2,

\[
y_{g/L/h}=y_{sccm}\frac{60}{1000}\frac{44.01}{22.414}\frac{1}{V_L};\quad
V_L=2\Rightarrow1\ \mathrm{SCCM}=0.05890515\ \mathrm{g\,L^{-1}h^{-1}}. \tag{R63}
\]

Fuente inmediata: **[EXECUTED]** `run_co2_matrix_cross_validation_2026.py`, `_sccm_to_g_l_h`, líneas 555--557; constantes líneas 132--133.

En el holdout LAB016--018,

\[
y_{g/L/h}=y_{sccm}\frac{44.0095(60)(0.74)}{1000(24.16)(2.0)}
=0.04043919y_{sccm}. \tag{R64}
\]

Fuente inmediata: **[EXECUTED]** `lab016_018_natural_must_holdout.ipynb`, celda 17. **[CONFLICT]** R62 usa un gain perfilado contra R63, pero el holdout compara contra R64.

Corrección de cero usada en la calibración CO2:

\[
b_r=\max[0,Q_{0.10}\{y_{sccm}(t):t\le t_0+12h\}],\qquad
y_{corr}=\max(y_{sccm}-b_r,0). \tag{R65}
\]

Fuente inmediata: **[EXECUTED] [MATCH]** notebook CO2 celda 1; implementación `apply_sensor_zero_correction`, líneas 583--663. Ocurre antes de conversión, filtrado y suavizado.

## 10. Funciones de observación/conversión offline (R66--R74)

Estas relaciones no son cinética.

\[
X_{obs}=C_{total}[10^6\,cells/mL]\frac{Viability[\%]}{100}(0.03), \tag{R66}
\]

\[
X_{d,obs}=\max(C_{total}-C_{viable},0)(0.03). \tag{R67}
\]

Fuente inmediata: **[EXECUTED]** holdout celda 31, líneas internas 46--49 para R66; loader histórico `new_must_data_loader.py:222-235` para R67. En hojas históricas homologadas `Viability` se usa como concentración viable; en `report.csv` crudo es porcentaje. El factor 0.03 proviene de 30 pg/célula (`new_must_data_loader.py:53-57`).

\[
N[kg\,m^{-3}]=YAN[mg\,L^{-1}]10^{-3}. \tag{R68}
\]

Fuente inmediata: **[EXECUTED]** `new_must_data_loader.py:244-247`; LAB013--015 celdas 16 y 20.

\[
E[g\,L^{-1}]=\begin{cases}
ETANOL,&\text{si la serie primaria contiene algún valor}>25\text{ y el valor existe},\\
7.8924\,ETANOL[\%v/v],&\text{en caso contrario},\\
7.8924\,Alcolyzer[\%v/v],&\text{fallback}.
\end{cases} \tag{R69}
\]

Fuente inmediata: **[EXECUTED]** `new_must_data_loader.py`, `_ethanol_observation`, líneas 133--161; `ETHANOL_G_L_PER_PERCENT_VV=7.8924`, líneas 53--54.

\[
G_{obs}=Y15_{glucose},\quad F_{obs}=Y15_{fructose},\quad Gly_{obs}=Y15_{glycerol}. \tag{R70--R72}
\]

Fuente inmediata: **[EXECUTED]** `new_must_data_loader.py:237-260`. Son mapeos directos en g L^-1.

En LAB013--015 se usa adicionalmente

\[
H_S(y)=G+F, \tag{R73}
\]

Fuente inmediata: **[EXECUTED] [MATCH]** notebook LAB013--015, Markdown celda 5 y código celda 20. No reemplaza las observaciones separadas G/F del fit histórico.

Escala de residual central:

\[
\sigma_s(y)=\max(\sigma_{floor,s},r_s\max(|y|,\sigma_{floor,s})). \tag{R74}
\]

Fuente inmediata: **[EXECUTED]** `base.sigma_for_state`, líneas 588--592. Floors/relativos: X 0.06/0.08; Xd 0.06/0.12; N 0.012/0.08; G 2.5/0.025; F 2.5/0.025; E 2.0/0.025; Gly 0.35/0.05.

## 11. Perfilado de `matrix_gain` (R75)

Para puntos no censurados, con \(w_b=[\sigma_b\sqrt{n_b}]^{-1}\),

\[
\hat g=\operatorname{clip}_{[0.1,20]}
\frac{\sum_b\langle w_bq_{gas,b},w_by_b\rangle}
{\sum_b\langle w_bq_{gas,b},w_bq_{gas,b}\rangle}. \tag{R75}
\]

Fuente inmediata: **[EXECUTED] [PROFILED]** `_profile_matrix_gain`, líneas 1909--1948. Para el perfil completo `sigma_b=max(0.04,0.10 peak_b)` y cada batch se divide por `sqrt(n_b)`; censura, onset y peak postpulso se agregan en `_fit_residual`, líneas 1951--2008.

## 12. Condiciones iniciales consumidas

| Pipeline | X0/Xd0 | N0/G0/F0/E0/Gly0 | Clasificación |
|---|---|---|---|
| calibración upstream LAB004--012 | primera observación finita; fallback X=.45, Xd=0 | primera finita; fallbacks N=.18, G=80, F=80, E=0, Gly=0 | IC medida cuando existe; fallback codificado en `base._initials_from_group:266-277` |
| capa CO2 histórica | IC del batch histórico | mismas IC del loader | medidas/heredadas; pulso reemplazado |
| LAB013--015 | X=.45, Xd=0 | PI medido para N/G/F/Gly; E=0 | X/Xd/E fallback; composición PI medida; celda 16 |
| LAB016--018 | X=.45, Xd=0 | N/G/F/Gly proxy de `CondicionesIniciales`; E=0 o mediana histórica | heredada/proxy + escenarios; celdas 9--11 |

Los valores históricos exactos están en `results/estimability_historical_natural/batch_summary.csv`: X0 0.099--1.0656, Xd0 0.0009--0.1209, N0 0.22024--0.23922, G0 75.0--81.63, F0 70.81--87.95, E0 9.234108--11.759676 y Gly0 0.75--1.27.

## 13. Parámetros del modelo actual

### 13.1 Upstream: valores que determinan las siete ODE

| symbol | code_name | description | unit | equation_where_used | value_natural_current | status | source |
|---|---|---|---|---|---:|---|---|
| mu0 | `mu0` | escala de crecimiento | h^-1 | R09,R19 | 0.0787279168 | REESTIMATED_UPSTREAM | `theta.csv`, fila mu0 |
| sN | `sN` | parametriza KN=mu0/sN | (kg m^-3)^-1 h^-1 | R09 | **upstream fit 8.75144587; downstream 18.0** | FIXED_UPSTREAM | `theta_multistart_07.csv`; `DEFAULT_THETA:142` |
| qN | `qN` | consumo N por growth factor y X | h^-1 | R28 | 0.0210803824 | REESTIMATED_UPSTREAM | `theta.csv` |
| qXG | `qXG` | azúcar G asociada a crecimiento | h^-1 | R29 | **upstream 0.0814909864; downstream 0.1125** | FIXED_UPSTREAM | heredado; `DEFAULT_THETA:144` |
| qXF | `qXF` | azúcar F asociada a crecimiento | h^-1 | R30 | **upstream 0.0709327065; downstream 0.1125** | FIXED_UPSTREAM | heredado; `DEFAULT_THETA:145` |
| betaG0 | `betaG0` | producción de etanol desde G | h^-1 | R10,R20 | 0.4288780030 | REESTIMATED_UPSTREAM | `theta.csv` |
| sG | `sG` | parametriza KG=betaG0/sG | (g L^-1)^-1 h^-1 | R10 | **upstream 0.0974550987; downstream 0.03** | FIXED_UPSTREAM | heredado; `DEFAULT_THETA:147` |
| betaF0 | `betaF0` | producción de etanol desde F | h^-1 | R11,R21 | 3.4403991748 | REESTIMATED_UPSTREAM | `theta.csv` |
| sF | `sF` | parametriza KF=betaF0/sF | (g L^-1)^-1 h^-1 | R11 | **upstream 0.1782952055; downstream 0.03** | FIXED_UPSTREAM | heredado; `DEFAULT_THETA:149` |
| qEG | `qEG` | consumo G fermentativo | h^-1 | R29 | 1.7128067938 | REESTIMATED_UPSTREAM | `theta.csv` |
| qEF | `qEF` | consumo F fermentativo | h^-1 | R30 | 5.0230167502 | REESTIMATED_UPSTREAM | `theta.csv` |
| iG | `iG` | inhibición de F por G | L g^-1 | R12,R18,R21,R30,R32 | 0.0560374373 | REESTIMATED_UPSTREAM | `theta.csv` |
| iE | `iE` | inhibición por etanol | L g^-1 | R13,R17,R20,R21 | 0.0401679410 | REESTIMATED_UPSTREAM | `theta.csv` |
| Kd0 | `Kd0` | escala de muerte | h^-1 | R24,R26,R27 | 0.000150249548 | REESTIMATED_UPSTREAM | `theta.csv` |
| m0 | `m0` | mantenimiento | h^-1 | R22,R25,R29,R30 | **upstream 0.0183385794; downstream 0.01** | FIXED_UPSTREAM | heredado; `DEFAULT_THETA:155` |
| gammaG0 | `gammaG0` | formación Gly ligada a G | h^-1 | R32 | 0.1155587914 | REESTIMATED_UPSTREAM | `theta.csv` |
| gammaF0 | `gammaF0` | formación Gly ligada a F | h^-1 | R32 | 0.000100001622 | REESTIMATED_UPSTREAM | `theta.csv` |

**[CONFLICT]** “upstream fit” es el vector con el que se obtuvo el objetivo de calibración y “downstream” el vector reconstruido realmente por CO2/LAB013--018. `run_estimability_historical_by_medium.py:878-897` parte de `final.load_theta_final`; `co2_cross._load_theta:186-194` parte de `DEFAULT_THETA`.

### 13.2 Constantes upstream

| symbol/code_name | description/unit | value | equation | status/source |
|---|---|---:|---|---|
| `Cde` | coeficiente etanol en muerte, L g^-1 | 0.0415 | R24 | FIXED_CONSTANT, `base:160-172` |
| `Etd` | energía muerte, J mol^-1 | 130000 | R24 | FIXED_CONSTANT |
| `R` | constante gases, J mol^-1 K^-1 | 8.314 | R02--R24 | FIXED_CONSTANT |
| `Eac` | energía crecimiento, J mol^-1 | 59453 | R02 | FIXED_CONSTANT |
| `Eafe` | energía fermentación, J mol^-1 | 11000 | R03 | FIXED_CONSTANT |
| `EaKn`,`EaKg`,`EaKf`,`EaKig`,`EaKie` | energías, J mol^-1 | 46055 cada una | R04--R08 | FIXED_CONSTANT |
| `Eam` | energía mantenimiento, J mol^-1 | 37681 | R22 | FIXED_CONSTANT |
| `MAINTENANCE_SUGAR_CUTOFF_KG_M3` | semisaturación mantenimiento | 1.0 | R25 | FIXED_CONSTANT, `base:210` |
| `eps` | protección denominadores | 1e-8 | R09--R25 | FIXED_CONSTANT, `kinetic_terms:395` |

### 13.3 Capa CO2 natural adoptada

| symbol | code_name | description | unit | equation_where_used | value_natural_current | status | source |
|---|---|---|---|---|---:|---|---|
| k_release | `kCO2_release_h` | transferencia/liberación | h^-1 | R58 | 0.4245882714 | FITTED_CO2 | `fit_parameters.csv` |
| s_sat | `CO2sat_scale` | escala solubilidad CO2 | 1 | R56 | 0.3513895411 | FITTED_CO2 | idem; cota inferior activa |
| qO2max | `O2_qmax_mg_gdw_h` | consumo O2 | mg O2 gDW^-1 h^-1 | R39 | 0.15 | FITTED_CO2 | idem; cota inferior activa |
| sO2,0 | `O2_initial_scale` | fracción O2 inicial | 1 | R38 | 0.1953996657 | FITTED_CO2 | idem |
| t_rise | `pulse_t_rise_h` | duración rampa N | h | R44 | 64.65870375 | FITTED_CO2 | idem |
| gN | `pulse_activity_gain` | multiplicador final actividad | 1 | R48--R49 | 0.25 | FITTED_CO2 | idem; cota inferior activa |
| s | `chem_activation_start_fraction` | inicio relativo bracket | 1 | R52 | 0.7350566959 | FITTED_CO2 | idem |
| d | `chem_activation_duration_fraction` | duración relativa bracket | 1 | R52 | 1.0639098681 | FITTED_CO2 | idem |
| g_matrix | `matrix_gain` | escala observación | 1 | R62,R75 | 3.1157569444 | PROFILED | idem; `_profile_matrix_gain` |

Valores sintéticos coexistentes en el mismo artefacto, específicos de matriz: 3.8837002051, 0.4254086787, 0.1501636955, 0.3804161554, 36.50000857, 1.2333381539, 0.0100040237, 0.3500000007 y 2.1265561099, en el mismo orden.

### 13.4 Constantes, inputs y discretización CO2

| code_name | value | unit/role | equation | status/source |
|---|---:|---|---|---|
| `O2_K_MG_L` | 0.25 | mg L^-1 | R39 | FIXED_CONSTANT, `co2_cross:120` |
| `O2_ANA_K_MG_L` | 0.75 | mg L^-1 | R41 | FIXED_CONSTANT |
| `O2_ANA_HILL` | 2.0 | 1 | R41 | FIXED_CONSTANT |
| `O2_CRABTREE_FLOOR` | 0.08 | 1 | R42 | FIXED_CONSTANT |
| `CO2_G_PER_MG_O2_RESP` | (44.01/32)/1000 | g CO2 mgO2^-1 | R43 | FIXED_CONSTANT, pilot:79 |
| `CO2_CONTINUOUS_RELEASE_FLOOR` | 0.05 | 1 | R57 | FIXED_CONSTANT, `co2_cross:124` |
| `DRIVER_GRID_H` | 0.25 | h | R40,R52,R61 | FIXED_CONSTANT, `co2_cross:89` |
| solubilidad CO2 base | 1.69 | g L^-1 | R56 | FIXED_CONSTANT |
| coeficientes CO2 T/E/S | -0.032, +0.0016, -0.0012 | degC^-1, L g^-1, L g^-1 | R56 | FIXED_CONSTANT |
| solubilidad O2 base | 8.6 | mg L^-1 | R37 | FIXED_CONSTANT |
| coeficientes O2 T/E/S | -0.024, -0.0020, -0.0010 | degC^-1, L g^-1, L g^-1 | R37 | FIXED_CONSTANT |
| `temperature_c` | serie medida/reconstruida | degC | R01,R37,R56 | INPUT |
| `initials[X..Gly]` | por batch | unidades de estado | condición inicial | INPUT |
| `model_pulse_time_h`,`amount_N_kg_m3` | por batch | h, kg m^-3 | R33,R44 | INPUT |
| `44.01`, `22.414`, `V_L` | conversión artefacto | g mol^-1, L mol^-1, L | R63 | FIXED_CONSTANT/INPUT |
| `44.0095`, `24.16`, `0.74`, `2.0` | conversión holdout | varias | R64 | FIXED_CONSTANT |

### 13.5 Filas adicionales presentes en `theta.csv`

`theta.csv` también guarda `kPyrS_N`, `kPyrO2`, `kPyrDrain`, `kAldS_N`, `kAcAld`, `kAcStress`, seis constantes de síntesis de aromas y tres `alpha_*_loss`. Son `FIXED_UPSTREAM` en el artefacto, pero **no son consumidos por `base.rhs`, `build_driver_cache`, `effective_qprod_grid` ni `raw_qgas_grid_prediction`**. Por ello no forman parte de las 75 relaciones de la cadena central+CO2 aquí reconstruida y no deben presentarse como ecuaciones del observable CO2 actual.

## 14. Notebook vs código ejecutado

| equation_id | notebook/cell | markdown_equation | executed_function | code_location | status | notes |
|---|---|---|---|---|---|---|
| U01 | upstream c0 | F=J^T J | FIM del runner | `run_estimability_historical_by_medium.py:899-907` | MATCH | ecuación de estimabilidad, no de dinámica |
| C01 | CO2 c1 | b=max(0,Q0.10) | `apply_sensor_zero_correction` | `co2_cross:583-663` | MATCH | ventana 12 h |
| C02 | CO2 c1 | ycorr=max(y-b,0) | idem | idem | MATCH | exacta |
| C03 | CO2 c1 | ts=L+fs(U-L) | `_bounded_smoothstep_activation` | `co2_cross:1369-1376` | MATCH | exacta |
| C04 | CO2 c1 | Delta t=fd(U-L) | idem | `co2_cross:1372-1375` | MISMATCH | código usa max(fd(U-L),0.25 h) |
| C05 | CO2 c1 | achem=3z^2-2z^3 | idem | `co2_cross:1375-1380` | MATCH | equivalente a z^2(3-2z) |
| C06 | CO2 c1 | dO2/dt=-qmax X O2/(K+O2) | `effective_qprod_grid` | `co2_cross:1711-1722` | PARTIAL_MATCH | Euler + max a cero; X es Xeff de la rampa |
| C07 | CO2 c1 | phi anaeróbica Hill | `effective_qprod_grid` | `co2_cross:1723-1725` | MATCH | exacta |
| C08 | CO2 c1 | qprod=A[qbio fferm+qresp] | `effective_qprod_grid` | `co2_cross:1726-1745` | MATCH | exacta |
| C09 | CO2 c1 | fN=clip((t-tN)/trise) | `_pulse_utilization_fraction` | `co2_cross:1653-1665` | MATCH | exacta |
| C10 | CO2 c1 | qbio,N=[1+(g-1)f]q0+f(q+N-q0) | `effective_qprod_grid` | `co2_cross:1698-1705` | MATCH | exacta |
| C11 | CO2 c1 | biomasa misma diferencia sin gN | idem | `co2_cross:1693-1697` | MATCH | relación textual exacta |
| C12 | CO2 c1 | Cstar correlación | cache/pilot | `co2_cross:1429-1438,1776` | MATCH | exacta |
| C13 | CO2 c1 | dC/dt=qprod-qgas | `raw_qgas_grid_prediction` | `co2_cross:1777-1800` | PARTIAL_MATCH | ejecutado como Euler explícito R61 |
| C14 | CO2 c1 | qgas continuo | idem | `co2_cross:1781-1800` | PARTIAL_MATCH | forma física coincide; Markdown omite índices, máximos y eps |
| C15 | CO2 c1 | comparador k softplus(C-Cstar) | rama threshold | `co2_cross:1573-1579,1796-1798` | MATCH | no nominal, sí comparador ejecutado |
| L13-01 | LAB013 c5 | HS=G+F | residual celda 20 | notebook c20 | MATCH | suma exacta |
| L13-02 | LAB013 c17 | Ck=max(Ck-1+dt(qprod-qgas),0) | wrapper celda 18 | notebook c18 | MATCH | reproduce R61 |
| L13-03 | LAB013 c45 | log theta(lambda) convexa | diagnóstico celda 24 | notebook c24 | MATCH | no modifica modelo |
| L13-04 | LAB013 c53 | 0.489(Si-Sf) | diagnóstico balance | notebook c28 | DOCUMENTATION_ONLY | referencia diagnóstica, no cadena del modelo |
| H01 | LAB016 c25 | qshift(t)=qpred(t-Delta) | `shifted_prediction_at` | notebook c26 | MATCH | diagnóstico no predictivo |
| H02 | LAB016 c30 | Xobs=C*Viability/100*0.03 | `align_oculyze_report` | notebook c31 | MATCH | exacta |
| H03 | LAB016 c36 | ts=L+sB | smoothstep importado | `co2_cross:1372-1374` | MATCH | exacta |
| H04 | LAB016 c36 | D=max(dB,grid) | smoothstep importado | `co2_cross:1374` | MATCH | corrige omisión del notebook CO2 |
| H05 | LAB016 c36 | z y A=z^2(3-2z) | smoothstep importado | `co2_cross:1375-1380` | MATCH | exacta |
| H06 | LAB016 c36 | qprod=A[qbio fferm+qresp] | `effective_qprod_grid` | `co2_cross:1742-1745` | MATCH | exacta |
| H07 | LAB016 c36 | release C/(C+Csat), piso 0.05 | `raw_qgas_grid_prediction` | `co2_cross:1789-1800` | MATCH | texto completo y exacto |
| H08 | LAB016 c48 | DeltaN=0.14 protocolo | diagnóstico c29--30 | notebook c29--30 | MATCH | no pertenece al holdout estricto |
| K01 | sin Markdown | siete ODE | `base.rhs` | `base:445-468` | CODE_ONLY | importadas por todos los notebooks |
| K02 | sin Markdown | Arrhenius/limitaciones/muerte | `kinetic_terms` | `base:387-442` | CODE_ONLY | necesarias para ODE |
| K03 | sin Markdown | O2sat y O2 inicial | pilot/cache/effective | pilot:271-288; co2:1711 | CODE_ONLY | no ecuación en notebook CO2 |
| K04 | sin Markdown | qresp | `effective_qprod_grid` | `co2_cross:1727` | CODE_ONLY | coeficiente 44.01/32/1000 |
| K05 | sin Markdown | qobs=matrix_gain*qgas | `predict_and_score` | `co2_cross:2481` | CODE_ONLY | función final |
| K06 | sin Markdown | conversión 22.414 | `_sccm_to_g_l_h` | `co2_cross:555-557` | CODE_ONLY | calibración histórica |
| K07 | texto sin fórmula | conversión 24.16*0.74 | celda 17 | holdout c17 | CODE_ONLY | incompatibilidad activa |
| K08 | sin Markdown | clips estados/no negatividad | `kinetic_terms`,`simulate` | `base:387-392,581-585` | CODE_ONLY | afecta resultado numérico |

Conteo: MATCH 23; MISMATCH 1; PARTIAL_MATCH 3; DOCUMENTATION_ONLY 1; CODE_ONLY 8.

## 15. Conflictos y ramas activas

### 15.1 Parámetros fijos perdidos al serializar theta

| parámetro | usado al generar theta natural | usado al regenerar drivers CO2/holdout | cociente downstream/upstream |
|---|---:|---:|---:|
| sN | 8.751445871 | 18.0 | 2.0568 |
| qXG | 0.081490986 | 0.1125 | 1.3805 |
| qXF | 0.070932707 | 0.1125 | 1.5854 |
| sG | 0.097455099 | 0.03 | 0.3078 |
| sF | 0.178295206 | 0.03 | 0.1683 |
| m0 | 0.018338579 | 0.01 | 0.5453 |

Esto no es una hipótesis: se deduce de `final.load_theta_final` -> `joint.load_reference_theta` (primera ruta existente `theta_multistart_07.csv`) frente a `_load_theta` (`DEFAULT_THETA` + filas de `theta.csv`). LAB013 celda 8 repite explícitamente la segunda lógica.

### 15.2 Ramas de resultados

- **Calibración upstream natural:** forma R01--R33; 11 parámetros ajustados; seis fijos heredados; pulso 0.08.
- **Calibración CO2 natural y sus resultados:** misma forma upstream, pero seis fijos `DEFAULT_THETA`; pulso 0.14 y tiempos por densidad; R34--R65; parámetros CO2 ajustados.
- **LAB013--015 escenario A:** mismos defaults downstream + 11 valores de `theta.csv`; sin pulso. Escenario B cambia los 11 nombres a valores literales congelados; no es el artefacto canónico `theta.csv`.
- **LAB016--018 estricto:** mismos defaults downstream + `theta.csv`; sin pulso; ICs proxy/escenario; bracket `[0,0]` activa A=1 desde t=0; observación con R64.
- **Diagnósticos LAB016--018:** usan CO2 observado para mover el gate o dosis asumidas; se ejecutaron, pero están marcados como no holdout y no constituyen una calibración canónica.

## 16. MODELO ACTUAL REALMENTE IMPLEMENTADO

En orden de reproducción conceptual:

**A. Estados upstream:** `y=(X,Xd,N,G,F,E,Gly)` con IC por batch y no negatividad.

**B. Tasas cinéticas:** R01--R25, incluida temperatura interpolada, saturaciones, inhibiciones, mantenimiento y muerte piecewise.

**C. ODE upstream:** R26--R32.

**D. Dependencia de temperatura:** R01--R13 y R22--R24.

**E. Eventos discretos:** R33 con orden muestra-antes-de-acción. La dosis depende de la rama (0.08 upstream, 0.14 CO2).

**F. Producción biológica de CO2:** R34--R36; N no entra directamente en betaG/betaF.

**G. Activación:** R50--R54; bracket químico futuro y smoothstep; fallback escalón.

**H. O2:** R37--R43; pool Euler separado, sin kLa, Monod, Hill anaeróbico, piso Crabtree y CO2 respiratorio.

**I. Respuesta nutricional:** R44--R49, basada en dos simulaciones upstream y una rampa causal permanente.

**J. Solubilidad CO2:** R56.

**K. Pool CO2 disuelto:** R61, inicial cero, Euler 0.25 h.

**L. Liberación gaseosa:** R57--R60, incluidos 0.05/0.95 y limitador disponible.

**M. Observación final:** R62; observación experimental convertida por R63 o R64 según pipeline.

**N. Observaciones offline:** R66--R74. Brix, densidad y DO de LAB016--018 no tienen función de observación validada en el pipeline estricto.

## 17. NO IMPLEMENTADO ACTUALMENTE

| elemento discutido | IMPLEMENTED | evidencia |
|---|---|---|
| estado metabólico causal `a(t)` en el ODE central | NO | solo propuesta en documentación previa |
| estados `Nx`, `Ntr`, `Tr` | NO | no aparecen en `STATE_NAMES`, `rhs` ni capa CO2 |
| O2 como estado del ODE central | NO | es pool interno Euler de la capa CO2 |
| CO2 disuelto como estado de `base.rhs` | NO | es pool interno Euler posterior |
| gate causal de onset | NO | el gate actual usa química futura; diagnósticos usan CO2 observado |
| transitorio nutricional rise--decay | NO | solo sensibilidad manual del holdout, celda 40+ |
| terminación lenta independiente del pulso | NO | no existe término separado |
| separación PAN/amoniacal dentro del estado N | NO | N es YAN escalar |
| función Brix/densidad -> G/F validada para holdout | NO | notebook LAB016--018 la excluye explícitamente |
| múltiples pulsos en `build_driver_cache` | NO | lanza error si hay más de uno; `base.simulate` sí los soporta |

## 18. Control de calidad

- [x] Siete ODE upstream transcritas sin simplificación oculta.
- [x] Auxiliares, Arrhenius, inhibiciones, piecewise, eps y clips documentados.
- [x] Pulso N, contrafactual con/sin pulso y conflicto 0.08/0.14 documentados.
- [x] O2, activación, solubilidad, pool, `qgas` y `qobs` documentados con discretización real.
- [x] Markdown relevante contrastado con el código ejecutado.
- [x] Ecuaciones obsoletas separadas como comparadores o no implementadas.
- [x] Valores extraídos de artefactos versionados; no se ejecutó fitting.
- [x] Notebook CO2 fuente y ejecutado tienen fuentes de las 30 celdas idénticas.
- [x] Se identificó el notebook upstream real y su versión ejecutada.

## 19. Rutas auditadas

Núcleo: `shared/run_new_must_glycerol_estimability_doe.py`, `shared/new_must_data_loader.py`, `laboratory_2026/run_estimability_historical_by_medium.py`, `laboratory_2026/run_estimability_old_vs_lot1.py`, `laboratory_2026/run_final_operational_doe_v2.py`, `laboratory_2026/run_co2_matrix_cross_validation_2026.py`, `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py`, `shared/run_secondary_joint_campaign_doe.py`.

Artefactos: `laboratory_2026/results/estimability_historical_natural/theta.csv`, `batch_summary.csv`, `measurement_support.csv`, `laboratory_2026/results/co2_matrix_cross_validation_2026/fit_parameters.csv`, `driver_diagnostics.csv`, `natural_nutrient_pulse_details.csv`, `effective_nutrient_pulses.csv`, `analysis_manifest.json`, y el artefacto heredado `shared/results/new_must_glycerol_overnight_validation/theta_multistart_07.csv` requerido para reconstruir el vector que realmente alimentó la calibración upstream.
