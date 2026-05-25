# logica/logica_alerta.py
# Capa de negocio — gestión de alertas de stock mínimo.
# Sin SQL directo ni widgets Tkinter.

from datos.datos_alerta import crear_alerta, existe_activa, actualizar_estado


def evaluar_y_generar_alerta(producto_id: int,
                              stock_actual: int,
                              stock_minimo: int,
                              movimiento_id: int) -> None:
    """Crea alerta si stock_actual <= stock_minimo
    Y no existe alerta ACTIVA para ese producto."""
    if stock_actual <= stock_minimo:
        if not existe_activa(producto_id):
            crear_alerta(
                producto_id      = producto_id,
                stock_al_activar = stock_actual,
                stock_minimo_ref = stock_minimo,
                movimiento_id    = movimiento_id,
            )


def cerrar_alertas_por_reposicion(producto_id: int,
                                   stock_actual: int,
                                   stock_minimo: int) -> None:
    """Cierra alerta ACTIVA/EN_GESTION si stock_actual > stock_minimo.
    Llamar tras ENTRADA y DEVOLUCION."""
    if stock_actual > stock_minimo:
        actualizar_estado(
            producto_id  = producto_id,
            nuevo_estado = "ATENDIDA",
            usuario_id   = None,
            observacion  = "Cerrada automáticamente por reposición de stock.",
        )
