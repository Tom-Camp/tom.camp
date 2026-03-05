from typing import Any

from flask import Blueprint, abort, render_template, request
from loguru import logger
from slugify import slugify
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
    post_data.slug = slugify(data.get("title"))

    with Session(engine) as session:
        service = PostService(session)
        try:
            post = service.create_post(post_data)
        except ValueError as exc:
            abort(409, description=str(exc))  # slug already exists

        logger.info("Post created: id={} title={!r}", post.id, post.title)
        return post.model_dump(mode="json"), 201


@posts_bp.get("/<string:slug>")
def read_post(slug: str) -> dict:
    with Session(engine) as session:
        service = PostService(session)
        post = service.get_post(slug)
        if not post:
            logger.warning("get_post: post {} not found", slug)
            abort(404, description="Post not found")
        return render_template("posts/index.html", post=post)


@posts_bp.get("/")
def list_posts() -> str:
    with Session(engine) as session:
        service = PostService(session)
        posts = service.list_posts()
        return render_template("posts/list.html", posts=posts)


@posts_bp.get("/tag/<string:tag>")
def list_posts_by_tag(tag: str) -> str:
    with Session(engine) as session:
        service = PostService(session)
        posts = service.list_posts_by_tag(tag)
        return render_template("posts/list_by_tag.html", posts=posts, tag=tag)
