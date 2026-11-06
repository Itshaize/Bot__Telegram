import Pyro4

servidor = Pyro4.Proxy(
    "PYRONAME:practica.autenticacion@localhost:9090"
)

print("SISTEMA DE AUTENTICACION")
print("1. Crear usuario")
print("2. Iniciar sesion")

opcion = input("Elige una opcion: ")

if opcion == "1":

    usuario = input("Nuevo usuario: ")
    password = input("Nueva contraseña: ")

    print(servidor.registrar_usuario(usuario, password))

elif opcion == "2":

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

else:
    print("Opcion incorrecta")
