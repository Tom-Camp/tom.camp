from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TagRead(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class CreatePost(BaseModel):
    title: str
    body: str
    images: list[str] | None = []
    slug: str | None = None
    tags: list[str] | None = []


class UpdatePost(BaseModel):
    title: str
    body: str
    images: list[str] | None = []
    tags: list[str] | None = None


class ReadPost(BaseModel):
    id: UUID
    title: str
    body: str
    images: list[str] | None = []
    slug: str
    tags: list[TagRead] = []
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
