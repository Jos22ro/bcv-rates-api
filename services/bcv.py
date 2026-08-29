from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from requests import get
from requests.exceptions import RequestException
from sqlmodel import Session

from config import database
from config.config import DIVISAS_SOPORTADAS, HEADERS, URL_BCV, TTL_HORAS
from exceptions import ScrapingError,DivisaNoEncontradaError
from models.models import Tasa

def vigencia(tasa: Tasa) -> bool:
    if tasa is None:
        return False
    tiempo_actual = datetime.now()
    diferencia: timedelta = tiempo_actual - tasa.date
    return diferencia >= timedelta(hours=TTL_HORAS)

def parse_moneda(soup,id_element):
    moneda_container = soup.find(id=id_element)
    if not moneda_container:
        return None
    moneda = moneda_container.find('strong')
    if moneda is None:
        return None
    texto = moneda.text.strip().replace(',','.')
    try:
        return float(texto)
    except ValueError:
        return None

def scrapping(url:str):
    try:
        response = get(url,headers=HEADERS,verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text,'html.parser')
        return soup

    except  (RequestException) as e:
        print(f"Error: {e}")
        return None

def guardar_cotizaciones(session: Session):
        soup = scrapping(URL_BCV)
        if soup is None:
            raise ScrapingError("Error al extraer datos del BCV.")
        dolar = parse_moneda(soup,'dolar')
        euro = parse_moneda(soup,'euro')
        if dolar is None or euro is None:
            raise ScrapingError("Error al extraer los campos de divisas del BCV.")

        tasa_usd = Tasa(divisa = 'dolar', valor= dolar)
        tasa_euro = Tasa(divisa = 'euro', valor=euro)

        database.guardar_cotizacion(session, [tasa_usd,tasa_euro])


        return tasa_usd,tasa_euro




def obtener_cotizacion_reciente(session: Session, divisa: str):
    if divisa not in DIVISAS_SOPORTADAS:
        raise DivisaNoEncontradaError("Divisa no encontrada")
    tasa = database.obtener_cotizacion_reciente(session,divisa)
    if tasa is None or vigencia(tasa):
        guardar_cotizaciones(session)
        return database.obtener_cotizacion_reciente(session, divisa)
    return tasa

def obtener_cotizaciones_recientes(session: Session):
    lista_cotizaciones = []
    for divisa in DIVISAS_SOPORTADAS:
        tasa = obtener_cotizacion_reciente(session, divisa)
        if tasa is not None:
            lista_cotizaciones.append(tasa)
    return lista_cotizaciones
def obtener_historial(session: Session, divisa: str, limit: int):
    if divisa not in DIVISAS_SOPORTADAS:
        raise DivisaNoEncontradaError("Divisa no encontrada")
    historial = database.obtener_cotizaciones(session, divisa, limit)
    return historial
def obtener_historiales(session: Session, limit: int):
    historiales = []
    for divisa in DIVISAS_SOPORTADAS:
        historial = obtener_historial(session, divisa, limit)
        historiales.append(historial)
    return historiales
