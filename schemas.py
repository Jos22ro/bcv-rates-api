from pydantic import BaseModel
from datetime import datetime

class TasaRespuesta(BaseModel):
    moneda: str
    fuente: str
    divisa: str
    valor: float | None
    fecha_registro: datetime

class HistorialRespuesta(BaseModel): # respuesta paginada
    total: int
    datos: list[TasaRespuesta]
