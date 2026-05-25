# main.py
# Punto de entrada del TPS GiftNow.
# Ejecutar: python main.py

import sys
import os

# Asegura que la raíz del proyecto esté en el path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.ui_login import VentanaLogin

if __name__ == "__main__":
    app = VentanaLogin()
    app.mainloop()
