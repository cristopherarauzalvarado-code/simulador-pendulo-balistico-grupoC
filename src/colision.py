# -*- coding: utf-8 -*-
"""
Modulo: colision.py
Responsable: Cristopher Arauz
Proyecto: pendulo-balistico-sim (Fisica I - CENFOTEC - Grupo C)

Que modela:
    La colision perfectamente inelastica entre el proyectil (masa m, velocidad
    v0) y la caja suspendida del pendulo (masa M, inicialmente en reposo). Tras
    el impacto el proyectil queda incrustado en la caja y ambos se mueven con una
    velocidad comun v1. Se aplica conservacion del momentum lineal:

        m * v0 = (m + M) * v1   =>   v1 = m * v0 / (m + M)

    En una colision inelastica NO se conserva la energia cinetica: parte de la
    energia se disipa (calor, deformacion). Este modulo calcula esa perdida.

    Ademas del baseline, el modulo ofrece el metodo exacto: trata la caja como
    un pendulo fisico (con su propio momento de inercia respecto a su centro
    de masa) y permite un impacto no central, mediante conservacion del
    momento angular respecto al pivote:

        m * v0 * b = I_total * omega1
        I_total = (I_caja_cm + M * L^2) + m * b^2

    donde b es el brazo de palanca del impacto (distancia perpendicular del
    pivote a la linea de accion de v0). Con I_caja_cm = 0 y b = L, este
    metodo exacto se reduce algebraicamente al baseline (omega1 = v1 / L).

    Tambien se ofrece un modelo de choque con coeficiente de restitucion e
    (0 = perfectamente inelastico / proyectil incrustado, hasta 1 = elastico),
    para choques donde el proyectil no queda necesariamente incrustado.

Estado:
    Baseline funcional (masa puntual, choque 1D horizontal, e = 0) mas
    extensiones para el Informe Final: metodo exacto con inercia rotacional,
    impacto no central y coeficiente de restitucion.

Contrato (no cambiar la firma):
    velocidad_tras_impacto(m, M, v0) -> v1

TODO (Informe Final):
    - [x] Considerar el caso del pendulo fisico (caja con dimensiones e inercia
          rotacional) en lugar de masa puntual.
    - [x] Modelar impacto no central (con brazo de palanca) usando conservacion
          del momento angular respecto al pivote.
    - [x] Reportar el coeficiente de restitucion para choques parcialmente
          elasticos (e entre 0 y 1).
    - [ ] Conectar el metodo exacto (omega1) con oscilacion.py y con el
          selector de metodo de la interfaz (pendiente en esos modulos).
"""


def velocidad_tras_impacto(m, M, v0):
    """
    Velocidad comun del conjunto (proyectil + caja) inmediatamente despues del
    impacto inelastico, por conservacion del momentum lineal.

    Parametros:
        m  : masa del proyectil (kg), debe ser > 0.
        M  : masa de la caja del pendulo (kg), debe ser >= 0.
        v0 : velocidad inicial del proyectil (m/s).

    Retorna:
        v1 : velocidad comun tras el impacto (m/s).
    """
    if m <= 0:
        raise ValueError("La masa del proyectil m debe ser mayor que cero.")
    if M < 0:
        raise ValueError("La masa de la caja M no puede ser negativa.")
    return m * v0 / (m + M)


def momentum(masa, velocidad):
    """
    Momentum lineal p = masa * velocidad.

    Parametros:
        masa      : masa del cuerpo (kg).
        velocidad : velocidad del cuerpo (m/s).

    Retorna:
        p : momentum lineal (kg*m/s).
    """
    return masa * velocidad


def energia_cinetica(masa, velocidad):
    """
    Energia cinetica Ek = 0.5 * masa * velocidad^2.

    Parametros:
        masa      : masa del cuerpo (kg).
        velocidad : velocidad del cuerpo (m/s).

    Retorna:
        Ek : energia cinetica (J).
    """
    return 0.5 * masa * velocidad ** 2


def energia_perdida(m, M, v0):
    """
    Energia cinetica disipada durante el choque inelastico (J).

    Es la diferencia entre la energia cinetica del proyectil antes del impacto y
    la energia cinetica del conjunto despues del impacto.

    Parametros:
        m  : masa del proyectil (kg).
        M  : masa de la caja (kg).
        v0 : velocidad inicial del proyectil (m/s).

    Retorna:
        delta_E : energia perdida en el choque (J), valor >= 0.
    """
    v1 = velocidad_tras_impacto(m, M, v0)
    ek_antes = energia_cinetica(m, v0)
    ek_despues = energia_cinetica(m + M, v1)
    return ek_antes - ek_despues


def momento_angular(I, omega):
    """
    Momento angular L = I * omega.

    Parametros:
        I     : momento de inercia respecto al eje de giro (kg*m^2).
        omega : velocidad angular (rad/s).

    Retorna:
        L : momento angular (kg*m^2/s).
    """
    return I * omega


def energia_cinetica_rotacional(I, omega):
    """
    Energia cinetica rotacional Ek = 0.5 * I * omega^2.

    Parametros:
        I     : momento de inercia respecto al eje de giro (kg*m^2).
        omega : velocidad angular (rad/s).

    Retorna:
        Ek : energia cinetica rotacional (J).
    """
    return 0.5 * I * omega ** 2


def velocidad_angular_tras_impacto_exacto(m, M, v0, L, I_caja_cm=0.0, b=None):
    """
    Metodo exacto: velocidad angular del conjunto (caja + proyectil
    incrustado) inmediatamente despues del impacto, tratando la caja como un
    pendulo fisico (con inercia rotacional propia) y permitiendo un impacto
    no central. Se aplica conservacion del momento angular respecto al pivote
    (no se conserva el momentum lineal por si solo porque el pivote ejerce
    una fuerza impulsiva sobre la cuerda/eje).

        I_total = (I_caja_cm + M * L^2) + m * b^2
        omega1  = m * v0 * b / I_total

    Parametros:
        m         : masa del proyectil (kg), debe ser > 0.
        M         : masa de la caja del pendulo (kg), debe ser >= 0.
        v0        : velocidad inicial del proyectil (m/s).
        L         : distancia del pivote al centro de masa de la caja (m),
                    debe ser > 0.
        I_caja_cm : momento de inercia de la caja respecto a su propio centro
                    de masa (kg*m^2), debe ser >= 0. Por defecto 0 (caja
                    tratada como masa puntual, igual que el baseline).
        b         : brazo de palanca del impacto: distancia perpendicular del
                    pivote a la linea de accion de v0 (m), debe ser > 0. Por
                    defecto None, que equivale a b = L (impacto central, en
                    el centro de masa de la caja).

    Retorna:
        omega1 : velocidad angular comun tras el impacto (rad/s).
    """
    if m <= 0:
        raise ValueError("La masa del proyectil m debe ser mayor que cero.")
    if M < 0:
        raise ValueError("La masa de la caja M no puede ser negativa.")
    if L <= 0:
        raise ValueError("La distancia L debe ser mayor que cero.")
    if I_caja_cm < 0:
        raise ValueError("El momento de inercia I_caja_cm no puede ser negativo.")
    if b is None:
        b = L
    if b <= 0:
        raise ValueError("El brazo de palanca b debe ser mayor que cero.")

    i_caja_pivote = I_caja_cm + M * L ** 2
    i_total = i_caja_pivote + m * b ** 2
    return m * v0 * b / i_total


def velocidades_con_restitucion(m, M, v0, e=0.0):
    """
    Velocidades del proyectil y de la caja inmediatamente despues de un
    choque 1D con coeficiente de restitucion e, con la caja inicialmente en
    reposo. Generaliza el baseline (choque perfectamente inelastico, e = 0,
    donde el proyectil queda incrustado y ambas velocidades coinciden con
    velocidad_tras_impacto) a choques parcialmente o totalmente elasticos.

        v_proyectil = v0 * (m - e * M) / (m + M)
        v_caja      = v0 * m * (1 + e) / (m + M)

    Parametros:
        m  : masa del proyectil (kg), debe ser > 0.
        M  : masa de la caja del pendulo (kg), debe ser >= 0.
        v0 : velocidad inicial del proyectil (m/s).
        e  : coeficiente de restitucion, 0 <= e <= 1. Por defecto 0.0
             (perfectamente inelastico, igual al baseline).

    Retorna:
        (v_proyectil, v_caja) : velocidades tras el choque (m/s).
    """
    if m <= 0:
        raise ValueError("La masa del proyectil m debe ser mayor que cero.")
    if M < 0:
        raise ValueError("La masa de la caja M no puede ser negativa.")
    if not (0.0 <= e <= 1.0):
        raise ValueError("El coeficiente de restitucion e debe estar entre 0 y 1.")

    v_proyectil = v0 * (m - e * M) / (m + M)
    v_caja = v0 * m * (1.0 + e) / (m + M)
    return v_proyectil, v_caja


def resumen_colision_exacto(m, M, v0, L, I_caja_cm=0.0, b=None):
    """
    Version del resumen de la colision para el metodo exacto (inercia
    rotacional, impacto no central). Analoga a resumen_colision, pero en
    terminos angulares respecto al pivote.

    Retorna un dict con: omega1, v1_equivalente (omega1 * L, para comparar
    contra el baseline), momento_angular_antes, momento_angular_despues,
    ek_antes, ek_despues, energia_perdida y fraccion_perdida.
    """
    if b is None:
        b = L
    omega1 = velocidad_angular_tras_impacto_exacto(m, M, v0, L, I_caja_cm, b)
    i_total = (I_caja_cm + M * L ** 2) + m * b ** 2

    momento_angular_antes = m * v0 * b
    momento_angular_despues = momento_angular(i_total, omega1)
    ek_antes = energia_cinetica(m, v0)
    ek_despues = energia_cinetica_rotacional(i_total, omega1)
    perdida = ek_antes - ek_despues
    fraccion = (perdida / ek_antes) if ek_antes != 0 else 0.0

    return {
        "omega1": omega1,
        "v1_equivalente": omega1 * L,
        "momento_angular_antes": momento_angular_antes,
        "momento_angular_despues": momento_angular_despues,
        "ek_antes": ek_antes,
        "ek_despues": ek_despues,
        "energia_perdida": perdida,
        "fraccion_perdida": fraccion,
    }


def resumen_colision(m, M, v0):
    """
    Devuelve un diccionario con las magnitudes principales de la colision.
    Util para depuracion y para alimentar la interfaz.

    Retorna un dict con: v1, p_antes, p_despues, ek_antes, ek_despues,
    energia_perdida y fraccion_perdida.
    """
    v1 = velocidad_tras_impacto(m, M, v0)
    p_antes = momentum(m, v0)
    p_despues = momentum(m + M, v1)
    ek_antes = energia_cinetica(m, v0)
    ek_despues = energia_cinetica(m + M, v1)
    perdida = ek_antes - ek_despues
    fraccion = (perdida / ek_antes) if ek_antes != 0 else 0.0
    return {
        "v1": v1,
        "p_antes": p_antes,
        "p_despues": p_despues,
        "ek_antes": ek_antes,
        "ek_despues": ek_despues,
        "energia_perdida": perdida,
        "fraccion_perdida": fraccion,
    }


def _demostracion():
    """Pequena demo que se ejecuta con `python -m src.colision`."""
    m, M, v0 = 0.05, 2.0, 300.0
    print("Demostracion del modulo colision.py (responsable: Cristopher Arauz)")
    print("Parametros: m = {} kg, M = {} kg, v0 = {} m/s".format(m, M, v0))
    datos = resumen_colision(m, M, v0)
    print("Velocidad tras impacto v1 = {:.4f} m/s".format(datos["v1"]))
    print("Momentum antes  = {:.4f} kg*m/s".format(datos["p_antes"]))
    print("Momentum despues = {:.4f} kg*m/s".format(datos["p_despues"]))
    print("Energia cinetica antes  = {:.4f} J".format(datos["ek_antes"]))
    print("Energia cinetica despues = {:.4f} J".format(datos["ek_despues"]))
    print("Energia perdida = {:.4f} J ({:.2f}%)".format(
        datos["energia_perdida"], 100.0 * datos["fraccion_perdida"]))
    # Verificacion: el momentum lineal debe conservarse.
    assert abs(datos["p_antes"] - datos["p_despues"]) < 1e-9, \
        "El momentum no se conserva: revisar el modelo."
    print("Verificacion de conservacion del momentum: OK")

    print()
    print("Metodo exacto (inercia rotacional, impacto no central):")
    L = 0.5
    exacto = resumen_colision_exacto(m, M, v0, L)
    print("omega1 = {:.4f} rad/s | v1_equivalente = {:.4f} m/s".format(
        exacto["omega1"], exacto["v1_equivalente"]))
    # Con I_caja_cm = 0 y b = L (impacto central), el metodo exacto debe
    # coincidir con el baseline de masa puntual.
    assert abs(exacto["v1_equivalente"] - datos["v1"]) < 1e-9, \
        "El metodo exacto (caso limite) deberia coincidir con el baseline."
    print("Verificacion metodo exacto == baseline (caso limite): OK")

    print()
    print("Choque con coeficiente de restitucion (e = 0.3):")
    v_proy, v_caja = velocidades_con_restitucion(m, M, v0, e=0.3)
    print("v_proyectil = {:.4f} m/s | v_caja = {:.4f} m/s".format(v_proy, v_caja))
    # Con e = 0, ambas velocidades deben coincidir con el baseline.
    v_proy_e0, v_caja_e0 = velocidades_con_restitucion(m, M, v0, e=0.0)
    assert abs(v_proy_e0 - v_caja_e0) < 1e-9, \
        "Con e = 0 el proyectil y la caja deben moverse juntos."
    assert abs(v_caja_e0 - datos["v1"]) < 1e-9, \
        "Con e = 0 la velocidad conjunta debe coincidir con el baseline."
    print("Verificacion restitucion (e = 0) == baseline: OK")


if __name__ == "__main__":
    _demostracion()
