import Pyro4
from getpass import getpass

ns = Pyro4.locateNS(host="localhost", port=9090)

uri = ns.lookup("practica.autenticacion")

servidor = Pyro4.Proxy(uri)

usuario = input("Usuario: ")
password = getpass("Contraseña: ")

respuesta = servidor.iniciar_sesion(usuario, password)

print(respuesta)

if respuesta.startswith("Credenciales correctas"):

    codigo = input("Ingrese el código de 6 dígitos: ")

    resultado = servidor.verificar_codigo(usuario, codigo)

    print(resultado)