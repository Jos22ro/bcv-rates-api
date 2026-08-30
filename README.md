# bcv-rates-api

API REST de **práctica y aprendizaje** construida como parte de un curso FullStack. Consulta las tasas de cambio oficiales del Banco Central de Venezuela (BCV) mediante scraping, las cachea en SQLite y expone endpoints para consulta e historial.

> ⚠️ **Nota del autor:** este es un proyecto **personal y exclusivamente de práctica**. No está pensado para producción ni para uso comercial. El scraping del portal del BCV se hace con fines educativos; trátalo con respeto (evita hacer peticiones masivas o innecesarias).

## Stack

- **FastAPI** — framework web
- **SQLModel** — ORM sobre SQLite para la persistencia
- **requests + BeautifulSoup** — scraping del portal del BCV
- **Python 3.14** — entorno local en `.venv`

## Comandos

```bash
source .venv/bin/activate          # activa el venv local
uvicorn main:app --reload          # dev server en http://127.0.0.1:8000
```

- Docs interactiva (Swagger): http://127.0.0.1:8000/docs

## Endpoints

Todos bajo el prefijo `/v1/api/tasa`.

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/v1/api/tasa` | Tasas de cambio vigentes (dólar y euro). Si la caché expiró, re-scrapea automáticamente. Acepta `?divisa=dolar` o `?divisa=euro`. |
| `POST` | `/v1/api/tasa/refresh` | Fuerza un scrape y guarda las tasas más recientes en BD. |
| `GET` | `/v1/api/tasa/historial` | Historial paginado con filtros. Devuelve `{total, datos}`. |

### Parámetros de `/historial`

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `divisa` | string | — | Filtra por `dolar` o `euro`. |
| `desde` | fecha `YYYY-MM-DD` | — | Registros posteriores o iguales a esa fecha. |
| `hasta` | fecha `YYYY-MM-DD` | — | Registros anteriores o iguales a esa fecha. |
| `limit` | int | `50` | Cantidad de registros por página (1-100). |
| `offset` | int | `0` | Número de registros a saltar (paginación). |

### Ejemplos

```
GET /v1/api/tasa/historial
GET /v1/api/tasa/historial?divisa=dolar
GET /v1/api/tasa/historial?desde=2026-08-01&hasta=2026-08-15
GET /v1/api/tasa/historial?divisa=euro&limit=10&offset=20
GET /v1/api/tasa/historial?divisa=dolar&desde=2026-08-01&hasta=2026-08-31&limit=5&offset=10
```

Respuesta (siempre con el `total` global, incluso al paginar):

```json
{
  "total": 120,
  "datos": [
    { "moneda": "USD", "fuente": "https://www.bcv.org.ve", "divisa": "dolar", "valor": 36.5, "fecha_registro": "2026-08-28T..." }
  ]
}
```

Errores: divisa inválida → `404`; fecha mal formada o `desde > hasta` → `400`; `limit`/`offset` fuera de rango → `422`. Una tabla vacía responde `200` con `total: 0` y `datos: []`.

## Arquitectura

Flujo: `routers/` → `services/bcv.py` (scraping) → `config/database.py` (persistencia) → `models/models.py` (SQLModel).

```
routers/tasa.py  →  services/bcv.py  →  config/database.py  →  models/models.py
     (HTTP)             (scraping)          (solo persistencia)      (tabla Tasa)
```

- Los **routers** solo orquestan y validan.
- Los **services** hacen el scraping y la lógica de negocio (como el TTL).
- `config/database.py` se encarga **solo** de la base de datos.
- Las respuestas JSON se validan con esquemas Pydantic de `schemas.py`.

## Mecanismo de caché (TTL)

La API cachea las tasas en SQLite. Para evitar golpear el portal del BCV en cada request:

- `GET /v1/api/tasa` sirve la tasa desde la BD si tiene menos de `TTL_HORAS` (configurado en `config/config.py`, por defecto `24` horas). Si el dato está vencido o la BD está vacía, re-scrapea y guarda automáticamente.
- `POST /v1/api/tasa/refresh` fuerza siempre un scraping manual, sin importar la vigencia.

Las fechas se trabajan en **UTC-naive** para evitar choques de zonas horarias (naive vs. aware) al leer desde SQLite.

## Estructura del proyecto

| Archivo | Rol |
|---|---|
| `main.py` | App FastAPI; `lifespan` crea las tablas al arrancar |
| `routers/tasa.py` | Definen los endpoints y validan `divisa`, fechas, `limit` y `offset` |
| `services/bcv.py` | Scraping del BCV, vigencia (TTL) y guardado |
| `config/database.py` | Persistencia (guardar y consultar cotizaciones) |
| `config/db.py` | Engine SQLite y generador de sesiones |
| `config/config.py` | Constantes (`URL_BCV`, `DIVISAS_SOPORTADAS`, `TTL_HORAS`, etc.) |
| `models/models.py` | Modelo `Tasa` (SQLModel) con PK compuesta (`divisa`, `date`) |
| `schemas.py` | Esquemas Pydantic de respuesta |
| `exceptions.py` | Excepciones de dominio (`ScrapingError`, `DivisaNoEncontradaError`, `DatabaseError`) |

## Notas

- El scraper usa `verify=False` (desactiva la verificación SSL); es aceptable aquí solo por ser un proyecto de práctica, pero no lo copies a producción sin revisarlo.
- No hay `requirements.txt` todavía: las dependencias se instalaron a mano en el venv (`fastapi`, `uvicorn`, `sqlmodel`, `requests`, `beautifulsoup4`).
- No hay tests, linter ni formateador configurados.

---

Proyecto personal de práctica — hecho para aprender. 😄
