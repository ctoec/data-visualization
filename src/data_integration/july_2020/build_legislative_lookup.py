import pandas as pd
import requests
import math
import json
import time
from constants import SITE_FILE, SITE_LEGIS_LOOKUP, FACILITY_CODE_COL

# ENTER YOUR OPEN STATES KEY
API_KEY = '5edee751-ebd3-4b5f-ae32-3f8038f03055'
RAW_RESULT_KEY = 'raw_result'


def get_lat_lon_key(lat, lon):
    """"
    Standardized key for dictionary
    """
    return f"{lat}----{lon}"


def parse_legislator_results(results_json):
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


def get_district(lat, lon):
    """
    This function calls the Open States API on
    a lat lon pair decoded from the lat lon pair string
    Parameters: str
    Returns: dict (results)
    """

    geo_url = f"https://v3.openstates.org/people.geo?lat={lat}&lng={lon}&apikey={API_KEY}"
    print(f"Calling {lat} and {lon}")
    response = requests.get(geo_url)

    counter = 0
    while response.status_code != 200:

        # The open state API only allows 10 queries a minute and then returns a 429, this adds a wait for that time
        if response.status_code != 500:
            print(f"Sleeping on {lat} and {lon} with {response.text}")
            time.sleep(61)
        print(f"Calling {lat} and {lon}")
        response = requests.get(geo_url)

        # Try twice and then return None, the API 500s regularly
        counter += 1
        if counter >= 2:
            return None

    results = response.json()
    return results


def create_legislative_lookup(df):
    """
    Looks up legislatures associated with the location of each site in the site dataframe
    :param df: Dataframe with all sites
    :return: None, saves a json file with a lookup of the raw results keyed by lat/long
    """
    with open(SITE_LEGIS_LOOKUP, 'r') as f:
        legis_lookup = json.load(f)
    for i, row in df.iterrows():

        # Checkpoint save legislative district data
        if i % 10 == 0:
            print(f"Saving at {i} records")
            with open(SITE_LEGIS_LOOKUP, 'w') as fp:
                json.dump(legis_lookup, fp)

        lat = row['Latitude']
        lon = row['Longitude']

        # Skip NaN Lat/Longs
        if math.isnan(lat) or math.isnan(lon):
            continue
        lat_lon_key = get_lat_lon_key(lat=lat, lon=lon)

        # Get result from dictionary if it exists there, otherwise, call the API
        if lat_lon_key in legis_lookup:
            raw_result = legis_lookup[lat_lon_key][RAW_RESULT_KEY]
        else:
            raw_result = get_district(lat=lat, lon=lon)

        # Skip lookups that did not have a return
        if not raw_result:
            continue

        # Log result with facility code,
        save_object = {FACILITY_CODE_COL: row[FACILITY_CODE_COL],
                       'lat': lat,
                       'lon': lon,
                       RAW_RESULT_KEY: raw_result}
        legis_lookup[lat_lon_key] = save_object

    # Save final lookup dictionary
    with open(SITE_LEGIS_LOOKUP, 'w') as fp:
        json.dump(legis_lookup, fp)


if __name__ == '__main__':
    site_df = pd.read_csv(SITE_FILE)
    create_legislative_lookup(site_df)
