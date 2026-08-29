from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class Tasa(SQLModel, table=True):
    divisa: str = Field(primary_key=True)
    date: datetime = Field(
        primary_key=True,
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    valor: float | None = None
