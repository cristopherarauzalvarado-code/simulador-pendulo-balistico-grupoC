# -*- coding: utf-8 -*-
"""
Modulo: interfaz.py
Responsable: Tatiana Solis

Que modela:
    La interfaz grafica (GUI) del simulador construida con Tkinter. Reune todos
    los modulos del proyecto:

        - Campos de entrada para los parametros: m, M, v0, L (y, para el
          metodo exacto, I_caja_cm y b).
        - Selector de metodo: aproximado (masa puntual) o exacto (pendulo
          fisico con inercia rotacional e impacto no central).
        - Casilla de amortiguamiento viscoso, con su coeficiente.
        - Boton "Iniciar simulacion" y controles "Pausar/Reanudar" y
          "Reiniciar" para la animacion.
        - Un Canvas que anima el pendulo (la cuerda y la caja) cuadro a cuadro.
        - Un panel numerico con v1, energia perdida, amplitud y periodo.
        - El PanelGraficas (modulo graficas) con las graficas en tiempo real,
          mas botones para comparar metodos, comparar simulaciones (con/sin
          amortiguamiento) y exportar todo a PNG.

    Flujo de datos que conecta los modulos:
        - Metodo aproximado:
            colision.velocidad_tras_impacto(m, M, v0) -> v1
        - Metodo exacto:
            colision.resumen_colision_exacto(m, M, v0, L, I_caja_cm, b)
                -> v1_equivalente = omega1 * L
        En ambos casos:
            oscilacion.simular_oscilacion(m, M, L, v1, t_max, dt, metodo=...,
                I_caja_cm=..., b=..., amortiguamiento=..., coef_amortiguamiento=...)
                -> datos
            graficas.PanelGraficas.agregar_punto(...) por cada cuadro

    La animacion usa el metodo after() de Tkinter (no bloqueante).

Estado:
    Implementado: metodo aproximado y exacto, amortiguamiento, controles de
    pausar/reanudar/reiniciar, panel numerico ampliado (v1, energia perdida,
    amplitud, periodo aproximado y exacto) y validaciones de entrada. La
    ventana es redimensionable y su tamano inicial se calcula a partir del
    ancho/alto real que piden los widgets (winfo_reqwidth/reqheight) mas un
    margen, para que el panel de graficas (Notebook + figuras de Matplotlib)
    no quede recortado contra el borde derecho como ocurria con un tamano
    fijo calculado de antemano.

Contrato (no cambiar las firmas):
    App(tk.Tk)
    lanzar()

TODO (baseline):
    - [x] Construir los campos de entrada (m, M, v0, L) y el boton de inicio.
    - [x] Crear el Canvas de animacion del pendulo.
    - [x] Incrustar el PanelGraficas y conectar colision -> oscilacion -> panel.
    - [x] Animar con after() llamando a agregar_punto por cuadro.
TODO (Informe Final):
    - [x] Controles para pausar, reanudar y reiniciar la animacion.
    - [x] Selector de metodo: aproximado vs exacto (con inercia).
    - [x] Casilla para activar/desactivar el amortiguamiento.
    - [x] Panel numerico con v1, energia perdida en la colision y periodo
          estimado.
    - [x] Agregar validaciones de los parametros de entrada (m, M, v0, L).
"""

import math
import tkinter as tk
from tkinter import messagebox, ttk

from src.colision import (energia_perdida, resumen_colision_exacto,
                           velocidad_tras_impacto)
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
DEFECTO_I_CAJA_CM = "0.0"
DEFECTO_COEF_AMORTIGUAMIENTO = "0.15"

METODOS_DISPONIBLES = ("Aproximado (masa puntual)", "Exacto (inercia rotacional)")


class App(tk.Tk):
    """
    Ventana principal del simulador del pendulo balistico.

    Estructura la ventana en dos zonas:
        - Panel izquierdo: campos de entrada, selector de metodo,
          amortiguamiento, botones de control, resultados numericos y el
          Canvas con la animacion del pendulo.
        - Panel derecho: el PanelGraficas con las graficas en tiempo real y
          las graficas estaticas del Informe Final.

    La animacion se realiza con after() (no bloqueante): en cada cuadro se
    reposiciona el pendulo en el Canvas y se agrega el punto correspondiente al
    panel de graficas.
    """

    def __init__(self):
        super().__init__()
        self.title("Simulador de Pendulo Balistico - Fisica I - Grupo C")

        # La ventana SI se puede redimensionar (a diferencia del baseline):
        # el panel de graficas (Notebook + figuras de Matplotlib) necesita
        # espacio variable segun la pestana y el sistema operativo, y con un
        # tamano fijo calculado de antemano algunas graficas quedaban
        # recortadas contra el borde derecho. Solo la columna de graficas
        # (columna 1) y la fila de la animacion (fila 1) crecen al agrandar
        # la ventana; los controles de la izquierda mantienen su ancho natural.
        self.resizable(True, True)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Estado de la animacion en curso.
        self._datos = None          # dict devuelto por simular_oscilacion
        self._datos_sin_amortiguar = None  # corrida gemela sin amortiguar (para comparar)
        self._indice = 0            # indice del cuadro actual
        self._tarea_after = None    # id del after() programado (para cancelar)
        self._animando = False      # bandera de animacion activa
        self._pausado = False       # bandera de pausa (distinta de detenida)
        self._ultimos_parametros = None  # (m, M, v0, L) de la ultima corrida

        # Diccionario de variables de los campos de entrada.
        self._entradas = {}

        self._construir_controles()
        self._construir_animacion()
        self._construir_panel_graficas()

        # Tamano inicial: se calcula a partir de lo que Tk reporta que
        # necesitan los widgets ya construidos (winfo_reqwidth/reqheight),
        # con un margen de seguridad extra para que el borde de las figuras
        # de Matplotlib y las pestanas del Notebook nunca queden recortados
        # contra el borde de la ventana. Como la ventana es redimensionable,
        # esto es solo el punto de partida: el usuario puede agrandarla o
        # maximizarla si su pantalla es mas chica.
        self.update_idletasks()
        ancho_inicial = self.winfo_reqwidth() + 40
        alto_inicial = self.winfo_reqheight() + 30
        self.geometry("{}x{}".format(ancho_inicial, alto_inicial))
        self.minsize(min(ancho_inicial, 1000), min(alto_inicial, 650))

        # Cierre ordenado: cancela cualquier after() pendiente.
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------
    def _construir_controles(self):
        """Crea los campos de entrada, el selector de metodo, el amortiguamiento,
        los botones y el panel de resultados."""
        marco = ttk.LabelFrame(self, text="Parametros de la simulacion")
        marco.grid(row=0, column=0, padx=10, pady=10, sticky="new")

        # Etiqueta descriptiva, clave interna y unidad de cada campo basico.
        campos = [
            ("Masa del proyectil m", "m", "kg"),
            ("Masa de la caja M", "M", "kg"),
            ("Velocidad inicial v0", "v0", "m/s"),
            ("Longitud de la cuerda L", "L", "m"),
        ]

        fila = 0
        for etiqueta, clave, unidad in campos:
            ttk.Label(marco, text=etiqueta + ":").grid(
                row=fila, column=0, sticky="w", padx=6, pady=4)
            variable = tk.StringVar(value=VALORES_POR_DEFECTO[clave])
            self._entradas[clave] = variable
            ttk.Entry(marco, textvariable=variable, width=10).grid(
                row=fila, column=1, padx=6, pady=4)
            ttk.Label(marco, text=unidad).grid(
                row=fila, column=2, sticky="w", padx=(0, 6))
            fila += 1

        # Selector de metodo: aproximado (baseline) o exacto (inercia).
        ttk.Label(marco, text="Metodo:").grid(
            row=fila, column=0, sticky="w", padx=6, pady=(10, 4))
        self._metodo_var = tk.StringVar(value=METODOS_DISPONIBLES[0])
        combo_metodo = ttk.Combobox(
            marco, textvariable=self._metodo_var, values=METODOS_DISPONIBLES,
            state="readonly", width=24)
        combo_metodo.grid(row=fila, column=1, columnspan=2, sticky="w", padx=6, pady=(10, 4))
        combo_metodo.bind("<<ComboboxSelected>>", self._al_cambiar_metodo)
        fila += 1

        # Parametros del metodo exacto (inercia de la caja y brazo de palanca
        # del impacto). Se muestran siempre pero solo se usan si el metodo
        # seleccionado es "exacto"; con sus valores por defecto (I=0, b=L) el
        # metodo exacto coincide con el aproximado.
        self._marco_exacto = ttk.Frame(marco)
        self._marco_exacto.grid(row=fila, column=0, columnspan=3, sticky="w")

        ttk.Label(self._marco_exacto, text="Inercia de la caja I_cm:").grid(
            row=0, column=0, sticky="w", padx=6, pady=2)
        self._entradas["I_caja_cm"] = tk.StringVar(value=DEFECTO_I_CAJA_CM)
        ttk.Entry(self._marco_exacto, textvariable=self._entradas["I_caja_cm"], width=8).grid(
            row=0, column=1, padx=6, pady=2)
        ttk.Label(self._marco_exacto, text="kg*m^2").grid(row=0, column=2, sticky="w")

        ttk.Label(self._marco_exacto, text="Brazo de palanca b:").grid(
            row=1, column=0, sticky="w", padx=6, pady=2)
        self._entradas["b"] = tk.StringVar(value="")
        ttk.Entry(self._marco_exacto, textvariable=self._entradas["b"], width=8).grid(
            row=1, column=1, padx=6, pady=2)
        ttk.Label(self._marco_exacto, text="m (vacio = L, impacto central)").grid(
            row=1, column=2, sticky="w")
        fila += 1
        self._al_cambiar_metodo()

        # Amortiguamiento viscoso.
        self._amortiguar_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            marco, text="Amortiguamiento viscoso", variable=self._amortiguar_var,
            command=self._al_cambiar_amortiguamiento).grid(
                row=fila, column=0, columnspan=2, sticky="w", padx=6, pady=(6, 2))
        self._entradas["coef_amortiguamiento"] = tk.StringVar(
            value=DEFECTO_COEF_AMORTIGUAMIENTO)
        self._entrada_coef = ttk.Entry(
            marco, textvariable=self._entradas["coef_amortiguamiento"], width=8,
            state="disabled")
        self._entrada_coef.grid(row=fila, column=2, padx=6, pady=(6, 2))
        fila += 1

        # Botones de control de la simulacion y la animacion.
        marco_botones = ttk.Frame(marco)
        marco_botones.grid(row=fila, column=0, columnspan=3, pady=(8, 6))
        self._boton_iniciar = ttk.Button(
            marco_botones, text="Iniciar simulacion", command=self._iniciar_simulacion)
        self._boton_iniciar.grid(row=0, column=0, padx=3)
        self._boton_pausar = ttk.Button(
            marco_botones, text="Pausar", command=self._alternar_pausa, state="disabled")
        self._boton_pausar.grid(row=0, column=1, padx=3)
        self._boton_reiniciar = ttk.Button(
            marco_botones, text="Reiniciar", command=self._reiniciar_animacion, state="disabled")
        self._boton_reiniciar.grid(row=0, column=2, padx=3)
        fila += 1

        # Botones de las graficas estaticas del Informe Final.
        marco_extra = ttk.Frame(marco)
        marco_extra.grid(row=fila, column=0, columnspan=3, pady=(0, 6))
        ttk.Button(
            marco_extra, text="Comparar metodos", command=self._comparar_metodos
        ).grid(row=0, column=0, padx=3, pady=2)
        ttk.Button(
            marco_extra, text="Comparar con/sin amortiguamiento",
            command=self._comparar_amortiguamiento
        ).grid(row=0, column=1, padx=3, pady=2)
        ttk.Button(
            marco_extra, text="Exportar graficas a PNG", command=self._exportar_png
        ).grid(row=1, column=0, columnspan=2, padx=3, pady=2)
        fila += 1

        # Panel de resultados numericos (v1, energia perdida, amplitud, periodo).
        self._texto_resultado = tk.StringVar(
            value="Ingrese los parametros y presione Iniciar simulacion.")
        ttk.Label(
            marco, textvariable=self._texto_resultado, wraplength=280,
            justify="left", foreground="#333333").grid(
                row=fila, column=0, columnspan=3,
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
        marco = ttk.LabelFrame(self, text="Graficas")
        marco.grid(row=0, column=1, rowspan=2, padx=(0, 10), pady=10,
                   sticky="nsew")

        self._panel = PanelGraficas(marco)
        self._panel.widget.pack(fill="both", expand=True, padx=4, pady=4)

    # ------------------------------------------------------------------
    # Reacciones a los controles
    # ------------------------------------------------------------------
    def _al_cambiar_metodo(self, _evento=None):
        """Habilita/deshabilita los campos del metodo exacto segun el selector."""
        es_exacto = self._metodo_var.get() == METODOS_DISPONIBLES[1]
        estado = "normal" if es_exacto else "disabled"
        for hijo in self._marco_exacto.winfo_children():
            if isinstance(hijo, ttk.Entry):
                hijo.config(state=estado)

    def _al_cambiar_amortiguamiento(self):
        """Habilita/deshabilita el campo del coeficiente de amortiguamiento."""
        estado = "normal" if self._amortiguar_var.get() else "disabled"
        self._entrada_coef.config(state=estado)

    # ------------------------------------------------------------------
    # Lectura y validacion de parametros
    # ------------------------------------------------------------------
    def _leer_parametros(self):
        """
        Lee y valida todos los campos de entrada (basicos, metodo exacto y
        amortiguamiento).

        Retorna un dict con m, M, v0, L, metodo, I_caja_cm, b,
        amortiguamiento, coef_amortiguamiento; o None si alguna entrada es
        invalida (en ese caso muestra un mensaje al usuario).
        """
        try:
            m = float(self._entradas["m"].get())
            M = float(self._entradas["M"].get())
            v0 = float(self._entradas["v0"].get())
            L = float(self._entradas["L"].get())
        except ValueError:
            messagebox.showerror(
                "Entrada invalida",
                "m, M, v0 y L deben ser numeros validos.")
            return None

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
        if v0 == 0:
            messagebox.showerror(
                "Entrada invalida",
                "La velocidad inicial v0 no puede ser cero (no habria impacto).")
            return None

        es_exacto = self._metodo_var.get() == METODOS_DISPONIBLES[1]
        metodo = "exacto" if es_exacto else "aproximado"

        try:
            I_caja_cm = float(self._entradas["I_caja_cm"].get())
        except ValueError:
            messagebox.showerror(
                "Entrada invalida", "La inercia I_caja_cm debe ser un numero valido.")
            return None
        if I_caja_cm < 0:
            messagebox.showerror(
                "Entrada invalida", "La inercia I_caja_cm no puede ser negativa.")
            return None

        texto_b = self._entradas["b"].get().strip()
        b = None
        if texto_b:
            try:
                b = float(texto_b)
            except ValueError:
                messagebox.showerror(
                    "Entrada invalida",
                    "El brazo de palanca b debe ser un numero valido o dejarse vacio.")
                return None
            if b <= 0:
                messagebox.showerror(
                    "Entrada invalida", "El brazo de palanca b debe ser mayor que cero.")
                return None

        amortiguar = self._amortiguar_var.get()
        coef_amortiguamiento = 0.0
        if amortiguar:
            try:
                coef_amortiguamiento = float(self._entradas["coef_amortiguamiento"].get())
            except ValueError:
                messagebox.showerror(
                    "Entrada invalida",
                    "El coeficiente de amortiguamiento debe ser un numero valido.")
                return None
            if coef_amortiguamiento < 0:
                messagebox.showerror(
                    "Entrada invalida",
                    "El coeficiente de amortiguamiento no puede ser negativo.")
                return None

        return {
            "m": m, "M": M, "v0": v0, "L": L,
            "metodo": metodo, "I_caja_cm": I_caja_cm, "b": b,
            "amortiguamiento": amortiguar,
            "coef_amortiguamiento": coef_amortiguamiento,
        }

    # ------------------------------------------------------------------
    # Logica de la simulacion y la animacion
    # ------------------------------------------------------------------
    def _calcular_v1(self, parametros):
        """
        Calcula v1 (o v1_equivalente) y un resumen de la colision segun el
        metodo elegido. Retorna (v1, resumen_dict).
        """
        m, M, v0, L = parametros["m"], parametros["M"], parametros["v0"], parametros["L"]
        if parametros["metodo"] == "exacto":
            resumen = resumen_colision_exacto(
                m, M, v0, L, I_caja_cm=parametros["I_caja_cm"], b=parametros["b"])
            v1 = resumen["v1_equivalente"]
        else:
            v1 = velocidad_tras_impacto(m, M, v0)
            resumen = {
                "v1_equivalente": v1,
                "energia_perdida": energia_perdida(m, M, v0),
            }
        return v1, resumen

    def _simular(self, parametros):
        """Ejecuta simular_oscilacion con los parametros ya validados."""
        v1, resumen = self._calcular_v1(parametros)
        datos = simular_oscilacion(
            parametros["m"], parametros["M"], parametros["L"], v1, T_MAX, DT,
            metodo=parametros["metodo"], I_caja_cm=parametros["I_caja_cm"],
            b=parametros["b"], amortiguamiento=parametros["amortiguamiento"],
            coef_amortiguamiento=parametros["coef_amortiguamiento"])
        return datos, resumen

    def _iniciar_simulacion(self):
        """Calcula la simulacion completa y arranca la animacion cuadro a cuadro."""
        parametros = self._leer_parametros()
        if parametros is None:
            return

        # Detiene cualquier animacion previa y limpia el panel de graficas.
        self._detener_animacion()
        self._panel.reiniciar()

        datos, resumen = self._simular(parametros)
        self._datos = datos
        self._indice = 0
        self._ultimos_parametros = parametros

        # Muestra los resultados numericos del choque y de la oscilacion.
        self._texto_resultado.set(
            "Metodo: {}\n"
            "Velocidad tras el impacto v1 = {:.4f} m/s\n"
            "Energia perdida en el choque = {:.4f} J\n"
            "Amplitud maxima = {:.4f} rad ({:.2f} grados)\n"
            "Periodo (angulos pequenos) = {:.4f} s\n"
            "Periodo exacto (integral eliptica) = {:.4f} s\n"
            "Cuadros a animar = {}".format(
                parametros["metodo"], resumen["v1_equivalente"],
                resumen["energia_perdida"], datos["theta_max"],
                math.degrees(datos["theta_max"]),
                datos["periodo_aproximado"], datos["periodo_exacto"],
                len(datos["t"])))

        # Arranca la animacion no bloqueante.
        self._animando = True
        self._pausado = False
        self._boton_iniciar.config(state="disabled")
        self._boton_pausar.config(state="normal", text="Pausar")
        self._boton_reiniciar.config(state="normal")
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
            self._boton_pausar.config(state="disabled")
            return

        datos = self._datos

        # Reposiciona el pendulo en el Canvas segun el angulo actual.
        self._dibujar_pendulo(datos["theta"][i])

        # Agrega el punto a las graficas basicas y a las de energia/dinamica.
        self._panel.agregar_punto(
            datos["t"][i], datos["theta"][i], datos["omega"][i],
            datos["p"][i], datos["ek"][i], x=datos["x"][i], y=datos["y"][i],
            v=datos["v"][i], ep=datos["ep"][i], emec=datos["emec"][i],
            tension=datos["tension"][i])

        # Avanza al siguiente cuadro y reprograma.
        self._indice = i + 1
        self._tarea_after = self.after(MS_POR_CUADRO, self._siguiente_cuadro)

    def _alternar_pausa(self):
        """Pausa la animacion en curso o la reanuda desde donde quedo."""
        if not self._animando and not self._pausado:
            return
        if self._pausado:
            # Reanudar.
            self._pausado = False
            self._boton_pausar.config(text="Pausar")
            self._tarea_after = self.after(MS_POR_CUADRO, self._siguiente_cuadro)
        else:
            # Pausar: cancela el after() pendiente pero conserva el indice.
            if self._tarea_after is not None:
                self.after_cancel(self._tarea_after)
                self._tarea_after = None
            self._pausado = True
            self._boton_pausar.config(text="Reanudar")

    def _reiniciar_animacion(self):
        """
        Reinicia la animacion actual desde t=0 usando los mismos datos ya
        calculados (sin volver a resolver la colision ni la oscilacion),
        dejando el pendulo y las graficas en su estado inicial.
        """
        if self._datos is None:
            return
        self._detener_animacion()
        self._panel.reiniciar()
        self._indice = 0
        self._dibujar_pendulo(0.0)
        self._pausado = False
        self._boton_pausar.config(state="normal", text="Pausar")
        self._boton_iniciar.config(state="disabled")
        self._animando = True
        self._tarea_after = self.after(0, self._siguiente_cuadro)

    def _dibujar_pendulo(self, theta):
        """
        Reposiciona la cuerda y la caja en el Canvas para el angulo dado.

        Parametros:
            theta : angulo respecto a la vertical (rad). theta = 0 es la posicion
                    de reposo (cuerda vertical hacia abajo).
        """
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
        self._pausado = False

    # ------------------------------------------------------------------
    # Graficas estaticas del Informe Final
    # ------------------------------------------------------------------
    def _comparar_metodos(self):
        """Genera la grafica 9 (metodo exacto vs aproximado) en el panel."""
        parametros = self._leer_parametros()
        if parametros is None:
            return
        self._panel.graficar_comparacion_metodos(
            parametros["m"], parametros["M"], parametros["v0"], parametros["L"],
            I_caja_cm=parametros["I_caja_cm"])
        messagebox.showinfo(
            "Comparacion de metodos",
            "Grafica generada en la pestana \"Comparacion de metodos\".")

    def _comparar_amortiguamiento(self):
        """
        Corre dos simulaciones con los parametros actuales (una sin
        amortiguamiento y otra con el coeficiente indicado) y las superpone
        en la pestana "Comparar simulaciones".
        """
        parametros = self._leer_parametros()
        if parametros is None:
            return

        parametros_sin = dict(parametros, amortiguamiento=False, coef_amortiguamiento=0.0)
        parametros_con = dict(parametros, amortiguamiento=True)
        if parametros_con["coef_amortiguamiento"] <= 0:
            parametros_con["coef_amortiguamiento"] = float(DEFECTO_COEF_AMORTIGUAMIENTO)

        datos_sin, _ = self._simular(parametros_sin)
        datos_con, _ = self._simular(parametros_con)

        self._panel.comparar_simulaciones(
            datos_sin, "sin amortiguamiento", datos_con,
            "con amortiguamiento (c={:.3f})".format(parametros_con["coef_amortiguamiento"]))
        messagebox.showinfo(
            "Comparar simulaciones",
            "Grafica generada en la pestana \"Comparar simulaciones\".")

    def _exportar_png(self):
        """Exporta todas las figuras del panel a PNG (carpeta 'reportes')."""
        rutas = self._panel.exportar_png(carpeta="reportes", prefijo="pendulo")
        messagebox.showinfo(
            "Exportacion completada",
            "Se generaron {} imagenes en la carpeta 'reportes':\n{}".format(
                len(rutas), "\n".join(rutas)))

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
