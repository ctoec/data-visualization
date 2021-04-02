import os
APP_ICON = '/static/assets/images/mounted_images/logo.png'
APP_ICON_WIDTH = 35
SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://superset_admin:{os.environ["POSTGRES_PASSWORD"]}@superset_db/superset'
MAPBOX_API_KEY=f'{os.environ["MAPBOX_KEY"]}'
ENABLE_JAVASCRIPT_CONTROLS = True

# Default cache for Superset objects
CACHE_CONFIG = {"CACHE_TYPE": "filesystem",
                "CACHE_DIR": "/cache"}

# Cache for datasource metadata and query results
DATA_CACHE_CONFIG = {"CACHE_TYPE": "filesystem",
                     "CACHE_DIR": "/cache"}
