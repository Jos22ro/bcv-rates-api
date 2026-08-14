from fastapi import APIRouter, HTTPException
from services import bcv
from config import URL,DIVISAS_SOPORTADAS
from schemas import Tasa

router = APIRouter()

@router.get('/')
async def root():
    return {'message': 'Hello World'}

@router.get('/tasa', response_model=Tasa)
async def cotizaciones():
    usd = bcv.obtener_cotizacion('dolar')
    euro = bcv.obtener_cotizacion('euro')
    if usd is None or euro is None:
        raise HTTPException(status_code=502, detail="No se pudo obtener la tasa del BCV")
    return {'fuente': URL, 'usd': usd, 'euro': euro}

@router.get('/tasa/{moneda}')
async def cotizacion(moneda):
    if moneda.lower() not in DIVISAS_SOPORTADAS:
        raise HTTPException(status_code=404, detail=f"Divisa '{moneda}' no soportada")
    tasa_moneda = bcv.obtener_cotizacion(DIVISAS_SOPORTADAS[moneda.lower()])
    if tasa_moneda is None:
        raise HTTPException(status_code=502, detail="No se pudo obtener la tasa del BCV")
    return{'fuente' : URL, DIVISAS_SOPORTADAS[moneda.lower()] : tasa_moneda}
