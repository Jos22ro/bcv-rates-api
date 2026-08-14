from pydantic import BaseModel

class Tasa(BaseModel):
    fuente:str
    usd: float
    euro: float
