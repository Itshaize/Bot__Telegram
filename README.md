# MFA con Pyro4, Telegram y SQLite

Proyecto de demostracion: el cliente Pyro4 solicita usuario, contrasena y codigo de Telegram. El servidor guarda usuarios, codigos, intentos y bloqueos en SQLite (`mfa.db`).

## Ubuntu

```bash
sudo apt install python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="TOKEN_DE_BOTFATHER"
export TELEGRAM_CHAT_ID_ISMAEL="CHAT_ID_DE_ISMAEL"
```

En tres terminales (activa el entorno en cada una):

1. `python3 -m Pyro4.naming`
2. `python3 server.py` (en esta terminal configura las variables Telegram)
3. `python3 cliente.py`

Cuenta de demostracion: `ismael` / `1234`. Se crea automaticamente en la primera ejecucion. Para cambiar la contrasena inicial antes de crear la base: `export MFA_DEMO_PASSWORD="OTRA_CLAVE"`.

La base se crea automaticamente. Cada codigo vence despues de 180 segundos; tres errores bloquean durante 60 segundos. No subir el token ni la base a GitHub. Este ejemplo no es apto para uso en produccion.
