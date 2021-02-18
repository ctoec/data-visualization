import geopandas
import io
import os
import requests
import zipfile


DATA_FOLDER = 'data/'

# Documentation surrounding census data and shapefiles
# https://www2.census.gov/geo/tiger/Directory_Contents_ReadMe.pdf
# https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2020pl/TGRSHP2020PL_TechDoc.pdf
# https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
SUB_COUNTY = 'cousub'
PUMA = 'puma'
SENATE = 'sldu'
HOUSE = 'sldl'
TIGER = 'tiger'
CARTO = 'carto'

sub_county_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/COUSUB/tl_2020_09_cousub.zip'
sub_county_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_cousub_500k.zip'
puma_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_puma10_500k.zip'
puma_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/PUMA/tl_2020_09_puma10.zip'
senate_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/SLDU/tl_2020_09_sldu.zip'
house_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/SLDL/tl_2020_09_sldl.zip'
house_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_sldl_500k.zip'
senate_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_sldu_500k.zip'

reference_dict = {SUB_COUNTY: {TIGER: sub_county_full_tiger_file, CARTO: sub_county_carto_file},
                  PUMA: {TIGER: puma_full_tiger_file, CARTO: sub_county_carto_file},
                  SENATE: {TIGER: senate_full_tiger_file, CARTO: senate_carto_file},
                  HOUSE: {TIGER: house_full_tiger_file, CARTO: house_carto_file}}

def get_shapefile(url, geo_type, file_type):
    """

    :param url:
    :param geo_type:
    :param file_type:
    :return:
    """
    url = 'https://www2.census.gov/geo/tiger/TIGER2020/COUSUB/tl_2020_09_cousub.zip'
    request = requests.get(url)
    file = zipfile.ZipFile(io.BytesIO(request.content))
    file.extractall(DATA_FOLDER)





