from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from config.db import generar_session
from exceptions import DivisaNoEncontradaError, ScrapingError, BaseBCVException
from services import bcv
from config.config import URL_BCV,DIVISAS_SOPORTADAS
from schemas import TasaRespuesta, HistorialRespuesta

router = APIRouter(prefix='/v1/api/tasa')

def convertir_tasa(tasa):
    return TasaRespuesta(
        moneda=DIVISAS_SOPORTADAS[tasa.divisa.lower()],
        fuente=URL_BCV,
        divisa=tasa.divisa,
        valor=tasa.valor,
        fecha_registro=tasa.date,
    )

@router.get('',response_model= list[TasaRespuesta])
async def cotizaciones(divisa: Annotated[str | None, Query()] = None, session: Session = Depends(generar_session)):
    try:
        if divisa is not None:
            tasa = bcv.obtener_cotizacion_reciente(session, divisa)
            if tasa is None:
                raise HTTPException(status_code=502, detail="No se pudo obtener la tasa del BCV")
            return [convertir_tasa(tasa)]

        lista_cotizaciones = bcv.obtener_cotizaciones_recientes(session)
        if not lista_cotizaciones:
            raise HTTPException(status_code=502, detail="No se pudo obtener la tasa del BCV")
        return [convertir_tasa(tasa) for tasa in lista_cotizaciones]
    except DivisaNoEncontradaError:
        raise HTTPException(status_code=404, detail="Divisa no encontrada")
    except BaseBCVException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/refresh', response_model=list[TasaRespuesta])
async def refresh_tasa(session: Session = Depends(generar_session)):
    try:
        tasa_usd,tasa_euro = bcv.guardar_cotizaciones(session)
        return [convertir_tasa(tasa) for tasa in [tasa_usd, tasa_euro]]
    except ScrapingError as e:
        raise HTTPException(status_code=502, detail=f"Error al obtener la tasa del BCV: {str(e)}")
    except BaseBCVException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/historial', response_model=list[HistorialRespuesta])
async def history_tasa(divisa: Annotated[str | None, Query()] = None, limit: Annotated[int | None, Query(ge=1,le=100)] = None, session: Session = Depends(generar_session)):
    try:
        if divisa is not None:
            historial = bcv.obtener_historial(session, divisa,limit)
            if not historial:
                raise HTTPException(status_code=502, detail=f"No se pudo obtener el historial por {divisa} del BCV")
            return [HistorialRespuesta(total = len(historial), datos = [convertir_tasa(tasa) for tasa in historial])]
        historiales = bcv.obtener_historiales(session, limit)
        if not historiales:
            raise HTTPException(status_code=502, detail="No se pudo obtener el historial del BCV")
        return [HistorialRespuesta(total = len(historial), datos = [convertir_tasa(tasa) for tasa in historial]) for historial in historiales]
    except DivisaNoEncontradaError:
        raise HTTPException(status_code=404, detail="Divisa no encontrada")
    except BaseBCVException as e:
        raise HTTPException(status_code=500, detail=str(e))
