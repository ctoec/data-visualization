import geopandas as gpd
import sqlalchemy
from sqlalchemy import create_engine
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from geoalchemy2 import Geometry, WKTElement
from shapefiles import TOWN, CARTO, build_level_df, DEFAULT_LAT_LONG_PROJ, HOUSE, SENATE

GEOMETRY_COL = 'geometry'
DEFAULT_SCHEMA = 'uploaded_data'


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
                 engine: sqlalchemy.engine, srid: int=DEFAULT_LAT_LONG_PROJ, schema: str=DEFAULT_SCHEMA):
    """
    Writes the specified columns in the geodataframe to a DB table, if the table already exists
    this overwrites it. The projection of the resulting geography is specified by the SRID. This assumes
    a PostGIS table
    :param table_name: Name of table to write to
    :param geo_df: Geodataframe
    :param columns: columns to use from the geodataframe in addition to the geometry column
    :param engine: Engine used to write to the database
    :param srid: Spatial reference system
    :param schema: DB Schema where table will be written
    ## TODO
    # Check if CT spatial code works better here
    :return: None, writes to table
    """
    # Convert to multi-polygon and stringify the geography column
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(convert_to_poly)
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(create_wkt_element)

    print(f"Loading {table_name}")
    # Write to table specifying the geometry as a MULTIPOLYGON with the given projection
    geo_df[columns + [GEOMETRY_COL]].to_sql(table_name, engine, schema='uploaded_data', if_exists='replace', index=False,
                                            dtype={GEOMETRY_COL: Geometry("POLYGON", srid=srid)})
    print(f"Table {table_name} loaded")


if __name__ == '__main__':

    # Build postgres engine
    ## TODO
    # Replace with calls from AWS once there is a production instance and creds
    password = ''
    host = ''
    user = ''
    db_name = ''
    engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:5432/{db_name}')

    # Create postgis extension, this will be a no-op if it already exists
    # engine.execute('CREATE EXTENSION postgis')

    # Load town data to Superset keeping data that will allow for joins to other Census and unmet needs data
    town_geo_df = build_level_df(geo_level=TOWN, file_type=CARTO)
    town_cols = ['NAME', 'STATEFP', 'COUNTYFP', 'COUSUBFP', 'lat', 'long']
    write_to_sql(table_name='ct_town_geo', geo_df=town_geo_df, engine=engine, columns=town_cols)

    # Load house shapefiles
    house_geo_df = build_level_df(geo_level=HOUSE, file_type=CARTO)
    house_cols = ['STATEFP', 'SLDLST', 'lat', 'long']
    write_to_sql(table_name='ct_house_geo', geo_df=house_geo_df, engine=engine, columns=house_cols)

    # Load senate shapefiles
    senate_geo_df = build_level_df(geo_level=SENATE, file_type=CARTO)
    senate_cols = ['STATEFP', 'SLDUST', 'lat', 'long']
    write_to_sql(table_name='ct_senate_geo', geo_df=senate_geo_df, engine=engine, columns=senate_cols)



