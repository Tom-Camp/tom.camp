from typing import Literal
from uuid import UUID

from loguru import logger
from slugify import slugify
from sqlalchemy import Sequence
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.post import Image, Post, Tag
from app.schemas.post_schemas import CreatePost, UpdatePost


class PostService:

    def __init__(self, session: Session):
        self._db = session

    @staticmethod
    def _normalize_tags(tags: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            value = tag.strip().lower()
            if value and value not in seen:
                normalized.append(value)
                seen.add(value)
        return normalized

    def _get_or_create_tags(self, tags: list[str]) -> list[Tag]:
        names = self._normalize_tags(tags)
        if not names:
            return []
        existing = self._db.exec(select(Tag).where(Tag.name.in_(names))).all()  # type: ignore[attr-defined]
        existing_by_name = {t.name: t for t in existing}
        tag_models: list[Tag] = []
        for name in names:
            if name in existing_by_name:
                tag_models.append(existing_by_name[name])
            else:
                new_tag = Tag(name=name)
                self._db.add(new_tag)
                tag_models.append(new_tag)
        return tag_models

    @staticmethod
    def _order_by(order: Literal["asc", "desc"]):  # type: ignore[return]
        if order == "desc":
            return Post.created_date.desc()  # type: ignore[attr-defined]
        return Post.created_date.asc()  # type: ignore[attr-defined]

    def create_post(self, post: CreatePost) -> Post:
        payload = post.model_dump(exclude={"tags", "images"})
        new_post = Post(**payload, slug=slugify(post.title))
        new_post.tags = self._get_or_create_tags(post.tags)
        self._db.add(new_post)
        self._db.commit()
        self._db.refresh(new_post)
        return new_post

    def get_post(self, slug: str) -> Post | None:
        statement = (
            select(Post)
            .where(Post.slug == slug)
            .options(selectinload(Post.images), selectinload(Post.tags))
        )
        return self._db.exec(statement).first()

    def update_post(self, post_id: UUID, data: UpdatePost) -> Post | None:
        statement = (
            select(Post).where(Post.id == post_id).options(selectinload(Post.images))
        )
        post: Post | None = self._db.exec(statement).first()
        if not post:
            logger.warning("update_post: post {} not found", post_id)
            return None

        updates = data.model_dump(exclude_unset=True)
        if "tags" in updates:
            post.tags = self._get_or_create_tags(updates.pop("tags"))

        for field, value in updates.items():
            setattr(post, field, value)

        self._db.add(post)
        self._db.commit()
        self._db.refresh(post)
        logger.info("Post updated: id={}", post_id)
        return post

    def delete_post(self, post_id: UUID) -> bool:
        post = self._db.get(Post, post_id)
        if not post:
            logger.warning("delete_post: post {} not found", post_id)
            return False
        self._db.delete(post)
        self._db.commit()
        logger.info("Post deleted: id={}", post_id)
        return True

    def list_posts(
        self, skip: int = 0, limit: int = 10, order: Literal["asc", "desc"] = "desc"
    ) -> Sequence[Post]:
        statement = (
            select(Post)
            .options(selectinload(Post.images))
            .options(selectinload(Post.tags))
            .offset(skip)
            .limit(limit)
            .order_by(self._order_by(order))
        )
        return self._db.exec(statement).all()

    def list_posts_by_tag(
        self,
        tag: str,
        skip: int = 0,
        limit: int = 10,
        order: Literal["asc", "desc"] = "desc",
    ) -> Sequence[Post]:
        statement = (
            select(Post)
            .join(Post.tags)
            .where(Tag.name == tag.strip().lower())
            .options(selectinload(Post.images))
            .offset(skip)
            .limit(limit)
            .order_by(self._order_by(order))
        )
        return self._db.exec(statement).all()

    def add_image_to_post(
        self,
        post: Post,
        filename: str,
        caption: str | None,
        alt: str | None,
    ) -> Image:
        existing = self._db.exec(
            select(Image).where(Image.filename == filename)
        ).first()
        if existing:
            raise ValueError(f"Image with filename {filename!r} already exists")

        image = Image(
            filename=filename,
            caption=caption,
            alt=alt,
            post_id=post.id,
        )
        self._db.add(image)
        self._db.commit()
        self._db.refresh(image)
        return image
