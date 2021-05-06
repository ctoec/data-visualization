import json
import pandas as pd
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapefiles import CARTO, build_level_df, SENATE, HOUSE, FINAL_SENATE_ID, FINAL_HOUSE_ID

LEGISLATOR_RENAME = {'name': 'legislator_name',
                     'current_party': 'legislator_party'}
GEOMETRY_COL = 'geometry'
DEFAULT_SCHEMA = 'uploaded_data'

# This site claims to update daily
CT_OPEN_DATA_CSV = 'https://data.openstates.org/people/current/ct.csv'

# Name of column corresponding the text code associated with the district number
CURRENT_DISTRICT = 'current_district'


def convert_to_poly(geom) -> Polygon:
    """
    Selects the largest Polygon for MultiPolygons since all CT towns are contiguous, this removes small islands
    :param geom: Geometry object
    :return: MultiPolygon object
    """
    return max(geom, key=lambda a: a.area) if type(geom) == MultiPolygon else geom


def get_level_table(geo_level, columns, file_type=CARTO):
    """
    Builds a dataframe with geojson and metadata and loads it directly to the database
    :param geo_level: level (TOWN, leg etc.)
    :param file_type:
    :param columns: Columns to keep from original census shapefile
    :return: pandas dataframe
    """

    # Load data to Superset keeping data that will allow for joins to other Census and unmet needs data
    level_geo_df = build_level_df(geo_level=geo_level, file_type=file_type)

    # If the dataset is a legislative district the name of the Legislator should be added
    if geo_level in [SENATE, HOUSE]:
        legis_df = pd.read_csv(CT_OPEN_DATA_CSV)

        # Reduce legislator df to relevant columns
        cur_chamber = 'lower' if geo_level == HOUSE else 'upper'
        legis_df = legis_df.loc[legis_df['current_chamber'] == cur_chamber]
        legis_df = legis_df.rename(columns=LEGISLATOR_RENAME)

        # Update district to facilitate joins
        legis_df[CURRENT_DISTRICT] = legis_df.loc[:,CURRENT_DISTRICT].astype(str).str.zfill(3)

        # join chamber with names to level df
        geo_leg_key = FINAL_HOUSE_ID if geo_level == HOUSE else FINAL_SENATE_ID
        level_geo_df = level_geo_df.merge(legis_df, how='left', left_on=geo_leg_key, right_on=CURRENT_DISTRICT)

    # Convert geometries to JSON strings that are readable by Mapbox (in Superset)
    level_geo_df[GEOMETRY_COL] = level_geo_df[GEOMETRY_COL].apply(convert_to_poly)
    json_geometries = [json.dumps({'geometry': town['geometry']}) for town in json.loads(level_geo_df[GEOMETRY_COL].to_json())['features']]
    level_geo_df[GEOMETRY_COL] = json_geometries
    return level_geo_df[columns + [GEOMETRY_COL]]
