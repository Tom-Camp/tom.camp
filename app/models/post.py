from uuid import UUID

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import ModelBase

JSONType = JSON().with_variant(JSONB(), "postgresql")


class PostTagLink(SQLModel, table=True):  # type: ignore
    post_id: UUID = Field(
        foreign_key="post.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )
    tag_id: UUID = Field(
        foreign_key="tag.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )


class Tag(ModelBase, table=True):  # type: ignore
    name: str = Field(..., unique=True)
    posts: list["Post"] = Relationship(back_populates="tags", link_model=PostTagLink)


class Image(ModelBase, table=True):  # type: ignore
    filename: str = Field(..., unique=True)
    caption: str
    alt: str
    post_id: UUID = Field(foreign_key="post.id", nullable=False)
    post: "Post" = Relationship(back_populates="images")


class Post(ModelBase, table=True):  # type: ignore
    title: str = Field(..., unique=True)
    body: str = Field(
        default_factory=dict,
        sa_type=JSONType,
        nullable=False,
    )
    images: list[Image] | None = Relationship(back_populates="post")
    slug: str | None = None
    tags: list[Tag] = Relationship(back_populates="posts", link_model=PostTagLink)
