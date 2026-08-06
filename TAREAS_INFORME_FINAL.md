# Tareas pendientes para el Informe Final

Este documento asigna a cada integrante el trabajo de codigo que falta para
completar el Informe Final, segun los TODO marcados en cada modulo y los
entregables descritos en el Avance 1. Cada quien trabaja unicamente sobre su
modulo, respetando las firmas del contrato definidas en `CLAUDE.md`.

## Cristopher Arauz - `src/colision.py`

- [ ] Implementar el metodo exacto: incorporar la inercia rotacional del
      pendulo fisico (caja con dimensiones) en el calculo de la colision, en
      lugar de tratarla como masa puntual.
- [ ] Modelar el impacto no central: usar conservacion del momento angular
      respecto al pivote cuando el proyectil no impacta en el centro de masa.
- [ ] Agregar el coeficiente de restitucion para soportar choques
      parcialmente elasticos (e entre 0 y 1), ademas del caso perfectamente
      inelastico actual.

## Sidney Rodriguez - `src/oscilacion.py`

- [ ] Implementar el metodo exacto de oscilacion: pendulo fisico con
      momento de inercia (en vez de masa puntual), coordinado con el metodo
      exacto de `colision.py`.
- [ ] Agregar amortiguamiento viscoso al modelo (termino proporcional a
      omega en la ecuacion diferencial).
- [ ] Calcular el periodo real mediante integral eliptica y compararlo con
      la aproximacion de angulos pequenos.
- [ ] Generar los datos adicionales que requieren las graficas 5-9 (posicion
      del centro de masa x(t)/y(t), velocidad lineal v(t), energia potencial
      Ep(t), energia mecanica total Emec(t), tension T(t)).

## Maciel Gomez - `src/graficas.py`

- [ ] Agregar la grafica 5: x(t), y(t) - posicion del centro de masa.
- [ ] Agregar la grafica 6: v(t) - velocidad lineal.
- [ ] Agregar la grafica 7: Ek(t), Ep(t), Emec(t) en conjunto.
- [ ] Agregar la grafica 8: T(t) - tension de la cuerda.
- [ ] Agregar la grafica 9: comparacion de v0 (metodo exacto vs
      aproximado) en funcion del angulo theta.
- [ ] Implementar exportacion de las graficas a PNG para el informe.
- [ ] Soportar comparar dos simulaciones superpuestas (por ejemplo,
      con friccion/amortiguamiento vs sin el).
- [ ] Optimizar el redibujado con blitting.

## Tatiana Solis - `src/interfaz.py`

- [ ] Agregar controles para pausar, reanudar y reiniciar la animacion.
- [ ] Agregar un selector de metodo (aproximado vs exacto con inercia).
- [ ] Agregar una casilla para activar/desactivar el amortiguamiento.
- [ ] Agregar un panel numerico con v1, energia perdida en la colision y
      periodo estimado.
- [ ] Agregar validaciones de los parametros de entrada (m, M, v0, L).

## Tarea compartida - `src/main.py`

- [ ] Soportar argumentos de linea de comandos para ejecutar una simulacion
      sin GUI y exportar las graficas a PNG (depende de la exportacion PNG
      de Maciel).

## Tareas de integracion (todo el grupo, una vez cerrado lo anterior)

- [ ] Validar resultados con distintos parametros de entrada (semana 11 del
      cronograma).
- [ ] Corregir errores detectados durante la validacion (semana 12).
- [ ] Refinar la interfaz y redactar el Informe Final (semana 13).
