#!/bin/bash
# ---------------------------------------------------------------------------
# abrir_simulador.command
# Proyecto: pendulo-balistico-sim (Fisica I - CENFOTEC - Grupo C)
#
# Que hace (para macOS):
#   Lanzador de UN SOLO CLIC. Doble clic en Finder y hace todo solo:
#     1. Verifica/instala un Python con Tk moderno (soluciona la ventana en
#        blanco del Python del sistema en macOS).
#     2. Crea el entorno virtual (.venv) si no existe.
#     3. Instala numpy, scipy y matplotlib si faltan.
#     4. Abre el simulador.
#
#   Es idempotente: la primera vez instala todo; las siguientes solo abre la
#   ventana en segundos.
# ---------------------------------------------------------------------------

set -e

# Ir a la carpeta donde vive este script (funciona con doble clic).
cd "$(dirname "$0")"

echo "============================================================"
echo "  Simulador de Pendulo Balistico - Fisica I - Grupo C"
echo "============================================================"

# --- 1. Localizar Homebrew --------------------------------------------------
if [ -x /opt/homebrew/bin/brew ]; then
    BREW=/opt/homebrew/bin/brew          # Mac con chip Apple (M1/M2/M3...)
elif [ -x /usr/local/bin/brew ]; then
    BREW=/usr/local/bin/brew             # Mac con chip Intel
else
    echo ""
    echo "ERROR: No se encontro Homebrew (necesario una sola vez)."
    echo "Instalalo pegando esto en la Terminal y volve a intentar:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo ""
    read -n 1 -s -r -p "Presiona una tecla para cerrar..."
    exit 1
fi

# --- 2. Asegurar Python 3.13 con Tk moderno --------------------------------
PY="$("$BREW" --prefix)/opt/python@3.13/bin/python3.13"

if [ ! -x "$PY" ]; then
    echo "Instalando Python 3.13 + Tk (solo la primera vez, puede tardar)..."
    "$BREW" install python-tk@3.13
fi

# --- 3. Crear el entorno virtual si no existe ------------------------------
if [ ! -x ".venv/bin/python" ]; then
    echo "Creando entorno virtual (.venv)..."
    "$PY" -m venv .venv
fi

# --- 4. Instalar dependencias si faltan ------------------------------------
if ! .venv/bin/python -c "import numpy, scipy, matplotlib" 2>/dev/null; then
    echo "Instalando dependencias (numpy, scipy, matplotlib)..."
    .venv/bin/python -m pip install --upgrade pip -q
    .venv/bin/python -m pip install -r requirements.txt
fi

# --- 5. Abrir el simulador -------------------------------------------------
echo "Abriendo el simulador..."
.venv/bin/python run.py
