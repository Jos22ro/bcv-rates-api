from config import URL, HEADERS
from bs4 import BeautifulSoup
import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException

def parse_moneda(soup,id_element):
    moneda_container = soup.find(id=id_element)
    if not moneda_container:
        return None
    moneda = float(moneda_container.find('strong').text.strip().replace(',','.'))
    return moneda
def obtener_cotizacion(moneda):
    try:
        response = requests.get(URL,headers=HEADERS,verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text,'html.parser')
        return parse_moneda(soup,moneda)
    except  (ConnectionError,HTTPError,RequestException) as e:
        print(f"Error: {e}")
        return None
