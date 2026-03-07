# tom.camp

A Flask blog application with a JSON-structured post body, image uploads, and tag-based filtering. Uses
SQLModel (SQLAlchemy + Pydantic) for the ORM and PostgreSQL for persistence.

## Stack

- **Python 3.14+** with [uv](https://github.com/astral-sh/uv) for package management
- **Flask 3** — web framework
- **SQLModel** — ORM (SQLAlchemy + Pydantic)
- **PostgreSQL** — database
- **Loguru** — structured logging
- **Docker Compose** — dev and production environments

## Project Structure

```
app/
  main.py          # App factory (create_app)
  models/          # SQLModel table definitions (Post, Tag, Image)
  routes/          # Flask blueprints
  schemas/         # Pydantic request/response schemas
  services/        # Business logic
  utils/           # Config, database, auth, helpers, logging
  templates/       # Jinja2 HTML templates
  static/          # Static assets
tests/             # pytest test suite
```

## Setup

### 1. Install dependencies

```bash
uv sync --group dev
```

### 2. Configure environment

Copy `.env.example` to `.env` (or create `.env`) and set:

```env
ADMIN_SECRET_KEY=your-secret
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=dbname
DB_HOST=localhost
DB_PORT=5432
FLASK_SECRET_KEY=your-flask-secret
```

### 3. Run (local)

```bash
uv run flask run
```

### 4. Run (Docker — dev)

```bash
docker compose up
```

This starts the Flask app and a PostgreSQL container (`tcdata`), with source code mounted as a volume and
hot reload enabled.

### 5. Run (Docker — production)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run linting and formatting
uv run pre-commit run --all-files
```

**Linting stack:** black, isort (black profile), flake8 (max line 109), mypy, bandit.

## API

Admin routes require the `X-Admin-Secret` header matching `ADMIN_SECRET_KEY`.

| Method  | Path                       | Auth  | Description               |
|---------|----------------------------|-------|---------------------------|
| `GET`   | `/`                        | —     | Homepage (latest 4 posts) |
| `GET`   | `/posts/`                  | —     | List all posts            |
| `GET`   | `/posts/<slug>`            | —     | View a post               |
| `GET`   | `/posts/tag/<tag>`         | —     | Filter posts by tag       |
| `POST`  | `/posts/`                  | Admin | Create a post             |
| `POST`  | `/posts/<slug>/images`     | Admin | Upload an image to a post |
| `GET`   | `/posts/images/<filename>` | —     | Serve an uploaded image   |

### Create a post

```bash
curl -X POST http://localhost:5000/posts/ \
  -H "X-Admin-Secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "body": {
      "paragraphs": [
        "Hello, world.",
        "This is a JSON-structured post body."
      ],
      "links:": [
        {"text": "Flask", "url": "https://flask.palletsprojects.com/"},
        {"text": "SQLModel", "url": "https://sqlmodel.tiangolo.com/"}
      ]
    },
    "tags": ["intro"]
  }'
```

### Upload an image

```bash
curl -X POST http://localhost:5000/posts/my-first-post/images \
  -H "X-Admin-Secret: your-secret" \
  -F "file=@photo.jpg" \
  -F "caption=A photo" \
  -F "alt=Description of photo"
```

## Data Model

- **Post** — title (unique), body (JSONB), slug (auto-generated), tags, images
- **Tag** — name (unique); many-to-many with Post
- **Image** — filename, caption, alt; belongs to a Post

All models include a UUID primary key and `created_date`/`updated_date` timestamps set server-side.
