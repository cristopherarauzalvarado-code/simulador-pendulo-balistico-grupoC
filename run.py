# -*- coding: utf-8 -*-
"""
Archivo: run.py
Proyecto: pendulo-balistico-sim (Fisica I - CENFOTEC - Grupo C)

Que hace:
    Punto de arranque de UN SOLO COMANDO para el profesor:

        python run.py

    Verifica que las dependencias (numpy, scipy, matplotlib) esten instaladas;
    si falta alguna, la instala automaticamente con pip leyendo requirements.txt.
    Luego lanza la interfaz grafica del simulador. No se requieren pasos manuales
    de instalacion.

Requisitos:
    - Python 3.10 o superior.
    - Tkinter (incluido en la libreria estandar de Python).

Estado:
    Baseline funcional.

TODO (Informe Final):
    - [ ] Permitir crear un entorno virtual automaticamente (opcional).
    - [ ] Detectar y avisar si Tkinter no esta disponible en el sistema.
"""

import importlib
import importlib.util
import os
import subprocess
import sys

# Mapa: nombre del paquete pip -> nombre del modulo a importar.
DEPENDENCIAS = {
    "numpy": "numpy",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
}

RAIZ = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(RAIZ, "requirements.txt")


def _verificar_version_python():
    """Avisa si la version de Python es inferior a la recomendada (3.10)."""
    if sys.version_info < (3, 10):
        print("ADVERTENCIA: se recomienda Python 3.10 o superior. "
              "Version actual: {}.{}.{}".format(
                  sys.version_info.major, sys.version_info.minor,
                  sys.version_info.micro))


def _faltan_dependencias():
    """Devuelve la lista de paquetes pip que no estan instalados."""
    faltantes = []
    for paquete, modulo in DEPENDENCIAS.items():
        if importlib.util.find_spec(modulo) is None:
            faltantes.append(paquete)
    return faltantes


def _instalar_dependencias():
    """Instala las dependencias con pip usando requirements.txt."""
    print("Instalando dependencias (numpy, scipy, matplotlib)...")
    print("Esto puede tardar un par de minutos la primera vez.")
    if os.path.exists(REQUIREMENTS):
        comando = [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS]
    else:
        # Respaldo por si no se encuentra requirements.txt.
        comando = [sys.executable, "-m", "pip", "install"] + list(DEPENDENCIAS)
    try:
        subprocess.check_call(comando)
    except subprocess.CalledProcessError as error:
        print("ERROR: no se pudieron instalar las dependencias.")
        print("Intente manualmente: pip install -r requirements.txt")
        print("Detalle: {}".format(error))
        sys.exit(1)


def _asegurar_dependencias():
    """Verifica e instala las dependencias que falten."""
    faltantes = _faltan_dependencias()
    if faltantes:
        print("Faltan dependencias: {}".format(", ".join(faltantes)))
        _instalar_dependencias()
        # Reverificar tras la instalacion.
        if _faltan_dependencias():
            print("ERROR: aun faltan dependencias tras la instalacion.")
            sys.exit(1)
    else:
        print("Dependencias verificadas: numpy, scipy, matplotlib.")


def main():
    """Prepara el entorno y lanza el simulador."""
    print("=" * 60)
    print("  Simulador de Pendulo Balistico - Fisica I - Grupo C")
    print("=" * 60)

    _verificar_version_python()

    # Asegurar que la raiz del proyecto este en sys.path para poder importar
    # el paquete 'src' al ejecutar 'python run.py'.
    if RAIZ not in sys.path:
        sys.path.insert(0, RAIZ)

    _asegurar_dependencias()

    print("Lanzando la interfaz grafica...")
    from src.main import iniciar
    iniciar()


if __name__ == "__main__":
    main()
