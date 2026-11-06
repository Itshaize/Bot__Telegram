import sqlite3

def conectar():
    return sqlite3.connect("usuarios.db")


def crear_tablas():
    db = conectar()

    db.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            password TEXT
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

    db.commit()
    db.close()


def crear_usuario(usuario, password):
    db = conectar()

    existe = db.execute(
        "SELECT * FROM usuarios WHERE usuario=?",
        (usuario,)
    ).fetchone()

    if existe:
        db.close()
        return "El usuario ya existe"

    db.execute(
        "INSERT INTO usuarios VALUES (?, ?)",
        (usuario, password)
    )

    db.commit()
    db.close()

    return "Usuario creado correctamente"


def validar_usuario(usuario, password):
    db = conectar()

    dato = db.execute(
        "SELECT * FROM usuarios WHERE usuario=? AND password=?",
        (usuario, password)
    ).fetchone()

    db.close()
    return dato is not None


def guardar_codigo(usuario, codigo, expira):
    db = conectar()

    db.execute(
        "INSERT OR REPLACE INTO codigos VALUES (?, ?, ?, ?)",
        (usuario, codigo, expira, 0)
    )

    db.commit()
    db.close()
