# Historial de modificaciones realizadas por agentes

Registro breve de cambios implementados por agentes en el repositorio.

### 2026-10-07 17:20 HSP

- Archivos: `laboratory_2026/notebooks/EKF/ekf_general_block_diagram.ipynb` (+ `.executed.ipynb` y `ekf_general_block_diagram.png`, regenerados)
- Cambio: se rehízo por completo el diagrama de bloques del EKF en el mismo notebook: flujo desde INICIO con bloque de inicialización explícito (x̂₀, P₀, Q, R), predicción dividida en dos bloques (estado por f / incertidumbre por el Jacobiano F), actualización con los 7 pasos numerados (h, H, innovación, S, ganancia, corrección, Joseph), by-pass sin medición, lazo k→k+1 y un panel "mapa de matrices" al pie con todas las cantidades por familia (declaradas / fabricadas / calculadas / fuera del algoritmo). Aceptado visualmente tras dos rondas de corrección de colisiones de texto.

### 2026-10-06 19:26 HSP

- Archivos: `laboratory_2026/notebooks/lab013_015_natural_must_co2_model_analysis.ipynb`
- Cambio: figura diagnóstica de la sección 6 rehecha como grilla 2x3 (CO2 gaseoso arriba, temperatura del logger filtrada abajo, una columna por lote, rango completo 0–192 h), sin leyendas, sin línea de corte y sin texto de exclusión. La temperatura (`Temp_{F1,F2,F3}_{LAB}.csv`) se filtra con el mismo esquema de `lab019_021_theta_full_holdout` (mediana 1min -> mediana móvil centrada 20min -> media móvil centrada 45min), parámetros documentados en markdown y código. `gas_reference` sigue truncado a la ventana offline; celda 14 re-ejecutada en kernel limpio y markdown 13 actualizado.

### 2026-10-06 18:37 HSP

- Archivos: `laboratory_2026/notebooks/lab013_015_natural_must_co2_model_analysis.ipynb`
- Cambio: la figura diagnóstica de CO2 gaseoso (sección 6) ahora muestra el rango completo de adquisición de los sensores (0–192 h) en vez de cortarse en la ventana offline (~143.5 h); se marca con línea punteada el fin de la ventana offline. `gas_reference` sigue truncado a la ventana offline, por lo que la capa de diagnóstico (sección 16) y los checks finales quedan sin cambio. Celda 14 re-ejecutada en kernel limpio y markdown 13 documentado.

### 2026-10-06 09:48 HSP

- Archivos: `laboratory_2026/notebooks/EKF/ekf_general_block_diagram.ipynb` (+ `.executed.ipynb` y `ekf_general_block_diagram.png`)
- Cambio: nuevo folder `laboratory_2026/notebooks/EKF/` con notebook standalone (SOURCE + EXECUTED) que genera con matplotlib un diagrama de bloques general del ciclo EKF (predicción/actualización, Jacobianos F y H por linealización, by-pass sin medición, lazo k→k+1 e inicialización), sin referencia al caso de fermentación; la figura se guarda como PNG para reutilizar en la memoria.

### 2026-09-19 01:07 HSP

- Archivos: `docs/current_model_equations_audit_2026/`, `docs/modelo_fermentacion_CO2_EKF_2026/`, `docs/natural_must_model_calibration_and_estimator_readiness_2026/`, `docs/planning/proximos_lotes_mosto_natural_2026/`
- Cambio: reorganización de `docs/`: cada `.tex` se movió a su propia carpeta junto con su PDF y auxiliares de compilación (`current_model_equations_audit_2026.tex` + `current_model_equations_090926.pdf`; `modelo_fermentacion_CO2_EKF_2026.tex` solo; `natural_must_..._2026.tex` + `.pdf` + `.synctex.gz`; `proximos_lotes_mosto_natural_2026.tex`). Los `.md`/`.xlsx` homónimos se mantuvieron en su ubicación original por estar referenciados por ruta desde notebooks y otros documentos.

### 2026-09-14 16:48 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_pulse_inconsistency_review.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_pulse_inconsistency_review.executed.ipynb`
- Cambio: nuevo notebook de diagnóstico (SOURCE + EXECUTED) que audita la inconsistencia del pulso de N entre el modelo cinético upstream (fila `pulso_nut` del workbook, 0.08 kg/m³) y la capa CO2 (cruce de densidad 1040 + dosis de protocolo 0.14 kg/m³) para LAB004–LAB012, incluido LAB009. Verifica origen t=0 común, reproduce `natural_nutrient_pulse_schedule` contra `effective_nutrient_pulses.csv`, y entrega tabla resumen por lote y 3 figuras multipanel (CO2+N combinado, CO2 global, N global). Solo diagnóstico: sin recalibración ni cambios de tiempos/dosis; sin artefactos CSV/PNG adicionales.

### 2026-09-14 21:48 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.executed.ipynb` (movidos desde `laboratory_2026/notebooks/`, que antes existía como archivo único con outputs)
- Cambio: se reorganizó el análisis de retardo del filtro CO2 al esquema SOURCE (sin outputs) / EXECUTED y se movió a `notebooks/diagnostics/`. Se agregaron a las figuras RAW vs FILT las líneas verticales del pulso 2 de N según ambas convenciones — `Pulso_nut planilla (upstream)` (verde continua, desde la columna `pulso_nut` del workbook) y `Cruce densidad 1040 (capa CO2)` (roja discontinua, desde `effective_nutrient_pulses.csv` de la corrida congelada) — llevadas al eje temporal vía el t=0 del lote; LAB001–003 sin registro de pulso quedan sin líneas. No se modificó el cálculo de retardos ni se corrigió el delay en la calibración.

### 2026-09-14 22:03 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.executed.ipynb`
- Cambio: se agregó al final de la sección 4.1 una figura global multipanel (LAB004–LAB012) con RAW original, RAW robust/suavizado y FILT **sin compensar**, convertidos a g/L/h con la conversión definitiva `SCCM_CORRECTED` (0.0404391928807947 g/L/h por sccm a 2 L, leída de `analysis_manifest.json`), incluyendo las líneas del pulso 2 de N de ambas convenciones (`Pulso_nut planilla (upstream)` y `Cruce densidad 1040 (capa CO2)`) y el Δt por lote en los títulos. Ejecución completa regenerada: 19/19 celdas de código, cero errores.

### 2026-09-14 22:20 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_filter_delay_analysis_lab2026.executed.ipynb`
- Cambio: se agregó la sección 4.3 con la figura de temperaturas de LAB004–LAB012 (mismo estilo que los perfiles del cross-matrix, sin DOE): T medida (mediana 30 min, input del modelo) y setpoint desde `process_temperature_30min.csv`, con ambas líneas de pulso de N. Documentado en el notebook que la temperatura no lleva filtro Hampel/Butterworth ni corrección de offset — solo remuestreo por mediana a 30 min y posterior interpolación lineal al grid del modelo con fallback nominal. Ejecución regenerada: 20/20 celdas de código, cero errores.

### 2026-09-20 20:33 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `docs/planning/planificacion_LAB019_021_replica_lote2_2026.tex`, `docs/planning/planificacion_LAB019_021_replica_lote2_2026.pdf` (PDF compilado del .tex); eliminados los planes previos `planificacion_proximas_fermentaciones_natural_2026.xlsx`, `proximos_lotes_mosto_natural_2026.xlsx` y `proximos_lotes_mosto_natural_2026/`
- Cambio: nueva planificación de la réplica del Lote 2 (LAB019=F1/A, LAB020=F2/A, LAB021=F3/C) con inicio lunes 21/09/2026 16:00 (t0 = fin de inoculación automatizada), construida desde los parámetros ejecutados reales de LAB004–006 (`Eventos_operacion`/`Perfiles_temperatura`: pulsos 2 a t=51/75 h, setpoints a t=99/171/123/219 h) y la cinética original (A seca t≈122–146 h, C t≈170–194 h). Cronograma con ventanas laborales (lun–jue 8:30–12:30/14:30–16:45, vie 8:30–11:30), muestreo con separación ≥6.5 h intra-día (PI + 15 eventos), eventos automáticos por bomba, criterios de término y contingencias. Excel validado (audit/scan/validate sin hallazgos, sin fórmulas); LaTeX compilado sin errores/overfull y aceptado visualmente (5/5 páginas).

### 2026-09-20 21:29 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `.tex`, `.pdf` (actualizados); `docs/planning/registro_muestras_LAB019_021_2026.xlsx`, `.tex`, `.pdf` (nuevos)
- Cambio: planificación v2 — (a) visitas de muestreo de tarde movidas de 15:00 a 14:30 porque cada visita demora ~1.5–2 h de procesamiento (término ~16:30, margen antes de la limpieza de 17:00); (b) DO agregado a todas las muestras; (c) Carbodoseur (CO2 disuelto, ~100 mL/lectura) en 7 eventos fijos (PI, -01, -02, -05, -06, -09, -14) + -15 condicional, elegidos para observar el pool de CO2 disuelto: IC real (≠0), discriminación threshold vs continuous release y validación de Csat(T) en los cambios de setpoint; (d) presupuesto de volumen documentado (~0.7–0.8 L/reactor en Carbodoseur). Nueva planilla de registro (Excel + LaTeX/PDF): 16 bloques (uno por muestra) con hora real, filas F1/F2/F3 y columnas Brix/densidad/T/OD/volumen remanente Carbodoseur/CO2 disuelto de tabla/notas; Oculyze excluido (queda en su software). Validación: ambos Excel passed (audit/scan/validate), ambos PDF sin errores/overfull y aceptados visualmente (plan 6/6, registro 6/6 tras corregir cortes de bloque entre páginas con minipage).

### 2026-09-20 21:52 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `.tex`, `.pdf`; `docs/planning/registro_muestras_LAB019_021_2026.xlsx`, `.tex`, `.pdf`
- Cambio: planificación v3 — se agregó MINI-MUESTRA -02B el martes 22/09 11:45 (t=19.75 h; solo Carbodoseur + densidad/Brix/DO, sin Y15/Oculyze/Alcolyzer, ~15-20 min) para tener tres puntos del pool de CO2 disuelto el día del onset (16.5/19.75/22.5 h); con ello el conteo de lecturas Carbodoseur pasa a 8 fijas + -15 condicional (~0.8-0.9 L/reactor, ~65-75% del batch) y la planilla de registro pasa a 17 bloques. Corregido además el horario de MUESTRA -03 (15:00→14:30) para restaurar la coherencia de las visitas de tarde con el diseño v2. Validación: ambos Excel passed (audit/scan/validate); ambos PDF sin errores/overfull y aceptados visualmente (plan 6/6 tras corregir errata en pág. 3; registro 6/6 tras eliminar rellenos grises que tapaban las reglas horizontales).

### 2026-09-21 11:05 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`, `.tex`, `.pdf`; `docs/planning/registro_muestras_LAB019_021_2026.xlsx`, `.tex`, `.pdf`
- Cambio: rediseño de la réplica por decisión del laboratorio — ya no replica el Lote 2 completo (LAB004-006) sino LAB004 (Protocolo A, F1), LAB006 (Protocolo C, F2) y LAB009 (Protocolo A, F3, grupo 17/04 sin registro Maestro). Eventos automáticos por fermentador según su original: pulsos 2 a t=48 h (F3, vía ICS; sin registro en workbook; densidad cruzó 1040 ~t=44 h), 51 h (F1) y 75 h (F2); setpoints F3 21 °C@96 h y 16 °C@168 h (inferido en original), F1 99/171 h, F2 123/219 h. Muestreo rediseñado a 22 eventos: t0 hoy lunes (PI + -01), mar-jue 4 muestreos/día (08:30 y 14:30 completas + minis 11:15/16:40 solo instrumental), vie 2 (08:30 + mini 11:00), semana siguiente cola liviana (lun ×2, mar ×1, mié ×2, jue condicional). Carbodoseur: 11 lecturas fijas + 1 condicional (~1.0-1.1 L/reactor; presupuesto 75-85% del batch con orden de suspensión documentado); 4 puntos el martes (16.5/19.25/22.5/24.7 h) cubren la trayectoria del pool hasta el onset esperado de A (24-30 h según loggers de abril, 22-24 h en LAB016-018). Planilla de registro a 22 bloques. Validación: ambos Excel passed (audit/scan/validate); planificación 7/7 páginas y registro 8/8 aceptadas visualmente (corregidas columna de la condicional -21 a F2, nota al pie -15→-21 y paginación final).

### 2026-09-22 10:47 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_v2_2026.xlsx`, `.tex`, `.pdf`; `docs/planning/registro_muestras_LAB019_021_v2_2026.xlsx`, `.tex`, `.pdf`
- Cambio: nueva versión v2 de la planificación y de la planilla de registro (archivos `_v2` nuevos, sin borrar los anteriores) con el horario de muestreo redefinido por el laboratorio: mar-jue 09:00 / 12:00 (mini instrumental) / 15:00 + intermedia opcional martes 16:45 (t=24.75 h, discrimina threshold vs continuous), viernes 09:00 + 11:00, lunes PI 15:30 + t0 16:10 (20 eventos; Carbodoseur 10 fijas + 1 condicional). Setpoints y pulsos 2 en múltiplos de 12 h desde t0, de modo que todos los eventos automáticos caen a las 16:00: F1 (A) 48/96/168 h, F2 (C) 72/120/216 h, F3 (B) 48/72 h con inicio 21 °C→18 °C y segundo cambio omitido (perfil real del logger de LAB009); se incluyó nota de auditoría homologación-vs-logger de LAB009 (perfil invertido usado por θ_natural, etiquetas LAB007/LAB009 intercambiadas). Validación: ambos Excel passed (audit/scan/validate); ambos PDF sin errores ni overfull y aceptados visualmente (planificación 8/8 tras corregir el anclaje de tablas con [h]/[H]+needspace; registro 7/7).

### 2026-09-22 11:19 -03

- Archivos: `README.md`, `REPOSITORY_MAP.md`, `docs/work_state/PROJECT_CONTEXT.md`
- Cambio: se documentó la trazabilidad de theta y se actualizaron los endpoints principales para distinguir la variante full-theta corregida (17/17 parámetros) del baseline histórico que reconstruye los subsets `theta.csv`/`theta_by_case.csv` sobre `DEFAULT_THETA`; también se clasificaron los notebooks aún incompletos y los usos intencionales o seguros de los artefactos parciales.

### 2026-09-22 11:20 HSP

- Archivos: `docs/planning/planificacion_LAB019_021_v2_2026.xlsx`/`.tex`/`.pdf`; `docs/planning/planificacion_LAB019_021_replica_lote2_2026.xlsx`/`.tex`/`.pdf`; `docs/planning/registro_muestras_LAB019_021_v2_2026.xlsx`/`.tex`/`.pdf`; `docs/planning/registro_muestras_LAB019_021_2026.xlsx`/`.tex`/`.pdf`
- Cambio: corrección del balance de volumen en las cuatro versiones de los documentos (es general del muestreo, no de una versión): la alícuota del Carbodoseur (~100 mL) SE DEVUELVE al reactor, por lo que se eliminó el presupuesto apretado 75-85% y la orden de suspensión de lecturas; el único volumen perdido por reactor es Alcolyzer 50 mL/muestra (F1/F3 ≈3 muestras = 150 mL; F2 ≈5 = 250 mL) + Y15 1 mL y Oculyze 1 mL por visita completa + ~2 mL/visita de mangueras (también minis) → pérdida total ≈0.2 L (F1/F3) y ≈0.3 L (F2), volumen final ≈1.7-1.8 L de 2.0 L. En las planillas de registro se agregó en cada bloque la columna «mL no retornados (ledger)» con el desglose por defecto en la instrucción de cabecera, y el bloque condicional solo-F2 marca F1/F3 con «—» también en el PDF v2. Planificaciones: ediciones in situ en las filas de Resumen/Restricciones; registros: reconstruidos con el mismo formato. Validación: 4 Excel passed (audit/scan/validate); 4 PDF sin errores ni overfull (columna Notas ajustada a 3.5 cm) y aceptados visualmente (planificaciones 15/15; registros 15/15 tras corrección del bloque 19).

### 2026-09-22 11:52 -03

- Archivos: `docs/current_model_equations_audit_2026.md`, `docs/current_model_equations_audit_2026/current_model_equations_audit_2026.tex`, `docs/current_model_equations_audit_2026/current_model_equations_audit_2026.pdf`
- Cambio: se actualizó la auditoría integral del modelo para distinguir el baseline histórico A (`theta.csv` + `DEFAULT_THETA`) de B/C con theta completo 17/17, incorporar la conversión SCCM corregida y los parámetros/objetivos A-B-C, mantener como abierto el conflicto de dosis y calendario de N, y clasificar `modelo_ecuaciones_2026` como descripción del estado B. Se generó un PDF actual sincronizado y se conservó intacto `current_model_equations_090926.pdf` como snapshot histórico.

### 2026-09-22 13:13 HSP

- Archivos: `docs/planning/registro_muestras_LAB019_021_v3_2026.tex`, `.pdf`
- Cambio: nueva versión v3 de la planilla de registro, solo PDF (el v2 editado a mano por el laboratorio y su xlsx quedan intactos): papel carta explícito (letterpaper landscape), formato compactado para reducir de 7 a 4 páginas (margen 1.0 cm, arraystretch 1.15, filas de 0.55 cm, menos espaciado entre bloques, 5 bloques/página) y corrección de las muestras de las 12:00 (03/07/10), que sí son visita completa con Y15/Oculyze/Alcolyzer — se quitó su etiqueta "(mini: sin ...)"; las mini 05 (mar 16:45 opcional) y 13 (vie 11:00) conservan su marca. Se preservaron las ediciones manuales del v2 (sin título ni párrafos de instrucciones ni pie). Validación: PDF sin errores ni overfull, tamaño carta verificado (792×612 pt) y aceptado visualmente 4/4.

### 2026-09-23 13:30 -03:00

- Archivos: `laboratory_2026/notebooks/volume_analysis/01_auditoria_volumen_natural.ipynb`, `01_auditoria_volumen_natural.executed.ipynb`, `02_comparacion_theta_fijo_quimica_co2.ipynb`, `02_comparacion_theta_fijo_quimica_co2.executed.ipynb`, `_volume_analysis.py`
- Cambio: se añadieron notebooks ejecutados para auditar escenarios de pérdida/adición de volumen en LAB004–012 y comparar química y CO₂ con parámetros congelados; se explicitan los supuestos de 65 mL por muestra y 20 mL de nutrición ilustrativa. Ambos notebooks se ejecutaron y validaron sin errores; no se modificó el modelo productivo ni se recalibraron parámetros.

### 2026-09-25 19:47 HSP

- Archivos: `data/mem2026/LAB019-021/Mediciones-Offline-LAB019-021.xlsx`
- Cambio: se agregó la hoja `Nutricion` con los pulsos nutricionales 2 ejecutados según registro del laboratorio (LAB019/F1 24-09 09:20; LAB020/F2 24-09 16:40; LAB021/F3 23-09 16:30; 80 ppm YAN, 1 g Springferm Xtrem + 0.4 g FDA en 100 mL de solución), anotando en Notas la muestra de densidad que disparó cada pulso (≈1040 g/L). El llenado de la hoja `MedicionesOffline` (muestras PI–11) corresponde al laboratorio; no se modificaron otras hojas.

### 2026-09-27 21:47 HSP

- Archivos: `data/mem2026/LAB019-021/Oculyze_report_LAB019.csv`
- Cambio: corrección del typo de densidad en la fila `LAB019-9` (10134.4 → 1034.4 g/L), detectado por contraste con el Excel offline y el Brix de la misma muestra. Las densidades del Excel `Mediciones-Offline-LAB019-021.xlsx` resultaron todas consistentes (residual ρ-vs-Brix ≤1.1 g/L en 36 puntos) y no se modificaron. Nota para uso futuro: la columna `Density` de los CSV Oculyze en la muestra 1 contiene "1070" sin decimales con T=0 en los tres fermentadores (entrada redondeada de la app, no medición); la densidad maestra sigue siendo la del Excel.

### 2026-09-27 22:18 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `lab019_021_replica_vs_originals_data_comparison.executed.ipynb`, `laboratory_2026/results/lab019_021_replica_vs_originals_data_comparison/` (5 CSV)
- Cambio: nuevo notebook de diagnóstico (SOURCE + EXECUTED, 13 celdas de código sin errores, 7 figuras solo inline en el EXECUTED — sin PNG en `results/`, política acordada de no guardar imágenes salvo pedido expreso) que compara los datos de laboratorio de las réplicas LAB019-021 contra sus originales LAB004/006/009, sin modelo ni capa CO2. Carga workbook homologado (abril) + Y15/Excel offline/Oculyze con resta de fila CERO (septiembre); dos alineaciones (reloj y azúcar consumida); hitos interpolados (cruce densidad 1040, GF=100/90/40, agotamiento NH3) con Δ réplica−original; dispersión por grupo A vs C; tabla de flags QA exportada. Fallbacks documentados: filas m11 sin metadatos (orden F1/F2/F3, 25/09 08:30), hora de muestreo del Excel como tiempo de observación (m1 Oculyze con su propio timestamp), temperatura Anton Paar excluida. Resultados destacados: LAB020 replica a LAB006 en hitos de azúcar (Δ entre −1.6 y +0.3 h), LAB019 corre +6.5–7.5 h tras LAB004, LAB021 +4.0–4.7 h tras LAB009 pero cruza GF40 5.7 h antes; media |Δ| grupo A 6.7 h vs C 4.1 h.

### 2026-09-27 23:31 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`
- Cambio: se añadió una figura conjunta de los tres pares alineada por horas desde t0, con las mismas cinco señales de la figura por estado y marcas QA; se regeneró el notebook ejecutado (8 figuras, sin errores).

### 2026-09-28 10:06 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`
- Cambio: se unificó el nombre de la columna de acetaldehído de las réplicas con el panel secundario y se regeneró la figura ejecutada; ahora aparecen las tres curvas naranjas de acetaldehído.

### 2026-09-28 10:24 HSP

- Archivos: `data/mem2026/LAB019-021/Mediciones-Offline-LAB019-021.xlsx` (hoja `Nutricion`); `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`/`.executed.ipynb`; `laboratory_2026/notebooks/diagnostics/provisional_co2_temperatura_backups_lab019_021.ipynb`/`.executed.ipynb` (nuevo, provisorio a eliminar)
- Cambio: corrección del t0 de las réplicas: la inoculación (aplicación manual de levadura) fue el lun 21/09 **17:00**, no las 16:00 del plan — el Excel `Experimentos` (17:00) era correcto. El pulso 1 de nutrición (misma dosis del pulso 2: 80 ppm YAN, 1 g SFX + 0.4 g FDA en 100 mL) se dosificó **al mosto antes del inóculo**, por lo que la muestra 01 es pre-inoculación (explica su YAN 260 y la concentración Oculyze de 17:21, post-inóculo). En ambos notebooks T0 pasó de 16:00 a 17:00 y se re-ejecutaron (cero errores); en la hoja `Nutricion` se agregaron las 3 filas del Pulso 1 (hora exacta por confirmar, entre 13:00 y 15:50). Hitos actualizados (Δ réplica−original): LAB019 +5.5…+6.5 h tras LAB004, LAB020 −2.6…−0.7 h vs LAB006, LAB021 +3.0…+3.7 h tras LAB009 y −6.7 h en GF40; media |Δ| grupo A 5.9 h vs C 4.5 h. El notebook provisorio grafica CO2 raw/filtrado y temperatura de los backups globales (carga robusta: 1 línea corrupta en temperatura, 6 timestamps en CO2, fuera de la ventana de campaña). Verificado que `nutricion_activa`/`freq_nut` no registran actividad en toda la campaña (nutrición e inóculo manuales).

### 2026-09-28 14:28 HSP

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/results/lab019_021_theta_full_holdout/transient_kernel_diagnostic_metrics.csv`
- Cambio: se añadió al holdout una sección de variante diagnóstica sin calibración (réplica de la sección 14 de `lab016_018_natural_must_holdout`): kernel rise-decay normalizado A=0.30, tau_r=2 h, tau_d=4 h superpuesto al qprod de la capa congelada, con dos escalados de dosis (0.14 modelada y 0.08 ejecutada) y réplica verificada del pool de release continuo. Figura inline (trayectoria completa + zoom post-pulso); sin cambios en theta ni en los parámetros CO2 (verificado por snapshots).

### 2026-09-28 20:01 HSP

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/results/lab019_021_theta_full_holdout/dissolved_co2_carbodoseur.csv`
- Cambio: nueva sección de señal del logger: figura 2x3 (CO2 filtrado + temperatura filtrada con mediana 1 min + mediana móvil 15 min, SP como referencia) y cálculo de CO2 disuelto por Carbodoseur interpolando la tabla digitalizada `Tabla_CO2_disuelto_carbodoseur_long.csv` con la lectura `Vol_Residual_mL` (muestras 1-6) y la temperatura del log filtrada; T recortada al techo de tabla (20 °C) se marca. Sin ajustes ni optimizaciones.

### 2026-09-28 21:08 HSP

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/results/lab019_021_theta_full_holdout/dissolved_co2_carbodoseur.csv`
- Cambio: sección del logger movida al inicio del notebook (celdas 4-6, tras los parámetros congelados), ahora con carga propia de los CSV de respaldo; filtrado de temperatura más agresivo (mediana 1 min -> mediana móvil 20 min -> media móvil 45 min, centradas) y líneas más gruesas en ambas figuras. Valores de CO2 disuelto regenerados con el filtro nuevo (cambios < 0.02 g/L).

### 2026-09-29 09:22 -03:00

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/results/lab019_021_theta_full_holdout/co2_auc_replicas_vs_originals.csv`
- Cambio: nueva celda bajo la figura de CO2 disuelto que calcula el AUC del flujo de CO2 (CO2 total emitido) de las tres réplicas y lo compara con sus originales pareados (LAB004/006/009, cargados con el loader histórico y reconvertidos con la misma convención 0.0404 g/L/h por sccm; regla simétrica: inicio 2.5 h, cero p10, mediana horaria). Figura con curvas acumuladas por pareja y barras (ventana común 0-160 h y horizonte completo); ratios réplica/original 1.15 / 1.48 / 4.04, consistente con fugas crecientes en los originales (57-88% del CO2 estequiométrico no llegó al medidor).

### 2026-09-29 10:01 -03:00

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`, resultados CSV asociados.
- Cambio: lectura completa del Excel actualizado, incluida m12 a 166 h; auditoría explícita de Y15 faltante para m12. El holdout ahora toma hora y dosis del segundo pulso desde `Nutricion` (80 mg/L registrados), y añade diagnósticos de arranque con CO2 disuelto y sensibilidad a X0 sin recalibración. Ambos notebooks se regeneraron con figuras inline y sin errores.
- Auditoría: el AUC de LAB009 se conserva como comparación descriptiva; su gas fue excluido por QC histórico y los cocientes réplica/original no demuestran fugas.

### 2026-09-29 10:52 -03:00

- Archivos: `data/mem2026/LAB019-021/ONLINE(26-09-28 15-33)_1.txt` (nuevo dato del usuario), `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`, resultados CSV asociados.
- Cambio: se incorporó Y15 m12 de los tres reactores a química, tablas, métricas y figuras. Los azúcares negativos se conservan como QA y se usa el canal de rango bajo cuando entrega valores no negativos (LAB020/021); LAB019 m12 queda sin G+F cuantitativo. Se explicita la extrapolación de temperatura hasta 166 h. Ambos notebooks se regeneraron sin errores y con figuras inline.

### 2026-09-29 11:08 -03:00

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`
- Cambio: se corrigió la figura de diagnóstico temprano con una leyenda única, espacio reservado para título y paneles, y notación matemática para CO2 y exponentes. Se regeneró el notebook ejecutado; figura inspeccionada, sin warnings de glifos ni solapamientos.


### 2026-09-29 16:05 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: prueba reversible de modelos causales efectivos M1/M2 con `theta_natural_full` congelado; ajuste en LAB004-LAB008, seleccion historica en LAB011-LAB012 y evaluacion sin ajuste en LAB019-LAB021. M0 se reprodujo exactamente, las figuras quedaron inline y no se escribieron imagenes ni resultados externos.


### 2026-09-29 16:15 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: se separaron el titulo, la leyenda y los paneles en la figura de calibracion historica M1/M2; se regenero el notebook ejecutado y la figura se verifico visualmente sin solapamientos.


### 2026-09-29 16:35 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: se rehizo la prueba de la capa de CO2 con LAB005/LAB007/LAB008 en peso 1 y LAB019-LAB021 en peso 2, excluyendo LAB004/LAB006; LAB011-LAB012 seleccionan M1/M2 y LAB016-LAB018 quedan como holdout externo con condiciones iniciales heredadas del mismo mosto. Se regeneraron y verificaron las figuras inline sin escribir resultados ni imagenes externas.


### 2026-09-29 16:45 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: las figuras de calibracion, seleccion y holdout ahora muestran las curvas completas. Los limites de ajuste o puntuacion se marcan explicitamente y el tramo posterior al primer pulso posible de LAB016-LAB018 queda sombreado como contexto no puntuado.


### 2026-09-29 16:49 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: se retiraron de todas las figuras las lineas de fin de tramo, el sombreado y sus leyendas; se conservaron unicamente las curvas observadas y las predicciones completas M0/M1/M2.


### 2026-09-29 17:20 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: se agrego un reajuste local de M0 dentro del notebook (nueva seccion tras el ajuste M1/M2), reutilizando `co2_cross.fit_matrix` con los mismos lotes, tramos y pesos (LAB005/007/008 peso 1; LAB019-021 peso 2 como lotes gemelos), con `theta_full` y `three_state_co2_parameters.csv` congelados. El holdout externo, el resumen y las figuras ahora comparan M0 actual, M0 reajustado, M1 y M2. El reajuste vive solo en el notebook: 0 archivos de resultados escritos y auditoria de inmutabilidad OK.

### 2026-09-30 09:02 HSP

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: integrada la nueva columna `Etanol` (% v/v, muestras 1/4/7/10/11/12) del Excel offline `Mediciones-Offline-LAB019-021.xlsx` en los tres análisis de LAB019-021. Comparación de datos: etanol de réplicas vs originales en el panel secundario (rotulado corregido a % v/v), QA flags nuevos (m1 pre-inoculación, LAB021 m12 no monótono) y `n_etanol` en la auditoría. Holdout theta_full: etanol observado convertido a g/L (×7.8924, convención del repo), E ahora se puntúa en las métricas y figura, y E0 se inicializa desde m1 (misma convención que los originales; antes E0=0). Prueba CO2 onset: etanol en el bracket químico observado y E0 consistente. Los tres notebooks re-ejecutados y sus resultados regenerados (CSV del holdout y de la comparación actualizados); auditoría de inmutabilidad de la prueba CO2 OK.

### 2026-09-30 09:12 HSP

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`
- Cambio: los paneles secundarios ahora conectan sólo los puntos medidos (`np.isfinite`), de modo que series esparsas como el etanol (% v/v en m1/m4/m7/m10/m11/m12) se ven como trayectoria continua en vez de puntos aislados cortados por los NaN de las muestras sin medición. Notebook re-ejecutado y figura verificada.

### 2026-09-30 09:30 HSP

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: corrección de dilución del Alcolyzer en m12 de LAB020/LAB021 (27.5 mL de vino + 10 mL de agua = 37.5 mL): solo la columna Etanol se multiplica x37.5/27.5 (7.33->10.00 y 8.66->11.81 % v/v); Brix y densidad se midieron antes de diluir y quedan sin corrección. Documentado en `protocol_lock.json`, QA flags (LAB021 m12 sigue marcado: 11.81 % v/v excede el máximo teórico desde GF0) y markdowns. Tres notebooks re-ejecutados; solo cambian las métricas de E de LAB020/LAB021.

### 2026-09-30 09:53 HSP

- Archivos: `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.ipynb`, `laboratory_2026/notebooks/holdouts/lab019_021_theta_full_holdout.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: precisión por lote de la dilución del Alcolyzer m12: LAB020 = 27.5 mL vino + 10 mL agua (x15/11) y LAB021 = 32.5 mL vino + 5 mL agua (x15/13), ambas a 37.5 mL (aclaración del laboratorio). LAB021 m12 queda en 9.99 % v/v, consistente con LAB019 sin diluir (9.91): se retiró la marca de anomalía del QA flag y del gráfico. Tres notebooks re-ejecutados; solo cambia la métrica E de LAB021 (MAE 4.42->3.73 g/L, bias -0.96->+1.91).

### 2026-09-30 11:06 -03:00

- Archivos: `laboratory_2026/notebooks/KalmanFilter/lab005_m0_interval_advance_ekf_prep.ipynb`, `laboratory_2026/notebooks/KalmanFilter/lab005_m0_interval_advance_ekf_prep.executed.ipynb` (carpeta nueva `notebooks/KalmanFilter`)
- Cambio: primer notebook preparatorio del EKF. Implementa `advance_m0(estado, tiempo_objetivo, entradas, theta, parametros_co2)` con estado extendido (7 estados biológicos + O2 + pool de CO2 disuelto + tiempo) y temperatura exógena, reutilizando `base.rhs`/`base.kinetic_terms` (LSODA igual que `base.simulate`) y la discretización 0.25 h de `effective_qprod_grid`/`raw_qgas_grid_prediction` con M0_actual congelado (theta_natural_full + three_state_co2_parameters C_full_theta_refit/natural). Caso LAB005 0-55 h pre-pulso: reproduce la referencia bit a bit (estados, qprod, O2, pool, qgas, qobs), bordes externos 1 h/2 h equivalentes, reanudación desde checkpoint exacta, corrección artificial X+10 % a las 20 h propagada con pools conservados y tasas recalculadas, balance discreto del pool residual 0. Sin escritura de artefactos; no se implementó el EKF ni P0/Q/R.

### 2026-09-30 12:40 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: añadida prueba de respuesta nutricional transitoria rise-decay con curvas completas válidas y theta_full congelado; LAB005/007/008 peso 1, LAB019-021 peso 2. Comparador sin transitorio ajustado sobre el mismo soporte, activación con química predicha, métricas por pulso/cola, validación LAB011-012 y holdout pre-nutrición LAB016-018. Cuatro figuras nuevas inline, límites de parámetros y dosis/retiros documentados; ejecución sin errores, artefactos anteriores protegidos intactos y sin escritura de imágenes/resultados externos.

### 2026-09-30 13:12 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: incorporada nutrición posterior de LAB016-018 en horas recuperadas del log, incluidos ambos eventos de LAB017, con saltos N exactos y dosis de referencia explícita del diagnóstico previo. Añadidas máscaras de artefactos raw, métricas post-pulso/cola y curvas completas con nutrición. Corregido el reajuste pre-pulso de M0 congelando los dos parámetros nutricionales no informados por ese soporte, eliminando la amplificación arbitraria. Añadidos perfiles térmicos LAB011-012 y diagnóstico de sensibilidad/producción/liberación, sin cambiar theta_full ni constantes térmicas. Ejecutado sin errores, 12 figuras inline y artefactos protegidos intactos.

### 2026-09-30 13:37 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_onset_effective_model_test.executed.ipynb`
- Cambio: retiradas las secciones obsoletas de M1/M2, M0 pre-pulso y sus comparaciones, cálculos, tablas y figuras; notebook centrado en el ajuste completo con transitorio nutricional, holdout con nutrición y diagnóstico térmico. EXECUTED regenerado sin errores, con siete figuras inline y resultados numéricos vigentes idénticos.

### 2026-09-30 16:56 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.executed.ipynb`
- Cambio: creada auditoría de seis variantes de nutrición/oxígeno con comparación congelada y reajustes equivalentes, validación LAB011–012, holdout LAB016–018, sensibilidad de activación y diagnóstico térmico. Controles manuales centralizados para recalcular curvas sin repetir los ajustes. EXECUTED verificado sin errores, con siete figuras inline, balances y referencia reproducidos; theta_full y notebooks anteriores protegidos.

### 2026-10-01 11:59 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`
- Cambio: creada auditoría del reloj térmico, adaptación inicial y liberación dependiente de temperatura, conservando theta_full, el pool seleccionado y la respuesta transitoria de nutrición. Incluye ajuste estructural, selección LAB011–LAB012, holdout LAB016–LAB018, cambios de setpoint, sensibilidad isotérmica y explorador manual. EXECUTED verificado sin errores ni warnings, con seis figuras inline y artefactos anteriores intactos.

### 2026-10-01 15:01 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`
- Cambio: añadida prueba del reloj térmico residual dentro de las siete ecuaciones cinéticas, con pulsos exactos en tiempo real, búsqueda discreta, selección LAB011–LAB012 y evaluación externa LAB016–LAB018. Incorporados controles manuales, auditoría de estados internos y 21 figuras SVG inline; EXECUTED verificado sin errores ni warnings y sin imágenes externas.

### 2026-10-01 16:16 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`
- Cambio: EXECUTED regenerado con el intérprete del environment `fermentation` (Python 3.11.16) porque la versión anterior de hoy fue ejecutada con el Python del sistema 3.12 desde una sesión sin el entorno activado (`language_info` 3.12 en el artefacto). Notebook fuente sin cambios; ejecución completa sin errores ni warnings (31 celdas, 21 figuras SVG inline, identidad s_kin(B=0) exacta y auditoría de artefactos protegidos OK).

### 2026-10-01 17:15 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`
- Cambio: reemplazado en la sección del reloj cinético el render SVG artesanal (`svg_line_chart` con fuente Arial, introducido para esquivar el crash 0xC06D007F de una sesión con PATH corrupto) por figuras matplotlib estándar del notebook (`kinetic_line_chart`, estilo seaborn global, salida PNG inline). Misma firma de datos, colores y líneas verticales de pulsos; 21 figuras (11 ajuste + 6 LAB021 + 4 explorador manual). EXECUTED regenerado con `fermentation` 3.11.16 sin errores ni warnings, artefactos protegidos intactos.

### 2026-10-05 09:22 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.executed.ipynb`
- Cambio: añadida debajo del holdout externo una comparación de las seis variantes con activación condicionada por onset manual, siguiendo el mecanismo de LAB016-018. Incluye controles editables por LAB, curvas completas y métricas antes/después; nueva figura PNG inline ejecutada sin errores ni warnings, conservando celdas y outputs anteriores.

### 2026-10-05 10:12 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.executed.ipynb`
- Cambio: añadida comparación controlada de `Actual con O2` sustituyendo individualmente `matrix_gain`, `kCO2_release_h` y `CO2sat_scale` por sus valores históricos, además del caso conjunto. Conserva `theta_full`, onset manual, pulsos y transitorio; incluye curvas completas y métricas prepulso, con figura PNG inline ejecutada sin errores ni warnings.

### 2026-10-05 10:27 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.executed.ipynb`
- Cambio: añadida comparación controlada de `Actual con O2` entre `theta_full` y el theta antiguo efectivo con seis defaults, conservando capa de CO2, onset, condiciones iniciales, pulsos y transitorio. Incluye flujo predicho, producción biológica y métricas prepulso; figura PNG inline ejecutada sin errores ni warnings.

### 2026-10-05 11:49 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.executed.ipynb`
- Cambio: reemplazada la curva conjunta de tres parámetros históricos por un ajuste diagnóstico compartido sobre LAB016–LAB018 de los parámetros del pool y del transitorio, conservando `theta_full`, oxígeno, onset, condiciones iniciales y pulsos. SOURCE y EXECUTED incluyen la figura PNG inline, tablas de parámetros y métricas; ejecución completa instrumentada sin errores ni warnings.

### 2026-10-05 13:09 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`
- Cambio: nueva sección "Curvas de CO2: réplica vs original (alineación por reloj)" tras la comparación conjunta: 3 paneles con el flujo de CO2 por par (réplicas desde `backup_global_co2.csv`, originales vía loader histórico PT1/PT2), misma convención 0.0404 g/L/h por sccm + cero p10 + mediana horaria, pulsos marcados y anotación de AUC 0-160 h por panel; ratios 1.15/1.48/4.04 (fugas crecientes de los originales documentadas en el markdown). Figura inline solamente, sin nuevos artefactos en results.

### 2026-10-05 16:00 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/01_co2_production_baseline.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/01_co2_production_baseline.executed.ipynb`, `laboratory_2026/notebooks/co2_reformulation/_co2_reformulation.py`, `laboratory_2026/notebooks/co2_reformulation/_build_notebook.py`
- Cambio: nueva comparación de seis formulaciones de CO2 con theta_full congelado, calibración compartida LAB019–021, validación interna por LAB excluido y evaluación externa LAB016–018. Incluye ecuaciones del paper y adaptación reducida explícita, transitorio único, retiros/adiciones registrados, auditorías de masa y CO2 disuelto, residuos, sensibilidades y perfiles. SOURCE sin outputs y EXECUTED con 12 figuras inline de trayectorias completas, verificados sin errores ni warnings de celdas; sin imágenes en results, commit ni push.

### 2026-10-05 16:32 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/01_co2_production_baseline.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/01_co2_production_baseline.executed.ipynb`, `laboratory_2026/notebooks/co2_reformulation/_co2_reformulation.py`, `laboratory_2026/notebooks/co2_reformulation/_build_notebook.py`
- Cambio: sustituidos el transitorio exponencial y el pool de saturación/liberación por producción de CO2 y estados auxiliares de nitrógeno/transportadores de David 2012, condicionados a theta_full intacto. Calibración LAB019–021, exclusión por LAB y transferencia LAB016–018; hipótesis térmicas y de reparto explícitas, residuos, conservación de N y coherencia química. SOURCE y EXECUTED verificados con 12 figuras inline completas, sin errores ni warnings de celdas; se documenta que el ajuste sigue siendo insuficiente. Sin imágenes en results, commit ni push.

### 2026-10-05 18:58 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_production_blocks_audit.executed.ipynb`
- Cambio: añadida figura LAB016–LAB018 con los nueve parámetros históricos de CO2, ICs antiguas y transitorio A=0.30, subida=4 h y caída=12 h, comparando theta_full con theta antiguo efectivo sin ajuste. Incluye parámetros y métricas; EXECUTED regenerado con fermentation, figura inspeccionada y liberación/transitorio verificados contra las funciones antiguas, sin errores de celdas.

### 2026-10-05 20:58 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.executed.ipynb`, `laboratory_2026/notebooks/co2_reformulation/_nutrition_structure_comparison.py`
- Cambio: comparación congelada de la formulación vigente y nutrición directa con/sin transitorio, cruzando theta antiguo/full y parámetros históricos/curva azul para LAB016–021. Incluye ecuaciones, parámetros, ICs, pulsos, métricas, gate predicho y diagnóstico separado con onset manual; SOURCE limpio y EXECUTED con diez figuras inline. Ejecución verificada en fermentation, reproducción de referencias y balance del pool comprobados, sin reajustes ni cambios a datos o notebooks anteriores.

### 2026-10-05 21:12 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.executed.ipynb`, `laboratory_2026/notebooks/co2_reformulation/_nutrition_structure_comparison.py`
- Cambio: añadida figura LAB019–021 con rampa/gain/transitorio y todos los parámetros antiguos, comparando theta antiguo/full con onset manual editable de 28/32/24 h. Incluye ecuaciones, parámetros y métricas; EXECUTED regenerado con once figuras, figura nueva inspeccionada y referencias anteriores verificadas. Se comprobó que el cambio de gate conserva biología, oxígeno y transitorio, sin reajustes.

### 2026-10-05 22:03 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.executed.ipynb`, `laboratory_2026/notebooks/co2_reformulation/_nutrition_structure_comparison.py`
- Cambio: estandarizada la notación de tasas de CO2 por etapa, con tabla de definiciones, equivalencias anteriores y correspondencia con columnas internas. Ecuaciones de las figuras distinguen q_bio, q_base, q_prod, q_out y q_pred, y separan T_N de M_N. EXECUTED regenerado en fermentation; las once figuras permanecen idénticas y las referencias numéricas se conservan, sin cambios al modelo ni parámetros.

### 2026-10-06 09:30 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.executed.ipynb`, `laboratory_2026/notebooks/co2_reformulation/_nutrition_structure_comparison.py`
- Cambio: añadida una figura final LAB019–021 con tres curvas por panel: modelo actual, transitorio dentro de q_bio y esa modificación sin CO2 respiratorio, conservando O2, parámetros antiguos, onset manual y ambos theta. Incluye explicación, ecuaciones, parámetros, diferencias y métricas; pool reintegrado por variante, balance y referencia verificados. EXECUTED regenerado en fermentation con doce figuras; las once anteriores permanecen idénticas. La procedencia azul ausente se trata como referencia archivada opcional, manteniendo obligatorios los inputs científicos y el snapshot congelado.

### 2026-10-06 09:38 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.executed.ipynb`
- Cambio: ampliada la referencia permanente de parámetros antiguos/nuevos con valores, procedencia histórica y snapshot azul, normalización del transitorio y separación respecto de theta, onset e ICs. SOURCE y EXECUTED sincronizados; código, parámetros efectivos y figuras conservados sin reejecución de celdas científicas.

### 2026-10-06 09:44 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.source.ipynb`, `laboratory_2026/notebooks/co2_reformulation/02_nutrition_structure_comparison.executed.ipynb`, `laboratory_2026/notebooks/co2_reformulation/_nutrition_structure_comparison.py`
- Cambio: incorporado CO2 observado válido en negro a la figura final de tres modelos, distinguido el modelo original en gris y cambiado el pulso nutricional a morado con leyenda. Explicación actualizada y EXECUTED regenerado en fermentation; figura inspeccionada, referencias numéricas verificadas y once figuras anteriores conservadas.

### 2026-10-06 11:26 -03:00

- Archivos: `docs/CO2_equation_simplified.tex`, `docs/CO2_equation_simplified.pdf`
- Cambio: documentada la variante CO2 con rampa/gain/transitorio dentro de q_bio y sin aporte respiratorio, conservando A y N_ref. Incluye definiciones químicas, unidades, parámetros antiguos/nuevos y theta, convenciones numéricas y procedencia; revisados nueve papers de context/modeling con bibliografía y distinción entre respaldo directo y cierres propios. PDF de 12 páginas compilado y revisado visualmente, valores theta verificados y discrepancia del coeficiente CO2/etanol explicitada, sin cambios al modelo ni notebooks.

### 2026-10-06 12:47 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/_co2_temperature_shape_audit.py`
- Cambio: reconstruida la auditoría térmica con la ecuación simplificada (transitorio en q_bio, O2 conservado y sin aporte respiratorio), capa CO2 antigua y comparación theta_full/theta_defaults con seis defaults explícitos. Recalculados los ajustes térmicos posteriores y la grilla del reloj cinético por theta; conservadas particiones, ICs, dosis y máscaras, con ventanas térmicas, química y exploradores manuales. SOURCE limpio y EXECUTED regenerado en fermentation con 14 figuras inline revisadas; referencia, pulsos, balance y 36 inputs protegidos verificados, sin modificar datos ni parámetros históricos.

### 2026-10-06 13:57 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/_co2_temperature_shape_audit.py` (eliminado)
- Cambio: integradas las funciones de la auditoría en el SOURCE y eliminado su auxiliar Python. Aumentado a 6 g/L el umbral local de G+F predicho consumido, conservando etanol generado de 2 g/L y la condición «o». EXECUTED regenerado en fermentation con 14 figuras y sin errores; verificados referencia simplificada con el nuevo gate, pulsos, balance, parámetros congelados e inputs protegidos.

### 2026-10-06 14:10 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`
- Cambio: incorporadas las 33 mediciones Oculyze de LAB019–LAB021, vinculadas al tiempo de muestreo y convertidas a biomasa viable con 30 pg/célula y viabilidad porcentual. Añadidos puntos X al diagnóstico de estados, comparación de biomasa con cinco relojes cinéticos y ambos theta, y métricas X excluyendo m1. EXECUTED regenerado sin errores con 15 figuras; ajustes y 13 figuras anteriores conservados, inputs protegidos verificados y sin nuevos auxiliares Python.

### 2026-10-07 09:56 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.tex`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.pdf`
- Cambio: creado resumen académico de cinco páginas con evolución de la ecuación CO2, transitorio y N_ref, tablas de parámetros históricos/snapshot azul y theta, análisis cuantitativo del notebook 02 y expresiones químicas con bibliografía. PDF compilado y revisado visualmente; notebooks y auxiliar conservados sin cambios ni reejecución.

### 2026-10-07 10:14 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.tex`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.pdf`
- Cambio: sustituidas referencias a colores y snapshots por una explicación autónoma de las dos etapas de calibración, sus LAB y parámetros heredados/reajustados. Explicitados los tres valores previos del ajuste sin LAB010 y la procedencia posterior del transitorio; PDF de cinco páginas recompilado y revisado visualmente, sin modificar notebooks ni parámetros.

### 2026-10-07 10:42 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.tex`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.pdf`
- Cambio: añadida tabla de notación con las siete tasas CO2, definiciones y unidades, aclarando que q_bio,0 conserva el N inicial. Renumerada tabla de métricas; PDF recompilado y revisado visualmente manteniendo cinco páginas.

### 2026-10-07 11:17 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary_v2.tex`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary_v2.pdf`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary_v2_figures/`
- Cambio: creada copia v2 de cinco páginas con dos figuras vectoriales monocromáticas del notebook 02: cruce theta/capa CO2 en LAB017/LAB019 y comparación de ubicación del transitorio/retiro de respiración en LAB021. Curvas reproducidas sin reajuste en fermentation, métricas y diferencias numéricas verificadas; incluidos script y procedencia, PDF compilado y revisado visualmente. Documento original y notebooks conservados.

### 2026-10-07 11:26 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary_v2.tex`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary_v2.pdf`
- Cambio: restaurado íntegramente el análisis de resultados del documento original, incluidos picos individuales, errores de área y cantidades de curvas diagnósticas, conservando ambas figuras de v2. PDF ampliado a seis páginas, recompilado y revisado visualmente; verificada conservación del original, notebooks y figuras.

### 2026-10-07 12:05 -03:00

- Archivos: `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.tex`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary.pdf`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary_v2.tex`, `laboratory_2026/notebooks/co2_reformulation/03_co2_reformulation_summary_v2.pdf`, sus carpetas de figuras, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_co2_temperature_shape_audit.executed.ipynb`
- Cambio: unificada nomenclatura theta_defaults, distinguidos umbrales históricos de 5 g/L y térmicos de 6 g/L de G+F (o 2 g/L de etanol), y corregida explicación/metadatos del notebook sin alterar código ni salidas. Añadida evidencia térmica, límites de interpretación y comparaciones vectoriales de CO2/temperatura y biomasa de LAB019–021; actualizadas etiquetas de figuras históricas. Curvas y métricas verificadas sin nuevos ajustes; PDF de ocho y nueve páginas compilados sin advertencias y revisados visualmente, sin nuevos auxiliares Python en el proyecto.

### 2026-10-07 12:32 -03:00

- Archivos: `<repo>/entrega_CO2_LAB013-021_2026-10-07.zip`
- Cambio: creada entrega incremental con siete análisis principales (SOURCE/EXECUTED disponibles), auditoría de condiciones iniciales requerida, datos originales completos de LAB013–021, documentación y dependencias/artefactos congelados. Incluidos README, manifiesto SHA-256 e informe de verificación; excluidos los notebooks ya compartidos de la imagen y los datos originales anteriores. Integridad ZIP, 504 copias del proyecto e importación/lectura de entradas de los siete análisis verificadas sin repetir optimizaciones; fuentes y datos sin modificaciones.

### 2026-10-07 12:51 -03:00

- Archivos: `<repo>/entrega_CO2_LAB013-021_SOLO_NOTEBOOKS_Y_DATOS_2026-10-07.zip`
- Cambio: creado ZIP separado limitado a los siete análisis seleccionados y sus EXECUTED disponibles (13 archivos de notebook), más los 51 archivos de datos de LAB013–021. Sin módulos, documentación, resultados auxiliares, manifiestos ni notebooks de apoyo. Verificadas las 64 copias con SHA-256 y conservación íntegra del ZIP anterior; notebooks y datos originales sin cambios.

### 2026-10-07 12:57 -03:00

- Archivos: `<repo>/co2_reformulation.zip`
- Cambio: añadidos únicamente 03_co2_reformulation_summary_v2.pdf y 03_co2_reformulation_summary_v2.tex en la carpeta co2_reformulation del ZIP. Verificadas por SHA-256 las dos copias y la conservación íntegra de las 64 entradas anteriores; documentos fuente sin cambios.

### 2026-10-07 21:02 -03:00

- Archivos: `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.ipynb`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.executed.ipynb`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.png`
- Cambio: creada segunda versión del diagrama EKF con modelo y supuestos de ruido aditivo, transición discreta frente a dinámica continua, notación y dimensiones, interpretación de covarianzas y actualización agrupada en tres etapas. Notebook ejecutado en fermentation y figura revisada visualmente; comprobadas la coincidencia SOURCE/EXECUTED, ausencia de errores y conservación de la imagen y ambos notebooks originales mediante SHA-256.

### 2026-10-07 21:15 -03:00

- Archivos: `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.ipynb`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.executed.ipynb`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.png`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.svg`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_paper.png`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_paper.svg`
- Cambio: rehecha la guía v2 en monocromo con un único bloque de predicción y tres pasos numerados; añadida figura compacta formal de dos bloques con tipografía serif, ecuaciones y pie sugerido. Ambas figuras exportadas a PNG y SVG, notebook ejecutado en fermentation y maquetación revisada visualmente. Verificadas las salidas SOURCE/EXECUTED, ausencia de color y conservación de los tres archivos de la primera versión mediante SHA-256.

### 2026-10-08 15:52 -03:00

- Archivos: `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.ipynb`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_v2.executed.ipynb`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_paper_with_measurement.png`, `laboratory_2026/notebooks/EKF/ekf_general_block_diagram_paper_with_measurement.svg`
- Cambio: añadida tercera figura simplificada monocromática con decisión explícita de disponibilidad de medición, ramas de corrección y paso directo, salida común y avance del índice temporal. Nueva celda ejecutada en fermentation; verificados SOURCE/EXECUTED, tres figuras sin errores, exportaciones PNG/SVG y maquetación. Conservados los diagramas anteriores mediante SHA-256 y las salidas previas del notebook.

### 2026-10-13 10:28 -03:00

- Archivos: `laboratory_2026/notebooks/EKF/co2_local_observability.source.ipynb`, `laboratory_2026/notebooks/EKF/co2_local_observability.executed.ipynb`, `laboratory_2026/notebooks/EKF/observability_results/`, `laboratory_2026/notebooks/EKF/diagrams/`.
- Cambio: creado y ejecutado en fermentation el diagnóstico local de CO2 para LAB019–021, con sensibilidad de condiciones iniciales y estados pre-pulso, SVD escalada, parámetros inciertos, información offline hipotética y verificaciones numéricas y de integridad. Conservados datos, calibraciones y ecuaciones originales; SOURCE limpio y EXECUTED con explicación, tablas y cinco figuras revisadas. Reubicados los once archivos de diagramas, ajustadas sus rutas y regenerados ambos EXECUTED. Sin commit ni push.

### 2026-10-13 13:40 -03:00

- Archivos: `laboratory_2026/notebooks/EKF/co2_local_observability.source.ipynb`, `laboratory_2026/notebooks/EKF/co2_local_observability.executed.ipynb`, `laboratory_2026/notebooks/EKF/observability_results/`.
- Cambio: ampliado el diagnóstico con theta_full frente a theta incompleto con defaults, conservando los parámetros antiguos del notebook 02. Añadidos priors exploratorios, propagación desde t0, información secuencial de CO2 y muestras Y15, simulaciones no lineales y controles de admisibilidad, ESS y estabilidad numérica. Biomasa reciente excluida de validación; SOURCE limpio, EXECUTED y figuras revisados, datos y calibraciones intactos. Sin commit ni push.

### 2026-10-13 16:01 -03:00

- Archivos: `laboratory_2026/notebooks/theta_full_vs_incomplete_defaults_natural_review.ipynb`, `laboratory_2026/notebooks/theta_full_vs_incomplete_defaults_natural_review.executed.ipynb`, `laboratory_2026/results/theta_full_vs_incomplete_defaults_natural_review/nitrogen_diagnostic/`.
- Cambio: ampliado el notebook existente con diagnóstico químico de N para LAB004–012 y comparación externa LAB013–015, sin usar CO2. Añadidos balances, trazabilidad YAN/PAN/amonio, tasas iniciales, comparación full/defaults y escenarios de biomasa, captación, crecimiento, saturación y temperatura. SOURCE limpio y EXECUTED regenerado en fermentation; verificadas tablas, figuras, reproducción histórica y conservación de datos, parámetros y ecuaciones. Sin commit ni push.

### 2026-10-13 16:16 -03:00

- Archivos: `laboratory_2026/notebooks/theta_full_vs_incomplete_defaults_natural_review.ipynb`, `laboratory_2026/notebooks/theta_full_vs_incomplete_defaults_natural_review.executed.ipynb`.
- Cambio: corregida la etiqueta del lote sin cruce de N antes del pulso al reducir X0: corresponde a LAB009, no LAB006. Sin cambios de simulaciones ni tablas; verificada la correspondencia SOURCE/EXECUTED y la conservación de resultados e insumos.

### 2026-10-13 17:12 -03:00

- Archivos: `laboratory_2026/nut_sample_audit.py`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.ipynb`, `laboratory_2026/notebooks/diagnostics/lab019_021_replica_vs_originals_data_comparison.executed.ipynb`, `laboratory_2026/notebooks/EKF/co2_local_observability.source.ipynb`, `laboratory_2026/notebooks/EKF/co2_local_observability.executed.ipynb`, resultados asociados de comparación y observabilidad.
- Cambio: incorporadas las tres muestras NUT con PAN, amonio, YAN y procedencia, símbolos propios y tiempos provisionales explícitos entre pulso y primer análisis. Añadido contraste reservado de N sobre ese intervalo y reutilización de simulaciones con controles de integridad y código. SOURCE limpios y EXECUTED regenerados en fermentation; verificadas figuras, muestras únicas, canales ausentes y conservación de datos, parámetros y trayectorias. Sin commit ni push.

### 2026-10-14 10:09 -03:00

- Archivos: `laboratory_2026/notebooks/EKF/post_activity_prediction_comparison.source.ipynb`, `laboratory_2026/notebooks/EKF/post_activity_prediction_comparison.executed.ipynb`, `laboratory_2026/notebooks/EKF/_post_activity_prediction.py`, `laboratory_2026/notebooks/EKF/post_activity_prediction_results/`.
- Cambio: creado y ejecutado en fermentation el diagnóstico de reinicio desde química medida a las 46 y 70,5 h para LAB019–021, con parámetros antiguos y ambos theta, hasta las 166 h y conservando pulsos e historia nutricional. Incluidos reparto G/F explícito cuando falta, sensibilidad de biomasa/CO2 disuelto/O2, contraste reservado de química y NUT, cinco figuras y conclusiones. Verificados 108 escenarios, controles de reloj, continuación y balances, SOURCE limpio, EXECUTED completo e integridad de 25 inputs; sin EKF, reajustes, commit ni push.

### 2026-10-14 11:41 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/_nitrogen_diagnosis.py`, `laboratory_2026/results/nitrogen_consumption_diagnosis/`.
- Cambio: creado y ejecutado en fermentation el diagnóstico de consumo de nitrógeno para LAB004–012 y LAB019–021, con parámetros antiguos, ambos theta, horizontes completos y pulsos registrados. Incluidos 336 escenarios, 24 figuras con subfiguras, componentes PAN/amonio, muestras NUT, balances, sensibilidad y contraste con otras variables; reproducida la calibración original y señalados escenarios con recorte de glucosa negativa. Verificados SOURCE limpio, EXECUTED completo, balances e integridad de 25 inputs; sin reajustes, uso de CO2, EKF, commit ni push.

### 2026-10-14 12:51 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/`.
- Cambio: añadida sección final con inóculo común de 7,44 millones de células/mL para LAB019–021, comparación con la inicialización anterior y variante con 85,39 % de viabilidad. Ejecutadas 12 simulaciones nuevas con ambos theta hasta 166 h, conservando pulsos y NUT; incluidas tres figuras, métricas por variable y límites específicos por lab. Verificados balances, condiciones iniciales, SOURCE/EXECUTED e integridad de 25 inputs; sin reajustes, CO2, EKF, commit ni push.

### 2026-10-14 15:07 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/`.
- Cambio: añadida sección 16.2 con biomasa viable ponderada para LAB019–021, cálculo exacto del promedio y aporte del inóculo, hipótesis explícitas y comparación con aporte viable común y referencia anterior. Ejecutadas 12 simulaciones nuevas con ambos theta hasta 166 h; incluidas tres figuras, métricas por lab y contraste NUT, conservando pulsos. Verificadas normalización, balances, métricas, SOURCE/EXECUTED e integridad de 25 inputs; sin nuevos módulos Python, reajustes, CO2, EKF, commit ni push.

### 2026-10-14 15:26 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/`.
- Cambio: añadidos marcadores rellenos y valores de X₀ para las nuevas condiciones iniciales en los paneles de biomasa de 16.1 y 16.2, sustituyendo el punto inicial del proxy anterior y conservando las mediciones posteriores y la curva de referencia. Regeneradas las figuras en fermentation y verificados 24 marcadores, correspondencia SOURCE/EXECUTED e integridad de inputs, trayectorias y métricas; sin nuevos módulos Python, commit ni push.

### 2026-10-14 16:15 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/`.
- Cambio: añadidas secciones 17–21 con residuos y errores por tramo, balances sobre química simultánea, tasas medias, barrido de X₀ y malla de captación/capacidad fermentativa para LAB019–021 y ambos theta. Ejecutadas 450 simulaciones nuevas hasta 166 h con pulsos completos y generadas 12 figuras; distinguidas mejoras estrictas y mejoras que conservan otras variables. Verificados 492 trayectorias, balances, métricas, escalado cinético, SOURCE/EXECUTED e integridad de 25 inputs; sin nuevos módulos Python, adopción de parámetros ajustados, CO2, EKF, commit ni push.

### 2026-10-14 16:56 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/`.
- Cambio: incorporado GF final de LAB019-12 a 166 h como 0 g/L por solicitud del usuario, conservando ambos resultados negativos originales, flag y auditoría explícita. Regenerado todo el notebook en fermentation con el punto marcado y actualizado en figuras, métricas, balances, tasas y barridos. Verificadas 57 celdas, inclusión de una sola observación, métricas recalculadas y conservación exacta de 864 trayectorias y 25 inputs; sin nuevos módulos Python, commit ni push.

### 2026-10-14 17:06 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/`.
- Cambio: simplificadas las figuras por solicitud del usuario: puntos normales para GF final e inicializaciones, NUT como punto y leyenda simple, sin marcadores especiales, leyendas adicionales ni recuadros de X₀. Conservada la explicación en el texto y regeneradas 32 figuras en fermentation con resultados guardados. Verificados SOURCE/EXECUTED y conservación exacta de CSV y trayectorias; sin nuevos módulos Python, commit ni push.

### 2026-10-15 08:59 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/separated_N_fermentation_temperature/`.
- Cambio: añadida sección 22 para separar captación de N, actividad fermentativa y temperatura en LAB019–021, con biomasa viable común/ponderada y ambos parámetros antiguos. Incorporadas rutas térmicas aisladas de crecimiento/fermentación, 13 figuras y errores antes/después del pulso hasta 166 h. Verificadas 204 curvas, 74 simulaciones nuevas, paridad con el RHS oficial, balances, pulsos y métricas recalculadas independientemente; SOURCE limpio y EXECUTED concordante. Datos, calibraciones y resultados anteriores intactos; sin nuevos módulos Python del proyecto, commit ni push.

### 2026-10-15 10:28 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/co2_detected_activity/`.
- Cambio: añadida sección 23 y figura 1×3 de CO₂ para LAB019–021 con referencia anterior, viable común y ponderada, sólo theta_full y parámetros antiguos. Inicio detectado a 30/34/21 h mediante tres bins horarios completos sobre 0,05 g/L/h; Cd inicial estimado con caudal previo, O₂ propagado y gate=1 posterior. Conservadas exactamente la química y las nutriciones hasta 166 h; documentado soporte gaseoso válido hasta 160 h. Verificadas nueve curvas, balances del pool, pulsos, parámetros, métricas independientes, integridad de resultados previos y 77 celdas SOURCE/EXECUTED concordantes; figura revisada visualmente. Sin nuevos módulos Python del proyecto, reajuste, EKF, commit ni push.

### 2026-10-15 10:52 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/co2_detected_activity/`.
- Cambio: añadida sección 23.4 con figura adicional 1×3 de CO₂ usando theta_defaults para referencia anterior, viable común y ponderada; conservada exactamente la figura theta_full. Mismos inicios detectados, parámetros antiguos, mediciones futuras y pulsos hasta 166 h. Exportadas nueve curvas y comparación de errores defaults/full para la misma biomasa; verificados balances, química original, métricas independientes, integridad de resultados previos y 80 celdas SOURCE/EXECUTED concordantes. Figura revisada visualmente; sin nuevos módulos Python del proyecto, commit ni push.

### 2026-10-15 11:18 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/co2_causal_sugar_activation/`.
- Cambio: añadida sección 24 con activación suave basada en consumo predicho de G+F entre 2 y 6 g/L, comparando ambos theta y biomasas viable común/ponderada desde inoculación hasta 166 h. Incorporados control a=1, kernel normalizado por pico analítico con parámetros numéricos antiguos y auditoría separada grid_max. Generadas tres figuras 1×3, errores por soporte e inicio predicho; documentado que la química permanece intacta y queda pendiente la consistencia estequiométrica de la capa. Verificadas 36 curvas, 48 controles por prefijos, balances, pulsos, métricas independientes y 88 celdas SOURCE/EXECUTED concordantes; figuras y resultados previos conservados y revisión visual completa. Sin nuevos módulos Python del proyecto, reajuste, EKF, commit ni push.

### 2026-10-15 11:35 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/co2_activation_threshold_comparison/`.
- Cambio: añadida sección 25 debajo de las figuras anteriores para comparar umbrales causales 2–6, 5–10 y 8–15 g/L en LAB019–021 con ambos theta y biomasas viable común/ponderada. Incorporadas cuatro figuras 3×3 de inicio, máximo y caída hasta 166 h, métricas sobre soporte observado y conclusiones por LAB. Verificadas 36 curvas, 144 prefijos, balances, reproducción del caso 2–6, métricas y tiempos recalculados independientemente; SOURCE limpio y EXECUTED concordante con 96 celdas. Conservadas las 88 celdas previas y sus resultados; cuatro figuras revisadas visualmente. Sin nuevos módulos Python del proyecto, reajuste, EKF, commit ni push.

### 2026-10-15 12:05 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/co2_causal_sugar_activation/`.
- Cambio: añadidas curvas predichas de G+F y etanol como fondo tenue en las dos figuras 1×3 de CO₂ de sección 24, para ambas biomasas, con eje derecho en g/L y explicación en el notebook. Regeneradas y revisadas visualmente ambas figuras; conservados todos los resultados numéricos, las demás celdas y sus salidas. SOURCE/EXECUTED concordantes y SOURCE limpio; sin commit ni push.

### 2026-10-15 12:42 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.source.ipynb`, `laboratory_2026/notebooks/diagnostics/nitrogen_consumption_diagnosis.executed.ipynb`, `laboratory_2026/results/nitrogen_consumption_diagnosis/co2_hard_sugar_activation/`.
- Cambio: añadida comparación de encendido completo a 2 frente a 6 g/L inmediatamente debajo de la figura de activación suave, con figura 4×3 de activación y caudal para LAB019–021, ambos theta y biomasas. Conservados parámetros antiguos, química y pulsos hasta 166 h; documentado el encendido en el primer nodo que alcanza cada umbral. Verificadas 24 curvas, 96 prefijos, balances, métricas y cruces de umbral; SOURCE limpio y EXECUTED concordante con 99 celdas. Resultados y figuras previos conservados; figura nueva revisada visualmente. Sin nuevos módulos Python del proyecto, commit ni push.

### 2026-10-15 18:54 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/`.
- Cambio: creada y ejecutada calibración gaseosa exclusiva de LAB016–021, comparando ganancia sola y liberación/solubilidad/ganancia con ambos theta químicos antiguos fijos. Aplicado remanente de N de 30 mg/L, biomasa viable ponderada para LAB019–021 e hipótesis existentes de LAB016–018. Incorporadas nueve figuras, transferencia entre corridas, integración implícita conservativa del reservorio, auditorías de datos, balances y refinación numérica. SOURCE limpio y EXECUTED concordante; datos crudos, parámetros compartidos y calibraciones anteriores conservados como referencia. Sin commit ni push.

### 2026-10-15 22:10 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/nitrogen_offset_diagnostic/`, `laboratory_2026/results/co2_lab016_021_recalibration/manifest.json`.
- Cambio: añadido apartado inicial de remanente de N por LAB019–021 con YAN original, dos figuras 1×3 y selección de muestras posterior al agotamiento predicho postpulso sin offset, para ambas theta y biomasa viable ponderada. Calculadas medianas y sensibilidad a umbrales y esperas; documentada la ausencia de series equivalentes de N para LAB016–018. Verificados datos, selección, resultados y concordancia SOURCE/EXECUTED; conservados los resultados y salidas de la recalibración anterior con B=30 mg/L, sin aplicar los candidatos, recalibrar CO₂, commit ni push.

### 2026-10-15 22:25 -03:00

- Archivos: `data/mem2026/LAB019-021/YAN_muestras_corregidas.csv`.
- Cambio: creado archivo independiente con las 39 muestras de YAN de LAB019–021, incluidas NUT, restando 30 mg N/L y truncando resultados negativos a cero. Conservados identificadores, horarios y flags temporales; verificados valores y archivos originales intactos. Sin cambios en exports Y15, notebooks, ecuaciones, parámetros o recalibraciones; sin commit ni push.

### 2026-10-15 22:39 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/`.
- Cambio: conectado YAN_muestras_corregidas.csv directamente a observaciones y N0 de LAB019–021, retirando el descuento del notebook y conservando N0 previo de LAB016–018 como hipótesis. Regenerados EXECUTED, figuras y errores con los ocho ceros del archivo; actualizadas explicaciones y trazabilidad, y sustituida la exportación química anterior. Verificadas las 39 muestras, ausencia de doble descuento, estabilidad numérica de predicciones/ajustes y ecuaciones y archivos originales intactos. SOURCE/EXECUTED concordantes; sin commit ni push.

### 2026-10-15 22:52 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/transfer_hard_activation_6g/`, `laboratory_2026/results/co2_lab016_021_recalibration/manifest.json`.
- Cambio: añadidas dos figuras de transferencia 2×3, con ambos theta y Z1/Z2, usando encendido completo de la fuente al consumo predicho de G+F ≥6 g/L. Reintegrado el reservorio desde cero con parámetros previamente ajustados, sin recalibración; incorporados tiempos de activación y errores frente a la transición 2–6. Verificadas 24 curvas, balances, umbrales y métricas; figuras revisadas y SOURCE/EXECUTED concordantes. Conservados resultados, figuras anteriores, muestras corregidas y ecuaciones compartidas; sin commit ni push.

### 2026-10-15 23:04 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/06_chemistry_lab016_018.png`, `laboratory_2026/results/co2_lab016_021_recalibration/manifest.json`.
- Cambio: añadida figura 3×3 de N, G+F y etanol predichos de LAB016–018, comparando ambos theta y mostrando pulsos hasta el final, antes de las figuras de transferencia. Reutilizadas las trayectorias químicas existentes y explicadas las condiciones iniciales heredadas y ausencia de validación química directa. Figura revisada, SOURCE/EXECUTED concordantes y resultados previos intactos; sin recalibración, commit ni push.

### 2026-10-15 23:30 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/`.
- Cambio: superpuestos en las dos figuras químicas los azúcares estimados por densidad con la relación de Lima, para LAB016–021; añadidas cobertura, diferencias frente al Y15 y trazabilidad. Conservados horarios, valores negativos de la aproximación y predicciones existentes; verificados 60 puntos, concordancia SOURCE/EXECUTED e integridad de datos y resultados numéricos, y revisadas ambas figuras. Sin cambios de modelo, recalibración, commit ni push.

### 2026-10-16 01:04 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/`.
- Cambio: retirado el apartado 0 y sus figuras del notebook; reunidas las figuras químicas de LAB019–021 y LAB016–018 con una columna de biomasa viable. Incorporados los nueve recuentos Oculyze de LAB016–018 en sus horarios, documentando una fecha inconsistente y conservando X0=0.45 g/L. Conectados CO2 y temperatura completos de LAB019–021 hasta la última química (166 h), regenerados ajustes, transferencias y auditorías. Verificados cobertura, balances, datos originales intactos, 35 celdas concordantes y 12 figuras; revisadas figuras. Sin commit ni push.

### 2026-10-16 01:21 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/`.
- Cambio: incorporada la densidad inicial común 1069 g/L reportada por el usuario a las 00:00 para LAB016–018, asignando G+F inicial=172.5 g/L y conservando la proporción G:F anterior. Añadidos los puntos iniciales a las figuras y su trazabilidad temporal; regeneradas predicciones, calibraciones gaseosas y transferencias. Verificados ambos theta, reparto inicial, 63 puntos de densidad, balances y SOURCE/EXECUTED; datos originales, parámetros químicos y química de LAB019–021 intactos. Sin commit ni push.

### 2026-10-16 01:39 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/`.
- Cambio: sustituida la biomasa inicial de LAB016–018 por 7×10⁶ células viables/mL, convertidas directamente a X0=0.21 g/L sin otro factor de viabilidad. Conservados G+F inicial=172.5 g/L y las demás entradas; regeneradas predicciones, ajustes gaseosos, transferencias y conclusiones. Verificados ambos theta, balances, originales intactos, química de LAB019–021 conservada y concordancia SOURCE/EXECUTED; revisada la figura química. Sin commit ni push.

### 2026-10-16 01:53 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/`.
- Cambio: corregida la concentración viable inicial común de LAB016–018 a 13×10⁶ células/mL según el usuario, equivalente a X0=0.39 g/L sin otro factor de viabilidad. Conservados G+F inicial=172.5 g/L y el resto de entradas; regeneradas curvas, ajustes y transferencias, y añadido resumen de conclusiones calculado desde las métricas actuales. Verificados ambos theta, balances, originales intactos, química de LAB019–021 conservada y SOURCE/EXECUTED concordantes; revisada la figura química. Sin commit ni push.

### 2026-10-16 02:13 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration/manifest.json`, `laboratory_2026/results/co2_lab016_021_recalibration/transfer_hard_activation_6g/` (eliminado).
- Cambio: retirada la sección 8.1, sus dos figuras, cálculos y resultados exclusivos; eliminadas referencias del manifiesto. Conservada la transferencia de la sección 8 con activación progresiva 2–6 g/L. Verificadas 32 celdas SOURCE/EXECUTED concordantes, diez figuras y resultados restantes intactos, sin recalibrar, commit ni push.

### 2026-10-16 02:25 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v2.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v2.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration_v2/`.
- Cambio: creada v2 con salidas independientes, conservando intactos el notebook anterior y todos sus resultados. Añadida a la transición por consumo predicho de G+F 2–6 g/L la condición simultánea de etanol producido E−E0≥10 g/L. Regenerados ajustes, figuras y transferencias; exportados tiempos y trayectorias de activación. Verificados doce casos, causalidad, fuente nula antes del umbral, balances, misma química/observaciones y 32 celdas SOURCE/EXECUTED concordantes; revisadas figuras. Sin commit ni push.

### 2026-10-16 02:35 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v2.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v2.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration_v2/`.
- Cambio: retirada la condición de etanol de v2 y sustituida por activación progresiva por consumo predicho de S=G+F entre 2 y 10 g/L (50 % a 6 g/L). Regenerados ajustes, figuras, transferencias y diagnósticos de activación. Verificados doce casos, causalidad, activación sin umbral de etanol, balances, química/observaciones conservadas y SOURCE/EXECUTED concordantes; figuras revisadas y respaldo v1 intacto. Sin commit ni push.

### 2026-10-16 03:23 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v2.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v2.executed.ipynb`, `laboratory_2026/results/co2_lab016_021_recalibration_v2/`.
- Cambio: añadida sección 9.1 con sustituciones individuales y conjuntas de sF/sG por defaults, comparando química, CO2 global y transferencia en LAB016–021 con parámetros gaseosos de theta_full congelados. Añadidas cuatro figuras, métricas y trayectorias independientes; verificadas reproducción de referencia, balances y concordancia SOURCE/EXECUTED. Conservados ajustes previos, entradas y respaldo v1; sin commit ni push.

### 2026-10-20 10:43 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_joint_search.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_joint_search.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/_co2_joint_search.py`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_joint_search_artifacts/`.
- Cambio: creado y ejecutado seguimiento de v2 con 26 vectores químicos y 15 escenarios gaseosos, diagnóstico de cancelación de fuentes, validación interna en LAB019–021 y transferencia a LAB016–018 sin incluirlo en objetivos ni selección. Incorporadas cinco figuras dentro del notebook y tablas trazables; verificadas reproducción de referencia, balances, refinamiento numérico, concordancia SOURCE/EXECUTED e integridad de 62 archivos previos. Sin figuras nuevas en results, cambios de producción, commit ni push.

### 2026-10-20 11:30 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_joint_search.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_joint_search.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_joint_search_artifacts/`.
- Cambio: añadida y ejecutada sección 9 fijando únicamente matrix_gain=1.025 en ambas mezclas positivas, sin recalibrar ni cambiar la selección previa. Incorporadas comparación por LAB y ventanas, figura integrada y tablas independientes; verificadas escala exacta, química y reservorio conservados, reproducción de métricas, concordancia SOURCE/EXECUTED e integridad de entradas. Sin figuras en results, commit ni push.

### 2026-10-20 12:44 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v3.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v3.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/_co2_recalibration_v3.py`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v3_artifacts/`.
- Cambio: creada y ejecutada v3 desde CO2 crudo y respaldos completos, con Hampel centrado y Butterworth sin desfase, comparación de intensidades de filtrado y temperatura suavizada utilizada efectivamente por el modelo. Recalibración con medianas de 10 minutos, recortes trazables que cubren la química, transferencias y comparación de mezclas positivas. Verificados 28 ajustes, balances, refinamiento, concordancia SOURCE/EXECUTED e integridad de 121 archivos previos; diez figuras integradas, ninguna nueva en results. Sin commit ni push.

### 2026-10-20 15:22 -03:00

- Archivos: `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v3.source.ipynb`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v3.executed.ipynb`, `laboratory_2026/notebooks/diagnostics/_co2_recalibration_v3.py`, `laboratory_2026/notebooks/diagnostics/co2_lab016_021_recalibration_v3_artifacts/`.
- Cambio: corregido el tiempo transcurrido mediante America/Santiago y UTC, identificado el salto de septiembre como 14 segundos reales y eliminadas las máscaras por bomba, puentes sobre nutrición y márgenes de exclusión. Reejecutada la recalibración con la respuesta a nutrición conservada; actualizadas diez figuras, tablas, auditorías de reloj y soporte, y conclusiones. Verificados 28 ajustes, balances, refinamiento, concordancia SOURCE/EXECUTED e integridad de 121 archivos previos. Sin figuras en results, commit ni push.
