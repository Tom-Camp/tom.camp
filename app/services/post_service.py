from uuid import UUID

from loguru import logger
from sqlalchemy import Sequence
from sqlmodel import Session, select

from app.models.post import Post, Tag
from app.schemas.post_schemas import CreatePost, UpdatePost


class PostService:

    def __init__(self, session: Session):
        self._db = session

    @staticmethod
    def _normalize_tags(tags: list[str] | None) -> list[str]:
        if not tags:
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            value = tag.strip().lower()
            if value and value not in seen:
                normalized.append(value)
                seen.add(value)
        return normalized

    def _get_or_create_tags(self, tags: list[str] | None) -> list[Tag]:
        tag_models: list[Tag] = []
        for name in self._normalize_tags(tags):
            statement = select(Tag).where(Tag.name == name)
            existing = self._db.exec(statement).first()
            if existing:
                tag_models.append(existing)
                continue
            new_tag = Tag(name=name)
            self._db.add(new_tag)
            tag_models.append(new_tag)
        return tag_models

    def create_post(self, post: CreatePost) -> Post:
        payload = post.model_dump(exclude={"tags"})
        new_post = Post(**payload)
        new_post.tags = self._get_or_create_tags(post.tags)
        self._db.add(new_post)
        self._db.commit()
        self._db.refresh(new_post)
        return new_post

    def get_post(self, slug: str) -> Post | None:
        statement = select(Post).where(Post.slug == slug)
        return self._db.exec(statement).first()

    def update_post(self, post_id: UUID, data: UpdatePost) -> Post | None:
        post: Post | None = self._db.get(Post, post_id)
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
        self, skip: int = 0, limit: int = 10, order="desc"
    ) -> Sequence[Post]:
        statement = (
            select(Post)
            .offset(skip)
            .limit(limit)
            .order_by(
                Post.created_date.desc()  # type: ignore[union-attr]
                if order == "desc"
                else Post.created_date.asc()  # type: ignore[union-attr]
            )
        )
        posts = self._db.exec(statement).all()
        return posts

    def list_posts_by_tag(
        self, tag: str, skip: int = 0, limit: int = 10, order="desc"
    ) -> Sequence[Post]:
        statement = (
            select(Post)
            .join(Post.tags)
            .where(Tag.name == tag.strip().lower())
            .offset(skip)
            .limit(limit)
            .order_by(
                Post.created_date.desc()  # type: ignore[union-attr]
                if order == "desc"
                else Post.created_date.asc()  # type: ignore[union-attr]
            )
        )
        posts = self._db.exec(statement).all()
        return posts
