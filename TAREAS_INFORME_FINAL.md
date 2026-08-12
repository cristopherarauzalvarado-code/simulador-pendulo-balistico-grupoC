# Tareas pendientes para el Informe Final

Este documento asigna a cada integrante el trabajo de codigo que falta para
completar el Informe Final, segun los TODO marcados en cada modulo y los
entregables descritos en el Avance 1. Cada quien trabaja unicamente sobre su
modulo, respetando las firmas del contrato definidas en `CLAUDE.md`.

**Estado: todas las tareas de codigo listadas abajo estan implementadas.**
Quedan solo las tareas de integracion (validacion con el grupo y redaccion
del informe), que no son de codigo.

## Cristopher Arauz - `src/colision.py`

- [x] Implementar el metodo exacto: incorporar la inercia rotacional del
      pendulo fisico (caja con dimensiones) en el calculo de la colision, en
      lugar de tratarla como masa puntual.
- [x] Modelar el impacto no central: usar conservacion del momento angular
      respecto al pivote cuando el proyectil no impacta en el centro de masa.
- [x] Agregar el coeficiente de restitucion para soportar choques
      parcialmente elasticos (e entre 0 y 1), ademas del caso perfectamente
      inelastico actual.
- [x] Conectar `velocidad_angular_tras_impacto_exacto` con `oscilacion.py` y
      con el selector de metodo de la interfaz: la interfaz calcula
      `v1_equivalente = omega1 * L` con `resumen_colision_exacto` y lo pasa a
      `simular_oscilacion(..., metodo="exacto", I_caja_cm=..., b=...)`.

## Sidney Rodriguez - `src/oscilacion.py`

- [x] Implementar el metodo exacto de oscilacion: pendulo fisico con
      momento de inercia (en vez de masa puntual), coordinado con el metodo
      exacto de `colision.py` (parametro `metodo="exacto"`, con `I_caja_cm`
      y `b`; se reduce algebraicamente al baseline cuando `I_caja_cm=0` y
      `b=L`).
- [x] Agregar amortiguamiento viscoso al modelo (termino proporcional a
      omega en la ecuacion diferencial; parametros `amortiguamiento` y
      `coef_amortiguamiento`).
- [x] Calcular el periodo real mediante integral eliptica (`periodo_pendulo`,
      con `scipy.special.ellipk`) y compararlo con la aproximacion de
      angulos pequenos.
- [x] Generar los datos adicionales que requieren las graficas 5-9 (posicion
      del centro de masa x(t)/y(t), velocidad lineal v(t), energia potencial
      Ep(t), energia mecanica total Emec(t), tension T(t), aceleracion
      angular alpha(t)).

## Maciel Gomez - `src/graficas.py`

- [x] Agregar la grafica 5: x(t), y(t) - posicion del centro de masa.
- [x] Agregar la grafica 6: v(t) - velocidad lineal.
- [x] Agregar la grafica 7: Ek(t), Ep(t), Emec(t) en conjunto.
- [x] Agregar la grafica 8: T(t) - tension de la cuerda.
- [x] Agregar la grafica 9: comparacion de v1 (metodo exacto vs
      aproximado) segun la posicion relativa del impacto b/L.
- [x] Implementar exportacion de las graficas a PNG para el informe
      (`PanelGraficas.exportar_png` y `generar_figuras_estaticas` para el
      modo sin GUI).
- [x] Soportar comparar dos simulaciones superpuestas (por ejemplo,
      con friccion/amortiguamiento vs sin el): `comparar_simulaciones`.
- [x] Optimizar el redibujado con blitting (pestanas en tiempo real).

## Tatiana Solis - `src/interfaz.py`

- [x] Agregar controles para pausar, reanudar y reiniciar la animacion.
- [x] Agregar un selector de metodo (aproximado vs exacto con inercia).
- [x] Agregar una casilla para activar/desactivar el amortiguamiento.
- [x] Agregar un panel numerico con v1, energia perdida en la colision y
      periodo estimado (aproximado y exacto por integral eliptica).
- [x] Agregar validaciones de los parametros de entrada (m, M, v0, L, y los
      del metodo exacto/amortiguamiento).

## Tarea compartida - `src/main.py`

- [x] Soportar argumentos de linea de comandos para ejecutar una simulacion
      sin GUI y exportar las graficas a PNG (`python -m src.main --sin-gui
      ...`).

## Tareas de integracion (todo el grupo, una vez cerrado lo anterior)

- [ ] Validar resultados con distintos parametros de entrada (semana 11 del
      cronograma).
- [ ] Corregir errores detectados durante la validacion (semana 12).
- [ ] Refinar la interfaz y redactar el Informe Final (semana 13).
