from typing import Any

from flask import Blueprint, abort, request
from loguru import logger
from sqlmodel import Session

from app.schemas.post_schemas import CreatePost
from app.services.post_service import PostService
from app.utils.auth import require_admin
from app.utils.database import engine

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


@posts_bp.post("/")
@require_admin
def create_post() -> tuple[dict, int]:
    data: dict[str, Any] = request.get_json(force=True, silent=True) or {}
    logger.warning("create_post called with data: {}", data)
    if not data.get("title") or not data.get("body"):
        logger.warning("create_post rejected: missing title or body: {}", data)
        abort(400, description="title and body are required")

    post_data = CreatePost(**data)

    with Session(engine) as session:
        service = PostService(session)
        post = service.create_post(post_data)
        logger.info("Post created: id={} title={!r}", post.id, post.title)
        return post.model_dump(mode="json"), 201
