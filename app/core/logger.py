import logging
import os
from app.core.config import settings


def init_logging(app):
    if not settings.LOG_ENABLED:
        return

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.ERROR)

    os.makedirs(os.path.dirname(settings.LOG_PATH), exist_ok=True)

    handler = logging.FileHandler(settings.LOG_PATH)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(module)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    app.logger.setLevel(level)
    app.logger.addHandler(handler)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(level)
