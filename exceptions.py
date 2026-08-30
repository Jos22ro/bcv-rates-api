
class BaseBCVException(Exception):
    """Excepción base para errores del dominio BCV."""

    pass


class ScrapingError(BaseBCVException):
    """Se lanza cuando falla la conexión o el parseo del portal del BCV."""

    pass


class DivisaNoEncontradaError(BaseBCVException):
    """Se lanza cuando la divisa solicitada no existe o no está soportada."""

    pass


class DatabaseError(BaseBCVException):
    """Se lanza cuando falla una operación de lectura o escritura en la BD."""

    pass
