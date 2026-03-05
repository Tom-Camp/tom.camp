from uuid import UUID

from pydantic import model_validator
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import ModelBase


class PostTagLink(SQLModel, table=True):  # type: ignore
    post_id: UUID = Field(
        foreign_key="post.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )
    tag_id: UUID = Field(
        foreign_key="tags.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )


class Tags(ModelBase, table=True):  # type: ignore
    name: str = Field(..., unique=True)
    posts: list["Post"] = Relationship(back_populates="tags", link_model=PostTagLink)

    @model_validator(mode="before")
    @classmethod
    def validate_name(cls, values):
        name = values.get("name")
        if name:
            values["name"] = name.strip().lower()
        return values


class Post(ModelBase, table=True):  # type: ignore
    title: str = Field(..., unique=True)
    body: str
    images: list[str] = Field(
        default_factory=list, sa_type=JSON, description="List of image filenames"
    )
    slug: str | None = None
    tags: list[Tags] = Relationship(back_populates="posts", link_model=PostTagLink)
