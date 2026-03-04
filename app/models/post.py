from sqlalchemy import JSON
from sqlmodel import Field

from app.models.base import ModelBase


class Post(ModelBase, table=True):  # type: ignore
    title: str
    body: str
    images: list[str] = Field(
        default_factory=list, sa_type=JSON, description="List of image filenames"
    )
