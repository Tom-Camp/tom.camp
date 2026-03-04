import logging
import sys
from types import FrameType

from loguru import logger

from app.utils.config import settings


class _InterceptHandler(logging.Handler):
    """Redirect stdlib logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    log_level = "DEBUG" if settings.FLASK_DEBUG else "INFO"

    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Intercept stdlib logging used by Flask, Werkzeug, SQLAlchemy, etc.
    intercept = _InterceptHandler()
    logging.basicConfig(handlers=[intercept], level=0, force=True)
    for name in ("werkzeug", "sqlalchemy.engine", "sqlalchemy.pool"):
        logging.getLogger(name).handlers = [intercept]
        logging.getLogger(name).propagate = False
