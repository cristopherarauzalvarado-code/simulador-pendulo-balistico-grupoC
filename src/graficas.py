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
    Baseline implementado. Metodo aproximado: 4 subgraficas (2x2) que crecen
    cuadro a cuadro. Sin blitting (redibujado completo por cuadro).

Contrato (no cambiar la firma):
    PanelGraficas(contenedor)
    PanelGraficas.agregar_punto(t, theta, omega, p, ek)

TODO (baseline):
    - [x] Crear la Figure con 4 subgraficas (2x2), ejes etiquetados y unidades.
    - [x] Incrustar la figura en Tkinter con FigureCanvasTkAgg.
    - [x] Implementar agregar_punto: acumular datos y redibujar por cuadro.
    - [x] Exponer self.widget para que la interfaz lo empaquete.
TODO (Informe Final):
    - [ ] Graficas 5-9: Ep(t), energia total E(t), retrato de fase, alpha(t), y(t).
    - [ ] Exportar las graficas a PNG para el informe.
    - [ ] Comparar dos simulaciones superpuestas (con/sin friccion).
    - [ ] Optimizar el redibujado con blitting.
"""

import matplotlib

# Backend de Matplotlib para incrustar figuras en Tkinter. Debe fijarse antes de
# importar pyplot / FigureCanvasTkAgg.
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PanelGraficas:
    """
    Panel con 4 subgraficas en tiempo real incrustado en un contenedor Tkinter.

    Acumula los puntos recibidos por agregar_punto y redibuja las cuatro curvas
    (theta, omega, p y Ek en funcion del tiempo). Expone self.widget con el
    widget de Tkinter del canvas para que la interfaz lo pueda empaquetar.
    """

    def __init__(self, contenedor):
        """
        Construye el panel y lo incrusta en el contenedor de Tkinter dado.

        Parametros:
            contenedor : widget de Tkinter (por ejemplo un Frame) donde se
                         dibujara el canvas de Matplotlib.

        Deja disponible self.widget (el get_tk_widget del canvas) para que la
        interfaz pueda empaquetarlo.
        """
        # Acumuladores de datos: crecen un elemento por cada agregar_punto.
        self._t = []
        self._theta = []
        self._omega = []
        self._p = []
        self._ek = []

        # Figura con las 4 subgraficas dispuestas en una cuadricula 2x2.
        self._figura = Figure(figsize=(7, 5), dpi=100)
        self._figura.suptitle("Pendulo balistico - magnitudes en el tiempo")

        self._ax_theta = self._figura.add_subplot(2, 2, 1)
        self._ax_omega = self._figura.add_subplot(2, 2, 2)
        self._ax_p = self._figura.add_subplot(2, 2, 3)
        self._ax_ek = self._figura.add_subplot(2, 2, 4)

        # Configuracion de cada subgrafica: titulo, etiquetas y unidades.
        self._configurar_eje(
            self._ax_theta, "Angulo theta(t)", "Tiempo (s)", "theta (rad)")
        self._configurar_eje(
            self._ax_omega, "Velocidad angular omega(t)", "Tiempo (s)",
            "omega (rad/s)")
        self._configurar_eje(
            self._ax_p, "Momentum lineal p(t)", "Tiempo (s)", "p (kg*m/s)")
        self._configurar_eje(
            self._ax_ek, "Energia cinetica Ek(t)", "Tiempo (s)", "Ek (J)")

        # Una linea (curva) por subgrafica. Se actualizan sus datos en cada
        # cuadro sin recrear los ejes.
        (self._linea_theta,) = self._ax_theta.plot([], [], color="tab:blue")
        (self._linea_omega,) = self._ax_omega.plot([], [], color="tab:orange")
        (self._linea_p,) = self._ax_p.plot([], [], color="tab:green")
        (self._linea_ek,) = self._ax_ek.plot([], [], color="tab:red")

        # Ajusta los margenes para que no se solapen titulos y etiquetas.
        self._figura.tight_layout(rect=(0, 0, 1, 0.96))

        # Incrustacion de la figura en el contenedor de Tkinter.
        self._canvas = FigureCanvasTkAgg(self._figura, master=contenedor)
        self._canvas.draw()

        # Widget de Tkinter que la interfaz empaqueta (pack/grid).
        self.widget = self._canvas.get_tk_widget()

    @staticmethod
    def _configurar_eje(eje, titulo, etiqueta_x, etiqueta_y):
        """Aplica titulo, etiquetas y rejilla a una subgrafica."""
        eje.set_title(titulo, fontsize=9)
        eje.set_xlabel(etiqueta_x, fontsize=8)
        eje.set_ylabel(etiqueta_y, fontsize=8)
        eje.grid(True, linestyle=":", alpha=0.6)

    def agregar_punto(self, t, theta, omega, p, ek):
        """
        Agrega un punto a las 4 graficas y solicita un redibujado.

        Parametros:
            t     : instante de tiempo (s).
            theta : angulo (rad).
            omega : velocidad angular (rad/s).
            p     : momentum lineal (kg*m/s).
            ek    : energia cinetica (J).
        """
        # Acumular el nuevo punto en cada serie.
        self._t.append(t)
        self._theta.append(theta)
        self._omega.append(omega)
        self._p.append(p)
        self._ek.append(ek)

        # Actualizar los datos de cada curva (x = tiempo, y = magnitud).
        self._linea_theta.set_data(self._t, self._theta)
        self._linea_omega.set_data(self._t, self._omega)
        self._linea_p.set_data(self._t, self._p)
        self._linea_ek.set_data(self._t, self._ek)

        # Reajustar los limites de cada subgrafica al rango actual de datos.
        for eje in (self._ax_theta, self._ax_omega, self._ax_p, self._ax_ek):
            eje.relim()
            eje.autoscale_view()

        # Redibujado no bloqueante: se programa el repintado sin forzarlo.
        self._canvas.draw_idle()

    def reiniciar(self):
        """
        Limpia todas las series y las curvas para comenzar una nueva simulacion.

        Util para la interfaz cuando se ejecuta mas de una simulacion sin cerrar
        la ventana (soporte para el boton "reiniciar" del Informe Final).
        """
        self._t.clear()
        self._theta.clear()
        self._omega.clear()
        self._p.clear()
        self._ek.clear()

        for linea in (self._linea_theta, self._linea_omega,
                      self._linea_p, self._linea_ek):
            linea.set_data([], [])

        for eje in (self._ax_theta, self._ax_omega, self._ax_p, self._ax_ek):
            eje.relim()
            eje.autoscale_view()

        self._canvas.draw_idle()


def _demostracion():
    """
    Demo que se ejecuta con `python -m src.graficas`.

    Abre una ventana Tkinter con el panel de graficas y reproduce, cuadro a
    cuadro con after(), una oscilacion real calculada por el modulo oscilacion
    a partir de la velocidad tras el impacto del modulo colision. Sirve para
    verificar el panel sin depender de la interfaz completa.
    """
    import tkinter as tk

    from src.colision import velocidad_tras_impacto
    from src.oscilacion import simular_oscilacion

    print("Demostracion del modulo graficas.py (responsable: Maciel Gomez)")

    # Parametros de ejemplo: proyectil ligero contra una caja de 2 kg.
    m, M, v0, L = 0.05, 2.0, 300.0, 2.0
    t_max, dt = 4.0, 0.02

    v1 = velocidad_tras_impacto(m, M, v0)
    datos = simular_oscilacion(m, M, L, v1, t_max, dt)
    print("Velocidad tras impacto v1 = {:.4f} m/s".format(v1))
    print("Cuadros a animar          = {}".format(len(datos["t"])))

    ventana = tk.Tk()
    ventana.title("Demo PanelGraficas - Pendulo Balistico")

    panel = PanelGraficas(ventana)
    panel.widget.pack(fill="both", expand=True)

    # Estado mutable para el indice del cuadro actual dentro del callback.
    indice = {"i": 0}

    def _siguiente_cuadro():
        i = indice["i"]
        if i >= len(datos["t"]):
            print("Animacion completada.")
            return
        panel.agregar_punto(
            datos["t"][i], datos["theta"][i], datos["omega"][i],
            datos["p"][i], datos["ek"][i])
        indice["i"] = i + 1
        # Reprograma el siguiente cuadro (~20 ms => ~50 cuadros por segundo).
        ventana.after(20, _siguiente_cuadro)

    ventana.after(0, _siguiente_cuadro)
    ventana.mainloop()


if __name__ == "__main__":
    _demostracion()
