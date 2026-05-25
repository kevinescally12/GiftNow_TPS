# datos/conexion.py
# Capa de datos — gestión de conexión MySQL.
# Única capa autorizada a importar config.py.

import sys
import os

# Permite importar config.py desde la raíz del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error as MySQLError
from config import DB_CONFIG


def obtener_conexion() -> mysql.connector.MySQLConnection:
    """Retorna conexión activa a giftnow_tps. Lanza ConnectionError si falla."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        if conexion.is_connected():
            return conexion
        raise ConnectionError("La conexión no quedó activa tras mysql.connector.connect().")
    except MySQLError as e:
        raise ConnectionError(
            f"No se pudo conectar a MySQL ({DB_CONFIG['host']}:{DB_CONFIG['port']} "
            f"→ {DB_CONFIG['database']}): {e}"
        ) from e


def cerrar_conexion(conexion, cursor=None) -> None:
    """Cierra cursor y conexión de forma segura."""
    try:
        if cursor is not None:
            cursor.close()
    except Exception:
        pass
    try:
        if conexion is not None and conexion.is_connected():
            conexion.close()
    except Exception:
        pass
