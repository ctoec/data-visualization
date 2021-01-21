import pandas as pd
from constants import JULY_2020_DATA_FILE, PROGRAM_TOTAL_COLS, PII_COLUMNS, DUMMY_REGION, DATA_FOLDER

STRIPPED_FILE = DATA_FOLDER + '/stripped_file.csv'

if __name__ == '__main__':

    # Load file as tab separated sheet, file is a copy of the
    df = pd.read_csv(JULY_2020_DATA_FILE, sep='\t')

    # Drop rows that are actually site metadata
    df = df[df['C4K Region'] != DUMMY_REGION]

    # Strip whitespace from columns
    df.rename(columns=lambda x: x.strip(), inplace=True)

    # Round dates to the nearest birth month. 109 rows have bad dates
    # 106 of which are value errors in Excel or were input as 0
    df['Birth Month'] = pd.to_datetime(df['Child Date of Birth'], errors='coerce').dt.strftime("%Y-%m-01")
    # Drop PII and additional added columns
    df.drop(['Unnamed: 0'] + PII_COLUMNS + PROGRAM_TOTAL_COLS, axis=1, inplace=True)

    df.to_csv(STRIPPED_FILE, index=False)
