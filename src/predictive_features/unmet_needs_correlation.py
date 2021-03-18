import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.svm import SVC
from sklearn.feature_selection import RFE
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score
import copy

'''
Data files to read data from to create the training and response
matrices:
- Supply file: file to pull childcare supply from
- Supply cols: the columns in supply file to aggregate for the supply
  estimate
- Demand file: file to pull demand from
- Demand col: column in demand file to use as the demand estimate
- Demo file: file with demographic information by town
'''
SUPPLY_DATA_FILE = "../data_integration/unmet_needs/overall_supply_and_estimated_demand_for_child_care_by_age_and_by_town.csv"
SUPPLY_COLS = ['Available_Spaces_for_Children_Supply_InfantsToddlers',
                'Available_Spaces_for_Children_Supply_Preschoolers']
DEMAND_DATA_FILE = "../data_integration/demand_estimation/final_demand_by_town.csv"
DEMAND_COL = "estimated_demand_by_care_availability"

DEMO_FILE = "../data_integration/census_data/town_demographic_data_all_fields.csv"

'''
Selection of two response variables to have the model train on.
'''
# RESPONSE_VARIABLE = 'eligibility_differential'
RESPONSE_VARIABLE = 'need_differential'


'''
Pulls the appropriate columns from the supply and demand files 
and creates data matrices out of them. Calculates two different
'gaps' in service provision: an eligibility gap (between available
slots and all children eligible for enrollment in those slots), 
and a 'demand' gap (between slots and the estimated number of
those slots that constituents want to use).
'''
def generate_supply_demand_dataset(supply_fp, demand_fp, supply_cols, demand_col):
    supply_df = pd.read_csv(supply_fp)
    demand_df = pd.read_csv(demand_fp)
    
    # Only need to keep City so we can join to the demographic cols
    keep_cols = ['City']
    keep_cols.extend(supply_cols)
    supply_df.drop(columns=[c for c in supply_df.columns if not c in keep_cols], inplace=True)
    supply_df.rename(columns={'City': 'town'}, inplace=True)
    supply_df[supply_cols] = supply_df[supply_cols].apply(pd.to_numeric, errors="coerce")
    
    # Aggregate childcare supply between infants/toddlers and preschoolers
    supply_df['childcare_supply'] = supply_df[supply_cols[0]] + supply_df[supply_cols[1]]
    mean_supply = supply_df['childcare_supply'].dropna().mean()
    supply_df['childcare_supply'] = supply_df['childcare_supply'].fillna(value=mean_supply)
    df = supply_df.merge(demand_df, on='town')
    supply_Y = df['childcare_supply']
    df.drop(columns=supply_cols, inplace=True)
    
    # Calculate two kinds of gaps so that we can test different responses
    df['need_differential'] = df['childcare_supply'] - df[demand_col]
    df['eligibility_differential'] = df['childcare_supply'] - df['children_eligible_for_care_services']
    total_slots = df['childcare_supply'].sum()
    total_need = df[demand_col].sum()
    
    # Also calculate CAE, if it's desired
    expected_capacity = total_slots / float(total_need)
    df["expected_slots_by_need"] = df[demand_col].apply(lambda x: float(x) * expected_capacity)
    df["delta_slots"] = df['childcare_supply'] - df["expected_slots_by_need"]
    df["capacity_above_expectation"] = df["delta_slots"] / df["expected_slots_by_need"] * 100.0
    df.drop(columns=['expected_slots_by_need', 'delta_slots'], inplace=True)
    return df, supply_Y


'''
Calculate the permutation importance of a variable in a given prediction
model. The permutation importance is a useful statistic for measuring
the impact of a given variable on change in overall model performance.
The model is trained using the field, and then the values of the field
are randomized, wiping out the information content of the field while
still forcing the model to rely on it (which is better than just re-
training a model because the coefficients would compensate). Also 
calculates precision and recall score changes for each variable tested.
'''
def perm_import_no_cv(xv, yv, columns, estim, iters=100):
    
    # Structures to hold accumulations, and baseline scores
    # to find changes
    scores = {}
    ps = {}
    rs = {}
    for c in columns:
        scores[c] = []
        ps[c] = []
        rs[c] = []
    baseline = estim.score(xv, yv)
    base_preds = estim.predict(xv)
    p = precision_score(yv, base_preds)
    r = recall_score(yv, base_preds)

    # For each field: copy the training data, scramble the
    # values of that field across samples, and evaluate 
    # change in prediction quality
    for c in columns:
        x1 = copy.deepcopy(xv)
        for _ in range(iters):
            temp = x1[c].tolist()
            np.random.shuffle(temp)
            x1[c] = temp
            scores[c].append(estim.score(x1, yv))
            preds = estim.predict(x1)
            ps[c].append(precision_score(yv, preds))
            rs[c].append(recall_score(yv, preds))
            
        # Save the average across multiple runs for stability
        scores[c] = baseline - np.mean(np.asarray(scores[c]))
        ps[c] = p - np.mean(np.asarray(ps[c]))
        rs[c] = r - np.mean(np.asarray(rs[c]))
    
    return baseline, scores, ps, rs
        

# Read supply and demand estimates
np.random.seed(1208)
estimate_df, supply_Y = generate_supply_demand_dataset(SUPPLY_DATA_FILE, DEMAND_DATA_FILE, SUPPLY_COLS, DEMAND_COL)
estimate_df.drop(columns=[c for c in estimate_df.columns if not c in ['town', RESPONSE_VARIABLE]], inplace=True)

# Read demographics file
demos = pd.read_csv(DEMO_FILE)
df = demos.merge(estimate_df, on='town')
df.drop(columns=['town'], inplace=True)

# Re-parse the categorical variable to be numeric
min_house_year = df.loc[df['median year housing unit was built'] > 0, 'median year housing unit was built'].min()
df['median year housing unit was built'] = df['median year housing unit was built'].apply(lambda x: x - min_house_year if x >= min_house_year else 0)
df = df.rename(columns={'median year housing unit was built': 'median year of home construction after ' + str(min_house_year)})

# Reduce number of features, being smart about it
df['mean inter quintile income gap'] = df['income quintile means - fourth'] - df['income quintile means - second']
quintile_cols = ['income quintile means - lowest', 'income quintile means - second', 'income quintile means - third', 'income quintile means - fourth', 'income quintile means - highest', 'income quintile means - top 5%']
df.drop(columns=quintile_cols, inplace=True)

# Household income--duplicates and is codependent with family income
df.drop(columns=[c for c in df.columns if 'household income' in str(c)], inplace=True)

# Extraneous earnings columns--don't have enough mutual information
# with response variables to be worth keeping
df.drop(columns=['male median earnings past 12 months', 'female median earnings past 12 months', 'male median income past 12 months', 'female median income past 12 months'], inplace=True)

# Ratio of income to poverty level--need to drop because we use it
# in estimating both response variables
df.drop(columns=[c for c in df.columns if 'ratio of income to poverty level' in str(c)], inplace=True)

# Supplemental income sources--model isn't sensitive enough to 
# disambiguate individual effects, so lump everything together as
# 'supplemental' income
df.drop(columns=['received public assistance income'], inplace=True)
supplemental_income_cols = ['receiving social security income', 'receiving supplemental security income', 'received cash public assistance or food stamps/snap', 'received retirement income']
df['received income from supplemental source'] = 0
for c in supplemental_income_cols:
    df['received income from supplemental source'] += df[c]
df.drop(columns=supplemental_income_cols, inplace=True)

# All income columns in general--useful if we want to assume
# they're controlled for estimation purposes (assumption may not
# necessarily hold, but it's a good way to force more interesting
# fields to the surface)
# df.drop(columns=[c for c in df.columns if 'income' in str(c)], inplace=True)

# Rent payment columns
# df.drop(columns=[c for c in df.columns if 'rent paid for non-owned housing units' in str(c)], inplace=True)

# Housing cost columns
# df.drop(columns=[c for c in df.columns if 'monthly housing cost' in str(c)], inplace=True)

# Home value columns--bundle 'expensive' houses together because
# they don't really need to be treated as separate features, it just
# confounds the model 
df['home value of owned/mortgaged housing units - > 300k'] = 0
dollar_values = ['300k - 400k', '400k - 500k', '500k - 750k', '750k - 1m', '1m+']
dollar_values = ['home value of owned/mortgaged housing units - ' + dv for dv in dollar_values]
for dollar_v in dollar_values:
    df['home value of owned/mortgaged housing units - > 300k'] += df[dollar_v]
df.drop(columns=[c for c in df.columns if c in dollar_values], inplace=True)

# Heating fuel columns--interestingly, fuel type is actually a really
# informative proxy of family well-being due to "purity"/"cleanliness"
# of the fuel, moreso than cost (no fuel << wood << coal < oil, etc.) 
# df.drop(columns=[c for c in df.columns if 'heating fuel' in str(c)], inplace=True)

# Race columns--not enough training data to disambiguate the effects of different
# racial groups; clearer results if separate race along white/non-white
df['non-white population'] = 0
race_cols = ['black or african american', 'american indian and alaska native', 'asian', 'native hawaiian and other pacific islander', 'other race']
for c in race_cols:
    df['non-white population'] += df[c]
df.drop(columns=race_cols, inplace=True)

# Bedroom and vehicle columns
# df.drop(columns=[c for c in df.columns if 'bedrooms' in str(c)], inplace=True)
# df.drop(columns=[c for c in df.columns if 'vehicles available' in str(c)], inplace=True)

# Household type of homes with children: drop for eligibility training
# df.drop(columns=[c for c in df.columns if 'household type of homes with children' in str(c)], inplace=True)

# Columns with low information given the response ask
cols_to_drop=['nativity and citizenship - foreign-born non-citizen', \
              'school enrollment - grad school', \
              'primary spoken language at home - english']
df.drop(columns=cols_to_drop, inplace=True)

# Z-score standardize attributes, handle null entries
response_mean = 0
response_std = 0
for c in df.columns:
    non_zeros = df.loc[df[c].notna(), c]
    mu = np.mean(non_zeros)
    std = np.std(non_zeros)
    df.loc[df[c].isna(), c] = mu
    df[c] = df[c].apply(lambda x: (x - mu) / std)
    if c == RESPONSE_VARIABLE:
        response_mean = mu
        response_std = std
        
# Split data into features and response
Y = df[RESPONSE_VARIABLE]
Y_c = df.loc[:, RESPONSE_VARIABLE].apply(lambda x: 1 if x <= (-1 * response_mean / response_std) else 0)
X = df.drop(columns=[RESPONSE_VARIABLE])

# Run a linear regression on the supply-side of the problem
# Potentially interesting ground to see what features are associated
# with positive/negative public investment in childcare services
supply_mean = supply_Y.mean()
supply_std = supply_Y.std()
supply_Y = supply_Y.apply(lambda x: (x - supply_mean) / supply_std)
reg = Lasso(alpha=0.001, fit_intercept=False, max_iter=5000)
reg.fit(X, supply_Y)
print('Lasso correlation', reg.score(X, supply_Y))
coef_scores = {}
col_list = list(X.columns)
for i in range(len(col_list)):
    coef_scores[col_list[i]] = reg.coef_[i]
supply_side_vars = list(coef_scores.items())
supply_side_vars.sort(key=lambda x: abs(x[1]), reverse=True)
supply_side_vars = [t for t in supply_side_vars if abs(t[1]) != 0]
print('Lasso features selected', len(supply_side_vars))
for t in supply_side_vars:
    print(t[0], "coef", t[1])
print("")

# Get a train-test split for some ML analysis
print('Number of SVM features: ' + str(len(list(X.columns))))
X_t, X_v, Y_t, Y_v = train_test_split(X, Y, test_size=0.3)
X_t2, X_v2, Y_t2, Y_v2 = train_test_split(X, Y_c, test_size=0.3, stratify=Y_c)

# Do a little hyper parameter search on an SVM
cv_scores = []
cs = np.asarray([0.0001, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 25.0, 50.0, 100.0])
for c in cs:
    svc = SVC(C=c, kernel='linear', gamma='scale')
    svc.fit(X_t2, Y_t2)
    cv_scores.append(svc.score(X_v2, Y_v2))
max_c_idx = np.argmax(cv_scores)
print('Best C = ' + str(cs[max_c_idx]), ' which scored ' + str(cv_scores[max_c_idx]))

# Use recursive feature elimination to select the optimal number
# of features to model--we explicitly don't use the CV verison of
# RFE because we don't have enough training data to make cross-
# validating meaningful (we're prone to batches of outlier 
# accuracies)
rfe_scores = []
ns = range(1, len(list(X.columns)) + 1)
params = []
estimators = []
rfes = []
for num_features in ns:
    estim = SVC(C=cs[max_c_idx], kernel='linear', gamma='scale')
    rfe = RFE(estim, n_features_to_select=num_features, step=1)
    rfe.fit(X_t2, Y_t2)
    rfe_scores.append(rfe.score(X_v2, Y_v2))
    feature_idx = np.argwhere(rfe.ranking_ == 1)
    params.append(X.columns[feature_idx])
    estimators.append(rfe.estimator_)
    rfes.append(rfe)
max_idx = np.argmax(rfe_scores)
print("Best num features = " + str(ns[max_idx]) + ", which scored " + str(rfe_scores[max_idx]))
print("Optimal features were: " + str(list(params[max_idx])))

# Format the training data to use the RFE estimated optimal features.
# Check model performance with these estimates, and collect statistics
# describing feature importance with this model.
good_cols = list(params[max_idx])
X_rfe = X_v2.drop(columns=[c for c in X_v2.columns if not c in good_cols])
baseline, scores, ps, rs = perm_import_no_cv(X_rfe, Y_v2, list(params[max_idx]), estimators[max_idx], iters=250)
pairs = [(c, scores[c]) for c in scores]
pairs.sort(key=lambda x: x[1], reverse=True)
for p in pairs:
    print(p, 'precision', ps[p[0]], 'recall', rs[p[0]])

# Finally, write our results into two files for visualization
out_supply_df = pd.DataFrame()
out_supply_df['feature'] = [p[0] for p in supply_side_vars]
out_supply_df['coefficient magnitude'] = [p[1] for p in supply_side_vars]
out_supply_df.to_csv('supply_side_features.csv', index=False)
need_gap_df = pd.DataFrame()
need_gap_df['feature'] = [p[0] for p in pairs]
need_gap_df['mean accuracy change'] = [p[1] for p in pairs]
need_gap_df['mean precision change'] = [ps[p[0]] for p in pairs]
need_gap_df['mean recall change'] = [rs[p[0]] for p in pairs]
need_gap_df.to_csv('need_gap_predictive_features.csv', index=False)
 

