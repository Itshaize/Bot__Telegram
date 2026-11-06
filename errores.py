"""Excepciones sencillas que comparten el servidor y el cliente Pyro4."""


class CredencialesInvalidas(Exception):
    pass


class CodigoIncorrecto(Exception):
    pass


class CodigoExpirado(Exception):
    pass


class CuentaBloqueada(Exception):
    pass


class EnvioTelegramFallido(Exception):
    pass


def configurar_excepciones_pyro():
    """Permite que Pyro4 envíe estas excepciones con el serializador seguro serpent."""
    from Pyro4.util import SerializerBase

    tipos = (
        CredencialesInvalidas,
        CodigoIncorrecto,
        CodigoExpirado,
        CuentaBloqueada,
        EnvioTelegramFallido,
    )
    clases = {f"{tipo.__module__}.{tipo.__name__}": tipo for tipo in tipos}

    def a_diccionario(error):
        return {
            "__class__": f"{type(error).__module__}.{type(error).__name__}",
            "args": list(error.args),
        }

    def a_excepcion(nombre, datos):
        return clases[nombre](*datos.get("args", []))

    for nombre, tipo in clases.items():
        SerializerBase.register_class_to_dict(tipo, a_diccionario)
        SerializerBase.register_dict_to_class(nombre, a_excepcion)
