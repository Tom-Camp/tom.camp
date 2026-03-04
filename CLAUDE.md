# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`tom.camp` is a Flask web application using SQLModel (SQLAlchemy + Pydantic) for ORM, PostgreSQL for the database, and `uv` for Python package management. It requires Python 3.14+.

## Commands

All commands use `uv run` — no manual venv activation needed.

```bash
# Run development server
uv run flask run

# Run tests
uv run pytest

# Run a single test file
uv run pytest path/to/test_file.py

# Run a single test
uv run pytest path/to/test_file.py::test_function_name

# Run with coverage
uv run pytest --cov

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --group dev
```

## Linting & Pre-commit

The stack: **black** (formatter), **isort** (import sorting, black profile), **flake8** (max line length 109), **mypy** (type checking), **bandit** (security, B101 skipped).

```bash
# Run all pre-commit hooks
uv run pre-commit run --all-files

# Run a specific hook
uv run pre-commit run black --all-files
```

Bandit skips `B101` (assert statements) and excludes test files.

## Docker

Development uses `docker-compose.yml` + `docker-compose.override.yml` (auto-merged by Docker Compose). The override adds a Postgres service (`tcdata`) and mounts source code as a volume.

```bash
# Start dev environment (Flask + Postgres)
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```

The dev Dockerfile runs `uvicorn` with `--reload`; the prod Dockerfile runs `flask run`.

## Architecture

### App entry point
`app/main.py` — creates the Flask app via `create_app()`, which calls `create_db_and_tables()` on startup to auto-create all SQLModel-registered tables.

### Configuration
`app/utils/config.py` — `Settings` (pydantic-settings) reads from `.env`. Required env vars: `ADMIN_SECRET_KEY`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SECRET_KEY`, `FLASK_SECRET_KEY`. The `database_url` property builds the PostgreSQL connection string.

### Database
`app/utils/database.py` — single SQLAlchemy engine, `get_session()` yields a `Session` for use in route handlers.

### Models
All models inherit from `ModelBase` (`app/models/base.py`), which provides:
- UUID primary key (auto-generated)
- `created_date` and `updated_date` with server-side `now()` defaults

Current models: `User` (`app/models/user.py`), `Post` (`app/models/post.py`).

**Important**: For a model to have its table created on startup, it must be imported somewhere before `create_db_and_tables()` is called — SQLModel discovers tables via import side-effects.
