import json
from pathlib import Path
from typing import Any

from flask import Blueprint, abort, render_template, request, send_from_directory
from loguru import logger
from sqlmodel import Session
from werkzeug.utils import secure_filename

from app.models.post import Post
from app.schemas.post_schemas import CreatePost, ListPost, UpdatePost
from app.services.post_service import PostService
from app.utils.auth import require_admin
from app.utils.config import settings
from app.utils.database import engine
from app.utils.helpers import structure_post_response, truncate_at_boundary

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
UPLOAD_DIR = Path(settings.UPLOAD_DIR)


def _allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


@posts_bp.post("/")
@require_admin
def create_post() -> tuple[dict, int]:
    data: dict[str, Any] = request.get_json(silent=True) or {}
    logger.warning("create_post called with data: {}", data.get("title"))
    if not data.get("title") or not data.get("body"):
        logger.warning("create_post rejected: missing title or body: {}", data)
        abort(400, description="title and body are required")

    post_data = CreatePost(
        title=data.get("title"),
        body=json.dumps(data.get("body", {})),
        tags=data.get("tags", []),
        is_published=data.get("is_published", False),
    )

    with Session(engine) as session:
        service = PostService(session)
        try:
            post = service.create_post(post_data)
        except ValueError as exc:
            abort(409, description=str(exc))

        logger.info("Post created: id={} title={!r}", post.id, post.title)
        return post.model_dump(mode="json"), 201


PAGE_SIZE = 10


def _format_posts(posts: list) -> list[ListPost]:
    formatted = []
    for post in posts:
        try:
            first_paragraph = json.loads(post.body).get("paragraphs", [""])[0]
        except json.JSONDecodeError:
            first_paragraph = ""
        except IndexError:
            first_paragraph = ""
        formatted.append(
            ListPost(
                title=post.title,
                slug=post.slug,
                teaser=truncate_at_boundary(first_paragraph, 150),
                created_date=post.created_date,
            )
        )
    return formatted


@posts_bp.get("/")
def list_posts() -> str:
    page = max(1, request.args.get("page", 1, type=int))
    skip = (page - 1) * PAGE_SIZE
    with Session(engine) as session:
        service = PostService(session)
        batch = service.list_posts(skip=skip, limit=PAGE_SIZE + 1)
        has_next = len(batch) > PAGE_SIZE
        formatted_posts = _format_posts(list(batch[:PAGE_SIZE]))
    return render_template(
        "posts/list.html",
        posts=formatted_posts,
        page=page,
        has_prev=page > 1,
        has_next=has_next,
    )


@posts_bp.get("/images/<path:filename>")
def serve_image(filename: str) -> Any:
    return send_from_directory(UPLOAD_DIR, filename)


@posts_bp.get("/tag/<string:tag>")
def list_posts_by_tag(tag: str) -> str:
    page = max(1, request.args.get("page", 1, type=int))
    skip = (page - 1) * PAGE_SIZE
    with Session(engine) as session:
        service = PostService(session)
        batch = service.list_posts_by_tag(tag, skip=skip, limit=PAGE_SIZE + 1)
        has_next = len(batch) > PAGE_SIZE
        formatted_posts = _format_posts(list(batch[:PAGE_SIZE]))
    return render_template(
        "posts/list_by_tag.html",
        posts=formatted_posts,
        tag=tag,
        page=page,
        has_prev=page > 1,
        has_next=has_next,
    )


@posts_bp.get("/<string:slug>")
def read_post(slug: str) -> str:
    with Session(engine) as session:
        service = PostService(session)

        post: Post | None = service.get_post(slug, only_published=True)
        if post is None:
            logger.warning("get_post: post {} not found", slug)
            abort(404, description="Post not found")
        assert post is not None

        full_post = structure_post_response(post=post)
        return render_template("posts/index.html", post=full_post)


@posts_bp.put("/<string:slug>")
@require_admin
def update_post(slug: str) -> tuple[dict, int]:
    data: dict[str, Any] = request.get_json(silent=True) or {}
    if not data:
        abort(400, description="No update data provided")

    with Session(engine) as session:
        service = PostService(session)
        post: Post | None = service.get_post(slug)
        if post is None:
            abort(404, description="Post not found")
        assert post is not None

        post_fields: dict[str, Any] = {}
        if "title" in data:
            post_fields["title"] = data["title"]
        if "body" in data:
            post_fields["body"] = json.dumps(data["body"])
        if "tags" in data:
            post_fields["tags"] = data["tags"]
        if "is_published" in data:
            post_fields["is_published"] = data["is_published"]

        post_data = UpdatePost(**post_fields)
        updated = service.update_post(post.id, post_data)
        assert updated is not None

        logger.info("Post updated: slug={!r}", slug)
        return updated.model_dump(mode="json"), 200


@posts_bp.delete("/<string:slug>")
@require_admin
def delete_post(slug: str) -> tuple[dict, int]:
    with Session(engine) as session:
        service = PostService(session)
        post: Post | None = service.get_post(slug)
        if post is None:
            abort(404, description="Post not found")
        assert post is not None

        service.delete_post(post.id)
        logger.info("Post deleted: slug={!r}", slug)
        return {}, 204


@posts_bp.post("/<string:slug>/images")
@require_admin
def upload_image(slug: str) -> tuple[dict, int]:
    with Session(engine) as session:
        service = PostService(session)

        post: Post | None = service.get_post(slug)
        if post is None:
            logger.warning("upload_image: post {} not found", slug)
            abort(404, description="Post not found")
        assert post is not None

        file = request.files.get("file")
        if not file or not file.filename:
            abort(400, description="No file provided")
        if not _allowed_file(file.filename):
            abort(400, description="File type not allowed")

        caption: str = request.form.get("caption", "")
        alt: str = request.form.get("alt", "")
        if not caption or not alt:
            abort(400, description="caption and alt are required")

        safe_name = secure_filename(file.filename)
        # Prefix with post slug to avoid collisions across posts
        stored_name = f"{slug}__{safe_name}"
        dest = UPLOAD_DIR / stored_name

        dest.parent.mkdir(parents=True, exist_ok=True)
        file.save(dest)

        try:
            image = service.add_image_to_post(
                post=post,
                filename=stored_name,
                caption=caption,
                alt=alt,
            )
        except ValueError as exc:
            dest.unlink(missing_ok=True)
            abort(409, description=str(exc))
        except Exception:
            dest.unlink(missing_ok=True)
            raise

        assert image is not None

        logger.info("Image uploaded: {} → post {!r}", stored_name, post.title)
        return image.model_dump(mode="json"), 201
