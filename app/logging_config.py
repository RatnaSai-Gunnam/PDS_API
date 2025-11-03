
import os, logging
from logging.config import dictConfig

def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    fmt = os.getenv("LOG_FORMAT", "json").lower()  # "json" or "plain"
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "class": "logging.Formatter",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                "format": (
                    '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
                    '"msg":"%(message)s","request_id":"%(request_id)s","path":"%(path)s",'
                    '"method":"%(method)s","status":"%(status)s","extra":%(extra)s}'
                ),
            },
            "plain": {
                "class": "logging.Formatter",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "json" if fmt == "json" else "plain",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": level, "handlers": ["stdout"]},
    })
    logging.getLogger("werkzeug").setLevel(os.getenv("LOG_WERKZEUG", "WARNING"))
    logging.getLogger("urllib3").setLevel("WARNING")
