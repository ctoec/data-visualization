import os
from sqlalchemy import text
from data_integration.census_data.field_lookup import create_census_variable_output
from data_integration.unmet_needs.unmet_needs import get_supply_demand_with_cae
from data_integration.ece_data.pull_ece_data import backfill_ece, get_space_df
from data_integration.july_2020.build_tables import build_site_df, build_student_df
from data_integration.july_2020.merge_leg import merge_legislative_data
from data_integration.census_data.setup_geo_json import get_level_table
from data_integration.census_data.shapefiles import TOWN, HOUSE, SENATE, BLOCK, TIGER, \
    FINAL_NAME,FINAL_GEO_ID, FINAL_TOWN_ID, FINAL_COUNTY_ID, FINAL_STATE_ID, FINAL_HOUSE_ID,\
    FINAL_SENATE_ID
from data_integration.connections.databases import get_db_connection
from data_integration.census_data.bulk_geocoding import run_geo_code
from demand_estimation.estimate_eligible_population import get_town_eligible_df
from demand_estimation.calculate_town_demand import create_final_town_demand
from demand_estimation.demand_estimate_script import build_need_demand_df
from data_integration.historical_care_4_kids.data_aggregation import get_historical_c4k
from record_deduplication.dedupe import get_dedupe_mapping_from_db

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


def get_deduplication(filename):
    ece_conn = get_db_connection(section='ECE Reporter DB')
    dedupe_df = get_dedupe_mapping_from_db(db_conn=ece_conn)
    dedupe_df.to_csv(filename, index=False)


def get_ece_student_data(filename):
    ece_conn = get_db_connection(section='ECE Reporter DB')
    child_df = backfill_ece(ece_conn)
    child_df.to_csv(filename, index=False)

def get_ece_geocode(filename):
    ece_conn = get_db_connection(section='ECE Reporter DB')
    geocode_df = run_geo_code(ece_conn)
    geocode_df.to_csv(filename, index=False)

def get_ece_site_data(filename):
    ece_conn = get_db_connection(section='ECE Reporter DB')
    site_df = get_space_df(ece_conn)
    site_df.to_csv(filename, index=False)


def get_july_2020_sites(filename):

    site_df = build_site_df()
    merge_legislative_data(site_df, filename)


def get_july_2020_students(filename):
    student_df = build_student_df()
    merge_legislative_data(student_df, filename)


def create_shapefile_csvs():
    """
    Loads town, house, block and senate shapefiles to the dashboard database
    :return: None, adds data to DB
    """
    town_cols = [FINAL_NAME, FINAL_STATE_ID, FINAL_COUNTY_ID, FINAL_TOWN_ID, FINAL_GEO_ID, 'lat', 'long']
    town_df = get_level_table(geo_level=TOWN, columns=town_cols)
    town_df.to_csv(f"{DB_DATA_FOLDER}/ct_town_geo.csv", index=False)

    house_cols = [FINAL_STATE_ID, FINAL_HOUSE_ID, FINAL_GEO_ID, 'legislator_name', 'legislator_party','lat', 'long']
    house_df = get_level_table(geo_level=HOUSE, columns=house_cols)
    house_df.to_csv(f"{DB_DATA_FOLDER}/ct_house_geo.csv", index=False)

    senate_cols = [FINAL_STATE_ID, FINAL_SENATE_ID, FINAL_GEO_ID, 'legislator_name', 'legislator_party', 'lat', 'long']
    senate_df = get_level_table(geo_level=SENATE, columns=senate_cols)
    senate_df.to_csv(f"{DB_DATA_FOLDER}/ct_senate_geo.csv", index=False)

def init_database():
    """
    Adds initial tables to database
    :return:
    """
    db_engine = get_db_connection(section='SUPERSET DB')

    # Load all tables in analytics table folder
    for filename in os.listdir(TABLE_FOLDER):
        print(f"Creating {filename}")
        db_engine.execute(text(open(TABLE_FOLDER + filename).read()))


if __name__ == '__main__':

    # Write CAE CSV
    print("Pulling Unmet needs report")
    get_supply_demand_with_cae(filename=f'{DB_DATA_FOLDER}/overall_supply_demand_with_cae.csv')

    # Write July data CSV
    print("Pulling July 2020 data")
    get_july_2020_sites(filename=f"{DB_DATA_FOLDER}/july_2020_sites.csv")
    get_july_2020_students(filename=f"{DB_DATA_FOLDER}/pii/july_2020.csv")

    # Get ECE Data
    print("Pulling ECE student data")
    get_ece_student_data(filename=f"{DB_DATA_FOLDER}/pii/ece_student_data.csv")
    print("Pulling ECE site data")
    get_ece_site_data(filename=f"{DB_DATA_FOLDER}/ece_space_data.csv")
    print("Geocoding ECE data")
    get_ece_geocode(filename=f"{DB_DATA_FOLDER}/pii/ece_student_data_geocode.csv")
    print("Deduplicating data")
    get_deduplication(filename=f'{DB_DATA_FOLDER}/pii/ece_deduplication.csv')

    ## TODO
    # Add ECE table creation for students/geos into script as well as loading CSV directly to DB

    # Build demand estimates
    print("Getting demand estimation")
    get_demand_estimates(filename=f"{DB_DATA_FOLDER}/demand_estimation.csv")

    # Get C4K data
    print("Getting historical C4K data")
    get_historical_c4k(final_filename=f"{DB_DATA_FOLDER}/all_c4k_data.csv")

    # Create shapefile CSVs
    create_shapefile_csvs()

