# Modelo macroscópico: calibraciones químicas recuperadas

Fecha: 2026-09-10. Estado: utilizable con las limitaciones de calibración indicadas.

Este paquete recupera el modelo de siete estados y sus **17 parámetros completos**.
La comparación comprende 21 candidatos químicos existentes. No se realizó una
nueva optimización. No se usaron lecturas de flujo de CO2, ajustes de solubilidad,
estados de CO2 disuelto, retardos de sensor ni activaciones ajustadas con gas.
Tampoco se incluyen los bloques de metabolitos secundarios y aromas.

## Qué archivo utilizar

| Uso | Parámetros completos | Calibración recuperada |
| --- | --- | --- |
| Mosto natural | `theta_natural_full.csv` | `natural_historical`, LAB004–LAB012 |
| Mosto sintético | `theta_synthetic_full.csv` | `synthetic_plus_lot2`, MS007–MS016 + lote 2 F1–F3 |
| Un solo conjunto histórico para ambas matrices | `theta_joint_reference_full.csv` | `multistart_07`, LAB004–LAB012 + MS007–MS016 |

El último es la mejor referencia **conjunta existente entre los candidatos
revisados**, no una demostración de transferencia universal. Natural y sintético
están asociados a cepas diferentes según la auditoría histórica. Los conjuntos
específicos son las referencias recomendadas para cada población.

`macroscopic_model.py` contiene las ecuaciones y el integrador congelados,
sin importar otros módulos del repositorio. Sólo requiere NumPy, pandas y SciPy.
El cargador exige exactamente 17 parámetros positivos y finitos: no completa
parámetros ausentes con defaults. Cada fila del CSV identifica su fuente.

```powershell
python example.py
```

El ejemplo simula LAB004 con el ajuste natural, compara con las predicciones
auditadas y guarda `example_LAB004.csv`. Para reproducir toda la selección desde
el repositorio:

```powershell
python fermentation_model/laboratory_2026/export_macroscopic_chemical_model.py
```

## Evidencia de recuperación y comparación

Todos los candidatos se simularon con las mismas observaciones, temperaturas,
pulsos y ponderaciones dentro de cada población. Los valores de tiempo inicial
condicionan los estados y se excluyen del error de evaluación.

| Selección | Población evaluada | Observaciones posteriores al inicio | WSSE químico | RMSE estandarizado |
| --- | --- | ---: | ---: | ---: |
| Natural específico | 9 LAB | 545 | 11672.084819 | 4.6278 |
| Sintético + lote 2 | 13 fermentaciones sintéticas | 768 | 17876.911229 | 4.8246 |
| Conjunto histórico | 19 fermentaciones, ambas matrices | 1027 | 23694.827064 | 4.8033 |

Los WSSE de filas con poblaciones distintas no son comparables directamente.
`comparison.csv` permite comparar candidatos sobre la misma población.
`chemical_predictions.csv` conserva cada observación, predicción, sigma y residuo.
`metrics_by_batch_state.csv` desagrega por variable y experimento.

El WSSE natural reproduce el valor archivado 11672.084819320407. El sintético
reproduce 17876.91122418397 con diferencia absoluta aproximada de 0.0000051.
El WSSE conjunto aquí es una reevaluación: usa temperatura medida en natural,
excluye observaciones iniciales y no incluye penalización L2. No debe igualarse
sin más al objetivo de su optimización histórica regularizada.

Estos errores estandarizados son bastante mayores que uno: los modelos no
explican la química a la precisión supuesta por las ponderaciones. Seleccionar
el mejor ajuste disponible no certifica que su ajuste sea excelente.

Las evaluaciones sobre datos usados para estimar parámetros son de calibración.
La evaluación de un modelo de una matriz sobre la otra es una prueba de
transferencia retrospectiva, no una validación prospectiva independiente.
No se inventó un experimento reservado después de observar los resultados.

## Ecuaciones

Estados, en g/L (numéricamente equivalentes a kg/m3): biomasa viable X, biomasa
muerta Xd, nitrógeno asimilable N, glucosa G, fructosa F, etanol E y glicerol Gly.
Tiempo en horas. T es la temperatura en kelvin; la entrada del simulador está en °C.

Definimos A(Q,Tr) = exp[Q (T-Tr)/(Tr R T)], con R = 8.314.

```text
A_mu   = A(59453, 300)
A_beta = A(11000, 296.15)
A_K    = A(46055, 293.15)

Kn = (mu0/sN) A_K
Kg = (betaG0/sG) A_K
Kf = (betaF0/sF) A_K
iG(T) = iG/A_K; iE(T) = iE/A_K

a = A_mu N/(N+Kn)
bG = A_beta G/(G+Kg) / (1+iE(T) E)
bF = A_beta F/(F+Kf) / [(1+iG(T) G)(1+iE(T) E)]
mu = mu0 a
m = m0 A(37681,293.3)
M = m (G+F)/(G+F+1)

dX/dt   = (mu-kd) X
dXd/dt  = kd X
dN/dt   = -qN a X
dG/dt   = -[qXG a + qEG bG + M G/(G+F)] X
dF/dt   = -[qXF a + qEF bF + M F/(G+F)] X
dE/dt   = [betaG0 bG + betaF0 bF] X
dGly/dt = [gammaG0 bG + gammaF0 bF] X

Td(E) = -0.0001 E^3 + 0.0049 E^2 - 0.1279 E + 315.89
kd = 0, si T < Td(E)
kd = Kd0 exp[0.0415 E + 130000(T-305.65)/(305.65 R T)], si T >= Td(E)
```

Estas ecuaciones omiten epsilon por legibilidad. El código conserva exactamente
los epsilon de 1e-8, evaluación con estados no negativos y límites de salida
del modelo original. También conserva el umbral discontinuo de muerte; no se
lo reemplazó por las variantes suaves exploradas para diseño experimental.

Temperatura: interpolación lineal de la trayectoria almacenada en `batches.json`.
En natural se usa el registro procesado de temperatura; fuera de su cobertura
se conserva la temperatura nominal histórica. Pulsos: saltos exactos de
concentración en N/G/F/E/X, con muestra antes de adición si coinciden tiempos.
No se añade un estado de volumen ni dilución: las dosis históricas son
incrementos netos de concentración, tal como en el modelo calibrado.

## Qué representan los parámetros

| Parámetros | Papel |
| --- | --- |
| mu0 | Escala de velocidad específica de crecimiento |
| sN | Parametrización de afinidad por N: Kn0 = mu0/sN |
| qN | Consumo de N asociado a crecimiento; Yxn = mu0/qN |
| qXG, qXF | Consumo de G/F asociado a crecimiento; Yxg = mu0/qXG, Yxf = mu0/qXF |
| betaG0, betaF0 | Escalas de producción específica de etanol desde G/F |
| sG, sF | Parametrización de saturación: Kg0 = betaG0/sG, Kf0 = betaF0/sF |
| qEG, qEF | Consumo de G/F asociado a fermentación; Yeg = betaG0/qEG, Yef = betaF0/qEF |
| iG | Inhibición del término de fructosa por glucosa |
| iE | Inhibición fermentativa por etanol |
| Kd0 | Escala de muerte celular, modulada por temperatura y etanol |
| m0 | Escala de consumo de azúcar por mantenimiento |
| gammaG0, gammaF0 | Producción de glicerol ligada a los términos fermentativos |

Los seis parámetros congelados en los ajustes recientes —sN, qXG, qXF, sG,
sF, m0— se restauraron desde `theta_multistart_07.csv`, con todos sus decimales.
En el ajuste conjunto histórico se estimaron los 17 con regularización L2.
La incertidumbre de los seis congelados no desaparece al fijarlos.

## Límites de esta recuperación

1. Los pulsos del ajuste natural archivado son anteriores a la corrección
   posterior por densidad 1040. Por ejemplo, LAB004 conserva 0.08 gN/L a 68 h;
   la tabla posterior de protocolo registra 0.14 gN/L alrededor de 56.09 h.
   Corregir esa entrada requiere **recalibrar la química**. Este paquete no
   presenta el ajuste antiguo como si ya incorporara esa corrección.
2. Se conservan LAB004–LAB012, incluido LAB009, porque ésa es la población
   de la calibración química recuperada. Las exclusiones por sensor de gas
   defectuoso no prueban por sí mismas que deba descartarse su analítica química.
3. El histórico sintético es MS007–MS016; lote 2 corresponde a F04–F06,
   registrados localmente como lot2_F1–lot2_F3. El ajuste sintético seleccionado
   no incluye lote 1. `batches.json` y el manifiesto enumeran la población exacta.
4. Algunos estados iniciales proceden del primer valor finito de su variable,
   incluso si se midió después del primer tiempo. Se preservó esa convención
   histórica; no equivale a disponer de todas las mediciones al inicio.
5. La auditoría global de rutas/hashes de datos crudos no pasó: hay rutas
   históricas ausentes y discrepancias ajenas a este paquete. Esta recuperación
   está respaldada por tablas procesadas congeladas y sus hashes, no por una
   revalidación completa desde los archivos crudos.
6. Los ajustes posteriores del modelo expandido con observaciones de flujo
   de CO2 se excluyen de esta selección: sus parámetros cinéticos podrían haber
   sido influidos por los sensores ahora cuestionados.

`manifest.json` registra fuentes y hashes; `verification.json` verifica que la
copia autónoma y los CSV completos reproducen el simulador del repositorio.
La guía de validación aplicada exigió poblaciones y ponderaciones comunes,
separar recuperación de recalibración y explicitar estos límites.
