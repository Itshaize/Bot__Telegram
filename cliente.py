"""Cliente de autenticacion: se conecta por IP al servidor Pyro4."""
import getpass
import os

import Pyro4
from Pyro4.errors import CommunicationError, TimeoutError as PyroTimeoutError


def solicitar_servidor():
    ip = os.getenv("SERVER_IP") or input("IP del servidor: ").strip()
    if not ip:
        raise ValueError("Debes indicar la IP del servidor")
    puerto = int(os.getenv("SERVER_PORT", "50000"))
    if not 1 <= puerto <= 65535:
        raise ValueError("Puerto no valido")
    return Pyro4.Proxy(f"PYRO:autenticacion@{ip}:{puerto}")


def main():
    try:
        with solicitar_servidor() as servidor:
            servidor._pyroTimeout = 12
            while True:
                print("\nSISTEMA DE AUTENTICACION")
                print("1. Crear usuario")
                print("2. Iniciar sesion")
                print("3. Salir")
                opcion = input("Elige una opcion: ").strip()

                if opcion == "3":
                    break
                if opcion not in ("1", "2"):
                    print("Opcion incorrecta")
                    continue

                usuario = input("Usuario: ").strip()
                password = getpass.getpass("Contraseña: ")

                if opcion == "1":
                    print(servidor.registrar_usuario(usuario, password))
                    continue

                respuesta = servidor.iniciar_sesion(usuario, password)
                print(respuesta)
                if respuesta == "Codigo enviado a Telegram":
                    codigo = input("Codigo de Telegram: ").strip()
                    print(servidor.verificar_codigo_mfa(usuario, codigo))
    except (CommunicationError, PyroTimeoutError, OSError) as error:
        print("No se pudo conectar con el servidor. Comprueba la IP, el puerto,")
        print("la red y el firewall. Detalle:", error)
    except ValueError as error:
        print("Configuracion incorrecta:", error)
    except KeyboardInterrupt:
        print("\nCliente finalizado.")


if __name__ == "__main__":
    main()
