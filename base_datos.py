"""Almacenamiento SQLite de usuarios y codigos MFA."""
import hashlib
import hmac
import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "usuarios.db"))
ITERACIONES = 310_000


def conectar():
    return sqlite3.connect(DB_PATH, timeout=10)


def crear_tablas():
    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS codigos (
                usuario TEXT PRIMARY KEY,
                codigo TEXT,
                expira REAL,
                intentos INTEGER
            )
        """)


def _hash_password(password):
    sal = os.urandom(16)
    resumen = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${resumen.hex()}"


def crear_usuario(usuario, password):
    if not isinstance(usuario, str) or not isinstance(password, str):
        return "Datos invalidos"
    if not usuario.strip() or len(usuario) > 60 or len(password) < 8:
        return "Usuario obligatorio (max. 60) y contraseña de al menos 8 caracteres"
    try:
        with conectar() as db:
            db.execute(
                "INSERT INTO usuarios (usuario, password) VALUES (?, ?)",
                (usuario.strip(), _hash_password(password)),
            )
        return "Usuario creado correctamente"
    except sqlite3.IntegrityError:
        return "El usuario ya existe"


def validar_usuario(usuario, password):
    if not isinstance(usuario, str) or not isinstance(password, str):
        return False
    with conectar() as db:
        fila = db.execute(
            "SELECT password FROM usuarios WHERE usuario=?", (usuario,)
        ).fetchone()
        if not fila:
            return False
        almacenada = fila[0]
        if almacenada.startswith("pbkdf2_sha256$"):
            try:
                _, iteraciones, sal, esperado = almacenada.split("$")
                actual = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"),
                    bytes.fromhex(sal), int(iteraciones)
                )
                return hmac.compare_digest(actual, bytes.fromhex(esperado))
            except (ValueError, TypeError):
                return False
        # Compatibilidad con las contraseñas antiguas, migradas tras el login.
        if hmac.compare_digest(almacenada, password):
            db.execute(
                "UPDATE usuarios SET password=? WHERE usuario=?",
                (_hash_password(password), usuario),
            )
            return True
        return False


def guardar_codigo(usuario, codigo, expira):
    with conectar() as db:
        db.execute(
            "INSERT OR REPLACE INTO codigos (usuario, codigo, expira, intentos) "
            "VALUES (?, ?, ?, 0)",
            (usuario, codigo, expira),
        )
