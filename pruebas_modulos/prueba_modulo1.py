#!/usr/bin/env python3
# prueba_modulo1.py
# Verifica que la BD esté creada y que obtener_conexion() funcione.
# Ejecutar desde la raíz del proyecto: python prueba_modulo1.py
#
# Requisito previo: ejecutar giftnow_tps_schema.sql en MySQL.
#   mysql -u root -p < giftnow_tps_schema.sql

import sys
import os

# Agrega la carpeta raíz del proyecto al path para que Python
# encuentre los paquetes datos/, logica/ y ui/ sin importar
# desde qué directorio se ejecute el script.
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from datos.conexion import obtener_conexion, cerrar_conexion

TABLAS_ESPERADAS = {"usuario", "producto", "movimiento", "alerta_stock"}

def verificar_tablas(cursor):
    cursor.execute("SHOW TABLES;")
    tablas_existentes = {fila[0] for fila in cursor.fetchall()}
    faltantes = TABLAS_ESPERADAS - tablas_existentes
    if faltantes:
        print(f"  [ERROR] Tablas faltantes: {faltantes}")
        return False
    print(f"  [OK]  Tablas encontradas: {tablas_existentes}")
    return True

def verificar_supervisor(cursor):
    cursor.execute(
        "SELECT usuario_id, username, rol, activo FROM usuario "
        "WHERE username = 'supervisor';"
    )
    fila = cursor.fetchone()
    if fila is None:
        print("  [ERROR] Usuario 'supervisor' no encontrado.")
        return False
    print(f"  [OK]  Usuario supervisor: id={fila[0]}, username={fila[1]}, "
          f"rol={fila[2]}, activo={fila[3]}")
    return True

def verificar_indices(cursor):
    cursor.execute(
        "SELECT INDEX_NAME, TABLE_NAME "
        "FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = 'giftnow_tps' "
        "  AND INDEX_NAME IN ("
        "    'idx_producto_stock_code',"
        "    'idx_mov_producto_fecha',"
        "    'idx_alerta_producto_estado'"
        "  );"
    )
    indices = {fila[0] for fila in cursor.fetchall()}
    esperados = {
        "idx_producto_stock_code",
        "idx_mov_producto_fecha",
        "idx_alerta_producto_estado",
    }
    faltantes = esperados - indices
    if faltantes:
        print(f"  [ERROR] Índices faltantes: {faltantes}")
        return False
    print(f"  [OK]  Índices presentes: {indices}")
    return True

def verificar_engine_charset(cursor):
    cursor.execute(
        "SELECT TABLE_NAME, ENGINE, TABLE_COLLATION "
        "FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = 'giftnow_tps' "
        "  AND TABLE_TYPE = 'BASE TABLE';"
    )
    filas = cursor.fetchall()
    ok = True
    for nombre, engine, collation in filas:
        if engine != "InnoDB":
            print(f"  [ERROR] {nombre}: engine={engine} (esperado InnoDB)")
            ok = False
        elif "utf8mb4" not in collation:
            print(f"  [ERROR] {nombre}: collation={collation} (esperado utf8mb4)")
            ok = False
        else:
            print(f"  [OK]  {nombre}: engine={engine}, collation={collation}")
    return ok

def main():
    print("=" * 60)
    print("  PRUEBA MÓDULO 1 — Infraestructura BD — GiftNow TPS")
    print("=" * 60)

    # 1. Conexión
    print("\n[1] Probando obtener_conexion()...")
    try:
        conn = obtener_conexion()
        print(f"  [OK]  Conexión establecida. Server: {conn.get_server_info()}")
    except ConnectionError as e:
        print(f"  [FALLO] {e}")
        print("\n  Asegúrese de:")
        print("  1. Tener MySQL corriendo en localhost:3306")
        print("  2. Haber ejecutado: mysql -u root -p < giftnow_tps_schema.sql")
        print("  3. Actualizar config.py con su usuario/contraseña MySQL")
        sys.exit(1)

    cursor = conn.cursor()

    # 2. Tablas
    print("\n[2] Verificando tablas...")
    ok_tablas = verificar_tablas(cursor)

    # 3. Motor e índices
    print("\n[3] Verificando engine=InnoDB y charset=utf8mb4...")
    ok_engine = verificar_engine_charset(cursor)

    # 4. Índices
    print("\n[4] Verificando índices de optimización...")
    ok_indices = verificar_indices(cursor)

    # 5. Usuario inicial
    print("\n[5] Verificando usuario supervisor inicial...")
    ok_super = verificar_supervisor(cursor)

    # 6. Cierre
    cerrar_conexion(conn, cursor)
    print("\n[6] Conexión cerrada correctamente.")

    # Resultado
    print("\n" + "=" * 60)
    todo_ok = all([ok_tablas, ok_engine, ok_indices, ok_super])
    if todo_ok:
        print("  RESULTADO: MÓDULO 1 OK — listo para Módulo 2.")
    else:
        print("  RESULTADO: HAY ERRORES — revisar los puntos marcados [ERROR].")
    print("=" * 60)


if __name__ == "__main__":
    main()
