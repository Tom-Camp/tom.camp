from sqlalchemy import Engine
from sqlmodel import create_engine

from app.utils.config import settings


def make_engine() -> Engine:
    return create_engine(settings.database_url, echo=True)
