import json

from app.models.post import Post
from app.schemas.post_schemas import BodyContent, Link, ReadPost


def truncate_at_boundary(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text

    cut = text[:max_len]

    last_dot = cut.rfind(".")
    last_space = cut.rfind(" ")
    idx = max(last_dot, last_space)

    if idx == -1:
        return cut

    return f"{cut[:idx]}..."


def structure_post_response(post: Post) -> ReadPost:
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
