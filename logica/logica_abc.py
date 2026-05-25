# logica/logica_abc.py
# Capa de negocio — clasificación ABC del inventario.
# Sin SQL directo ni widgets Tkinter.

from datos.datos_producto import listar_activos, actualizar_clasificacion


def recalcular_abc() -> None:
    """
    1. Obtener todos los productos activos.
    2. valor_total = stock_actual * precio_unitario (por SKU).
    3. Ordenar DESC por valor_total.
    4. Acumular % del total:
         0-70%  → A  |  70-90% → B  |  90-100% → C
    5. Si valor_global == 0: retornar sin modificar.
    6. UPDATE clasificacion_abc para cada producto.
    """
    productos = listar_activos()
    if not productos:
        return

    # Calcular valor total por producto
    for p in productos:
        p["_valor"] = float(p["stock_actual"]) * float(p["precio_unitario"])

    valor_global = sum(p["_valor"] for p in productos)
    if valor_global == 0:
        return

    # Ordenar de mayor a menor valor
    productos.sort(key=lambda p: p["_valor"], reverse=True)

    acumulado = 0.0
    for p in productos:
        acumulado += p["_valor"]
        pct = acumulado / valor_global

        if pct <= 0.70:
            categoria = "A"
        elif pct <= 0.90:
            categoria = "B"
        else:
            categoria = "C"

        actualizar_clasificacion(p["producto_id"], categoria)
