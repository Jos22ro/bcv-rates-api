from pydantic import BaseModel
from datetime import datetime

class Tasa(BaseModel):              # respuesta de /api/tasa (agrupada)
    fuente: str
    usd: float
    euro: float

class TasaRegistro(BaseModel):      # una fila del historial
    divisa: str
    valor: float
    fecha_registro: datetime

class HistorialRespuesta(BaseModel): # respuesta paginada
    total: int
    datos: list[TasaRegistro]
