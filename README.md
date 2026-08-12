# Simulador de Pendulo Balistico

Simulador interactivo de un **pendulo balistico** para el curso de **Fisica I**
(CENFOTEC, Grupo C).

Modela el disparo de un proyectil contra una caja suspendida de una cuerda, la
**colision perfectamente inelastica** con conservacion del momentum, la
**oscilacion** resultante del pendulo y la **visualizacion en tiempo real** de
las magnitudes fisicas.

---

## Como abrir el proyecto (macOS)

### Opcion A - Un solo clic (recomendada, sin comandos)

Doble clic en el archivo **`abrir_simulador.command`** que esta en la carpeta
del proyecto. Eso es todo: la primera vez instala lo que falte (Python con Tk,
numpy, scipy, matplotlib) y abre el simulador; las siguientes veces lo abre en
segundos.

> La primera vez macOS puede advertir que el archivo se descargo de internet.
> Si no deja abrirlo: clic derecho sobre `abrir_simulador.command` -> **Abrir**
> -> **Abrir**. Solo hay que hacerlo una vez.

> **Nota (descarga como ZIP):** si obtuvo el proyecto bajando el ZIP de GitHub
> (en lugar de `git clone`), el doble clic puede no funcionar porque el ZIP
> pierde el permiso de ejecucion. Solucion, una sola vez desde la carpeta del
> proyecto en la Terminal: `chmod +x abrir_simulador.command`. Con
> `git clone` / `git pull` esto no pasa.

### Opcion B - Por terminal (equivalente, paso a paso)

Desde la carpeta del proyecto:

```bash
# 1. Instalar un Python con Tk moderno (SOLO la primera vez en la maquina)
brew install python-tk@3.13

# 2. Crear el entorno virtual con ese Python
/opt/homebrew/opt/python@3.13/bin/python3.13 -m venv .venv

# 3. Instalar dependencias (numpy, scipy, matplotlib)
.venv/bin/python -m pip install -r requirements.txt

# 4. Abrir el simulador
.venv/bin/python run.py
```

Despues de la instalacion (pasos 1-3, una sola vez), para abrir el proyecto
basta el paso 4.

> **Importante (macOS):** NO use `python run.py` a secas ni el boton "Play" de
> VS Code apuntando al Python del sistema. Ese Python trae una version vieja de
> Tk (8.5.9) que en macOS moderno dibuja la **ventana en blanco**. Use siempre
> el lanzador o el Python del entorno `.venv` (Tk 9.0). En VS Code:
> `Cmd+Shift+P` -> "Python: Select Interpreter" -> elija el de `.venv`.

> Requiere [Homebrew](https://brew.sh) instalado (una sola vez por maquina).

---

## Como se usa

1. Ingrese los parametros en la columna izquierda:
   - **m**  : masa del proyectil (kg)
   - **M**  : masa de la caja (kg)
   - **v0** : velocidad inicial del proyectil (m/s)
   - **L**  : longitud de la cuerda (m)
2. Elija el **metodo** (aproximado o exacto con inercia) y, si quiere,
   active el **amortiguamiento viscoso** con su coeficiente.
3. Presione **"Iniciar simulacion"**. Puede **pausar/reanudar** o
   **reiniciar** la animacion con los botones correspondientes.
4. Observe en el centro la **animacion del pendulo**, debajo el **panel
   numerico** (v1, energia perdida, amplitud y periodos) y a la derecha las
   **graficas por pestanas**:
   - *Cinematica basica*: theta(t), omega(t), p(t), Ek(t)
   - *Energia y dinamica*: x(t)/y(t), v(t), Ek/Ep/Emec, T(t)
   - *Comparacion de metodos*: v1 exacto vs aproximado (boton "Comparar metodos")
   - *Comparar simulaciones*: con vs sin amortiguamiento (boton correspondiente)
5. Use **"Exportar graficas a PNG"** para guardar todas las figuras en la
   carpeta `reportes/` y usarlas en el Informe Final.

> La ventana se puede **redimensionar y maximizar**: si en su pantalla las
> graficas se ven apretadas o algun borde se corta, agrande la ventana (o
> maximicela) y el panel de graficas usa el espacio libre. El tamano inicial
> ya se calcula con margen para que nada quede cortado, pero en pantallas muy
> pequenas (por ejemplo, un portatil de 13") puede convenir maximizarla.

### Modo sin interfaz grafica (linea de comandos)

Para generar las graficas sin abrir ninguna ventana (por ejemplo, para
automatizar la generacion de figuras del informe):

```bash
python -m src.main --sin-gui --m 0.05 --M 2.0 --v0 300 --L 2.0 \
    --metodo exacto --amortiguamiento --coef-amortiguamiento 0.2 \
    --salida reportes
```

Ejecute `python -m src.main --help` para ver todas las opciones disponibles.

---

## Modelo fisico

- **Colision:** perfectamente inelastica por defecto,
  `v1 = m * v0 / (m + M)` (conservacion del momentum). El metodo exacto
  trata la caja como un pendulo fisico con inercia rotacional propia y
  admite impacto no central (conservacion del momento angular respecto al
  pivote); tambien se puede modelar un choque con coeficiente de
  restitucion `e` (0 = inelastico, 1 = elastico).
- **Oscilacion:** metodo **aproximado** (masa puntual,
  `theta'' = -(g/L) sin(theta)`) o **exacto** (pendulo fisico,
  `I_total*theta'' = -(M*L + m*b)*g*sin(theta)`), ambos con
  `g = 9.81 m/s^2`, integrados con `scipy.integrate.solve_ivp` (sin
  aproximacion de angulos pequenos) y con amortiguamiento viscoso opcional.
- Condiciones iniciales: `theta(0) = 0`, `omega(0) = v1 / L`.
- El periodo se calcula por dos vias: la aproximacion de angulos pequenos
  (`2*pi*sqrt(L/g)`) y la formula exacta por integral eliptica.

---

## Estructura del proyecto

```
pendulo-balistico-sim/
  abrir_simulador.command  Lanzador de un clic para macOS (instala todo y abre)
  run.py            Instala dependencias si faltan y lanza el simulador
  requirements.txt  numpy, scipy, matplotlib
  README.md         Este archivo
  CLAUDE.md         Contexto para agentes de IA (arquitectura y contrato)
  .gitignore        Python estandar
  src/
    __init__.py
    colision.py     velocidad_tras_impacto + metodo exacto y restitucion (Cristopher Arauz)
    oscilacion.py   simular_oscilacion con solve_ivp, exacto y amortiguamiento (Sidney Rodriguez)
    graficas.py     PanelGraficas por pestanas (graficas 1-9) en Tkinter (Maciel Gomez)
    interfaz.py     App(tk.Tk) y lanzar(): GUI completa + animacion (Tatiana Solis)
    main.py         iniciar() arranca la GUI o corre en modo --sin-gui
```

---

## Estado de desarrollo

Todos los modulos estan implementados, incluidas las extensiones del Informe
Final (ver el detalle en `TAREAS_INFORME_FINAL.md` y el contrato ampliado en
`CLAUDE.md`):

| Modulo        | Responsable      | Estado                                    |
|---------------|------------------|--------------------------------------------|
| colision.py   | Cristopher Arauz | Implementado (baseline + exacto + restitucion) |
| oscilacion.py | Sidney Rodriguez | Implementado (baseline + exacto + amortiguamiento + periodos) |
| graficas.py   | Maciel Gomez     | Implementado (graficas 1-9, export PNG, comparaciones, blitting) |
| interfaz.py   | Tatiana Solis    | Implementado (metodo, amortiguamiento, pausar/reiniciar, panel numerico) |
| main.py       | Compartido       | Implementado (GUI + modo `--sin-gui`)     |

Solo quedan las tareas de integracion del grupo (validar con distintos
parametros, corregir errores y redactar el Informe Final), que no son de
codigo.

## Pruebas rapidas de los modulos

Cada modulo se puede ejecutar de forma aislada e imprime una demostracion con
verificaciones (conservacion del momentum, de la energia mecanica, etc.):

```bash
python -m src.colision      # colision inelastica, metodo exacto, restitucion
python -m src.oscilacion    # oscilacion aproximada vs exacta, amortiguamiento
python -m src.graficas      # demo interactiva del panel de graficas (abre una ventana)
python -m src.main --sin-gui --salida reportes   # simulacion completa + export PNG
```

---

## Troubleshooting

- **`python: command not found`**
  Use `python3 run.py`. Verifique la instalacion con `python3 --version`.

- **La instalacion de dependencias falla**
  Actualice pip e intente manualmente:
  ```bash
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  ```

- **`ModuleNotFoundError: No module named 'tkinter'`**
  Tkinter no esta incluido en su instalacion de Python.
  - macOS (Homebrew): `brew install python-tk`
  - Ubuntu/Debian: `sudo apt-get install python3-tk`
  - Windows: reinstale Python marcando la opcion "tcl/tk and IDLE".

- **La ventana abre pero sale en BLANCO (macOS)**
  Es el sintoma del Tk viejo (8.5.9) del Python del sistema. Solucion: use el
  lanzador `abrir_simulador.command` o el Python del entorno `.venv` creado con
  `python-tk@3.13` (ver "Como abrir el proyecto"). Para confirmar la version de
  Tk: `python3 -c "import tkinter; print(tkinter.TkVersion)"` (debe ser 8.6 o
  superior; 8.5 es la que falla).

- **No aparece la ventana / error de backend de Matplotlib**
  Asegurese de ejecutar en un entorno con interfaz grafica (no por SSH sin
  reenvio de X11). El simulador usa el backend `TkAgg`.

- **Alguna grafica se ve cortada contra el borde de la ventana**
  Agrande o maximice la ventana: es redimensionable y el panel de graficas
  crece con ella. El tamano inicial se calcula con margen extra, pero varia
  segun el sistema operativo y el escalado de pantalla (HiDPI/Retina).

- **`ModuleNotFoundError: No module named 'src'`**
  Ejecute siempre desde la carpeta raiz del proyecto con `python run.py`.

---

## Creditos

Proyecto del **Grupo C** - Fisica I - CENFOTEC.

| Modulo        | Responsable        |
|---------------|--------------------|
| colision.py   | Cristopher Arauz   |
| oscilacion.py | Sidney Rodriguez   |
| graficas.py   | Maciel Gomez       |
| interfaz.py   | Tatiana Solis      |
