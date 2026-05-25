# datos/datos_usuario.py
# Capa de datos — tabla usuario.
# Solo SQL. Sin lógica de negocio.

from datos.conexion import obtener_conexion, cerrar_conexion


def buscar_por_username(username: str) -> dict | None:
    """Retorna dict del usuario activo o None si no existe/inactivo."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT usuario_id, nombre_completo, username, "
            "       password_hash, rol, activo, fecha_registro "
            "FROM usuario "
            "WHERE username = %s AND activo = 1;",
            (username,)
        )
        return cursor.fetchone()
    finally:
        cerrar_conexion(conexion, cursor)


def listar_activos() -> list[dict]:
    """Retorna lista de todos los usuarios activos."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT usuario_id, nombre_completo, username, "
            "       rol, activo, fecha_registro "
            "FROM usuario "
            "WHERE activo = 1 "
            "ORDER BY nombre_completo;"
        )
        return cursor.fetchall()
    finally:
        cerrar_conexion(conexion, cursor)
