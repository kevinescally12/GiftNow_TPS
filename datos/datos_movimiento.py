# datos/datos_movimiento.py
# Capa de datos — tabla movimiento.
# Solo SQL. Sin lógica de negocio.

from datos.conexion import obtener_conexion, cerrar_conexion


def insertar_movimiento(producto_id: int,
                        tipo: str,
                        cantidad: int,
                        stock_antes: int,
                        stock_despues: int,
                        usuario_id: int,
                        referencia: str = None,
                        motivo: str = None,
                        supervisor_id: int = None,
                        aprobado: int = 0,
                        cursor=None) -> int:
    """INSERT en movimiento. Ejecutar DENTRO de transacción activa.
    Si se pasa cursor externo, lo usa (participa en la transacción del llamador).
    Retorna movimiento_id generado."""
    sql = (
        "INSERT INTO movimiento "
        "(producto_id, tipo_movimiento, cantidad, stock_antes, stock_despues, "
        " usuario_id, referencia, motivo, supervisor_id, aprobado) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
    )
    params = (producto_id, tipo, cantidad, stock_antes, stock_despues,
              usuario_id, referencia, motivo, supervisor_id, aprobado)

    if cursor is not None:
        # Usar cursor externo — el commit lo maneja el llamador
        cursor.execute(sql, params)
        return cursor.lastrowid

    # Cursor propio — solo para uso directo sin transacción externa
    conexion = None
    cur = None
    try:
        conexion = obtener_conexion()
        cur = conexion.cursor()
        cur.execute(sql, params)
        conexion.commit()
        return cur.lastrowid
    finally:
        cerrar_conexion(conexion, cur)


def historial_sku(producto_id: int,
                  fecha_desde=None,
                  fecha_hasta=None) -> list[dict]:
    """Historial de movimientos del SKU, filtrable por fechas.
    Orden: fecha_hora DESC."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        condiciones = ["m.producto_id = %s"]
        params = [producto_id]

        if fecha_desde is not None:
            condiciones.append("m.fecha_hora >= %s")
            params.append(fecha_desde)
        if fecha_hasta is not None:
            condiciones.append("m.fecha_hora <= %s")
            params.append(fecha_hasta)

        where = " AND ".join(condiciones)
        sql = (
            "SELECT m.movimiento_id, m.tipo_movimiento, m.cantidad, "
            "       m.stock_antes, m.stock_despues, m.fecha_hora, "
            "       m.referencia, m.motivo, m.aprobado, "
            "       u.username AS usuario, "
            "       s.username AS supervisor "
            "FROM movimiento m "
            "JOIN usuario u ON m.usuario_id = u.usuario_id "
            "LEFT JOIN usuario s ON m.supervisor_id = s.usuario_id "
            f"WHERE {where} "
            "ORDER BY m.fecha_hora DESC;"
        )
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cerrar_conexion(conexion, cursor)


def movimientos_por_periodo(fecha_desde=None,
                             fecha_hasta=None) -> list[dict]:
    """Todos los movimientos en el período, con datos del producto.
    Orden: fecha_hora DESC."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        condiciones = []
        params = []

        if fecha_desde is not None:
            condiciones.append("m.fecha_hora >= %s")
            params.append(fecha_desde)
        if fecha_hasta is not None:
            condiciones.append("m.fecha_hora <= %s")
            params.append(fecha_hasta)

        where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

        sql = (
            "SELECT m.movimiento_id, p.stock_code, p.descripcion, "
            "       m.tipo_movimiento, m.cantidad, "
            "       m.stock_antes, m.stock_despues, m.fecha_hora, "
            "       m.referencia, m.motivo, "
            "       u.username AS usuario, "
            "       s.username AS supervisor "
            "FROM movimiento m "
            "JOIN producto p  ON m.producto_id  = p.producto_id "
            "JOIN usuario  u  ON m.usuario_id   = u.usuario_id "
            "LEFT JOIN usuario s ON m.supervisor_id = s.usuario_id "
            f"{where} "
            "ORDER BY m.fecha_hora DESC;"
        )
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cerrar_conexion(conexion, cursor)
