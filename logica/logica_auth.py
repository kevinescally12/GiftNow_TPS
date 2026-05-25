# logica/logica_auth.py
# Capa de negocio — autenticación de usuarios.
# Sin SQL directo ni widgets Tkinter.

import hashlib
from datos.datos_usuario import buscar_por_username


def autenticar_usuario(username: str, password: str) -> dict | None:
    """Hashea password con SHA-256, consulta tabla usuario.
    Retorna dict del usuario autenticado o None si falla.

    El dict retornado contiene:
        usuario_id, nombre_completo, username, rol, activo, fecha_registro
    (password_hash NO se incluye en el retorno por seguridad).
    """
    if not username or not username.strip():
        return None
    if not password:
        return None

    # SHA-256 del password en texto plano → hexdigest (igual que SHA2(...,256) de MySQL)
    hash_ingresado = hashlib.sha256(password.encode("utf-8")).hexdigest()

    usuario = buscar_por_username(username.strip())
    if usuario is None:
        return None

    if usuario["password_hash"] != hash_ingresado:
        return None

    # Retornar sin exponer el hash
    return {
        "usuario_id":      usuario["usuario_id"],
        "nombre_completo": usuario["nombre_completo"],
        "username":        usuario["username"],
        "rol":             usuario["rol"],
        "activo":          usuario["activo"],
        "fecha_registro":  usuario["fecha_registro"],
    }
