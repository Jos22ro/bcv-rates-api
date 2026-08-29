# AGENTS.md — API BCV

Proyecto de aprendizaje (curso FullStack): API REST con FastAPI que consulta las tasas de cambio oficiales del BCV (scraping), las cachea en SQLite y expone endpoints para consulta e historial. El archivo `Solicitud_Proyecto_API_BCV.md` es el "brief del cliente" que define el alcance por fases; `docs/plans/` guarda planes de implementación fechados.

## Comandos

```bash
source .venv/bin/activate          # Python 3.14, venv local
uvicorn main:app --reload          # dev server en http://127.0.0.1:8000
```

- Docs interactiva (Swagger): http://127.0.0.1:8000/docs
- No hay requirements.txt ni pyproject.toml todavía (dependencias instaladas a mano en el venv: fastapi, uvicorn, sqlmodel, requests, beautifulsoup4).
- No hay tests, linter ni formateador configurados.

## Arquitectura

Flujo: `routers/` → `services/bcv.py` (scraping) → `config/database.py` (persistencia) → `models/models.py` (SQLModel).

| Archivo | Rol |
|---|---|
| `main.py` | App FastAPI; `lifespan` crea tablas al arrancar vía `create_db_and_table()` |
| `routers/tasa.py` | Endpoints con `APIRouter(prefix='v1/api/tasa')`: `GET ''`, `POST /tasa/refresh`, `GET /tasa/historial`. Inyecta sesión SQLModel con `Depends(generar_session)` |
| `services/bcv.py` | Scraping del portal BCV con `requests` + BeautifulSoup (ids `dolares`, `euro`). Guarda ambas divisas |
| `config/database.py` | Capa de persistencia: guardar y obtener cotizaciones (solo BD, sin scraping) |
| `config/db.py` | Engine SQLite (`sqlite:///./bcv_tasas.db`) + generador de sesiones |
| `config/config.py` | Constantes: URL, HEADERS, `DIVISAS_SOPORTADAS` (dolar→USD, euro→EUR), DATABASE_URL |
| `models/models.py` | Modelo `Tasa` (SQLModel): PK compuesta (`divisa`, `date` UTC), campo `valor` |
| `schemas.py` | Modelos Pydantic de respuesta: `Tasa`, `HistorialRespuesta` |

## Convenciones

- Código y comentarios en español; nombres de dominio en español (`divisa`, `valor`, `cotizacion`).
- Type hints modernos (`str | None`, `list[Tasa]`).
- Separación de capas: routers solo orquestan/validan; servicios hacen scraping; `database.py` solo persistencia.
- Respuestas JSON validadas con esquemas Pydantic de `schemas.py`.
- Fechas en UTC (`datetime.now(timezone.utc)`).
- Commits en español con prefijo convencional (`feat:`, etc.).

## Estado y pendientes

Fuente de verdad del alcance: checklist en `Solicitud_Proyecto_API_BCV.md` (Fases 2–5). Pendiente principal:

- TTL/caché (constante `TTL_HORAS`): hoy cada GET lee la última fila pero nunca re-scrapea si está vieja; solo `POST /tasa/refresh` scrapea.
- Filtros (`?divisa=`, `?desde=`, `?hasta=`), paginación (`limite`, `offset` + `total`) y orden por fecha en `/historial`.

## Problemas conocidos (no romper más, corregir al tocar)

- Rutas anidadas de más: el prefix ya trae `tasa`, así que los paths reales son `/v1/api/tasa/tasa/refresh` y `/v1/api/tasa/tasa/historial` (duplicado).
- `routers/tasa.py` importa `Tasa` desde `schemas` (Pydantic) y usa `select(Tasa)` / `Tasa.id` en `/historial`, pero el modelo SQLModel ya no tiene `id` (PK compuesta). El endpoint de historial está roto tras la migración al nuevo esquema.
- `services/bcv.py` lanza `HTTPError(status_code=..., detail=...)`, firma que no corresponde a `requests.HTTPError`; debería ser `HTTPException` de FastAPI o una excepción propia.
- `verify=False` desactiva verificación SSL al scrapear; `response_model=Tasa` en `POST /refresh` no coincide con el dict `{mensaje, datos}` que se devuelve.
- Uso de `print()` para errores en lugar de `logging`.
