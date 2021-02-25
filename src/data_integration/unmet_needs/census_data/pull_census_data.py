import requests
import urllib.parse
import censusdata
from us import states
from census_fields import CENSUS_FIELDS

import pandas as pd

## TODO
# Get common API key

CENSUS_API_KEY = '' # Get an API key https://api.census.gov/data/key_signup.html
TOWN = 'county subdivision' # For Connecticut, county subdivision corresponds to towns


def get_census_fields(fields: list, year: int = 2019, data_set: str = 'acs/acs5', geography: str = TOWN, state_fips: int = states.CT.fips):
    """
    Calls Census API for the provided fields, defaults to acs 5 data from 2019 in Connecticut. This will pull all the
    data requested for ever geography division in the passed geography (
    https://www.census.gov/data/developers/data-sets/acs-5year.html
    :param fields: list of Census variables
    :param year: Year of census data
    :param data_set: Census data set to use
    :param geography: Geogrpa
    :param state_fips:
    :return:
    """
    # Build and encode URL
    field_string = ",".join(fields)
    url = f'https://api.census.gov/data/{year}/{data_set}?get=NAME,{field_string}&for={urllib.parse.quote(geography)}:*&in=state:{str(state_fips)}&key={CENSUS_API_KEY}'
    res = requests.get(url)

    # Raise error if the call was not successful
    res.raise_for_status()

    # Convert response to a dataframe and rename columns to be human readable
    data = res.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    df.rename(columns=CENSUS_FIELDS, inplace=True)
    return df


def filter_concepts(search_term):
    """
    Uses census data package to more effectively search for a certain term
    :param search_term:
    :return: list of all metrics that have the search term in the concept
    """
    init_list = censusdata.search('acs5', 2019, 'concept', search_term)
    concept_set = set([x[1] for x in init_list])
    for x in concept_set:
        print(x)
    return init_list


def get_code_from_concept(concept_name, init_list):
    """
    Gets precise code information from concept name
    :param concept_name: Precise concept name that will be exact matched
    :param init_list: list from filter_concepts of all potential concept fields
    :return: Tuple of code, concept and metric name
    """

    for x in init_list:
        if x[1] == concept_name:
            return x


if __name__ == '__main__':
    census_fields = list(CENSUS_FIELDS.keys())
    census_df = get_census_fields(census_fields)
    census_df.to_csv('data/census_data.csv', index=False)
    