from pydantic import BaseModel


class CreatePost(BaseModel):
    title: str
    body: str
    images: list[str] | None = []


class UpdatePost(BaseModel):
    title: str
    body: str
    images: list[str] | None = []
