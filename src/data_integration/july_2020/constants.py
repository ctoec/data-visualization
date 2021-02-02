import os

DATA_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/data/'
REFERENCE_DATA_FOLDER = os.path.dirname(os.path.realpath(__file__)) + '/reference_data/'
JULY_2020_DATA_FILE = DATA_FOLDER + 'ece_feb_20_data_collection.csv'
SMI_AND_FPL_DATA = REFERENCE_DATA_FOLDER + 'fpl_and_smi.csv'
LICENSE_DATA = REFERENCE_DATA_FOLDER + 'license_data.csv'

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
               'Family town of residence': 'Town - Family'
               }
