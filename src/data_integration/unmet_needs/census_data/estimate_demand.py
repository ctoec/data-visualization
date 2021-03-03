import pandas as pd

CENSUS_DATA_FILE = 'data/census_data.csv'


# Assume demand is only children in poverty

def get_poverty_based_demand(original_df):

    poverty_df = original_df[['NAME', 'income_under_poverty_under_6']].copy()
    return poverty_df


def get_full_child_demand(original_df):

    child_demand_df = original_df[['NAME', 'pop_male_under_5', 'pop_female_under_5']].copy()
    child_demand_df['total_children'] = child_demand_df['pop_male_under_5'] + child_demand_df['pop_female_under_5']
    return child_demand_df[['NAME', 'total_children']]


def fancy_model_combining(combined_df):
    return combined_df


if __name__ == '__main__':
    df = pd.read_csv(CENSUS_DATA_FILE)
    child_df = get_full_child_demand(df)
    poverty_df = get_poverty_based_demand(df)

    final_df = child_df.merge(poverty_df, on='NAME')
    fancy_model_combining(combined_df=final_df)
