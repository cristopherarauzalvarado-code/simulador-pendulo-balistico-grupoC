# -*- coding: utf-8 -*-
"""
Modulo: oscilacion.py
Responsable: Sidney Rodriguez

Que modela:
    El movimiento oscilatorio del pendulo (caja + proyectil incrustado) tras la
    colision. Soporta dos modos:

    1. Baseline (masa puntual, sin friccion):
        theta''(t) = -(g / L) * sin(theta)

    2. Pendulo fisico con amortiguamiento viscoso:
        theta''(t) = -((m+M)*g*L_cm / I) * sin(theta) - (b_amort / I) * omega

    donde I es el momento de inercia total respecto al pivote, L_cm es la
    distancia del pivote al centro de masa del conjunto, y b_amort es el
    coeficiente de amortiguamiento viscoso. Cuando I = (m+M)*L^2, L_cm = L y
    b_amort = 0, la ecuacion se reduce exactamente al baseline.

    Debe integrarse con scipy.integrate.solve_ivp (sin aproximacion de angulos
    pequenos). Condiciones iniciales:
        theta(0) = 0
        omega(0) = v1 / L        (baseline)
        omega(0) = omega1         (metodo exacto, via kwarg)

Estado:
    Implementado: baseline + metodo exacto (pendulo fisico con inercia
    rotacional), amortiguamiento viscoso, periodo por integral eliptica,
    y datos para graficas 5-9.

Contrato (no cambiar la firma de los 6 argumentos posicionales):
    simular_oscilacion(m, M, L, v1, t_max, dt, **kwargs) -> dict(
        t, theta, omega, v, p, ek,             # claves del baseline
        x_cm, y_cm, ep, emec, tension,         # magnitudes adicionales
        T_real, T_aprox)                       # periodos (escalares)

    Los kwargs opcionales son: omega1, I_total, L_cm, b_amort.
    Cuando no se pasan kwargs, el comportamiento es identico al baseline.

    Donde cada clave (salvo T_real y T_aprox) es un arreglo NumPy de igual
    longitud:
        t       : tiempo (s)
        theta   : angulo respecto a la vertical (rad)
        omega   : velocidad angular (rad/s)
        v       : velocidad tangencial del CM, v = L_cm*omega (m/s), con signo
        p       : momentum lineal, p = (m+M)*v (kg*m/s), con signo
        ek      : energia cinetica rotacional, Ek = 0.5*I*omega^2 (J)
        x_cm    : posicion horizontal del CM, x = L_cm*sin(theta) (m)
        y_cm    : posicion vertical del CM, y = -L_cm*cos(theta) (m)
        ep      : energia potencial, Ep = (m+M)*g*L_cm*(1 - cos(theta)) (J)
        emec    : energia mecanica total, Emec = Ek + Ep (J)
        tension : tension de la cuerda (N)
        T_real  : periodo real por integral eliptica (s) - escalar, asume b_amort=0
        T_aprox : periodo de angulos pequenos (s) - escalar, asume b_amort=0

TODO (baseline):
    - [x] Definir la ecuacion del pendulo theta'' = -(g/L) sin(theta).
    - [x] Integrar con solve_ivp usando t_eval = arange(0, t_max, dt).
    - [x] Calcular las magnitudes derivadas v, p, ek y armar el dict de salida.
    - [x] Validar parametros (L > 0, t_max > 0, dt > 0).
TODO (Informe Final):
    - [x] Metodo exacto: pendulo fisico con inercia rotacional.
    - [x] Agregar amortiguamiento viscoso.
    - [x] Periodo real por integral eliptica vs aproximacion de angulos pequenos.
    - [x] Datos para las graficas 5-9.
"""

import numpy as np
import scipy.integrate as integrate
from scipy.special import ellipk

# Gravedad estandar usada por el modelo (m/s^2).
GRAVEDAD = 9.81


def parametros_pendulo_fisico(m, M, L, I_caja_cm=0.0, b_impacto=None):
    """
    Calcula el momento de inercia total (I_total) y la distancia del pivote al
    centro de masa del conjunto (L_cm) para un pendulo fisico compuesto por una
    caja de masa M (con CM a distancia L del pivote) y un proyectil de masa m
    incrustado a distancia b_impacto del pivote.

    Formulas:
        I_total = (I_caja_cm + M * L^2) + m * b_impacto^2
        L_cm    = (M * L + m * b_impacto) / (m + M)

    Caso baseline (I_caja_cm = 0, b_impacto = L):
        I_total = (m + M) * L^2
        L_cm    = L

    Parametros:
        m          : masa del proyectil (kg), debe ser > 0.
        M          : masa de la caja (kg), debe ser >= 0.
        L          : distancia del pivote al CM de la caja (m), debe ser > 0.
        I_caja_cm  : momento de inercia de la caja respecto a su propio centro
                     de masa (kg*m^2), debe ser >= 0. Por defecto 0.0 (caja
                     tratada como masa puntual).
        b_impacto  : distancia del pivote al punto de impacto del proyectil (m),
                     debe ser > 0. Por defecto None, equivalente a b_impacto = L
                     (impacto en el CM de la caja).

    Retorna:
        dict con:
            I_total : momento de inercia total respecto al pivote (kg*m^2).
            L_cm    : distancia del pivote al CM del conjunto (m).
    """
    if m <= 0:
        raise ValueError("La masa del proyectil m debe ser mayor que cero.")
    if M < 0:
        raise ValueError("La masa de la caja M no puede ser negativa.")
    if L <= 0:
        raise ValueError("La distancia L debe ser mayor que cero.")
    if I_caja_cm < 0:
        raise ValueError(
            "El momento de inercia I_caja_cm no puede ser negativo.")
    if b_impacto is None:
        b_impacto = L
    if b_impacto <= 0:
        raise ValueError(
            "La distancia de impacto b_impacto debe ser mayor que cero.")

    I_total = (I_caja_cm + M * L ** 2) + m * b_impacto ** 2
    L_cm = (M * L + m * b_impacto) / (m + M)
    return {"I_total": I_total, "L_cm": L_cm}


def simular_oscilacion(m, M, L, v1, t_max, dt, **kwargs):
    """
    Integra la oscilacion del pendulo balistico desde t=0 hasta t=t_max.

    Soporta dos modos de operacion:
    - Sin kwargs: baseline (masa puntual, sin friccion). Identico al original.
    - Con kwargs: pendulo fisico con inercia rotacional y/o amortiguamiento.

    Parametros posicionales (contrato - no cambiar):
        m     : masa del proyectil (kg).
        M     : masa de la caja (kg).
        L     : longitud de la cuerda (m).
        v1    : velocidad lineal del conjunto tras el impacto (m/s).
        t_max : tiempo total de simulacion (s).
        dt    : paso de muestreo para los arreglos de salida (s).

    Kwargs opcionales:
        omega1  : velocidad angular inicial (rad/s). Si None, se calcula como
                  v1 / L (baseline). Usar el valor de
                  colision.velocidad_angular_tras_impacto_exacto para el
                  metodo exacto.
        I_total : momento de inercia total respecto al pivote (kg*m^2). Si
                  None, se calcula como (m+M)*L^2 (masa puntual).
        L_cm    : distancia del pivote al CM del conjunto (m). Si None, usa L.
        b_amort : coeficiente de amortiguamiento viscoso (kg*m^2/s). Por
                  defecto 0.0 (sin amortiguamiento).

    Nota: I_total y L_cm deben proporcionarse juntos o no proporcionarse.
    Pasar solo uno de los dos genera un ValueError.

    Retorna:
        dict con arreglos NumPy: t, theta, omega, v, p, ek, x_cm, y_cm, ep,
        emec, tension, y escalares: T_real, T_aprox.
    """
    # Validaciones de parametros posicionales.
    if L <= 0:
        raise ValueError("La longitud de la cuerda L debe ser mayor que cero.")
    if t_max <= 0:
        raise ValueError(
            "El tiempo total de simulacion t_max debe ser mayor que cero.")
    if dt <= 0:
        raise ValueError("El paso de muestreo dt debe ser mayor que cero.")

    # Masa total del conjunto tras el impacto.
    masa_total = m + M

    # --- Extraccion y validacion de kwargs ---
    omega0 = kwargs.get("omega1", None)
    I_ef = kwargs.get("I_total", None)
    L_cm_ef = kwargs.get("L_cm", None)
    b_amort = kwargs.get("b_amort", 0.0)

    # Politica de coherencia: I_total y L_cm deben ir juntos.
    if (I_ef is None) != (L_cm_ef is None):
        raise ValueError(
            "I_total y L_cm deben proporcionarse juntos o no proporcionarse.")

    # Valores efectivos: si no se proporcionan, usar defaults del baseline.
    if I_ef is None:
        I_ef = masa_total * L ** 2      # masa puntual a distancia L
        L_cm_ef = L                      # CM a distancia L del pivote
    else:
        if I_ef <= 0:
            raise ValueError(
                "El momento de inercia I_total debe ser mayor que cero.")
        if L_cm_ef <= 0:
            raise ValueError(
                "La distancia al CM L_cm debe ser mayor que cero.")

    if b_amort < 0:
        raise ValueError(
            "El coeficiente de amortiguamiento b_amort no puede ser negativo.")

    # Condicion inicial de velocidad angular.
    if omega0 is None:
        omega0 = v1 / L

    # Condiciones iniciales: theta(0) = 0, omega(0) = omega0.
    theta0 = 0.0
    estado_inicial = [theta0, omega0]

    # Tiempos de evaluacion solicitados.
    t_eval = np.arange(0, t_max, dt)

    # Ecuacion diferencial del pendulo fisico con amortiguamiento viscoso, en
    # forma de sistema de primer orden:
    #   dy[0]/dt = y[1]                                        (theta' = omega)
    #   dy[1]/dt = -((m+M)*g*L_cm / I)*sin(theta) - (b/I)*omega
    #
    # Con I = (m+M)*L^2, L_cm = L y b_amort = 0, se reduce al baseline:
    #   dy[1]/dt = -(g/L)*sin(theta)
    def _ecuacion_pendulo(t, y):
        theta, omega = y
        dtheta_dt = omega
        domega_dt = (-(masa_total * GRAVEDAD * L_cm_ef) / I_ef) \
            * np.sin(theta) - (b_amort / I_ef) * omega
        return [dtheta_dt, domega_dt]

    # Integracion numerica con el metodo RK45 (Runge-Kutta de orden 4-5).
    solucion = integrate.solve_ivp(
        fun=_ecuacion_pendulo,
        t_span=(0.0, t_max),
        y0=estado_inicial,
        method="RK45",
        t_eval=t_eval,
        rtol=1e-10,
        atol=1e-12,
        dense_output=False,
    )

    # Extraccion de resultados.
    t = solucion.t
    theta = solucion.y[0]
    omega = solucion.y[1]

    # --- Magnitudes derivadas (baseline, actualizadas para pendulo fisico) ---
    # v mantiene el signo de omega para preservar la direccion del momentum.
    v = L_cm_ef * omega                   # velocidad tangencial del CM (m/s)
    p = masa_total * v                    # momentum lineal (kg*m/s)
    ek = 0.5 * I_ef * omega ** 2          # energia cinetica rotacional (J)

    # --- Magnitudes nuevas (graficas 5-9) ---
    x_cm = L_cm_ef * np.sin(theta)        # posicion X del CM (m)
    y_cm = -L_cm_ef * np.cos(theta)       # posicion Y del CM (m)
    ep = masa_total * GRAVEDAD * L_cm_ef * (1.0 - np.cos(theta))  # Ep (J)
    emec = ek + ep                        # energia mecanica total (J)
    tension = masa_total * (GRAVEDAD * np.cos(theta)
                            + L_cm_ef * omega ** 2)  # tension (N)

    # --- Periodo por integral eliptica (valido para b_amort = 0) ---
    # Se busca el primer maximo local de |theta| como amplitud representativa.
    # Para oscilacion sin amortiguamiento coincide con max(|theta|). Para
    # oscilacion amortiguada, el primer pico es el de mayor amplitud.
    abs_theta = np.abs(theta)
    theta0_amp = 0.0
    for i in range(1, len(abs_theta) - 1):
        if abs_theta[i] > abs_theta[i - 1] \
                and abs_theta[i] >= abs_theta[i + 1]:
            theta0_amp = abs_theta[i]
            break
    # Si no se encontro un maximo local (e.g. t_max muy corto), usar el maximo
    # global del arreglo.
    if theta0_amp == 0.0 and len(abs_theta) > 0:
        theta0_amp = float(np.max(abs_theta))

    # Longitud equivalente del pendulo simple: l_eq = I / ((m+M)*g*L_cm).
    longitud_eq = I_ef / (masa_total * GRAVEDAD * L_cm_ef)
    T_aprox = 2.0 * np.pi * np.sqrt(longitud_eq)

    if theta0_amp > 0.0:
        k_cuadrado = np.sin(theta0_amp / 2.0) ** 2
        T_real = 4.0 * np.sqrt(longitud_eq) * float(ellipk(k_cuadrado))
    else:
        # Caso degenerado: sin oscilacion (theta0 = 0).
        T_real = T_aprox

    return {
        "t": t,
        "theta": theta,
        "omega": omega,
        "v": v,
        "p": p,
        "ek": ek,
        "x_cm": x_cm,
        "y_cm": y_cm,
        "ep": ep,
        "emec": emec,
        "tension": tension,
        "T_real": T_real,
        "T_aprox": T_aprox,
    }


def calcular_periodos(m, M, L, theta0, **kwargs):
    """
    Calcula el periodo real (integral eliptica) y el periodo aproximado (angulos
    pequenos) del pendulo, sin necesidad de simular la oscilacion completa.

    Las formulas asumen oscilacion conservativa (sin amortiguamiento, b_amort=0).

    Parametros:
        m      : masa del proyectil (kg).
        M      : masa de la caja (kg).
        L      : longitud de la cuerda (m), debe ser > 0.
        theta0 : amplitud maxima de la oscilacion (rad), debe ser >= 0.

    Kwargs opcionales:
        I_total : momento de inercia total respecto al pivote (kg*m^2).
        L_cm    : distancia del pivote al CM del conjunto (m).

    Nota: I_total y L_cm deben proporcionarse juntos o no proporcionarse.

    Retorna:
        dict con:
            T_real    : periodo real por integral eliptica (s).
            T_aprox   : periodo de angulos pequenos (s).
            error_pct : error porcentual de la aproximacion respecto al real (%).
    """
    if L <= 0:
        raise ValueError("La longitud de la cuerda L debe ser mayor que cero.")
    if theta0 < 0:
        raise ValueError("La amplitud theta0 no puede ser negativa.")

    masa_total = m + M

    I_ef = kwargs.get("I_total", None)
    L_cm_ef = kwargs.get("L_cm", None)

    # Politica de coherencia: I_total y L_cm deben ir juntos.
    if (I_ef is None) != (L_cm_ef is None):
        raise ValueError(
            "I_total y L_cm deben proporcionarse juntos o no proporcionarse.")

    if I_ef is None:
        I_ef = masa_total * L ** 2
        L_cm_ef = L
    else:
        if I_ef <= 0:
            raise ValueError(
                "El momento de inercia I_total debe ser mayor que cero.")
        if L_cm_ef <= 0:
            raise ValueError(
                "La distancia al CM L_cm debe ser mayor que cero.")

    # Longitud equivalente del pendulo simple: l_eq = I / ((m+M)*g*L_cm).
    longitud_eq = I_ef / (masa_total * GRAVEDAD * L_cm_ef)
    T_aprox = 2.0 * np.pi * np.sqrt(longitud_eq)

    if theta0 > 0.0:
        k_cuadrado = np.sin(theta0 / 2.0) ** 2
        T_real = 4.0 * np.sqrt(longitud_eq) * float(ellipk(k_cuadrado))
    else:
        T_real = T_aprox

    error_pct = (abs(T_real - T_aprox) / T_real * 100.0) \
        if T_real > 0.0 else 0.0

    return {"T_real": T_real, "T_aprox": T_aprox, "error_pct": error_pct}


def _demostracion():
    """Pequena demo que se ejecuta con `python -m src.oscilacion`."""
    # --- Demo 1: baseline (sin kwargs) ---
    m, M, L, v1, t_max, dt = 0.05, 2.0, 2.0, 1.2, 3.0, 0.05

    print("Demostracion del modulo oscilacion.py (responsable: Sidney Rodriguez)")
    print("=" * 72)
    print()
    print("1) Baseline (masa puntual, sin amortiguamiento)")
    print("Parametros: m={} kg, M={} kg, L={} m, v1={} m/s, t_max={} s, "
          "dt={} s".format(m, M, L, v1, t_max, dt))

    datos = simular_oscilacion(m, M, L, v1, t_max, dt)

    theta_max_rad = np.max(np.abs(datos["theta"]))
    theta_max_deg = np.degrees(theta_max_rad)
    ek_max = np.max(datos["ek"])

    print("Tiempo maximo simulado   = {:.4f} s".format(datos["t"][-1]))
    print("Angulo maximo alcanzado  = {:.6f} rad  ({:.4f} grados)".format(
        theta_max_rad, theta_max_deg))
    print("Energia cinetica maxima  = {:.6f} J".format(ek_max))
    print("Periodo real (eliptica)  = {:.6f} s".format(datos["T_real"]))
    print("Periodo aprox (peq. ang) = {:.6f} s".format(datos["T_aprox"]))

    # Verificacion: todos los arreglos deben tener el mismo numero de muestras.
    claves_arreglos = ["t", "theta", "omega", "v", "p", "ek",
                       "x_cm", "y_cm", "ep", "emec", "tension"]
    n = len(datos["t"])
    for clave in claves_arreglos:
        assert len(datos[clave]) == n, \
            "Error: '{}' tiene {} elementos, se esperaban {}.".format(
                clave, len(datos[clave]), n)
    print("Verificacion de tamanos de arreglos: OK ({} muestras)".format(n))

    # Verificacion: energia mecanica constante (sin amortiguamiento).
    emec = datos["emec"]
    variacion_emec = np.max(emec) - np.min(emec)
    assert variacion_emec < 1e-4, \
        "Error: la energia mecanica varia {:.2e} J (deberia ser constante" \
        ").".format(variacion_emec)
    print("Verificacion de conservacion de energia: OK "
          "(variacion = {:.2e} J)".format(variacion_emec))

    # --- Demo 2: pendulo fisico con amortiguamiento ---
    print()
    print("2) Pendulo fisico con amortiguamiento")
    params = parametros_pendulo_fisico(m, M, L, I_caja_cm=0.02,
                                       b_impacto=1.8)
    print("   I_caja_cm=0.02 kg*m^2, b_impacto=1.8 m")
    print("   -> I_total = {:.6f} kg*m^2, L_cm = {:.6f} m".format(
        params["I_total"], params["L_cm"]))

    omega1 = 0.6  # velocidad angular inicial de ejemplo
    datos2 = simular_oscilacion(m, M, L, v1, t_max, dt,
                                omega1=omega1,
                                I_total=params["I_total"],
                                L_cm=params["L_cm"],
                                b_amort=0.05)

    emec2 = datos2["emec"]
    print("   omega1 = {} rad/s, b_amort = 0.05 kg*m^2/s".format(omega1))
    print("   Energia mecanica inicial = {:.6f} J".format(emec2[0]))
    print("   Energia mecanica final   = {:.6f} J".format(emec2[-1]))
    print("   Periodo real (eliptica)  = {:.6f} s".format(datos2["T_real"]))
    print("   Periodo aprox (peq. ang) = {:.6f} s".format(datos2["T_aprox"]))

    # Verificacion: energia mecanica debe decaer con amortiguamiento.
    assert emec2[-1] < emec2[0], \
        "Error: la energia mecanica no decae con amortiguamiento."
    print("   Verificacion de decaimiento de energia: OK")

    # --- Demo 3: funcion calcular_periodos ---
    print()
    print("3) Funcion calcular_periodos (independiente)")
    periodos = calcular_periodos(m, M, L, theta0=0.5)
    print("   theta0 = 0.5 rad (baseline) -> T_real = {:.6f} s, "
          "T_aprox = {:.6f} s, error = {:.4f}%".format(
              periodos["T_real"], periodos["T_aprox"], periodos["error_pct"]))

    periodos2 = calcular_periodos(m, M, L, theta0=0.5,
                                  I_total=params["I_total"],
                                  L_cm=params["L_cm"])
    print("   theta0 = 0.5 rad (fisico)   -> T_real = {:.6f} s, "
          "T_aprox = {:.6f} s, error = {:.4f}%".format(
              periodos2["T_real"], periodos2["T_aprox"],
              periodos2["error_pct"]))

    # --- Demo 4: verificacion de compatibilidad hacia atras ---
    print()
    print("4) Verificacion de compatibilidad hacia atras")
    # El baseline sin kwargs debe producir exactamente los mismos resultados
    # que la version original del modulo.
    datos_baseline = simular_oscilacion(m, M, L, v1, t_max, dt)
    v_esperado = L * datos_baseline["omega"]
    p_esperado = (m + M) * v_esperado
    ek_esperado = 0.5 * (m + M) * v_esperado ** 2

    assert np.allclose(datos_baseline["v"], v_esperado), \
        "Error: v no coincide con el baseline."
    assert np.allclose(datos_baseline["p"], p_esperado), \
        "Error: p no coincide con el baseline."
    assert np.allclose(datos_baseline["ek"], ek_esperado), \
        "Error: ek no coincide con el baseline."
    print("   v  = L*omega             : OK")
    print("   p  = (m+M)*v             : OK")
    print("   ek = 0.5*(m+M)*v^2       : OK")
    print("   Compatibilidad hacia atras verificada.")


if __name__ == "__main__":
    _demostracion()
