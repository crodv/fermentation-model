# AGENTS.md

Reglas para agentes de código que trabajen en este repositorio.

## Python / Conda environment

- El entorno oficial es `fermentation`.

- En Windows, NO se debe asumir que ejecutar directamente:

  `D:\anaconda3\envs\fermentation\python.exe`

  equivale a una activación completa del entorno Conda.

- Para ejecuciones científicas que utilicen NumPy, SciPy, Matplotlib, Pyomo, IPOPT, notebooks o librerías nativas, se debe activar realmente el environment `fermentation` antes de ejecutar.

- La activación debe ejecutar los scripts de:

  `D:\anaconda3\envs\fermentation\etc\conda\activate.d\`

  porque `fermentation_idaes.ps1` mantiene el orden correcto de las DLL.

- El orden requerido en PATH es:

  `D:\anaconda3\envs\fermentation\Library\bin`

  ANTES de:

  `C:\Users\claud\AppData\Local\idaes\bin`

- `IDAES\bin` debe seguir presente para que IPOPT funcione, pero debe aparecer después de las DLL del environment Conda, una sola vez y al final del PATH.

- Nunca anteponer manualmente `IDAES\bin` al PATH.

- Nunca duplicar `IDAES\bin` en PATH.

## Conda activation for agent shells

Asignación conocida de shell por herramienta:

| Harness | Shell asumido |
| --- | --- |
| OpenCode UI | Windows PowerShell 5.1 |
| ZCode (y modelos ejecutados desde su harness) | Git Bash / MINGW64 |
| Codex CLI | PowerShell heredado del flujo del usuario |
| Codex / VS Code | PowerShell heredado del flujo del usuario |

Reglas comunes:

- Cada agente asume el shell asignado a su harness salvo evidencia explícita de lo contrario, y NO debe volver a detectar el shell en cada comando.

- La activación se realiza una vez por sesión/contexto persistente y se reutiliza mientras la sesión siga siendo la misma. Solo se repite cuando se abre un proceso de shell nuevo que no conserva el estado anterior (ver `### Verification and troubleshooting`).

- Ambos comandos de inicialización deben ejecutarse en el MISMO shell/sesión que vaya a ejecutar los comandos de Python/Jupyter; la activación no se propaga entre sesiones distintas.

- `conda` NO está disponible directamente en el shell por defecto de estas herramientas; los mecanismos indicados abajo son los verificados para esta instalación.

### OpenCode UI

Shell: Windows PowerShell 5.1.

```powershell
. D:\anaconda3\shell\condabin\conda-hook.ps1
conda activate fermentation
```

- Asumir PowerShell 5.1 salvo evidencia explícita de lo contrario.

- Como OpenCode puede iniciarse desde su UI sin heredar una terminal donde `fermentation` esté activado, aplicar exactamente este mecanismo antes de la primera ejecución científica de cada sesión.

- Si OpenCode crea un proceso de shell nuevo que no conserva el estado anterior, incluir la inicialización y activación en ese nuevo contexto antes de ejecutar Python/Jupyter.

- No usar directamente `D:\anaconda3\envs\fermentation\python.exe` como sustituto de la activación completa.

### ZCode

Shell: Git Bash / MINGW64.

```bash
source /d/anaconda3/etc/profile.d/conda.sh
conda activate fermentation
```

- Asumir Git Bash salvo evidencia explícita de lo contrario.

- Activar `fermentation` una vez por sesión/contexto persistente y reutilizar esa activación mientras la sesión siga siendo la misma.

- En Git Bash, `fermentation_idaes.ps1` NO se ejecuta automáticamente (bash no ejecuta `.ps1`, y en `activate.d` no existe `fermentation_idaes.sh`).

- Por tanto, para tareas científicas o con IPOPT, verificar una vez por sesión que `D:\anaconda3\envs\fermentation\Library\bin` aparezca antes de `C:\Users\claud\AppData\Local\idaes\bin`.

- `idaes\bin` debe aparecer una sola vez y al final del PATH.

- Si es necesario reproducir temporalmente el efecto de `fermentation_idaes.ps1`, hacerlo solo en la sesión actual del shell (eliminar duplicados y agregar `C:\Users\claud\AppData\Local\idaes\bin` al final del PATH), sin modificar archivos ni el environment.

- No crear todavía `fermentation_idaes.sh`.

### Codex CLI

Flujo habitual del usuario (desde PowerShell):

```powershell
Enable-Conda
conda activate fermentation
codex
```

- Si Codex CLI fue iniciado desde una terminal donde `fermentation` ya está activo, asumir que el proceso hereda correctamente el entorno y no repetir innecesariamente toda la inicialización.

- Verificar el entorno solo al comienzo de una tarea científica larga o si aparece evidencia de que el contexto cambió.

- Si Codex CLI abre un shell nuevo independiente que no hereda la activación, usar el mecanismo estándar de PowerShell descrito en `### Other PowerShell agents`.

### Codex / VS Code

Flujo habitual del usuario:

```powershell
Enable-Conda
conda activate fermentation
code .
```

y luego se trabaja desde VS Code con Codex/extensiones dentro de esa instancia.

- Si VS Code fue abierto desde una terminal donde `fermentation` ya estaba activo, asumir inicialmente que el proceso heredó el contexto correcto; no repetir una detección completa antes de cada ejecución.

- Antes de una ejecución científica larga, Run All, optimización o tarea con IPOPT, realizar una verificación rápida del entorno (ver `### Verification and troubleshooting`).

- Si una herramienta/extensión interna abre un shell independiente que no conserva la activación heredada, activar `fermentation` dentro de ese shell con el mecanismo estándar de PowerShell.

### Other PowerShell agents

Para cualquier otro agente o herramienta que ejecute Python/Jupyter en este repositorio desde Windows PowerShell y no tenga el entorno activado (OpenCode, Codex CLI, agentes/subagentes, terminales automatizadas u otros asistentes de código):

```powershell
. D:\anaconda3\shell\condabin\conda-hook.ps1
conda activate fermentation
```

- Esta activación ejecuta los scripts de `D:\anaconda3\envs\fermentation\etc\conda\activate.d\`, incluido `fermentation_idaes.ps1`, que es justamente lo que mantiene el orden correcto de las DLL descrito en `## Python / Conda environment`.

- El PATH debe mantener `D:\anaconda3\envs\fermentation\Library\bin` ANTES de `C:\Users\claud\AppData\Local\idaes\bin`.

### Verification and troubleshooting

Frecuencia:

- No repetir verificaciones completas antes de cada comando, ni repetir la detección/activación/verificación mientras el mismo contexto de ejecución siga funcionando correctamente.

- Al comienzo de una sesión nueva de trabajo científico, o antes de una ejecución larga, verificar una sola vez lo indicado abajo.

- Repetir la detección/activación/verificación solo si ocurre alguna de estas situaciones: se inicia una nueva sesión de shell; la herramienta abre un proceso de shell independiente; cambia el harness o la herramienta; `python` deja de apuntar a `fermentation`; IPOPT deja de resolverse correctamente; cambia el PATH; aparece un crash nativo; reaparece `0xC06D007F`; NumPy/SciPy/Matplotlib dejan de cargar correctamente.

Verificación única por sesión:

```
python -c "import sys; print(sys.executable); print(sys.prefix)"
```

Resultado esperado:

```
D:\anaconda3\envs\fermentation\python.exe
D:\anaconda3\envs\fermentation
```

y:

```
python -c "import numpy, scipy, pandas, matplotlib; from scipy import signal; print('Scientific stack OK')"
```

con salida `Scientific stack OK`.

Para tareas con IPOPT:

```powershell
# PowerShell
where.exe ipopt
ipopt --version
```

```bash
# Git Bash
which ipopt
ipopt --version
```

IPOPT debe resolver a `C:\Users\claud\AppData\Local\idaes\bin\ipopt.exe`, con versión funcional equivalente a `Ipopt 3.13.2 (x86_64-w64-mingw32), ASL(20190605)`.

Error nativo `0xC06D007F`:

- La causa histórica identificada en este proyecto fue una colisión de DLL por un orden incorrecto del PATH entre `C:\Users\claud\AppData\Local\idaes\bin` y `D:\anaconda3\envs\fermentation\Library\bin`.

- Si reaparece `0xC06D007F`, NO reinstalar NumPy, SciPy, Matplotlib, BLAS, LAPACK ni Conda; NO reconstruir el environment; NO crear otro environment ni venv; NO modificar paquetes automáticamente.

- Revisar primero, en este orden:

  1. si `fermentation` está realmente activo;
  2. si el shell corresponde al esperado para ese harness (tabla de `## Conda activation for agent shells`);
  3. si `fermentation\Library\bin` aparece antes de `idaes\bin`;
  4. si `idaes\bin` está duplicado;
  5. si el stack científico pasa la verificación indicada arriba.

Reglas generales que se conservan:

- No crear nuevos `venv`, entornos Conda ni otros entornos Python para resolver problemas de ejecución o dependencias.

- No usar el Python del sistema si puede utilizarse el intérprete del environment `fermentation`.

- No utilizar como solución alternativa agregar manualmente `site-packages` de `fermentation` al `sys.path` desde otro Python. Debe ejecutarse realmente con el intérprete de `fermentation`.

- No instalar ni actualizar paquetes automáticamente (ver `## Dependency management`).

Si en el futuro alguna herramienta cambia de shell o esta configuración deja de funcionar, se actualizará este archivo en ese momento.

## Dependency management

- No instalar ni actualizar paquetes automáticamente.

- Si una dependencia necesaria no está disponible en el entorno `fermentation`, primero:

  1. verifica que realmente falta mediante el error correspondiente;
  2. identifica exactamente qué paquete se necesita;
  3. determina si esa dependencia ya está declarada en `environment.yml`, `requirements.txt`, `pyproject.toml` u otro archivo de dependencias del repositorio;
  4. explica brevemente por qué es necesaria para completar la tarea;
  5. pide autorización antes de instalarla.

- Si existe una alternativa equivalente utilizando únicamente paquetes ya instalados, prefiérela antes de solicitar una instalación.

- No actualizar versiones de paquetes existentes salvo que sea necesario para la tarea, se explique el motivo y exista autorización explícita.

- Si detectas que el entorno `fermentation` no coincide con las dependencias declaradas formalmente por el repositorio, informa la discrepancia antes de modificar el entorno.

- No crear otro entorno como solución a una dependencia faltante.
