from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.post import Tag


class ReadImage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    caption: str | None = None
    alt: str | None = None


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
    images: list[str] = []
    is_published: bool = False
    tags: list[str] = []


class UpdatePost(BaseModel):
    title: str | None = None
    body: str | None = None
    images: list[str] = []
    is_published: bool | None = None
    tags: list[str] = []


class ReadPost(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    body: BodyContent
    images: list[ReadImage] = []
    is_published: bool
    slug: str
    tags: list[Tag] = []
    created_date: datetime


class ListPost(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    slug: str
    teaser: str
    images: list[str] = []
    created_date: datetime
