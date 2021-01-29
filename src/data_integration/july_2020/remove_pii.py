import numpy as np
import pandas as pd
from constants import JULY_2020_DATA_FILE, PROGRAM_TOTAL_COLS, PII_COLUMNS, DUMMY_REGION, \
    DATA_FOLDER, SMI_AND_FPL_DATA, RENAME_DICT

STRIPPED_FILE = DATA_FOLDER + '/stripped_file.csv'


def clean_column(df_col):
    """
    Strip white space and underscores from column data and properly title
    :param df_col:
    :return:
    """
    return df_col.str.replace('_', ' ').str.strip().str.title()


if __name__ == '__main__':

    # Load file as tab separated sheet, file is a copy of the
    df = pd.read_csv(JULY_2020_DATA_FILE, sep='\t')

    # Round dates to the nearest birth month. 109 rows have bad dates
    # 106 of which are value errors in Excel or were input as 0
    df['Birth Month'] = pd.to_datetime(df['Child Date of Birth'], errors='coerce').dt.strftime("%Y-%m-01")

    # Convert concatenated names and birthdays to unique categories for deduplication analysis
    id_cols = ['Child First Name ', 'Child Middle Name ', 'Child Last Name ', 'Child Date of Birth']
    df['unique_name_ids'] = pd.Categorical(df[id_cols].apply(lambda row: ''.join(x.lower() for x in row.values.astype(str)), axis=1))
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

    # Make income a float
    df['Annual Household Income'] = df["Annual Household Income"].str.replace('$', '').str.replace(',', '')
    df['Annual Household Income'] = pd.to_numeric(df['Annual Household Income'], errors='coerce')

    # Add SMI and FPL
    df['Household size'] = df['Household size'].replace({'SPED': np.nan, '9 or more': 9}).astype(float)
    smi_and_fpl = pd.read_csv(SMI_AND_FPL_DATA)
    df = df.merge(smi_and_fpl, how='left', left_on='Household size', right_on='family_size')
    df.to_csv(STRIPPED_FILE, index=False)
