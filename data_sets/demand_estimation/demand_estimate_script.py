import censusdata
import pandas as pd
import numpy as np

OUT_FILE = "town_demand_estimated_data.csv"

'''
Define a function for each of the four demand estimates already written in the Jupyter 
notebook.
'''

# read in data

town = pd.read_csv('town_demand_data.csv')

def ratio_poverty (level_1, level_2, level_3, total_pop):

	return (level_1 + level_2 + level_3)/total_pop


def demand_estimate_ratio_poverty(ratio, female, male):

	return (ratio * (female + male)).apply(np.ceil)
	

def lower_income(housing, total_pop):
	
	return ((housing/total_pop) * 0.5)
	

def demand_estimate_income_housing(housing_lower, female, male):
	
	return (housing_lower * (female + male)).apply(np.ceil)
	
	
def below_200_poverty(level_1, level_2, level_3):

	return level_1 + level_2 + level_3


def all_parents_working(both, dad_only, mom_only, all):

	return (both + dad_only + mom_only)/all


def demand_estimate_working_parents(below_200_poverty, all_parents):

	return (below_200_poverty * all_parents).apply(np.ceil)


# calculating ratio of poverty
town['ratio_poverty'] = ratio_poverty(town['ratio of income to poverty level - < 0.5'],  
town['ratio of income to poverty level - 0.51 - 1.0'], town['ratio of income to poverty level - 1.01 - 2.0'],
town['total population'])

# demand estimate 1
town['demand_estimate_lower_quintiles'] = demand_estimate_ratio_poverty(0.5, town['pop_female_under_5'], town['pop_male_under_5'])

# demand estimate 2
town['demand_estimate_ratio_poverty'] = demand_estimate_ratio_poverty(town['ratio_poverty'], town['pop_female_under_5'], town['pop_male_under_5'])

# percent of housing in bottom half of income
town['pct_housing_lowerHalf_income'] = lower_income(town['housing units'],town['total population'])

# demand estimate 3
town['demand_estimate_income_housing'] = demand_estimate_income_housing(town['pct_housing_lowerHalf_income'], town['pop_female_under_5'], town['pop_male_under_5'])

# calculating children below 200% of poverty level
town['children_below_200_pct_poverty'] = below_200_poverty(town['children under 6 ratio of income to poverty level - < 0.5'], 
town['children under 6 ratio of income to poverty level - 0.51 - 1.0'],
town['children under 6 ratio of income to poverty level - 1.01 - 2.0'])

# calculating percentage of households where all parents are working
town['pct_all_parents_working'] = (town['children under 6 by parent employment status - both parents - in labor force'] + 
town['children under 6 by parent employment status - only father - in labor force'] + 
town['children under 6 by parent employment status - only mother - in labor force']) / town['children under 6 by parent employment status - all categories']

# demand estimate 4
town['demand_estimate_working_parents'] = demand_estimate_working_parents(town['children_below_200_pct_poverty'], town['pct_all_parents_working'])

# write out CSV

file = town[['town','demand_estimate_working_parents']]

file.to_csv(OUT_FILE, index=False)

