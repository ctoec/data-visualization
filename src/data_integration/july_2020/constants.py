import os

DATA_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/data/'
REFERENCE_DATA_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/reference_data/'
JULY_2020_DATA_FILE = DATA_FOLDER + 'ece_feb_20_data_collection.csv'
JULY_2020_SITE_DATA_FILE = DATA_FOLDER + 'ece_feb_20_site_data.csv'
SMI_AND_FPL_DATA = REFERENCE_DATA_FOLDER + 'fpl_and_smi.csv'
LICENSE_DATA = REFERENCE_DATA_FOLDER + 'state_funded_program_list.csv'
STUDENT_FILE = DATA_FOLDER + 'student_data.csv'
STUDENT_LEGIS_FILE = DATA_FOLDER + 'student_data_legislative.csv'
SITE_FILE = DATA_FOLDER + 'site_data.csv'
LAT_LONG_LOOKUP = REFERENCE_DATA_FOLDER + 'site_lat_long_lookup.json'
SITE_LEGIS_LOOKUP = REFERENCE_DATA_FOLDER + 'site_legislature_lookup.json'
FACILITY_CODE_COL = 'Facility Code'

# Columns with explict PII,
PII_COLUMNS = ['Name and DOB',
               'Child Last Name ',
               'Child Middle Name ',
               'Child First Name ',
               'Child Date of Birth',
               'SASID (if available) ',
               'Family street address '
               ]

# Columns that were added to the spreadsheet to calculate all available spaces, not child level data
PROGRAM_TOTAL_COLS = [
    'PROGRAM/SITE/SUBGRANTEE \n(Registry Licensed Name)\n(ALL) [ECE Division Contact List]',
    'Legal Operator (LO) (eLicense Sep2020)',
    'FACILITY CODE (ECIS & PSIS)',
    'License # (ECE & eLicense Sep2020)',
    'License Type (eLicense Sep2020)',
    'License # (eLicense)',
    'NAEYC EXPIRATION [ECE]',
    'Funding \n(Multiple types)',
    'Total Preschool Spaces # Spaces Feb 2020',
    'Total Infant/Toddler Spaces # Spaces Feb 2020',
    'Total School Age Spaces # Spaces Feb 2020',
    'Total All Spaces (Sum) Spaces Feb 2020',
    'Total All Spaces # Spaces Feb 2020']

# Indicator in C4K Region that the row is metadata about a site and not a child
DUMMY_REGION = 'x_ECE Site Details'

RENAME_DICT = {'Race of Child For Reporting': 'Race for Reporting',
               'Child Race American Indian or Alaskan Native, Asian, Black or African American, Native Hawaiian Or Pacific Islander, White - rev': 'All Race Options',
               'Gender Female, Male, Nonbinary, Unknown': 'Gender',
               'Ethnicity Not Hispanic or Latinx, Hispanic or Latinx - rev': 'Ethnicity',
               'Annual household income_x': 'Annual Household Income',
               'From': 'Data Submitted By',
               'City ECE Site': 'Town - Site',
               'Family town of residence': 'Town - Family',
               'ECIS/PSIS Facility Code': FACILITY_CODE_COL
               }

SITE_COL_RENAME_DICT = {
    'PROGRAM/SITE/SUBGRANTEE \n(Registry Licensed Name)\n(ALL) [ECE Division Contact List]': 'Site Name',
    'AssignedFacilityCode - ECIS': FACILITY_CODE_COL,
    'Total Preschool Spaces # Spaces Feb 2020': 'Preschool Spaces',
    'Total Infant/Toddler Spaces # Spaces Feb 2020': 'Infant/Toddler Spaces',
    'Total School Age Spaces # Spaces Feb 2020': 'School Age Spaces',
    'Total All Spaces (Sum) Spaces Feb 2020': 'All Available Spaces',
    'ADDRESS [ECE]': 'Address',
    'TOWN [ECE]': 'Town',
    'ZIP [ECE]': 'ZIP Code'
}

SITE_FINAL_COLS = ['Site Name',
                   'Full Address',
                   'Preschool Spaces',
                   'Infant/Toddler Spaces',
                   'School Age Spaces',
                   'All Available Spaces',
                   'Facility Code',
                   'Town Code',
                   'Address',
                   'Town',
                   'ZIP Code',
                   'Latitude',
                   'Longitude',
                   'Town from Census'
                   ]
