"""Servidor Pyro4 con autenticacion MFA y base de datos SQLite. Dio German."""
import hashlib
import secrets
import time
import Pyro4

from base_datos import BaseDatos
from telegram_bot import enviar_codigo
from errores import (CredencialesInvalidas, CodigoIncorrecto, CodigoExpirado,
                     CuentaBloqueada, EnvioTelegramFallido, configurar_excepciones_pyro)


@Pyro4.expose
@Pyro4.behavior(instance_mode='single')
class ServidorAutenticacion:
    def __init__(self, ruta_db='mfa.db'):
        self.db = BaseDatos(ruta_db)

    def iniciar_sesion(self, usuario, password):
        if self.db.bloqueado(usuario):
            raise CuentaBloqueada('Cuenta bloqueada por 60 segundos')
        if not self.db.comprobar_clave(usuario, password):
            if self.db.error(usuario):
                raise CuentaBloqueada('Tres intentos fallidos. Espera 60 segundos')
            raise CredencialesInvalidas('Usuario o contrasena incorrectos')

        codigo = f'{secrets.randbelow(1_000_000):06d}'
        if not enviar_codigo(usuario, codigo):
            raise EnvioTelegramFallido('No se pudo enviar el codigo por Telegram')
        self.db.guardar_codigo(usuario, codigo)
        return 'Codigo enviado a Telegram. Tienes 3 minutos.'

    def verificar_codigo_mfa(self, usuario, codigo):
        if self.db.bloqueado(usuario):
            raise CuentaBloqueada('Cuenta bloqueada por 60 segundos')
        datos = self.db.consultar_codigo(usuario)
        if not datos:
            raise CodigoExpirado('No hay codigo activo. Inicia sesion otra vez')
        if time.time() >= datos['expira']:
            self.db.borrar_codigo(usuario)
            raise CodigoExpirado('El codigo ha expirado')
        recibido = hashlib.sha256(str(codigo).encode()).hexdigest()
        if not secrets.compare_digest(recibido, datos['codigo_hash']):
            if self.db.error(usuario):
                raise CuentaBloqueada('Tres intentos fallidos. Espera 60 segundos')
            raise CodigoIncorrecto('Codigo incorrecto')
        self.db.borrar_codigo(usuario)
        self.db.reiniciar_intentos(usuario)
        return 'Acceso autorizado'


if __name__ == '__main__':
    configurar_excepciones_pyro()
    Pyro4.config.SERVERTYPE = 'multiplex'
    daemon = Pyro4.Daemon(host='localhost')
    ns = Pyro4.locateNS(host='localhost', port=9090)
    uri = daemon.register(ServidorAutenticacion())
    ns.register('practica.autenticacion', uri)
    print('Servidor Pyro4 + SQLite iniciado')
    daemon.requestLoop()
