#!/usr/bin/env python3
# importar_csv.py
# Importa el CSV histórico a giftnow_tps usando procesamiento por lotes.
# Una sola conexión por lote — no agota puertos MySQL en Windows.
#
# Ejecutar: python importar_csv.py
# Re-ejecutable: omite filas ya importadas.

import sys, os, csv, time
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Configuración ────────────────────────────────────────────────────────────
CSV_NOMBRE   = "online_retail_II.csv"   # cambia a online_retail_II.csv si quieres el completo
BATCH_SIZE   = 200    # filas por lote (una conexión por lote)
USUARIO_ID   = 1      # supervisor
STOCK_MIN    = 5      # stock mínimo por defecto
PAUSA_LOTES  = 0.05   # segundos entre lotes (evita saturar puertos)
# ─────────────────────────────────────────────────────────────────────────────

CSV_PATH = os.path.join(ROOT, CSV_NOMBRE)

from datos.conexion import obtener_conexion, cerrar_conexion
from logica.logica_abc import recalcular_abc


# ── Operaciones en lote (1 conexión por lote) ────────────────────────────────

def obtener_skus_existentes(conn) -> dict:
    """Retorna {stock_code: producto_id} de todos los productos activos."""
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT producto_id, stock_code FROM producto WHERE activo=1;")
    result = {r["stock_code"]: r["producto_id"] for r in cur.fetchall()}
    cur.close()
    return result

def obtener_refs_importadas(conn) -> set:
    """Retorna set de referencias 'IMP-{invoice}-{sku}' ya en movimiento."""
    cur = conn.cursor()
    cur.execute(
        "SELECT referencia FROM movimiento "
        "WHERE referencia LIKE 'IMP-%' AND referencia IS NOT NULL;"
    )
    result = {r[0] for r in cur.fetchall()}
    cur.close()
    return result

def insertar_productos_lote(conn, nuevos: list) -> dict:
    """
    INSERT IGNORE de productos nuevos.
    nuevos = [{"stock_code","descripcion","precio"}, ...]
    Retorna {stock_code: producto_id} de los recién insertados.
    """
    if not nuevos:
        return {}
    cur = conn.cursor()
    cur.executemany(
        "INSERT IGNORE INTO producto "
        "(stock_code, descripcion, stock_actual, stock_minimo, "
        " precio_unitario, clasificacion_abc, usuario_alta_id) "
        "VALUES (%s, %s, 0, %s, %s, 'C', %s);",
        [(p["stock_code"], p["descripcion"], STOCK_MIN,
          p["precio"], USUARIO_ID) for p in nuevos]
    )
    conn.commit()
    # Recuperar IDs de los recién insertados
    codes = tuple(p["stock_code"] for p in nuevos)
    if len(codes) == 1:
        cur.execute(
            "SELECT producto_id, stock_code FROM producto WHERE stock_code=%s;",
            (codes[0],))
    else:
        cur.execute(
            f"SELECT producto_id, stock_code FROM producto "
            f"WHERE stock_code IN {codes};"
        )
    result = {r[1]: r[0] for r in cur.fetchall()}
    cur.close()
    return result

def procesar_lote_movimientos(conn, movimientos: list,
                               skus_map: dict) -> tuple:
    """
    Procesa un lote de movimientos en una sola transacción.
    movimientos = [{"stock_code","cantidad","invoice","precio"}, ...]
    Retorna (creados, omitidos).
    """
    creados = omitidos = 0
    cur = conn.cursor()
    try:
        conn.start_transaction()
        for m in movimientos:
            pid        = skus_map.get(m["stock_code"])
            referencia = f"IMP-{m['invoice']}-{m['stock_code']}"

            if pid is None:
                omitidos += 1
                continue

            # Obtener stock actual (dentro de la transacción)
            cur.execute(
                "SELECT stock_actual, stock_minimo FROM producto "
                "WHERE producto_id=%s FOR UPDATE;", (pid,))
            fila = cur.fetchone()
            if fila is None:
                omitidos += 1
                continue

            stock_antes   = fila[0]
            stock_despues = stock_antes + m["cantidad"]

            # Insertar movimiento
            cur.execute(
                "INSERT INTO movimiento "
                "(producto_id, tipo_movimiento, cantidad, "
                " stock_antes, stock_despues, usuario_id, "
                " referencia, motivo, aprobado) "
                "VALUES (%s,'ENTRADA',%s,%s,%s,%s,%s,%s,0);",
                (pid, m["cantidad"], stock_antes, stock_despues,
                 USUARIO_ID, referencia,
                 "Importación histórica CSV")
            )
            mov_id = cur.lastrowid

            # Actualizar stock
            cur.execute(
                "UPDATE producto SET stock_actual=%s WHERE producto_id=%s;",
                (stock_despues, pid)
            )

            # Alerta si stock <= minimo
            cur.execute(
                "SELECT COUNT(*) FROM alerta_stock "
                "WHERE producto_id=%s AND estado='ACTIVA';", (pid,))
            ya_alerta = cur.fetchone()[0]
            if stock_despues <= fila[1] and not ya_alerta:
                cur.execute(
                    "INSERT INTO alerta_stock "
                    "(producto_id, stock_al_activar, stock_minimo_ref, "
                    " movimiento_id) VALUES (%s,%s,%s,%s);",
                    (pid, stock_despues, fila[1], mov_id)
                )

            creados += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        raise e

    cur.close()
    return creados, omitidos


# ── Main ─────────────────────────────────────────────────────────────────────

def importar():
    print("=" * 64)
    print("  IMPORTACIÓN CSV → giftnow_tps  (modo lotes)")
    print(f"  Archivo : {CSV_NOMBRE}")
    print(f"  Lote    : {BATCH_SIZE} filas / conexión")
    print("=" * 64)

    if not os.path.exists(CSV_PATH):
        print(f"\n[ERROR] Archivo no encontrado:\n  {CSV_PATH}")
        sys.exit(1)

    # Leer CSV completo en memoria
    print("\n  Leyendo CSV...", end=" ", flush=True)
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    print(f"{len(filas):,} filas.")

    # ── Pre-análisis: separar válidas de omitidas ──────────────────────
    validas     = []
    omit_previo = 0
    for fila in filas:
        invoice = str(fila["Invoice"]).strip()
        sku     = fila["StockCode"].strip().upper()
        desc    = (fila.get("Description") or f"SKU {sku}").strip()
        try:
            cantidad = int(fila["Quantity"])
            precio   = float(fila["Price"] or 0)
        except ValueError:
            omit_previo += 1
            continue
        if cantidad <= 0:
            omit_previo += 1
            continue
        if precio <= 0:
            precio = 0.01
        validas.append({"invoice": invoice, "stock_code": sku,
                         "descripcion": desc, "cantidad": cantidad,
                         "precio": precio})

    print(f"  Filas válidas: {len(validas):,}  |  "
          f"Omitidas (qty≤0 / inválidas): {omit_previo:,}")

    # ── Abrir UNA conexión para el estado inicial ──────────────────────
    print("\n  Conectando a MySQL...", end=" ", flush=True)
    conn_init = obtener_conexion()
    print("OK")

    skus_map  = obtener_skus_existentes(conn_init)
    refs_ya   = obtener_refs_importadas(conn_init)
    cerrar_conexion(conn_init)

    print(f"  SKUs en BD: {len(skus_map):,}  |  "
          f"Movimientos ya importados: {len(refs_ya):,}")

    # ── Filtrar ya importados ─────────────────────────────────────────
    pendientes = [
        v for v in validas
        if f"IMP-{v['invoice']}-{v['stock_code']}" not in refs_ya
    ]
    ya_import = len(validas) - len(pendientes)
    print(f"  Ya importados: {ya_import:,}  |  "
          f"Pendientes: {len(pendientes):,}")

    if not pendientes:
        print("\n  Todo ya fue importado. Nada que hacer.")
        return

    # ── Identificar SKUs nuevos ───────────────────────────────────────
    skus_pendientes = {v["stock_code"] for v in pendientes}
    skus_nuevos_set = skus_pendientes - set(skus_map.keys())

    if skus_nuevos_set:
        # Tomar precio y desc del primer registro de cada SKU nuevo
        sku_info = {}
        for v in pendientes:
            if v["stock_code"] in skus_nuevos_set and \
               v["stock_code"] not in sku_info:
                sku_info[v["stock_code"]] = {
                    "stock_code":  v["stock_code"],
                    "descripcion": v["descripcion"],
                    "precio":      v["precio"],
                }

        print(f"\n  Insertando {len(sku_info):,} SKUs nuevos...",
              end=" ", flush=True)
        conn_sku = obtener_conexion()
        nuevos_ids = insertar_productos_lote(conn_sku, list(sku_info.values()))
        skus_map.update(nuevos_ids)
        cerrar_conexion(conn_sku)
        print(f"OK — {len(nuevos_ids):,} insertados.")

    # ── Procesar movimientos en lotes ─────────────────────────────────
    total_lotes  = (len(pendientes) + BATCH_SIZE - 1) // BATCH_SIZE
    total_creados = 0
    total_errores = 0
    t_inicio = time.time()

    print(f"\n  Procesando {len(pendientes):,} movimientos "
          f"en {total_lotes:,} lotes de {BATCH_SIZE}...\n")

    for n_lote in range(total_lotes):
        inicio = n_lote * BATCH_SIZE
        lote   = pendientes[inicio: inicio + BATCH_SIZE]

        conn_lote = None
        try:
            conn_lote = obtener_conexion()
            creados, omitidos = procesar_lote_movimientos(
                conn_lote, lote, skus_map)
            total_creados += creados
            fila_actual    = inicio + len(lote)
            pct            = fila_actual / len(pendientes) * 100
            elapsed        = time.time() - t_inicio
            vel            = fila_actual / elapsed if elapsed > 0 else 0
            print(f"  Lote {n_lote+1:>4}/{total_lotes}  "
                  f"filas {inicio+1:>7}–{fila_actual:<7}  "
                  f"creados: {creados:>3}  "
                  f"{pct:5.1f}%  "
                  f"{vel:6.0f} filas/s")
        except Exception as e:
            total_errores += 1
            print(f"  [ERROR] Lote {n_lote+1}: {e}")
        finally:
            if conn_lote:
                cerrar_conexion(conn_lote)

        if PAUSA_LOTES > 0:
            time.sleep(PAUSA_LOTES)

    # ── Recalcular ABC ────────────────────────────────────────────────
    print("\n  Recalculando clasificación ABC...", end=" ", flush=True)
    conn_abc = obtener_conexion()
    # ABC directo en SQL para no abrir múltiples conexiones
    cur_abc = conn_abc.cursor(dictionary=True)
    cur_abc.execute(
        "SELECT producto_id, stock_actual * precio_unitario AS valor "
        "FROM producto WHERE activo=1 ORDER BY valor DESC;"
    )
    productos = cur_abc.fetchall()
    valor_global = sum(float(p["valor"]) for p in productos)

    if valor_global > 0:
        acum = 0.0
        cur_upd = conn_abc.cursor()
        for p in productos:
            acum += float(p["valor"])
            pct   = acum / valor_global
            cat   = "A" if pct <= 0.70 else ("B" if pct <= 0.90 else "C")
            cur_upd.execute(
                "UPDATE producto SET clasificacion_abc=%s "
                "WHERE producto_id=%s;",
                (cat, p["producto_id"])
            )
        conn_abc.commit()
        cur_upd.close()

    cur_abc.close()
    cerrar_conexion(conn_abc)
    print("OK")

    # ── Resumen final ─────────────────────────────────────────────────
    elapsed_total = time.time() - t_inicio
    print("\n" + "=" * 64)
    print("  RESUMEN")
    print(f"  Filas en CSV:            {len(filas):>10,}")
    print(f"  Omitidas (qty≤0/error):  {omit_previo:>10,}")
    print(f"  Ya importadas antes:     {ya_import:>10,}")
    print(f"  Movimientos creados:     {total_creados:>10,}")
    print(f"  Lotes con error:         {total_errores:>10,}")
    print(f"  Tiempo total:            {elapsed_total:>9.1f}s")
    if total_errores == 0:
        print("\n  Datos históricos cargados.")
        print("  python main.py → Reportes del Almacén")
    else:
        print(f"\n  Hubo {total_errores} lote(s) con error.")
        print("  Vuelve a ejecutar el script (re-ejecutable).")
    print("=" * 64)


if __name__ == "__main__":
    importar()
