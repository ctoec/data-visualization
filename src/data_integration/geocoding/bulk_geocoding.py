import requests
import pandas as pd
from io import StringIO
import geopandas as gpd
# from ..census_data.shapefiles import build_level_df, TOWN, TIGER, HOUSE, SENATE, DEFAULT_LAT_LONT_PROJ
DEFAULT_LAT_LONG_PROJ = 4269

CENSUS_GEOCODE_URL = 'https://geocoding.geo.census.gov/geocoder/locations/addressbatch'
LOCATION_IDENTIFIER = 'match_location'
MAX_SIZE = 10000
INPUT_COLUMNS = ['id', 'address', 'city', 'state', 'zip_code']

# Returns data in the form specified here: https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/census-geocoder.html
LOCATION_FIELDS = ['input_id', 'input_address', 'range_match_indicator','match_type','match_address',LOCATION_IDENTIFIER,'tiger_line_id','tiger_line_side_id']
# town_df = build_level_df()


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
    with open(filename, 'rb') as rf:
        files = {'addressFile': rf}
        r = requests.post(CENSUS_GEOCODE_URL, data=payload, files=files)
        returned_text = r.text
    output_df = pd.read_csv(StringIO(returned_text), names=LOCATION_FIELDS)

    # Get lat/lon lon
    output_df[['lat', 'lon']] = output_df[LOCATION_IDENTIFIER].str.split(',', expand=True)
    geo_output = gpd.GeoDataFrame(output_df, geometry=gpd.points_from_xy(output_df.lat, output_df.lon))
    geo_output = geo_output.set_crs(DEFAULT_LAT_LONG_PROJ)
    return geo_output

def join_geo_df(child_df, geo_df, geo_name_col, id_col, geo_name):

    geo_cols = geo_df.columns
    joined_df = gpd.sjoin(geo_df, child_df, how='right', op='intersects')
    return_lookup = joined_df[[id_col, geo_name_col]]





if __name__ == '__main__':
    filename = 'upload_files/test_upload.csv'
    gdf = get_bulk_data_upload_from_census()
    town_df = build_level_df(geo_level=TOWN, file_type=TIGER)
    gpd.sjoin(town_df, gdf, how='right', op='intersects')
    pass
