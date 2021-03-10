import censusdata
import pandas as pd
import numpy as np

OUT_FILE = "town_demandEstimated_data.csv"

'''
Define a function for each of the four demand estimates already written in the Jupyter 
notebook.
'''

# read in data

town = pd.read_csv('town_demand_data.csv')

def demand_estimate_1(female, male):

	return ((female + male)*0.5).apply(np.ceil) 
	#town.to_csv(OUT_FILE, index=False)

town['demand_estimate'] = demand_estimate_1(town['pop_female_under_5'], town['pop_male_under_5'])

def ratio_poverty (level_1, level_2, level_3, total_pop):

	return (level_1 + level_2 + level_3)/total_pop

town['ratio_poverty'] = ratio_poverty(town['ratio of income to poverty level - < 0.5'],  
town['ratio of income to poverty level - 0.51 - 1.0'], town['ratio of income to poverty level - 1.01 - 2.0'],
town['total population'])

def demand_estimate_2(ratio, female, male):

	return (ratio * (female + male)).apply(np.ceil)
	
town['demand_estimate_2'] = demand_estimate_2(town['ratio_poverty'], town['pop_female_under_5'], town['pop_male_under_5'])

def lowerIncome(housing, total_pop):

	#town['housing per person'] = town['housing units']/town['total population']
	
	return ((housing/total_pop) * 0.5)
	
town['%housing_lowerHalf_income'] = lowerIncome(town['housing units'],town['total population'])

def demand_estimate_3(housing_lower, female, male):
	
	return (housing_lower * (female + male)).apply(np.ceil)
	
town['demand_estimate_3'] = demand_estimate_3(town['%housing_lowerHalf_income'], town['pop_female_under_5'], town['pop_male_under_5'])

def below_200_poverty(level_1, level_2, level_3):

	return level_1 + level_2 + level_3
	
town['children_below_200%_poverty'] = below_200_poverty(town['children under 6 ratio of income to poverty level - < 0.5'], 
town['children under 6 ratio of income to poverty level - 0.51 - 1.0'],
town['children under 6 ratio of income to poverty level - 1.01 - 2.0'])

def all_parents_working(both, dad_only, mom_only, all):

	return (both + dad_only + mom_only)/all

town['%all_parents_working'] = (town['children under 6 by parent employment status - both parents - in labor force'] + 
town['children under 6 by parent employment status - only father - in labor force'] + 
town['children under 6 by parent employment status - only mother - in labor force']) / town['children under 6 by parent employment status - all categories']

def demand_estimate_4(below_200_poverty, all_parents):

	return (below_200_poverty * all_parents).apply(np.ceil)

town['demand_estimate_4'] = demand_estimate_4(town['children_below_200%_poverty'], town['%all_parents_working'])

# write out CSV

town.to_csv(OUT_FILE, index=False)

