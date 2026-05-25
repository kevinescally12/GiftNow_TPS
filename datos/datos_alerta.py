# datos/datos_alerta.py
# Capa de datos — tabla alerta_stock.
# Solo SQL. Sin lógica de negocio.

from datetime import datetime
from datos.conexion import obtener_conexion, cerrar_conexion

_ESTADOS_VALIDOS = {"ACTIVA", "EN_GESTION", "ATENDIDA"}


def crear_alerta(producto_id: int,
                 stock_al_activar: int,
                 stock_minimo_ref: int,
                 movimiento_id: int) -> None:
    """INSERT en alerta_stock con estado='ACTIVA'."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO alerta_stock "
            "(producto_id, stock_al_activar, stock_minimo_ref, movimiento_id) "
            "VALUES (%s, %s, %s, %s);",
            (producto_id, stock_al_activar, stock_minimo_ref, movimiento_id)
        )
        conexion.commit()
    finally:
        cerrar_conexion(conexion, cursor)


def existe_activa(producto_id: int) -> bool:
    """True si existe alerta con estado ACTIVA para el producto."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM alerta_stock "
            "WHERE producto_id = %s AND estado = 'ACTIVA';",
            (producto_id,)
        )
        fila = cursor.fetchone()
        return fila[0] > 0
    finally:
        cerrar_conexion(conexion, cursor)


def actualizar_estado(producto_id: int,
                      nuevo_estado: str,
                      usuario_id: int = None,
                      observacion: str = None) -> None:
    """UPDATE estado de la alerta activa/en_gestión del producto.
    nuevo_estado: 'EN_GESTION' | 'ATENDIDA'."""
    if nuevo_estado not in _ESTADOS_VALIDOS:
        raise ValueError(
            f"Estado inválido: '{nuevo_estado}'. "
            f"Valores válidos: {_ESTADOS_VALIDOS}"
        )
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE alerta_stock "
            "SET estado = %s, "
            "    usuario_gestion_id = %s, "
            "    fecha_gestion = %s, "
            "    observacion = %s "
            "WHERE producto_id = %s "
            "  AND estado IN ('ACTIVA', 'EN_GESTION') "
            "ORDER BY fecha_activacion DESC "
            "LIMIT 1;",
            (nuevo_estado,
             usuario_id,
             datetime.now() if usuario_id is not None else None,
             observacion,
             producto_id)
        )
        conexion.commit()
    finally:
        cerrar_conexion(conexion, cursor)


def listar_activas() -> list[dict]:
    """Alertas con estado ACTIVA o EN_GESTION, con datos del producto."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT a.alerta_id, a.estado, "
            "       a.stock_al_activar, a.stock_minimo_ref, "
            "       a.fecha_activacion, a.observacion, "
            "       p.producto_id, p.stock_code, p.descripcion, "
            "       p.stock_actual, p.clasificacion_abc, "
            "       u.username AS usuario_gestion "
            "FROM alerta_stock a "
            "JOIN producto p ON a.producto_id = p.producto_id "
            "LEFT JOIN usuario u ON a.usuario_gestion_id = u.usuario_id "
            "WHERE a.estado IN ('ACTIVA', 'EN_GESTION') "
            "ORDER BY a.fecha_activacion DESC;"
        )
        return cursor.fetchall()
    finally:
        cerrar_conexion(conexion, cursor)


def listar_historico() -> list[dict]:
    """Todas las alertas (todos los estados), con datos del producto.
    Usado por el módulo de reportes."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT a.alerta_id, a.estado, "
            "       a.stock_al_activar, a.stock_minimo_ref, "
            "       a.fecha_activacion, a.fecha_gestion, a.observacion, "
            "       p.stock_code, p.descripcion, p.clasificacion_abc, "
            "       u.username AS usuario_gestion "
            "FROM alerta_stock a "
            "JOIN producto p ON a.producto_id = p.producto_id "
            "LEFT JOIN usuario u ON a.usuario_gestion_id = u.usuario_id "
            "ORDER BY a.fecha_activacion DESC;"
        )
        return cursor.fetchall()
    finally:
        cerrar_conexion(conexion, cursor)
