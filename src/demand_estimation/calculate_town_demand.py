import os
import pandas as pd

BASE_TOWN_FILE = os.path.dirname(os.path.realpath(__file__)) + "/town_data.csv"


def create_final_town_demand(parent_metric_df, smi_df, write_filename):

    towns = pd.read_csv(BASE_TOWN_FILE)
    towns.drop(columns=[c for c in towns.columns if not c in ['NAME', 'COUSUBFP', 'COUNTYFP']], inplace=True)
    towns.rename(columns={'NAME': 'town'}, inplace=True)
    df = towns.merge(parent_metric_df, on='town')
    df = df.merge(smi_df, on='town')
    df.drop(columns=['min_full_estimate', 'max_full_estimate'], inplace=True)
    df.rename(columns={'COUNTYFP': 'county_code','COUSUBFP': 'sub_county_code', 'demand_estimate_working_parents': 'estimated_demand_by_care_availability', 'mid_full_estimate': 'children_eligible_for_care_services'}, inplace=True)
    df['county_code'] = df['county_code'].astype(str).str.zfill(3)
    df['sub_county_code'] = df['sub_county_code'].astype(str).str.zfill(5)
    df.to_csv(write_filename, index=False)
