from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from app.utils.config import settings


def make_engine() -> Engine:
    return create_engine(settings.database_url, echo=True)


def create_db_and_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)
