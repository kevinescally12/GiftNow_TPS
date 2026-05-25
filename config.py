# config.py
# Parámetros de conexión a la base de datos giftnow_tps.
# Importado ÚNICAMENTE por datos/conexion.py.
# Nunca importar desde logica_* ni ui_*.

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "giftnow_tps",
    "user":     "root",
    "password": "72054651",          # Cambiar según entorno local
    "charset":  "utf8mb4",
}
