#!/usr/bin/env python3
# importar_csv.py — versión optimizada
#
# Flujo de tipos:
#   Quantity > 0  →  SALIDA     (ventas / salidas del almacén)
#   Quantity < 0  →  DEVOLUCION (devoluciones al almacén)
#   Por SKU se inserta una ENTRADA inicial = total_vendido + buffer
#   para que el stock nunca quede negativo.
#
# Optimizaciones:
#   - Una sola conexión MySQL durante todo el proceso
#   - Stock calculado en Python (sin SELECT por fila)
#   - Bulk INSERT con executemany en lotes de 2 000
#   - UPDATE de stocks en un solo batch al final
#   - Alertas generadas con una única INSERT … SELECT
#
# Ejecutar: python importar_csv.py
# Re-ejecutable: omite filas ya importadas (IMP-* y ENT-INICIAL-*).

import sys, os, csv, time
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CSV_NOMBRE = "online_retail_II.csv"
BATCH_SIZE = 2000   # filas por commit
USUARIO_ID = 1      # supervisor que firma la importación
STOCK_MIN  = 5      # stock mínimo para productos nuevos

CSV_PATH = os.path.join(ROOT, CSV_NOMBRE)

from datos.conexion import obtener_conexion, cerrar_conexion

SQL_INS = (
    "INSERT INTO movimiento "
    "(producto_id, tipo_movimiento, cantidad, stock_antes, stock_despues, "
    " usuario_id, referencia, motivo, fecha_hora, aprobado) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0);"
)


def _in_clause(cur, sql_template: str, values: tuple):
    placeholders = ", ".join(["%s"] * len(values))
    cur.execute(sql_template.replace("__IN__", placeholders), values)


def _bulk_insert(cur, conn, movs: list, label: str):
    """Inserta una lista de tuplas en lotes y muestra progreso."""
    total_lotes = (len(movs) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n  {label}: {len(movs):,} registros en {total_lotes:,} lotes...\n")
    t = time.time()
    creados = 0
    for n in range(total_lotes):
        lote = movs[n * BATCH_SIZE:(n + 1) * BATCH_SIZE]
        cur.executemany(SQL_INS, lote)
        conn.commit()
        creados += len(lote)
        pct = creados / len(movs) * 100
        vel = creados / max(time.time() - t, 0.001)
        print(f"  Lote {n+1:>4}/{total_lotes}  "
              f"insertados: {creados:>8,}  {pct:5.1f}%  {vel:6.0f}/s")
    return creados


def importar():
    print("=" * 64)
    print("  IMPORTACIÓN CSV → giftnow_tps  (optimizado)")
    print(f"  Archivo : {CSV_NOMBRE}   Lote: {BATCH_SIZE}")
    print("=" * 64)

    if not os.path.exists(CSV_PATH):
        print(f"\n[ERROR] Archivo no encontrado:\n  {CSV_PATH}")
        sys.exit(1)

    # ── 1. Leer y parsear CSV ─────────────────────────────────────────
    print("\n  Leyendo CSV...", end=" ", flush=True)
    t0 = time.time()
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    print(f"{len(filas):,} filas  ({time.time()-t0:.1f}s)")

    validas, omitidas = [], 0
    for fila in filas:
        invoice = str(fila["Invoice"]).strip()
        sku     = fila["StockCode"].strip().upper()
        desc    = (fila.get("Description") or f"SKU {sku}").strip()
        fecha   = fila.get("InvoiceDate", "").strip() or None
        try:
            cantidad = int(fila["Quantity"])
            precio   = float(fila["Price"] or 0)
        except ValueError:
            omitidas += 1
            continue
        if cantidad == 0:
            omitidas += 1
            continue
        if precio <= 0:
            precio = 0.01

        tipo = "SALIDA" if cantidad > 0 else "DEVOLUCION"
        validas.append({
            "invoice":     invoice,
            "stock_code":  sku,
            "descripcion": desc,
            "cantidad":    abs(cantidad),
            "precio":      precio,
            "tipo":        tipo,
            "fecha":       fecha,
        })

    n_sal = sum(1 for v in validas if v["tipo"] == "SALIDA")
    n_dev = sum(1 for v in validas if v["tipo"] == "DEVOLUCION")
    print(f"  SALIDA: {n_sal:,}  DEVOLUCION: {n_dev:,}  Omitidas: {omitidas:,}")

    # ── 2. Conexión única ─────────────────────────────────────────────
    print("\n  Conectando...", end=" ", flush=True)
    conn = obtener_conexion()
    cur  = conn.cursor()
    print("OK")

    # ── 3. Estado inicial ─────────────────────────────────────────────
    cur.execute(
        "SELECT producto_id, stock_code, stock_actual "
        "FROM producto WHERE activo=1;"
    )
    skus_map = {
        r[1]: {"id": r[0], "stock": int(r[2])}
        for r in cur.fetchall()
    }

    cur.execute(
        "SELECT referencia FROM movimiento "
        "WHERE referencia LIKE 'IMP-%' AND referencia IS NOT NULL;"
    )
    refs_ya = {r[0] for r in cur.fetchall()}

    cur.execute(
        "SELECT referencia FROM movimiento "
        "WHERE referencia LIKE 'ENT-INICIAL-%';"
    )
    ent_iniciales_ya = {r[0] for r in cur.fetchall()}

    print(f"  SKUs en BD: {len(skus_map):,}  |  "
          f"IMP ya importados: {len(refs_ya):,}  |  "
          f"ENT iniciales: {len(ent_iniciales_ya):,}")

    # ── 4. Filtrar ya importados ──────────────────────────────────────
    pendientes = [
        v for v in validas
        if f"IMP-{v['invoice']}-{v['stock_code']}" not in refs_ya
    ]
    ya_import = len(validas) - len(pendientes)
    print(f"  Ya importados: {ya_import:,}  |  Pendientes: {len(pendientes):,}")

    hay_pendientes = bool(pendientes)

    # ── 5. Insertar SKUs nuevos (bulk) ────────────────────────────────
    if hay_pendientes:
        skus_nuevos = {v["stock_code"] for v in pendientes} - set(skus_map)
        if skus_nuevos:
            sku_info = {}
            for v in pendientes:
                if v["stock_code"] in skus_nuevos and v["stock_code"] not in sku_info:
                    sku_info[v["stock_code"]] = (
                        v["stock_code"], v["descripcion"],
                        STOCK_MIN, v["precio"], USUARIO_ID
                    )
            print(f"\n  Insertando {len(sku_info):,} SKUs nuevos...", end=" ", flush=True)
            cur.executemany(
                "INSERT IGNORE INTO producto "
                "(stock_code, descripcion, stock_actual, stock_minimo, "
                " precio_unitario, clasificacion_abc, usuario_alta_id) "
                "VALUES (%s, %s, 0, %s, %s, 'C', %s);",
                list(sku_info.values())
            )
            conn.commit()
            codes = tuple(sku_info.keys())
            _in_clause(
                cur,
                "SELECT producto_id, stock_code, stock_actual "
                "FROM producto WHERE stock_code IN (__IN__);",
                codes
            )
            for r in cur.fetchall():
                skus_map[r[1]] = {"id": r[0], "stock": int(r[2])}
            print("OK")

    # ── 5.5. ENTRADA inicial por SKU ──────────────────────────────────
    # Cada SKU recibe una ENTRADA = total_vendido_en_csv + STOCK_MIN
    # para que nunca haya stock negativo. Se fecha antes del primer registro.
    total_vendido = defaultdict(int)
    for v in validas:
        if v["tipo"] == "SALIDA":
            total_vendido[v["stock_code"]] += v["cantidad"]

    # Todos los SKUs del CSV (incluyendo los que solo tienen devoluciones)
    todos_skus_csv = {v["stock_code"] for v in validas}

    ent_iniciales = []
    for sku in todos_skus_csv:
        ref = f"ENT-INICIAL-{sku}"
        if ref in ent_iniciales_ya:
            continue        # ya insertada en una ejecución anterior
        if sku not in skus_map:
            continue        # SKU sin producto en BD (no debería ocurrir)
        pid         = skus_map[sku]["id"]
        stock_antes = skus_map[sku]["stock"]
        cantidad    = total_vendido.get(sku, 0) + STOCK_MIN
        stock_desp  = stock_antes + cantidad
        # Actualizar en memoria para que el paso 6 arranque desde aquí
        skus_map[sku]["stock"] = stock_desp
        ent_iniciales.append((
            pid, "ENTRADA", cantidad,
            stock_antes, stock_desp,
            USUARIO_ID, ref,
            "Stock inicial — importación histórica",
            "2009-11-30 00:00:00",  # fecha anterior a cualquier venta del CSV
        ))

    n_ent_inicial = 0
    if ent_iniciales:
        n_ent_inicial = _bulk_insert(cur, conn, ent_iniciales,
                                     "ENTRADAs iniciales")
    else:
        print("\n  ENTRADAs iniciales: ya existen, se omiten.")

    if not hay_pendientes and not ent_iniciales:
        print("\n  Todo ya fue importado. Nada que hacer.")
        cerrar_conexion(conn, cur)
        return

    # ── 6. Calcular stock acumulado en Python ─────────────────────────
    pendientes.sort(key=lambda x: x["fecha"] or "")
    stock_vivo   = {sku: info["stock"] for sku, info in skus_map.items()}
    movs, omitidos_sku = [], 0

    for v in pendientes:
        info = skus_map.get(v["stock_code"])
        if info is None:
            omitidos_sku += 1
            continue
        pid        = info["id"]
        referencia = f"IMP-{v['invoice']}-{v['stock_code']}"
        stock_antes = stock_vivo.get(v["stock_code"], 0)

        if v["tipo"] == "SALIDA":
            stock_desp = stock_antes - v["cantidad"]
        else:
            stock_desp = stock_antes + v["cantidad"]

        stock_vivo[v["stock_code"]] = stock_desp
        movs.append((
            pid, v["tipo"], v["cantidad"],
            stock_antes, stock_desp,
            USUARIO_ID, referencia,
            "Importación histórica CSV",
            v["fecha"],
        ))

    print(f"\n  Movimientos SALIDA/DEVOLUCION a insertar: {len(movs):,}  "
          f"(omitidos sin SKU: {omitidos_sku})")

    # ── 7. Bulk INSERT movimientos ────────────────────────────────────
    n_mov = 0
    if movs:
        n_mov = _bulk_insert(cur, conn, movs, "SALIDA / DEVOLUCION")

    # ── 8. Bulk UPDATE stocks finales ─────────────────────────────────
    print("\n  Actualizando stocks finales...", end=" ", flush=True)
    updates = [
        (stock_vivo[sku], skus_map[sku]["id"])
        for sku in stock_vivo if sku in skus_map
    ]
    cur.executemany(
        "UPDATE producto SET stock_actual=%s WHERE producto_id=%s;",
        updates
    )
    conn.commit()
    print(f"OK — {len(updates):,} productos actualizados")

    # ── 9. Alertas en una sola INSERT … SELECT ────────────────────────
    print("  Generando alertas de stock bajo...", end=" ", flush=True)
    cur.execute(
        "INSERT INTO alerta_stock "
        "  (producto_id, stock_al_activar, stock_minimo_ref, movimiento_id) "
        "SELECT p.producto_id, p.stock_actual, p.stock_minimo, ult.movimiento_id "
        "FROM   producto p "
        "INNER JOIN ( "
        "    SELECT producto_id, MAX(movimiento_id) AS movimiento_id "
        "    FROM   movimiento "
        "    GROUP BY producto_id "
        ") ult ON ult.producto_id = p.producto_id "
        "LEFT JOIN alerta_stock a "
        "       ON  a.producto_id = p.producto_id "
        "       AND a.estado = 'ACTIVA' "
        "WHERE  p.activo = 1 "
        "  AND  p.stock_actual <= p.stock_minimo "
        "  AND  a.alerta_id IS NULL;"
    )
    alertas = cur.rowcount
    conn.commit()
    print(f"OK — {alertas:,} alertas generadas")

    # ── 10. Recalcular ABC ────────────────────────────────────────────
    print("  Recalculando clasificación ABC...", end=" ", flush=True)
    cur.execute(
        "SELECT producto_id, "
        "       CAST(stock_actual * precio_unitario AS DECIMAL(20,4)) AS valor "
        "FROM   producto WHERE activo=1 ORDER BY valor DESC;"
    )
    productos    = cur.fetchall()
    valor_global = sum(float(r[1]) for r in productos)

    if valor_global > 0:
        acum, batch_abc = 0.0, []
        for r in productos:
            acum += float(r[1])
            pct   = acum / valor_global
            cat   = "A" if pct <= 0.70 else ("B" if pct <= 0.90 else "C")
            batch_abc.append((cat, r[0]))
        cur.executemany(
            "UPDATE producto SET clasificacion_abc=%s WHERE producto_id=%s;",
            batch_abc
        )
        conn.commit()
    print("OK")

    cerrar_conexion(conn, cur)

    elapsed = time.time() - t0
    n_sal_ins = sum(1 for m in movs if m[1] == "SALIDA")
    n_dev_ins = sum(1 for m in movs if m[1] == "DEVOLUCION")

    print("\n" + "=" * 64)
    print("  RESUMEN")
    print(f"  Filas en CSV:             {len(filas):>10,}")
    print(f"  Omitidas (qty=0/error):   {omitidas:>10,}")
    print(f"  Ya importadas antes:      {ya_import:>10,}")
    print(f"  ENTRADAs iniciales:       {n_ent_inicial:>10,}")
    print(f"  Movimientos creados:      {n_mov:>10,}")
    print(f"    └─ SALIDA:              {n_sal_ins:>10,}")
    print(f"    └─ DEVOLUCION:          {n_dev_ins:>10,}")
    print(f"  Alertas generadas:        {alertas:>10,}")
    print(f"  Tiempo total:             {elapsed:>9.1f}s")
    print("  python main.py  →  Reportes del Almacén")
    print("=" * 64)


if __name__ == "__main__":
    importar()
