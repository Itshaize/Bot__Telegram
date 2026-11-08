"""Servidor Pyro4 para clientes de la red local o una VPN privada."""
import os
import random
import sqlite3
import threading
import time

import Pyro4

from base_datos import crear_tablas, crear_usuario, validar_usuario, guardar_codigo, conectar
from telegram_bot import enviar_codigo

# Se usa un puerto fijo y un identificador conocido, sin Name Server.
HOST = os.getenv("SERVER_BIND_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", "50000"))
OBJECT_ID = "autenticacion"


@Pyro4.expose
class Servidor:
    def __init__(self):
        crear_tablas()
        self.bloqueados = {}
        self.lock = threading.RLock()

    def registrar_usuario(self, usuario, password):
        return crear_usuario(usuario, password)

    def iniciar_sesion(self, usuario, password):
        with self.lock:
            if self.bloqueados.get(usuario, 0) > time.time():
                return "Usuario bloqueado"

            if not validar_usuario(usuario, password):
                return "Usuario o contraseña incorrectos"

            codigo = f"{random.SystemRandom().randint(0, 999999):06d}"
            expira = time.time() + 180
            # Registrar antes de enviar evita inconsistencias entre clientes.
            guardar_codigo(usuario, codigo, expira)

            if not enviar_codigo(usuario, codigo):
                with conectar() as db:
                    db.execute("DELETE FROM codigos WHERE usuario=?", (usuario,))
                return "No se pudo enviar el codigo"

            return "Codigo enviado a Telegram"

    def verificar_codigo_mfa(self, usuario, codigo):
        with self.lock:
            if self.bloqueados.get(usuario, 0) > time.time():
                return "Usuario bloqueado"

            with conectar() as db:
                dato = db.execute(
                    "SELECT codigo, expira, intentos FROM codigos WHERE usuario=?",
                    (usuario,),
                ).fetchone()

                if dato is None:
                    return "No existe un codigo"

                codigo_guardado, expira, intentos = dato
                if time.time() > expira:
                    db.execute("DELETE FROM codigos WHERE usuario=?", (usuario,))
                    return "Codigo expirado"

                if not isinstance(codigo, str) or not __import__("hmac").compare_digest(codigo, codigo_guardado):
                    intentos += 1
                    if intentos >= 3:
                        self.bloqueados[usuario] = time.time() + 60
                        db.execute("DELETE FROM codigos WHERE usuario=?", (usuario,))
                        return "Bloqueado por 60 segundos"

                    db.execute(
                        "UPDATE codigos SET intentos=? WHERE usuario=?",
                        (intentos, usuario),
                    )
                    return "Codigo incorrecto"

                db.execute("DELETE FROM codigos WHERE usuario=?", (usuario,))
                return "ACCESO AUTORIZADO"


def main():
    if not 1 <= PORT <= 65535:
        raise ValueError("SERVER_PORT debe estar entre 1 y 65535")
    servidor = Servidor()
    with Pyro4.Daemon(host=HOST, port=PORT) as daemon:
        daemon.register(servidor, objectId=OBJECT_ID)
        print(f"Servidor activo en {HOST}:{PORT}")
        print(f"Clientes: PYRO:{OBJECT_ID}@IP_DEL_SERVIDOR:{PORT}")
        print("Permite el puerto TCP solo en tu red local o VPN.")
        daemon.requestLoop()


if __name__ == "__main__":
    main()
