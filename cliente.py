"""Cliente Pyro4 de autenticacion con codigo enviado a Telegram.
Integrante: Mauricio Jácome
"""

import os
import Pyro4
from getpass import getpass

from errores import (
    CredencialesInvalidas, CodigoIncorrecto, CodigoExpirado,
    CuentaBloqueada, EnvioTelegramFallido, configurar_excepciones_pyro
)


def ejecutar(servidor):
    usuario = input("Usuario: ").strip()
    password = getpass("Contraseña: ")

    try:
        respuesta = servidor.iniciar_sesion(usuario, password)
        print(respuesta)
    except CredencialesInvalidas:
        print("Usuario o contraseña incorrectos.")
        return False
    except CuentaBloqueada:
        print("Cuenta bloqueada. Intenta nuevamente en 60 segundos.")
        return False
    except EnvioTelegramFallido:
        print("No se pudo enviar el codigo. Revisa el bot de Telegram.")
        return False

    codigo = input("Codigo MFA de 6 digitos: ").strip()

    try:
        resultado = servidor.verificar_codigo_mfa(usuario, codigo)
        if resultado == "Autenticacion exitosa":
            print("Acceso autorizado.")
            return True
        print("No se pudo completar la verificacion.")
        return False
    except CodigoIncorrecto:
        print("Codigo incorrecto.")
    except CodigoExpirado:
        print("Codigo expirado o no disponible. Vuelve a iniciar sesion.")
    except CuentaBloqueada:
        print("Demasiados intentos. Cuenta bloqueada por 60 segundos.")

    return False


def main():
    configurar_excepciones_pyro()
    try:
        host = os.getenv("PYRO_NS_HOST", "localhost")
        ns = Pyro4.locateNS(host=host, port=9090)
        uri = ns.lookup("practica.autenticacion")
        with Pyro4.Proxy(uri) as servidor:
            servidor._pyroTimeout = 15
            ejecutar(servidor)
    except (Pyro4.errors.CommunicationError, Pyro4.errors.NamingError):
        print("No se pudo conectar al servidor Pyro4. Revisa que este encendido.")
    except Pyro4.errors.PyroError:
        print("Ocurrio un error remoto en el servidor.")
    except (KeyboardInterrupt, EOFError):
        print("\nOperacion cancelada.")


if __name__ == "__main__":
    main()
