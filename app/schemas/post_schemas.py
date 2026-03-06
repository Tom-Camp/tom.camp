from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.post import Tag


class Link(BaseModel):
    url: str
    text: str | None = None
    title: str | None = None
    description: str | None = None


class BodyContent(BaseModel):
    paragraphs: list[str] = []
    links: list[Link] = []
    repo: str | None = None


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
    title: str
    body: BodyContent
    images: list[str] | None = []
    slug: str
    tags: list[Tag] = []
    created_date: datetime

    class Config:
        from_attributes = True


class ListPost(BaseModel):
    id: UUID
    title: str
    slug: str
    created_date: datetime

    class Config:
        from_attributes = True
