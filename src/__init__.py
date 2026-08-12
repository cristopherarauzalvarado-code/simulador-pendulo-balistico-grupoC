# -*- coding: utf-8 -*-
"""
Paquete: src
Proyecto: pendulo-balistico-sim
Curso: Fisica I - CENFOTEC - Grupo C

Descripcion:
    Paquete que agrupa los modulos del simulador del pendulo balistico.
    Cada modulo tiene un unico responsable y respeta el contrato de firmas
    descrito en CLAUDE.md.

Modulos y estado:
    colision    -> Cristopher Arauz   (IMPLEMENTADO)
    oscilacion  -> Sidney Rodriguez   (IMPLEMENTADO)
    graficas    -> Maciel Gomez       (IMPLEMENTADO)
    interfaz    -> Tatiana Solis      (IMPLEMENTADO)
    main        -> punto de arranque de la GUI (andamiaje)

Nota: cada integrante desarrolla su propio modulo respetando el contrato de
firmas descrito en CLAUDE.md. No modificar el codigo de otros responsables.
"""

__all__ = ["colision", "oscilacion", "graficas", "interfaz", "main"]

# Constante fisica compartida por los modulos (gravedad estandar, m/s^2).
GRAVEDAD = 9.81
