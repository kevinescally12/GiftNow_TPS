#!/usr/bin/env python3
# prueba_modulo4.py
# Prueba de lógica de movimientos (CP-05 a CP-17) sin UI.
# Ejecutar: python prueba_modulo4.py

import sys, os
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from datos.conexion         import obtener_conexion, cerrar_conexion
from datos.datos_producto   import insertar_producto, obtener_por_id, buscar_por_code
from datos.datos_movimiento import historial_sku
from datos.datos_alerta     import listar_activas, existe_activa
from logica.logica_movimiento import procesar_movimiento

ok_count = err_count = 0

def ok(cp, msg):
    global ok_count; ok_count += 1
    print(f"  [OK]  {cp}: {msg}")

def err(cp, msg):
    global err_count; err_count += 1
    print(f"  [ERROR] {cp}: {msg}")

def sec(titulo):
    print(f"\n{'─'*60}\n  {titulo}\n{'─'*60}")

# ── Setup ────────────────────────────────────────────────────────────────────

SKU_A = "TM4-SKU-A"   # producto con stock normal
SKU_B = "TM4-SKU-B"   # producto para probar alertas

SUP_ID = 1   # supervisor creado en Módulo 1

def limpiar():
    conn = obtener_conexion(); cur = conn.cursor()
    for sku in [SKU_A, SKU_B]:
        cur.execute(
            "DELETE a FROM alerta_stock a JOIN producto p "
            "ON a.producto_id=p.producto_id WHERE p.stock_code=%s;", (sku,))
        cur.execute(
            "DELETE m FROM movimiento m JOIN producto p "
            "ON m.producto_id=p.producto_id WHERE p.stock_code=%s;", (sku,))
        cur.execute("DELETE FROM producto WHERE stock_code=%s;", (sku,))
    conn.commit(); cerrar_conexion(conn, cur)

def crear_productos():
    pid_a = insertar_producto(SKU_A, "Producto M4 A", 100, 10, 50.00, SUP_ID)
    pid_b = insertar_producto(SKU_B, "Producto M4 B (alerta)", 5, 10, 20.00, SUP_ID)
    return pid_a, pid_b

# ════════════════════════════════════════════════════════════════════════════

def main():
    print("="*60)
    print("  PRUEBA MÓDULO 4 — Registro de Movimientos — GiftNow TPS")
    print("  CP-05 a CP-17")
    print("="*60)

    limpiar()
    pid_a, pid_b = crear_productos()
    print(f"\n  Productos de prueba: {SKU_A}(id={pid_a}), {SKU_B}(id={pid_b})")

    # ── CP-05: ENTRADA válida ─────────────────────────────────────────────
    sec("CP-05: ENTRADA válida")
    p_antes = obtener_por_id(pid_a)
    mov_id = procesar_movimiento(pid_a, "ENTRADA", 20, SUP_ID, referencia="ENT-001")
    p_despues = obtener_por_id(pid_a)
    esperado = p_antes["stock_actual"] + 20
    if p_despues["stock_actual"] == esperado and isinstance(mov_id, int):
        ok("CP-05", f"ENTRADA 20u → stock {p_antes['stock_actual']} → {p_despues['stock_actual']}, mov_id={mov_id}")
    else:
        err("CP-05", f"Esperado stock={esperado}, obtuvo={p_despues['stock_actual']}")

    # ── CP-06: SALIDA válida ──────────────────────────────────────────────
    sec("CP-06: SALIDA válida")
    p_antes = obtener_por_id(pid_a)
    mov_id2 = procesar_movimiento(pid_a, "SALIDA", 15, SUP_ID, referencia="SAL-001")
    p_despues = obtener_por_id(pid_a)
    esperado = p_antes["stock_actual"] - 15
    if p_despues["stock_actual"] == esperado:
        ok("CP-06", f"SALIDA 15u → stock {p_antes['stock_actual']} → {p_despues['stock_actual']}")
    else:
        err("CP-06", f"Esperado stock={esperado}, obtuvo={p_despues['stock_actual']}")

    # ── CP-07: DEVOLUCION válida ──────────────────────────────────────────
    sec("CP-07: DEVOLUCION válida")
    p_antes = obtener_por_id(pid_a)
    procesar_movimiento(pid_a, "DEVOLUCION", 5, SUP_ID, referencia="DEV-001")
    p_despues = obtener_por_id(pid_a)
    esperado = p_antes["stock_actual"] + 5
    if p_despues["stock_actual"] == esperado:
        ok("CP-07", f"DEVOLUCION 5u → stock {p_antes['stock_actual']} → {p_despues['stock_actual']}")
    else:
        err("CP-07", f"Esperado stock={esperado}, obtuvo={p_despues['stock_actual']}")

    # ── CP-08: AJUSTE válido (supervisor) ─────────────────────────────────
    sec("CP-08: AJUSTE válido (Supervisor)")
    procesar_movimiento(pid_a, "AJUSTE", 200, SUP_ID,
                        motivo="Conteo físico mensual",
                        supervisor_id=SUP_ID)
    p_despues = obtener_por_id(pid_a)
    if p_despues["stock_actual"] == 200:
        ok("CP-08", f"AJUSTE → stock absoluto = 200")
    else:
        err("CP-08", f"Esperado 200, obtuvo {p_despues['stock_actual']}")

    # ── CP-09: SALIDA con stock insuficiente → ValueError ─────────────────
    sec("CP-09: SALIDA con stock insuficiente")
    p = obtener_por_id(pid_a)
    try:
        procesar_movimiento(pid_a, "SALIDA", p["stock_actual"] + 9999, SUP_ID)
        err("CP-09", "Debió lanzar ValueError")
    except ValueError as e:
        if "insuficiente" in str(e).lower():
            ok("CP-09", f"ValueError correcto: {e}")
        else:
            err("CP-09", f"ValueError con mensaje inesperado: {e}")

    # ── CP-10: AJUSTE sin motivo → ValueError ─────────────────────────────
    sec("CP-10: AJUSTE sin motivo")
    try:
        procesar_movimiento(pid_a, "AJUSTE", 50, SUP_ID,
                            motivo="", supervisor_id=SUP_ID)
        err("CP-10", "Debió lanzar ValueError")
    except ValueError as e:
        ok("CP-10", f"ValueError correcto: {e}")

    # ── CP-11: AJUSTE sin supervisor_id → ValueError ──────────────────────
    sec("CP-11: AJUSTE sin supervisor_id")
    try:
        procesar_movimiento(pid_a, "AJUSTE", 50, SUP_ID,
                            motivo="Ajuste válido", supervisor_id=None)
        err("CP-11", "Debió lanzar ValueError")
    except ValueError as e:
        ok("CP-11", f"ValueError correcto: {e}")

    # ── CP-12: Cantidad negativa → ValueError ─────────────────────────────
    sec("CP-12: Cantidad negativa o cero")
    for cant in [0, -5]:
        try:
            procesar_movimiento(pid_a, "ENTRADA", cant, SUP_ID)
            err("CP-12", f"Cantidad={cant} debió lanzar ValueError")
        except ValueError as e:
            ok("CP-12", f"Cantidad={cant} → ValueError: {e}")

    # ── CP-13: Tipo inválido → ValueError ────────────────────────────────
    sec("CP-13: Tipo de movimiento inválido")
    try:
        procesar_movimiento(pid_a, "VENTA", 10, SUP_ID)
        err("CP-13", "Debió lanzar ValueError")
    except ValueError as e:
        ok("CP-13", f"ValueError correcto: {e}")

    # ── CP-14: Producto inexistente → ValueError ──────────────────────────
    sec("CP-14: Producto inexistente")
    try:
        procesar_movimiento(99999, "ENTRADA", 10, SUP_ID)
        err("CP-14", "Debió lanzar ValueError")
    except ValueError as e:
        ok("CP-14", f"ValueError correcto: {e}")

    # ── CP-15: Alerta generada al bajar de stock_minimo ───────────────────
    sec("CP-15: Alerta generada en SALIDA bajo stock mínimo")
    # pid_b tiene stock=5, minimo=10 → ya debería tener alerta o generarla ahora
    # Primero asegurar stock > minimo con una ENTRADA para partir de estado limpio
    p_b = obtener_por_id(pid_b)
    if p_b["stock_actual"] <= p_b["stock_minimo"]:
        # Reponer para poder hacer SALIDA significativa
        procesar_movimiento(pid_b, "ENTRADA", 50, SUP_ID)
    # Hacer SALIDA que deje stock < minimo
    p_b = obtener_por_id(pid_b)
    procesar_movimiento(pid_b, "SALIDA", p_b["stock_actual"] - 2, SUP_ID)
    p_b2 = obtener_por_id(pid_b)
    if existe_activa(pid_b):
        ok("CP-15", f"Alerta ACTIVA generada. Stock={p_b2['stock_actual']} <= Min={p_b2['stock_minimo']}")
    else:
        err("CP-15", f"Alerta NO generada. Stock={p_b2['stock_actual']}, Min={p_b2['stock_minimo']}")

    # ── CP-16: Alerta cerrada automáticamente en ENTRADA ─────────────────
    sec("CP-16: Alerta cerrada automáticamente por ENTRADA")
    procesar_movimiento(pid_b, "ENTRADA", 100, SUP_ID)
    p_b3 = obtener_por_id(pid_b)
    if not existe_activa(pid_b) and p_b3["stock_actual"] > p_b3["stock_minimo"]:
        ok("CP-16", f"Alerta cerrada. Stock={p_b3['stock_actual']} > Min={p_b3['stock_minimo']}")
    else:
        err("CP-16", f"Alerta sigue activa o stock insuficiente. "
                     f"Stock={p_b3['stock_actual']}, Min={p_b3['stock_minimo']}")

    # ── CP-17: ABC recalculado tras movimiento ────────────────────────────
    sec("CP-17: Clasificación ABC recalculada tras movimiento")
    # AJUSTE pid_a a 9999u * 50.00 = S/. 499,950 → valor dominante en la BD
    # pid_b queda en ~102u * 20.00 = S/. 2,040 → valor mucho menor
    procesar_movimiento(pid_a, "AJUSTE", 9999, SUP_ID,
                        motivo="Ajuste prueba ABC", supervisor_id=SUP_ID)
    from logica.logica_abc import recalcular_abc
    recalcular_abc()
    p_a = obtener_por_id(pid_a)
    p_b = obtener_por_id(pid_b)
    orden_abc = {"A": 0, "B": 1, "C": 2}
    # Verificar que:
    # 1) ABC fue asignado (no None)
    # 2) pid_a tiene mejor o igual categoría que pid_b
    if (p_a["clasificacion_abc"] in ("A","B","C") and
        p_b["clasificacion_abc"] in ("A","B","C") and
        orden_abc[p_a["clasificacion_abc"]] <= orden_abc[p_b["clasificacion_abc"]]):
        ok("CP-17", f"ABC recalculado correctamente: {SKU_A}={p_a['clasificacion_abc']} "
                    f"(val=S/.{9999*50:.0f}), {SKU_B}={p_b['clasificacion_abc']} "
                    f"(val menor)")
    else:
        err("CP-17", f"ABC inesperado: {SKU_A}={p_a['clasificacion_abc']}, "
                     f"{SKU_B}={p_b['clasificacion_abc']}")

    # ── Historial ─────────────────────────────────────────────────────────
    sec("Verificación: historial_sku registra todos los movimientos")
    hist = historial_sku(pid_a)
    if len(hist) >= 4:
        ok("HIST", f"historial_sku({SKU_A}) → {len(hist)} movimientos registrados")
    else:
        err("HIST", f"Esperaba >=4 movimientos, obtuvo {len(hist)}")

    # ── Resultado ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print(f"  OK: {ok_count}   ERRORES: {err_count}")
    if err_count == 0:
        print("  RESULTADO: MÓDULO 4 OK — listo para Módulo 5.")
        print("  Prueba visual: python main.py → Registrar Movimiento")
    else:
        print("  RESULTADO: HAY ERRORES — revisar los puntos [ERROR].")
    print("="*60)

if __name__ == "__main__":
    main()