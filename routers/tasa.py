from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from config.db import generar_session
from exceptions import DivisaNoEncontradaError, ScrapingError, DatabaseError, BaseBCVException
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
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except BaseBCVException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/refresh', response_model=list[TasaRespuesta])
async def refresh_tasa(session: Session = Depends(generar_session)):
    try:
        tasa_usd,tasa_euro = bcv.guardar_cotizaciones(session)
        return [convertir_tasa(tasa) for tasa in [tasa_usd, tasa_euro]]
    except ScrapingError as e:
        raise HTTPException(status_code=502, detail=f"Error al obtener la tasa del BCV: {str(e)}")
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except BaseBCVException as e:
        raise HTTPException(status_code=500, detail=str(e))

def _parse_fecha(valor: str | None, nombre: str) -> datetime | None:
    if valor is None:
        return None
    try:
        return datetime.combine(date.fromisoformat(valor), datetime.min.time())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"El parametro '{nombre}' no es una fecha valida (formato YYYY-MM-DD)")


@router.get('/historial', response_model=HistorialRespuesta)
async def history_tasa(
    divisa: Annotated[str | None, Query()] = None,
    desde: Annotated[str | None, Query()] = None,
    hasta: Annotated[str | None, Query()] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = 50,
    offset: Annotated[int | None, Query(ge=0)] = 0,
    session: Session = Depends(generar_session),
):
    try:
        fecha_desde = _parse_fecha(desde, 'desde')
        fecha_hasta = _parse_fecha(hasta, 'hasta')
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise HTTPException(status_code=400, detail="'desde' no puede ser posterior a 'hasta'")

        if divisa is not None:
            historial, total = bcv.obtener_historial(session, divisa, limit, offset, fecha_desde, fecha_hasta)
            return HistorialRespuesta(total=total, datos=[convertir_tasa(t) for t in historial])

        historiales, total = bcv.obtener_historiales(session, limit, offset, fecha_desde, fecha_hasta)
        return HistorialRespuesta(total=total, datos=[convertir_tasa(t) for t in historiales])
    except DivisaNoEncontradaError:
        raise HTTPException(status_code=404, detail="Divisa no encontrada")
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except BaseBCVException as e:
        raise HTTPException(status_code=500, detail=str(e))
