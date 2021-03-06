import geopandas as gpd
import os
import requests

CT_EPSG_CODE = 2775 # Projection for state of Connecticut, makes centroids more precise
DEFAULT_LAT_LONG_PROJ = 4269 # Default lat/long projection for US
DATA_FOLDER = 'data'

# Documentation surrounding census data and shapefiles
# https://www2.census.gov/geo/tiger/Directory_Contents_ReadMe.pdf
# https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2020pl/TGRSHP2020PL_TechDoc.pdf
# https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
# https://www2.census.gov/geo/tiger/GENZ2018/2018_file_name_def.pdf
# https://www2.census.gov/geo/tiger/TIGER2020/2020_TL_Shapefiles_File_Name_Definitions.pdf
TOWN = 'county subdivision'
PUMA = 'puma'
SENATE = 'sldu'
HOUSE = 'sldl'
TIGER = 'tiger'
CARTO = 'carto'
BLOCK = 'block'

CENSUS_NAME = 'NAME'
CENSUS_STATE_ID = 'STATEFP'
CENSUS_COUNTY_ID = 'COUNTYFP'
CENSUS_TOWN_ID = 'COUSUBFP'
CENSUS_GEO_ID = 'GEOID'
CENSUS_HOUSE_ID = 'SLDLST'
CENSUS_SENATE_ID = 'SLDUST'
CENSUS_TRACT_ID = 'TRACTCE'
CENSUS_BLOCK_ID = 'BLKGRPCE'

FINAL_NAME = 'name'
FINAL_STATE_ID = 'state_id'
FINAL_COUNTY_ID = 'county_id'
FINAL_TOWN_ID = 'town_id'
FINAL_GEO_ID = 'geo_id'
FINAL_HOUSE_ID = 'house_district_id'
FINAL_SENATE_ID = 'senate_district_id'
FINAL_TRACT_ID = 'tract_id'
FINAL_BLOCK_ID = 'block_id'


RENAME_DICT = {CENSUS_NAME: FINAL_NAME,
               CENSUS_STATE_ID: FINAL_STATE_ID,
               CENSUS_COUNTY_ID: FINAL_COUNTY_ID,
               CENSUS_TOWN_ID: FINAL_TOWN_ID,
               CENSUS_GEO_ID: FINAL_GEO_ID,
               CENSUS_HOUSE_ID: FINAL_HOUSE_ID,
               CENSUS_SENATE_ID: FINAL_SENATE_ID,
               CENSUS_BLOCK_ID: FINAL_BLOCK_ID,
               CENSUS_TRACT_ID: FINAL_TRACT_ID}

sub_county_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/COUSUB/tl_2020_09_cousub.zip'
sub_county_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_cousub_500k.zip'
puma_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_puma10_500k.zip'
puma_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/PUMA/tl_2020_09_puma10.zip'
senate_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/SLDU/tl_2020_09_sldu.zip'
house_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/SLDL/tl_2020_09_sldl.zip'
house_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_sldl_500k.zip'
senate_carto_file = 'https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_09_sldu_500k.zip'
block_full_tiger_file = 'https://www2.census.gov/geo/tiger/TIGER2020/BG/tl_2020_09_bg.zip'

REFERENCE_DICT = {TOWN: {TIGER: sub_county_full_tiger_file, CARTO: sub_county_carto_file},
                  PUMA: {TIGER: puma_full_tiger_file, CARTO: sub_county_carto_file},
                  SENATE: {TIGER: senate_full_tiger_file, CARTO: senate_carto_file},
                  HOUSE: {TIGER: house_full_tiger_file, CARTO: house_carto_file},
                  BLOCK: {TIGER: block_full_tiger_file}}


def download_all_data():

    for geo_level, file_type_dict in REFERENCE_DICT.items():
        for file_type in file_type_dict.keys():
            build_level_df(geo_level=geo_level, file_type=file_type, redownload=True)


def add_centroid(geo_df: gpd.GeoDataFrame,
                 new_epsg_code: int = CT_EPSG_CODE,
                 final_epsg_code: int = DEFAULT_LAT_LONG_PROJ) -> gpd.GeoDataFrame:
    """

    :param geo_df:
    :param new_epsg_code:
    :return:
    """
    geo_df = geo_df.to_crs(epsg=new_epsg_code)
    geo_df['centroid'] = geo_df.centroid
    geo_df = geo_df.to_crs(epsg=final_epsg_code)
    geo_df['centroid'] = geo_df['centroid'].to_crs(epsg=final_epsg_code)
    geo_df['lat'] = geo_df['centroid'].y
    geo_df['long'] = geo_df['centroid'].x
    return geo_df


def build_level_df(geo_level, file_type, redownload=False):

    file_type_dict = REFERENCE_DICT[geo_level]
    url = file_type_dict[file_type]

    file_name = get_geo_data_zip_file(url=url, geo_type=geo_level, file_type=file_type, redownload=redownload)
    df = gpd.read_file(f'zip://{file_name}')
    df = add_centroid(geo_df=df)
    df.rename(columns=RENAME_DICT, inplace=True)
    return df


def get_geo_data_zip_file(url: str, geo_type: str, file_type: str, redownload=False) -> [str]:
    """
    Downloads and unzips files from URL if they don't already exist and returns a list of all the downloaded file names
    :param url: Url where zip file lives
    :param geo_type: Level of geographic detail (Towns, leg. districts)
    :param file_type: Flavor of shapefile to download (TIGER, cartographic lines)
    :param redownload: Whether to download the data regardless of whether it exists locally
    :return: list of filenames in the pulled directory
    """

    file_dir = os.path.dirname(os.path.realpath(__file__))
    geo_folder_name = f"{file_dir}/{DATA_FOLDER}/{geo_type.replace(' ', '_')}"
    if not os.path.exists(geo_folder_name):
        os.mkdir(geo_folder_name)
    full_folder_name = f"{geo_folder_name}/{file_type}/"
    if not os.path.exists(full_folder_name):
        os.mkdir(full_folder_name)
    file_name = (full_folder_name + os.path.basename(url))

    if not os.path.exists(file_name) or redownload:
        request = requests.get(url)
        print(f"Downloading data from {url}, saving to {file_name}")
        with open(file_name, 'wb') as output_file:
            output_file.write(request.content)

    # Check if the folder has already been downloaded or if it should be redownloaded
    return file_name


if __name__ == '__main__':
    download_all_data()


