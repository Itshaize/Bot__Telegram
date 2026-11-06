"""SQLite: usuarios, codigos MFA e intentos fallidos."""
import hashlib
import os
import secrets
import sqlite3
import time


def hash_clave(clave, sal):
    return hashlib.pbkdf2_hmac('sha256', clave.encode(), bytes.fromhex(sal), 100_000).hex()


class BaseDatos:
    def __init__(self, ruta='mfa.db'):
        self.db = sqlite3.connect(ruta)
        self.db.row_factory = sqlite3.Row
        self.db.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY, sal TEXT NOT NULL, clave_hash TEXT NOT NULL,
            intentos INTEGER NOT NULL DEFAULT 0, bloqueado_hasta REAL NOT NULL DEFAULT 0)''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS codigos (
            usuario TEXT PRIMARY KEY, codigo_hash TEXT NOT NULL, expira REAL NOT NULL)''')
        self.db.commit()
        if not self.db.execute('SELECT 1 FROM usuarios WHERE usuario=?', ('ismael',)).fetchone():
            sal = secrets.token_hex(16)
            clave = os.getenv('MFA_DEMO_PASSWORD', '1234')
            self.db.execute('INSERT INTO usuarios(usuario, sal, clave_hash) VALUES (?, ?, ?)',
                            ('ismael', sal, hash_clave(clave, sal)))
            self.db.commit()

    def comprobar_clave(self, usuario, clave):
        fila = self.db.execute('SELECT sal, clave_hash FROM usuarios WHERE usuario=?', (usuario,)).fetchone()
        return bool(fila) and secrets.compare_digest(hash_clave(clave, fila['sal']), fila['clave_hash'])

    def bloqueado(self, usuario):
        fila = self.db.execute('SELECT bloqueado_hasta FROM usuarios WHERE usuario=?', (usuario,)).fetchone()
        return bool(fila) and time.time() < fila['bloqueado_hasta']

    def error(self, usuario):
        fila = self.db.execute('SELECT intentos FROM usuarios WHERE usuario=?', (usuario,)).fetchone()
        if not fila:
            return False
        intentos = fila['intentos'] + 1
        if intentos >= 3:
            self.db.execute('UPDATE usuarios SET intentos=0, bloqueado_hasta=? WHERE usuario=?',
                            (time.time() + 60, usuario))
            self.db.execute('DELETE FROM codigos WHERE usuario=?', (usuario,))
        else:
            self.db.execute('UPDATE usuarios SET intentos=? WHERE usuario=?', (intentos, usuario))
        self.db.commit()
        return intentos >= 3

    def reiniciar_intentos(self, usuario):
        self.db.execute('UPDATE usuarios SET intentos=0, bloqueado_hasta=0 WHERE usuario=?', (usuario,))
        self.db.commit()

    def guardar_codigo(self, usuario, codigo):
        codigo_hash = hashlib.sha256(codigo.encode()).hexdigest()
        self.db.execute('INSERT OR REPLACE INTO codigos VALUES (?, ?, ?)',
                        (usuario, codigo_hash, time.time() + 180))
        self.db.commit()

    def consultar_codigo(self, usuario):
        return self.db.execute('SELECT codigo_hash, expira FROM codigos WHERE usuario=?', (usuario,)).fetchone()

    def borrar_codigo(self, usuario):
        self.db.execute('DELETE FROM codigos WHERE usuario=?', (usuario,))
        self.db.commit()
