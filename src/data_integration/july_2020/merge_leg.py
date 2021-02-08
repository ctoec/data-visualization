import pandas as pd
from constants import LEG_DIST_FILE
from constants import STUDENT_FILE
student_df = pd.read_csv(STUDENT_FILE)
leg_df = pd.read_csv(LEG_DIST_FILE)

merged_df = student_df.merge(leg_df, how='left', on='Facility Code')
merged_df.to_csv('/Users/kylemagida/code/skylight/data-visualization/src/data_integration/july_2020/data/student_leg.csv')
