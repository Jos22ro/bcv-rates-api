from contextlib import asynccontextmanager

from fastapi import FastAPI
from routers import tasa
from config.db import create_db_and_table
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_table()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(tasa.router)
