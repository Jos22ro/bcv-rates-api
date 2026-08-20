from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class Tasa(SQLModel, table=True):
    divisa: str = Field(primary_key=True)
    data: datetime = Field(
        primary_key=True,
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP"}
    )
    valor: float | None = None
