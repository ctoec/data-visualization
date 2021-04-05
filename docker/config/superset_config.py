import os
from celery.schedules import crontab
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

CELERYBEAT_SCHEDULE = {
        "email_reports.schedule_hourly": {
            "task": "email_reports.schedule_hourly",
            "schedule": crontab(minute=1, hour="*"),
        },
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=0, hour=0),
        },
        # From https://superset.apache.org/docs/installation/cache
        'cache-warmup-daily': {
                'task': 'cache-warmup',
                'schedule': crontab(minute=0, hour=6),  # Refresh daily, cache will last for 24 hours on site
                'kwargs': {
                    'strategy_name': 'top_n_dashboards',
                    'top_n': 10,
                    'since': '1 month ago',
                    }
        }
    }
