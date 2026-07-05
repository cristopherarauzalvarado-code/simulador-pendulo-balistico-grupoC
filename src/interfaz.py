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

    Flujo de datos que conecta los modulos:
        colision.velocidad_tras_impacto(m, M, v0) -> v1
        oscilacion.simular_oscilacion(m, M, L, v1, t_max, dt) -> datos
        graficas.PanelGraficas.agregar_punto(...) por cada cuadro

    La animacion usa el metodo after() de Tkinter (no bloqueante).

Estado:
    Baseline implementado. Metodo aproximado: conecta colision -> oscilacion ->
    panel de graficas y anima el pendulo cuadro a cuadro con after().

Contrato (no cambiar las firmas):
    App(tk.Tk)
    lanzar()

TODO (baseline):
    - [x] Construir los campos de entrada (m, M, v0, L) y el boton de inicio.
    - [x] Crear el Canvas de animacion del pendulo.
    - [x] Incrustar el PanelGraficas y conectar colision -> oscilacion -> panel.
    - [x] Animar con after() llamando a agregar_punto por cuadro.
TODO (Informe Final):
    - [ ] Controles para pausar, reanudar y reiniciar la animacion.
    - [ ] Selector de metodo: aproximado vs exacto (con inercia).
    - [ ] Casilla para activar/desactivar el amortiguamiento.
    - [ ] Panel numerico con v1, energia perdida y periodo estimado.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from src.colision import (energia_perdida, velocidad_tras_impacto)
from src.graficas import PanelGraficas
from src.oscilacion import simular_oscilacion

# Parametros de la simulacion temporal (no expuestos al usuario en el baseline).
T_MAX = 6.0            # duracion total de la simulacion (s)
DT = 0.02              # paso de muestreo de la oscilacion (s)
MS_POR_CUADRO = 20     # milisegundos entre cuadros de animacion (~50 FPS)

# Geometria del lienzo de animacion del pendulo. El pivote se coloca en el
# centro del lienzo y la cuerda se dibuja corta para que la caja quepa en
# cualquier angulo, incluso cuando la oscilacion es tan energetica que el
# pendulo pasa la horizontal o da la vuelta completa.
ANCHO_CANVAS = 420     # ancho del Canvas de animacion (px)
ALTO_CANVAS = 460      # alto del Canvas de animacion (px)
PIVOTE_X = ANCHO_CANVAS // 2   # posicion X del pivote de la cuerda (px)
PIVOTE_Y = ALTO_CANVAS // 2    # posicion Y del pivote de la cuerda (px)
LARGO_CUERDA_PX = 170          # largo de la cuerda dibujada (px, escala visual)
LADO_CAJA_PX = 44              # lado de la caja suspendida (px)

# Valores por defecto de los campos de entrada (ejemplo tipico del enunciado).
VALORES_POR_DEFECTO = {"m": "0.05", "M": "2.0", "v0": "300.0", "L": "2.0"}


class App(tk.Tk):
    """
    Ventana principal del simulador del pendulo balistico.

    Estructura la ventana en dos zonas:
        - Panel izquierdo: campos de entrada, boton de inicio, resultados
          numericos y el Canvas con la animacion del pendulo.
        - Panel derecho: el PanelGraficas con las 4 graficas en tiempo real.

    La animacion se realiza con after() (no bloqueante): en cada cuadro se
    reposiciona el pendulo en el Canvas y se agrega el punto correspondiente al
    panel de graficas.
    """

    def __init__(self):
        super().__init__()
        self.title("Simulador de Pendulo Balistico - Fisica I - Grupo C")
        self.resizable(False, False)

        # Estado de la animacion en curso.
        self._datos = None          # dict devuelto por simular_oscilacion
        self._indice = 0            # indice del cuadro actual
        self._tarea_after = None    # id del after() programado (para cancelar)
        self._animando = False      # bandera de animacion activa

        # Diccionario de variables de los campos de entrada.
        self._entradas = {}

        self._construir_controles()
        self._construir_animacion()
        self._construir_panel_graficas()

        # Cierre ordenado: cancela cualquier after() pendiente.
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------
    def _construir_controles(self):
        """Crea los campos de entrada (m, M, v0, L), el boton y los resultados."""
        marco = ttk.LabelFrame(self, text="Parametros de la simulacion")
        marco.grid(row=0, column=0, padx=10, pady=10, sticky="new")

        # Etiqueta descriptiva, clave interna y unidad de cada campo.
        campos = [
            ("Masa del proyectil m", "m", "kg"),
            ("Masa de la caja M", "M", "kg"),
            ("Velocidad inicial v0", "v0", "m/s"),
            ("Longitud de la cuerda L", "L", "m"),
        ]

        for fila, (etiqueta, clave, unidad) in enumerate(campos):
            ttk.Label(marco, text=etiqueta + ":").grid(
                row=fila, column=0, sticky="w", padx=6, pady=4)
            variable = tk.StringVar(value=VALORES_POR_DEFECTO[clave])
            self._entradas[clave] = variable
            ttk.Entry(marco, textvariable=variable, width=10).grid(
                row=fila, column=1, padx=6, pady=4)
            ttk.Label(marco, text=unidad).grid(
                row=fila, column=2, sticky="w", padx=(0, 6))

        # Boton que dispara la simulacion completa.
        self._boton_iniciar = ttk.Button(
            marco, text="Iniciar simulacion", command=self._iniciar_simulacion)
        self._boton_iniciar.grid(
            row=len(campos), column=0, columnspan=3, pady=(8, 6))

        # Etiqueta de resultados numericos (v1 y energia perdida en el choque).
        self._texto_resultado = tk.StringVar(
            value="Ingrese los parametros y presione Iniciar simulacion.")
        ttk.Label(
            marco, textvariable=self._texto_resultado, wraplength=260,
            justify="left", foreground="#333333").grid(
                row=len(campos) + 1, column=0, columnspan=3,
                sticky="w", padx=6, pady=(0, 6))

    def _construir_animacion(self):
        """Crea el Canvas donde se anima el pendulo (cuerda + caja)."""
        marco = ttk.LabelFrame(self, text="Animacion del pendulo")
        marco.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self._canvas = tk.Canvas(
            marco, width=ANCHO_CANVAS, height=ALTO_CANVAS, bg="white",
            highlightthickness=1, highlightbackground="#cccccc")
        self._canvas.pack(padx=4, pady=4)

        # Marca fija del pivote (punto del que cuelga la cuerda).
        radio_pivote = 4
        self._canvas.create_oval(
            PIVOTE_X - radio_pivote, PIVOTE_Y - radio_pivote,
            PIVOTE_X + radio_pivote, PIVOTE_Y + radio_pivote,
            fill="#444444", outline="")

        # Linea vertical de referencia (posicion de reposo, theta = 0).
        self._canvas.create_line(
            PIVOTE_X, PIVOTE_Y, PIVOTE_X, PIVOTE_Y + LARGO_CUERDA_PX,
            fill="#dddddd", dash=(4, 4))

        # Elementos moviles: la cuerda y la caja. Se crean en reposo y luego se
        # reposicionan en cada cuadro con _dibujar_pendulo.
        self._cuerda = self._canvas.create_line(
            PIVOTE_X, PIVOTE_Y, PIVOTE_X, PIVOTE_Y + LARGO_CUERDA_PX,
            fill="#8b5a2b", width=2)
        self._caja = self._canvas.create_rectangle(
            0, 0, 0, 0, fill="#4a90d9", outline="#2c5aa0", width=2)

        self._dibujar_pendulo(0.0)

    def _construir_panel_graficas(self):
        """Incrusta el PanelGraficas (modulo graficas) a la derecha."""
        marco = ttk.LabelFrame(self, text="Graficas en tiempo real")
        marco.grid(row=0, column=1, rowspan=2, padx=(0, 10), pady=10,
                   sticky="nsew")

        self._panel = PanelGraficas(marco)
        self._panel.widget.pack(fill="both", expand=True, padx=4, pady=4)

    # ------------------------------------------------------------------
    # Logica de la simulacion y la animacion
    # ------------------------------------------------------------------
    def _leer_parametros(self):
        """
        Lee y valida los campos de entrada.

        Retorna la tupla (m, M, v0, L) con valores float validos, o None si
        alguna entrada es invalida (en ese caso muestra un mensaje al usuario).
        """
        try:
            m = float(self._entradas["m"].get())
            M = float(self._entradas["M"].get())
            v0 = float(self._entradas["v0"].get())
            L = float(self._entradas["L"].get())
        except ValueError:
            messagebox.showerror(
                "Entrada invalida",
                "Todos los parametros deben ser numeros validos.")
            return None

        # Validaciones fisicas basicas antes de llamar a los modulos.
        if m <= 0:
            messagebox.showerror(
                "Entrada invalida", "La masa del proyectil m debe ser mayor que cero.")
            return None
        if M < 0:
            messagebox.showerror(
                "Entrada invalida", "La masa de la caja M no puede ser negativa.")
            return None
        if L <= 0:
            messagebox.showerror(
                "Entrada invalida", "La longitud de la cuerda L debe ser mayor que cero.")
            return None

        return m, M, v0, L

    def _iniciar_simulacion(self):
        """Calcula la simulacion completa y arranca la animacion cuadro a cuadro."""
        parametros = self._leer_parametros()
        if parametros is None:
            return
        m, M, v0, L = parametros

        # Detiene cualquier animacion previa y limpia el panel de graficas.
        self._detener_animacion()
        self._panel.reiniciar()

        # 1) Colision inelastica: velocidad comun tras el impacto.
        v1 = velocidad_tras_impacto(m, M, v0)
        delta_e = energia_perdida(m, M, v0)

        # 2) Oscilacion del pendulo a partir de v1.
        self._datos = simular_oscilacion(m, M, L, v1, T_MAX, DT)
        self._indice = 0

        # Muestra los resultados numericos del choque.
        self._texto_resultado.set(
            "Velocidad tras el impacto v1 = {:.4f} m/s\n"
            "Energia perdida en el choque = {:.4f} J\n"
            "Cuadros a animar = {}".format(
                v1, delta_e, len(self._datos["t"])))

        # 3) Arranca la animacion no bloqueante.
        self._animando = True
        self._boton_iniciar.config(state="disabled")
        self._tarea_after = self.after(0, self._siguiente_cuadro)

    def _siguiente_cuadro(self):
        """Dibuja un cuadro de la animacion y programa el siguiente con after()."""
        if self._datos is None:
            return

        i = self._indice
        if i >= len(self._datos["t"]):
            # Fin de la animacion: rehabilita el boton para una nueva corrida.
            self._animando = False
            self._tarea_after = None
            self._boton_iniciar.config(state="normal")
            return

        # Reposiciona el pendulo en el Canvas segun el angulo actual.
        self._dibujar_pendulo(self._datos["theta"][i])

        # Agrega el punto al panel de graficas (theta, omega, p, ek).
        self._panel.agregar_punto(
            self._datos["t"][i], self._datos["theta"][i],
            self._datos["omega"][i], self._datos["p"][i], self._datos["ek"][i])

        # Avanza al siguiente cuadro y reprograma.
        self._indice = i + 1
        self._tarea_after = self.after(MS_POR_CUADRO, self._siguiente_cuadro)

    def _dibujar_pendulo(self, theta):
        """
        Reposiciona la cuerda y la caja en el Canvas para el angulo dado.

        Parametros:
            theta : angulo respecto a la vertical (rad). theta = 0 es la posicion
                    de reposo (cuerda vertical hacia abajo).
        """
        import math

        # Posicion de la caja: el pivote esta arriba y el angulo se mide desde la
        # vertical. En coordenadas de pantalla, Y crece hacia abajo.
        caja_x = PIVOTE_X + LARGO_CUERDA_PX * math.sin(theta)
        caja_y = PIVOTE_Y + LARGO_CUERDA_PX * math.cos(theta)

        # Actualiza la cuerda (del pivote al centro de la caja).
        self._canvas.coords(self._cuerda, PIVOTE_X, PIVOTE_Y, caja_x, caja_y)

        # Actualiza la caja (cuadrado centrado en el extremo de la cuerda).
        mitad = LADO_CAJA_PX / 2
        self._canvas.coords(
            self._caja, caja_x - mitad, caja_y - mitad,
            caja_x + mitad, caja_y + mitad)

    def _detener_animacion(self):
        """Cancela el after() pendiente y marca la animacion como detenida."""
        if self._tarea_after is not None:
            self.after_cancel(self._tarea_after)
            self._tarea_after = None
        self._animando = False

    def _al_cerrar(self):
        """Manejo del cierre de la ventana: cancela tareas y destruye la app."""
        self._detener_animacion()
        self.destroy()


def lanzar():
    """
    Crea la aplicacion y arranca el bucle principal de Tkinter.

    Es el punto de entrada que invoca src/main.iniciar().
    """
    app = App()
    app.mainloop()
