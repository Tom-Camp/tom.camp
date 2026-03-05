import mistune
from flask import Flask, render_template
from loguru import logger
from sqlmodel import Session

from app.routes.post_routes import posts_bp
from app.services.post_service import PostService
from app.utils.config import settings
from app.utils.database import create_db_and_tables, engine
from app.utils.logging_config import setup_logging


def create_app() -> Flask:
    setup_logging()
    app = Flask(__name__)
    logger.info("Starting {} (env={})", settings.APP_NAME, settings.FLASK_ENV)

    # Keep markdown output untrusted; templates should opt-in to |safe only when appropriate.
    markdown_renderer = mistune.create_markdown(escape=True)
    app.jinja_env.filters["markdown"] = lambda text: markdown_renderer(text or "")
    app.register_blueprint(posts_bp)

    with app.app_context():
        create_db_and_tables()

    @app.get("/")
    def index():
        with Session(engine) as session:
            service = PostService(session)
            posts = service.list_posts()
        return render_template("index.html", posts=posts)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=settings.FLASK_DEBUG)
