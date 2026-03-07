import io
import json

from sqlmodel import Session

from app.models.post import Post
from app.schemas.post_schemas import CreatePost
from app.services.post_service import PostService

ADMIN_HEADER = {"X-Admin-Secret": "test-admin-secret"}


def seed_post(
    test_engine,
    title: str = "Test Post",
    paragraphs: list[str] | None = None,
    tags: list[str] | None = None,
    is_published: bool = True,
) -> Post:
    """Create a post directly in the DB for route test setup."""
    body = {"paragraphs": paragraphs or ["A paragraph about things."], "links": []}
    post_data = CreatePost(
        title=title, body=json.dumps(body), tags=tags or [], is_published=is_published
    )
    with Session(test_engine) as session:
        return PostService(session).create_post(post_data)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------
class TestIndexRoute:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_renders_page(self, client):
        response = client.get("/")
        assert b"Tom.Camp" in response.data

    def test_shows_post_title(self, client, test_engine):
        seed_post(test_engine, "My Featured Post")
        response = client.get("/")
        assert b"My Featured Post" in response.data

    def test_limits_to_four_posts(self, client, test_engine):
        titles = [f"Featured Post {i}" for i in range(6)]
        for title in titles:
            seed_post(test_engine, title)
        response = client.get("/")
        shown = sum(1 for t in titles if t.encode() in response.data)
        assert shown == 4


# ---------------------------------------------------------------------------
# GET /posts/
# ---------------------------------------------------------------------------
class TestListPostsRoute:
    def test_returns_200(self, client):
        response = client.get("/posts/")
        assert response.status_code == 200

    def test_empty_list_renders_without_error(self, client):
        response = client.get("/posts/")
        assert b"Posts" in response.data

    def test_shows_post_title(self, client, test_engine):
        seed_post(test_engine, "Route Test Post")
        response = client.get("/posts/")
        assert b"Route Test Post" in response.data

    def test_shows_teaser_text(self, client, test_engine):
        seed_post(
            test_engine, "Teaser Post", paragraphs=["This is the intro paragraph."]
        )
        response = client.get("/posts/")
        assert b"This is the intro" in response.data

    def test_shows_continue_reading_link(self, client, test_engine):
        post = seed_post(test_engine, "Link Post")
        response = client.get("/posts/")
        assert post.slug.encode() in response.data


# ---------------------------------------------------------------------------
# GET /posts/<slug>
# ---------------------------------------------------------------------------
class TestReadPostRoute:
    def test_returns_200_for_existing_post(self, client, test_engine):
        post = seed_post(test_engine, "Read Me")
        response = client.get(f"/posts/{post.slug}")
        assert response.status_code == 200

    def test_shows_post_title(self, client, test_engine):
        post = seed_post(test_engine, "Read Me")
        response = client.get(f"/posts/{post.slug}")
        assert b"Read Me" in response.data

    def test_renders_paragraph(self, client, test_engine):
        post = seed_post(
            test_engine, "Para Post", paragraphs=["Unique paragraph content."]
        )
        response = client.get(f"/posts/{post.slug}")
        assert b"Unique paragraph content." in response.data

    def test_shows_tags(self, client, test_engine):
        post = seed_post(test_engine, "Tagged Post", tags=["python"])
        response = client.get(f"/posts/{post.slug}")
        assert b"python" in response.data

    def test_returns_404_for_unknown_slug(self, client):
        response = client.get("/posts/does-not-exist")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /posts/tag/<tag>
# ---------------------------------------------------------------------------
class TestListByTagRoute:
    def test_returns_200_for_existing_tag(self, client, test_engine):
        seed_post(test_engine, "Python Post", tags=["python"])
        response = client.get("/posts/tag/python")
        assert response.status_code == 200

    def test_returns_200_for_unknown_tag(self, client):
        response = client.get("/posts/tag/nonexistent")
        assert response.status_code == 200

    def test_shows_only_matching_posts(self, client, test_engine):
        seed_post(test_engine, "Python Post", tags=["python"])
        seed_post(test_engine, "Flask Post", tags=["flask"])
        response = client.get("/posts/tag/python")
        assert b"Python Post" in response.data
        assert b"Flask Post" not in response.data

    def test_shows_tag_name_in_heading(self, client, test_engine):
        seed_post(test_engine, "Python Post", tags=["python"])
        response = client.get("/posts/tag/python")
        assert b"Python" in response.data


# ---------------------------------------------------------------------------
# POST /posts/
# ---------------------------------------------------------------------------
class TestCreatePostRoute:
    def test_requires_auth_header(self, client):
        response = client.post("/posts/", json={"title": "T", "body": {}})
        assert response.status_code == 401

    def test_wrong_key_returns_401(self, client):
        response = client.post(
            "/posts/",
            json={"title": "T", "body": {}},
            headers={"X-Admin-Secret": "wrong-key"},
        )
        assert response.status_code == 401

    def test_creates_post_successfully(self, client):
        response = client.post(
            "/posts/",
            json={"title": "New Post", "body": {"paragraphs": ["Hello."]}},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "New Post"
        assert data["slug"] == "new-post"

    def test_missing_title_returns_400(self, client):
        response = client.post(
            "/posts/",
            json={"body": {"paragraphs": []}},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 400

    def test_missing_body_returns_400(self, client):
        response = client.post(
            "/posts/",
            json={"title": "No Body"},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 400

    def test_empty_payload_returns_400(self, client):
        response = client.post("/posts/", json={}, headers=ADMIN_HEADER)
        assert response.status_code == 400

    def test_creates_with_tags(self, client):
        response = client.post(
            "/posts/",
            json={
                "title": "Tagged",
                "body": {"paragraphs": []},
                "tags": ["python", "flask"],
            },
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 201

    def test_response_includes_id(self, client):
        response = client.post(
            "/posts/",
            json={"title": "With ID", "body": {"paragraphs": []}},
            headers=ADMIN_HEADER,
        )
        data = response.get_json()
        assert "id" in data


# ---------------------------------------------------------------------------
# POST /posts/<slug>/images
# ---------------------------------------------------------------------------
class TestUploadImageRoute:
    def test_requires_auth_header(self, client, test_engine):
        post = seed_post(test_engine, "Auth Check Post")
        response = client.post(f"/posts/{post.slug}/images")
        assert response.status_code == 401

    def test_returns_404_for_unknown_post(self, client, tmp_path, monkeypatch):
        import app.routes.post_routes as r

        monkeypatch.setattr(r, "UPLOAD_DIR", tmp_path)
        response = client.post("/posts/no-such-post/images", headers=ADMIN_HEADER)
        assert response.status_code == 404

    def test_returns_400_with_no_file(self, client, test_engine, tmp_path, monkeypatch):
        import app.routes.post_routes as r

        monkeypatch.setattr(r, "UPLOAD_DIR", tmp_path)
        post = seed_post(test_engine, "No File Post")
        response = client.post(
            f"/posts/{post.slug}/images",
            headers=ADMIN_HEADER,
            data={},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_returns_400_for_disallowed_extension(
        self, client, test_engine, tmp_path, monkeypatch
    ):
        import app.routes.post_routes as r

        monkeypatch.setattr(r, "UPLOAD_DIR", tmp_path)
        post = seed_post(test_engine, "Bad Ext Post")
        response = client.post(
            f"/posts/{post.slug}/images",
            headers=ADMIN_HEADER,
            data={
                "file": (io.BytesIO(b"data"), "malware.exe"),
                "caption": "c",
                "alt": "a",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_returns_400_when_caption_missing(
        self, client, test_engine, tmp_path, monkeypatch
    ):
        import app.routes.post_routes as r

        monkeypatch.setattr(r, "UPLOAD_DIR", tmp_path)
        post = seed_post(test_engine, "No Caption Post")
        response = client.post(
            f"/posts/{post.slug}/images",
            headers=ADMIN_HEADER,
            data={"file": (io.BytesIO(b"img"), "photo.jpg"), "alt": "alt text"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_returns_400_when_alt_missing(
        self, client, test_engine, tmp_path, monkeypatch
    ):
        import app.routes.post_routes as r

        monkeypatch.setattr(r, "UPLOAD_DIR", tmp_path)
        post = seed_post(test_engine, "No Alt Post")
        response = client.post(
            f"/posts/{post.slug}/images",
            headers=ADMIN_HEADER,
            data={"file": (io.BytesIO(b"img"), "photo.jpg"), "caption": "cap"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_uploads_image_successfully(
        self, client, test_engine, tmp_path, monkeypatch
    ):
        import app.routes.post_routes as r

        monkeypatch.setattr(r, "UPLOAD_DIR", tmp_path)
        post = seed_post(test_engine, "Upload Post")
        response = client.post(
            f"/posts/{post.slug}/images",
            headers=ADMIN_HEADER,
            data={
                "file": (io.BytesIO(b"fake image bytes"), "photo.jpg"),
                "caption": "A nice photo",
                "alt": "Photo description",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["filename"].endswith("photo.jpg")
        assert data["caption"] == "A nice photo"
        assert data["alt"] == "Photo description"

    def test_saved_file_exists_on_disk(
        self, client, test_engine, tmp_path, monkeypatch
    ):
        import app.routes.post_routes as r

        monkeypatch.setattr(r, "UPLOAD_DIR", tmp_path)
        post = seed_post(test_engine, "Disk Check Post")
        client.post(
            f"/posts/{post.slug}/images",
            headers=ADMIN_HEADER,
            data={
                "file": (io.BytesIO(b"fake image bytes"), "disk.jpg"),
                "caption": "cap",
                "alt": "alt",
            },
            content_type="multipart/form-data",
        )
        stored = list(tmp_path.glob("*.jpg"))
        assert len(stored) == 1


# ---------------------------------------------------------------------------
# PUT /posts/<slug>
# ---------------------------------------------------------------------------
class TestUpdatePostRoute:
    def test_requires_auth_header(self, client, test_engine):
        post = seed_post(test_engine, "Update Auth Post")
        response = client.put(f"/posts/{post.slug}", json={"title": "T", "body": {}})
        assert response.status_code == 401

    def test_wrong_key_returns_401(self, client, test_engine):
        post = seed_post(test_engine, "Update Auth Post")
        response = client.put(
            f"/posts/{post.slug}",
            json={"title": "T", "body": {}},
            headers={"X-Admin-Secret": "wrong-key"},
        )
        assert response.status_code == 401

    def test_returns_404_for_unknown_slug(self, client):
        response = client.put(
            "/posts/no-such-post",
            json={"title": "T", "body": {"paragraphs": []}},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 404

    def test_body_only_update_returns_200(self, client, test_engine):
        post = seed_post(test_engine, "Body Only Post")
        response = client.put(
            f"/posts/{post.slug}",
            json={"body": {"paragraphs": ["updated"]}},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 200

    def test_title_only_update_returns_200(self, client, test_engine):
        post = seed_post(test_engine, "Title Only Post")
        response = client.put(
            f"/posts/{post.slug}",
            json={"title": "Title Only Post"},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 200

    def test_updates_post_successfully(self, client, test_engine):
        post = seed_post(test_engine, "Original Title")
        response = client.put(
            f"/posts/{post.slug}",
            json={"title": "Original Title", "body": {"paragraphs": ["Updated body."]}},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Original Title"

    def test_updates_tags(self, client, test_engine):
        post = seed_post(test_engine, "Tag Update Post", tags=["old"])
        response = client.put(
            f"/posts/{post.slug}",
            json={
                "title": "Tag Update Post",
                "body": {"paragraphs": []},
                "tags": ["new"],
            },
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /posts/<slug>
# ---------------------------------------------------------------------------
class TestDeletePostRoute:
    def test_requires_auth_header(self, client, test_engine):
        post = seed_post(test_engine, "Delete Auth Post")
        response = client.delete(f"/posts/{post.slug}")
        assert response.status_code == 401

    def test_wrong_key_returns_401(self, client, test_engine):
        post = seed_post(test_engine, "Delete Auth Post")
        response = client.delete(
            f"/posts/{post.slug}",
            headers={"X-Admin-Secret": "wrong-key"},
        )
        assert response.status_code == 401

    def test_returns_404_for_unknown_slug(self, client):
        response = client.delete("/posts/no-such-post", headers=ADMIN_HEADER)
        assert response.status_code == 404

    def test_deletes_post_successfully(self, client, test_engine):
        post = seed_post(test_engine, "Post To Delete")
        response = client.delete(f"/posts/{post.slug}", headers=ADMIN_HEADER)
        assert response.status_code == 204

    def test_post_no_longer_accessible_after_delete(self, client, test_engine):
        post = seed_post(test_engine, "Gone Post")
        client.delete(f"/posts/{post.slug}", headers=ADMIN_HEADER)
        response = client.get(f"/posts/{post.slug}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
class TestPagination:
    def test_list_posts_page_one(self, client, test_engine):
        for i in range(12):
            seed_post(test_engine, f"Paged Post {i}")
        response = client.get("/posts/?page=1")
        assert response.status_code == 200

    def test_list_posts_page_two_shows_next_batch(self, client, test_engine):
        for i in range(12):
            seed_post(test_engine, f"Batch Post {i}")
        r1 = client.get("/posts/?page=1")
        r2 = client.get("/posts/?page=2")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Page 2 should have different content
        assert r1.data != r2.data

    def test_list_posts_next_link_present_when_more(self, client, test_engine):
        for i in range(11):
            seed_post(test_engine, f"Next Link Post {i}")
        response = client.get("/posts/?page=1")
        assert b"page=2" in response.data

    def test_list_posts_no_next_link_on_last_page(self, client, test_engine):
        for i in range(3):
            seed_post(test_engine, f"Short List Post {i}")
        response = client.get("/posts/?page=1")
        assert b"page=2" not in response.data

    def test_list_by_tag_pagination(self, client, test_engine):
        for i in range(12):
            seed_post(test_engine, f"Tagged Paged {i}", tags=["python"])
        response = client.get("/posts/tag/python?page=1")
        assert b"page=2" in response.data


# ---------------------------------------------------------------------------
# Published / draft state
# ---------------------------------------------------------------------------
class TestPublishedState:
    def test_draft_not_shown_in_list(self, client, test_engine):
        seed_post(test_engine, "Draft Post", is_published=False)
        response = client.get("/posts/")
        assert b"Draft Post" not in response.data

    def test_published_shown_in_list(self, client, test_engine):
        seed_post(test_engine, "Live Post", is_published=True)
        response = client.get("/posts/")
        assert b"Live Post" in response.data

    def test_draft_returns_404_on_read(self, client, test_engine):
        post = seed_post(test_engine, "Hidden Post", is_published=False)
        response = client.get(f"/posts/{post.slug}")
        assert response.status_code == 404

    def test_draft_not_shown_in_tag_list(self, client, test_engine):
        seed_post(test_engine, "Draft Tagged", tags=["python"], is_published=False)
        response = client.get("/posts/tag/python")
        assert b"Draft Tagged" not in response.data

    def test_create_post_defaults_to_draft(self, client):
        response = client.post(
            "/posts/",
            json={"title": "Unpublished Post", "body": {"paragraphs": []}},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 201
        assert response.get_json()["is_published"] is False

    def test_create_post_can_be_published(self, client):
        response = client.post(
            "/posts/",
            json={
                "title": "Published Post",
                "body": {"paragraphs": []},
                "is_published": True,
            },
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 201
        assert response.get_json()["is_published"] is True

    def test_update_publishes_draft(self, client, test_engine):
        post = seed_post(test_engine, "To Publish", is_published=False)
        response = client.put(
            f"/posts/{post.slug}",
            json={"is_published": True},
            headers=ADMIN_HEADER,
        )
        assert response.status_code == 200
        assert response.get_json()["is_published"] is True


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
class TestErrorHandlers:
    def test_404_returns_html_for_browser(self, client):
        response = client.get("/posts/no-such-slug")
        assert response.status_code == 404
        assert b"404" in response.data

    def test_404_returns_json_for_api_client(self, client):
        response = client.get(
            "/posts/no-such-slug", headers={"Accept": "application/json"}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_401_returns_json_for_api_client(self, client):
        response = client.post(
            "/posts/",
            json={"title": "T", "body": {}},
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 401
        assert "error" in response.get_json()

    def test_partial_update_empty_body_returns_400(self, client, test_engine):
        post = seed_post(test_engine, "Partial Post")
        response = client.put(f"/posts/{post.slug}", json={}, headers=ADMIN_HEADER)
        assert response.status_code == 400
