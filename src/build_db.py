import os
from data_integration.census_data.field_lookup import create_census_variable_output
from data_integration.unmet_needs.unmet_needs import get_supply_demand_with_cae
from data_integration.ece_data.pull_ece_data import backfill_ece
from data_integration.july_2020.build_tables import build_site_df, build_student_df
from data_integration.july_2020.merge_leg import merge_legislative_data
from data_integration.census_data.setup_geo_json import load_level_table
from data_integration.census_data.shapefiles import TOWN, HOUSE, SENATE
from data_integration.connections.databases import get_db_connection
from demand_estimation.estimate_eligible_population import get_town_eligible_df
from demand_estimation.calculate_town_demand import create_final_town_demand
from demand_estimation.demand_estimate_script import build_need_demand_df

DB_DATA_FOLDER = 'final_data'
CUR_FOLDER = os.path.dirname(os.path.realpath(__file__))
NEED_SINGLE_VARIABLE = f'{CUR_FOLDER}/demand_estimation/need_single_field_lookups.txt'
NEED_MULTI_VARIABLE = f'{CUR_FOLDER}/demand_estimation/need_combination_field_lookups.txt'


def get_demand_estimates(filename):

    eligible_df = get_town_eligible_df()
    town_df = create_census_variable_output(single_field_mapping_file=NEED_SINGLE_VARIABLE, combination_field_mapping_file=NEED_MULTI_VARIABLE)
    demand_df = build_need_demand_df(town=town_df, filename=None)
    create_final_town_demand(parent_metric_df=demand_df, smi_df=eligible_df, write_filename=filename)


def get_ece_data(filename):
    ece_conn = get_db_connection(section='ECE Reporter DB')
    child_df = backfill_ece(ece_conn)
    child_df.to_csv(filename, index=False)


def get_july_2020_sites(filename):

    site_df = build_site_df()
    merge_legislative_data(site_df, filename)


def get_july_2020_students(filename):
    student_df = build_student_df()
    merge_legislative_data(student_df, filename)


def load_shapefiles_to_db(init_postgis=False):
    """
    Loads town, house and senate shapefiles to the
    :param init_postgis: Boolean whether to install postgis in database
    :return: None, adds data to DB
    """
    db_engine = get_db_connection(section='SUPERSET DB')
    if init_postgis:
        db_engine.execute('CREATE EXTENSION postgis')
    town_cols = ['NAME', 'STATEFP', 'COUNTYFP', 'COUSUBFP', 'lat', 'long']
    load_level_table(geo_level=TOWN, table_name='ct_town_geo', columns=town_cols, engine=db_engine)

    house_cols = ['STATEFP', 'SLDLST', 'lat', 'long']
    load_level_table(geo_level=HOUSE, table_name='ct_house_geo', columns=house_cols, engine=db_engine)

    senate_cols = ['STATEFP', 'SLDUST', 'lat', 'long']
    load_level_table(geo_level=SENATE, table_name='ct_house_geo', columns=senate_cols, engine=db_engine)


if __name__ == '__main__':

    # Write CAE CSV
    get_supply_demand_with_cae(filename=f'{DB_DATA_FOLDER}/overall_supply_demand_with_cae.csv')

    # Write July data CSV
    get_july_2020_sites(filename=f"{DB_DATA_FOLDER}/july_2020_sites.csv")
    get_july_2020_students(filename=f"{DB_DATA_FOLDER}/pii/july_2020.csv")

    # Get ECE Data
    get_ece_data(filename=f"{DB_DATA_FOLDER}/pii/ece_student_data.csv")

    # Build demand estimates
    get_demand_estimates(filename=f"{DB_DATA_FOLDER}/demand_estimation.csv")