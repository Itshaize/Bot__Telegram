import Pyro4
import secrets
import time
import hmac
from threading import Lock


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class ServidorAutenticacion:

    def __init__(self):
        # Usuarios de prueba
        self.usuarios = {
            "admin": "1234",
            "usuario1": "abcd",
            "usuario2": "5678"
        }

        # Códigos temporales por usuario
        self.codigos = {}
        self.lock = Lock()

    def iniciar_sesion(self, usuario, password):

        # Validar credenciales
        if self.usuarios.get(usuario) != password:
            return "Usuario o contraseña incorrectos"

        # Generar código aleatorio de 6 dígitos
        codigo = f"{secrets.randbelow(1000000):06d}"

        # Expiración de 3 minutos
        expiracion = time.monotonic() + 180

        # Guardar código temporalmente
        with self.lock:
            self.codigos[usuario] = {
                "codigo": codigo,
                "expiracion": expiracion
            }

        # Mostrar código en servidor (solo para pruebas)
        print(f"Usuario: {usuario} - Código: {codigo}")

        return "Credenciales correctas. Código generado, válido por 3 minutos"

    def verificar_codigo(self, usuario, codigo):

        with self.lock:
            datos = self.codigos.get(usuario)

            if datos is None:
                return "No existe un código para este usuario"

            # Verificar expiración
            if time.monotonic() >= datos["expiracion"]:
                del self.codigos[usuario]
                return "El código ha expirado"

            # Comparar códigos
            if hmac.compare_digest(str(codigo), datos["codigo"]):
                del self.codigos[usuario]
                return "Autenticación exitosa"

            return "Código incorrecto"


daemon = Pyro4.Daemon(host="localhost")

ns = Pyro4.locateNS(host="localhost", port=9090)

uri = daemon.register(ServidorAutenticacion())

ns.register("practica.autenticacion", uri)

print("Servidor iniciado")
print("URI:", uri)
print("Registrado como practica.autenticacion")

daemon.requestLoop()