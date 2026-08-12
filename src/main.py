# -*- coding: utf-8 -*-
"""
Modulo: main.py
Proyecto: pendulo-balistico-sim (Fisica I - CENFOTEC - Grupo C)

Que hace:
    Punto de entrada de la aplicacion. La funcion iniciar() decide, segun los
    argumentos de linea de comandos, si:

    - No hay argumentos (o se pide explicitamente): arranca la interfaz
      grafica del simulador (comportamiento original, invocado por run.py).
    - Se pasa --sin-gui: corre una unica simulacion de punta a punta
      (colision -> oscilacion) con los parametros indicados y exporta las
      graficas 1-8 a PNG, sin abrir ninguna ventana. Util para generar las
      figuras del Informe Final desde un script o en un entorno sin pantalla.

Estado:
    Baseline funcional (GUI) mas modo de linea de comandos para el Informe
    Final.

Contrato (no cambiar la firma):
    iniciar()

TODO (Informe Final):
    - [x] Soportar argumentos de linea de comandos (ejecutar una simulacion
          sin GUI y exportar las graficas a PNG para el informe).
"""

import argparse
import sys


def _construir_parser():
    """Arma el parser de argumentos del modo de linea de comandos."""
    parser = argparse.ArgumentParser(
        prog="pendulo-balistico-sim",
        description=(
            "Simulador de pendulo balistico. Sin argumentos abre la interfaz "
            "grafica; con --sin-gui corre una simulacion y exporta las "
            "graficas a PNG sin abrir ninguna ventana."))

    parser.add_argument(
        "--sin-gui", action="store_true",
        help="ejecuta la simulacion sin interfaz grafica y exporta PNG.")

    grupo_fisico = parser.add_argument_group("parametros fisicos")
    grupo_fisico.add_argument("--m", type=float, default=0.05, help="masa del proyectil (kg).")
    grupo_fisico.add_argument("--M", type=float, default=2.0, help="masa de la caja (kg).")
    grupo_fisico.add_argument("--v0", type=float, default=300.0, help="velocidad inicial del proyectil (m/s).")
    grupo_fisico.add_argument("--L", type=float, default=2.0, help="longitud de la cuerda (m).")
    grupo_fisico.add_argument(
        "--metodo", choices=("aproximado", "exacto"), default="aproximado",
        help="metodo de calculo: masa puntual o pendulo fisico con inercia.")
    grupo_fisico.add_argument(
        "--I-caja-cm", dest="I_caja_cm", type=float, default=0.0,
        help="momento de inercia de la caja respecto a su CM (kg*m^2, solo metodo exacto).")
    grupo_fisico.add_argument(
        "--b", type=float, default=None,
        help="brazo de palanca del impacto (m, solo metodo exacto; por defecto L).")
    grupo_fisico.add_argument(
        "--amortiguamiento", action="store_true",
        help="activa el amortiguamiento viscoso.")
    grupo_fisico.add_argument(
        "--coef-amortiguamiento", dest="coef_amortiguamiento", type=float, default=0.0,
        help="coeficiente de amortiguamiento viscoso (1/s).")

    grupo_temporal = parser.add_argument_group("parametros temporales")
    grupo_temporal.add_argument("--t-max", dest="t_max", type=float, default=6.0, help="duracion de la simulacion (s).")
    grupo_temporal.add_argument("--dt", type=float, default=0.02, help="paso de muestreo (s).")

    grupo_salida = parser.add_argument_group("salida")
    grupo_salida.add_argument(
        "--salida", default="reportes",
        help="carpeta donde se guardan las graficas PNG (se crea si no existe).")
    grupo_salida.add_argument(
        "--prefijo", default="pendulo",
        help="prefijo de los nombres de archivo de las graficas PNG.")

    return parser


def _ejecutar_sin_gui(args):
    """Corre la simulacion completa con los parametros dados y exporta PNG."""
    # Importaciones diferidas: run.py instala las dependencias antes de que
    # se carguen numpy/scipy/matplotlib.
    from src.colision import (energia_perdida, resumen_colision_exacto,
                               velocidad_tras_impacto)
    from src.oscilacion import simular_oscilacion
    from src.graficas import generar_figuras_estaticas

    if args.metodo == "exacto":
        resumen = resumen_colision_exacto(
            args.m, args.M, args.v0, args.L, I_caja_cm=args.I_caja_cm, b=args.b)
        v1 = resumen["v1_equivalente"]
        energia_disipada = resumen["energia_perdida"]
    else:
        v1 = velocidad_tras_impacto(args.m, args.M, args.v0)
        energia_disipada = energia_perdida(args.m, args.M, args.v0)

    datos = simular_oscilacion(
        args.m, args.M, args.L, v1, args.t_max, args.dt, metodo=args.metodo,
        I_caja_cm=args.I_caja_cm, b=args.b, amortiguamiento=args.amortiguamiento,
        coef_amortiguamiento=args.coef_amortiguamiento)

    print("Simulacion sin GUI - Pendulo Balistico (Grupo C)")
    print("Parametros: m={} kg, M={} kg, v0={} m/s, L={} m, metodo={}".format(
        args.m, args.M, args.v0, args.L, args.metodo))
    print("Velocidad tras el impacto v1 = {:.4f} m/s".format(v1))
    print("Energia perdida en el choque = {:.4f} J".format(energia_disipada))
    print("Amplitud maxima = {:.4f} rad".format(datos["theta_max"]))
    print("Periodo aproximado = {:.4f} s | Periodo exacto = {:.4f} s".format(
        datos["periodo_aproximado"], datos["periodo_exacto"]))

    rutas = generar_figuras_estaticas(datos, carpeta=args.salida, prefijo=args.prefijo)
    print("Graficas exportadas:")
    for ruta in rutas:
        print("  - {}".format(ruta))


def iniciar():
    """
    Punto de entrada: arranca la GUI, o corre en modo sin GUI segun los
    argumentos de linea de comandos (sys.argv).
    """
    parser = _construir_parser()
    args = parser.parse_args(sys.argv[1:])

    if args.sin_gui:
        _ejecutar_sin_gui(args)
        return

    # La importacion se hace dentro de la funcion para que run.py pueda instalar
    # las dependencias antes de que se carguen numpy/scipy/matplotlib.
    from src.interfaz import lanzar
    lanzar()


if __name__ == "__main__":
    iniciar()
