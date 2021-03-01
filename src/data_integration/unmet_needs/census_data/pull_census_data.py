import requests
import urllib.parse
import censusdata
from us import states
from census_fields import CENSUS_FIELDS
from shapefiles import TOWN

import pandas as pd

## TODO
# Get common API key

CENSUS_API_KEY = '98a3cf08d29a1fdb0e6ad0c5107f66bf932bfba4' # Get an API key https://api.census.gov/data/key_signup.html
CENSUS_FIELD_LIMIT = 50
CENSUS_NAME_FIELD = 'NAME'


def get_census_fields(fields: list, year: int = 2019, data_set: str = 'acs/acs5', geography: str = TOWN, state_fips: int = states.CT.fips):
    """
    Wrapper for Census API call that gets around the Census' limit on 50 fields per API call
    :param fields: list of Census variables
    :param year: Year of census data
    :param data_set: Census data set to use
    :param geography: Geogrpa
    :param state_fips:
    :return: combined dataframe from all calls
    """
    field_list_of_list = []
    for i in range(0, len(fields), CENSUS_FIELD_LIMIT):
        field_list_of_list.append(fields[i:i+CENSUS_FIELD_LIMIT])

    return_df = _get_census_fields(fields=field_list_of_list[0], year=year, data_set=data_set, geography=geography, state_fips=state_fips)

    for field_list in field_list_of_list[1:]:
        new_df = _get_census_fields(fields=field_list, year=year, data_set=data_set, geography=geography, state_fips=state_fips)
        return_df = return_df.merge(new_df, how='outer', on=CENSUS_NAME_FIELD)

    return return_df


def _get_census_fields(fields: list, year: int = 2019, data_set: str = 'acs/acs5', geography: str = TOWN, state_fips: int = states.CT.fips, sub_geos='in=county:*'):
    """
    Calls Census API for the provided fields, defaults to acs 5 data from 2019 in Connecticut. This will pull all the
    data requested for ever geography division in the passed geography
    https://www.census.gov/data/developers/data-sets/acs-5year.html
    :param fields: list of Census variables, full ACS list can be found here: https://api.census.gov/data/2019/acs/acs5/variables.html
    :param year: Year of census data
    :param data_set: Census data set to use
    :param geography: Lowest level of geography required
    :param sub_geos: Sub-state geopraphies to return eg. counties and tracts, these are generally in the form &in=tract:*
    https://api.census.gov/data/2019/acs/acs5/examples.html
    :param state_fips:
    :return:
    """
    # Build and encode URL
    field_string = ",".join(fields)
    url = f'https://api.census.gov/data/{year}/{data_set}?get={CENSUS_NAME_FIELD},{field_string}&for={urllib.parse.quote(geography)}:*&in=state:{str(state_fips)}&{sub_geos}&key={CENSUS_API_KEY}'
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

