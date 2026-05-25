# logica/logica_movimiento.py
# Capa de negocio — función central del sistema.
# Sin SQL directo ni widgets Tkinter.

from datos.conexion       import obtener_conexion, cerrar_conexion
from datos.datos_producto import buscar_por_code, obtener_por_id, actualizar_stock
from datos.datos_movimiento import insertar_movimiento
from logica.logica_alerta import evaluar_y_generar_alerta, cerrar_alertas_por_reposicion
from logica.logica_abc    import recalcular_abc

TIPOS_VALIDOS = {"ENTRADA", "SALIDA", "DEVOLUCION", "AJUSTE"}


def procesar_movimiento(producto_id: int,
                        tipo: str,
                        cantidad: int,
                        usuario_id: int,
                        referencia: str = None,
                        motivo: str = None,
                        supervisor_id: int = None) -> int:
    """
    Función central del TPS. Secuencia obligatoria:

    1. Validar campos (ValueError si falla)
    2. Obtener producto (ValueError si no existe/inactivo)
    3. Calcular stock_despues según tipo
    4. Verificar stock suficiente para SALIDA (ValueError si falla)
    5. Ejecutar transacción atómica:
         START TRANSACTION
           insertar_movimiento(...)  → movimiento_id
           actualizar_stock(...)     → stock_actual = stock_despues
         COMMIT  (ROLLBACK si cualquier paso falla)
    6. Si tipo in {SALIDA, AJUSTE}:
           evaluar_y_generar_alerta(...)
    7. Si tipo in {ENTRADA, DEVOLUCION}:
           cerrar_alertas_por_reposicion(...)
    8. recalcular_abc()
    9. Retornar movimiento_id
    """

    # ── Paso 1: Validaciones ─────────────────────────────────────────────
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(
            f"Tipo de movimiento inválido: '{tipo}'. "
            f"Valores válidos: {TIPOS_VALIDOS}"
        )

    if not isinstance(cantidad, int) or cantidad <= 0:
        raise ValueError(
            f"La cantidad debe ser un entero positivo. Recibido: {cantidad!r}"
        )

    if tipo == "AJUSTE":
        if not motivo or not str(motivo).strip():
            raise ValueError("El campo 'motivo' es obligatorio para movimientos de tipo AJUSTE.")
        if supervisor_id is None:
            raise ValueError("El campo 'supervisor_id' es obligatorio para movimientos de tipo AJUSTE.")

    # ── Paso 2: Obtener producto ─────────────────────────────────────────
    producto = obtener_por_id(producto_id)
    if producto is None or not producto["activo"]:
        raise ValueError(
            f"Producto con id={producto_id} no existe o está inactivo."
        )

    stock_antes = int(producto["stock_actual"])
    stock_minimo = int(producto["stock_minimo"])

    # ── Paso 3: Calcular stock_despues ───────────────────────────────────
    if tipo in ("ENTRADA", "DEVOLUCION"):
        stock_despues = stock_antes + cantidad
    elif tipo == "SALIDA":
        stock_despues = stock_antes - cantidad
    else:  # AJUSTE
        stock_despues = cantidad   # valor absoluto

    # ── Paso 4: Verificar stock suficiente para SALIDA ───────────────────
    if tipo == "SALIDA" and stock_despues < 0:
        raise ValueError(
            f"Stock insuficiente. Disponible: {stock_antes}, Solicitado: {cantidad}."
        )

    # ── Paso 5: Transacción atómica ──────────────────────────────────────
    aprobado  = 1 if tipo == "AJUSTE" else 0
    conexion  = None
    cursor    = None
    movimiento_id = None

    try:
        conexion = obtener_conexion()
        cursor   = conexion.cursor()
        conexion.start_transaction()

        movimiento_id = insertar_movimiento(
            producto_id   = producto_id,
            tipo          = tipo,
            cantidad      = cantidad,
            stock_antes   = stock_antes,
            stock_despues = stock_despues,
            usuario_id    = usuario_id,
            referencia    = referencia,
            motivo        = motivo,
            supervisor_id = supervisor_id,
            aprobado      = aprobado,
            cursor        = cursor,
        )

        actualizar_stock(producto_id, stock_despues, cursor)

        conexion.commit()

    except Exception:
        if conexion:
            try:
                conexion.rollback()
            except Exception:
                pass
        raise

    finally:
        cerrar_conexion(conexion, cursor)

    # ── Paso 6 / 7: Alertas ──────────────────────────────────────────────
    if tipo in ("SALIDA", "AJUSTE"):
        evaluar_y_generar_alerta(
            producto_id  = producto_id,
            stock_actual = stock_despues,
            stock_minimo = stock_minimo,
            movimiento_id= movimiento_id,
        )
    elif tipo in ("ENTRADA", "DEVOLUCION"):
        cerrar_alertas_por_reposicion(
            producto_id  = producto_id,
            stock_actual = stock_despues,
            stock_minimo = stock_minimo,
        )

    # ── Paso 8: Recalcular ABC ───────────────────────────────────────────
    recalcular_abc()

    # ── Paso 9: Retornar movimiento_id ───────────────────────────────────
    return movimiento_id
