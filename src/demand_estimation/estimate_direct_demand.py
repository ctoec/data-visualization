import pandas as pd
import censusdata

'''
Poverty levels come from https://aspe.hhs.gov/poverty-guidelines
State SMI numbers come from https://www.ctcare4kids.com/income-guidelines-for-new-applications/ 
'''

POVERTY_PROPORTION_FIELD = 'B17024'
STATE_CODE = '09'

def get_poverty_based_demand(original_df):

    poverty_df = original_df[['NAME', 'income_under_poverty_under_6']].copy()
    return poverty_df


def get_full_child_demand(original_df):

    child_demand_df = original_df[['NAME', 'pop_male_under_5', 'pop_female_under_5']].copy()
    child_demand_df['total_children'] = child_demand_df['pop_male_under_5'] + child_demand_df['pop_female_under_5']
    return child_demand_df[['NAME', 'total_children']]


def get_under_6_poverty_levels():

    # 2 and 14 here are the upper and lower bounds for the range of fields from the census for relative income to poverty
    # for under 6 year olds
    under_6_fields = [f'B17024_{str(x).zfill(3)}E' for x in range(2, 15)]
    under_6_initial_pull_state = censusdata.download('acs5', 2019, censusdata.censusgeo([('state', STATE_CODE)]), under_6_fields)
    under_6_initial_pull_towns = censusdata.download('acs5', 2019, censusdata.censusgeo([('state', STATE_CODE), ('county', '*'), ('county subdivision', '*')]), under_6_fields)
    field_dicts = censusdata.censusvar('acs5', 2019, under_6_fields)
    rename_dict = {x: field_dicts[x][1].split('!!')[-1] for x in under_6_fields}
    under_6_initial_pull_state.rename(columns=rename_dict, inplace=True)
    under_6_initial_pull_towns.rename(columns=rename_dict, inplace=True)

    return under_6_initial_pull_state, under_6_initial_pull_towns


if __name__ == '__main__':
    get_under_6_poverty_levels()
