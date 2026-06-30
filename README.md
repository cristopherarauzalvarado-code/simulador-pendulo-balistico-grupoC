# Simulador de Pendulo Balistico

Simulador interactivo de un **pendulo balistico** para el curso de **Fisica I**
(CENFOTEC, Grupo C).

Modela el disparo de un proyectil contra una caja suspendida de una cuerda, la
**colision perfectamente inelastica** con conservacion del momentum, la
**oscilacion** resultante del pendulo y la **visualizacion en tiempo real** de
las magnitudes fisicas.

---

## Ejecucion de un solo comando

Con Python 3.10 o superior instalado, desde la carpeta del proyecto ejecute:

```bash
python run.py
```

`run.py` se encarga de **instalar automaticamente** las dependencias (numpy,
scipy, matplotlib) si faltan, y luego lanza la interfaz grafica. No se requieren
pasos manuales de instalacion.

> En algunos sistemas el comando es `python3 run.py` en lugar de `python run.py`.

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

## Modelo fisico (baseline)

- **Colision inelastica:** `v1 = m * v0 / (m + M)` (conservacion del momentum).
- **Oscilacion:** pendulo simple de masa puntual, ecuacion completa
  `theta'' = -(g/L) sin(theta)` con `g = 9.81 m/s^2`, integrada con
  `scipy.integrate.solve_ivp`.
- Condiciones iniciales: `theta(0) = 0`, `omega(0) = v1 / L`.
- Metodo **aproximado**: masa puntual, **sin friccion** ni amortiguamiento.

El metodo exacto (inercia rotacional, amortiguamiento y graficas 5-9) queda
anotado en los `TODO` de cada modulo para el **Informe Final**.

---

## Estructura del proyecto

```
pendulo-balistico-sim/
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
| oscilacion.py | Sidney Rodriguez | Pendiente (esqueleto)   |
| graficas.py   | Maciel Gomez     | Pendiente (esqueleto)   |
| interfaz.py   | Tatiana Solis    | Pendiente (esqueleto)   |

Los modulos pendientes ya tienen su encabezado, la firma del contrato y una
lista de `TODO`; lanzan `NotImplementedError` hasta que se desarrollen.

## Pruebas rapidas de los modulos

El modulo de colision (ya implementado) se puede ejecutar de forma aislada:

```bash
python -m src.colision
```

Imprime una demostracion y verifica la conservacion del momentum.

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
