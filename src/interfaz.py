# -*- coding: utf-8 -*-
"""
Modulo: interfaz.py
Responsable: Tatiana Solis

Interfaz grafica del simulador de Pendulo Balistico.

Incluye:
    - Parametros m, M, v0 y L.
    - Metodo aproximado y exacto.
    - Inercia de la caja y brazo de palanca.
    - Amortiguamiento viscoso.
    - Pausar, reanudar y reiniciar.
    - Animacion del pendulo.
    - Resultados numericos.
    - Graficas en tiempo real.
    - Comparacion de metodos.
    - Comparacion con/sin amortiguamiento.
    - Exportacion de graficas a PNG.
"""

import math
import tkinter as tk
from tkinter import messagebox, ttk

from src.colision import (
    energia_perdida,
    resumen_colision_exacto,
    velocidad_tras_impacto
)

from src.graficas import PanelGraficas
from src.oscilacion import simular_oscilacion


# ==============================================================
# SIMULACION
# ==============================================================

T_MAX = 6.0
DT = 0.02
MS_POR_CUADRO = 20


# ==============================================================
# ANIMACION
# ==============================================================

ANCHO_CANVAS = 420
ALTO_CANVAS = 360

PIVOTE_X = ANCHO_CANVAS // 2
PIVOTE_Y = 75

# Escala visual.
# No modifica la longitud fisica real L.
LARGO_CUERDA_PX = 140

# Tamano visual de la caja.
LADO_CAJA_PX = 44


# ==============================================================
# VALORES INICIALES
# ==============================================================

VALORES_POR_DEFECTO = {
    "m": "0.05",
    "M": "2.0",
    "v0": "300.0",
    "L": "2.0"
}

DEFECTO_I_CAJA_CM = "0.0"
DEFECTO_COEF_AMORTIGUAMIENTO = "0.15"

METODOS_DISPONIBLES = (
    "Aproximado (masa puntual)",
    "Exacto (inercia rotacional)"
)


class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title(
            "Simulador de Pendulo Balistico - Fisica I - Grupo C"
        )

        self.configure(bg="#f4f7fb")

        self._configurar_estilos()

        # Mantiene la distribucion original.
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # ----------------------------------------------------------
        # Estado de la animacion.
        # ----------------------------------------------------------

        self._datos = None
        self._datos_sin_amortiguar = None

        self._indice = 0
        self._tarea_after = None

        self._animando = False
        self._pausado = False

        self._ultimos_parametros = None

        # Variables asociadas a los campos de entrada.
        self._entradas = {}

        # Construccion de la interfaz.
        self._construir_controles()
        self._construir_animacion()
        self._construir_panel_graficas()

        # ----------------------------------------------------------
        # Tamano inicial de ventana.
        # ----------------------------------------------------------

        self.update_idletasks()

        ancho_inicial = self.winfo_reqwidth() + 40
        alto_inicial = self.winfo_reqheight() + 30

        self.geometry(
            "{}x{}".format(
                ancho_inicial,
                alto_inicial
            )
        )

        self.minsize(
            min(ancho_inicial, 1000),
            min(alto_inicial, 650)
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self._al_cerrar
        )

    # ==============================================================
    # ESTILOS
    # ==============================================================

    def _configurar_estilos(self):
        """
        Mejora la apariencia de la interfaz sin cambiar
        su estructura ni funcionamiento.
        """

        estilo = ttk.Style(self)

        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "TLabelframe",
            background="#f4f7fb",
            bordercolor="#cbd5e1",
            lightcolor="#cbd5e1",
            darkcolor="#cbd5e1",
            borderwidth=1
        )

        estilo.configure(
            "TLabelframe.Label",
            background="#f4f7fb",
            foreground="#174a8b",
            font=("Segoe UI Semibold", 10)
        )

        estilo.configure(
            "TFrame",
            background="#f4f7fb"
        )

        estilo.configure(
            "TLabel",
            background="#f4f7fb",
            foreground="#243447",
            font=("Segoe UI", 9)
        )

        estilo.configure(
            "TEntry",
            padding=4,
            font=("Segoe UI", 9),
            fieldbackground="white"
        )

        estilo.configure(
            "TCombobox",
            padding=4,
            font=("Segoe UI", 9)
        )

        estilo.configure(
            "TCheckbutton",
            background="#f4f7fb",
            foreground="#243447",
            font=("Segoe UI", 9)
        )

        estilo.map(
            "TCheckbutton",
            background=[
                ("active", "#f4f7fb")
            ]
        )

        estilo.configure(
            "TButton",
            padding=(8, 5),
            font=("Segoe UI", 9)
        )

        estilo.configure(
            "Principal.TButton",
            background="#2563eb",
            foreground="white",
            padding=(10, 6),
            font=("Segoe UI Semibold", 9)
        )

        estilo.map(
            "Principal.TButton",
            background=[
                ("active", "#1d4ed8"),
                ("disabled", "#94a3b8")
            ],
            foreground=[
                ("active", "white"),
                ("disabled", "#e2e8f0")
            ]
        )

    # ==============================================================
    # CONTROLES
    # ==============================================================

    def _construir_controles(self):
        """
        Construye los parametros, selector de metodo,
        amortiguamiento, botones y resultados.
        """

        marco = ttk.LabelFrame(
            self,
            text="⚙  Parametros de la simulacion"
        )

        marco.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky="new"
        )

        campos = [
            ("Masa del proyectil m", "m", "kg"),
            ("Masa de la caja M", "M", "kg"),
            ("Velocidad inicial v0", "v0", "m/s"),
            ("Longitud de la cuerda L", "L", "m"),
        ]

        fila = 0

        for etiqueta, clave, unidad in campos:

            ttk.Label(
                marco,
                text=etiqueta + ":"
            ).grid(
                row=fila,
                column=0,
                sticky="w",
                padx=6,
                pady=4
            )

            variable = tk.StringVar(
                value=VALORES_POR_DEFECTO[clave]
            )

            self._entradas[clave] = variable

            ttk.Entry(
                marco,
                textvariable=variable,
                width=10
            ).grid(
                row=fila,
                column=1,
                padx=6,
                pady=4
            )

            ttk.Label(
                marco,
                text=unidad
            ).grid(
                row=fila,
                column=2,
                sticky="w",
                padx=(0, 6)
            )

            fila += 1

        # ----------------------------------------------------------
        # Metodo.
        # ----------------------------------------------------------

        ttk.Label(
            marco,
            text="Metodo:"
        ).grid(
            row=fila,
            column=0,
            sticky="w",
            padx=6,
            pady=(10, 4)
        )

        self._metodo_var = tk.StringVar(
            value=METODOS_DISPONIBLES[0]
        )

        combo_metodo = ttk.Combobox(
            marco,
            textvariable=self._metodo_var,
            values=METODOS_DISPONIBLES,
            state="readonly",
            width=24
        )

        combo_metodo.grid(
            row=fila,
            column=1,
            columnspan=2,
            sticky="w",
            padx=6,
            pady=(10, 4)
        )

        combo_metodo.bind(
            "<<ComboboxSelected>>",
            self._al_cambiar_metodo
        )

        fila += 1

        # ----------------------------------------------------------
        # Parametros del metodo exacto.
        # ----------------------------------------------------------

        self._marco_exacto = ttk.Frame(marco)

        self._marco_exacto.grid(
            row=fila,
            column=0,
            columnspan=3,
            sticky="w"
        )

        ttk.Label(
            self._marco_exacto,
            text="Inercia de la caja I_cm:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=6,
            pady=2
        )

        self._entradas["I_caja_cm"] = tk.StringVar(
            value=DEFECTO_I_CAJA_CM
        )

        ttk.Entry(
            self._marco_exacto,
            textvariable=self._entradas["I_caja_cm"],
            width=8
        ).grid(
            row=0,
            column=1,
            padx=6,
            pady=2
        )

        ttk.Label(
            self._marco_exacto,
            text="kg*m^2"
        ).grid(
            row=0,
            column=2,
            sticky="w"
        )

        ttk.Label(
            self._marco_exacto,
            text="Brazo de palanca b:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=6,
            pady=2
        )

        self._entradas["b"] = tk.StringVar(
            value=""
        )

        ttk.Entry(
            self._marco_exacto,
            textvariable=self._entradas["b"],
            width=8
        ).grid(
            row=1,
            column=1,
            padx=6,
            pady=2
        )

        ttk.Label(
            self._marco_exacto,
            text="m (vacio = L, impacto central)"
        ).grid(
            row=1,
            column=2,
            sticky="w"
        )

        fila += 1

        self._al_cambiar_metodo()

        # ----------------------------------------------------------
        # Amortiguamiento.
        # ----------------------------------------------------------

        self._amortiguar_var = tk.BooleanVar(
            value=False
        )

        ttk.Checkbutton(
            marco,
            text="Amortiguamiento viscoso",
            variable=self._amortiguar_var,
            command=self._al_cambiar_amortiguamiento
        ).grid(
            row=fila,
            column=0,
            columnspan=2,
            sticky="w",
            padx=6,
            pady=(6, 2)
        )

        self._entradas["coef_amortiguamiento"] = tk.StringVar(
            value=DEFECTO_COEF_AMORTIGUAMIENTO
        )

        self._entrada_coef = ttk.Entry(
            marco,
            textvariable=self._entradas["coef_amortiguamiento"],
            width=8,
            state="disabled"
        )

        self._entrada_coef.grid(
            row=fila,
            column=2,
            padx=6,
            pady=(6, 2)
        )

        fila += 1

        # ----------------------------------------------------------
        # Botones principales.
        # ----------------------------------------------------------

        marco_botones = ttk.Frame(marco)

        marco_botones.grid(
            row=fila,
            column=0,
            columnspan=3,
            pady=(8, 6)
        )

        self._boton_iniciar = ttk.Button(
            marco_botones,
            text="▶  Iniciar simulacion",
            command=self._iniciar_simulacion,
            style="Principal.TButton"
        )

        self._boton_iniciar.grid(
            row=0,
            column=0,
            padx=3
        )

        self._boton_pausar = ttk.Button(
            marco_botones,
            text="⏸  Pausar",
            command=self._alternar_pausa,
            state="disabled"
        )

        self._boton_pausar.grid(
            row=0,
            column=1,
            padx=3
        )

        self._boton_reiniciar = ttk.Button(
            marco_botones,
            text="↻  Reiniciar",
            command=self._reiniciar_animacion,
            state="disabled"
        )

        self._boton_reiniciar.grid(
            row=0,
            column=2,
            padx=3
        )

        fila += 1

        # ----------------------------------------------------------
        # Botones adicionales.
        # ----------------------------------------------------------

        marco_extra = ttk.Frame(marco)

        marco_extra.grid(
            row=fila,
            column=0,
            columnspan=3,
            pady=(0, 6)
        )

        ttk.Button(
            marco_extra,
            text="Comparar metodos",
            command=self._comparar_metodos
        ).grid(
            row=0,
            column=0,
            padx=3,
            pady=2
        )

        ttk.Button(
            marco_extra,
            text="Comparar con/sin amortiguamiento",
            command=self._comparar_amortiguamiento
        ).grid(
            row=0,
            column=1,
            padx=3,
            pady=2
        )

        ttk.Button(
            marco_extra,
            text="▣  Exportar graficas a PNG",
            command=self._exportar_png
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            padx=3,
            pady=2
        )

        fila += 1

        # ----------------------------------------------------------
        # Resultados.
        # ----------------------------------------------------------

        self._texto_resultado = tk.StringVar(
            value=(
                "Ingrese los parametros y presione "
                "Iniciar simulacion."
            )
        )

        ttk.Label(
            marco,
            textvariable=self._texto_resultado,
            wraplength=300,
            justify="left",
            foreground="#475569"
        ).grid(
            row=fila,
            column=0,
            columnspan=3,
            sticky="w",
            padx=6,
            pady=(2, 6)
        )

    # ==============================================================
    # ANIMACION
    # ==============================================================

    def _construir_animacion(self):
        """
        Construye el area de animacion.

        La escala visual fue ajustada para que el pendulo permanezca
        completamente visible incluso con angulos grandes.
        """

        marco = ttk.LabelFrame(
            self,
            text="⚙  Animacion del pendulo"
        )

        marco.grid(
            row=1,
            column=0,
            padx=10,
            pady=(0, 10),
            sticky="nsew"
        )

        self._canvas = tk.Canvas(
            marco,
            width=ANCHO_CANVAS,
            height=ALTO_CANVAS,
            bg="#fbfdff",
            highlightthickness=1,
            highlightbackground="#cbd5e1"
        )

        self._canvas.pack(
            padx=4,
            pady=4
        )

        # ----------------------------------------------------------
        # Titulo dentro del Canvas.
        # ----------------------------------------------------------

        self._canvas.create_text(
            12,
            12,
            anchor="nw",
            text="Movimiento del sistema",
            fill="#64748b",
            font=("Segoe UI", 9)
        )

        # ----------------------------------------------------------
        # Soporte superior.
        # ----------------------------------------------------------

        self._canvas.create_line(
            PIVOTE_X - 62,
            PIVOTE_Y - 18,
            PIVOTE_X + 62,
            PIVOTE_Y - 18,
            fill="#64748b",
            width=7
        )

        self._canvas.create_line(
            PIVOTE_X - 47,
            PIVOTE_Y - 18,
            PIVOTE_X - 30,
            PIVOTE_Y + 4,
            fill="#94a3b8",
            width=3
        )

        self._canvas.create_line(
            PIVOTE_X + 47,
            PIVOTE_Y - 18,
            PIVOTE_X + 30,
            PIVOTE_Y + 4,
            fill="#94a3b8",
            width=3
        )

        # ----------------------------------------------------------
        # Pivote.
        # ----------------------------------------------------------

        radio_pivote = 9

        self._canvas.create_oval(
            PIVOTE_X - radio_pivote,
            PIVOTE_Y - radio_pivote,
            PIVOTE_X + radio_pivote,
            PIVOTE_Y + radio_pivote,
            fill="#334155",
            outline="#0f172a",
            width=2
        )

        # ----------------------------------------------------------
        # Linea vertical de referencia.
        # ----------------------------------------------------------

        self._canvas.create_line(
            PIVOTE_X,
            PIVOTE_Y,
            PIVOTE_X,
            PIVOTE_Y + LARGO_CUERDA_PX,
            fill="#d1d5db",
            dash=(5, 5),
            width=1
        )

        # ----------------------------------------------------------
        # Cuerda.
        # ----------------------------------------------------------

        self._cuerda = self._canvas.create_line(
            PIVOTE_X,
            PIVOTE_Y,
            PIVOTE_X,
            PIVOTE_Y + LARGO_CUERDA_PX,
            fill="#a16207",
            width=4
        )

        # ----------------------------------------------------------
        # Caja.
        #
        # Se utiliza polygon en lugar de rectangle para permitir
        # la rotacion visual.
        # ----------------------------------------------------------

        self._caja = self._canvas.create_polygon(
            0, 0,
            0, 0,
            0, 0,
            0, 0,
            fill="#3b82f6",
            outline="#1e40af",
            width=3
        )

        # ----------------------------------------------------------
        # Proyectil incrustado.
        # ----------------------------------------------------------

        self._proyectil = self._canvas.create_oval(
            0,
            0,
            0,
            0,
            fill="#1f2937",
            outline="#111827",
            width=1
        )

        # ----------------------------------------------------------
        # Angulo actual.
        # ----------------------------------------------------------

        self._texto_angulo_canvas = self._canvas.create_text(
            12,
            ALTO_CANVAS - 18,
            anchor="w",
            text="θ = 0.00°",
            fill="#475569",
            font=("Segoe UI Semibold", 9)
        )

        self._dibujar_pendulo(0.0)

    # ==============================================================
    # GRAFICAS
    # ==============================================================

    def _construir_panel_graficas(self):

        marco = ttk.LabelFrame(
            self,
            text="▥  Graficas"
        )

        marco.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=(0, 10),
            pady=10,
            sticky="nsew"
        )

        self._panel = PanelGraficas(marco)

        self._panel.widget.pack(
            fill="both",
            expand=True,
            padx=4,
            pady=4
        )

    # ==============================================================
    # CAMBIO DE METODO
    # ==============================================================

    def _al_cambiar_metodo(self, _evento=None):

        es_exacto = (
            self._metodo_var.get()
            == METODOS_DISPONIBLES[1]
        )

        estado = (
            "normal"
            if es_exacto
            else "disabled"
        )

        for hijo in self._marco_exacto.winfo_children():

            if isinstance(hijo, ttk.Entry):
                hijo.config(state=estado)

    # ==============================================================
    # CAMBIO DE AMORTIGUAMIENTO
    # ==============================================================

    def _al_cambiar_amortiguamiento(self):

        estado = (
            "normal"
            if self._amortiguar_var.get()
            else "disabled"
        )

        self._entrada_coef.config(
            state=estado
        )

    # ==============================================================
    # LECTURA Y VALIDACION
    # ==============================================================

    def _leer_parametros(self):

        try:
            m = float(self._entradas["m"].get())
            M = float(self._entradas["M"].get())
            v0 = float(self._entradas["v0"].get())
            L = float(self._entradas["L"].get())

        except ValueError:

            messagebox.showerror(
                "Entrada invalida",
                "m, M, v0 y L deben ser numeros validos."
            )

            return None

        if m <= 0:

            messagebox.showerror(
                "Entrada invalida",
                "La masa del proyectil m debe ser mayor que cero."
            )

            return None

        if M < 0:

            messagebox.showerror(
                "Entrada invalida",
                "La masa de la caja M no puede ser negativa."
            )

            return None

        if L <= 0:

            messagebox.showerror(
                "Entrada invalida",
                "La longitud de la cuerda L debe ser mayor que cero."
            )

            return None

        if v0 == 0:

            messagebox.showerror(
                "Entrada invalida",
                "La velocidad inicial v0 no puede ser cero "
                "(no habria impacto)."
            )

            return None

        es_exacto = (
            self._metodo_var.get()
            == METODOS_DISPONIBLES[1]
        )

        metodo = (
            "exacto"
            if es_exacto
            else "aproximado"
        )

        try:
            I_caja_cm = float(
                self._entradas["I_caja_cm"].get()
            )

        except ValueError:

            messagebox.showerror(
                "Entrada invalida",
                "La inercia I_caja_cm debe ser un numero valido."
            )

            return None

        if I_caja_cm < 0:

            messagebox.showerror(
                "Entrada invalida",
                "La inercia I_caja_cm no puede ser negativa."
            )

            return None

        texto_b = self._entradas["b"].get().strip()

        b = None

        if texto_b:

            try:
                b = float(texto_b)

            except ValueError:

                messagebox.showerror(
                    "Entrada invalida",
                    "El brazo de palanca b debe ser un numero "
                    "valido o dejarse vacio."
                )

                return None

            if b <= 0:

                messagebox.showerror(
                    "Entrada invalida",
                    "El brazo de palanca b debe ser mayor que cero."
                )

                return None

        amortiguar = self._amortiguar_var.get()

        coef_amortiguamiento = 0.0

        if amortiguar:

            try:
                coef_amortiguamiento = float(
                    self._entradas[
                        "coef_amortiguamiento"
                    ].get()
                )

            except ValueError:

                messagebox.showerror(
                    "Entrada invalida",
                    "El coeficiente de amortiguamiento debe "
                    "ser un numero valido."
                )

                return None

            if coef_amortiguamiento < 0:

                messagebox.showerror(
                    "Entrada invalida",
                    "El coeficiente de amortiguamiento "
                    "no puede ser negativo."
                )

                return None

        return {
            "m": m,
            "M": M,
            "v0": v0,
            "L": L,
            "metodo": metodo,
            "I_caja_cm": I_caja_cm,
            "b": b,
            "amortiguamiento": amortiguar,
            "coef_amortiguamiento": coef_amortiguamiento
        }

    # ==============================================================
    # COLISION
    # ==============================================================

    def _calcular_v1(self, parametros):

        m = parametros["m"]
        M = parametros["M"]
        v0 = parametros["v0"]
        L = parametros["L"]

        if parametros["metodo"] == "exacto":

            resumen = resumen_colision_exacto(
                m,
                M,
                v0,
                L,
                I_caja_cm=parametros["I_caja_cm"],
                b=parametros["b"]
            )

            v1 = resumen["v1_equivalente"]

        else:

            v1 = velocidad_tras_impacto(
                m,
                M,
                v0
            )

            resumen = {
                "v1_equivalente": v1,
                "energia_perdida": energia_perdida(
                    m,
                    M,
                    v0
                )
            }

        return v1, resumen

    # ==============================================================
    # SIMULACION
    # ==============================================================

    def _simular(self, parametros):

        v1, resumen = self._calcular_v1(
            parametros
        )

        datos = simular_oscilacion(
            parametros["m"],
            parametros["M"],
            parametros["L"],
            v1,
            T_MAX,
            DT,
            metodo=parametros["metodo"],
            I_caja_cm=parametros["I_caja_cm"],
            b=parametros["b"],
            amortiguamiento=parametros["amortiguamiento"],
            coef_amortiguamiento=parametros[
                "coef_amortiguamiento"
            ]
        )

        return datos, resumen

    # ==============================================================
    # INICIAR
    # ==============================================================

    def _iniciar_simulacion(self):

        parametros = self._leer_parametros()

        if parametros is None:
            return

        self._detener_animacion()
        self._panel.reiniciar()

        datos, resumen = self._simular(
            parametros
        )

        self._datos = datos
        self._indice = 0

        self._ultimos_parametros = parametros

        self._texto_resultado.set(
            "Metodo: {}\n"
            "Velocidad tras el impacto v1 = {:.4f} m/s\n"
            "Energia perdida en el choque = {:.4f} J\n"
            "Amplitud maxima = {:.4f} rad ({:.2f} grados)\n"
            "Periodo (angulos pequenos) = {:.4f} s\n"
            "Periodo exacto (integral eliptica) = {:.4f} s\n"
            "Cuadros a animar = {}".format(
                parametros["metodo"],
                resumen["v1_equivalente"],
                resumen["energia_perdida"],
                datos["theta_max"],
                math.degrees(
                    datos["theta_max"]
                ),
                datos["periodo_aproximado"],
                datos["periodo_exacto"],
                len(datos["t"])
            )
        )

        self._animando = True
        self._pausado = False

        self._boton_iniciar.config(
            state="disabled"
        )

        self._boton_pausar.config(
            state="normal",
            text="⏸  Pausar"
        )

        self._boton_reiniciar.config(
            state="normal"
        )

        self._tarea_after = self.after(
            0,
            self._siguiente_cuadro
        )

    # ==============================================================
    # CUADROS
    # ==============================================================

    def _siguiente_cuadro(self):

        if self._datos is None:
            return

        i = self._indice

        if i >= len(self._datos["t"]):

            self._animando = False
            self._tarea_after = None

            self._boton_iniciar.config(
                state="normal"
            )

            self._boton_pausar.config(
                state="disabled"
            )

            return

        datos = self._datos

        self._dibujar_pendulo(
            datos["theta"][i]
        )

        self._panel.agregar_punto(
            datos["t"][i],
            datos["theta"][i],
            datos["omega"][i],
            datos["p"][i],
            datos["ek"][i],
            x=datos["x"][i],
            y=datos["y"][i],
            v=datos["v"][i],
            ep=datos["ep"][i],
            emec=datos["emec"][i],
            tension=datos["tension"][i]
        )

        self._indice = i + 1

        self._tarea_after = self.after(
            MS_POR_CUADRO,
            self._siguiente_cuadro
        )

    # ==============================================================
    # PAUSAR / REANUDAR
    # ==============================================================

    def _alternar_pausa(self):

        if not self._animando and not self._pausado:
            return

        if self._pausado:

            self._pausado = False

            self._boton_pausar.config(
                text="⏸  Pausar"
            )

            self._tarea_after = self.after(
                MS_POR_CUADRO,
                self._siguiente_cuadro
            )

        else:

            if self._tarea_after is not None:

                self.after_cancel(
                    self._tarea_after
                )

                self._tarea_after = None

            self._pausado = True

            self._boton_pausar.config(
                text="▶  Reanudar"
            )

    # ==============================================================
    # REINICIAR
    # ==============================================================

    def _reiniciar_animacion(self):

        if self._datos is None:
            return

        self._detener_animacion()

        self._panel.reiniciar()

        self._indice = 0

        self._dibujar_pendulo(0.0)

        self._pausado = False
        self._animando = True

        self._boton_pausar.config(
            state="normal",
            text="⏸  Pausar"
        )

        self._boton_iniciar.config(
            state="disabled"
        )

        self._tarea_after = self.after(
            0,
            self._siguiente_cuadro
        )

    # ==============================================================
    # DIBUJAR PENDULO
    # ==============================================================

    def _dibujar_pendulo(self, theta):
        """
        Dibuja el pendulo manteniendo el sistema dentro del Canvas.

        La caja rota con el angulo del pendulo y se muestra el
        angulo actual en grados.
        """

        # ----------------------------------------------------------
        # Centro de la caja.
        # ----------------------------------------------------------

        caja_x = (
            PIVOTE_X
            + LARGO_CUERDA_PX
            * math.sin(theta)
        )

        caja_y = (
            PIVOTE_Y
            + LARGO_CUERDA_PX
            * math.cos(theta)
        )

        # ----------------------------------------------------------
        # Cuerda.
        # ----------------------------------------------------------

        self._canvas.coords(
            self._cuerda,
            PIVOTE_X,
            PIVOTE_Y,
            caja_x,
            caja_y
        )

        # ----------------------------------------------------------
        # Caja rotada.
        # ----------------------------------------------------------

        mitad = LADO_CAJA_PX / 2

        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        esquinas = [
            (-mitad, -mitad),
            (mitad, -mitad),
            (mitad, mitad),
            (-mitad, mitad)
        ]

        puntos = []

        for x_local, y_local in esquinas:

            x_rot = (
                x_local * cos_t
                - y_local * sin_t
            )

            y_rot = (
                x_local * sin_t
                + y_local * cos_t
            )

            puntos.extend([
                caja_x + x_rot,
                caja_y + y_rot
            ])

        self._canvas.coords(
            self._caja,
            *puntos
        )

        # ----------------------------------------------------------
        # Proyectil.
        # ----------------------------------------------------------

        radio_proyectil = 6

        self._canvas.coords(
            self._proyectil,
            caja_x - radio_proyectil,
            caja_y - radio_proyectil,
            caja_x + radio_proyectil,
            caja_y + radio_proyectil
        )

        # ----------------------------------------------------------
        # Angulo actual.
        # ----------------------------------------------------------

        angulo_grados = math.degrees(theta)

        self._canvas.itemconfig(
            self._texto_angulo_canvas,
            text="θ = {:.2f}°".format(
                angulo_grados
            )
        )

    # ==============================================================
    # DETENER
    # ==============================================================

    def _detener_animacion(self):

        if self._tarea_after is not None:

            try:

                self.after_cancel(
                    self._tarea_after
                )

            except tk.TclError:
                pass

            self._tarea_after = None

        self._animando = False
        self._pausado = False

    # ==============================================================
    # COMPARAR METODOS
    # ==============================================================

    def _comparar_metodos(self):

        parametros = self._leer_parametros()

        if parametros is None:
            return

        self._panel.graficar_comparacion_metodos(
            parametros["m"],
            parametros["M"],
            parametros["v0"],
            parametros["L"],
            I_caja_cm=parametros["I_caja_cm"]
        )

        messagebox.showinfo(
            "Comparacion de metodos",
            "Grafica generada en la pestana "
            "\"Comparacion de metodos\"."
        )

    # ==============================================================
    # COMPARAR AMORTIGUAMIENTO
    # ==============================================================

    def _comparar_amortiguamiento(self):

        parametros = self._leer_parametros()

        if parametros is None:
            return

        parametros_sin = dict(
            parametros,
            amortiguamiento=False,
            coef_amortiguamiento=0.0
        )

        parametros_con = dict(
            parametros,
            amortiguamiento=True
        )

        if parametros_con["coef_amortiguamiento"] <= 0:

            parametros_con[
                "coef_amortiguamiento"
            ] = float(
                DEFECTO_COEF_AMORTIGUAMIENTO
            )

        datos_sin, _ = self._simular(
            parametros_sin
        )

        datos_con, _ = self._simular(
            parametros_con
        )

        self._panel.comparar_simulaciones(
            datos_sin,
            "sin amortiguamiento",
            datos_con,
            "con amortiguamiento (c={:.3f})".format(
                parametros_con[
                    "coef_amortiguamiento"
                ]
            )
        )

        messagebox.showinfo(
            "Comparar simulaciones",
            "Grafica generada en la pestana "
            "\"Comparar simulaciones\"."
        )

    # ==============================================================
    # EXPORTAR PNG
    # ==============================================================

    def _exportar_png(self):

        rutas = self._panel.exportar_png(
            carpeta="reportes",
            prefijo="pendulo"
        )

        messagebox.showinfo(
            "Exportacion completada",
            "Se generaron {} imagenes "
            "en la carpeta 'reportes':\n{}".format(
                len(rutas),
                "\n".join(rutas)
            )
        )

    # ==============================================================
    # CERRAR
    # ==============================================================

    def _al_cerrar(self):

        self._detener_animacion()

        self.destroy()


# ==============================================================
# LANZAR
# ==============================================================

def lanzar():

    app = App()

    app.mainloop()