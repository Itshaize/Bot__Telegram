import Pyro4
import random
import time
import sqlite3

from base_datos import crear_tablas, validar_usuario, guardar_codigo
from telegram_bot import enviar_codigo


@Pyro4.expose
class Servidor:

    def __init__(self):
        crear_tablas()
        self.bloqueados = {}

    def iniciar_sesion(self, usuario, password):

        if self.bloqueados.get(usuario, 0) > time.time():
            return "Usuario bloqueado"

        if not validar_usuario(usuario, password):
            return "Usuario o contraseña incorrectos"

        codigo = str(random.randint(100000, 999999))
        expira = time.time() + 180

        if not enviar_codigo(usuario, codigo):
            return "No se pudo enviar el codigo"

        guardar_codigo(usuario, codigo, expira)

        return "Codigo enviado a Telegram"

    def verificar_codigo_mfa(self, usuario, codigo):

        if self.bloqueados.get(usuario, 0) > time.time():
            return "Usuario bloqueado"

        db = sqlite3.connect("usuarios.db")

        dato = db.execute(
            "SELECT codigo, expira, intentos FROM codigos WHERE usuario=?",
            (usuario,)
        ).fetchone()

        if dato is None:
            db.close()
            return "No existe un codigo"

        codigo_guardado, expira, intentos = dato

        if time.time() > expira:
            db.execute(
                "DELETE FROM codigos WHERE usuario=?", (usuario,)
            )
            db.commit()
            db.close()
            return "Codigo expirado"

        if codigo != codigo_guardado:

            intentos += 1

            if intentos >= 3:
                self.bloqueados[usuario] = time.time() + 60
                db.execute(
                    "DELETE FROM codigos WHERE usuario=?", (usuario,)
                )
                mensaje = "Bloqueado por 60 segundos"
            else:
                db.execute(
                    "UPDATE codigos SET intentos=? WHERE usuario=?",
                    (intentos, usuario)
                )
                mensaje = "Codigo incorrecto"

            db.commit()
            db.close()
            return mensaje

        db.execute(
            "DELETE FROM codigos WHERE usuario=?", (usuario,)
        )
        db.commit()
        db.close()

        return "ACCESO AUTORIZADO"


servidor = Servidor()

daemon = Pyro4.Daemon(host="localhost")
ns = Pyro4.locateNS(host="localhost")

uri = daemon.register(servidor)
ns.register("practica.autenticacion", uri)

print("Servidor Pyro4 funcionando")

daemon.requestLoop()
