# -*- coding: utf-8 -*-
"""
Modulo: interfaz.py
Responsable: Tatiana Solis

Que modela:
    La interfaz grafica (GUI) del simulador construida con Tkinter. Reune todos
    los modulos del proyecto:

        - Campos de entrada para los parametros: m, M, v0, L.
        - Boton "Iniciar simulacion".
        - Un Canvas que anima el pendulo (la cuerda y la caja) cuadro a cuadro.
        - El PanelGraficas (modulo graficas) con las 4 graficas en tiempo real.

    Flujo de datos que debe conectar los modulos:
        colision.velocidad_tras_impacto(m, M, v0) -> v1
        oscilacion.simular_oscilacion(m, M, L, v1, t_max, dt) -> datos
        graficas.PanelGraficas.agregar_punto(...) por cada cuadro

    La animacion se sugiere con el metodo after() de Tkinter (no bloqueante).

Estado:
    PENDIENTE - esqueleto inicial. La implementacion corre por cuenta de la
    responsable. No modificar la firma publica (contrato entre modulos).

Contrato (no cambiar las firmas):
    App(tk.Tk)
    lanzar()

TODO (baseline):
    - [ ] Construir los campos de entrada (m, M, v0, L) y el boton de inicio.
    - [ ] Crear el Canvas de animacion del pendulo.
    - [ ] Incrustar el PanelGraficas y conectar colision -> oscilacion -> panel.
    - [ ] Animar con after() llamando a agregar_punto por cuadro.
TODO (Informe Final):
    - [ ] Controles para pausar, reanudar y reiniciar la animacion.
    - [ ] Selector de metodo: aproximado vs exacto (con inercia).
    - [ ] Casilla para activar/desactivar el amortiguamiento.
    - [ ] Panel numerico con v1, energia perdida y periodo estimado.
"""

import tkinter as tk


class App(tk.Tk):
    """
    Ventana principal del simulador del pendulo balistico.

    PENDIENTE: implementacion a cargo de Tatiana Solis.
    """

    def __init__(self):
        super().__init__()
        self.title("Simulador de Pendulo Balistico - Fisica I - Grupo C")
        raise NotImplementedError(
            "App pendiente de implementar (responsable: Tatiana Solis).")


def lanzar():
    """
    Crea la aplicacion y arranca el bucle principal de Tkinter.

    PENDIENTE: implementacion a cargo de Tatiana Solis.
    """
    raise NotImplementedError(
        "lanzar pendiente de implementar (responsable: Tatiana Solis).")
