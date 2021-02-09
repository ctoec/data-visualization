import pandas as pd
from constants import LEG_DIST_FILE
from constants import STUDENT_FILE, SITE_FILE
# from build_legislative_lookup import create_latlong_unique
from build_tables import standardize_facility_string
student_df = pd.read_csv(STUDENT_FILE)
leg_df = pd.read_csv(LEG_DIST_FILE)


# complete_df = pd.read_csv('/Users/kylemagida/code/skylight/data-visualization/src/data_integration/july_2020/data/complete.csv', low_memory=False)
# complete_cols_to_keep = ['LatLongUnique', 'senator_district', 'senator_full_name',
#        'senator_first_name', 'senator_last_name', 'senator_party',
#        'representative_district', 'representative_full_name',
#        'representative_first_name', 'representative_last_name',
#        'representative_party','ECIS/PSIS Facility Code', 'Site']
# complete_df = complete_df[complete_cols_to_keep]
# complete_df = complete_df.groupby(complete_cols_to_keep[:-1])['Site'].count().reset_index()
# complete_df.drop(['Site'], axis=1, inplace=True)
# complete_df.rename(columns={'ECIS/PSIS Facility Code': 'Facility Code'}, inplace=True)
# complete_df['Facility Code'] = standardize_facility_string(complete_df['Facility Code'])
# site_df = pd.read_csv(SITE_FILE)
# merged_df = student_df.merge(complete_df, how='left', on='Facility Code')
# merged_df = student_df.merge(site_df, how='left', on='Facility Code')
# merged_df['lat_long_unique'] = create_latlong_unique(merged_df['Latitude'], merged_df['Longitude'])
# merged_df = merged_df.merge(complete_df, how='left', on='Facility Code')
merged_df = student_df.merge(leg_df, how='left', on='Facility Code')
merged_df.to_csv('/Users/kylemagida/code/skylight/data-visualization/src/data_integration/july_2020/data/student_leg.csv', index=False)

