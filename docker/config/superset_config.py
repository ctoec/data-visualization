import os
APP_ICON = '/static/assets/images/mounted_images/logo.png'
SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://superset_admin:{os.environ["POSTGRES_PASSWORD"]}@superset_db/superset'
MAPBOX_API_KEY=f'{os.environ["MAPBOX_KEY"]}'
