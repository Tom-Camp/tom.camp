from uuid import UUID

from loguru import logger
from sqlalchemy import Sequence
from sqlmodel import Session, select

from app.models.post import Post
from app.schemas.post_schemas import CreatePost, UpdatePost


class PostService:

    def __init__(self, session: Session):
        self._db = session

    def create_post(self, post: CreatePost) -> Post:
        new_post = Post(**post.model_dump())
        self._db.add(new_post)
        self._db.commit()
        self._db.refresh(new_post)
        return new_post

    def get_post(self, slug: str) -> Post | None:
        statement = select(Post).where(Post.slug == slug)
        result = self._db.execute(statement)
        return result.scalars().first()

    def update_post(self, post_id: UUID, data: UpdatePost) -> Post | None:
        post: Post | None = self._db.get(Post, post_id)
        if not post:
            logger.warning("update_post: post {} not found", post_id)
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
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
        result = self._db.execute(statement)
        posts = result.scalars().all()
        return posts
