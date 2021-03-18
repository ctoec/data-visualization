from data_integration.ece_data.pull_ece_data import get_mysql_connection, backfill_ece
from data_integration.july_2020.build_tables import build_site_df, build_student_df
from data_integration.july_2020.merge_leg import merge_legislative_data
from data_integration.census_data.setup_geo_json import load_level_table
from data_integration.census_data.shapefiles import TOWN, HOUSE, SENATE
from sqlalchemy import create_engine


def get_ece_data(filename):
    ece_conn = get_mysql_connection(section='ECE Reporter DB')
    child_df = backfill_ece(ece_conn)
    child_df.to_csv(filename, index=False)


def get_july_2020_sites(filename):

    site_df = build_site_df()
    site_legislature_df = merge_legislative_data(site_df)
    site_legislature_df.to_csv(filename, index=False)


def get_july_2020_students(filename):
    student_df = build_student_df()
    student_legislature_df = merge_legislative_data(student_df)
    student_legislature_df.to_csv(filename, index=False)


def load_shapefiles_to_db(db_engine):

    town_cols = ['NAME', 'STATEFP', 'COUNTYFP', 'COUSUBFP', 'lat', 'long']
    load_level_table(geo_level=TOWN, table_name='ct_town_geo', columns=town_cols, engine=db_engine)

    house_cols = ['STATEFP', 'SLDLST', 'lat', 'long']
    load_level_table(geo_level=HOUSE, table_name='ct_house_geo', columns=house_cols, engine=db_engine)

    senate_cols = ['STATEFP', 'SLDUST', 'lat', 'long']
    load_level_table(geo_level=SENATE, table_name='ct_house_geo', columns=senate_cols, engine=db_engine)


def get_engine():
    # Build postgres engine
    ## TODO
    # Replace with calls from AWS once there is a production instance and creds (for Superset creds)
    password = ''
    host = ''
    user = ''
    db_name = ''
    engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:5432/{db_name}')
    engine.execute('CREATE EXTENSION postgis')


if __name__ == '__main__':
    pass