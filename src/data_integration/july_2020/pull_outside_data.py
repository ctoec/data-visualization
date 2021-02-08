# DataFrame Imports
import pandas as pd
import numpy as np
# Web Imports
import requests
import io
import json
# Python Utilities Imports
import os
import time
from constants import SITE_FILE, LEG_DIST_FILE, SITE_LEGIS_LOOKUP

# ENTER YOUR OPEN STATES KEY
API_KEY = '5edee751-ebd3-4b5f-ae32-3f8038f03055'



def create_latlong_unique(pandas_series_Lat, pandas_series_Lon):
    '''
    This function takes to two columns representing
    latitudes and longitudes and returns a single stirng
    to create an encoded uniqueID
    Parameters: two Pandas Column D.type float
    Returns: one str
    '''
    return pandas_series_Lat.astype(str) + '!!!' + pandas_series_Lon.astype(str)


def parse_results(results_json):
    '''
    This function parses the results of a API call
    response and returns a dictionary of values
    representing State Senators and Represeentatives
    Parameters: Dict (Json)
    Returns: Dict
    '''
    # set default values
    long_lat_jurisdiction = {
        'person_id': None,
        'senator_district' : None,
        'senator_full_name' : None,
        'senator_first_name': None,
        'senator_last_name': None,
        'senator_party': None,
        'representative_district' : None,
        'representative_full_name' : None,
        'representative_first_name': None,
        'representative_last_name': None,
        'representative_party': None,
    }

    num_results = len(results_json['results'])
    if num_results > 0:
        for i in range(len(results_json)):
            leg = results_json['results'][i]
            if 'Representative' in leg['current_role']['title']:
                long_lat_jurisdiction['person_id'] = leg['id']
                long_lat_jurisdiction['representative_district'] = leg['current_role']['district']
                long_lat_jurisdiction['representative_full_name'] = leg['name']
                long_lat_jurisdiction['representative_first_name'] = leg['given_name']
                long_lat_jurisdiction['representative_last_name'] = leg['family_name']
                long_lat_jurisdiction['representative_party'] = leg['party']
            if 'Senator' in leg['current_role']['title']:
                long_lat_jurisdiction['person_id'] = leg['id']
                long_lat_jurisdiction['senator_district'] = leg['current_role']['district']
                long_lat_jurisdiction['senator_full_name'] = leg['name']
                long_lat_jurisdiction['senator_first_name'] = leg['given_name']
                long_lat_jurisdiction['senator_last_name'] = leg['family_name']
                long_lat_jurisdiction['senator_party'] = leg['party']
    # return updated record
    return long_lat_jurisdiction


def get_district(lat, lon, leg_lookup):
    """
    This function calls the Open States API on
    a lat lon pair decoded from the lat lon pair string
    Parameters: str
    Returns: dict (results)
    """
    lat_lon_key = f"{lat}----{lon}"
    if lat_lon_key in leg_lookup:
        return leg_lookup[lat_lon_key], leg_lookup
    geo_url = f"https://v3.openstates.org/people.geo?lat={lat}&lng={lon}&apikey={API_KEY}"
    response = requests.get(geo_url)
    if lat != np.nan and lon != np.nan:
        while response.status_code != 200:
            print(f"Waiting on {lat_lon_key}")
            time.sleep(60)
            response = requests.get(geo_url)
        results = response.json()
        leg_lookup[lat_lon_key] = results
    else:
        results = {}
    print(results)
    # return district info
    return {'lat': lat, 'lon': lon, **parse_results(results)}, leg_lookup


def create_jurisdiction_dataframe(site_df):
    '''
    This function builds df of legislative jurisdictions
    pandas columns representing lat and long
    Parameters: pandas Series
    Returns: pandas DataFrame
    '''

    # long_lat_pairs_list = list(create_latlong_unique(lat_pandas_column, lon_pandas_column).unique())
    data = []
    with open(SITE_LEGIS_LOOKUP, 'r') as f:
        legis_lookup = json.load(f)
    for i, row in site_df.iterrows():
        if i % 10 == 0:
            print("Sleeping")
            time.sleep(61)
            df = pd.DataFrame(data)
            df.to_csv(LEG_DIST_FILE)
        print(f'SYSTEM: Processing {i} of {len(site_df)}\n\n')
        appendage, legis_lookup = get_district(lat=row['Latitude'], lon=row['Longitude'],
                                               leg_lookup=legis_lookup)
        appendage['Facility Code'] = row['Facility Code']
        print(f'System: Appendage:\n{appendage}\n\n')
        with open(SITE_LEGIS_LOOKUP, 'w') as fp:
            json.dump(legis_lookup, fp)
        data.append(appendage)
        print(f'SYSTEM: Data appended\n\n')
    df = pd.DataFrame(data)
    return df


if __name__ == '__main__':
    site_df = pd.read_csv(SITE_FILE)
    try:
        leg_dist_df = pd.read_csv(LEG_DIST_FILE)
    except:
        leg_dist_df = create_jurisdiction_dataframe(site_df)
        leg_dist_df.to_csv(LEG_DIST_FILE)

