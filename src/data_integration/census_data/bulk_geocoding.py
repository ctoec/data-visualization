import os
import requests
import pandas as pd
from math import ceil
from io import StringIO
import geopandas as gpd
from shapefiles import build_level_df, TOWN, TIGER, HOUSE, SENATE, BLOCK, DEFAULT_LAT_LONG_PROJ, FINAL_GEO_ID

FILE_DIR = os.path.dirname(os.path.realpath(__file__))

# Total number of rows accepted by the Census API
MAX_SIZE = 10000
CENSUS_GEOCODE_URL = 'https://geocoding.geo.census.gov/geocoder/locations/addressbatch'


UPLOAD_FILE_DIRECTORY = FILE_DIR + '/upload_files'

# Column from shapefiles with unique identifier
GEOID = 'geoid'
NAME_SHAPEFILE = 'name'
TOWN_COL = 'town'

# Census API
# Returns data in the form specified here: https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/census-geocoder.html
CHILD_ID = 'child_id'
LOCATION_IDENTIFIER = 'match_location'
MATCH_IDENTIFIER = 'range_match_indicator'

# Columns to upload to Census Bulk geocoder
ADDRESS_COL = 'address'
CITY_COL = 'city'
STATE_COL = 'state'
ZIP_CODE_COL = 'zip_code'
INPUT_COLUMNS = [CHILD_ID, ADDRESS_COL, CITY_COL, STATE_COL, ZIP_CODE_COL]

LOCATION_FIELDS = [CHILD_ID, 'input_address', MATCH_IDENTIFIER , 'match_type', 'match_address', LOCATION_IDENTIFIER, 'tiger_line_id', 'tiger_line_side_id']


def get_bulk_data_upload_from_census(filename: str) -> pd.DataFrame:
    """
    Uploads data in the CSV at filename and calls the Census API with
    :param filename: name of
    :return:
    """

    # Validate input file
    input_df = pd.read_csv(filename, names=INPUT_COLUMNS)
    n_rows, n_columns = input_df.shape
    if n_columns != len(INPUT_COLUMNS) or n_rows > MAX_SIZE:
        raise Exception(f"Improperly formatted input file {filename}")

    payload = {'benchmark': 'Public_AR_Current', 'vintage': 'Current_Current'}
    print(f"Uploading {filename}")
    with open(filename, 'rb') as rf:
        files = {'addressFile': rf}
        r = requests.post(CENSUS_GEOCODE_URL, data=payload, files=files)
        returned_text = r.text
    output_df = pd.read_csv(StringIO(returned_text), names=LOCATION_FIELDS)
    print(f"{filename} geocoded")

    # Delete file
    os.remove(filename)

    # Get lat/lon lon
    output_df[['lat', 'lon']] = output_df[LOCATION_IDENTIFIER].str.split(',', expand=True)
    geo_output = gpd.GeoDataFrame(output_df, geometry=gpd.points_from_xy(output_df.lat, output_df.lon))
    geo_output = geo_output.set_crs(DEFAULT_LAT_LONG_PROJ)
    return geo_output


def join_geo_df(student_df, geo_df, geo_name_col, geo_name):

    joined_df = gpd.sjoin(geo_df[[geo_name_col, 'geometry']], student_df, how='right', op='intersects')
    joined_df.rename(columns={geo_name_col: geo_name}, inplace=True)
    joined_df.drop(['index_left'], axis=1, inplace=True)
    return joined_df


def join_geos(student_df, geo_level_list, geo_type=TIGER):

    geo_level_id_list = []
    for geo_level in geo_level_list:
        geo_df = build_level_df(geo_level=geo_level, file_type=geo_type)

        # Add the geoid from the census shapefile to student data for joins to shapefiles in the database
        new_geo_level_name = geo_level.replace(' ','_') + f'_{FINAL_GEO_ID.lower()}'
        geo_level_id_list.append(new_geo_level_name)
        student_df = join_geo_df(student_df=student_df, geo_df=geo_df, geo_name_col=FINAL_GEO_ID, geo_name=new_geo_level_name)

        # For towns attempt to join on town name as well
        if geo_level == TOWN:
            town_df = geo_df[geo_df[NAME_SHAPEFILE] != 'County subdivisions not defined'][[NAME_SHAPEFILE,FINAL_GEO_ID]]
            # Create lookup for exact match town names
            town_df[NAME_SHAPEFILE] = town_df[NAME_SHAPEFILE].str.lower().str.strip()
            town_lookup = town_df.set_index(NAME_SHAPEFILE).to_dict(orient='index')

            def get_town_name_from_lookup(row):
                """
                Get town name if the geo code didn't identify one
                :param row:
                :return:
                """
                current_town_name = row[new_geo_level_name]

                # All null values will be nan
                if row[MATCH_IDENTIFIER] != 'No_Match':
                    return current_town_name
                else:
                    input_town = row[TOWN_COL].lower().strip() if row[TOWN_COL] else None
                    found_town_id = town_lookup.get(input_town, {FINAL_GEO_ID: None})[FINAL_GEO_ID]
                    return found_town_id

            student_df[new_geo_level_name] = student_df.apply(lambda row: get_town_name_from_lookup(row), axis=1)

    return student_df, geo_level_id_list


def split_and_write_files(df, max_size: int=MAX_SIZE) -> [str]:
    """
    Saves the passed dataframe as a set of files, each no larger than max_size
    :param df:
    :param max_size:
    :return: list of filenames for saved files
    """
    num_rows = df.shape[0]
    num_files = ceil(num_rows / max_size)
    filename_list = []
    for i in range(num_files):
        item_filename = f"{UPLOAD_FILE_DIRECTORY}/upload_file_{i}.csv"
        df[i*MAX_SIZE:(i+1)*MAX_SIZE].to_csv(item_filename, index=False, header=False)
        filename_list.append(item_filename)

    return filename_list


def run_geo_code(db_conn) -> pd.DataFrame:
    """
    Does a full run of all the active children in the database and ties them with towns, legislative districts and census blocks
    :param db_conn: SQL alchemy connection to ECE database
    :return: dataframe of child IDs and corresponding geographic entities
    """
    sql_string = f"""select c.id as {CHILD_ID}, 
                                          streetAddress as {ADDRESS_COL}, 
                                          town as {TOWN_COL}, 
                                          state as {STATE_COL}, 
                                          zipCode as {ZIP_CODE_COL}
                                from child c
                                LEFT OUTER join family f on c.familyId = f.id
                                where c.deletedDate is null and f.deletedDate is null
                                """

    df = pd.read_sql(sql=sql_string, con=db_conn)

    # Call bulk census API geocoder with results from SQL query, temporary files are written and removed
    file_list = split_and_write_files(df)
    print("Uploaded data to census")
    df_list = [get_bulk_data_upload_from_census(filename) for filename in file_list]
    combined_df = pd.concat(df_list)

    # Add town name in as a default for failed geocodes
    combined_df_w_town = combined_df.merge(df[[CHILD_ID,TOWN_COL]], how='inner', left_on=CHILD_ID, right_on=CHILD_ID)

    # Add matches for all geographies to existing student dataframe
    geo_list = [TOWN, SENATE, HOUSE, BLOCK]
    final_student_df, geo_id_list = join_geos(student_df=combined_df_w_town, geo_level_list=geo_list)

    # Only return child ID and the corresponding joined geographic areas to preserve PII
    return final_student_df[geo_id_list + [CHILD_ID]]


