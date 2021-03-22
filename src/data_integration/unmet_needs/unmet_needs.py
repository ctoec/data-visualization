import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from random import gauss, seed

OVERALL_DATA_FILE = "overall_supply_and_estimated_demand_for_child_care_by_age_and_by_town.csv"
OVERALL_DEMAND_COLS = ['children_needing_care_demandestimated_infantstoddlers',
                'children_needing_care_demandestimated_preschoolers']
OVERALL_SUPPLY_COLS = ['available_spaces_for_children_supply_infantstoddlers',
                'available_spaces_for_children_supply_preschoolers']
OVERALL_CONVERT_COLS = ['children_needing_care_demandestimated_infantstoddlers',
                'available_spaces_for_children_supply_infantstoddlers',
                'children_needing_care_demandestimated_preschoolers',
                'available_spaces_for_children_supply_preschoolers']
SCHOOL_DATA_FILE = "town_level_public_school_preschool_supply_and_demand.csv"
SCHOOL_DEMAND_COLS = ['total_preschoolers_needing_care']
SCHOOL_SUPPLY_COLS = ['total#_preschool_slots_public/charter/magnet_school_funded_includesoverlaps']
SCHOOL_CONVERT_COLS = ['total_preschoolers_needing_care',
                       'total#_preschool_slots_public/charter/magnet_school_funded_includesoverlaps']


# Impute missing supply rows with column means
def fill_missing_supply_rows(df, supply_cols):
    for col in supply_cols:
        col_mean = df[col].dropna().mean()
        df[col] = df[col].fillna(value=int(col_mean))
    return df

# Impute corrections to demand estimates
def impute_corrected_demand_estimates(df, demand_cols, supply_cols):
    for col in demand_cols:
        partner_cols = [x for x in supply_cols if x.split('_')[-1] == col.split('_')[-1]]
        if len(partner_cols) == 1:
            matching_supply_col = partner_cols[0]
            age_group = col.split('_')[-1]
        else:
            matching_supply_col = supply_cols[0]
            age_group = 'preschool'
        rows_with_estimates = df.loc[(df[col] == 0) | (df[col] == 5) | (df[col].isna()), matching_supply_col]
        mu = rows_with_estimates.mean()
        sigma = rows_with_estimates.std(ddof=0)
        
        # UCONN always used 5 as their guess, so that's our signal for a row to
        # replace with an imputation
        new_values = df.loc[(df[col] == 0) | (df[col] == 5) | (df[col].isna()), col].apply(lambda x: max(5, int(gauss(mu, sigma))))
        df["is_imputed_"+age_group] = 0
        df.loc[(df[col] == 0) | (df[col] == 5) | (df[col].isna()), "is_imputed_" + age_group] = 1
        df.loc[(df[col] == 0) | (df[col] == 5) | (df[col].isna()), col] = new_values
#         df.loc[(df[col] != 0) & (df[col] != 5) & (df[col].notna()), "is_imputed_" + age_group] = 0
    return df, list(rows_with_estimates.index.values)

# Now determine capacity above expectation for each age group
def calculate_expectation_metric(df, demand_cols, supply_cols):
    for col in demand_cols:
        partner_cols = [x for x in supply_cols if x.split('_')[-1] == col.split('_')[-1]]
        if len(partner_cols) == 1:
            matching_supply_col = partner_cols[0]
            age_group = col.split('_')[-1]
        else:
            matching_supply_col = supply_cols[0]
            age_group = 'preschool'
        total_slots = df[matching_supply_col].sum()
        total_need = df[col].sum()
        expected_capacity = total_slots / float(total_need)
        df["expected_slots_by_need_" + str(age_group)] = df[col].apply(lambda x: float(x) * expected_capacity)
        df["delta_slots_"+age_group] = df[matching_supply_col] - df["expected_slots_by_need_"+age_group]
        df["capacity_above_expectation_"+age_group] = df["delta_slots_"+age_group] / df["expected_slots_by_need_"+age_group] * 100.0
    return df

def plot_need_and_capacity(df, n, age_group, town_col, demand_col, supply_col, expectation_col, show_worst=True, points_to_exclude=[]):
    sort_idx = df[expectation_col].argsort().values
    if not show_worst:
        sort_idx = np.flip(sort_idx)
    if len(points_to_exclude) > 0:
        sort_idx = np.array([i for i in list(sort_idx) if not i in points_to_exclude])
    worst_towns = [df[town_col].values[sort_idx[i]] for i in range(len(sort_idx))]
    their_need = [df[demand_col].values[sort_idx[i]] for i in range(len(sort_idx))]
    their_capacity = [df[supply_col].values[sort_idx[i]] for i in range(len(sort_idx))]
    fig, ax = plt.subplots()
    x = np.arange(len(worst_towns[:n]))
    width = 0.35
    rects1 = ax.bar(x - width/2, their_need[:n], width, label="Need")
    rects2 = ax.bar(x + width/2, their_capacity[:n], width, label="Capacity")
    ax.set_xticks(x)
    ax.set_xticklabels(worst_towns[:n])
    plt.xticks(rotation="vertical")
    fig.tight_layout()
    title_start = age_group + ': '
    if show_worst:
        title_start += 'Worst '
    else:
        title_start += 'Best '
    plt.title(title_start + str(n) + ' Towns: Needs and Capacities' + ' (excluding imputated towns)' if len(points_to_exclude) > 0 else '')
    plt.ylabel('Number of Children / Slots')
    plt.show()

def plot_expectation(df, n, age_group, town_col, demand_col, supply_col, expectation_col, show_worst=True, points_to_exclude=[]):
    sort_idx = df[expectation_col].argsort().values
    if not show_worst:
        sort_idx = np.flip(sort_idx)
    if len(points_to_exclude) > 0:
        sort_idx = np.array([i for i in list(sort_idx) if not i in points_to_exclude])
    vals = df[expectation_col].values
    worst_performers = [vals[sort_idx[i]] for i in range(len(sort_idx))]
    worst_towns = [df[town_col].values[sort_idx[i]] for i in range(len(sort_idx))]
    plt.bar(worst_towns[:n], worst_performers[:n])
    title_start = age_group + ': '
    if show_worst:
        title_start += 'Worst '
    else:
        title_start += 'Best '
    plt.title(title_start + str(n) + ' Towns by Capacity Above Expectation' + ' (excluding imputated towns)' if len(points_to_exclude) > 0 else '')
    plt.ylabel('Percent Above Expectation')
    plt.xticks(rotation="vertical")
    plt.show()
    

    df = pd.read_csv(OVERALL_DATA_FILE, dtype="object")[1:]
    df[OVERALL_CONVERT_COLS] = df[OVERALL_CONVERT_COLS].apply(pd.to_numeric, errors="coerce")
    df = fill_missing_supply_rows(df, OVERALL_SUPPLY_COLS)
    df, rows_with_estimates = impute_corrected_demand_estimates(df, OVERALL_DEMAND_COLS, OVERALL_SUPPLY_COLS)
    df = calculate_expectation_metric(df, OVERALL_DEMAND_COLS, OVERALL_SUPPLY_COLS)
#     df.to_csv("overall_supply_demand_by_town_with_cae.csv")

def analyze_overall_data(n, show_worst=True, exclude_imputations=True):
    plot_expectation(df, n, 'infant/toddler', "city", "children_needing_care_demandestimated_infantstoddlers", "available_spaces_for_children_supply_infantstoddlers", "capacity_above_expectation_infantstoddlers", show_worst=show_worst, points_to_exclude=[] if not exclude_imputations else rows_with_estimates)
    plot_need_and_capacity(df, n, 'infant/toddler', "city", "children_needing_care_demandestimated_infantstoddlers", "available_spaces_for_children_supply_infantstoddlers", "capacity_above_expectation_infantstoddlers", show_worst=show_worst, points_to_exclude=[] if not exclude_imputations else rows_with_estimates)
    plot_expectation(df, n, 'preschooler', "city", "children_needing_care_demandestimated_infantstoddlers", "available_spaces_for_children_supply_infantstoddlers", "capacity_above_expectation_preschoolers", show_worst=show_worst, points_to_exclude=[] if not exclude_imputations else rows_with_estimates)
    plot_need_and_capacity(df, n, 'preschooler', "city", "children_needing_care_demandestimated_infantstoddlers", "available_spaces_for_children_supply_infantstoddlers", "capacity_above_expectation_preschoolers", show_worst=show_worst, points_to_exclude=[] if not exclude_imputations else rows_with_estimates)
    
def analyze_school_data(n, show_worst=True, exclude_imputations=True):
    df = pd.read_csv(SCHOOL_DATA_FILE, dtype="object")[1:]
    df[SCHOOL_CONVERT_COLS] = df[SCHOOL_CONVERT_COLS].apply(pd.to_numeric, errors="coerce")
    df = fill_missing_supply_rows(df, SCHOOL_SUPPLY_COLS)
    df, rows_with_estimates = impute_corrected_demand_estimates(df, SCHOOL_DEMAND_COLS, SCHOOL_SUPPLY_COLS)
#     df = calculate_expectation_metric(df, SCHOOL_DEMAND_COLS, SCHOOL_SUPPLY_COLS)
    df.to_csv("preschool_supply_demand_by_town_with_cae.csv")
    plot_expectation(df, n, 'preschooler', "city", SCHOOL_DEMAND_COLS[0], SCHOOL_SUPPLY_COLS[0], "capacity_above_expectation_Preschool", show_worst=show_worst, points_to_exclude=[] if not exclude_imputations else rows_with_estimates)
    plot_need_and_capacity(df, n, 'preschooler', "city", SCHOOL_DEMAND_COLS[0], SCHOOL_SUPPLY_COLS[0], "capacity_above_expectation_Preschool", show_worst=show_worst, points_to_exclude=[] if not exclude_imputations else rows_with_estimates)


#Fix random seed for replicability
seed(123456789)

analyze_overall_data(40, show_worst=True, exclude_imputations=True)
# analyze_school_data(40, show_worst=True, exclude_imputations=True)


