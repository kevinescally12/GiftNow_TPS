#!/usr/bin/env python3
# prueba_modulo3.py
# Prueba de lógica de autenticación (CP-01 a CP-04).
# No lanza ventanas — prueba solo la capa de lógica.
# Ejecutar: python prueba_modulo3.py

import sys
import os
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logica.logica_auth import autenticar_usuario
from datos.datos_usuario import buscar_por_username
from datos.conexion import obtener_conexion, cerrar_conexion
import hashlib

ok_count  = 0
err_count = 0

def ok(cp, msg):
    global ok_count
    ok_count += 1
    print(f"  [OK]  {cp}: {msg}")

def err(cp, msg):
    global err_count
    err_count += 1
    print(f"  [ERROR] {cp}: {msg}")

def seccion(titulo):
    print(f"\n{'─'*60}")
    print(f"  {titulo}")
    print(f"{'─'*60}")

# ── Utilidades de setup ──────────────────────────────────────────────────────

def crear_usuario_almacenero():
    """Crea un usuario ALMACENERO de prueba si no existe."""
    conn = None
    cur  = None
    try:
        conn = obtener_conexion()
        cur  = conn.cursor()
        hash_pw = hashlib.sha256("test1234".encode()).hexdigest()
        cur.execute(
            "INSERT IGNORE INTO usuario "
            "(nombre_completo, username, password_hash, rol) "
            "VALUES ('Almacenero Test', 'almacenero_test', %s, 'ALMACENERO');",
            (hash_pw,)
        )
        conn.commit()
    finally:
        cerrar_conexion(conn, cur)

def desactivar_usuario(username):
    conn = None
    cur  = None
    try:
        conn = obtener_conexion()
        cur  = conn.cursor()
        cur.execute("UPDATE usuario SET activo = 0 WHERE username = %s;", (username,))
        conn.commit()
    finally:
        cerrar_conexion(conn, cur)

def reactivar_usuario(username):
    conn = None
    cur  = None
    try:
        conn = obtener_conexion()
        cur  = conn.cursor()
        cur.execute("UPDATE usuario SET activo = 1 WHERE username = %s;", (username,))
        conn.commit()
    finally:
        cerrar_conexion(conn, cur)

# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  PRUEBA MÓDULO 3 — Autenticación — GiftNow TPS")
    print("  (CP-01 a CP-04 — prueba de lógica sin UI)")
    print("=" * 60)

    crear_usuario_almacenero()

    # ── CP-01: Login válido SUPERVISOR ────────────────────────────────────
    seccion("CP-01: Login válido — SUPERVISOR")
    u = autenticar_usuario("supervisor", "cambiar1234")
    if u and u["rol"] == "SUPERVISOR" and "password_hash" not in u:
        ok("CP-01", f"autenticar_usuario OK → rol={u['rol']}, "
                    f"nombre='{u['nombre_completo']}'")
        ok("CP-01", "password_hash NO está en el dict retornado (seguridad OK)")
    else:
        err("CP-01", f"Resultado inesperado: {u}")

    # ── CP-02: Login válido ALMACENERO ────────────────────────────────────
    seccion("CP-02: Login válido — ALMACENERO")
    u2 = autenticar_usuario("almacenero_test", "test1234")
    if u2 and u2["rol"] == "ALMACENERO":
        ok("CP-02", f"autenticar_usuario OK → rol={u2['rol']}, "
                    f"nombre='{u2['nombre_completo']}'")
    else:
        err("CP-02", f"Resultado inesperado: {u2}")

    # ── CP-03: Password incorrecto ────────────────────────────────────────
    seccion("CP-03: Password incorrecto → None")
    u3 = autenticar_usuario("supervisor", "password_errado")
    if u3 is None:
        ok("CP-03", "autenticar_usuario('supervisor', 'password_errado') → None")
    else:
        err("CP-03", f"Esperaba None, obtuvo: {u3}")

    # ── CP-03b: Usuario inexistente ───────────────────────────────────────
    seccion("CP-03b: Usuario inexistente → None")
    u3b = autenticar_usuario("no_existe_xyz", "cualquier")
    if u3b is None:
        ok("CP-03b", "autenticar_usuario('no_existe_xyz', ...) → None")
    else:
        err("CP-03b", f"Esperaba None, obtuvo: {u3b}")

    # ── CP-03c: Username vacío ────────────────────────────────────────────
    seccion("CP-03c: Username vacío → None")
    u3c = autenticar_usuario("", "cambiar1234")
    if u3c is None:
        ok("CP-03c", "autenticar_usuario('', ...) → None")
    else:
        err("CP-03c", f"Esperaba None, obtuvo: {u3c}")

    # ── CP-04: Usuario inactivo → None ────────────────────────────────────
    seccion("CP-04: Usuario inactivo → None")
    desactivar_usuario("almacenero_test")
    u4 = autenticar_usuario("almacenero_test", "test1234")
    reactivar_usuario("almacenero_test")   # restaurar para pruebas futuras
    if u4 is None:
        ok("CP-04", "Usuario inactivo → autenticar_usuario retorna None")
    else:
        err("CP-04", f"Esperaba None para usuario inactivo, obtuvo: {u4}")

    # ── Verificación de consistencia del hash SHA-256 ──────────────────────
    seccion("Verificación: SHA-256 Python == SHA2 MySQL")
    hash_py    = hashlib.sha256("cambiar1234".encode()).hexdigest()
    u_raw      = buscar_por_username("supervisor")
    hash_mysql = u_raw["password_hash"] if u_raw else None
    if hash_py == hash_mysql:
        ok("HASH", f"SHA-256 Python == SHA2 MySQL: {hash_py[:20]}...")
    else:
        err("HASH", f"Mismatch!\n  Python: {hash_py}\n  MySQL:  {hash_mysql}")

    # ── Resultado ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  OK: {ok_count}   ERRORES: {err_count}")
    if err_count == 0:
        print("  RESULTADO: MÓDULO 3 OK — ejecuta 'python main.py' para probar la UI.")
        print("\n  Credenciales de prueba:")
        print("    Supervisor  → usuario: supervisor    / pass: cambiar1234")
        print("    Almacenero  → usuario: almacenero_test / pass: test1234")
    else:
        print("  RESULTADO: HAY ERRORES — revisar los puntos marcados [ERROR].")
    print("=" * 60)


if __name__ == "__main__":
    main()
