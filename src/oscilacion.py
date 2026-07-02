# -*- coding: utf-8 -*-
"""
Modulo: oscilacion.py
Responsable: Sidney Rodriguez

Que modela:
    El movimiento oscilatorio del pendulo (caja + proyectil incrustado) tras la
    colision. Se modela como un pendulo simple de masa puntual (m + M) colgado de
    una cuerda ideal de longitud L. La ecuacion diferencial que gobierna el
    angulo theta(t) respecto a la vertical es:

        theta''(t) = -(g / L) * sin(theta)        con g = 9.81 m/s^2

    Debe integrarse con scipy.integrate.solve_ivp (sin aproximacion de angulos
    pequenos). Condiciones iniciales sugeridas:
        theta(0) = 0
        omega(0) = v1 / L     (omega0)

Estado:
    Baseline implementado. Metodo aproximado: masa puntual, sin friccion ni
    amortiguamiento.

Contrato (no cambiar la firma):
    simular_oscilacion(m, M, L, v1, t_max, dt) -> dict(t, theta, omega, v, p, ek)

    Donde cada clave es un arreglo NumPy de igual longitud:
        t     : tiempo (s)
        theta : angulo respecto a la vertical (rad)
        omega : velocidad angular (rad/s)
        v     : rapidez tangencial, v = L*omega (m/s)
        p     : momentum lineal, p = (m+M)*v (kg*m/s)
        ek    : energia cinetica, Ek = 0.5*(m+M)*v^2 (J)

TODO (baseline):
    - [x] Definir la ecuacion del pendulo theta'' = -(g/L) sin(theta).
    - [x] Integrar con solve_ivp usando t_eval = arange(0, t_max, dt).
    - [x] Calcular las magnitudes derivadas v, p, ek y armar el dict de salida.
    - [x] Validar parametros (L > 0, t_max > 0, dt > 0).
TODO (Informe Final):
    - [ ] Metodo exacto: pendulo fisico con inercia rotacional.
    - [ ] Agregar amortiguamiento viscoso.
    - [ ] Periodo real por integral eliptica vs aproximacion de angulos pequenos.
    - [ ] Datos para las graficas 5-9.
"""

import numpy as np
import scipy.integrate as integrate

# Gravedad estandar usada por el modelo (m/s^2).
GRAVEDAD = 9.81


def simular_oscilacion(m, M, L, v1, t_max, dt):
    """
    Integra la oscilacion del pendulo balistico desde t=0 hasta t=t_max.

    Parametros:
        m     : masa del proyectil (kg).
        M     : masa de la caja (kg).
        L     : longitud de la cuerda (m).
        v1    : velocidad lineal del conjunto tras el impacto (m/s).
        t_max : tiempo total de simulacion (s).
        dt    : paso de muestreo para los arreglos de salida (s).

    Retorna:
        dict con arreglos NumPy: t, theta, omega, v, p, ek.
    """
    # Validaciones de parametros.
    if L <= 0:
        raise ValueError("La longitud de la cuerda L debe ser mayor que cero.")
    if t_max <= 0:
        raise ValueError("El tiempo total de simulacion t_max debe ser mayor que cero.")
    if dt <= 0:
        raise ValueError("El paso de muestreo dt debe ser mayor que cero.")

    # Masa total del conjunto tras el impacto.
    masa_total = m + M

    # Condiciones iniciales: theta(0) = 0, omega(0) = v1 / L.
    theta0 = 0.0
    omega0 = v1 / L
    estado_inicial = [theta0, omega0]

    # Tiempos de evaluacion solicitados.
    t_eval = np.arange(0, t_max, dt)

    # Ecuacion diferencial del pendulo simple en forma de sistema de primer orden.
    # Se reescribe theta'' = -(g/L)*sin(theta) como:
    #   dy[0]/dt = y[1]            (derivada del angulo = omega)
    #   dy[1]/dt = -(g/L)*sin(y[0]) (derivada de omega = aceleracion angular)
    def _ecuacion_pendulo(t, y):
        theta, omega = y
        dtheta_dt = omega
        domega_dt = -(GRAVEDAD / L) * np.sin(theta)
        return [dtheta_dt, domega_dt]

    # Integracion numerica con el metodo RK45 (Runge-Kutta de orden 4-5).
    solucion = integrate.solve_ivp(
        fun=_ecuacion_pendulo,
        t_span=(0.0, t_max),
        y0=estado_inicial,
        method="RK45",
        t_eval=t_eval,
        dense_output=False,
    )

    # Extraccion de resultados.
    t = solucion.t
    theta = solucion.y[0]
    omega = solucion.y[1]

    # Magnitudes derivadas.
    v = L * omega                         # rapidez tangencial (m/s)
    p = masa_total * v                    # momentum lineal (kg*m/s)
    ek = 0.5 * masa_total * v ** 2        # energia cinetica (J)

    return {
        "t": t,
        "theta": theta,
        "omega": omega,
        "v": v,
        "p": p,
        "ek": ek,
    }


def _demostracion():
    """Pequeña demo que se ejecuta con `python -m src.oscilacion`."""
    m, M, L, v1, t_max, dt = 0.05, 2.0, 2.0, 1.2, 3.0, 0.05

    print("Demostracion del modulo oscilacion.py (responsable: Sidney Rodriguez)")
    print("Parametros: m={} kg, M={} kg, L={} m, v1={} m/s, t_max={} s, dt={} s".format(
        m, M, L, v1, t_max, dt))

    datos = simular_oscilacion(m, M, L, v1, t_max, dt)

    theta_max_rad = np.max(np.abs(datos["theta"]))
    theta_max_deg = np.degrees(theta_max_rad)
    ek_max = np.max(datos["ek"])

    print("Tiempo maximo simulado   = {:.4f} s".format(datos["t"][-1]))
    print("Angulo maximo alcanzado  = {:.6f} rad  ({:.4f} grados)".format(
        theta_max_rad, theta_max_deg))
    print("Energia cinetica maxima  = {:.6f} J".format(ek_max))

    # Verificacion: todos los arreglos deben tener el mismo numero de muestras.
    assert len(datos["t"]) == len(datos["theta"]), \
        "Error: el arreglo 't' y el arreglo 'theta' tienen distinto tamano."
    print("Verificacion de tamannos de arreglos: OK")


if __name__ == "__main__":
    _demostracion()
