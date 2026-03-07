import json

from app.models.post import Post
from app.schemas.post_schemas import BodyContent, Link, ReadImage, ReadPost


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
    body: dict = json.loads(post.body) if isinstance(post.body, str) else post.body
    links = [
        Link(url=link.get("url"), text=link.get("text"))
        for link in body.get("links", [])
    ]
    content = [paragraph for paragraph in body.get("paragraphs", [])]
    # Convert Image to ReadImage
    images = [
        ReadImage(filename=img.filename, caption=img.caption, alt=img.alt)
        for img in post.images
    ]
    return ReadPost(
        title=post.title,
        body=BodyContent(paragraphs=content, links=links, repo=body.get("repo", None)),
        images=images,
        is_published=post.is_published,
        slug=post.slug,
        tags=post.tags,
        created_date=post.created_date,
    )
