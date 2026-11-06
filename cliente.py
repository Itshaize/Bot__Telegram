# Cliente Pyro4 - Mauricio Jacome
import Pyro4
from getpass import getpass

from errores import (
    CredencialesInvalidas, CodigoIncorrecto, CodigoExpirado,
    CuentaBloqueada, EnvioTelegramFallido, configurar_excepciones_pyro
)


def main():
    configurar_excepciones_pyro()

    try:
        ns = Pyro4.locateNS(host="localhost", port=9090)
        uri = ns.lookup("practica.autenticacion")

        with Pyro4.Proxy(uri) as servidor:
            print("SISTEMA DE AUTENTICACION MFA")
            usuario = input("Usuario: ").strip()
            password = getpass("Contrasena: ")

            print(servidor.iniciar_sesion(usuario, password))

            codigo = input("Codigo recibido en Telegram: ").strip()
            print(servidor.verificar_codigo_mfa(usuario, codigo))

    except (
        CredencialesInvalidas, CodigoIncorrecto, CodigoExpirado,
        CuentaBloqueada, EnvioTelegramFallido
    ) as error:
        print("Error:", error)
    except Pyro4.errors.PyroError:
        print("No se pudo conectar o comunicar con el servidor Pyro4.")
    except (KeyboardInterrupt, EOFError):
        print("\nOperacion cancelada.")


if __name__ == "__main__":
    main()
