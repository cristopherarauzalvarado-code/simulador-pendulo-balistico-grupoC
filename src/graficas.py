# -*- coding: utf-8 -*-
"""
Modulo: graficas.py
Responsable: Maciel Gomez

Que modela:
    El panel de visualizacion con las 4 graficas en tiempo real del simulador,
    incrustado en la ventana de Tkinter mediante FigureCanvasTkAgg. Las 4
    subgraficas son:

        1. theta(t)  -> angulo respecto a la vertical (rad)
        2. omega(t)  -> velocidad angular (rad/s)
        3. p(t)      -> momentum lineal del conjunto (kg*m/s)
        4. Ek(t)     -> energia cinetica del conjunto (J)

    El metodo agregar_punto(t, theta, omega, p, ek) recibe un punto por cuadro de
    animacion y redibuja las curvas (las graficas crecen con la simulacion).

Estado:
    PENDIENTE - esqueleto inicial. La implementacion corre por cuenta de la
    responsable. No modificar la firma publica (contrato entre modulos).

Contrato (no cambiar la firma):
    PanelGraficas(contenedor)
    PanelGraficas.agregar_punto(t, theta, omega, p, ek)

TODO (baseline):
    - [ ] Crear la Figure con 4 subgraficas (2x2), ejes etiquetados y unidades.
    - [ ] Incrustar la figura en Tkinter con FigureCanvasTkAgg.
    - [ ] Implementar agregar_punto: acumular datos y redibujar por cuadro.
    - [ ] Exponer self.widget para que la interfaz lo empaquete.
TODO (Informe Final):
    - [ ] Graficas 5-9: Ep(t), energia total E(t), retrato de fase, alpha(t), y(t).
    - [ ] Exportar las graficas a PNG para el informe.
    - [ ] Comparar dos simulaciones superpuestas (con/sin friccion).
"""


class PanelGraficas:
    """
    Panel con 4 subgraficas en tiempo real incrustado en un contenedor Tkinter.

    PENDIENTE: implementacion a cargo de Maciel Gomez.
    """

    def __init__(self, contenedor):
        """
        Construye el panel y lo incrusta en el contenedor de Tkinter dado.

        Parametros:
            contenedor : widget de Tkinter (por ejemplo un Frame) donde se
                         dibujara el canvas de Matplotlib.

        Debe dejar disponible self.widget (el get_tk_widget del canvas) para que
        la interfaz pueda empaquetarlo.
        """
        raise NotImplementedError(
            "PanelGraficas pendiente de implementar (responsable: Maciel Gomez).")

    def agregar_punto(self, t, theta, omega, p, ek):
        """
        Agrega un punto a las 4 graficas y solicita un redibujado.

        Parametros:
            t     : instante de tiempo (s).
            theta : angulo (rad).
            omega : velocidad angular (rad/s).
            p     : momentum lineal (kg*m/s).
            ek    : energia cinetica (J).

        PENDIENTE: implementacion a cargo de Maciel Gomez.
        """
        raise NotImplementedError(
            "agregar_punto pendiente de implementar (responsable: Maciel Gomez).")
