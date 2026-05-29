# datos/datos_producto.py
# Capa de datos — tabla producto.
# Solo SQL. Sin lógica de negocio.

from datos.conexion import obtener_conexion, cerrar_conexion


def buscar_por_code(stock_code: str) -> dict | None:
    """Retorna dict del producto activo o None si no existe/inactivo."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT producto_id, stock_code, descripcion, "
            "       stock_actual, stock_minimo, precio_unitario, "
            "       clasificacion_abc, activo, fecha_registro, usuario_alta_id "
            "FROM producto "
            "WHERE stock_code = %s AND activo = 1;",
            (stock_code,)
        )
        return cursor.fetchone()
    finally:
        cerrar_conexion(conexion, cursor)


def obtener_por_id(producto_id: int) -> dict | None:
    """Retorna dict del producto o None si no existe."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT producto_id, stock_code, descripcion, "
            "       stock_actual, stock_minimo, precio_unitario, "
            "       clasificacion_abc, activo, fecha_registro, usuario_alta_id "
            "FROM producto "
            "WHERE producto_id = %s;",
            (producto_id,)
        )
        return cursor.fetchone()
    finally:
        cerrar_conexion(conexion, cursor)


def listar_activos() -> list[dict]:
    """Retorna lista de todos los productos activos."""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT producto_id, stock_code, descripcion, "
            "       stock_actual, stock_minimo, precio_unitario, "
            "       clasificacion_abc, activo, fecha_registro, usuario_alta_id "
            "FROM producto "
            "WHERE activo = 1 "
            "ORDER BY stock_code;"
        )
        return cursor.fetchall()
    finally:
        cerrar_conexion(conexion, cursor)


def actualizar_stock(producto_id: int, nuevo_stock: int, cursor) -> None:
    """UPDATE stock_actual. Ejecutar DENTRO de transacción activa.
    Recibe cursor externo para participar en la transacción del llamador."""
    cursor.execute(
        "UPDATE producto SET stock_actual = %s WHERE producto_id = %s;",
        (nuevo_stock, producto_id)
    )


def actualizar_clasificacion(producto_id: int, categoria: str) -> None:
    """UPDATE clasificacion_abc. Valores válidos: 'A', 'B', 'C'."""
    if categoria not in ("A", "B", "C"):
        raise ValueError(f"Clasificación inválida: '{categoria}'. Debe ser A, B o C.")
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE producto SET clasificacion_abc = %s WHERE producto_id = %s;",
            (categoria, producto_id)
        )
        conexion.commit()
    finally:
        cerrar_conexion(conexion, cursor)


def actualizar_clasificaciones_bulk(updates: list) -> None:
    """UPDATE clasificacion_abc para todos los productos en una sola transacción.
    updates = [(categoria, producto_id), ...]"""
    if not updates:
        return
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.executemany(
            "UPDATE producto SET clasificacion_abc = %s WHERE producto_id = %s;",
            updates
        )
        conexion.commit()
    finally:
        cerrar_conexion(conexion, cursor)


def insertar_producto(stock_code: str, descripcion: str, stock_actual: int,
                      stock_minimo: int, precio_unitario: float,
                      usuario_alta_id: int,
                      clasificacion_abc: str = "C") -> int:
    """INSERT de un nuevo producto. Retorna producto_id generado.
    Función auxiliar usada en pruebas y en la UI de alta de productos."""
    if clasificacion_abc not in ("A", "B", "C"):
        raise ValueError(f"Clasificación inválida: '{clasificacion_abc}'.")
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO producto "
            "(stock_code, descripcion, stock_actual, stock_minimo, "
            " precio_unitario, clasificacion_abc, usuario_alta_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s);",
            (stock_code, descripcion, stock_actual, stock_minimo,
             precio_unitario, clasificacion_abc, usuario_alta_id)
        )
        conexion.commit()
        return cursor.lastrowid
    finally:
        cerrar_conexion(conexion, cursor)
