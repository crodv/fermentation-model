# PROJECT_CONTEXT — contexto operativo mínimo del proyecto (handoff para agentes)

**Qué es este documento**: contexto global y relativamente estable, para iniciar sesiones nuevas sin
arrastrar conversación previa. NO es un informe científico ni una bitácora. El detalle técnico vive en
los documentos/enlaces citados. Regla de tamaño: si algo no cambia lo que un agente debe hacer,
asumir o verificar, no va aquí.

## Objetivo del proyecto

Modelar fermentaciones alcohólicas (mosto natural Sauvignon blanc y sintético) para llegar a un
**estimador de estados** (EKF/UKF/MHE) del fermentador usando **CO2 gaseoso como sensor online
principal** (X y N como estados prioritarios a estimar). La química offline y Oculyze son validación,
no información operativa futura.

## Arquitectura conceptual (estable)

```
temperatura medida (input exógeno, no estado)
        ↓
upstream kinetics (ODE)  →  estados: X, Xd, N, G, F, E, Gly  (pulsos N como saltos exactos)
        ↓
qprod biológico (0.4777·(βG+βF)·X)
        ↓
capa CO2: gate de activación + pool disuelto + release continuo + matrix_gain
        ↓
qobs [g/L/h]  ↔  sensor de flujo SCCM
```

- **Separación dura**: modelo upstream (θ_natural, congelado) y capa CO2 (parámetros de
  observación/transferencia) son artefactos distintos; calibrar uno NO recalibra el otro.
- **Conversión SCCM**: para análisis nuevos usar `SCCM_CORRECTED` (factor 0.0404392 g·L⁻¹·h⁻¹·SCCM⁻¹;
  MW 44.0095, Vm 24.16 L/mol, K 0.74, 2 L). Los artefactos LEGACY se leen, no se reoptimizan.
- `matrix_gain` es un parámetro empírico de la función de observación: NO representa recuperación
  física de CO2 ni corrige fugas.

## Datos y política

- `fermentation_model/data/` es **inmutable**: el análisis nunca escribe ahí. Resultados derivados van
  al `results/` del workflow que los creó.
- LAB016–LAB018 son **holdout/referencia externa**: no usarlos como training salvo decisión explícita
  por escrito. LAB009 y LAB001–003 están excluidos de la capa CO2 por QC.
- Los notebooks científicos usan el patrón **SOURCE (canónico, sin outputs, execution_count null) /
  EXECUTED (copia ejecutada desde kernel limpio, 0 errores)**; verificar identidad código/markdown.
- Los notebooks diagnósticos viven en `laboratory_2026/notebooks/diagnostics/`.

## Rutas principales para orientarse

| Rol | Ruta |
| --- | --- |
| ODE upstream + fitting base | `shared/run_new_must_glycerol_estimability_doe.py` (`base`) |
| Loader de datos naturales | `shared/new_must_data_loader.py` |
| Capa CO2 (runner autoritativo) | `laboratory_2026/run_co2_matrix_cross_validation_2026.py` (`co2x`) |
| Artefactos canónicos capa CO2 (SCCM corregido) | `laboratory_2026/results/co2_matrix_cross_validation_2026_sccm_corrected/` |
| ICs usadas por θ_natural | `laboratory_2026/results/estimability_historical_natural/batch_summary.csv` |
| Workbook homologado natural (química LAB004–012) | `data/Laboratorio 2026/Vendimia_2026/mosto_natural_xthiol.xlsx` |
| Referencia técnica maestra (calibración/estimador) | `docs/natural_must_model_calibration_and_estimator_readiness_2026.md` |
| Auditoría de ICs temporales + análisis cuantitativo | `docs/natural_must_temporal_audit_LAB001_018.md` |
| Informes diagnósticos permanentes | `docs/diagnostics/` |
| Handoffs operativos por tema | `docs/work_state/` (este directorio) |

## Reglas de trabajo para agentes

- Entorno Conda `fermentation`: activar según `AGENTS.md` (Git Bash: `source /d/anaconda3/etc/profile.d/conda.sh && conda activate fermentation`); verificar una vez por sesión.
- **NO commit, NO push** salvo solicitud explícita del usuario.
- NO modificar raw data, θ, parámetros, resultados históricos ni notebooks existentes sin instrucción.
- Informes detallados permanentes en `docs/diagnostics/` y docs técnicos; este directorio (`work_state/`)
  solo guarda ESTADO operativo compacto.

## Cómo usar docs/work_state (para el agente nuevo)

1. Leer `PROJECT_CONTEXT.md` (este archivo).
2. Leer solo el work_state del tema actual de la sesión.
3. Abrir artefactos detallados (informes/notebooks/CSV) únicamente si la tarea lo requiere.
4. Al cerrar una fase, **reescribir/compactar** el work_state del tema; NO anexar historia
   acumulativa, NO registrar errores temporales ni razonamiento paso a paso.
