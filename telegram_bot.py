# Integracion con Telegram y control de intentos MFA
# Integrante: Ismael Cornejo

import os
import time

import requests


# Configurar en la terminal: export TELEGRAM_BOT_TOKEN="TOKEN_DEL_BOT"
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# El chat de Ismael ya estaba registrado. Los demas son opcionales.
# Cada persona debe iniciar el bot en Telegram antes de recibir mensajes.
CHATS = {
    "ismael": os.getenv("TELEGRAM_CHAT_ID_ISMAEL", "1248963335"),
    "admin": os.getenv("TELEGRAM_CHAT_ID_ADMIN", ""),
    "usuario1": os.getenv("TELEGRAM_CHAT_ID_USUARIO1", ""),
    "usuario2": os.getenv("TELEGRAM_CHAT_ID_USUARIO2", ""),
}


def enviar_codigo(usuario, codigo):
    """Envia un codigo al chat de Telegram registrado."""
    chat_id = CHATS.get(usuario)

    if not TOKEN or not chat_id:
        print("Falta configurar Telegram para:", usuario)
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    mensaje = (
        "SISTEMA DE SEGURIDAD MFA\n\n"
        f"Hola {usuario}\n"
        f"Tu codigo de acceso es: {codigo}\n\n"
        "El codigo vence en 3 minutos.\n"
        "No compartas este codigo."
    )

    try:
        respuesta = requests.post(
            url,
            data={"chat_id": chat_id, "text": mensaje},
            timeout=10,
        )
        respuesta.raise_for_status()

        if respuesta.json().get("ok") is True:
            print("Codigo enviado a:", usuario)
            return True

        print("Telegram no confirmo el envio")
    except (requests.RequestException, ValueError):
        # No imprimir la URL del error: contiene el token del bot.
        print("Error al comunicarse con Telegram")

    return False


class Seguridad:
    """Controla intentos fallidos y bloqueos temporales por usuario."""

    def __init__(self):
        self.intentos = {}
        self.bloqueados = {}
        self.max_intentos = 3
        self.tiempo_bloqueo = 60

    def esta_bloqueado(self, usuario):
        fin = self.bloqueados.get(usuario, 0)
        if time.monotonic() < fin:
            return True

        if fin:
            del self.bloqueados[usuario]
            self.intentos[usuario] = 0

        return False

    def registrar_error(self, usuario):
        if self.esta_bloqueado(usuario):
            return True

        actual = self.intentos.get(usuario, 0)
        self.intentos[usuario] = actual + 1
        print("Intentos fallidos de", usuario, ":", self.intentos[usuario])

        if self.intentos[usuario] >= self.max_intentos:
            self.bloqueados[usuario] = time.monotonic() + self.tiempo_bloqueo
            print("Usuario bloqueado por 60 segundos:", usuario)
            return True

        return False

    def reiniciar_intentos(self, usuario):
        self.intentos[usuario] = 0


if __name__ == "__main__":
    print("Probando envio del codigo a Telegram...")
    if enviar_codigo("ismael", "583921"):
        print("PRUEBA EXITOSA")
    else:
        print("ERROR AL ENVIAR EL CODIGO")
