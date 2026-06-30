# -*- coding: utf-8 -*-
"""
Modulo: main.py
Proyecto: pendulo-balistico-sim (Fisica I - CENFOTEC - Grupo C)

Que hace:
    Punto de entrada de la aplicacion. La funcion iniciar() arranca la interfaz
    grafica del simulador. Es invocado por run.py (que ademas se encarga de
    instalar las dependencias si faltan).

Estado:
    Baseline funcional.

TODO (Informe Final):
    - [ ] Soportar argumentos de linea de comandos (por ejemplo, ejecutar una
          simulacion sin GUI y exportar las graficas a PNG para el informe).
"""


def iniciar():
    """Arranca la interfaz grafica del simulador del pendulo balistico."""
    # La importacion se hace dentro de la funcion para que run.py pueda instalar
    # las dependencias antes de que se carguen numpy/scipy/matplotlib.
    from src.interfaz import lanzar
    lanzar()


if __name__ == "__main__":
    iniciar()
