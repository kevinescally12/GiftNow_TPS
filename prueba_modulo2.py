#!/usr/bin/env python3
# prueba_modulo2.py
# Prueba directa de las funciones de capa de datos.
# No usa UI ni lógica de negocio.
# Ejecutar: python prueba_modulo2.py

import sys
import os
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from datos.datos_usuario   import buscar_por_username, listar_activos as usuarios_activos
from datos.datos_producto  import (buscar_por_code, obtener_por_id,
                                   listar_activos as productos_activos,
                                   actualizar_clasificacion, insertar_producto)
from datos.datos_movimiento import insertar_movimiento, historial_sku, movimientos_por_periodo
from datos.datos_alerta    import (crear_alerta, existe_activa,
                                   actualizar_estado, listar_activas)
from datos.conexion        import obtener_conexion, cerrar_conexion

# ── Utilidades de impresión ──────────────────────────────────────────────────

ok_count  = 0
err_count = 0

def ok(msg):
    global ok_count
    ok_count += 1
    print(f"  [OK]  {msg}")

def err(msg):
    global err_count
    err_count += 1
    print(f"  [ERROR] {msg}")

def seccion(titulo):
    print(f"\n{'─'*60}")
    print(f"  {titulo}")
    print(f"{'─'*60}")

# ── Limpieza de datos de prueba ──────────────────────────────────────────────

SKU_PRUEBA = "TEST-M2-001"

def limpiar_datos_prueba():
    """Elimina registros de prueba para que la prueba sea re-ejecutable."""
    conn = None
    cur  = None
    try:
        conn = obtener_conexion()
        cur  = conn.cursor()
        # Orden inverso a FK: alerta → movimiento → producto
        cur.execute(
            "DELETE a FROM alerta_stock a "
            "JOIN producto p ON a.producto_id = p.producto_id "
            "WHERE p.stock_code = %s;", (SKU_PRUEBA,)
        )
        cur.execute(
            "DELETE m FROM movimiento m "
            "JOIN producto p ON m.producto_id = p.producto_id "
            "WHERE p.stock_code = %s;", (SKU_PRUEBA,)
        )
        cur.execute("DELETE FROM producto WHERE stock_code = %s;", (SKU_PRUEBA,))
        conn.commit()
    finally:
        cerrar_conexion(conn, cur)

# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  PRUEBA MÓDULO 2 — Capa de Datos — GiftNow TPS")
    print("=" * 60)

    limpiar_datos_prueba()

    # ── 1. datos_usuario ────────────────────────────────────────────────────
    seccion("1. datos_usuario")

    u = buscar_por_username("supervisor")
    if u and u["rol"] == "SUPERVISOR":
        ok(f"buscar_por_username('supervisor') → id={u['usuario_id']}, rol={u['rol']}")
    else:
        err(f"buscar_por_username('supervisor') retornó: {u}")

    u_none = buscar_por_username("no_existe_xyz")
    if u_none is None:
        ok("buscar_por_username('no_existe_xyz') → None  (correcto)")
    else:
        err(f"Esperaba None, obtuvo: {u_none}")

    lista_u = usuarios_activos()
    if isinstance(lista_u, list) and len(lista_u) >= 1:
        ok(f"listar_activos() → {len(lista_u)} usuario(s)")
    else:
        err(f"listar_activos() retornó: {lista_u}")

    supervisor_id = u["usuario_id"]  # lo usaremos en las siguientes pruebas

    # ── 2. datos_producto (alta) ────────────────────────────────────────────
    seccion("2. datos_producto — alta")

    pid = insertar_producto(
        stock_code     = SKU_PRUEBA,
        descripcion    = "Producto de prueba Módulo 2",
        stock_actual   = 50,
        stock_minimo   = 10,
        precio_unitario= 25.50,
        usuario_alta_id= supervisor_id,
        clasificacion_abc = "C"
    )
    if isinstance(pid, int) and pid > 0:
        ok(f"insertar_producto('{SKU_PRUEBA}') → producto_id={pid}")
    else:
        err(f"insertar_producto retornó: {pid}")
        return  # sin producto no hay pruebas siguientes

    # ── 3. datos_producto (consultas) ───────────────────────────────────────
    seccion("3. datos_producto — consultas")

    p_code = buscar_por_code(SKU_PRUEBA)
    if p_code and p_code["producto_id"] == pid:
        ok(f"buscar_por_code('{SKU_PRUEBA}') → stock_actual={p_code['stock_actual']}")
    else:
        err(f"buscar_por_code retornó: {p_code}")

    p_id = obtener_por_id(pid)
    if p_id and p_id["stock_code"] == SKU_PRUEBA:
        ok(f"obtener_por_id({pid}) → stock_code='{p_id['stock_code']}'")
    else:
        err(f"obtener_por_id retornó: {p_id}")

    p_none = buscar_por_code("NO-EXISTE-9999")
    if p_none is None:
        ok("buscar_por_code('NO-EXISTE-9999') → None  (correcto)")
    else:
        err(f"Esperaba None, obtuvo: {p_none}")

    lista_p = productos_activos()
    if isinstance(lista_p, list) and any(p["stock_code"] == SKU_PRUEBA for p in lista_p):
        ok(f"listar_activos() → {len(lista_p)} producto(s), incluye {SKU_PRUEBA}")
    else:
        err(f"listar_activos() no incluyó el producto de prueba.")

    # ── 4. datos_producto (actualizar_clasificacion) ─────────────────────
    seccion("4. datos_producto — actualizar_clasificacion")

    actualizar_clasificacion(pid, "A")
    p_actualizado = obtener_por_id(pid)
    if p_actualizado and p_actualizado["clasificacion_abc"] == "A":
        ok(f"actualizar_clasificacion({pid}, 'A') → OK")
    else:
        err(f"clasificacion_abc esperada 'A', obtuvo: {p_actualizado}")

    actualizar_clasificacion(pid, "C")  # restaurar
    try:
        actualizar_clasificacion(pid, "Z")
        err("Debió lanzar ValueError para clasificación 'Z'")
    except ValueError as e:
        ok(f"ValueError correcto para clasificación inválida: {e}")

    # ── 5. datos_movimiento (insertar dentro de transacción manual) ──────────
    seccion("5. datos_movimiento — insertar_movimiento")

    conn = obtener_conexion()
    cur  = conn.cursor()
    try:
        conn.start_transaction()
        stock_antes   = 50
        stock_despues = 40   # simula una SALIDA de 10 unidades
        mov_id = insertar_movimiento(
            producto_id   = pid,
            tipo          = "SALIDA",
            cantidad      = 10,
            stock_antes   = stock_antes,
            stock_despues = stock_despues,
            usuario_id    = supervisor_id,
            referencia    = "REF-TEST-001",
            cursor        = cur
        )
        # Actualizar stock en la misma transacción
        cur.execute(
            "UPDATE producto SET stock_actual = %s WHERE producto_id = %s;",
            (stock_despues, pid)
        )
        conn.commit()
        if isinstance(mov_id, int) and mov_id > 0:
            ok(f"insertar_movimiento(SALIDA, 10 u) → movimiento_id={mov_id}")
        else:
            err(f"insertar_movimiento retornó: {mov_id}")
    except Exception as e:
        conn.rollback()
        err(f"Transacción falló: {e}")
        mov_id = None
    finally:
        cerrar_conexion(conn, cur)

    # ── 6. datos_movimiento (historial_sku) ──────────────────────────────────
    seccion("6. datos_movimiento — historial_sku")

    historial = historial_sku(pid)
    if isinstance(historial, list) and len(historial) >= 1:
        h = historial[0]
        ok(f"historial_sku({pid}) → {len(historial)} registro(s), "
           f"último tipo='{h['tipo_movimiento']}'")
    else:
        err(f"historial_sku retornó: {historial}")

    # ── 7. datos_movimiento (movimientos_por_periodo) ─────────────────────────
    seccion("7. datos_movimiento — movimientos_por_periodo")

    todos = movimientos_por_periodo()
    if isinstance(todos, list) and len(todos) >= 1:
        ok(f"movimientos_por_periodo() → {len(todos)} movimiento(s) totales")
    else:
        err(f"movimientos_por_periodo retornó: {todos}")

    # ── 8. datos_alerta (crear + existe_activa) ───────────────────────────────
    seccion("8. datos_alerta — crear_alerta / existe_activa")

    if mov_id is not None:
        p_actual = obtener_por_id(pid)
        crear_alerta(
            producto_id     = pid,
            stock_al_activar= p_actual["stock_actual"],
            stock_minimo_ref= p_actual["stock_minimo"],
            movimiento_id   = mov_id
        )
        ok(f"crear_alerta(producto={pid}, mov={mov_id}) → OK")

        activa = existe_activa(pid)
        if activa:
            ok(f"existe_activa({pid}) → True  (correcto)")
        else:
            err(f"existe_activa({pid}) retornó False, debía ser True")
    else:
        err("Saltando pruebas de alerta (movimiento no creado).")

    # ── 9. datos_alerta (listar_activas) ─────────────────────────────────────
    seccion("9. datos_alerta — listar_activas")

    activas = listar_activas()
    if isinstance(activas, list) and any(a["producto_id"] == pid for a in activas):
        ok(f"listar_activas() → {len(activas)} alerta(s), incluye producto {pid}")
    else:
        err(f"listar_activas() no incluyó la alerta del producto {pid}: {activas}")

    # ── 10. datos_alerta (actualizar_estado) ──────────────────────────────────
    seccion("10. datos_alerta — actualizar_estado")

    actualizar_estado(pid, "EN_GESTION", usuario_id=supervisor_id,
                      observacion="En gestión — prueba M2")
    activas_post = listar_activas()
    en_gestion = [a for a in activas_post
                  if a["producto_id"] == pid and a["estado"] == "EN_GESTION"]
    if en_gestion:
        ok(f"actualizar_estado(→ EN_GESTION) → OK")
    else:
        err("Estado no cambió a EN_GESTION.")

    actualizar_estado(pid, "ATENDIDA", usuario_id=supervisor_id,
                      observacion="Atendida — prueba M2")
    activas_final = listar_activas()
    sigue_activa  = any(a["producto_id"] == pid for a in activas_final)
    if not sigue_activa:
        ok("actualizar_estado(→ ATENDIDA) → alerta sale de listar_activas()  (correcto)")
    else:
        err("La alerta ATENDIDA sigue apareciendo en listar_activas().")

    try:
        actualizar_estado(pid, "INVALIDO")
        err("Debió lanzar ValueError para estado 'INVALIDO'")
    except ValueError as e:
        ok(f"ValueError correcto para estado inválido: {e}")

    # ── Resultado final ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  OK: {ok_count}   ERRORES: {err_count}")
    if err_count == 0:
        print("  RESULTADO: MÓDULO 2 OK — listo para Módulo 3.")
    else:
        print("  RESULTADO: HAY ERRORES — revisar los puntos marcados [ERROR].")
    print("=" * 60)


if __name__ == "__main__":
    main()
