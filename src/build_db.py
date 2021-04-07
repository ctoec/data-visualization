import os
from sqlalchemy import text
from data_integration.census_data.field_lookup import create_census_variable_output
from data_integration.unmet_needs.unmet_needs import get_supply_demand_with_cae
from data_integration.ece_data.pull_ece_data import backfill_ece, get_space_df
from data_integration.july_2020.build_tables import build_site_df, build_student_df
from data_integration.july_2020.merge_leg import merge_legislative_data
from data_integration.census_data.setup_geo_json import load_level_table
from data_integration.census_data.shapefiles import TOWN, HOUSE, SENATE
from data_integration.connections.databases import get_db_connection
from demand_estimation.estimate_eligible_population import get_town_eligible_df
from demand_estimation.calculate_town_demand import create_final_town_demand
from demand_estimation.demand_estimate_script import build_need_demand_df
from data_integration.historical_care_4_kids.data_aggregation import get_historical_c4k

DB_DATA_FOLDER = 'final_data'
CUR_FOLDER = os.path.dirname(os.path.realpath(__file__))
NEED_SINGLE_VARIABLE = f'{CUR_FOLDER}/demand_estimation/need_single_field_lookups.txt'
NEED_MULTI_VARIABLE = f'{CUR_FOLDER}/demand_estimation/need_combination_field_lookups.txt'
TABLE_FOLDER = f'{CUR_FOLDER}/analytics_tables/'


def get_demand_estimates(filename):

    eligible_df = get_town_eligible_df()
    town_df = create_census_variable_output(single_field_mapping_file=NEED_SINGLE_VARIABLE, combination_field_mapping_file=NEED_MULTI_VARIABLE)
    demand_df = build_need_demand_df(town=town_df, filename=None)
    create_final_town_demand(parent_metric_df=demand_df, smi_df=eligible_df, write_filename=filename)


def get_ece_student_data(filename):
    ece_conn = get_db_connection(section='ECE Reporter DB')
    child_df = backfill_ece(ece_conn)
    child_df.to_csv(filename, index=False)


def get_ece_site_date(filename):
    ece_conn = get_db_connection(section='ECE Reporter DB')
    site_df = get_space_df(ece_conn)
    site_df.to_csv(filename, index=False)


def get_july_2020_sites(filename):

    site_df = build_site_df()
    merge_legislative_data(site_df, filename)


def get_july_2020_students(filename):
    student_df = build_student_df()
    merge_legislative_data(student_df, filename)


def load_shapefiles_to_db(db_engine):
    """
    Loads town, house and senate shapefiles to the dashboard database
    :param db_engine: SQLAlchemy engine
    :return: None, adds data to DB
    """

    town_cols = ['NAME', 'STATEFP', 'COUNTYFP', 'COUSUBFP', 'lat', 'long']
    load_level_table(geo_level=TOWN, table_name='ct_town_geo', columns=town_cols, engine=db_engine)

    house_cols = ['STATEFP', 'SLDLST', 'lat', 'long']
    load_level_table(geo_level=HOUSE, table_name='ct_house_geo', columns=house_cols, engine=db_engine)

    senate_cols = ['STATEFP', 'SLDUST', 'lat', 'long']
    load_level_table(geo_level=SENATE, table_name='ct_house_geo', columns=senate_cols, engine=db_engine)


def init_database(init_postgis: bool=False):
    """
    Adds initial tables to database and loads postgis
    :param init_postgis: Boolean whether to install postgis in database
    :return:
    """
    db_engine = get_db_connection(section='SUPERSET DB')
    if init_postgis:
        db_engine.execute('CREATE EXTENSION postgis')
    load_shapefiles_to_db(db_engine)
    for filename in os.listdir(TABLE_FOLDER):
        print(f"Creating {filename}")
        db_engine.execute(text(open(TABLE_FOLDER + filename).read()))






if __name__ == '__main__':
    init_database()
    # Write CAE CSV
    get_supply_demand_with_cae(filename=f'{DB_DATA_FOLDER}/overall_supply_demand_with_cae.csv')

    # Write July data CSV
    get_july_2020_sites(filename=f"{DB_DATA_FOLDER}/july_2020_sites.csv")
    get_july_2020_students(filename=f"{DB_DATA_FOLDER}/pii/july_2020.csv")

    # Get ECE Data
    get_ece_student_data(filename=f"{DB_DATA_FOLDER}/pii/ece_student_data.csv")
    get_ece_site_date(filename=f"{DB_DATA_FOLDER}/ece_space_data.csv")

    ## TODO
    # Add ECE table creation into script as well as loading CSV directly to DB

    # Build demand estimates
    get_demand_estimates(filename=f"{DB_DATA_FOLDER}/demand_estimation.csv")

    # Get C4K data
    get_historical_c4k(final_filename=f"{DB_DATA_FOLDER}/all_c4k_data.csv")
