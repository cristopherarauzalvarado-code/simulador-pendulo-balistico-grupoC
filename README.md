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
2. Presione **"Iniciar simulacion"**.
3. Observe en el centro la **animacion del pendulo** y a la derecha las
   **4 graficas en tiempo real**:
   - theta(t) : angulo (rad)
   - omega(t) : velocidad angular (rad/s)
   - p(t)     : momentum lineal (kg*m/s)
   - Ek(t)    : energia cinetica (J)

---

## Modelo fisico

- **Colision inelastica:** `v1 = m * v0 / (m + M)` (conservacion del momentum).
- **Oscilacion:** pendulo fisico con amortiguamiento viscoso, ecuacion completa
  `theta'' = -((m+M)*g*L_cm/I)*sin(theta) - (b/I)*omega` con `g = 9.81 m/s^2`,
  integrada con `scipy.integrate.solve_ivp`. Periodo por integral eliptica.
- Condiciones iniciales: `theta(0) = 0`, `omega(0) = v1 / L`.
- Sin kwargs: modo baseline (masa puntual, sin amortiguamiento) identico al
  original. Con kwargs: pendulo fisico con inercia rotacional.

El metodo exacto (inercia rotacional, amortiguamiento y datos para graficas 5-9)
esta implementado en `oscilacion.py`. Quedan pendientes las graficas 5-9 en
`graficas.py` y el selector de metodo en `interfaz.py`.

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
    colision.py     velocidad_tras_impacto, momentum, energia perdida (Cristopher Arauz)
    oscilacion.py   simular_oscilacion con solve_ivp (Sidney Rodriguez)
    graficas.py     PanelGraficas con 4 subgraficas en Tkinter (Maciel Gomez)
    interfaz.py     App(tk.Tk) y lanzar(): GUI + animacion (Tatiana Solis)
    main.py         iniciar() arranca la GUI
```

---

## Estado de desarrollo

Andamiaje compartido listo (`run.py`, `requirements.txt`, `README.md`,
`CLAUDE.md`, `.gitignore`). Cada integrante implementa su propio modulo
respetando el contrato de firmas (ver `CLAUDE.md`):

| Modulo        | Responsable      | Estado                  |
|---------------|------------------|-------------------------|
| colision.py   | Cristopher Arauz | Implementado            |
| oscilacion.py | Sidney Rodriguez | Implementado            |
| graficas.py   | Maciel Gomez     | Pendiente (esqueleto)   |
| interfaz.py   | Tatiana Solis    | Pendiente (esqueleto)   |

Los modulos pendientes ya tienen su encabezado, la firma del contrato y una
lista de `TODO`; lanzan `NotImplementedError` hasta que se desarrollen.

## Pruebas rapidas de los modulos

Los modulos de colision y oscilacion se pueden ejecutar de forma aislada:

```bash
python -m src.colision
python -m src.oscilacion
```

El primero verifica la conservacion del momentum. El segundo verifica la
conservacion de energia, el decaimiento con amortiguamiento y la
compatibilidad hacia atras con el baseline.

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
