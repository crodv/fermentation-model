# Antecedente de conversación Codex

## Metadatos

- **Thread ID:** `01a03977-41b5-7c53-b092-65a8418500fe`
- **Transcript:** `C:\Users\claud\.codex\sessions\2026\08\25\rollout-2026-08-25T11-08-32-01a03977-41b5-7c53-b092-65a8418500fe.jsonl`
- **Repositorio principal:** `cltorrealba/pyomo-doe`
- **Ámbito:** análisis de CO2 y control térmico de Laboratorio 2026 (notebook `co2_filter_delay_analysis_lab2026`), con incorporación y corrección de `LAB005_PT2`.
- **Restricciones respetadas:** sin cambios en datos RAW, parámetros científicos, entorno Conda, commits ni pushes.

## 1. Objetivo del trabajo

El trabajo se centró en el notebook:

`fermentation_model/laboratory_2026/notebooks/co2_filter_delay_analysis_lab2026.ipynb`

cuyo objetivo global es **inventariar los CSV de CO₂ de Laboratorio 2026, deduplicarlos por contenido, formar pares RAW/FILT por experimento y segmento, y estimar el retardo efectivo de la cadena causal de filtrado** `RAW → Hampel → Butterworth → FILT`, para luego relacionar la dinámica térmica con las fluctuaciones de CO₂.

Convención transversal del análisis:

> **delay > 0 significa que FILT aparece retrasado respecto de RAW.**

En la última etapa, la conversación se concentró en dos correcciones puntuales dentro del notebook:

1. corregir la incorporación de `LAB005_PT2` al análisis térmico para que usara una ventana explícita de 20–60 h respecto al inicio real del experimento (y no 0–40 h ni 0–25 h);
2. reemplazar el carácter Unicode `₂` por notación MathText de Matplotlib (`CO$_2$`) para eliminar el glifo `CO□` y los warnings `Glyph 8322`.

Se exigió además que la corrección quedara implementada en el notebook y fuera reproducible mediante **Clear All Outputs → Restart Kernel → Run All**, de modo que la figura embebida y el PNG externo procedieran del mismo código.

## 2. Estructura del notebook y análisis completo

El notebook no modifica ningún CSV original y escribe todos los resultados derivados en `laboratory_2026/results/co2_filter_delay_analysis/`. Sus secciones son:

1. Inventario programático y deduplicación.
2. Evidencia del filtro y retardo teórico.
3. Preparación de pares y estimadores.
4. Retardos experimentales.
5. Comparación entre F1/F2/F3 y estabilidad temporal.
6. Relación entre dinámica térmica y fluctuaciones de CO₂.

### 2.1 Inventario programático y deduplicación

- Se leen sólo las columnas y estadísticas necesarias de cada CSV; el inventario conserva los archivos físicos, pero el emparejamiento usa una única copia canónica por SHA-256.
- Clasificación: los archivos con `FILT` o `co2f` se clasifican como FILT; el resto, RAW. `labNNN` determina el experimento; la secuencia cíclica determina F1/F2/F3 cuando el fermentador no está escrito en el nombre; los sufijos `pt2`/`pt3` y fechas forman segmentos distintos.
- Columnas de valor: `flow_sccm` (RAW) y `flow_filt_sccm` (FILT).
- Resultado del inventario:
  - **65 archivos físicos** (RAW=34, FILT=31);
  - **51 contenidos únicos** (RAW=27, FILT=24);
  - **14 copias físicas duplicadas**.
  - **24 claves de segmento** y **24 pares RAW/FILT completos**.

### 2.2 Evidencia del filtro y retardo teórico

- El código histórico se localizó en `legacy/rendicion/.../NEW_GUI_filtrado_vCTORREALBA.py` y usa exactamente las columnas `flow_filt_sccm` e `is_spike` con una cadena causal Hampel + Butterworth SOS.
- Los parámetros se extraen automáticamente del archivo fuente (sin transcribirlos):
  - Hampel: ventana `120 s`, `k = 3.5`, `min_abs_spike = 0.5 sccm`.
  - Butterworth: orden `3`, `tau = 1200 s`, de lo que se deduce `fc = 1/(2πτ) ≈ 0.000133 Hz` y un período de corte de **125.66 min**.
- Períodos medianos observados en los CSV: `10, 11 y 15 s` (ventana Hampel equivalente de 12, 11 y 8 muestras, respectivamente).
- Se calculó el **retardo de grupo teórico** del Butterworth causal (`scipy.signal.group_delay`) para períodos de característica entre 0.5 h y 48 h:
  - el **límite de baja frecuencia (DC) es ≈ 40.00 min** (~2400 s);
  - el retardo de grupo de un IIR **no es constante con la frecuencia**.

### 2.3 Preparación de pares y estimadores

- La interpolación se restringe a la superposición temporal de cada par; RAW y FILT se llevan a una grilla regular con el período mediano conjunto.
- Para mitigar spikes sin introducir fase se usa una **mediana centrada de 120 s** sobre RAW (sólo para el análisis).
- La correlación de **niveles** usa suavizado Savitzky–Golay centrado de 15 min; la de **derivadas**, de 60 min.
- La correlación cruzada se calcula como `correlate(FILT, RAW)` (detrend + normalización), limitada a ±3 h; una **prueba sintética** validó el signo (desplazamiento de +13 muestras produce lag +13).

### 2.4 Retardos experimentales

- De los 24 pares completos resultaron **15 segmentos elegibles** y **12 experimentos representativos seleccionados** (uno por laboratorio).
- Criterios de elegibilidad: par completo, períodos compatibles, sin timestamps inválidos, superposición ≥ 12 h, amplitud dinámica ≥ 0.5 sccm, correlación de niveles ≥ 0.5 y lag preliminar entre 0 y 120 min.
- Además de las dos correlaciones (niveles y derivadas) se calculan por experimento:
  - `t10/t50/t90` sobre la subida hacia un máximo interior claro (NaN si la señal no tiene una subida/máximo suficientemente claros);
  - desplazamiento del máximo sobre las curvas suavizadas;
  - RMSE antes y después de compensar el lag de niveles, y correlación tras la compensación;
  - retardos por ventanas (24 h en segmentos largos, 8 h en cortos).
- Métricas de retardo de niveles por experimento seleccionado (min): lab001 45.0, lab002 37.2, lab003 41.0, lab004 42.5, lab005 38.8, lab006 42.8, lab007 51.2, lab008 51.0, lab009 55.0, lab010 50.5, lab011 44.8, lab012 46.0. Las de derivadas oscilan entre ~40 y ~53 min.

### 2.5 Comparación F1/F2/F3 y estabilidad temporal

Agregado por fermentador (min, niveles — media/mediana/desv. estándar):

- **F1** (4 exp.): 47.29 / 47.75 / 4.22 (derivadas 44.74);
- **F2** (4 exp.): 42.93 / 41.79 / 6.27 (derivadas 45.69);
- **F3** (4 exp.): 46.21 / 44.42 / 6.21 (derivadas 45.40).

Las diferencias entre fermentadores se interpretan con cautela: F1/F2/F3 están ligados a experimentos distintos y el contenido espectral de cada fermentación afecta el máximo de correlación; el retardo de grupo del IIR tampoco es estrictamente constante con la frecuencia.

### 2.6 Interpretación del retardo

- Los archivos FILT representan la salida de la cadena completa Hampel + Butterworth; por tanto, el valor experimental se denomina **retardo efectivo de la cadena de filtrado**.
- Hampel es causal, pero deja pasar las observaciones no clasificadas como spikes; su contribución sistemática al retardo es menor que la del Butterworth y sólo modifica localmente la señal (mediana de ventana pasada).
- El Butterworth causal de tercer orden tiene fase no lineal; un dead-time fijo es una aproximación operacional útil para las variaciones lentas si las estimaciones por niveles, derivadas y ventanas son concordantes, pero no reproduce exactamente todas las frecuencias ni los transitorios.

### 2.7 Relación entre dinámica térmica y fluctuaciones de CO₂

- La sección **reutiliza** el inventario, los pares seleccionados, los parámetros Hampel y las funciones de correlación; no recalcula ni redefine el análisis de retardo.
- Los registros térmicos contienen directamente `T`, `SP`, `banda`, `hot` y `cold`; las acciones del controlador no se infieren.
- Definición reproducible de la componente rápida:

  **CO₂ rápido = CO₂ después de Hampel − tendencia Savitzky–Golay centrada de 120 min.**

- En las correlaciones cruzadas, **lag > 0 significa que CO₂ cambia después de la variable térmica** (máximo restringido a ±60 min).
- Inventario térmico: **39 archivos físicos, 30 únicos, 9 copias**; períodos térmicos `3, 4 y 5 s`.
- Experimentos representativos para la figura térmica: `lab004/F1`, `lab005/F2`, `lab011/F2`, `lab012/F3`.
- Resultados agregados del bloque térmico (12 experimentos sincronizados):
  - `|correlación cruzada| >= 0.30`: 4/12;
  - periodicidad compartida (coherencia ≥ 0.4): 4/12;
  - efecto HOT con IC bootstrap fuera de cero: 8/12;
  - efecto COLD con IC bootstrap fuera de cero: 11/12;
  - **mediana de atenuación de varianza rápida por FILT: 99.7 %**.
  - Son asociaciones observacionales; no demuestran causalidad.

Criterios de interpretación y limitaciones declarados:

- Los estados HOT/COLD son registros directos, no inferencias desde T/SP.
- El Hampel se reconstruye desde cada RAW; los primeros 120 s son transitorio de reconstrucción.
- La grilla común sigue el período de CO₂; temperatura se agrega por mediana, estados por último valor y sólo se rellenan hasta dos huecos internos.
- Un máximo de correlación puede reflejar una tercera dinámica común y no prueba causalidad.
- Los intervalos bootstrap describen variación entre conmutaciones, pero eventos cercanos no son independientes.
- El análisis espectral se restringe a períodos de 2–120 min.
- Una asociación reproducible indicaría que parte de lo atenuado por Butterworth contiene dinámica física relacionada con el control; **no** implica que toda variación rápida deba conservarse ni justifica todavía cambiar τ.

## 3. Resultados clave (resumen reproducible)

- Correlación de **niveles**: media **45.48 min**, mediana **44.88 min**.
- Correlación de **derivadas**: media **45.27 min**, mediana **44.54 min**.
- Butterworth teórico, límite de baja frecuencia: **40.00 min**.
- Ventanas: **116 ventanas válidas**; mediana **44.2 min** e IQR **9.8 min**.
- Resultados escritos en `laboratory_2026/results/co2_filter_delay_analysis/` (incluye `file_inventory.csv`, `filter_parameters.csv`, `theoretical_group_delay.csv`, `paired_files.csv`, `delay_summary.csv`, `window_delay_summary.csv` y las figuras).

## 4. Corrección de LAB005_PT2 (ventana térmica 20–60 h)

Para `lab005` / `F2` / `PT2`, el tiempo transcurrido se calcula respecto al inicio completo del experimento y no respecto a la primera muestra mostrada:

```python
elapsed_h = (
    block["timestamp"] - cache["prepared"]["experiment_start"]
).dt.total_seconds() / 3600

window_mask = elapsed_h.between(20, 60, inclusive="both")
shown = block.loc[window_mask].reset_index(drop=True)
time_h = elapsed_h.loc[window_mask].reset_index(drop=True)
```

Los paneles temporales de LAB005_PT2 fijan además `time_axis.set_xlim(20, 60)`, de modo que el eje X muestra 20–60 h y no 0–40 h ni 0–25 h. Los demás experimentos conservan el comportamiento previo de selección automática de una ventana representativa de 24 h.

### Ventana efectiva validada

- Inicio real del experimento: `2026-04-07 08:22:33`.
- Timestamp solicitado para `t = 20 h`: `2026-04-08 04:22:33`.
- Timestamp solicitado para `t = 60 h`: `2026-04-09 20:22:33`.
- Primera muestra efectiva de la grilla: `2026-04-08 04:22:40`.
- Última muestra efectiva de la grilla: `2026-04-09 20:22:30`.
- `elapsed_h` mínimo: `20.001944 h`; máximo: `59.999167 h`.
- Número de muestras: `14400`; duración efectiva: `39.997222 h`; resolución: `10 s`.

### Consistencia de las métricas térmicas

El bloque sincronizado 20–60 h se selecciona antes de calcular las variables derivadas. Para LAB005_PT2, el mismo intervalo alimenta temperatura, setpoint, estados HOT/COLD, CO₂ posterior a Hampel, CO₂ filtrado, tendencia lenta, componentes rápidas, correlaciones (temperatura–CO₂ y dT/dt–dCO₂/dt), respuesta event-triggered HOT/COLD, PSD de temperatura y CO₂, coherencia espectral y períodos/frecuencias dominantes. LAB005_PT2 se recalcula desde este bloque y no reutiliza resultados cacheados de otro intervalo. Los parámetros de Hampel y Butterworth no fueron modificados.

## 5. Notación de CO₂ en las figuras (MathText)

Se eliminó el carácter Unicode `₂` de títulos, ejes, leyendas y anotaciones de la celda térmica y de su figura resumen, usando MathText de Matplotlib, por ejemplo: `r"CO$_2$"`, `r"CO$_2$ después de Hampel"`, `r"CO$_2$ FILT"`, `r"CO$_2$ rápido"`, `r"PSD CO$_2$ rápido post-Hampel"`, `r"T rápida vs CO$_2$ rápido"`, `r"dT/dt vs dCO$_2$/dt"`, `r"$\Delta$ CO$_2$ rápido [sccm]"` y `rf"{lab_id} · {row['fermenter']}{title_segment} — acoplamiento térmico–CO$_2$"`. Esto evita `CO□` y los warnings relacionados con `Glyph 8322`.

## 6. Figuras generadas

- `fermentation_model/laboratory_2026/results/co2_filter_delay_analysis/figures/thermal_coupling_lab005_F2_pt2.png`
- `fermentation_model/laboratory_2026/results/co2_filter_delay_analysis/figures/thermal_coupling_lab005_F2_pt2_h20_h60.png` (copia con la ventana explícita en el nombre)
- `fermentation_model/laboratory_2026/results/co2_filter_delay_analysis/figures/thermal_coupling_summary.png`
- Figuras por par (`{lab_id}_{fermenter}_{segment}.png`) y `theoretical_group_delay.png`.

La celda guarda y muestra el mismo objeto de Matplotlib (`fig.savefig(...)`, `plt.show()`, `plt.close(fig)`); no existe una segunda ruta de generación para LAB005_PT2 con la ventana antigua 0–25 h dentro de esa celda.

## 7. Validación realizada

Se ejecutó el flujo equivalente a **Clear All Outputs → Restart Kernel → Run All** con el kernel Conda `fermentation`. El notebook se ejecutó completamente y volvió a guardarse con sus outputs embebidos. Se verificó que:

- la figura embebida de LAB005_PT2 muestra el intervalo 20–60 h;
- la salida embebida y el PNG guardado proceden del mismo objeto de figura;
- la ejecución utilizó 14400 muestras de la ventana definida;
- el código contiene verificaciones explícitas de la ventana y del eje X;
- no aparecieron warnings por `Glyph 8322`;
- la notación de CO₂ se renderiza mediante MathText.

Nota menor: persisten `DeprecationWarning` de pandas (`DataFrameGroupBy.apply operated on the grouping columns`) en la celda de agregación del bloque térmico; no afectan los resultados.

## 8. Pendientes

1. No interpretar `f_s`, `f_d` ni `O2_qmax` como parámetros fisiológicos bien identificados (heredado del análisis CO₂ anterior).
2. Formalizar la ecuación de observación del sensor CO₂ antes de usar el flujo directamente en calibración.
3. Resolver los `DeprecationWarning` de pandas (`include_groups=False`) en la agregación del bloque térmico.
4. Una asociación térmica–CO₂ reproducible no justifica por sí sola cambiar τ ni conservar toda la variación rápida; se requiere evidencia física adicional.

## 9. Archivos relevantes

- `fermentation_model/laboratory_2026/notebooks/co2_filter_delay_analysis_lab2026.ipynb`
- `fermentation_model/laboratory_2026/results/co2_filter_delay_analysis/` (CSVs de resultados y carpeta `figures/`)
- `fermentation_model/laboratory_2026/results/co2_filter_delay_analysis/figures/thermal_coupling_lab005_F2_pt2.png`
- `fermentation_model/laboratory_2026/results/co2_filter_delay_analysis/figures/thermal_coupling_lab005_F2_pt2_h20_h60.png`
- `fermentation_model/laboratory_2026/results/co2_filter_delay_analysis/figures/thermal_coupling_summary.png`
- `fermentation_model/legacy/rendicion/technical_reports/A03_ensayos_estaciones_fermentacion_laboratorio/NEW_GUI_filtrado_vCTORREALBA.py` (fuente de parámetros del filtro histórico)
- `fermentation_model/data/Laboratorio 2026/raw_data/` (CSVs de CO₂ y térmicos de entrada)

## Estado de continuidad

El notebook `co2_filter_delay_analysis_lab2026.ipynb` documenta de extremo a extremo la estimación del retardo efectivo de la cadena de filtrado RAW → Hampel → Butterworth → FILT (≈ 44–45 min por correlación, frente a 40 min teóricos de baja frecuencia) y su vínculo observacional con la dinámica térmica. La corrección de `LAB005_PT2` queda implementada en el notebook con la ventana 20–60 h y la notación MathText de CO₂; una ejecución desde un kernel limpio `fermentation` regenera dentro del notebook y en disco la figura correspondiente. No se modificaron datos RAW, parámetros científicos ni el entorno, y no se realizaron commits ni pushes.
