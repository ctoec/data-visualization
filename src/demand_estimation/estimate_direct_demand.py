import pandas as pd
import censusdata

'''
Poverty levels come from https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-poverty-thresholds/thresh20.xls
and take the average poverty level cutoff between households with 1 non-child member and household with 2 non-child members.
All households for demand will have at least one child and the range of incomes is small.  
'''

CENSUS_POVERTY_LEVELS = 'https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-poverty-thresholds/thresh20.xls'
POVERTY_PROPORTION_FIELD = 'B17024'

def get_poverty_based_demand(original_df):

    poverty_df = original_df[['NAME', 'income_under_poverty_under_6']].copy()
    return poverty_df


def get_full_child_demand(original_df):

    child_demand_df = original_df[['NAME', 'pop_male_under_5', 'pop_female_under_5']].copy()
    child_demand_df['total_children'] = child_demand_df['pop_male_under_5'] + child_demand_df['pop_female_under_5']
    return child_demand_df[['NAME', 'total_children']]


def fancy_model_combining(combined_df):
    return combined_df

def get_under_6_poverty_levels():

    # 2 and 14 here are the upper and lower bounds for the range of fields from the census for relative income to poverty
    # for under 6 year olds
    under_6_fields = [f'B17024_{str(x).zfill(3)}E' for x in range(2, 15)]
    under_6_initial_pull = censusdata.download('acs5', 2019, censusdata.censusgeo([('state', '09')]), under_6_fields)
    field_dicts = censusdata.censusvar('acs5', 2019, under_6_fields)
    rename_dict = {x: field_dicts[x][1].split('!!')[-1] for x in under_6_fields}
    under_6_initial_pull.rename(columns=rename_dict)

    return under_6_initial_pull.T



def get_state_median_income():

    # Download median income for CT (state code 09) for 2-7 people in the household to calculate state median income
    census_smi_df = censusdata.download('acs5', 2019, censusdata.censusgeo([('state', '09')]),
                                        ['B19119_002E', 'B19119_003E', 'B19119_004E', 'B19119_005E',
                                         'B19119_006E', 'B19119_007E'])
    census_smi_df.rename(
        columns=lambda x: int(x.replace('B19119_00', '').replace('E','')),
        inplace=True,
        index=lambda x: 'ct_smi'
    )

    return census_smi_df.T


if __name__ == '__main__':
    df = pd.read_csv(CENSUS_DATA_FILE)
    child_df = get_full_child_demand(df)
    poverty_df = get_poverty_based_demand(df)

    final_df = child_df.merge(poverty_df, on='NAME')
    fancy_model_combining(combined_df=final_df)
