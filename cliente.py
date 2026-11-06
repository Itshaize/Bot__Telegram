import Pyro4

servidor = Pyro4.Proxy(
    "PYRONAME:practica.autenticacion@localhost:9090"
)

print("SISTEMA DE AUTENTICACION")

usuario = input("Usuario: ")
password = input("Contraseña: ")

respuesta = servidor.iniciar_sesion(usuario, password)

print(respuesta)

if respuesta == "Codigo enviado a Telegram":

    codigo = input("Codigo de Telegram: ")

    resultado = servidor.verificar_codigo_mfa(
        usuario, codigo
    )

    print(resultado)
