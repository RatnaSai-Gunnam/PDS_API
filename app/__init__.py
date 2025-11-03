import os
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flasgger import Swagger
from .config import Config
from .db.models import Base
from .api.routes import bp as api_bp
from .cache import cache
from .logging_config import setup_logging
from .middleware import request_id_middleware
from .log_context import RequestContextFilter

# Optional SQL echo (debug only)
echo = os.getenv("SQLALCHEMY_ECHO", "false").lower() in {"1", "true", "yes"}
engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True, echo=echo)
SessionLocal = scoped_session(sessionmaker(bind=engine))

def create_app():
    # 1) logging should be initialized first
    setup_logging()

    app = Flask(__name__)
    CORS(app)
    app.session_factory = SessionLocal

    # 2) attach request context filter to app logger
    for h in app.logger.handlers:
        h.addFilter(RequestContextFilter())

    # 3) correlation IDs
    request_id_middleware(app)

    # 4) DB tables
    Base.metadata.create_all(bind=engine)

    # 5) Swagger UI (optional)
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Political Data Service API",
            "description": "REST API for US legislators with weather integration.",
            "version": "1.0.0",
        },
        "basePath": "/api",
    }
    Swagger(app, template=swagger_template)

    # 6) Initialize cache (SimpleCache by default; Redis if configured via env)
    cache.init_app(app, config={
        "CACHE_TYPE": getattr(Config, "CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": getattr(Config, "CACHE_DEFAULT_TIMEOUT", 120),
        **(
            {"CACHE_REDIS_URL": getattr(Config, "CACHE_REDIS_URL")}
            if getattr(Config, "CACHE_TYPE", "SimpleCache") == "RedisCache"
            and getattr(Config, "CACHE_REDIS_URL", None)
            else {}
        )
    })

    # 7) Routes
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()

    return app
