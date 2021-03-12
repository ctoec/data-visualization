import pandas as pd

BASE_TOWN_FILE = "town_data.csv"
CALCULATED_PARENT_METRIC_FILE = "town_demand_estimated_data.csv"
SMI_ELIGIBLE_CHILDREN_FILE = "town_estimates.csv"
OUT_FILE = "final_demand_by_town.csv"

towns = pd.read_csv(BASE_TOWN_FILE)
towns.drop(columns=[c for c in towns.columns if not c in ['NAME', 'COUSUBFP']], inplace=True)
towns.rename(columns={'NAME': 'town'}, inplace=True)
parent_metric_df = pd.read_csv(CALCULATED_PARENT_METRIC_FILE)
smi_df = pd.read_csv(SMI_ELIGIBLE_CHILDREN_FILE)
df = towns.merge(parent_metric_df, on='town')
df = df.merge(smi_df, on='town')
df.drop(columns=['min_full_estimate', 'max_full_estimate'], inplace=True)
df.rename(columns={'COUSUBFP': 'county_code', 'demand_estimate_working_parents': 'estimated_demand_by_care_availability', 'mid_full_estimate': 'children_eligible_for_care_services'}, inplace=True)
df.to_csv(OUT_FILE, index=False)