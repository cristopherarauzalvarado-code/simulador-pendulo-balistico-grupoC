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
simular_oscilacion(m, M, L, v1, t_max, dt, **kwargs) -> dict(
    t, theta, omega, v, p, ek,                  # arreglos NumPy (baseline)
    x_cm, y_cm, ep, emec, tension,              # arreglos NumPy (nuevos)
    T_real, T_aprox)                            # escalares (periodos)

# graficas.py  (Responsable: Maciel Gomez)
PanelGraficas.agregar_punto(t, theta, omega, p, ek)

# interfaz.py  (Responsable: Tatiana Solis)
App(tk.Tk)
lanzar()
```

### Semantica de las magnitudes del dict de oscilacion

- `t`      : tiempo (s)
- `theta`  : angulo respecto a la vertical (rad), `theta(0)=0`
- `omega`  : velocidad angular (rad/s), `omega(0)=v1/L` o `omega1` (kwarg)
- `v`      : velocidad tangencial del CM, `v = L_cm*omega` (m/s), con signo
- `p`      : momentum lineal, `p = (m+M)*v` (kg*m/s)
- `ek`     : energia cinetica rotacional, `Ek = 0.5*I*omega^2` (J)
- `x_cm`   : posicion horizontal del CM, `x = L_cm*sin(theta)` (m)
- `y_cm`   : posicion vertical del CM, `y = -L_cm*cos(theta)` (m)
- `ep`     : energia potencial, `Ep = (m+M)*g*L_cm*(1-cos(theta))` (J)
- `emec`   : energia mecanica total, `Emec = Ek + Ep` (J)
- `tension`: tension de la cuerda (N)
- `T_real` : periodo real por integral eliptica (s) - escalar
- `T_aprox`: periodo de angulos pequenos (s) - escalar

## Modelo fisico

- Colision: perfectamente inelastica, conservacion del momentum lineal. Metodo
  exacto con inercia rotacional, impacto no central y coeficiente de restitucion.
- Oscilacion: pendulo fisico con amortiguamiento viscoso, ecuacion completa
  `theta'' = -((m+M)*g*L_cm/I)*sin(theta) - (b/I)*omega`, `g = 9.81`,
  integrada con `scipy.integrate.solve_ivp` (RK45). Sin aproximacion de angulos
  pequenos. Periodo calculado por integral eliptica.
- Modo baseline (sin kwargs): masa puntual, sin amortiguamiento — identico al
  original.

## Estado y pendientes (Informe Final)

Resumen de los `TODO` repartidos por modulo:

- **colision:** ~~inercia rotacional, impacto no central, coeficiente de
  restitucion~~ COMPLETADO.
- **oscilacion:** ~~metodo exacto (pendulo fisico con inercia), amortiguamiento,
  periodo por integral eliptica, datos para graficas 5-9~~ COMPLETADO.
- **graficas:** graficas 5-9 (Ep, energia total, retrato de fase, alpha, altura),
  exportar a PNG, comparar simulaciones, blitting.
- **interfaz:** pausar/reanudar/reiniciar, selector de metodo, casilla de
  amortiguamiento, panel numerico, validaciones.

## Estado de los modulos

- `colision.py`   : IMPLEMENTADO (Cristopher Arauz).
- `oscilacion.py` : IMPLEMENTADO - baseline + metodo exacto (Sidney Rodriguez).
- `graficas.py`   : IMPLEMENTADO - baseline 4 graficas 2x2 (Maciel Gomez).
- `interfaz.py`   : IMPLEMENTADO - baseline GUI + animacion (Tatiana Solis).
- `main.py`/`run.py`: andamiaje compartido listo.

Todos los modulos del baseline estan implementados y conectados: `python run.py`
lanza la GUI completa. Quedan pendientes los TODO del Informe Final de graficas
e interfaz (ver arriba).

## Como ejecutar / verificar

```bash
python run.py             # un solo comando: instala deps y lanza la GUI
python -m src.colision    # demo + verificacion del modulo de colision (listo)
python -m src.oscilacion  # demo + verificacion del modulo de oscilacion (listo)
```
