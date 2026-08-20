from sqlmodel import SQLModel, create_engine, Session

from config.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

def create_db_and_table():
    from models import models
    SQLModel.metadata.create_all(engine)
def generar_session():
    with Session(engine) as session:
        yield session
