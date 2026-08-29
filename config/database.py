from sqlmodel import Session, select
from models.models import Tasa

def obtener_cotizacion_reciente(session : Session,divisa):
    ultima_tasa = select(Tasa).where(Tasa.divisa == divisa).order_by(Tasa.date.desc()).limit(1)
    return session.exec(ultima_tasa).first()

def guardar_cotizacion(session: Session, tasas):
    session.add_all(tasas)
    session.commit()
    for tasa in tasas:
        session.refresh(tasa)



def obtener_cotizaciones(session: Session,divisa,limit = 10):
    cotizaciones = select(Tasa).where(Tasa.divisa == divisa).order_by(Tasa.date.desc()).limit(limit)
    return session.exec(cotizaciones).all()
