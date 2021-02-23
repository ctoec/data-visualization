import pandas as pd
from sqlalchemy import create_engine
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from geoalchemy2 import Geometry, WKTElement
import geopandas as gpd


def convert_to_multi_poly(geom):
	return MultiPolygon([geom]) if type(geom) == Polygon else geom

def create_wkt_element(geom):
    return WKTElement(geom.wkt, srid =4269)

def wkb_hexer(line):
    return line.wkb_hex