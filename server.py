# Servidor Pyro4 - Dio German
import os
import time
import secrets
import hmac
import Pyro4

from telegram_bot import enviar_codigo, Seguridad
from errores import (
    CredencialesInvalidas, CodigoIncorrecto, CodigoExpirado,
    CuentaBloqueada, EnvioTelegramFallido, configurar_excepciones_pyro
)


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class ServidorAutenticacion:
    def __init__(self):
        # Usuario de prueba. Para uso real, no guardar contrasenas aqui.
        self.usuarios = {"ismael": "1234"}
        self.codigos = {}
        self.seguridad = Seguridad()

    def iniciar_sesion(self, usuario, password):
        if self.seguridad.esta_bloqueado(usuario):
            raise CuentaBloqueada("Espera 60 segundos")

        if self.usuarios.get(usuario) != password:
            if self.seguridad.registrar_error(usuario):
                self.codigos.pop(usuario, None)
                raise CuentaBloqueada("Demasiados intentos. Espera 60 segundos")
            raise CredencialesInvalidas("Usuario o contrasena incorrectos")

        codigo = f"{secrets.randbelow(1000000):06d}"

        if not enviar_codigo(usuario, codigo):
            raise EnvioTelegramFallido("No se pudo enviar el codigo a Telegram")

        self.codigos[usuario] = {
            "codigo": codigo,
            "vence": time.monotonic() + 180
        }
        return "Codigo enviado a Telegram. Tienes 3 minutos."

    def verificar_codigo_mfa(self, usuario, codigo):
        if self.seguridad.esta_bloqueado(usuario):
            raise CuentaBloqueada("Espera 60 segundos")

        datos = self.codigos.get(usuario)
        if datos is None:
            raise CodigoExpirado("Primero debes iniciar sesion")

        if time.monotonic() >= datos["vence"]:
            del self.codigos[usuario]
            raise CodigoExpirado("El codigo ha expirado")

        if not hmac.compare_digest(str(codigo), datos["codigo"]):
            if self.seguridad.registrar_error(usuario):
                del self.codigos[usuario]
                raise CuentaBloqueada("Demasiados intentos. Espera 60 segundos")
            raise CodigoIncorrecto("Codigo incorrecto")

        del self.codigos[usuario]  # No se puede utilizar dos veces
        self.seguridad.reiniciar_intentos(usuario)
        return "Acceso autorizado"


if __name__ == "__main__":
    configurar_excepciones_pyro()
    Pyro4.config.SERVERTYPE = "multiplex"  # Una solicitud a la vez, sin locks
    daemon = Pyro4.Daemon(host="localhost")
    ns = Pyro4.locateNS(host="localhost", port=9090)
    uri = daemon.register(ServidorAutenticacion())
    ns.register("practica.autenticacion", uri)
    print("Servidor Pyro4 iniciado. Esperando al cliente...")
    daemon.requestLoop()
