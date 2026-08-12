# CLAUDE.md - Contexto para agentes de IA

Este archivo orienta a agentes de IA (y a nuevos integrantes) sobre la
arquitectura del proyecto y el contrato entre modulos. Leelo antes de modificar
codigo.

## Proyecto

**pendulo-balistico-sim**: simulador interactivo de un pendulo balistico para
Fisica I (CENFOTEC, Grupo C). Modela el disparo de un proyectil contra una caja
suspendida, la colision inelastica con conservacion del momentum, la oscilacion
del pendulo y la visualizacion en tiempo real.

## Convenciones (obligatorias)

- **Idioma:** comentarios, nombres de variables/funciones y documentacion en
  espanol.
- **Sin emojis** en codigo ni comentarios.
- Cada modulo lleva un encabezado con: responsable, que modela, estado y una
  lista `TODO` con pendientes para el Informe Final.
- **No cambiar las firmas publicas** descritas en el contrato (otros modulos
  dependen de ellas).
- Stack: Python 3.10+, NumPy, SciPy, Matplotlib, Tkinter (estandar).

## Arquitectura y flujo de datos

```
run.py
  -> instala numpy/scipy/matplotlib si faltan
  -> src/main.iniciar()
       -> src/interfaz.lanzar()  (GUI Tkinter)
            usuario ingresa m, M, v0, L y presiona "Iniciar simulacion"
              1) colision.velocidad_tras_impacto(m, M, v0) -> v1
              2) oscilacion.simular_oscilacion(m, M, L, v1, t_max, dt) -> datos
              3) por cada cuadro:
                   graficas.PanelGraficas.agregar_punto(t, theta, omega, p, ek)
                   + animacion del pendulo en el Canvas
```

## Contrato entre modulos (firmas - NO cambiar)

```python
# colision.py  (Responsable: Cristopher Arauz)
velocidad_tras_impacto(m, M, v0) -> v1          # v1 = m*v0/(m+M)

# oscilacion.py  (Responsable: Sidney Rodriguez)
simular_oscilacion(m, M, L, v1, t_max, dt) -> dict(
    t, theta, omega, v, p, ek)                  # arreglos NumPy de igual largo

# graficas.py  (Responsable: Maciel Gomez)
PanelGraficas.agregar_punto(t, theta, omega, p, ek)

# interfaz.py  (Responsable: Tatiana Solis)
App(tk.Tk)
lanzar()
```

Estas firmas no cambiaron. Para el Informe Final se extendieron con
**parametros opcionales** (con defaults que reproducen el baseline) y con
**claves nuevas en el dict de salida**, sin romper el contrato original:

```python
# colision.py: metodo exacto (inercia rotacional, impacto no central) y
# choque con coeficiente de restitucion, ademas del baseline.
velocidad_angular_tras_impacto_exacto(m, M, v0, L, I_caja_cm=0.0, b=None) -> omega1
resumen_colision_exacto(m, M, v0, L, I_caja_cm=0.0, b=None) -> dict(
    omega1, v1_equivalente, momento_angular_antes, momento_angular_despues,
    ek_antes, ek_despues, energia_perdida, fraccion_perdida)
velocidades_con_restitucion(m, M, v0, e=0.0) -> (v_proyectil, v_caja)

# oscilacion.py: metodo exacto y amortiguamiento son opcionales; el dict de
# salida agrega x, y, ep, emec, tension, alpha, metodo, theta_max,
# periodo_aproximado, periodo_exacto sin quitar las claves originales.
simular_oscilacion(m, M, L, v1, t_max, dt, metodo="aproximado",
    I_caja_cm=0.0, b=None, amortiguamiento=False, coef_amortiguamiento=0.0)
    -> dict(t, theta, omega, v, p, ek, x, y, ep, emec, tension, alpha,
             metodo, theta_max, periodo_aproximado, periodo_exacto)
periodo_pendulo(L, theta0, g=GRAVEDAD) -> (periodo_aproximado, periodo_exacto)

# graficas.py: agregar_punto acepta columnas extra opcionales (x, y, v, ep,
# emec, tension) para alimentar la pestana de energia/dinamica; self.widget
# ahora es un ttk.Notebook (se empaqueta igual, con .pack()).
PanelGraficas.agregar_punto(t, theta, omega, p, ek,
    x=None, y=None, v=None, ep=None, emec=None, tension=None)
PanelGraficas.graficar_comparacion_metodos(m, M, v0, L, I_caja_cm=0.0, n=60)
PanelGraficas.comparar_simulaciones(datos_a, etiqueta_a, datos_b, etiqueta_b)
PanelGraficas.exportar_png(carpeta="reportes", prefijo="pendulo") -> [rutas]
generar_figuras_estaticas(datos, carpeta="reportes", prefijo="pendulo") -> [rutas]

# main.py: modo sin GUI (linea de comandos), ademas de lanzar la GUI.
# python -m src.main --sin-gui --m 0.05 --M 2.0 --v0 300 --L 2.0 [--metodo exacto ...]
```

### Semantica de las magnitudes del dict de oscilacion

- `t`     : tiempo (s)
- `theta` : angulo respecto a la vertical (rad), `theta(0)=0`
- `omega` : velocidad angular (rad/s), `omega(0)=v1/L`
- `v`     : rapidez tangencial, `v = L*omega` (m/s)
- `p`     : momentum lineal, `p = (m+M)*v` (kg*m/s)
- `ek`    : energia cinetica, `Ek = 0.5*(m+M)*v^2` (J)
- `x`, `y`  : posicion del centro de masa respecto al pivote (m)
- `ep`      : energia potencial gravitatoria, referencia en `theta=0` (J)
- `emec`    : energia mecanica total, `Ek + Ep` (J); constante sin
  amortiguamiento, decreciente con el
- `tension` : tension de la cuerda (N)
- `alpha`   : aceleracion angular (rad/s^2)
- `metodo`, `theta_max`, `periodo_aproximado`, `periodo_exacto` : escalares
  (no arreglos) con el metodo usado, la amplitud maxima alcanzada y los dos
  periodos (angulos pequenos vs integral eliptica).

## Modelo fisico

- Colision: perfectamente inelastica (baseline, conservacion del momentum
  lineal), con extensiones para el metodo exacto (inercia rotacional,
  impacto no central via conservacion del momento angular respecto al
  pivote) y coeficiente de restitucion (choques parcialmente elasticos).
- Oscilacion:
  - **Aproximado**: pendulo simple, `theta'' = -(g/L)sin(theta)`.
  - **Exacto**: pendulo fisico, `I_total*theta'' = -(M*L + m*b)*g*sin(theta)`,
    con `I_total = I_caja_cm + M*L^2 + m*b^2` (se reduce al aproximado con
    `I_caja_cm=0`, `b=L`).
  - Ambos admiten amortiguamiento viscoso opcional: se resta `gamma*omega`.
  - `g = 9.81`, integrado con `scipy.integrate.solve_ivp` (RK45, `rtol=atol=1e-9`).
    Sin aproximacion de angulos pequenos.
  - Periodo real por integral eliptica completa de primer tipo (`scipy.special.ellipk`)
    vs la aproximacion de angulos pequenos (`2*pi*sqrt(L/g)`).

## Estado y pendientes (Informe Final)

Todos los `TODO` de codigo repartidos por modulo estan implementados (ver
detalle y checklist en `TAREAS_INFORME_FINAL.md`). Solo quedan las tareas de
integracion del grupo (validacion con distintos parametros, correccion de
errores y redaccion del Informe Final), que no son de codigo.

## Estado de los modulos

- `colision.py`   : IMPLEMENTADO (baseline + metodo exacto + restitucion). Cristopher Arauz.
- `oscilacion.py` : IMPLEMENTADO (baseline + metodo exacto + amortiguamiento + periodos). Sidney Rodriguez.
- `graficas.py`   : IMPLEMENTADO (graficas 1-9, export PNG, comparaciones, blitting). Maciel Gomez.
- `interfaz.py`   : IMPLEMENTADO (GUI completa: metodo, amortiguamiento, pausar/reiniciar, panel numerico, validaciones). Tatiana Solis.
- `main.py`/`run.py`: IMPLEMENTADO (GUI + modo `--sin-gui` por linea de comandos).

`python run.py` lanza la GUI completa con todas las funcionalidades del
Informe Final. `python -m src.main --sin-gui ...` corre una simulacion y
exporta las graficas a PNG sin abrir ninguna ventana.

## Como ejecutar / verificar

```bash
python run.py                          # un solo comando: instala deps y lanza la GUI
python -m src.colision                 # demo + verificacion del modulo de colision
python -m src.oscilacion               # demo + verificacion del modulo de oscilacion
python -m src.graficas                 # demo interactiva del panel de graficas
python -m src.main --sin-gui --metodo exacto --amortiguamiento \
    --coef-amortiguamiento 0.2 --salida reportes   # simulacion + PNG sin GUI
```
