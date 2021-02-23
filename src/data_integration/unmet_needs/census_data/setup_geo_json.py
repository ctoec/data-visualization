import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from geoalchemy2 import Geometry, WKTElement
from shapefiles import TOWN, CARTO, build_level_df

# Generic Lat Long spatial reference system
SRID = 4269
GEOMETRY_COL = 'geometry'


def convert_to_multi_poly(geom) -> MultiPolygon:
    """
    Converts all Polygon geography types to multi Polygons to account for any MultiPolygons already
    existing in the data. Polygons can convert to Multipolygons but not the other way around
    :param geom: Geometry object
    :return: MultiPolygon object
    """
    return MultiPolygon([geom]) if type(geom) == Polygon else geom


def create_wkt_element(geom, srid=SRID):
    """
    Converts a geometry element to a string that is readable by PostGIS
    :param geom: Geometry object
    :param srid: ID for a spatial reference system
    :return: SQL compatible string
    """
    return WKTElement(geom.wkt, srid=srid)


def write_to_sql(table_name, geo_df, columns, engine, srid=SRID):
    """

    :param table_name:
    :param geo_df:
    :param columns:
    :param srid:
    :return:
    """
    # Convert to multi-polygon and stringify the geography column
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(convert_to_multi_poly)
    geo_df[GEOMETRY_COL] = geo_df[GEOMETRY_COL].apply(create_wkt_element)
    geo_df[columns].to_sql(table_name, engine, if_exists='replace', index=False,
                           dtype={GEOMETRY_COL: Geometry("MULTIPOLYGON", srid=srid)})




if __name__ == '__main__':
    geo_df = build_level_df(geo_level=TOWN, file_type=CARTO)
    geo_df['geom_sql'] = geo_df['geometry'].apply(create_wkt_element)
    geo_df = gpd.read_file('zip:///home/ec2-user/cb_2018_09_cousub_500k.zip')

