# logica/logica_reportes.py
# Capa de negocio — generación de reportes del almacén.
# Sin SQL directo ni widgets Tkinter.

from datos.datos_producto   import listar_activos
from datos.datos_movimiento import movimientos_por_periodo, rotacion_por_periodo
from datos.datos_alerta     import listar_historico


def reporte_valorizacion() -> dict:
    """
    Valorización del inventario por clasificación ABC.

    Retorna:
    {
      "productos": [
          {"stock_code", "descripcion", "clasificacion_abc",
           "stock_actual", "precio_unitario", "valor_total"}, ...
      ],
      "resumen": {
          "A": {"cantidad_skus": int, "valor_total": float, "pct_valor": float},
          "B": {...},
          "C": {...},
      },
      "valor_global": float,
      "total_skus":   int,
    }
    """
    productos = listar_activos()

    filas = []
    for p in productos:
        valor = float(p["stock_actual"]) * float(p["precio_unitario"])
        filas.append({
            "stock_code":      p["stock_code"],
            "descripcion":     p["descripcion"],
            "clasificacion_abc": p["clasificacion_abc"],
            "stock_actual":    int(p["stock_actual"]),
            "precio_unitario": float(p["precio_unitario"]),
            "valor_total":     valor,
        })

    filas.sort(key=lambda x: x["valor_total"], reverse=True)

    valor_global = sum(f["valor_total"] for f in filas)

    resumen = {cat: {"cantidad_skus": 0, "valor_total": 0.0, "pct_valor": 0.0}
               for cat in ("A", "B", "C")}
    for f in filas:
        cat = f["clasificacion_abc"]
        resumen[cat]["cantidad_skus"] += 1
        resumen[cat]["valor_total"]   += f["valor_total"]

    if valor_global > 0:
        for cat in resumen:
            resumen[cat]["pct_valor"] = (
                resumen[cat]["valor_total"] / valor_global * 100)

    return {
        "productos":    filas,
        "resumen":      resumen,
        "valor_global": valor_global,
        "total_skus":   len(filas),
    }


def reporte_rotacion(fecha_desde=None, fecha_hasta=None) -> dict:
    """
    Rotación de stock por SKU en el período indicado.
    La agregación ocurre en MySQL — no trae filas individuales a Python.

    Retorna:
    {
      "productos": [
          {"stock_code", "descripcion", "clasificacion_abc",
           "entradas", "salidas", "devoluciones", "ajustes",
           "total_movimientos"}, ...
      ],
      "total_movimientos": int,
      "periodo": {"desde": str|None, "hasta": str|None},
    }
    """
    filas = rotacion_por_periodo(fecha_desde, fecha_hasta)

    # Normalizar tipos numéricos que MySQL puede devolver como Decimal
    for f in filas:
        f["entradas"]         = int(f["entradas"])
        f["salidas"]          = int(f["salidas"])
        f["devoluciones"]     = int(f["devoluciones"])
        f["ajustes"]          = int(f["ajustes"])
        f["total_movimientos"] = int(f["total_movimientos"])

    total = sum(f["total_movimientos"] for f in filas)

    return {
        "productos":        filas,
        "total_movimientos": total,
        "periodo": {
            "desde": str(fecha_desde) if fecha_desde else None,
            "hasta": str(fecha_hasta) if fecha_hasta else None,
        },
    }


def reporte_alertas_historico() -> dict:
    """
    Historial completo de alertas (todos los estados).

    Retorna:
    {
      "alertas": [...],
      "resumen": {"ACTIVA": int, "EN_GESTION": int, "ATENDIDA": int},
      "total": int,
    }
    """
    alertas = listar_historico()

    resumen = {"ACTIVA": 0, "EN_GESTION": 0, "ATENDIDA": 0}
    for a in alertas:
        estado = a.get("estado", "ACTIVA")
        if estado in resumen:
            resumen[estado] += 1

    return {
        "alertas": alertas,
        "resumen": resumen,
        "total":   len(alertas),
    }
