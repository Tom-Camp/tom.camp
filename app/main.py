from flask import Flask, current_app, render_template, request
from loguru import logger
from sqlalchemy import Engine
from sqlmodel import Session
from werkzeug.exceptions import HTTPException

from app.routes.post_routes import posts_bp
from app.services.post_service import PostService
from app.utils.config import settings
from app.utils.database import create_db_and_tables, make_engine
from app.utils.logging_config import setup_logging


def create_app(engine: Engine | None = None) -> Flask:
    setup_logging()
    app = Flask(__name__)
    app.secret_key = settings.FLASK_SECRET_KEY
    logger.info("Starting {} (env={})", settings.APP_NAME, settings.FLASK_ENV)

    if engine is None:
        engine = make_engine()
    app.config["ENGINE"] = engine

    app.register_blueprint(posts_bp)

    with app.app_context():
        create_db_and_tables(engine)

    @app.get("/")
    def index():
        with Session(current_app.config["ENGINE"]) as session:
            service = PostService(session)
            posts = service.list_posts(limit=4, only_published=True)
        return render_template("index.html", posts=posts)

    @app.errorhandler(HTTPException)
    def handle_http_error(e: HTTPException):
        if (
            request.accept_mimetypes.best_match(["application/json", "text/html"])
            == "application/json"
        ):
            return {"error": e.description}, e.code
        return render_template("error.html", code=e.code, message=e.description), e.code

    @app.context_processor
    def inject_year():
        from datetime import datetime

        return {"current_year": datetime.now().year}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=settings.FLASK_DEBUG)
