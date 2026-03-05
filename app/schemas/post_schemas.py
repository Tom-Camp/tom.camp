from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreatePost(BaseModel):
    title: str
    body: str
    images: list[str] | None = []
    slug: str | None = None


class UpdatePost(BaseModel):
    title: str
    body: str
    images: list[str] | None = []


class ReadPost(BaseModel):
    id: UUID
    title: str
    body: str
    images: list[str] | None = []
    slug: str
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class ListPost(BaseModel):
    id: UUID
    title: str
    slug: str
    created_date: datetime

    class Config:
        from_attributes = True
