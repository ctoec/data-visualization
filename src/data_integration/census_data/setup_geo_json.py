import pandas as pd
import geopandas as gpd
import sqlalchemy
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from geoalchemy2 import Geometry, WKTElement
from shapefiles import CARTO, build_level_df, DEFAULT_LAT_LONG_PROJ, SENATE, HOUSE, FINAL_SENATE_ID, FINAL_HOUSE_ID

LEGISLATOR_RENAME = {'name': 'legislator_name',
                     'current_party': 'legislator_party'}
GEOMETRY_COL = 'geometry'
DEFAULT_SCHEMA = 'uploaded_data'
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


def create_wkt_element(geom, srid=DEFAULT_LAT_LONG_PROJ):
    """
    Converts a geometry element to a string that is readable by PostGIS
    :param geom: Geometry object
    :param srid: ID for a spatial reference system
    :return: SQL compatible string
    """
    return WKTElement(geom.wkt, srid=srid)


def write_to_sql(table_name: str, geo_df: gpd.GeoDataFrame, columns: list,
                 engine: sqlalchemy.engine, srid: int = DEFAULT_LAT_LONG_PROJ, schema: str = DEFAULT_SCHEMA):
    """
    Writes the specified columns in the geodataframe to a DB table, if the table already exists
    this overwrites it. The projection of the resulting geography is specified by the SRID. This assumes
    a PostGIS table
    :param table_name: Name of table to write to
    :param geo_df: Geodataframe
    :param columns: columns to use from the geodataframe in addition to the geometry column
    :param engine: Engine used to write to the database
    :param srid: Spatial reference system     ## TODO
    # Check if CT spatial code works better here
    :param schema: DB Schema where table will be written
    :return: None, writes to table
    """
    # Convert to multi-polygon and stringify the geography column
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(convert_to_poly)
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(create_wkt_element)

    print(f"Loading {table_name}")
    # Write to table specifying the geometry as a POLYGON with the given projection
    geo_df[columns + [GEOMETRY_COL]].to_sql(table_name, engine, schema='uploaded_data', if_exists='replace', index=False,
                                            dtype={GEOMETRY_COL: Geometry("POLYGON", srid=srid)})

    print(f"Table {table_name} loaded")


def load_level_table(geo_level, table_name, columns, engine, file_type=CARTO):
    """
    Builds a dataframe with geojson and metadata and loads it directly to the database
    :param geo_level: level (TOWN, leg etc.)
    :param table_name: Name to give the table in the DB
    :param columns: Columns to keep from original census shapefile
    :param engine: DB engine
    :param file_type:
    :return: None, loads table to db
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

    write_to_sql(table_name=table_name, geo_df=level_geo_df, engine=engine, columns=columns)
