from sqlmodel import Session, select
from models.models import Tasa
from config.config import URL, HEADERS
from bs4 import BeautifulSoup
import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException

def parse_moneda(soup,id_element):
    moneda_container = soup.find(id=id_element)
    if not moneda_container:
        return None
    moneda = float(moneda_container.find('strong').text.strip().replace(',','.'))
    return moneda
def guardar_cotizacion(session: Session):
    try:
        response = requests.get(URL,headers=HEADERS,verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text,'html.parser')
        usd = parse_moneda(soup,'dolares')
        euro = parse_moneda(soup,'euro')
        if usd is None or euro is None:
            raise HTTPError(
                            status_code=502, detail="Error al extraer datos del BCV."
                )

        tasa = Tasa(usd = usd,euro=euro)

        session.add(tasa)
        session.commit()
        session.refresh(tasa)

        return tasa
    except  (ConnectionError,HTTPError,RequestException) as e:
        print(f"Error: {e}")
        return None
def obtener_cotizacion(session : Session):
    ultima_tasa = select(Tasa).order_by(Tasa.id.desc()).limit(1)
    return session.exec(ultima_tasa)
