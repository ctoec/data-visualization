import json
import numpy as np
import pandas as pd
import requests
from build_legislative_lookup import SITE_LEGIS_LOOKUP, parse_legislator_results
from constants import JULY_2020_DATA_FILE, PROGRAM_TOTAL_COLS, PII_COLUMNS, DUMMY_REGION, \
    SMI_AND_FPL_DATA, RENAME_DICT, SITE_COL_RENAME_DICT, FACILITY_CODE_COL, SITE_FACILITY_LOOKUP_DICT, \
    SITE_FINAL_COLS, JULY_2020_SITE_DATA_FILE, \
    LAT_LONG_LOOKUP


def standardize_facility_string(col: pd.Series) -> pd.Series:
    """
    The CSV upload to Superset is stripping leading Zeros in a unpredictable way, this coerces a string
    to facilitate future joins
    :param col: dataframe column with facility codes
    :return: column of renamed facility codes
    """
    def clean_string(item):

        # Some ids were listed as 12345 or 54321 manual checks confirm that the first number matched site and student data.
        # If 'or' is not in the name this will return the entire string
        item = str(item).split(' or ')[0]
        item = item.replace('Annex to', '').replace('?', '').strip()

        # Some facility codes were entered in correctly, this fixes the errors
        if item in SITE_FACILITY_LOOKUP_DICT:
            item = SITE_FACILITY_LOOKUP_DICT[item]
        # Add FC to Facility Code column and pad to 10 digits to ensure DB reads it correctly
        item = 'FC' + item.zfill(10)
        return item

    return_col = col.apply(clean_string)

    return return_col

def get_lat_lon(address, existing_lookup):
    """
    Get lat lon from US Census
    :param address: Address string
    :param existing_lookup: Dictionary of results from Census of previous searches base on address
    :return: tuple of lat, lon
    """
    if address in existing_lookup:
        return existing_lookup[address]
    url_encoded_address = requests.utils.quote(address)
    url = f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=" \
          f"{url_encoded_address}&benchmark=2020&format=json"
    res = requests.get(url)
    res_json = res.json()
    print(address)
    matched_address = res_json['result']['addressMatches'][0] if res_json['result']['addressMatches'] else None

    return matched_address


def clean_column(df_col):
    """
    Strip white space and underscores from column data and properly title
    :param df_col:
    :return:
    """
    return df_col.str.replace('_', ' ').str.strip().str.title()


def build_student_df():
    """
    Convert full student and site data file into just anonymous student data
    :return: Anonymized student dataframe
    """
    df = pd.read_csv(JULY_2020_DATA_FILE, sep='\t')

    # Round dates to the nearest birth month. 109 rows have bad dates
    # 106 of which are value errors in Excel or were input as 0
    df['Birth Month'] = pd.to_datetime(df['Child Date of Birth'], errors='coerce').dt.strftime("%Y-%m-01")

    # Convert concatenated names and birthdays to unique categories for deduplication analysis
    id_cols = ['Child First Name ', 'Child Middle Name ', 'Child Last Name ', 'Child Date of Birth']
    df['unique_name_ids'] = pd.Categorical(
        df[id_cols].apply(lambda row: ''.join(x.lower() for x in row.values.astype(str)), axis=1))
    df['unique_name_ids'] = df['unique_name_ids'].cat.codes

    # Flag duplicated names
    unique_ids = df['unique_name_ids'].value_counts()

    # Get all IDs included more than once
    duplicate_ids = unique_ids.index[unique_ids.gt(1)]
    df['is_duplicate'] = df['unique_name_ids'].isin(duplicate_ids)

    # Drop PII and additional added columns not associated with children
    df.drop(['Unnamed: 0'] + PII_COLUMNS + PROGRAM_TOTAL_COLS, axis=1, inplace=True)

    # Strip whitespace and parens for db loading from columns
    df.rename(columns=lambda x: x.strip().replace('(', '').replace(')', ''), inplace=True)

    # Rename columns to be easier to read
    df.rename(columns=RENAME_DICT, inplace=True)

    # Drop rows that are actually site metadata
    df = df[df['C4K Region'] != DUMMY_REGION]

    # Clean Race and Ethnicity column
    for col in ['Race for Reporting', 'Ethnicity', 'Town - Family', 'Town - Site']:
        df[col] = clean_column(df[col])

    # Add column for crossing towns
    df['attends_site_in_hometown'] = df['Town - Family'] == df['Town - Site']

    # Make income a float
    df['Annual Household Income'] = df["Annual Household Income"].str.replace('$', '').str.replace(',', '')
    df['Annual Household Income'] = pd.to_numeric(df['Annual Household Income'], errors='coerce')
    df[FACILITY_CODE_COL] = standardize_facility_string(df[FACILITY_CODE_COL])

    # Add SMI and FPL
    df['Household size'] = df['Household size'].replace({'SPED': np.nan, '9 or more': 9}).astype(float)
    smi_and_fpl = pd.read_csv(SMI_AND_FPL_DATA)
    df = df.merge(smi_and_fpl, how='left', left_on='Household size', right_on='family_size')
    return df


def build_site_df():
    """
    Converts full July 2020 student and site data file to single site file with license data included
    :param df: dataframe created from July 2020 data collection
    :return: Clean dataframe with site data
    """
    site_df = pd.read_csv(JULY_2020_SITE_DATA_FILE, sep='\t', dtype={'ZIP [ECE]': str})

    # Convert town code to integer and remove all sites that don't have a code
    site_df['Town Code'] = pd.to_numeric(site_df['Town Code'], errors='coerce')
    site_df.rename(columns=SITE_COL_RENAME_DICT, inplace=True)

    # Get address in a form acceptable for geocoding
    site_df['STATE'] = 'CT'
    base_address_cols = ['Town', 'STATE', 'ZIP Code']

    # Where there is no street address use 1 Main instead to get a reasonable location for the town
    site_df['Dummy Address'] = site_df['Address'].fillna('1 Main')
    site_df['ZIP Code'] = site_df['ZIP Code'].fillna('')
    site_df['Full Address - Lookup'] = site_df[['Dummy Address'] + base_address_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)
    site_df['Full Address'] = site_df[['Address'] + base_address_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)
    site_df['Facility Code'] = standardize_facility_string(site_df['Facility Code'])

    # Open saved file with existing data
    with open(LAT_LONG_LOOKUP) as f:
        existing_location_lookup = json.load(f)

    # Get all addresses from census API
    counter = 0
    lats = []
    longs = []
    census_towns = []
    for _, row in site_df.iterrows():
        address = row['Full Address - Lookup']
        address_result = get_lat_lon(address, existing_location_lookup)

        if not address_result:
            address = f'1 Main {row["Town"]} CT'
            address_result = get_lat_lon(address, existing_location_lookup)
            pass
        # Add nulls for results that didn't get a result
        if not address_result:
            lats.append(np.nan)
            longs.append(np.nan)
            census_towns.append('')

        # Add data to lats, longs and town and stores results
        else:
            existing_location_lookup[address] = address_result
            lats.append(address_result['coordinates']['y'])
            longs.append(address_result['coordinates']['x'])
            census_towns.append(address_result['addressComponents']['city'])

        # Checkpoint save results
        if counter % 5 == 0:
            print(counter)
            with open(LAT_LONG_LOOKUP, 'w') as f:
                json.dump(existing_location_lookup, f)

        counter += 1
    site_df['Latitude'] = lats
    site_df['Longitude'] = longs
    site_df['Town from Census'] = census_towns

    site_df_final = site_df[~site_df['Site Name'].isna()][SITE_FINAL_COLS]
    return site_df_final


def merge_legislative_data(df: pd.DataFrame, join_col=FACILITY_CODE_COL) -> pd.DataFrame:
    """
    Combine input df with legislative data based off data loaded in build_legislative_lookup
    :param df: Dataframe to join to legislative district
    :param join_col: Column to join legislative district to dataframe
    :return: pd.Dataframe with additional data on state legislators
    """
    with open(SITE_LEGIS_LOOKUP, 'r') as f:
        leg_lookup = json.load(f)

    rows = []
    for _, row_dict in leg_lookup.items():

        # Get metadata each the call to the API (lat, long, Facility Code)
        initial_data = {key: row_dict[key] for key in row_dict if key != 'raw_result'}

        # Get the raw results stored for the API and extract the needed fields from the return with parse_legislator results
        leg_dict = parse_legislator_results(row_dict['raw_result'])
        final_row_dict = {**initial_data, **leg_dict}
        rows.append(final_row_dict)

    # Build dataframe with Facility Code and legislative data
    leg_df = pd.DataFrame(rows)

    # Build table with data mapped to legislators
    merged_df = df.merge(leg_df, how='left', on=join_col)
    return merged_df

