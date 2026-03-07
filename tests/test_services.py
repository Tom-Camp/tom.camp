import uuid

import pytest
from sqlmodel import Session, select

from app.models.post import Post, Tag
from app.schemas.post_schemas import CreatePost, UpdatePost
from app.services.post_service import PostService


def make_post_data(
    title: str = "Test Post",
    paragraphs: list[str] | None = None,
    tags: list[str] | None = None,
    is_published: bool = True,
) -> CreatePost:
    body = {"paragraphs": paragraphs or ["Hello world."], "links": []}
    return CreatePost(
        title=title, body=body, tags=tags or [], is_published=is_published
    )


@pytest.fixture
def service(db_session: Session) -> PostService:
    return PostService(db_session)


@pytest.fixture
def existing_post(service: PostService) -> Post:
    return service.create_post(make_post_data())


class TestNormalizeTags:
    def test_lowercases_tags(self, service):
        post = service.create_post(make_post_data(tags=["Python", "FLASK"]))
        names = {t.name for t in post.tags}
        assert names == {"python", "flask"}

    def test_strips_whitespace(self, service):
        post = service.create_post(make_post_data(tags=["  python  "]))
        assert post.tags[0].name == "python"

    def test_deduplicates_tags(self, service):
        post = service.create_post(make_post_data(tags=["python", "Python", "PYTHON"]))
        assert len(post.tags) == 1

    def test_ignores_empty_strings(self, service):
        post = service.create_post(make_post_data(tags=["", "   "]))
        assert post.tags == []

    def test_reuses_existing_tag_row(self, service, db_session):
        service.create_post(make_post_data("Post 1", tags=["python"]))
        service.create_post(make_post_data("Post 2", tags=["python"]))
        tags = db_session.exec(select(Tag)).all()
        assert len(tags) == 1


class TestCreatePost:
    def test_returns_post_with_id(self, service):
        post = service.create_post(make_post_data())
        assert post.id is not None

    def test_slug_generated_from_title(self, service):
        post = service.create_post(make_post_data(title="Hello World Post"))
        assert post.slug == "hello-world-post"

    def test_body_round_trips(self, service):
        post = service.create_post(
            make_post_data(paragraphs=["Para one.", "Para two."])
        )
        assert post.body["paragraphs"] == ["Para one.", "Para two."]

    def test_creates_tags(self, service):
        post = service.create_post(make_post_data(tags=["python", "flask"]))
        assert {t.name for t in post.tags} == {"python", "flask"}

    def test_no_tags(self, service):
        post = service.create_post(make_post_data())
        assert post.tags == []

    def test_created_date_is_set(self, service):
        post = service.create_post(make_post_data())
        assert post.created_date is not None


class TestGetPost:
    def test_returns_post_by_slug(self, service, existing_post):
        found = service.get_post(existing_post.slug)
        assert found is not None
        assert found.id == existing_post.id

    def test_returns_none_for_unknown_slug(self, service):
        assert service.get_post("does-not-exist") is None

    def test_eager_loads_images_and_tags(self, service):
        post = service.create_post(make_post_data(tags=["python"]))
        found = service.get_post(post.slug)
        # Accessing these outside the session must not raise
        assert isinstance(found.tags, list)
        assert isinstance(found.images, list)


class TestUpdatePost:
    def test_updates_title(self, service, existing_post):
        data = UpdatePost(title="Updated Title", body={"paragraphs": []})
        updated = service.update_post(existing_post.id, data)
        assert updated is not None
        assert updated.title == "Updated Title"

    def test_updates_tags(self, service, existing_post):
        data = UpdatePost(title="Test Post", body={}, tags=["newtag"])
        updated = service.update_post(existing_post.id, data)
        assert {t.name for t in updated.tags} == {"newtag"}

    def test_replaces_tags(self, service):
        post = service.create_post(make_post_data(tags=["old"]))
        data = UpdatePost(title="Test Post", body={}, tags=["new"])
        updated = service.update_post(post.id, data)
        assert {t.name for t in updated.tags} == {"new"}

    def test_returns_none_for_unknown_id(self, service):
        data = UpdatePost(title="x", body={})
        assert service.update_post(uuid.uuid4(), data) is None


class TestDeletePost:
    def test_deletes_existing_post(self, service, existing_post, db_session):
        result = service.delete_post(existing_post.id)
        assert result is True
        assert db_session.get(Post, existing_post.id) is None

    def test_returns_false_for_unknown_id(self, service):
        assert service.delete_post(uuid.uuid4()) is False


class TestListPosts:
    def test_returns_empty_sequence(self, service):
        assert list(service.list_posts()) == []

    def test_returns_all_posts(self, service):
        service.create_post(make_post_data("Post A"))
        service.create_post(make_post_data("Post B"))
        assert len(service.list_posts()) == 2

    def test_respects_limit(self, service):
        for i in range(5):
            service.create_post(make_post_data(f"Post {i}"))
        assert len(service.list_posts(limit=3)) == 3

    def test_respects_skip(self, service):
        for i in range(5):
            service.create_post(make_post_data(f"Post {i}"))
        assert len(service.list_posts(skip=3, limit=10)) == 2

    def test_accepts_asc_order(self, service):
        service.create_post(make_post_data("Post A"))
        service.create_post(make_post_data("Post B"))
        posts = service.list_posts(order="asc")
        assert len(posts) == 2

    def test_accepts_desc_order(self, service):
        service.create_post(make_post_data("Post A"))
        service.create_post(make_post_data("Post B"))
        posts = service.list_posts(order="desc")
        assert len(posts) == 2

    def test_loads_images_and_tags(self, service):
        service.create_post(make_post_data(tags=["python"]))
        posts = service.list_posts()
        assert isinstance(posts[0].tags, list)
        assert isinstance(posts[0].images, list)


class TestListPostsByTag:
    def test_filters_by_tag(self, service):
        service.create_post(make_post_data("Tagged Post", tags=["python"]))
        service.create_post(make_post_data("Other Post", tags=["flask"]))
        posts = service.list_posts_by_tag("python")
        assert len(posts) == 1
        assert posts[0].title == "Tagged Post"

    def test_returns_empty_for_unknown_tag(self, service):
        service.create_post(make_post_data(tags=["python"]))
        assert list(service.list_posts_by_tag("java")) == []

    def test_tag_matching_is_case_insensitive(self, service):
        # Tags are stored lowercase; lookup normalises via Tag.name == tag.strip().lower()
        service.create_post(make_post_data(tags=["python"]))
        posts = service.list_posts_by_tag("python")
        assert len(posts) == 1

    def test_respects_limit(self, service):
        for i in range(5):
            service.create_post(make_post_data(f"Post {i}", tags=["python"]))
        assert len(service.list_posts_by_tag("python", limit=2)) == 2


class TestAddImageToPost:
    def test_adds_image_to_post(self, service, existing_post):
        image = service.add_image_to_post(
            existing_post, "photo.jpg", "Caption", "Alt text"
        )
        assert image.id is not None
        assert image.filename == "photo.jpg"
        assert image.post_id == existing_post.id

    def test_stores_caption_and_alt(self, service, existing_post):
        image = service.add_image_to_post(
            existing_post, "photo.jpg", "My caption", "My alt"
        )
        assert image.caption == "My caption"
        assert image.alt == "My alt"

    def test_raises_on_duplicate_filename(self, service, existing_post):
        service.add_image_to_post(existing_post, "photo.jpg", "cap", "alt")
        with pytest.raises(ValueError, match="already exists"):
            service.add_image_to_post(existing_post, "photo.jpg", "cap2", "alt2")

    def test_allows_null_caption_and_alt(self, service, existing_post):
        image = service.add_image_to_post(existing_post, "photo.jpg", None, None)
        assert image.caption is None
        assert image.alt is None


class TestPublishedFiltering:
    def test_list_posts_excludes_drafts_by_default(self, service):
        service.create_post(make_post_data("Draft", is_published=False))
        assert list(service.list_posts()) == []

    def test_list_posts_includes_published(self, service):
        service.create_post(make_post_data("Live", is_published=True))
        assert len(service.list_posts()) == 1

    def test_list_posts_only_published_false_returns_all(self, service):
        service.create_post(make_post_data("Draft", is_published=False))
        service.create_post(make_post_data("Live", is_published=True))
        assert len(service.list_posts(only_published=False)) == 2

    def test_get_post_only_published_hides_draft(self, service):
        post = service.create_post(make_post_data(is_published=False))
        assert service.get_post(post.slug, only_published=True) is None

    def test_get_post_only_published_false_returns_draft(self, service):
        post = service.create_post(make_post_data(is_published=False))
        assert service.get_post(post.slug, only_published=False) is not None

    def test_list_posts_by_tag_excludes_drafts(self, service):
        service.create_post(make_post_data(tags=["python"], is_published=False))
        assert list(service.list_posts_by_tag("python")) == []

    def test_list_posts_by_tag_includes_published(self, service):
        service.create_post(make_post_data(tags=["python"], is_published=True))
        assert len(service.list_posts_by_tag("python")) == 1
