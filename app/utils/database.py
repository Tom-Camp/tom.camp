from sqlmodel import SQLModel, create_engine

from app.utils.config import settings

engine = create_engine(settings.database_url, echo=True)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
