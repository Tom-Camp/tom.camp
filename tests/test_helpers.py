from app.utils.helpers import structure_post_response, truncate_at_boundary


class TestTruncateAtBoundary:
    def test_short_text_returned_unchanged(self):
        assert truncate_at_boundary("hello", 10) == "hello"

    def test_exact_length_returned_unchanged(self):
        assert truncate_at_boundary("hello world", 11) == "hello world"

    def test_empty_string(self):
        assert truncate_at_boundary("", 10) == ""

    def test_truncates_at_last_space(self):
        # text[:20] = "one two three four f"
        # last space at index 18, last dot at -1 → truncates at space
        text = "one two three four five six seven"
        result = truncate_at_boundary(text, 20)
        assert result.endswith("...")
        assert len(result) <= 23  # 20 chars + "..."

    def test_truncates_at_last_dot_when_ahead_of_space(self):
        # text[:10] = "Aaaaaa.bbb" → last_dot=6, last_space=-1 → idx=6
        text = "Aaaaaa.bbbbbbbbbbbbbbbbb"
        result = truncate_at_boundary(text, 10)
        assert result == "Aaaaaa..."

    def test_prefers_later_boundary(self):
        # text[:20] = "Hello world. Some mo"
        # last_dot=11, last_space=18 → idx=max(11,18)=18 → space wins
        # cuts at space before "mo", giving "Hello world. Some..."
        text = "Hello world. Some more text here"
        result = truncate_at_boundary(text, 20)
        assert result == "Hello world. Some..."

    def test_no_boundary_cuts_hard(self):
        text = "a" * 200
        result = truncate_at_boundary(text, 10)
        assert result == "a" * 10

    def test_truncation_appends_ellipsis(self):
        text = "word " * 50
        result = truncate_at_boundary(text, 30)
        assert result.endswith("...")


class TestStructurePostResponse:
    """Integration-style unit tests — create Post objects via the service layer."""

    def test_parses_body_from_dict(self, db_session):
        from app.schemas.post_schemas import CreatePost
        from app.services.post_service import PostService

        service = PostService(db_session)
        body = {
            "paragraphs": ["First para.", "Second para."],
            "links": [],
            "repo": "https://github.com/example",
        }
        post_data = CreatePost(title="Helper Test", body=body)
        post = service.create_post(post_data)

        result = structure_post_response(post)

        assert result.title == "Helper Test"
        assert result.body.paragraphs == ["First para.", "Second para."]
        assert result.body.repo == "https://github.com/example"

    def test_handles_empty_paragraphs(self, db_session):
        from app.schemas.post_schemas import CreatePost
        from app.services.post_service import PostService

        service = PostService(db_session)
        post = service.create_post(CreatePost(title="Empty Body", body={}))

        result = structure_post_response(post)

        assert result.body.paragraphs == []
        assert result.body.links == []
        assert result.body.repo is None

    def test_maps_links(self, db_session):
        from app.schemas.post_schemas import CreatePost
        from app.services.post_service import PostService

        service = PostService(db_session)
        body = {
            "paragraphs": [],
            "links": [{"url": "https://example.com", "text": "Example"}],
        }
        post = service.create_post(CreatePost(title="Links Post", body=body))

        result = structure_post_response(post)

        assert len(result.body.links) == 1
        assert result.body.links[0].url == "https://example.com"
        assert result.body.links[0].text == "Example"

    def test_maps_images(self, db_session):
        from app.schemas.post_schemas import CreatePost
        from app.services.post_service import PostService

        service = PostService(db_session)
        post = service.create_post(
            CreatePost(title="Image Post", body={"paragraphs": []})
        )
        service.add_image_to_post(post, "photo.jpg", "Caption", "Alt text")

        # Reload with images
        post = service.get_post(post.slug)
        result = structure_post_response(post)

        assert len(result.images) == 1
        assert result.images[0].filename == "photo.jpg"
        assert result.images[0].caption == "Caption"
