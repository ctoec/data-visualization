import pandas as pd
from constants import JULY_2020_DATA_FILE, PROGRAM_TOTAL_COLS, PII_COLUMNS, DUMMY_REGION, \
    DATA_FOLDER, SMI_AND_FPL_DATA, RENAME_DICT

STRIPPED_FILE = DATA_FOLDER + '/stripped_file.csv'

if __name__ == '__main__':

    # Load file as tab separated sheet, file is a copy of the
    df = pd.read_csv(JULY_2020_DATA_FILE, sep='\t')

    # Round dates to the nearest birth month. 109 rows have bad dates
    # 106 of which are value errors in Excel or were input as 0
    df['Birth Month'] = pd.to_datetime(df['Child Date of Birth'], errors='coerce').dt.strftime("%Y-%m-01")

    # Convert concatenated names and birthdays to unique categories
    df['Name and DOB'] = pd.Categorical(df['Name and DOB'])
    df['unique_name_ids'] = df['Name and DOB'].cat.codes

    # Drop PII and additional added columns
    df.drop(['Unnamed: 0'] + PII_COLUMNS + PROGRAM_TOTAL_COLS, axis=1, inplace=True)

    # Strip whitespace and parens for db loading from columns
    df.rename(columns=lambda x: x.strip().replace('(', '').replace(')', ''), inplace=True)

    # Rename columns to be easier to read
    df.rename(columns=RENAME_DICT, inplace=True)
    # Drop rows that are actually site metadata
    df = df[df['C4K Region'] != DUMMY_REGION]

    # Clean Race column
    df['Race'] = df['Race'].str.replace('_', ' ').str.strip().str.title()



    # Add SMI and FPL
    smi_and_fpl = pd.read_csv(SMI_AND_FPL_DATA)
    df.merge(smi_and_fpl, how='left', left_on='Household size', right_on='family_size')
    df.to_csv(STRIPPED_FILE, index=False)
