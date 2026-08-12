# -*- coding: utf-8 -*-
"""
Modulo: graficas.py
Responsable: Maciel Gomez

Que modela:
    El panel de visualizacion del simulador, incrustado en la ventana de
    Tkinter mediante FigureCanvasTkAgg. Esta organizado en pestanas
    (ttk.Notebook) para no saturar una sola ventana con las 9 graficas del
    Informe Final:

        Pestana "Cinematica basica" (tiempo real, 4 subgraficas 2x2):
            1. theta(t)  -> angulo respecto a la vertical (rad)
            2. omega(t)  -> velocidad angular (rad/s)
            3. p(t)      -> momentum lineal del conjunto (kg*m/s)
            4. Ek(t)     -> energia cinetica del conjunto (J)

        Pestana "Energia y dinamica" (tiempo real, 4 subgraficas 2x2):
            5. x(t), y(t) -> posicion del centro de masa
            6. v(t)       -> rapidez tangencial
            7. Ek/Ep/Emec -> energias en conjunto
            8. T(t)       -> tension de la cuerda

        Pestana "Comparacion de metodos" (estatica, bajo demanda):
            9. v1 (aproximado vs exacto) en funcion de la posicion relativa
               del impacto b/L.

        Pestana "Comparar simulaciones" (estatica, bajo demanda): superpone
        dos corridas completas (por ejemplo, con y sin amortiguamiento).

    El metodo agregar_punto(t, theta, omega, p, ek, ...) recibe un punto por
    cuadro de animacion y redibuja las curvas de las dos primeras pestanas
    (las graficas crecen con la simulacion). Los argumentos adicionales
    (x, y, ep, emec, tension) son opcionales para no romper el contrato.

Estado:
    Pestana basica (4 graficas 2x2) con blitting para el redibujado en tiempo
    real. Pestana de energia y dinamica (graficas 5-8). Comparacion de
    metodos (grafica 9) y comparacion de simulaciones superpuestas, ambas
    bajo demanda. Exportacion de cualquiera de las figuras a PNG.

Contrato (no cambiar la firma):
    PanelGraficas(contenedor)
    PanelGraficas.agregar_punto(t, theta, omega, p, ek)

    self.widget sigue siendo el widget de Tkinter que la interfaz empaqueta
    (antes era el canvas de una unica figura; ahora es el Notebook que
    contiene todas las pestanas, pero se usa exactamente igual: widget.pack(...)).

TODO (baseline):
    - [x] Crear la Figure con 4 subgraficas (2x2), ejes etiquetados y unidades.
    - [x] Incrustar la figura en Tkinter con FigureCanvasTkAgg.
    - [x] Implementar agregar_punto: acumular datos y redibujar por cuadro.
    - [x] Exponer self.widget para que la interfaz lo empaquete.
TODO (Informe Final):
    - [x] Graficas 5-9: x(t)/y(t), v(t), Ek/Ep/Emec, T(t), comparacion de
          metodos.
    - [x] Exportar las graficas a PNG para el informe.
    - [x] Comparar dos simulaciones superpuestas (por ejemplo, con/sin
          amortiguamiento).
    - [x] Optimizar el redibujado con blitting.
"""

import os

import matplotlib

# Backend de Matplotlib para incrustar figuras en Tkinter. Debe fijarse antes de
# importar pyplot / FigureCanvasTkAgg.
matplotlib.use("TkAgg")

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk


class PanelGraficas:
    """
    Panel con las graficas del simulador, organizado en pestanas e incrustado
    en un contenedor Tkinter.

    Acumula los puntos recibidos por agregar_punto y redibuja las curvas de
    las pestanas en tiempo real. Expone self.widget (el Notebook) para que la
    interfaz lo pueda empaquetar, y metodos adicionales bajo demanda para las
    graficas estaticas (comparacion de metodos, comparacion de simulaciones,
    exportacion a PNG).
    """

    def __init__(self, contenedor):
        """
        Construye el panel (un ttk.Notebook con varias pestanas) y lo
        incrusta en el contenedor de Tkinter dado.

        Parametros:
            contenedor : widget de Tkinter (por ejemplo un Frame) donde se
                         dibujara el Notebook con las graficas.

        Deja disponible self.widget (el Notebook) para que la interfaz lo
        pueda empaquetar.
        """
        # Acumuladores de datos: crecen un elemento por cada agregar_punto.
        self._t = []
        self._theta = []
        self._omega = []
        self._p = []
        self._ek = []
        self._x = []
        self._y = []
        self._v = []
        self._ep = []
        self._emec = []
        self._tension = []

        self._notebook = ttk.Notebook(contenedor)
        self.widget = self._notebook

        self._pestana_basica = ttk.Frame(self._notebook)
        self._pestana_energia = ttk.Frame(self._notebook)
        self._pestana_comparacion = ttk.Frame(self._notebook)
        self._pestana_simulaciones = ttk.Frame(self._notebook)

        self._notebook.add(self._pestana_basica, text="Cinematica basica")
        self._notebook.add(self._pestana_energia, text="Energia y dinamica")
        self._notebook.add(self._pestana_comparacion, text="Comparacion de metodos")
        self._notebook.add(self._pestana_simulaciones, text="Comparar simulaciones")

        self._construir_pestana_basica()
        self._construir_pestana_energia()
        self._construir_pestana_comparacion()
        self._construir_pestana_simulaciones()

    # ------------------------------------------------------------------
    # Construccion de pestanas
    # ------------------------------------------------------------------
    @staticmethod
    def _configurar_eje(eje, titulo, etiqueta_x, etiqueta_y):
        """Aplica titulo, etiquetas y rejilla a una subgrafica."""
        eje.set_title(titulo, fontsize=9)
        eje.set_xlabel(etiqueta_x, fontsize=8)
        eje.set_ylabel(etiqueta_y, fontsize=8)
        eje.grid(True, linestyle=":", alpha=0.6)

    def _construir_pestana_basica(self):
        """Graficas 1-4: theta(t), omega(t), p(t), Ek(t) (tiempo real)."""
        self._figura_basica = Figure(figsize=(7, 5), dpi=100)
        self._figura_basica.suptitle("Pendulo balistico - magnitudes basicas")

        self._ax_theta = self._figura_basica.add_subplot(2, 2, 1)
        self._ax_omega = self._figura_basica.add_subplot(2, 2, 2)
        self._ax_p = self._figura_basica.add_subplot(2, 2, 3)
        self._ax_ek = self._figura_basica.add_subplot(2, 2, 4)

        self._configurar_eje(self._ax_theta, "Angulo theta(t)", "Tiempo (s)", "theta (rad)")
        self._configurar_eje(self._ax_omega, "Velocidad angular omega(t)", "Tiempo (s)", "omega (rad/s)")
        self._configurar_eje(self._ax_p, "Momentum lineal p(t)", "Tiempo (s)", "p (kg*m/s)")
        self._configurar_eje(self._ax_ek, "Energia cinetica Ek(t)", "Tiempo (s)", "Ek (J)")

        (self._linea_theta,) = self._ax_theta.plot([], [], color="tab:blue", animated=True)
        (self._linea_omega,) = self._ax_omega.plot([], [], color="tab:orange", animated=True)
        (self._linea_p,) = self._ax_p.plot([], [], color="tab:green", animated=True)
        (self._linea_ek,) = self._ax_ek.plot([], [], color="tab:red", animated=True)

        self._ejes_basica = (self._ax_theta, self._ax_omega, self._ax_p, self._ax_ek)
        self._lineas_basica = (self._linea_theta, self._linea_omega, self._linea_p, self._linea_ek)

        self._figura_basica.tight_layout(rect=(0, 0, 1, 0.96))

        self._canvas_basica = FigureCanvasTkAgg(self._figura_basica, master=self._pestana_basica)
        self._canvas_basica.draw()
        self._canvas_basica.get_tk_widget().pack(fill="both", expand=True)

        # Estado para el redibujado optimizado con blitting.
        self._fondo_basica = None
        self._limites_previos_basica = {}

    def _construir_pestana_energia(self):
        """Graficas 5-8: x(t)/y(t), v(t), Ek/Ep/Emec, T(t) (tiempo real)."""
        self._figura_energia = Figure(figsize=(7, 5), dpi=100)
        self._figura_energia.suptitle("Pendulo balistico - energia y cinematica")

        self._ax_posicion = self._figura_energia.add_subplot(2, 2, 1)
        self._ax_velocidad = self._figura_energia.add_subplot(2, 2, 2)
        self._ax_energias = self._figura_energia.add_subplot(2, 2, 3)
        self._ax_tension = self._figura_energia.add_subplot(2, 2, 4)

        self._configurar_eje(self._ax_posicion, "Posicion del centro de masa", "Tiempo (s)", "x, y (m)")
        self._configurar_eje(self._ax_velocidad, "Rapidez tangencial v(t)", "Tiempo (s)", "v (m/s)")
        self._configurar_eje(self._ax_energias, "Energias Ek, Ep, Emec", "Tiempo (s)", "Energia (J)")
        self._configurar_eje(self._ax_tension, "Tension de la cuerda T(t)", "Tiempo (s)", "T (N)")

        (self._linea_x,) = self._ax_posicion.plot([], [], color="tab:blue", label="x(t)", animated=True)
        (self._linea_y,) = self._ax_posicion.plot([], [], color="tab:cyan", label="y(t)", animated=True)
        self._ax_posicion.legend(fontsize=7, loc="upper right")

        (self._linea_v,) = self._ax_velocidad.plot([], [], color="tab:purple", animated=True)

        (self._linea_ek2,) = self._ax_energias.plot([], [], color="tab:red", label="Ek", animated=True)
        (self._linea_ep,) = self._ax_energias.plot([], [], color="tab:green", label="Ep", animated=True)
        (self._linea_emec,) = self._ax_energias.plot([], [], color="tab:gray", label="Emec", animated=True)
        self._ax_energias.legend(fontsize=7, loc="upper right")

        (self._linea_tension,) = self._ax_tension.plot([], [], color="tab:brown", animated=True)

        self._ejes_energia = (self._ax_posicion, self._ax_velocidad, self._ax_energias, self._ax_tension)
        self._lineas_energia = (
            self._linea_x, self._linea_y, self._linea_v,
            self._linea_ek2, self._linea_ep, self._linea_emec,
            self._linea_tension,
        )

        self._figura_energia.tight_layout(rect=(0, 0, 1, 0.96))

        self._canvas_energia = FigureCanvasTkAgg(self._figura_energia, master=self._pestana_energia)
        self._canvas_energia.draw()
        self._canvas_energia.get_tk_widget().pack(fill="both", expand=True)

        self._fondo_energia = None
        self._limites_previos_energia = {}

    def _construir_pestana_comparacion(self):
        """Grafica 9 (estatica): comparacion de metodos, generada bajo demanda."""
        self._figura_comparacion = Figure(figsize=(7, 5), dpi=100)
        self._ax_comparacion = self._figura_comparacion.add_subplot(1, 1, 1)
        self._configurar_eje(
            self._ax_comparacion,
            "Presione \"Comparar metodos\" para generar esta grafica",
            "b / L (posicion relativa del impacto)", "v1 (m/s)")

        self._canvas_comparacion = FigureCanvasTkAgg(
            self._figura_comparacion, master=self._pestana_comparacion)
        self._canvas_comparacion.draw()
        self._canvas_comparacion.get_tk_widget().pack(fill="both", expand=True)

    def _construir_pestana_simulaciones(self):
        """Comparacion de simulaciones superpuestas (estatica, bajo demanda)."""
        self._figura_simulaciones = Figure(figsize=(7, 5), dpi=100)
        self._ax_sim_theta = self._figura_simulaciones.add_subplot(2, 1, 1)
        self._ax_sim_emec = self._figura_simulaciones.add_subplot(2, 1, 2)
        self._configurar_eje(
            self._ax_sim_theta,
            "Presione \"Comparar con/sin amortiguamiento\" para generar esta grafica",
            "Tiempo (s)", "theta (rad)")
        self._configurar_eje(self._ax_sim_emec, "Energia mecanica Emec(t)", "Tiempo (s)", "Emec (J)")
        self._figura_simulaciones.tight_layout()

        self._canvas_simulaciones = FigureCanvasTkAgg(
            self._figura_simulaciones, master=self._pestana_simulaciones)
        self._canvas_simulaciones.draw()
        self._canvas_simulaciones.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Actualizacion en tiempo real (con blitting)
    # ------------------------------------------------------------------
    def agregar_punto(self, t, theta, omega, p, ek,
                       x=None, y=None, v=None, ep=None, emec=None, tension=None):
        """
        Agrega un punto a las graficas en tiempo real y solicita un redibujado.

        Parametros (contrato original, obligatorios):
            t     : instante de tiempo (s).
            theta : angulo (rad).
            omega : velocidad angular (rad/s).
            p     : momentum lineal (kg*m/s).
            ek    : energia cinetica (J).

        Parametros adicionales (opcionales, para las graficas 5-8 del
        Informe Final; si se omiten, la pestana "Energia y dinamica" no
        recibe nuevos puntos en ese cuadro):
            x, y    : posicion del centro de masa (m).
            v       : rapidez tangencial (m/s).
            ep      : energia potencial (J).
            emec    : energia mecanica total (J).
            tension : tension de la cuerda (N).
        """
        self._t.append(t)
        self._theta.append(theta)
        self._omega.append(omega)
        self._p.append(p)
        self._ek.append(ek)

        self._linea_theta.set_data(self._t, self._theta)
        self._linea_omega.set_data(self._t, self._omega)
        self._linea_p.set_data(self._t, self._p)
        self._linea_ek.set_data(self._t, self._ek)

        self._redibujar_con_blitting(
            self._canvas_basica, self._figura_basica,
            self._ejes_basica, self._lineas_basica,
            "_fondo_basica", "_limites_previos_basica")

        if None not in (x, y, v, ep, emec, tension):
            self._x.append(x)
            self._y.append(y)
            self._v.append(v)
            self._ep.append(ep)
            self._emec.append(emec)
            self._tension.append(tension)

            self._linea_x.set_data(self._t, self._x)
            self._linea_y.set_data(self._t, self._y)
            self._linea_v.set_data(self._t, self._v)
            self._linea_ek2.set_data(self._t, self._ek)
            self._linea_ep.set_data(self._t, self._ep)
            self._linea_emec.set_data(self._t, self._emec)
            self._linea_tension.set_data(self._t, self._tension)

            self._redibujar_con_blitting(
                self._canvas_energia, self._figura_energia,
                self._ejes_energia, self._lineas_energia,
                "_fondo_energia", "_limites_previos_energia")

    def _redibujar_con_blitting(self, canvas, figura, ejes, lineas,
                                 attr_fondo, attr_limites):
        """
        Redibuja un conjunto de ejes/lineas usando blitting quiere decir: si
        los limites de los ejes no cambiaron respecto al cuadro anterior, solo
        se restaura el fondo cacheado y se redibujan las lineas (rapido). Si
        algun limite cambio (lo usual mientras la serie sigue creciendo), se
        hace un draw() completo y se recaptura el fondo para los proximos
        cuadros.
        """
        limites_previos = getattr(self, attr_limites)
        limites_cambiaron = False
        for eje in ejes:
            eje.relim()
            eje.autoscale_view()
            limites_actuales = (eje.get_xlim(), eje.get_ylim())
            if limites_previos.get(eje) != limites_actuales:
                limites_cambiaron = True
            limites_previos[eje] = limites_actuales

        fondo = getattr(self, attr_fondo)
        if fondo is None or limites_cambiaron:
            canvas.draw()
            setattr(self, attr_fondo, canvas.copy_from_bbox(figura.bbox))
        else:
            canvas.restore_region(fondo)
            for linea in lineas:
                linea.axes.draw_artist(linea)
            canvas.blit(figura.bbox)
            canvas.flush_events()

    def reiniciar(self):
        """
        Limpia todas las series y las curvas de las pestanas en tiempo real
        para comenzar una nueva simulacion.
        """
        for lista in (self._t, self._theta, self._omega, self._p, self._ek,
                      self._x, self._y, self._ep, self._emec, self._tension,
                      self._v):
            lista.clear()

        for linea in self._lineas_basica + self._lineas_energia:
            linea.set_data([], [])

        for eje in self._ejes_basica + self._ejes_energia:
            eje.relim()
            eje.autoscale_view()

        self._fondo_basica = None
        self._limites_previos_basica = {}
        self._fondo_energia = None
        self._limites_previos_energia = {}

        self._canvas_basica.draw()
        self._canvas_energia.draw()

    # ------------------------------------------------------------------
    # Graficas estaticas bajo demanda (Informe Final)
    # ------------------------------------------------------------------
    def graficar_comparacion_metodos(self, m, M, v0, L, I_caja_cm=0.0, n=60):
        """
        Grafica 9: compara, para un choque con parametros (m, M, v0) fijos, la
        velocidad tras el impacto segun el metodo aproximado (masa puntual,
        constante) contra el metodo exacto (v1_equivalente = omega1 * L),
        en funcion de la posicion relativa del impacto b/L (b = brazo de
        palanca, L = distancia del pivote al centro de masa de la caja).

        Con b = L (impacto central) ambos metodos coinciden; al alejarse el
        impacto del centro de masa (b < L) el metodo exacto se aparta del
        aproximado, lo cual es el punto que esta grafica busca ilustrar.
        """
        # Importacion diferida para evitar un ciclo de importacion al cargar
        # el modulo (colision.py no depende de graficas.py).
        from src.colision import velocidad_tras_impacto, velocidad_angular_tras_impacto_exacto

        v1_aproximado = velocidad_tras_impacto(m, M, v0)
        razones_b_l = np.linspace(0.05, 1.0, n)
        v1_exacto = np.array([
            velocidad_angular_tras_impacto_exacto(m, M, v0, L, I_caja_cm, razon * L) * L
            for razon in razones_b_l
        ])

        self._ax_comparacion.clear()
        self._configurar_eje(
            self._ax_comparacion,
            "Metodo exacto vs aproximado segun la posicion del impacto",
            "b / L (posicion relativa del impacto)", "v1 (m/s)")
        self._ax_comparacion.axhline(
            v1_aproximado, color="tab:blue", linestyle="--",
            label="Aproximado (masa puntual, constante)")
        self._ax_comparacion.plot(
            razones_b_l, v1_exacto, color="tab:red", marker="o", markersize=3,
            label="Exacto (v1_equivalente = omega1 * L)")
        self._ax_comparacion.legend(fontsize=8, loc="best")
        self._figura_comparacion.tight_layout()
        self._canvas_comparacion.draw()

    def comparar_simulaciones(self, datos_a, etiqueta_a, datos_b, etiqueta_b):
        """
        Superpone dos corridas completas de simular_oscilacion (por ejemplo,
        con y sin amortiguamiento) en la pestana "Comparar simulaciones":
        theta(t) y Emec(t) de ambas, con leyenda.

        Parametros:
            datos_a, datos_b     : dicts devueltos por simular_oscilacion.
            etiqueta_a, etiqueta_b : nombres para la leyenda.
        """
        self._ax_sim_theta.clear()
        self._ax_sim_emec.clear()
        self._configurar_eje(self._ax_sim_theta, "Angulo theta(t)", "Tiempo (s)", "theta (rad)")
        self._configurar_eje(self._ax_sim_emec, "Energia mecanica Emec(t)", "Tiempo (s)", "Emec (J)")

        self._ax_sim_theta.plot(datos_a["t"], datos_a["theta"], label=etiqueta_a, color="tab:blue")
        self._ax_sim_theta.plot(datos_b["t"], datos_b["theta"], label=etiqueta_b, color="tab:red")
        self._ax_sim_theta.legend(fontsize=8, loc="best")

        self._ax_sim_emec.plot(datos_a["t"], datos_a["emec"], label=etiqueta_a, color="tab:blue")
        self._ax_sim_emec.plot(datos_b["t"], datos_b["emec"], label=etiqueta_b, color="tab:red")
        self._ax_sim_emec.legend(fontsize=8, loc="best")

        self._figura_simulaciones.tight_layout()
        self._canvas_simulaciones.draw()

    def exportar_png(self, carpeta="reportes", prefijo="pendulo"):
        """
        Exporta las figuras del panel a PNG (una por pestana) para usarlas en
        el Informe Final.

        Parametros:
            carpeta : carpeta de destino (se crea si no existe).
            prefijo : prefijo de los nombres de archivo.

        Retorna:
            Lista con las rutas de los archivos generados.
        """
        os.makedirs(carpeta, exist_ok=True)
        figuras = {
            "basicas": self._figura_basica,
            "energia_dinamica": self._figura_energia,
            "comparacion_metodos": self._figura_comparacion,
            "comparar_simulaciones": self._figura_simulaciones,
        }
        rutas = []
        for nombre, figura in figuras.items():
            ruta = os.path.join(carpeta, "{}_{}.png".format(prefijo, nombre))
            figura.savefig(ruta, dpi=150)
            rutas.append(ruta)
        return rutas


def generar_figuras_estaticas(datos, carpeta="reportes", prefijo="pendulo"):
    """
    Genera y guarda en PNG las graficas 1-8 a partir de un dict COMPLETO
    devuelto por oscilacion.simular_oscilacion (no cuadro a cuadro), sin
    necesidad de Tkinter. Pensada para el modo sin GUI de main.py (ejecutar
    una simulacion y exportar las graficas para el Informe Final).

    Parametros:
        datos   : dict devuelto por simular_oscilacion (debe incluir al menos
                  t, theta, omega, p, ek; si ademas incluye x, y, ep, emec,
                  tension tambien se generan las graficas 5-8).
        carpeta : carpeta de destino (se crea si no existe).
        prefijo : prefijo de los nombres de archivo.

    Retorna:
        Lista con las rutas de los archivos PNG generados.
    """
    os.makedirs(carpeta, exist_ok=True)
    rutas = []

    def _guardar(figura, nombre):
        ruta = os.path.join(carpeta, "{}_{}.png".format(prefijo, nombre))
        figura.savefig(ruta, dpi=150)
        rutas.append(ruta)

    t = datos["t"]

    figura_basica = Figure(figsize=(9, 6), dpi=120)
    figura_basica.suptitle("Pendulo balistico - magnitudes basicas")
    ejes_series = [
        ("theta", "Angulo theta(t)", "theta (rad)"),
        ("omega", "Velocidad angular omega(t)", "omega (rad/s)"),
        ("p", "Momentum lineal p(t)", "p (kg*m/s)"),
        ("ek", "Energia cinetica Ek(t)", "Ek (J)"),
    ]
    for indice, (clave, titulo, etiqueta_y) in enumerate(ejes_series, start=1):
        eje = figura_basica.add_subplot(2, 2, indice)
        eje.plot(t, datos[clave], color="tab:blue")
        PanelGraficas._configurar_eje(eje, titulo, "Tiempo (s)", etiqueta_y)
    figura_basica.tight_layout(rect=(0, 0, 1, 0.96))
    _guardar(figura_basica, "basicas")

    if all(clave in datos for clave in ("x", "y", "ep", "emec", "tension")):
        figura_energia = Figure(figsize=(9, 6), dpi=120)
        figura_energia.suptitle("Pendulo balistico - energia y cinematica")

        eje_posicion = figura_energia.add_subplot(2, 2, 1)
        eje_posicion.plot(t, datos["x"], label="x(t)", color="tab:blue")
        eje_posicion.plot(t, datos["y"], label="y(t)", color="tab:cyan")
        eje_posicion.legend(fontsize=8)
        PanelGraficas._configurar_eje(eje_posicion, "Posicion del centro de masa", "Tiempo (s)", "x, y (m)")

        eje_velocidad = figura_energia.add_subplot(2, 2, 2)
        eje_velocidad.plot(t, datos["v"], color="tab:purple")
        PanelGraficas._configurar_eje(eje_velocidad, "Rapidez tangencial v(t)", "Tiempo (s)", "v (m/s)")

        eje_energias = figura_energia.add_subplot(2, 2, 3)
        eje_energias.plot(t, datos["ek"], label="Ek", color="tab:red")
        eje_energias.plot(t, datos["ep"], label="Ep", color="tab:green")
        eje_energias.plot(t, datos["emec"], label="Emec", color="tab:gray")
        eje_energias.legend(fontsize=8)
        PanelGraficas._configurar_eje(eje_energias, "Energias Ek, Ep, Emec", "Tiempo (s)", "Energia (J)")

        eje_tension = figura_energia.add_subplot(2, 2, 4)
        eje_tension.plot(t, datos["tension"], color="tab:brown")
        PanelGraficas._configurar_eje(eje_tension, "Tension de la cuerda T(t)", "Tiempo (s)", "T (N)")

        figura_energia.tight_layout(rect=(0, 0, 1, 0.96))
        _guardar(figura_energia, "energia_dinamica")

    return rutas


def _demostracion():
    """
    Demo que se ejecuta con `python -m src.graficas`.

    Abre una ventana Tkinter con el panel de graficas y reproduce, cuadro a
    cuadro con after(), una oscilacion real calculada por el modulo oscilacion
    a partir de la velocidad tras el impacto del modulo colision. Sirve para
    verificar el panel sin depender de la interfaz completa.
    """
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
            panel.graficar_comparacion_metodos(m, M, v0, L)
            return
        panel.agregar_punto(
            datos["t"][i], datos["theta"][i], datos["omega"][i],
            datos["p"][i], datos["ek"][i], x=datos["x"][i], y=datos["y"][i],
            v=datos["v"][i], ep=datos["ep"][i], emec=datos["emec"][i],
            tension=datos["tension"][i])
        indice["i"] = i + 1
        # Reprograma el siguiente cuadro (~20 ms => ~50 cuadros por segundo).
        ventana.after(20, _siguiente_cuadro)

    ventana.after(0, _siguiente_cuadro)
    ventana.mainloop()


if __name__ == "__main__":
    _demostracion()
