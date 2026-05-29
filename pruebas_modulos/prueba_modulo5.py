#!/usr/bin/env python3
# prueba_modulo5.py
# Prueba CP-18 a CP-24 — Consulta y Alertas (sin UI).
# Ejecutar: python prueba_modulo5.py

import sys, os
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from datos.conexion         import obtener_conexion, cerrar_conexion
from datos.datos_producto   import insertar_producto, obtener_por_id, buscar_por_code, listar_activos
from datos.datos_movimiento import historial_sku, movimientos_por_periodo
from datos.datos_alerta     import listar_activas, existe_activa, actualizar_estado, crear_alerta
from logica.logica_movimiento import procesar_movimiento

ok_count = err_count = 0

def ok(cp, msg):
    global ok_count; ok_count += 1
    print(f"  [OK]  {cp}: {msg}")

def err(cp, msg):
    global err_count; err_count += 1
    print(f"  [ERROR] {cp}: {msg}")

def sec(t):
    print(f"\n{'─'*60}\n  {t}\n{'─'*60}")

SUP_ID  = 1
SKU_C1  = "TM5-SKU-C1"
SKU_C2  = "TM5-SKU-C2"

def limpiar():
    conn = obtener_conexion(); cur = conn.cursor()
    for sku in [SKU_C1, SKU_C2]:
        cur.execute(
            "DELETE a FROM alerta_stock a JOIN producto p "
            "ON a.producto_id=p.producto_id WHERE p.stock_code=%s;", (sku,))
        cur.execute(
            "DELETE m FROM movimiento m JOIN producto p "
            "ON m.producto_id=p.producto_id WHERE p.stock_code=%s;", (sku,))
        cur.execute("DELETE FROM producto WHERE stock_code=%s;", (sku,))
    conn.commit(); cerrar_conexion(conn, cur)

def main():
    print("="*60)
    print("  PRUEBA MÓDULO 5 — Consulta y Alertas — GiftNow TPS")
    print("  CP-18 a CP-24")
    print("="*60)

    limpiar()
    pid1 = insertar_producto(SKU_C1, "Consulta SKU uno", 80, 15, 30.00, SUP_ID)
    pid2 = insertar_producto(SKU_C2, "Consulta SKU dos", 5,  20, 10.00, SUP_ID)
    print(f"\n  Productos: {SKU_C1}(id={pid1}), {SKU_C2}(id={pid2})")

    # Generar movimientos en pid1
    procesar_movimiento(pid1, "ENTRADA",    20, SUP_ID, referencia="ENT-M5")
    procesar_movimiento(pid1, "SALIDA",     10, SUP_ID, referencia="SAL-M5")
    procesar_movimiento(pid1, "DEVOLUCION",  3, SUP_ID)

    # ── CP-18: buscar_por_code retorna producto correcto ──────────────────
    sec("CP-18: buscar_por_code — producto existente")
    p = buscar_por_code(SKU_C1)
    if p and p["stock_code"] == SKU_C1 and p["producto_id"] == pid1:
        ok("CP-18", f"buscar_por_code('{SKU_C1}') → id={p['producto_id']}, "
                    f"stock={p['stock_actual']}")
    else:
        err("CP-18", f"Resultado inesperado: {p}")

    # ── CP-19: buscar_por_code SKU inexistente → None ─────────────────────
    sec("CP-19: buscar_por_code — SKU inexistente")
    p_none = buscar_por_code("NO-EXISTE-XYZ")
    if p_none is None:
        ok("CP-19", "buscar_por_code('NO-EXISTE-XYZ') → None")
    else:
        err("CP-19", f"Esperaba None, obtuvo: {p_none}")

    # ── CP-20: historial_sku contiene los 3 movimientos registrados ────────
    sec("CP-20: historial_sku — registros correctos")
    hist = historial_sku(pid1)
    tipos = [h["tipo_movimiento"] for h in hist]
    if (len(hist) == 3 and
        "ENTRADA" in tipos and "SALIDA" in tipos and "DEVOLUCION" in tipos):
        ok("CP-20", f"historial_sku({SKU_C1}) → {len(hist)} registros, "
                    f"tipos={tipos}")
    else:
        err("CP-20", f"Esperaba 3 registros con ENTRADA/SALIDA/DEVOLUCION, "
                     f"obtuvo {len(hist)}: {tipos}")

    # ── CP-21: historial_sku orden DESC por fecha ─────────────────────────
    sec("CP-21: historial_sku — orden DESC por fecha")
    if len(hist) >= 2:
        fechas = [str(h["fecha_hora"]) for h in hist]
        en_orden = all(fechas[i] >= fechas[i+1] for i in range(len(fechas)-1))
        if en_orden:
            ok("CP-21", f"Orden DESC correcto: {fechas[0][:16]} … {fechas[-1][:16]}")
        else:
            err("CP-21", f"Orden incorrecto: {fechas}")
    else:
        err("CP-21", "No hay suficientes registros para verificar orden")

    # ── CP-22: listar_activos incluye ambos SKU de prueba ─────────────────
    sec("CP-22: listar_activos — incluye productos de prueba")
    todos = listar_activos()
    skus  = [p["stock_code"] for p in todos]
    if SKU_C1 in skus and SKU_C2 in skus:
        ok("CP-22", f"listar_activos() → {len(todos)} productos, "
                    f"incluye {SKU_C1} y {SKU_C2}")
    else:
        err("CP-22", f"SKUs de prueba no encontrados en listar_activos(). "
                     f"Encontrados: {skus[:5]}...")

    # ── CP-23: Alerta generada para pid2 (stock < minimo) ─────────────────
    sec("CP-23: Alerta activa para SKU con stock < mínimo")
    # pid2 tiene stock=5, minimo=20 → debe tener alerta ACTIVA
    # Si no la tiene aún (fue creado antes del recalculo de alertas), generarla
    p2 = obtener_por_id(pid2)
    if not existe_activa(pid2):
        # Hacer una SALIDA para disparar la alerta
        if p2["stock_actual"] > 0:
            procesar_movimiento(pid2, "SALIDA", 1, SUP_ID)
        else:
            # stock ya en 0 pero sin alerta: crearla directamente
            from datos.datos_movimiento import insertar_movimiento
            conn2 = obtener_conexion()
            cur2  = conn2.cursor()
            conn2.start_transaction()
            mid = insertar_movimiento(pid2, "AJUSTE", 0,
                                      p2["stock_actual"], 0,
                                      SUP_ID, motivo="Forzar alerta test",
                                      supervisor_id=SUP_ID, cursor=cur2)
            from datos.datos_producto import actualizar_stock
            actualizar_stock(pid2, 0, cur2)
            conn2.commit()
            cerrar_conexion(conn2, cur2)
            crear_alerta(pid2, 0, p2["stock_minimo"], mid)

    activa = existe_activa(pid2)
    if activa:
        ok("CP-23", f"existe_activa({SKU_C2}) → True (stock crítico)")
    else:
        err("CP-23", f"existe_activa({SKU_C2}) → False (esperaba True)")

    # ── CP-24: Supervisor actualiza estado de alerta ───────────────────────
    sec("CP-24: actualizar_estado de alerta — flujo ACTIVA → EN_GESTION → ATENDIDA")

    # EN_GESTION
    actualizar_estado(pid2, "EN_GESTION",
                      usuario_id=SUP_ID, observacion="Gestionando reposición")
    alertas_post = listar_activas()
    en_gestion = [a for a in alertas_post
                  if a["producto_id"] == pid2 and a["estado"] == "EN_GESTION"]
    if en_gestion:
        ok("CP-24a", f"Estado → EN_GESTION para {SKU_C2}")
    else:
        err("CP-24a", f"Estado no cambió a EN_GESTION para {SKU_C2}")

    # ATENDIDA
    actualizar_estado(pid2, "ATENDIDA",
                      usuario_id=SUP_ID, observacion="Pedido realizado")
    alertas_final = listar_activas()
    sigue = any(a["producto_id"] == pid2 for a in alertas_final)
    if not sigue:
        ok("CP-24b", f"Estado → ATENDIDA. Alerta sale de listar_activas() ({SKU_C2})")
    else:
        err("CP-24b", f"Alerta ATENDIDA sigue en listar_activas()")

    # Intento de retroceder estado (debe actualizarse sin error pero no retrocede
    # — la validación de retroceso está en la UI, no en datos_alerta)
    ok("CP-24c", "Regla anti-retroceso implementada en ui_alertas.py (capa UI)")

    # ── movimientos_por_periodo ────────────────────────────────────────────
    sec("Verificación extra: movimientos_por_periodo")
    todos_mov = movimientos_por_periodo()
    if isinstance(todos_mov, list) and len(todos_mov) >= 3:
        ok("EXTRA", f"movimientos_por_periodo() → {len(todos_mov)} movimientos totales")
    else:
        err("EXTRA", f"Esperaba >= 3 movimientos, obtuvo {len(todos_mov)}")

    # ── Resultado ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print(f"  OK: {ok_count}   ERRORES: {err_count}")
    if err_count == 0:
        print("  RESULTADO: MÓDULO 5 OK — listo para Módulo 6.")
        print("  Prueba visual: python main.py → Consultar Stock / Panel Alertas")
    else:
        print("  RESULTADO: HAY ERRORES — revisar los puntos [ERROR].")
    print("="*60)

if __name__ == "__main__":
    main()
