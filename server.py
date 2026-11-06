"""Servidor central Pyro4: contraseña, OTP, expiración y bloqueo temporal."""

import os
import Pyro4
import secrets
import time
import hmac
from threading import Lock

from telegram_bot import enviar_codigo, Seguridad
from errores import (
    CredencialesInvalidas, CodigoIncorrecto, CodigoExpirado,
    CuentaBloqueada, EnvioTelegramFallido, configurar_excepciones_pyro
)


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class ServidorAutenticacion:

    def __init__(self):
        # Usuarios de demostración (no usar contraseñas fijas en producción).
        self.usuarios = {
            "admin": "1234",
            "usuario1": "abcd",
            "usuario2": "5678",
            "ismael": "1234",  # Usuario con Telegram configurado en telegram_bot.py
        }
        self.codigos = {}
        self.seguridad = Seguridad()
        self.lock = Lock()

    def iniciar_sesion(self, usuario, password):
        with self.lock:
            if self.seguridad.esta_bloqueado(usuario):
                raise CuentaBloqueada("Cuenta bloqueada por 60 segundos")

            if self.usuarios.get(usuario) != password:
                if self.seguridad.registrar_error(usuario):
                    self.codigos.pop(usuario, None)
                    raise CuentaBloqueada("Demasiados intentos. Espera 60 segundos")
                raise CredencialesInvalidas("Usuario o contraseña incorrectos")

            # Codigo aleatorio de 6 digitos que caduca en 3 minutos.
            codigo = f"{secrets.randbelow(1000000):06d}"
            self.codigos[usuario] = {
                "codigo": codigo,
                "expiracion": time.monotonic() + 180,
            }

        # Se envía fuera del bloqueo para no detener otras solicitudes.
        if not enviar_codigo(usuario, codigo):
            with self.lock:
                # Eliminar solo el mismo codigo, por si se inicio otra sesion.
                datos = self.codigos.get(usuario)
                if datos and datos["codigo"] == codigo:
                    self.codigos.pop(usuario, None)
            raise EnvioTelegramFallido("No se pudo enviar el codigo por Telegram")

        return "Credenciales correctas. Codigo enviado a Telegram (3 minutos)"

    def verificar_codigo_mfa(self, usuario, codigo):
        with self.lock:
            if self.seguridad.esta_bloqueado(usuario):
                raise CuentaBloqueada("Cuenta bloqueada por 60 segundos")

            datos = self.codigos.get(usuario)
            if datos is None:
                raise CodigoExpirado("No hay un codigo activo. Inicia sesion de nuevo")

            if time.monotonic() >= datos["expiracion"]:
                del self.codigos[usuario]
                raise CodigoExpirado("El codigo ha expirado")

            if not hmac.compare_digest(str(codigo), datos["codigo"]):
                if self.seguridad.registrar_error(usuario):
                    del self.codigos[usuario]
                    raise CuentaBloqueada("Demasiados intentos. Espera 60 segundos")
                raise CodigoIncorrecto("El codigo es incorrecto")

            # Una vez usado, el codigo deja de ser valido.
            del self.codigos[usuario]
            self.seguridad.reiniciar_intentos(usuario)
            return "Autenticacion exitosa"

    # Mantiene compatibilidad con clientes anteriores de los compañeros.
    def verificar_codigo(self, usuario, codigo):
        return self.verificar_codigo_mfa(usuario, codigo)


if __name__ == "__main__":
    configurar_excepciones_pyro()
    host = os.getenv("PYRO_HOST", "localhost")
    host_ns = os.getenv("PYRO_NS_HOST", "localhost")
    daemon = Pyro4.Daemon(host=host)
    ns = Pyro4.locateNS(host=host_ns, port=9090)
    uri = daemon.register(ServidorAutenticacion())
    ns.register("practica.autenticacion", uri)

    print("Servidor iniciado")
    print("URI:", uri)
    print("Registrado como practica.autenticacion")
    daemon.requestLoop()
