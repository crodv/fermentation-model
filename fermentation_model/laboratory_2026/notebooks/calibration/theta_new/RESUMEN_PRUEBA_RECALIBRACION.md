# Resumen de la prueba de recalibración química

**Estado al 21 de octubre de 2026: prueba fallida hasta ahora, descartada como calibración de referencia. NO CANÓNICA.**

Este documento registra lo que se exploró y modificó durante esta parte del trabajo. No constituye un protocolo validado ni autoriza a adoptar `theta_new`, sus supuestos o sus entradas como configuración oficial. La convergencia del optimizador y una mejora del error agregado no bastaron para considerar satisfactoria la calibración. Por decisión del usuario, se cierra esta prueba como fallida hasta ahora.

## 1. Objetivo y alcance

Se buscó mejorar conjuntamente la predicción de biomasa viable, nitrógeno asimilable (YAN), glucosa, fructosa y etanol, revisando primero los datos y las entradas experimentales. El problema inicial era el compromiso entre variables: varios LAB naturales presentaban predicciones razonables de azúcar/etanol y un consumo de nitrógeno demasiado rápido; LAB006 mostraba un comportamiento diferente, asociado como hipótesis a su baja biomasa inicial.

Se revisaron LAB004–012 y MS007–016. Para los nuevos ajustes se excluyeron LAB010–012 por escasez de muestras, biomasa inicial elevada y mediciones dudosas, especialmente de nitrógeno. Esta exclusión fue una decisión exploratoria, no una demostración de que todas sus mediciones fueran incorrectas. LAB006 se mantuvo; no se sustituyó arbitrariamente su biomasa inicial para forzar el ajuste.

La capa de CO₂ no se recalibró en estos intentos de química. Se conservaron las ecuaciones y los siete estados del modelo compartido: X, Xd, N, G, F, E y Gly. Aunque Xd y glicerol no eran el foco de las figuras principales, siguieron participando en el objetivo histórico. La densidad se utilizó en la revisión de datos y pulsos, no como un estado químico adicional ajustado.

## 2. Correcciones manuales de biomasa

El usuario revisó imágenes Oculyze mal medidas y proporcionó valores corregidos. Se modificó el Excel original y se sincronizaron ambos CSV normalizados, incluyendo concentraciones muertas y biomasas derivadas. La conversión utilizada fue 0,03 g/L por millón de células/mL (30 pg/célula); las muertas se calcularon como total menos viable.

| Muestra, a 43 h | Viable anterior, millones/mL | Viable corregida, millones/mL | Total utilizado, millones/mL | X viable corregida, g/L |
| --- | ---: | ---: | ---: | ---: |
| ING26-LAB004-04 | 17,90 | 34,80 | 35,71, conservado | 1,0440 |
| ING26-LAB005-04 | 31,72 | 51,92 | 52,69, conservado | 1,5576 |
| ING26-LAB006-04 | 14,90 | 30,65 | 36,56, corregido | 0,9195 |

Para LAB006 la captura corregida también informaba gemación de 23,53 % y viabilidad de 83,82 %. Los porcentajes mostrados por el software pueden estar redondeados; los campos derivados de los CSV se calcularon desde las concentraciones.

Estas correcciones de observaciones se distinguen de las hipótesis de calibración: que el ajuste haya resultado fallido no demuestra que las correcciones manuales sean erróneas.

## 3. Mediciones de biomasa retiradas

Primero se excluyeron en el análisis y después, por instrucción explícita del usuario, se vaciaron sus campos Oculyze en la fuente original y sus derivados normalizados. No se eliminaron las filas ni las mediciones de otras variables.

| Muestra | Tiempo histórico | X viable retirada, g/L |
| --- | ---: | ---: |
| ING26-LAB004-10 | 115 h | 0,8688 |
| ING26-LAB005-10 | 115 h | 1,0599 |
| ING26-LAB006-09 | 115 h | 1,2327 |
| ING26-LAB007-L-13 | 160 h | 0,8964 |
| ING26-LAB008-L-13 | 160 h | 0,6129 |
| ING26-LAB009-L-12 | 160 h | 0,1383 |

Las tres primeras mostraban una caída y recuperación posterior. Las tres últimas se consideraron sospechosas tras la revisión del usuario de las imágenes. No se estableció una causa experimental definitiva. La hipótesis de sedimentación o falta de homogeneización no justificó eliminar YAN, azúcar o etanol de esas mismas filas. El peso seco independiente tampoco se eliminó por esta depuración Oculyze.

## 4. Horarios de nutrición y documentos

Se compararon tres referencias distintas: el calendario operativo, el cruce interpolado de densidad 1040 y una propuesta manual basada en la muestra baja de YAN anterior a la subida. No se deben confundir con tres nutriciones efectivamente realizadas.

El usuario propuso un horario posterior a esa muestra baja y luego añadió una hora a LAB004–008. LAB009 conservó el cruce de 1040. Los valores finales se añadieron al Excel en una nueva columna llamada `pulso real`, sin borrar los horarios anteriores:

| LAB | Pulso propuesto final, horas históricas | Dosis asumida |
| --- | ---: | ---: |
| LAB004 | 68,5 | 80 mg N/L |
| LAB005 | 68,5 | 80 mg N/L |
| LAB006 | 100,0 | 80 mg N/L |
| LAB007 | 65,5 | 80 mg N/L |
| LAB008 | 65,5 | 80 mg N/L |
| LAB009 | 41,846153846 | 80 mg N/L |

**Pese al nombre `pulso real`, son horarios provisionales acordados para esta prueba; no una confirmación documental de ejecución.** La subida de YAN no demuestra por sí sola cuándo se realizó una adición.

El calendario `data/Laboratorio 2026/raw_data/Fernanda Folch.ics` no se modificó: se verificó idéntico en main, recalibration y la copia de trabajo. Los CSV normalizados conservaron sus filas y horarios anteriores de `pulso_nut`; el nuevo notebook sustituyó únicamente el horario del evento de simulación leyendo `pulso real` directamente del Excel, sin desplazar muestras ni duplicar dosis.

En sintéticos se aceptaron, para esta exploración, pulsos tabulados de 100 mg N/L en los horarios de 24, 72 o 96 h. Se observó que los horarios usados coincidían con 24 × el factor `Adicion`; no se presentó esto como una verificación independiente mediante logs de bomba. Una celda vacía de `pulso_nut` significa ausencia de adición en esa fila, no una concentración de nitrógeno igual a cero.

## 5. Temperatura

Se detectaron y corrigieron contradicciones de temperatura operacional en el Excel y ambos CSV:

- LAB007: SP del log de 18 → 21 °C, con cambio el 21/04/2026 a las 12:00:01. Se retiraron etiquetas/fases inferidas sin respaldo en el log disponible.
- LAB009: SP del log de 21 → 18 °C, con cambio el 20/04/2026 a las 12:00:03, equivalente a 68,0008333333 h. Se retiró una fase inferida posterior sin respaldo.

Para los naturales, la recalibración utilizó temperatura medida de los logs y un filtro offline: medianas de 30 minutos, mediana móvil centrada de tres intervalos y Butterworth de orden 2 con período de corte de 4 h. Se segmentó el filtrado ante huecos y cambios de consigna. Las extensiones de los extremos usaron el valor filtrado válido más cercano. Para integrar se utilizó una malla de 2 h enriquecida con tiempos químicos y puntos alrededor de los cambios térmicos.

En sintéticos no se encontraron logs continuos equivalentes para este análisis: se utilizó la temperatura operacional tabulada, distinguiéndola de las escasas temperaturas medidas. No se inventó una señal térmica continua de sensor ni un registro de bomba.

## 6. Intentos de recalibración

### Primer intento, posteriormente descartado y reemplazado

1. Ajuste conjunto de 17 parámetros con LAB004–009 y MS007–016: diez arranques, referencia nominal histórica de `theta_reference.csv` y regularización L2 λ = 1 sobre diez parámetros fuera de CORE_FIT.
2. Reajuste de once parámetros con LAB004–009: cuatro arranques, fijando seis valores procedentes de la nueva solución conjunta y sin L2 adicional en esta etapa.
3. Evaluación de parámetros, curvas, errores y estabilidad entre arranques; después, holdout de LAB019–021 sin reajuste.

Las curvas cambiaron sustancialmente aunque las ecuaciones fueran las mismas. La nueva combinación de parámetros modificó crecimiento, limitación por nitrógeno y consumo de azúcares. La mejora del objetivo natural coexistió con compromisos de transferencia y parámetros en cotas. El usuario descartó este theta_new.

Sus parámetros, checkpoint y JSON de la solución conjunta se sustituyeron por el segundo intento por solicitud explícita. El notebook actual no conserva una ejecución reproducible de ese primer ajuste; este apartado es un registro histórico, no un archivo de sus parámetros.

### Segundo intento, contenido actualmente en esta carpeta

Se partió de `laboratory_2026/results/estimability_historical_natural/theta_natural_full.csv`, es decir theta_full histórico, y se reajustaron solo LAB004–009 depurados. No se repitió el ajuste conjunto con sintéticos ni se reutilizó el theta_new descartado.

- Once libres: mu0, qN, betaG0, betaF0, qEG, qEF, iG, iE, Kd0, gammaG0 y gammaF0.
- Seis fijos, exactamente iguales a theta_full: sN, qXG, qXF, sG, sF y m0.
- Cuatro arranques: theta_full y tres perturbaciones lognormales del bloque libre, σ = 0,65 y semilla efectiva 90610; mismas cotas y ponderaciones históricas, sin L2 adicional.
- MS007–016 se evaluaron sin intervenir en el objetivo ni en la selección. LAB010–012 siguieron excluidos.
- Se conservaron los resultados históricos de theta_full, theta_defaults y multistart_07.

Los cuatro arranques declararon convergencia, con objetivos entre 2357,14 y 2357,36. Se seleccionó natural_01. Kd0 y gammaF0 quedaron en su cota inferior. El notebook se ejecutó de nuevo desde checkpoint y se comprobó que no cambiaron el vector ni el checkpoint.

## 7. Holdout y error corregido de condiciones iniciales

El primer holdout de esta serie usó por error biomasa cruda de m1, ignorando una corrección ya acordada en la recalibración v3 de CO₂. Sus conclusiones iniciales quedaron invalidadas y se regeneraron figuras y métricas.

Se recuperaron los siete estados iniciales de `co2_lab016_021_recalibration_v3_artifacts/initial_conditions_corrected_clock.csv`. La biomasa viable utilizada fue:

| LAB | X0 corregida, g/L | Xd0, g/L |
| --- | ---: | ---: |
| LAB019 | 0,2831619028436019 | 0,032661 |
| LAB020 | 0,1533416694312796 | 0,032661 |
| LAB021 | 0,1361529277251185 | 0,032661 |

Las observaciones Oculyze permanecieron separadas de estas condiciones iniciales. Se mantuvo el CSV YAN previamente corregido, sin aplicar otra resta de 30 mg N/L; temperatura del backup completo, pulsos documentados de 80 mg N/L y muestras NUT con tiempo provisional mostradas pero excluidas del error temporal principal. M1 también se excluyó de los errores principales.

LAB019–021 no se utilizaron para ajustar ni seleccionar el vector, pero ya habían sido explorados en trabajos anteriores: este holdout no es una validación ciega.

## 8. Resultado y conclusión

En la última ejecución, el WRMSE de los siete estados, excluyendo las entradas iniciales, fue:

| Grupo | theta_full anterior | theta_new del segundo intento |
| --- | ---: | ---: |
| LAB004–009, ajuste | 2,922 | 2,299 |
| LAB019–021, holdout | 3,610 | 3,282 |

Estas mejoras agregadas no implican una buena predicción de todas las variables o experimentos. Persistieron discrepancias de nitrógeno y del comportamiento temporal; LAB019 empeoró ligeramente en el holdout. La convergencia y la proximidad de objetivos entre arranques tampoco demostraron identificabilidad, validez de los horarios propuestos ni calidad experimental de todas las observaciones.

**Conclusión acordada: la recalibración se considera una prueba fallida hasta ahora. Ninguno de estos intentos se adopta como calibración oficial.** La existencia de `theta_new.json`, un EXECUTED o un manifiesto verificado acredita qué se ejecutó, no su aceptación científica. No usar esta carpeta como fuente canónica ni sustituir los thetas históricos automáticamente en otros análisis. Cualquier continuación deberá decidir expresamente qué datos corregidos y qué hipótesis provisionales conserva.

## 9. Archivos y situación de Git al documentar la prueba

Rutas siguientes relativas a `fermentation_model/`:

| Archivo o grupo | Papel en esta prueba |
| --- | --- |
| `data/Laboratorio 2026/Vendimia_2026/mosto_natural_xthiol.xlsx` | Fuente editada: correcciones y vaciado de campos Oculyze, temperatura operacional y columna provisional pulso real. |
| `shared/results/new_must_data_loading/new_must_normalized_long.csv` | Concentraciones y biomasa corregidas/depuradas; temperaturas corregidas; pulsos originales conservados. |
| `shared/results/secondary_metabolite_data_review/secondary_metabolite_long.csv` | Tabla química empleada para ajustar; mismas correcciones anteriores. |
| `laboratory_2026/notebooks/calibration/preparing_data.source.ipynb` y `.executed.ipynb` | Revisión visual de química, referencias de nutrición y temperatura, naturales y sintéticos separados. |
| `laboratory_2026/notebooks/calibration/chemistry_lab004_012_theta_comparison.source.ipynb` y `.executed.ipynb` | Comparación histórica, revisión de protocolos y sensibilidad a biomasa inicial. |
| `laboratory_2026/notebooks/calibration/theta_new/theta_new.source.ipynb` y `.executed.ipynb` | Segundo intento, comparación de parámetros, predicciones y holdout regenerados. |
| `theta_new.json`, `fit_checkpoint.json`, `manifest.json`, `holdout_lab019_021.json`, en esta carpeta | Resultados y trazabilidad del segundo intento, no parámetros oficiales. |
| `data/Laboratorio 2026/raw_data/Fernanda Folch.ics` | Calendario consultado; sin modificación. |
| `docs/AGENT_CHANGELOG.md` | Historial de las tareas y verificaciones; conserva las entradas de intentos luego descartados. |

La inspección de Git mostró que main aún conservaba las biomasas anteriores y las seis muestras retiradas, y no tenía la columna pulso real. Las correcciones/depuración de biomasa estaban guardadas en recalibration (commit c6c0b35). La columna pulso real y las correcciones térmicas de LAB007/LAB009 seguían como cambios locales. Este es un estado observado, no una instrucción para hacer merge, commit o push. No se realizaron commits ni push al redactar este resumen.
