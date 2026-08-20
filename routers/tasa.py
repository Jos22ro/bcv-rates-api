from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from config.db import generar_session
from services import bcv
from config.config import URL,DIVISAS_SOPORTADAS
from schemas import Tasa

router = APIRouter()

@router.get('/')
async def root():
    return {'message': 'Bienvenido a contizAngel'}

@router.get('/tasa', response_model=Tasa)
async def cotizaciones(session: Session = Depends(generar_session)):
    tasa = bcv.obtener_cotizacion(session)
    if tasa is None:
        raise HTTPException(status_code=502, detail="No se pudo obtener la tasa del BCV")
    return tasa

@router.get('/tasa')
async def cotizacion(moneda: str, session: Session = Depends(generar_session)):
    if moneda.lower() not in DIVISAS_SOPORTADAS:
        raise HTTPException(status_code=404, detail=f"Divisa '{moneda}' no soportada")
    tasa_moneda = bcv.obtener_cotizacion(session)
    if tasa_moneda is None:
        raise HTTPException(status_code=502, detail="No se pudo obtener la tasa del BCV")
    return{'fuente' : URL, DIVISAS_SOPORTADAS[moneda.lower()] : getattr(tasa_moneda, DIVISAS_SOPORTADAS[moneda.lower()])}

@router.post('/tasa/refresh', response_model=Tasa)
async def refresh_tasa(session: Session = Depends(generar_session)):
    tasa = bcv.guardar_cotizacion(session)
    return{'mensaje' : 'Se actualizo con exito', 'datos':tasa}

@router.get('/tasa/historial')
async def history_tasa(session: Session = Depends(generar_session)):
    tasa = select(Tasa).order_by(Tasa.id.desc()).limit(10)
    historial = session.exec(tasa).all()
    return historial
