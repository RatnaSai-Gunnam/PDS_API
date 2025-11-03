# app/cache.py
from flask_caching import Cache

# Shared cache instance to import in routes and init in create_app()
cache = Cache()
