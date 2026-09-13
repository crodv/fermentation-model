# Suite de análisis de calibración de la capa CO₂ — referencia metodológica

**Qué es**: documentación de los TIPOS de análisis que componen la calibración/validación de la capa
CO₂, su propósito y qué permiten juzgar de una calibración. No registra resultados de ninguna corrida.
**Fuente analizada**: `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.ipynb` (SOURCE)
y su copia EXECUTED; toda la lógica vive en el runner autoritativo
`laboratory_2026/run_co2_matrix_cross_validation_2026.py` (`co2x`). El notebook solo orquesta
(`analysis.run_analysis(...)`) y muestra tablas/figuras vía funciones `analysis.plot_*`.
**Aplica a**: futuras recalibraciones de la capa CO₂ (incluida la variante SCCM corregida).

> **Advertencia de conversión**: la versión 2026 documentada aquí usó la conversión LEGACY
> (1 SCCM ≈ 0.05890515 g·L⁻¹·h⁻¹, sin K=0.74) y se conserva inmutable por reproducibilidad.
> Toda calibración NUEVA debe usar `SCCM_CORRECTED` (0.0404392 g·L⁻¹·h⁻¹·SCCM⁻¹; ver
> PROJECT_CONTEXT) y comparar contra los artefactos de
> `results/co2_matrix_cross_validation_2026_sccm_corrected/`, no contra los LEGACY.

## 1. Estructura general del pipeline

```
CO2 crudo por canal (SCCM) + química (workbook) + temperatura + protocolo
   ↓ [pre-proceso]  cero de sensor por corrida → reparación de artefactos/transientes
   ↓                filtrado (mediana 3 h + Savitzky–Golay cuadrático 5 h) → obs horarias
   ↓                banderas de censura (señal bajo umbral operacional local)
   ↓ [diseño]       split por fermentación completa: calibración vs holdout por matriz
   ↓ [drivers]      upstream ODE cinético (θ congelado) → q_bio etc.; pulso de N como
   ↓                diferencia causal de simulaciones con/sin adición
   ↓ [fitting]      multistart por matriz de los parámetros de la capa CO₂
   ↓ [diagnóstico]  identificabilidad, perfiles, leave-one-batch-out
   ↓ [validación]   holdout por matriz + transferencia cruzada sin reajuste
   ↓ [comparación]  vs modelo comparador (liberación por umbral) y crudo vs filtrado
   ↓ [artefactos]   tablas CSV, figuras, predicciones y manifiesto en results/
```

Los análisis se dividen en **pre-proceso** (condicionan el ajuste, no dependen de parámetros),
**fitting** y **diagnósticos posteriores**.

## 2. Grupos de análisis

### A. QC del sensor y pre-proceso de señal (pre-fit; sin dependencia de parámetros)

- **Cero de sensor por corrida**: percentil 10 de las primeras 12 h de la señal nativa, estimado
  por corrida (los canales derivan entre campañas). *Evalúa*: deriva/offset instrumental.
  *Tabla*: offsets por sensor/corrida; señal antes/después. *Figura*: corrección de cero.
  Limitación conocida: si hay flujo biológico real en toda la ventana, sustrae señal verdadera →
  reemplazable por blancos de gas (ver §4).
- **Reparación de artefactos y transientes de muestreo**: excursiones asociadas a eventos de
  muestreo se reconstruyen solo con respaldo pre/post consistente. *Tabla* QC: artefactos
  reemplazados, transientes, fracción negativa, censura izquierda, horas de baja sensibilidad en
  frío, razones de suavizado (rugosidad/integral/pico). *Evalúa*: calidad de la observación, no
  del modelo. *Figuras*: overview de datos, ejemplos de filtrado.
- **Censura izquierda**: puntos bajo el umbral operacional local (0.10 g/L/h a setpoint ≤15.5 °C;
  0.05 en el resto — operacional, no LOD/LOQ certificado) entran como penalización unilateral si el
  modelo los excede. *Diagnostica*: coherencia del modelo con el límite del sensor.

### B. Alineación de drivers externos (pre-fit; inputs, no calibrados)

- **Temperatura medida/reconstruida vs setpoint**: entra a los drivers cinéticos y a la
  solubilidad. *Tablas*: estadísticos por lote, alineación temporal. *Figura*: perfiles.
- **Bracket químico de activación**: primera muestra con Δ(G+F) ≥5 g/L o ΔE ≥2 g/L fija el
  extremo superior del intervalo admisible de encendido; la muestra anterior fija el inferior.
  *Tabla*: bracket por lote. *Evalúa*: cuánta libertad tiene la activación por lote (un bracket
  ancho = incertidumbre de tiempo de encendido).
- **Timing del pulso de N**: en LAB, interpolación del cruce de densidad 1040 g/L; en DOE, tiempo
  de proceso registrado. *Tabla* de pulsos con fuente de timing y dosis. *Figura*: alineación de
  línea de tiempo de proceso. *Diagnostica*: consistencia protocolo ↔ señal ↔ química antes de
  ajustar nada.

### C. Calibración por matriz (fitting)

- **Multistart por matriz** (parámetros compartidos dentro de cada matriz; holdout excluido del
  ajuste). Objetivo: residuos del perfil completo + residuo del tiempo de inicio + desfase del
  máximo post-pulso (72 h) en lotes pulsados, con ponderación igualada por batch (`wsse_equal_batch`)
  y penalización de censura.
- *Tablas*: parámetros ajustados (con `active_bound`), mejor multistart por matriz. *Figuras*:
  comparación de parámetros entre matrices; overlays predicción vs observación por lote.
- **Lectura clave**: `active_bound=True` = el dato solo acota el parámetro en el borde → tensión
  estructural o falta de identificabilidad, NO una estimación interior resuelta. Siempre reportar.

### D. Identificabilidad y estabilidad de parámetros (post-fit)

- **Jacobiano local en log-parámetros**: número de condición alto = direcciones compensables.
- **Correlaciones locales** entre pares de parámetros (foco en el par de activación).
- **Perfiles del objetivo**: fijar uno de los parámetros de activación y reoptimizar todo lo demás.
- **Leave-one-batch-out**: re-estimar sin una fermentación completa y medir cuánto se mueve la
  estimación (franja de variabilidad; la línea de 5 % del objetivo es descriptiva, no un IC).
- *Evalúa*: si los parámetros calibrados están identificados por los datos o solo cofijados.
  Una calibración con buen RMSE pero parámetros en borde/correlacionados/inestables a LOO no está
  "resuelta".

### E. Diagnóstico del inicio y de la respuesta al pulso (post-fit; específico del fenómeno bajo estudio)

- **Definiciones operacionales**: onset observado = 3 puntos horarios consecutivos sobre
  max(límite de detección local, línea base +10 % del rango dinámico); primera emisión sostenida
  >0.005 g/L/h; duración visual del ascenso 2–10 %.
- **Tabla de transición de fuente**: onset observado vs predicho y su retraso, término del pulso,
  máximo post-pulso observado vs predicho y su desfase.
- *Figuras*: zoom del inicio por lote (comparador umbral vs liberación continua), comparación de
  error de onset entre modelos, zoom de lotes pulsados (marcando adición y fin de disponibilidad).
- *Evalúa*: si la estructura de activación/liberación corrige la cola inicial artificial y si el
  pulso de N produce una respuesta finita y con el timing correcto (actividad ≠ biomasa).

### F. Validación retenida y transferencia cruzada (post-fit; juicio principal de la calibración)

- **Escenarios**: (1) ajuste→holdout de la misma matriz (LAB012 natural, lot2_F3 sintético);
  (2) modelo de una matriz aplicado a la otra SIN reajuste (transferencia retrospectiva).
- *Métricas por escenario/batch*: RMSE, NRMSE normalizado por pico, sesgo, correlación, R², razón
  de integrales pred/obs (cota inferior consciente de censura), error de onset, error de duración
  de ascenso, desfase del máximo post-pulso, n censurado.
- *Figuras*: validación por escenario; comparación de validación entre modelos.
- *Diagnostica*: capacidad predictiva fuera del ajuste y transferibilidad de la parametrización de
  la capa CO₂ entre matrices. El error de holdout, no el de calibración, es el criterio de
  aceptación primario.

### G. Comparación de decisiones de modelación (post-fit)

- **model_comparison**: modelo actual (liberación continua con piso sub-saturado f₀) vs comparador
  directo (liberación por umbral softplus) sobre EXACTAMENTE los mismos holdouts y misma respuesta
  al pulso. Columnas de cambio (`*_change_*`): negativo = mejora.
- **filter_impact**: ajuste con señal cruda vs filtrada sobre el mismo soporte cuantificable →
  separa el aporte del pre-proceso del aporte del modelo.
- *Evalúa*: si una decisión estructural (o de pre-proceso) mejora de verdad, evitando atribuir al
  modelo lo que es del filtrado.

### H. Resumen por fermentación y veredicto operativo (post-fit)

- **batch_metrics**: tabla completa por lote con rol (calibración/holdout/transferencia) y todas
  las métricas de E/F. *Es la tabla de lectura principal para detectar lotes problemáticos.*
- **Resumen reproducible**: una línea por escenario + advertencia de parámetros en borde + cambios
  medios nuevo-vs-anterior (onset, RMSE, duración, pico post-pulso). *Sirve como veredicto
  compacto y comparable entre corridas.*

## 3. Dependencias (qué se rompe si cambia qué)

- **Dependen del θ cinético (upstream congelado)**: todos los análisis que simulan (overlays,
  validación, onset predicho, respuesta al pulso, C* por T/E/azúcares, qprod pico de referencia).
  El notebook es una validación de la capa CO₂ **condicionada** por los drivers upstream: cambiar
  θ (p. ej., resolver la inconsistencia de los 6 parámetros congelados) invalida todas las
  predicciones y exige re-ejecutar la suite completa, no solo el fitting de CO₂.
- **Dependen de los parámetros calibrados de CO₂** (`kCO2_release_h`, `CO2sat_scale`,
  `O2_qmax_mg_gdw_h`, `O2_initial_scale`, `pulse_t_rise_h`, `pulse_activity_gain`,
  `chem_activation_start_fraction`, `chem_activation_duration_fraction`, `matrix_gain`): C–H.
- **Independientes de parámetros**: A y B (solo datos + química + protocolo). Son reutilizables
  tal cual entre calibraciones.

## 4. Qué mantener en una nueva versión del notebook (parámetros actualizados)

Mantener completa la suite A–H (es el estándar de juicio de una calibración de CO₂):

1. A y B sin cambios (misma señal, misma química; solo cambia la conversión SCCM).
2. C con los nuevos parámetros, mismo protocolo de multistart/split/holdout.
3. D obligatorio: toda recalibración debe demostrar identificabilidad y estabilidad LOO.
4. E y F obligatorios: onset/pulso y holdout+transferencia son los criterios de aceptación.
5. G adaptado al comparador relevante de la nueva versión (el comparador "anterior" debe ser la
   mejor versión previa, evaluada en los mismos holdouts).
6. H como cierre; regenerar artefactos y manifiesto en un directorio de results/ nuevo
   (no sobrescribir la corrida anterior).
7. Actualizar el encabezado de conversión (SCCM_CORRECTED) y las constantes documentadas en el
   notebook; NUNCA editar el notebook LEGACY para "actualizarlo": crear versión nueva.
8. Mantener la convención SOURCE/EXECUTED del repo: SOURCE canónico sin outputs; EXECUTED desde
   kernel limpio, 0 errores, código y markdown idénticos (verificado en la revisión de este doc).

## 5. Limitaciones documentadas y experimentos propuestos (de la propia suite)

- Umbral operacional ≠ LOD/LOQ: para separar sensor de biología se propuso un ensayo a 15/18/21 °C
  con escalones 0.01–0.30 g CO₂·L⁻¹·h⁻¹ y referencia independiente (LOD, LOQ, sesgo,
  repetibilidad, tiempo de respuesta).
- El cero por percentil es operacional: reemplazar por blancos de gas sin fermentación al
  inicio/fin de cada corrida y canal.
- El bracket químico solo identifica un intervalo de activación; muestreo químico frecuente en las
  primeras 48–72 h (especialmente en frío) lo estrecharía.
