from uuid import UUID

from loguru import logger
from sqlmodel import Session

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

    def get_post(self, post_id: UUID) -> Post | None:
        return self._db.get(Post, post_id)

    def update_post(self, post_id: UUID, data: UpdatePost) -> Post | None:
        post = self._db.get(Post, post_id)
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
