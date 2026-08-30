from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, func, select

from exceptions import DatabaseError
from models.models import Tasa


def _filtros(query, divisa, desde, hasta):
    if divisa:
        query = query.where(Tasa.divisa == divisa)
    if desde:
        query = query.where(Tasa.date >= desde)
    if hasta:
        query = query.where(Tasa.date <= hasta)
    return query


def obtener_cotizacion_reciente(session: Session, divisa):
    try:
        ultima_tasa = select(Tasa).where(Tasa.divisa == divisa).order_by(Tasa.date.desc()).limit(1)
        return session.exec(ultima_tasa).first()
    except SQLAlchemyError as e:
        raise DatabaseError("Error al leer la cotizacion de la base de datos") from e


def guardar_cotizacion(session: Session, tasas):
    try:
        session.add_all(tasas)
        session.commit()
        for tasa in tasas:
            session.refresh(tasa)
    except SQLAlchemyError as e:
        session.rollback()
        raise DatabaseError("Error al guardar las cotizaciones en la base de datos") from e


def obtener_cotizaciones(session: Session, divisa=None, limit=50, offset=0, desde=None, hasta=None):
    try:
        query = _filtros(select(Tasa), divisa, desde, hasta)
        query = query.order_by(Tasa.date.desc()).offset(offset).limit(limit)
        return session.exec(query).all()
    except SQLAlchemyError as e:
        raise DatabaseError("Error al leer el historial de la base de datos") from e


def contar_cotizaciones(session: Session, divisa=None, desde=None, hasta=None) -> int:
    try:
        query = _filtros(select(func.count(Tasa.date)), divisa, desde, hasta)
        return session.exec(query).one()
    except SQLAlchemyError as e:
        raise DatabaseError("Error al contar las cotizaciones de la base de datos") from e
