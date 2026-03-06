from typing import Any
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import ModelBase


class PostTagLink(SQLModel, table=True):  # type: ignore
    """Link table for many-to-many relationship between Post and Tag."""

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

    def __repr__(self):
        return f"<PostTagLink post_id={self.post_id} tag_id={self.tag_id}>"


class Tag(ModelBase, table=True):  # type: ignore
    """Tag model for categorizing posts."""

    name: str = Field(..., unique=True)
    posts: list["Post"] = Relationship(back_populates="tags", link_model=PostTagLink)

    def __repr__(self):
        return f"<Tag name={self.name}>"


class Image(ModelBase, table=True):  # type: ignore
    """Image model for storing post images."""

    filename: str = Field(..., unique=True)
    caption: str | None = Field(default=None, nullable=True)
    alt: str | None = Field(default=None, nullable=True)
    post_id: UUID = Field(foreign_key="post.id", nullable=False, ondelete="CASCADE")
    post: "Post" = Relationship(back_populates="images")

    def __repr__(self):
        return f"<Image filename={self.filename} post_id={self.post_id}>"


class Post(ModelBase, table=True):  # type: ignore
    """Post model representing blog posts."""

    title: str = Field(..., unique=True)
    body: dict[str, Any] = Field(
        sa_column=Column(JSONB, nullable=False, default=dict),
    )
    images: list[Image] = Relationship(back_populates="post")
    slug: str | None = Field(default=None, unique=True)
    tags: list[Tag] = Relationship(back_populates="posts", link_model=PostTagLink)

    def __repr__(self):
        return f"<Post title={self.title} slug={self.slug}>"
