# Diagnóstico retrospectivo con reparación de transientes de muestreo — LAB004, LAB007 y LAB008

**Auditoría derivada, ejecutada el 2026-09-13.** Esta versión preserva la auditoría histórica original y cambia únicamente la señal observada de LAB004, LAB007 y LAB008 por la variante experimental `repaired + current smoothing` ya validada. No se desarrolló un método nuevo ni se recalibró CO2, la cinética o el modelo.

- SOURCE: `fermentation_model/laboratory_2026/notebooks/diagnostics/co2_historical_variability_microleaks_2026_sampling_repaired.ipynb`
- EXECUTED: `fermentation_model/laboratory_2026/notebooks/diagnostics/co2_historical_variability_microleaks_2026_sampling_repaired.executed.ipynb`
- Resultados: `fermentation_model/laboratory_2026/results/co2_historical_variability_microleaks_2026_sampling_repaired/`
- Auditoría original preservada: `co2_historical_variability_microleaks_2026.ipynb`, su EXECUTED y su carpeta de resultados no fueron sobrescritos.

## Cambio de datos y trazabilidad

### HECHO NUMÉRICO

La auditoría de procedencia de la señal detecta diferencias distintas de cero exclusivamente en los tres LAB solicitados:

| LAB | Señal usada | Máximo cambio absoluto [g/L/h] |
| --- | --- | ---: |
| LAB004 | repaired + current smoothing | 0.455838 |
| LAB007 | repaired + current smoothing | 0.214634 |
| LAB008 | repaired + current smoothing | 0.150300 |
| LAB005, LAB006, LAB010, LAB011, LAB012 | original current smoothed | 0.000000 |

Las predicciones del modelo congelado se verificaron idénticas antes y después. También permanecen iguales las señales de LAB005/006/010/011/012, conversiones, ventanas, grillas, fórmulas, grupos históricos, criterios de clasificación, referencia LAB016–LAB018, análisis térmico, contrafactuales y descomposición del modelo. Las métricas relativas a la mediana de campaña se recalculan para todos los LAB, porque esa mediana sí cambia al sustituir las tres señales.

Las ventanas sustituidas fueron:

| LAB | Ventana reparada [h] | Muestreos asociados [h] | Horas sustituidas |
| --- | ---: | ---: | ---: |
| LAB004 | 44–54 | 43, 50 | 11 |
| LAB004 | 70–76 | 67, 68, 74 | 7 |
| LAB004 | 92–98 | 91, 98 | 7 |
| LAB004 | 118–123 | 115, 122 | 6 |
| LAB007 | 44–49 | 40, 48 | 6 |
| LAB007 | 66–73 | 64, 65, 72 | 8 |
| LAB007 | 89–96 | 88, 96 | 8 |
| LAB007 | 113–121 | 112, 120 | 9 |
| LAB008 | 45–55 | 40, 48 | 11 |
| LAB008 | 67–73 | 64, 65, 72 | 7 |
| LAB008 | 89–98 | 88, 96 | 10 |
| LAB008 | 113–121 | 112, 120 | 9 |

## Métricas old vs repaired

### HECHO NUMÉRICO

| LAB | Integral old → new [g/L] | Δ integral | R_sugar old → new | R_rel old → new | Obs/pred old → new | Peak old → new [g/L/h] | t_peak old → new [h] | Onset old → new [h] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LAB004 | 31.240 → 34.333 | +3.093 (+9.90%) | 0.214 → 0.235 | 1.039 → 1.089 | 1.045 → 1.149 | 0.554 → 0.535 (−3.47%) | 42 → 43 | 27.74 → 27.69 |
| LAB007 | 35.227 → 36.156 | +0.929 (+2.64%) | 0.232 → 0.238 | 1.123 → 1.100 | 1.108 → 1.138 | 0.568 → 0.577 (+1.61%) | 51 → 51 | 26.80 → 26.86 |
| LAB008 | 29.957 → 29.894 | −0.063 (−0.21%) | 0.198 → 0.198 | 0.961 → 0.915 | 0.939 → 0.937 | 0.465 → 0.412 (−11.29%) | 52 → 57 | 20.66 → 19.54 |

`R_rel` es relativo a la mediana de campaña, por lo que puede moverse en dirección distinta a la integral individual cuando cambia esa mediana. En LAB008, el desplazamiento del onset canónico se debe a que su umbral depende del pico global reparado; usando el umbral original, el onset queda en 20.66 h. No representa una modificación de la parte inicial de la señal.

La posición ordinal respecto de integrales bajas cambió de 4 a 5 para LAB004, de 6 a 7 para LAB007 y se mantuvo en 3 para LAB008. En el orden por `R_rel` bajo cambió de 5 a 6, de 6 a 7 y permaneció en 4, respectivamente.

### INTERPRETACIÓN

- LAB004 recupera área de manera material, pero ya no presentaba déficit integral frente al modelo: la reparación aumenta su exceso observado/predicho. Esto reduce la posibilidad de confundir sus aperturas de muestreo con pérdida de señal, sin probar por sí solo ausencia de fuga.
- LAB007 recupera un área moderada y conserva la misma dinámica global: el pico cambia 1.6% y `t_peak` no cambia. Su evidencia de comportamiento normal se mantiene.
- LAB008 no recupera área neta: la interpolación conservadora compensa caídas y spikes casi exactamente. La disminución del pico y el desplazamiento de `t_peak` muestran que parte del máximo anterior era sensible a los transientes; no aparece nueva evidencia de pérdida de gas.

## Variabilidad histórica

### HECHO NUMÉRICO

| Grupo | CV integral old → new | CV peak old → new | Rango R_rel old → new |
| --- | ---: | ---: | ---: |
| Programa A: LAB004/005/008 | 3.91% → 6.91% | 9.32% → 12.88% | 0.091 → 0.185 |
| Cálidos: LAB004/005/007/008 | 6.98% → 8.08% | 9.77% → 14.07% | 0.175 → 0.195 |
| Todos los históricos aceptados | 27.66% → 27.82% | 41.85% → 43.09% | 0.843 → 0.804 |

La referencia independiente LAB016–LAB018 permanece sin cambios: CV de peak 2.25% y CV de integral 8.48% en la ventana pre-nutrición.

### INTERPRETACIÓN

La reparación no reduce uniformemente la dispersión dentro de los grupos cálidos: aumenta LAB004, aumenta menos LAB007 y deja casi igual la integral de LAB008. Por eso suben moderadamente sus CV, en vez de disminuir. La variabilidad de la campaña completa cambia muy poco y sigue dominada por los extremos no modificados, especialmente LAB010, LAB006 y LAB012. El CV integral de los históricos cálidos (8.08%) continúa cercano al de la referencia LAB016–LAB018 (8.48%).

## Impacto sobre las conclusiones de posibles microfugas

### HECHO NUMÉRICO

- Ninguna clasificación final cambió para LAB004, LAB007 o LAB008: los tres siguen como compatibles con cinética normal y réplicas A consistentes, con confianza alta.
- Después de reparar, sus ratios integral observado/predicho son 1.149, 1.138 y 0.937. Ninguno queda como el caso de recuperación anormalmente baja.
- Las discontinuidades detectadas después de la reparación quedan sólo en LAB011 (77 y 79 h) y LAB012 (97 h); desaparecen eventos de LAB004/007/008 de esta lista.
- LAB010 conserva exactamente su señal e integral (14.691 g/L). Su `R_rel` cambia de 0.468 a 0.446 sólo por el nuevo denominador de campaña y permanece como la única recuperación gaseosa anormalmente baja compatible tanto con pérdida como con lectura instrumental baja.
- LAB006 conserva su señal e integral (22.492 g/L); `R_rel` cambia de 0.693 a 0.662 por el mismo efecto de normalización. Su déficit sigue explicado por la cola sobrepredicha del modelo, por lo que la evidencia de pérdida continúa siendo insuficiente.
- LAB011 y LAB012 conservan señales e integrales; sus `R_rel` pasan de 1.137 a 1.085 y de 1.310 a 1.250. Ambos permanecen altos y con signo contrario al esperado para una pérdida.

### INTERPRETACIÓN

La conclusión general sobre microfugas **se mantiene**. Reparar los transientes conocidos evita atribuir a pérdida de gas artefactos locales de muestreo, pero no genera un patrón común de recuperación de área que explique la variabilidad histórica. La evidencia compatible con pérdida adicional sigue reducida a LAB010 y continúa sin ser demostrativa: el diseño histórico no permite separar fuga del biorreactor, canal/sensor o sesgo instrumental. La reparación fortalece la robustez de la lectura de LAB004 y LAB007 como fermentaciones normales; en LAB008 cambia la forma local y el pico, pero no su integral ni clasificación.

## Conclusiones robustas e incertidumbres restantes

### Conclusiones que permanecen robustas

1. La reparación de muestreo no cambia ninguna clasificación por LAB.
2. LAB006 combina cinética fría real con cola sobrepredicha; no hay evidencia suficiente de pérdida.
3. LAB010 es el único caso de recuperación gaseosa anormalmente baja, pero una microfuga no puede distinguirse de lectura instrumental baja.
4. LAB011 y LAB012 exhiben más CO2 observado que el modelo congelado; no son compatibles con pérdida y exponen limitaciones estructurales del modelo.
5. La predicción baja de mayo está fuertemente afectada por el gate químico del modelo; `obs/pred < 1` no constituye por sí solo evidencia de fuga.
6. La variabilidad global permanece prácticamente igual después de corregir los tres LAB.

### Incertidumbres que permanecen

- No hay metadata que separe inequívocamente fermentador, canal y sensor.
- Faltan pruebas contemporáneas de hermeticidad y blancos/calibraciones por canal, especialmente para LAB010.
- El balance absoluto de carbono no puede cerrarse con los datos disponibles; `R_sugar` y `R_rel` sólo sostienen comparaciones relativas.
- El tamaño muestral es pequeño y sólo el programa A está replicado.
- La reparación conoce los tiempos de muestreo, pero no demuestra que todo el residuo dentro de cada ventana provenga exclusivamente de la apertura.

## Verificación de ejecución

- Ejecución completa del SOURCE con el entorno Conda `fermentation`.
- EXECUTED regenerado desde el SOURCE; 71 celdas totales y 40 celdas de código ejecutadas secuencialmente.
- Cero outputs de error.
- Código y Markdown del SOURCE y EXECUTED idénticos; el SOURCE permanece sin outputs y con `execution_count = null`.
- Aserciones internas: predicciones congeladas idénticas; señales observadas de los LAB no reparados bit a bit idénticas; conjunto de LAB modificados exactamente `LAB004`, `LAB007`, `LAB008`. La única columna de la tabla maestra que cambia en LAB no reparados es `R_rel`, por depender de la mediana recalculada de campaña.
