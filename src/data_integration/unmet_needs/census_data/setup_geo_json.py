import geopandas as gpd
import sqlalchemy
from sqlalchemy import create_engine
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from geoalchemy2 import Geometry, WKTElement
from shapefiles import TOWN, CARTO, build_level_df, DEFAULT_LAT_LONG_PROJ

GEOMETRY_COL = 'geometry'


def convert_to_multi_poly(geom) -> MultiPolygon:
    """
    Converts all Polygon geography types to multi Polygons to account for any MultiPolygons already
    existing in the data. Polygons can convert to Multipolygons but not the other way around
    :param geom: Geometry object
    :return: MultiPolygon object
    """
    return MultiPolygon([geom]) if type(geom) == Polygon else geom


def create_wkt_element(geom, srid=DEFAULT_LAT_LONG_PROJ):
    """
    Converts a geometry element to a string that is readable by PostGIS
    :param geom: Geometry object
    :param srid: ID for a spatial reference system
    :return: SQL compatible string
    """
    return WKTElement(geom.wkt, srid=srid)


def write_to_sql(table_name: str, geo_df: gpd.GeoDataFrame, columns: list, engine: sqlalchemy.engine, srid: int=DEFAULT_LAT_LONG_PROJ):
    """
    Writes the specified columns in the geodataframe to a DB table, if the table already exists
    this overwrites it. The projection of the resulting geography is specified by the SRID. This assumes
    a PostGIS table
    :param table_name: Name of table to write to
    :param geo_df: Geodataframe
    :param columns: columns to use from the geodataframe in addition to the geometry column
    :param engine: Engine used to write to the database
    :param srid: Spatial reference system
    ## TODO
    # Check if CT code works better here
    :return: None, writes to table
    """
    # Convert to multi-polygon and stringify the geography column
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(convert_to_multi_poly)
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(create_wkt_element)

    print(f"Loading {table_name}")
    # Write to table specifying the geometry as a MULTIPOLYGON with the given projection
    geo_df[columns + [GEOMETRY_COL]].to_sql(table_name, engine, if_exists='replace', index=False,
                                            dtype={GEOMETRY_COL: Geometry("MULTIPOLYGON", srid=srid)})
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

    # Load town data to Superset keeping data that will allow for joins to other Census and unmet needs data
    town_geo_df = build_level_df(geo_level=TOWN, file_type=CARTO)
    town_cols = ['NAME', 'STATEFP', 'COUNTYFP', 'COUSUBFP']
    write_to_sql(table_name='ct_town_geo', geo_df=town_geo_df, engine=engine, columns=town_cols)


