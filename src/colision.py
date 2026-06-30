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

Estado:
    Baseline funcional. Metodo aproximado (masa puntual, choque 1D horizontal).

Contrato (no cambiar la firma):
    velocidad_tras_impacto(m, M, v0) -> v1

TODO (Informe Final):
    - [ ] Considerar el caso del pendulo fisico (caja con dimensiones e inercia
          rotacional) en lugar de masa puntual.
    - [ ] Modelar impacto no central (con brazo de palanca) usando conservacion
          del momento angular respecto al pivote.
    - [ ] Reportar el coeficiente de restitucion para choques parcialmente
          elasticos (e entre 0 y 1).
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


if __name__ == "__main__":
    _demostracion()
