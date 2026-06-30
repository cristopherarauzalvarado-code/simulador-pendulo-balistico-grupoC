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

### Semantica de las magnitudes del dict de oscilacion

- `t`     : tiempo (s)
- `theta` : angulo respecto a la vertical (rad), `theta(0)=0`
- `omega` : velocidad angular (rad/s), `omega(0)=v1/L`
- `v`     : rapidez tangencial, `v = L*omega` (m/s)
- `p`     : momentum lineal, `p = (m+M)*v` (kg*m/s)
- `ek`    : energia cinetica, `Ek = 0.5*(m+M)*v^2` (J)

## Modelo fisico

- Colision: perfectamente inelastica, conservacion del momentum lineal.
- Oscilacion: pendulo simple, ecuacion completa `theta'' = -(g/L)sin(theta)`,
  `g = 9.81`, integrada con `scipy.integrate.solve_ivp` (RK45). Sin aproximacion
  de angulos pequenos.
- Baseline **aproximado**: masa puntual, sin friccion/amortiguamiento.

## Estado y pendientes (Informe Final)

Resumen de los `TODO` repartidos por modulo:

- **colision:** inercia rotacional, impacto no central, coeficiente de
  restitucion.
- **oscilacion:** metodo exacto (pendulo fisico con inercia), amortiguamiento,
  periodo por integral eliptica, datos para graficas 5-9.
- **graficas:** graficas 5-9 (Ep, energia total, retrato de fase, alpha, altura),
  exportar a PNG, comparar simulaciones, blitting.
- **interfaz:** pausar/reanudar/reiniciar, selector de metodo, casilla de
  amortiguamiento, panel numerico, validaciones.

## Estado de los modulos

- `colision.py`   : IMPLEMENTADO (Cristopher Arauz).
- `oscilacion.py` : PENDIENTE - esqueleto con firma y TODO (Sidney Rodriguez).
- `graficas.py`   : PENDIENTE - esqueleto con firma y TODO (Maciel Gomez).
- `interfaz.py`   : PENDIENTE - esqueleto con firma y TODO (Tatiana Solis).
- `main.py`/`run.py`: andamiaje compartido listo.

Cada integrante implementa su propio modulo respetando el contrato. Los
esqueletos pendientes lanzan `NotImplementedError` hasta que se desarrollen.

## Como ejecutar / verificar

```bash
python run.py             # un solo comando: instala deps y lanza la GUI
                          # (requiere los modulos pendientes ya implementados)
python -m src.colision    # demo + verificacion del modulo de colision (listo)
```
