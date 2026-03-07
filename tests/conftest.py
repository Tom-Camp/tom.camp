import os

# Must be set before any app module is imported so pydantic-settings picks them up
# instead of (or in addition to) the .env file.
os.environ.setdefault("ADMIN_SECRET_KEY", "test-admin-secret")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("FLASK_SECRET_KEY", "test-flask-secret")

import pytest  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402
from sqlmodel.pool import StaticPool  # noqa: E402

import app.main as main_module  # noqa: E402
import app.routes.post_routes as routes_module  # noqa: E402
import app.utils.database as db_module  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.post import Post  # noqa: E402

ADMIN_KEY = "test-admin-secret"
ADMIN_HEADER = {"X-Admin-Secret": ADMIN_KEY}


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Patch the module-level engine references before creating tables or the app.
    db_module.engine = engine
    routes_module.engine = engine
    main_module.engine = engine

    # JSONB is PostgreSQL-only; swap to JSON so SQLite can create the table.
    from sqlalchemy import JSON

    Post.__table__.c.body.type = JSON()

    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def app(test_engine):
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(test_engine):
    with Session(test_engine) as session:
        yield session


@pytest.fixture(autouse=True)
def clean_db(test_engine):
    """Delete all rows before each test so tests are isolated."""
    with test_engine.connect() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
    yield
