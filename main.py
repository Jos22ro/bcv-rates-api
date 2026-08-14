from fastapi import FastAPI
from routers import tasa

app = FastAPI()
app.include_router(tasa.router,prefix='/api')
