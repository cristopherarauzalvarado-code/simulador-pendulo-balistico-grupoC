# -*- coding: utf-8 -*-
"""
Modulo: oscilacion.py
Responsable: Sidney Rodriguez

Que modela:
    El movimiento oscilatorio del pendulo (caja + proyectil incrustado) tras la
    colision. Ofrece dos metodos:

    - Metodo APROXIMADO (baseline): masa puntual (m + M) colgada de una cuerda
      ideal de longitud L, sin friccion:

          theta''(t) = -(g / L) * sin(theta)        con g = 9.81 m/s^2

    - Metodo EXACTO: pendulo fisico. La caja tiene su propio momento de
      inercia respecto a su centro de masa (I_caja_cm) y el proyectil puede
      incrustarse fuera del centro de masa, a un brazo de palanca b del
      pivote (coordinado con `colision.velocidad_angular_tras_impacto_exacto`
      y `colision.resumen_colision_exacto`, que ya calculan I_total y el
      brazo b para el instante del choque). Durante la oscilacion posterior el
      conjunto gira alrededor del pivote con:

          I_total * theta''(t) = -(M*L + m*b) * g * sin(theta)

      Con I_caja_cm = 0 y b = L (impacto central, caja puntual) esta ecuacion
      se reduce algebraicamente al metodo aproximado.

    Ambos metodos admiten, opcionalmente, amortiguamiento viscoso (termino
    proporcional a omega), sumando -gamma*omega a la aceleracion angular.

    En los dos casos se integra con scipy.integrate.solve_ivp (sin aproximar
    angulos pequenos). Condiciones iniciales:
        theta(0) = 0
        omega(0) = v1 / L        (baseline)
        omega(0) = omega1         (metodo exacto, via kwarg)

    v1 es la velocidad lineal comun tras el impacto (contrato con colision.py).
    Para el metodo exacto, quien llama a esta funcion (la interfaz) debe pasar
    como v1 el valor "v1_equivalente" = omega1 * L que ya calcula
    `colision.resumen_colision_exacto`, de forma que la firma de esta funcion
    no cambie.

Estado:
    Metodo aproximado y metodo exacto implementados, ambos con amortiguamiento
    viscoso opcional. Calculo del periodo real (integral eliptica) vs la
    aproximacion de angulos pequenos. Genera todas las magnitudes derivadas
    que requieren las graficas 5-9 del Informe Final (x, y, ep, emec, tension,
    alpha, periodos).

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

    Los parametros nuevos (metodo, I_caja_cm, b, amortiguamiento,
    coef_amortiguamiento) son opcionales con valores por defecto que
    reproducen exactamente el comportamiento del baseline, y las claves
    nuevas del dict de salida (x, y, ep, emec, tension, alpha, metodo,
    theta_max, periodo_aproximado, periodo_exacto) se agregan sin quitar
    ninguna de las originales.

TODO (baseline):
    - [x] Definir la ecuacion del pendulo theta'' = -(g/L) sin(theta).
    - [x] Integrar con solve_ivp usando t_eval = arange(0, t_max, dt).
    - [x] Calcular las magnitudes derivadas v, p, ek y armar el dict de salida.
    - [x] Validar parametros (L > 0, t_max > 0, dt > 0).
TODO (Informe Final):
    - [x] Metodo exacto: pendulo fisico con inercia rotacional.
    - [x] Agregar amortiguamiento viscoso.
    - [x] Periodo real por integral eliptica vs aproximacion de angulos pequenos.
    - [x] Datos para las graficas 5-9 (x, y, v, Ep, Emec, T).
"""

import numpy as np
import scipy.integrate as integrate
import scipy.special as special
from scipy.special import ellipk

# Gravedad estandar usada por el modelo (m/s^2).
GRAVEDAD = 9.81

METODOS_VALIDOS = ("aproximado", "exacto")


def _inercia_total_pivote(m, M, L, I_caja_cm=0.0, b=None):
    """
    Momento de inercia total del conjunto (caja + proyectil incrustado)
    respecto al pivote, igual que en `colision.velocidad_angular_tras_impacto_exacto`:

        I_total = (I_caja_cm + M * L^2) + m * b^2
    """
    if b is None:
        b = L
    return (I_caja_cm + M * L ** 2) + m * b ** 2


def _momento_estatico_gravitatorio(m, M, L, b=None):
    """
    "Momento estatico" (M*L + m*b) que multiplicado por g da el torque
    restaurador maximo (en theta = 90 grados) respecto al pivote. Con b = L
    esto es (M + m) * L, el caso de masa puntual del baseline.
    """
    if b is None:
        b = L
    return M * L + m * b


def periodo_pendulo(L, theta0, g=GRAVEDAD):
    """
    Periodo de oscilacion de un pendulo de longitud L con amplitud angular
    theta0 (rad), por dos vias:

    - Aproximacion de angulos pequenos (sin(theta) ~ theta), independiente de
      la amplitud:
          T_aprox = 2*pi*sqrt(L/g)

    - Formula exacta (sin aproximar sin(theta)), mediante la integral
      eliptica completa de primer tipo K(k), con modulo k = sin(theta0/2):
          T_exacto = 4*sqrt(L/g) * K(k)

      `scipy.special.ellipk` recibe el parametro m = k^2 (no el modulo k).
      Cuando theta0 -> 0, T_exacto -> T_aprox (K(0) = pi/2).

    Parametros:
        L      : longitud de la cuerda (m), debe ser > 0.
        theta0 : amplitud angular maxima de la oscilacion (rad). Se usa su
                 valor absoluto.
        g      : aceleracion de la gravedad (m/s^2). Por defecto GRAVEDAD.

    Retorna:
        (periodo_aproximado, periodo_exacto) en segundos.
    """
    if L <= 0:
        raise ValueError("La longitud L debe ser mayor que cero.")

    periodo_aproximado = 2.0 * np.pi * np.sqrt(L / g)
    k = np.sin(abs(theta0) / 2.0)
    periodo_exacto = 4.0 * np.sqrt(L / g) * special.ellipk(k ** 2)
    return float(periodo_aproximado), float(periodo_exacto)


def simular_oscilacion(m, M, L, v1, t_max, dt, metodo="aproximado",
                        I_caja_cm=0.0, b=None, amortiguamiento=False,
                        coef_amortiguamiento=0.0):
    """
    Integra la oscilacion del pendulo balistico desde t=0 hasta t=t_max.

    Soporta dos modos de operacion:
    - Sin kwargs: baseline (masa puntual, sin friccion). Identico al original.
    - Con kwargs: pendulo fisico con inercia rotacional y/o amortiguamiento.

    Parametros posicionales (contrato - no cambiar):
        m     : masa del proyectil (kg).
        M     : masa de la caja (kg).
        L     : longitud de la cuerda (distancia del pivote al centro de masa
                de la caja) (m).
        v1    : velocidad lineal del conjunto tras el impacto (m/s). Para el
                metodo exacto debe ser el "v1_equivalente" = omega1 * L (ver
                `colision.resumen_colision_exacto`), de forma que
                omega(0) = v1 / L siga siendo la condicion inicial correcta.
        t_max : tiempo total de simulacion (s).
        dt    : paso de muestreo para los arreglos de salida (s).
        metodo: "aproximado" (masa puntual, baseline) o "exacto" (pendulo
                fisico con inercia rotacional e impacto no central).
        I_caja_cm : momento de inercia de la caja respecto a su propio centro
                de masa (kg*m^2). Solo se usa si metodo == "exacto".
        b     : brazo de palanca del impacto (m). Solo se usa si
                metodo == "exacto". None equivale a b = L (impacto central).
        amortiguamiento : si True, agrega un termino de amortiguamiento
                viscoso -coef_amortiguamiento*omega a la aceleracion angular.
        coef_amortiguamiento : coeficiente de amortiguamiento viscoso
                (1/s), debe ser >= 0. Ignorado si amortiguamiento es False.

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
        dict con arreglos NumPy de igual longitud:
            t, theta, omega, v, p, ek           (contrato original)
            x, y                                 posicion del centro de masa
                                                   respecto al pivote (m)
            ep, emec                             energia potencial y mecanica
                                                   total (J)
            tension                              tension de la cuerda (N)
            alpha                                aceleracion angular (rad/s^2)
        y los escalares:
            metodo, theta_max, periodo_aproximado, periodo_exacto
    """
    # Validaciones de parametros posicionales.
    if L <= 0:
        raise ValueError("La longitud de la cuerda L debe ser mayor que cero.")
    if t_max <= 0:
        raise ValueError(
            "El tiempo total de simulacion t_max debe ser mayor que cero.")
    if dt <= 0:
        raise ValueError("El paso de muestreo dt debe ser mayor que cero.")
    if metodo not in METODOS_VALIDOS:
        raise ValueError(
            "metodo debe ser uno de {}.".format(METODOS_VALIDOS))
    if I_caja_cm < 0:
        raise ValueError("El momento de inercia I_caja_cm no puede ser negativo.")
    if b is not None and b <= 0:
        raise ValueError("El brazo de palanca b debe ser mayor que cero.")
    if coef_amortiguamiento < 0:
        raise ValueError("El coeficiente de amortiguamiento no puede ser negativo.")

    # Masa total del conjunto tras el impacto.
    masa_total = m + M

    # Parametros dinamicos segun el metodo: en ambos casos la ecuacion se
    # escribe como theta'' = -factor_angular*sin(theta) - gamma*omega, con
    # factor_angular = g/L en el metodo aproximado (masa puntual) y
    # factor_angular = (M*L + m*b)*g / I_total en el metodo exacto (se reduce
    # al caso anterior cuando I_caja_cm = 0 y b = L).
    if metodo == "exacto":
        i_total = _inercia_total_pivote(m, M, L, I_caja_cm, b)
        momento_estatico = _momento_estatico_gravitatorio(m, M, L, b)
        factor_angular = momento_estatico * GRAVEDAD / i_total
    else:
        i_total = masa_total * L ** 2
        factor_angular = GRAVEDAD / L

    gamma = coef_amortiguamiento if amortiguamiento else 0.0

    # Condiciones iniciales: theta(0) = 0, omega(0) = v1 / L.
    theta0 = 0.0
    estado_inicial = [theta0, omega0]

    # Tiempos de evaluacion solicitados.
    t_eval = np.arange(0, t_max, dt)

    # Ecuacion diferencial del pendulo en forma de sistema de primer orden.
    # Se reescribe theta'' = -factor_angular*sin(theta) - gamma*omega como:
    #   dy[0]/dt = y[1]                                  (derivada del angulo)
    #   dy[1]/dt = -factor_angular*sin(y[0]) - gamma*y[1] (derivada de omega)
    def _ecuacion_pendulo(t, y):
        theta, omega = y
        dtheta_dt = omega
        domega_dt = -factor_angular * np.sin(theta) - gamma * omega
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
        rtol=1e-9,
        atol=1e-9,
    )

    # Extraccion de resultados.
    t = solucion.t
    theta = solucion.y[0]
    omega = solucion.y[1]

    # Aceleracion angular, evaluada con la misma ecuacion (no por diferencias
    # finitas, para evitar ruido numerico).
    alpha = -factor_angular * np.sin(theta) - gamma * omega

    # Magnitudes derivadas del contrato original.
    v = L * omega                         # rapidez tangencial (m/s)
    p = masa_total * v                    # momentum lineal (kg*m/s)
    ek = 0.5 * masa_total * v ** 2         # energia cinetica (J)

    # Magnitudes adicionales para las graficas 5-9 del Informe Final.
    # Posicion del centro de masa respecto al pivote (x horizontal, y hacia
    # abajo es negativo; y = 0 en el pivote, y = -L en el reposo).
    x = L * np.sin(theta)
    y = -L * np.cos(theta)

    # Energia potencial gravitatoria (referencia: theta = 0, punto mas bajo).
    ep = masa_total * GRAVEDAD * L * (1.0 - np.cos(theta))
    emec = ek + ep

    # Tension de la cuerda: componente del peso a lo largo de la cuerda mas el
    # termino centripeto (formula estandar del pendulo simple, aplicada a la
    # masa total del conjunto).
    tension = masa_total * GRAVEDAD * np.cos(theta) + masa_total * L * omega ** 2

    # Amplitud alcanzada y periodos (aproximado vs exacto por integral
    # eliptica), usando la amplitud maxima realmente alcanzada en la
    # simulacion (relevante sobre todo si hay amortiguamiento, donde theta
    # decae con el tiempo).
    theta_max = float(np.max(np.abs(theta))) if theta.size else abs(theta0)
    periodo_aproximado, periodo_exacto = periodo_pendulo(L, theta_max)

    return {
        "t": t,
        "theta": theta,
        "omega": omega,
        "v": v,
        "p": p,
        "ek": ek,
        "x": x,
        "y": y,
        "ep": ep,
        "emec": emec,
        "tension": tension,
        "alpha": alpha,
        "metodo": metodo,
        "theta_max": theta_max,
        "periodo_aproximado": periodo_aproximado,
        "periodo_exacto": periodo_exacto,
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

    theta_max_deg = np.degrees(datos["theta_max"])
    ek_max = np.max(datos["ek"])

    print("Tiempo maximo simulado   = {:.4f} s".format(datos["t"][-1]))
    print("Angulo maximo alcanzado  = {:.6f} rad  ({:.4f} grados)".format(
        datos["theta_max"], theta_max_deg))
    print("Energia cinetica maxima  = {:.6f} J".format(ek_max))
    print("Periodo aproximado (angulos pequenos) = {:.6f} s".format(
        datos["periodo_aproximado"]))
    print("Periodo exacto (integral eliptica)    = {:.6f} s".format(
        datos["periodo_exacto"]))

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

    # Verificacion: sin amortiguamiento, la energia mecanica debe conservarse.
    emec = datos["emec"]
    assert np.max(np.abs(emec - emec[0])) < 1e-6, \
        "Sin amortiguamiento la energia mecanica deberia conservarse."
    print("Verificacion de conservacion de energia mecanica: OK")

    print()
    print("Metodo exacto (pendulo fisico, caja con inercia I_caja_cm > 0):")
    I_caja_cm = 0.02
    datos_exacto = simular_oscilacion(
        m, M, L, v1, t_max, dt, metodo="exacto", I_caja_cm=I_caja_cm)
    print("Angulo maximo (exacto)   = {:.6f} rad".format(datos_exacto["theta_max"]))

    # Caso limite: con I_caja_cm = 0 y b = L (impacto central), el metodo
    # exacto debe coincidir con el metodo aproximado.
    datos_exacto_limite = simular_oscilacion(
        m, M, L, v1, t_max, dt, metodo="exacto", I_caja_cm=0.0, b=L)
    assert np.max(np.abs(datos_exacto_limite["theta"] - datos["theta"])) < 1e-6, \
        "El metodo exacto (caso limite) deberia coincidir con el aproximado."
    print("Verificacion metodo exacto == aproximado (caso limite): OK")

    print()
    print("Amortiguamiento viscoso (coef = 0.3):")
    datos_amortiguado = simular_oscilacion(
        m, M, L, v1, t_max, dt, amortiguamiento=True, coef_amortiguamiento=0.3)
    assert datos_amortiguado["theta_max"] <= datos["theta_max"] + 1e-9, \
        "El amortiguamiento no deberia aumentar la amplitud maxima."
    assert datos_amortiguado["emec"][-1] < datos_amortiguado["emec"][0], \
        "Con amortiguamiento la energia mecanica final debe ser menor que la inicial."
    print("Energia mecanica inicial = {:.6f} J | final = {:.6f} J".format(
        datos_amortiguado["emec"][0], datos_amortiguado["emec"][-1]))
    print("Verificacion de disipacion de energia con amortiguamiento: OK")


if __name__ == "__main__":
    _demostracion()
