import pandas as pd
import censusdata

'''
Poverty levels come from https://aspe.hhs.gov/poverty-guidelines
State SMI numbers come from https://www.ctcare4kids.com/income-guidelines-for-new-applications/ 
'''

POVERTY_PROPORTION_FIELD = 'B17024'
HOUSEHOLD_SIZE_FIELD = 'B11016'
STATE_CODE = '09'

# Estimated in smi_to_poverty notebook, this is the approximate level relative to the poverty line the is equivalent to 75% SMI
# The weighted average of the 75% SMI / Poverty by household size is 3.44
LAST_BUCKET = 3.0
PROPORTION_OF_LAST_BUCKET = .44

def get_household_size_buckets():

    household_size_fields = [f"{HOUSEHOLD_SIZE_FIELD}_{str(x).zfill(3)}E" for x in range(3, 9)]
    household_size_pull = censusdata.download('acs5', 2019, censusdata.censusgeo([('state', STATE_CODE)]), household_size_fields)
    field_dicts = censusdata.censusvar('acs5', 2019, household_size_fields)
    rename_dict = {x: field_dicts[x][1].split('!!')[-1][0] for x in household_size_fields}

    household_size_pull.rename(columns=rename_dict, inplace=True)

    return household_size_pull.T.rename(columns=lambda x:'num_households')


def get_under_6_full_poverty_levels():

    # 3 and 15 here are the upper and lower bounds for the range of fields from the census for relative income to poverty
    # for under 6 year olds. This does not include the aggregate and goes from Under .5 of Poverty to 5x poverty and above
    under_6_fields = [f'{POVERTY_PROPORTION_FIELD}_{str(x).zfill(3)}E' for x in range(3, 15)]
    under_6_initial_pull_state = censusdata.download('acs5', 2019, censusdata.censusgeo([('state', STATE_CODE)]), under_6_fields)
    under_6_initial_pull_towns = censusdata.download('acs5', 2019, censusdata.censusgeo([('state', STATE_CODE), ('county', '*'), ('county subdivision', '*')]), under_6_fields)
    field_dicts = censusdata.censusvar('acs5', 2019, under_6_fields)
    rename_dict = {x: field_dicts[x][1].split('!!')[-1] for x in under_6_fields}
    under_6_initial_pull_state.rename(columns=rename_dict, inplace=True)
    under_6_initial_pull_towns.rename(columns=rename_dict, inplace=True)

    return under_6_initial_pull_state, under_6_initial_pull_towns


def clean_town_name(df):
    """
    Takes the census town name in the index and makes it into a column with the town name.
    All columns that aren't towns are dropped
    :param df:
    :return:
    """
    df['town'] = df.index.astype(str).str.split(',')
    df = df.loc[df['town'].apply(lambda x: True if 'town' in x[0] else False), :]
    df['town'] = df['town'].apply(lambda x: x[0].replace(' town', '').strip())
    df = df.reset_index(drop=True)
    return df


def rename_poverty_cols(col_name):
    if 'Under' in col_name:
        return 0
    else:
        val = col_name.split(' ')[0]
        try:
            return float(val)
        except Exception:
            return val


def get_town_estimates(df, cutoff=LAST_BUCKET, last_proportion=PROPORTION_OF_LAST_BUCKET):

    # Get columns including and not including the cutoff
    max_sum_cols = [x for x in df.columns if (type(x) == float or type(x) == int) and x <= cutoff]
    max_sum_cols.sort()
    min_sum_cols = max_sum_cols[:-1]
    min_calc = df[min_sum_cols].sum(axis=1)
    proportion_calc = df[cutoff] * last_proportion + df[min_sum_cols].sum(axis=1)
    max_calc = df[max_sum_cols].sum(axis=1)
    final_df = pd.concat([df['town'], min_calc, proportion_calc, max_calc], axis=1)
    final_df.columns = ['town', 'min_full_estimate', 'mid_full_estimate', 'max_full_estimate']
    return final_df


if __name__ == '__main__':
    state_under_6, town_under_6 = get_under_6_full_poverty_levels()
    town_under_6.rename(columns=lambda x: rename_poverty_cols(x), inplace=True)
    town_under_6 = clean_town_name(town_under_6)
    town_df = get_town_estimates(town_under_6)
    town_df.to_csv('town_estimates.csv', index=False)
