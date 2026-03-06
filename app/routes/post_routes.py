import json
from typing import Any

from flask import Blueprint, abort, render_template, request
from loguru import logger
from slugify import slugify
from sqlmodel import Session

from app.models.post import Post
from app.schemas.post_schemas import BodyContent, CreatePost, Link, ReadPost
from app.services.post_service import PostService
from app.utils.auth import require_admin
from app.utils.database import engine

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


def _structure_post_reponse(post: Post) -> ReadPost:
    post_body = json.loads(post.body) if post and post.body else {}
    links = [
        Link(url=link.get("url"), text=link.get("text"))
        for link in post_body.get("links", [])
    ]
    content = [paragraph for paragraph in post_body.get("paragraphs", [])]
    return ReadPost(
        title=post.title,
        body=BodyContent(
            paragraphs=content, links=links, repo=post_body.get("repo", None)
        ),
        images=post.images,
        slug=post.slug,
        tags=post.tags,
        created_date=post.created_date,
    )


@posts_bp.post("/")
@require_admin
def create_post() -> tuple[dict, int]:
    data: dict[str, Any] = request.get_json(force=True, silent=True) or {}
    logger.warning("create_post called with data: {}", data.get("title"))
    if not data.get("title") or not data.get("body"):
        logger.warning("create_post rejected: missing title or body: {}", data)
        abort(400, description="title and body are required")

    post_data = CreatePost(
        title=data.get("title"),
        body=json.dumps(data.get("body", {})),
        slug=slugify(data.get("title")),
        tags=data.get("tags", []),
    )

    with Session(engine) as session:
        service = PostService(session)
        try:
            post = service.create_post(post_data)
        except ValueError as exc:
            abort(409, description=str(exc))  # slug already exists

        logger.info("Post created: id={} title={!r}", post.id, post.title)
        return post.model_dump(mode="json"), 201


@posts_bp.get("/<string:slug>")
def read_post(slug: str) -> str:
    with Session(engine) as session:
        service = PostService(session)

        post: Post | None = service.get_post(slug)
        if post is None:
            logger.warning("get_post: post {} not found", slug)
            abort(404, description="Post not found")

        full_post = _structure_post_reponse(post=post)  # type: ignore
        return render_template("posts/index.html", post=full_post)


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
