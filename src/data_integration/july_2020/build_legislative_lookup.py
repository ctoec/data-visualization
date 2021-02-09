# DataFrame Imports
import pandas as pd
import numpy as np
# Web Imports
import requests
import math
import json
# Python Utilities Imports
import os
import time
from constants import SITE_FILE, LEG_DIST_FILE, SITE_LEGIS_LOOKUP

# ENTER YOUR OPEN STATES KEY
API_KEY = 'ad8c3463-59f9-4486-8ba0-2962a6cc4718' #5edee751-ebd3-4b5f-ae32-3f8038f03055


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
        for i in range(num_results):
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
    null_return = {'lat': lat, 'lon': lon}, leg_lookup

    if lat_lon_key in leg_lookup:
        results = leg_lookup[lat_lon_key]
        if results == {}:
            print('******* Missing data *********')
        else:
            return {'lat': lat, 'lon': lon, **parse_results(results)}, leg_lookup

    if math.isnan(lat) or math.isnan(lon):
        return null_return
    geo_url = f"https://v3.openstates.org/people.geo?lat={lat}&lng={lon}&apikey={API_KEY}"
    response = requests.get(geo_url)

    counter = 0
    while response.status_code != 200:
        print(f"Sleeping on {lat_lon_key}")
        if response.status_code != 500:
            time.sleep(70)
        else:
            print("500")
        response = requests.get(geo_url)
        counter += 1
        if counter >= 1:
            return null_return

    results = response.json()
    print("Active results")
    leg_lookup[lat_lon_key] = results
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
    with open(SITE_LEGIS_LOOKUP, 'r') as f:
        legis_lookup = json.load(f)
    leg_dist_df = create_jurisdiction_dataframe(site_df)
    leg_dist_df.to_csv(LEG_DIST_FILE)

