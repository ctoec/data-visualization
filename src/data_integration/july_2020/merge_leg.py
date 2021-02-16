import json
import pandas as pd
from constants import  STUDENT_LEGIS_FILE
from build_legislative_lookup import SITE_LEGIS_LOOKUP, parse_legislator_results


def merge_legislative_data(student_df):
    """
    Combines legislative data associated with a site with student data to build a table that can show
    legislators associated with children attending sites in their districts
    :param student_df:
    :return: None, saves file to disk
    """

    with open(SITE_LEGIS_LOOKUP, 'r') as f:
        leg_lookup = json.load(f)

    rows = []
    for key, row_dict in leg_lookup.items():

        # Get metadata from legislative lookup that is not from the API call
        initial_data = {key: row_dict[key] for key in row_dict if key != 'raw_result'}

        # Get the API call with the specified columns
        leg_dict = parse_legislator_results(row_dict['raw_result'])
        final_row_dict = {**initial_data, **leg_dict}
        rows.append(final_row_dict)

    # Build dataframe with Facility Coe and legislative data
    leg_df = pd.DataFrame(rows)

    # Build table with

    merged_df = student_df.merge(leg_df, how='left', on='Facility Code')
    merged_df.to_csv(STUDENT_LEGIS_FILE, index=False)

from constants import STUDENT_FILE
df = pd.read_csv(STUDENT_FILE)
merge_legislative_data(df)
