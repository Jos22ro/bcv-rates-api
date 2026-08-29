# Plan: Normalizar esquema a una divisa por registro + refactor de capas

Fecha: 2026-08-19
Fuente: `Solicitud_Proyecto_API_BCV.md` (Fase 4 y Fase 5) + decisión de diseño discutida
Dependencia de datos: scraping del portal BCV (`https://www.bcv.org.ve`)

## Objetivo

Cambiar el modelo de datos de una fila con `usd`+`euro` juntos a **una fila por divisa por fecha**, para cumplir la solicitud (PK compuesta `(divisa, fecha)`), habilitar el filtro por divisa del historial y escalar a nuevas monedas. De paso se separan responsabilidades (scraping vs. persistencia), se agrega el TTL y se completa el endpoint de historial.

## Contexto del problema

Estado actual del código:
- `models/models.py`: `Tasa(id, usd, euro, data)` — PK autoincremental, ambas divisas en la misma fila. Imposible filtrar por `divisa`, permite duplicados y no escala a más monedas.
- `services/bcv.py`: mezcla scraping (`requests`) + persistencia (`session.add/commit`). `obtener_cotizacion` devuelve un objeto `Select`, no una tasa (bug).
- No hay `TTL_HORAS`: cada request scrapea al BCV (no cumple requisito de éxito #5).
- `routers/tasa.py`: `/api/tasa/historial` sin filtros, paginación, `total`, orden por fecha, ni timestamps UTC/ISO.
- `schemas.py`: solo `Tasa(fuente, usd, euro)`.

## Spec de referencia

- Fase 4: esquema `tasas(divisa, valor, fecha_registro)` con PK compuesta; capa de persistencia `guardar_tasa/obtener_tasa_reciente`; TTL; separación de responsabilidades.
- Fase 5: historial con `?divisa`, `?desde`, `?hasta`, `?limite`, `?offset`, orden por fecha desc, `total`, timestamps ISO UTC, y errores 400.
- Endpoint `/api/tasa` sigue devolviendo `{fuente, usd, euro}` (agrupando las filas recientes).

## Decisiones de diseño

- **Persistencia normalizada**: una fila por `(divisa, fecha_registro)` con `UniqueConstraint` para evitar duplicados.
- **Presentación desnormalizada**: `/api/tasa` agrupa las filas recientes en `{usd, euro, fuente}` en la capa de servicio. La BD interna no se expone.
- **`database.py` en `config/`** (junto a `db.py`): operaciones de datos y lógica TTL. `db.py` queda solo con engine/sesión.
- **`services/bcv.py` solo scraping** puro (devuelve dict `{usd, euro}` o None); el guardado/orquestación va a la capa de servicio/router.
- **`schemas.py` crece a varios `response_model`**: `Tasa` (agrupada), `TasaRegistro` (fila), `HistorialRespuesta` (paginada).
- **Timestamps UTC/ISO**: `datetime.now(timezone.utc)` en el modelo; serialización ISO 8601.

## Tareas

| # | Tarea | Archivos | Depende de | Verificación |
|---|-------|----------|------------|--------------|
| 1 | Reestructurar `Tasa` del modelo: `id`, `divisa: str`, `valor: float`, `fecha_registro: datetime(utc)` con `UniqueConstraint(divisa, fecha_registro)` | `models/models.py` | — | Importa sin errores; `create_db_and_table()` crea la nueva tabla |
| 2 | Crear `config/database.py` con `guardar_tasa(session, divisa, valor)` y `obtener_tasa_reciente(session, divisa)` (executando la query, devolviendo la fila o None) | `config/database.py` | #1 | Prueba unitaria rápida con sesión en memoria |
| 3 | Añadir `TTL_HORAS = 24` y `VALORES_MONEDA` en `config/config.py` | `config/config.py` | — | Constantes disponibles |
| 4 | Refactor `services/bcv.py`: `obtener_cotizacion_bcv()` de scraping puro que devuelve `{usd, euro}` o None; quitar `session.add/commit` y el `Select` de ahí | `services/bcv.py` | #2 | Scraping devuelve dict; no toca BD |
| 5 | Nueva lógica de caché en la capa de servicio: dado el TTL, decidir si se sirve de BD o se scrapea y guarda (via `database.py`) | `services/tasa_service.py` (nuevo) o `routers/tasa.py` | #2 #3 #4 | `/api/tasa` sirve dato fresco con TTL y arma `{usd, euro, fuente}` |
| 6 | Actualizar `routers/tasa.py`: usar la capa de servicio; corregir `/tasa/{moneda}` (tipo/validación); que `/tasa/refresh` devuelva un schema correcto | `routers/tasa.py`, `schemas.py` | #5 | Endpoints responden JSON correcto por Swagger |
| 7 | Crear en `schemas.py` `TasaRegistro(divisa, valor, fecha_registro)` y `HistorialRespuesta(total, datos)` | `schemas.py` | #5 | Modelos pydantic válidos |
| 8 | Implementar `GET /tasa/historial` completo: filtros `?divisa`, `?desde`, `?hasta`, paginación `?limite=50`/`?offset`, orden por `fecha_registro desc`, `total`, y 400 para divisa/rango inválidos | `routers/tasa.py`, `config/database.py` | #6 #7 | Pruebas en Swagger con cada combinación de params |
| 9 | Migración de datos existentes: script o tarea manual para volcar filas `(usd, euro, data)` a filas `(divisa, valor, fecha)`; o borrar el `.db` en dev y regenerar | `bcv_tasas.db` | #1 | BD nueva sin duplicados tras la carga |
| 10 | Verificación final: `lint`/typecheck, arranque, medir latencia 1ª llamada (scraping) vs. siguientes (caché) | todo | #8 #9 | `/api/tasa` < 300 ms en cache; historial responde con filtros |

## Riesgos

- **Datos existentes**: el `.db` actual no se puede leer con el nuevo esquema → se migra o se descarta en dev (tarea #9).
- **Cambio de stack**: se mantiene `requests`/`sqlmodel` (no `urllib`/`sqlite3` como pide la solicitud). Requiere justificarlo en README para que el cliente lo acepte.
- **El BCV cambia su DOM**: el scraping ya tiene manejo de excepciones; si falla el parseo, `/api/tasa` debe degradar a la última fila de BD o 502.
- **Timestamp naive existente**: `data` local/naive → reemplazado por `fecha_registro` UTC en el nuevo modelo.

## Siguiente paso

Aprobar este plan (o pedir cambios) para implementar. Cuando la implementación termine, usá `/verificar-cambios` para probar los cambios.