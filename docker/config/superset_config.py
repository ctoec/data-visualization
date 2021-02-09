import os
APP_ICON = '/static/assets/images/mounted_images/logo.png'
APP_ICON_WIDTH = 35
SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://superset_admin:{os.environ["POSTGRES_PASSWORD"]}@superset_db/superset'
