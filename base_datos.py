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

    db.execute(
        "INSERT OR IGNORE INTO usuarios VALUES (?, ?)",
        ("ismael", "1234")
    )

    db.commit()
    db.close()


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
