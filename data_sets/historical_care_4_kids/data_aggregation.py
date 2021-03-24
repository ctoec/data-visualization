import pandas as pd
import os
import re

# Where all the historical reports are, named exactly as they
# were downloaded
DATA_DIR = "enrollment_reports/"

# File to write the result artifact aggregated DF to
OUT_FILE = "all_c4k_data.csv"


def get_month(str):
    '''
    Converts a two-digit string representation of a month into its
    three-letter abbrevation.    
    '''
    
    if str == '01':
        return 'Jan'
    if str == '02':
        return 'Feb'
    if str == '03':
        return 'Mar'
    if str == '04':
        return 'Apr'
    if str == '05':
        return 'May'
    if str == '06':
        return 'Jun'
    if str == '07':
        return 'Jul'
    if str == '08':
        return 'Aug'
    if str == '09':
        return 'Sep'
    if str == '10':
        return 'Oct'
    if str == '11':
        return 'Nov'
    if str == '12':
        return 'Dec'
    
    
def join_to_accumulator(df, xls, sheet):
    '''
    Combines the information generated from a single sub-sheet of an
    excel file into an existing data frame to accumulate the results
    of the enrollment report. Also trims footnotes and sporadic total
    rows that sometimes randomly occur
    '''
    
    # Some sheets have totals rows at the bottom, or footnotes--cut
    # 'em out
    if len(xls) > 170:
        rows_over = len(xls) - 170;
        xls = xls.iloc[: -1 * (rows_over), :]
        
    # Join the information to the accumulator data frame
    if sheet == 1:
        df = xls
    else:
        df = df.merge(xls, on='Town')
    return df
    
    
def flatten_hierarchical_columns(xls, sheet, month, year):
    '''
    Squash the multi-level hierarchical index into a series of flattened
    columns all at a single level. We create a unique identifier for each
    column by combining the month, year, age group, and stat category
    of columns to insure no information is overwritten by subsequent
    sheets. 
    '''
    
    # Rename doesn't play well with hierarchical index--easiest
    # solution is to just overwrite them with flattened names
    new_col_names = []
    totals_seen = 0
    for c in xls.columns:
        joint_name = ' '.join(c).replace('\n', ' ')
        
        # Some of the sheets parse with duplicate multi-index
        # total columns, so only keep the first
        if 'Total' in joint_name:
            joint_name = 'Total'
            totals_seen += 1
        
        # Prepend date information and age group
        age_group = ''
        if sheet == 1:
            age_group = 'Infant/Toddler'
        elif sheet == 2:
            age_group = 'Preschool'
        elif sheet == 3:
            age_group = 'School Aged'
        joint_name = month + ' ' + year + ' ' + age_group + ' ' + joint_name
        
        # Correct the town column to a standardized name
        if 'Municipality' in joint_name or 'Town' in joint_name:
            joint_name = 'Town'
        new_col_names.append(joint_name)
        
    xls.columns = new_col_names
    if totals_seen > 1:
        xls = xls.iloc[:, : -1 * (totals_seen - 1)]
    return xls


def parse_pre_18_report(filename):
    '''
    Handles parsing of an enrollment report file that was published 
    before 2018. These files have the month and year of the data in
    their name, and they have header information anywhere between
    rows 1 and 4 of each sheet. There are occasional blank rows
    thrown into these files seemingly at random, and we can use the
    unnamed convention of multi-index parsing to correct for this.
    '''
    
    print('Parsing', filename)
    df = pd.DataFrame()
    
    # Get month and year to append into column names
    parts = filename.split('-')
    month = parts[0].strip()[:3]
    year = parts[1].strip()

    # Process sheets one at a time because bad standardization    
    for sheet in range(1,4):
        
        # Some sheets in some files randomly have the first row as a blank
        # Need to check for this so we don't parse the wrong multi-header,
        # because that's *super* annoying
        skiprows = 1
        first_row = pd.read_excel(DATA_DIR + filename, sheet_name=sheet, nrows=1)
        if ('Unnamed' in first_row.columns[0]):
            skiprows += 1
        xls = pd.read_excel(DATA_DIR + filename, header=[0,1], sheet_name=sheet, skiprows=skiprows)   
        
        # Flatten columns and accumulate results
        xls = flatten_hierarchical_columns(xls, sheet, month, year)
        df = join_to_accumulator(df, xls, sheet)
    
    # Standardize case of towns
    df['Town'] = df['Town'].apply(lambda s: s.title())
    return df


def parse_post_18_report(filename, month, year):
    '''
    Handles parsing of an enrollment report file that was published
    after 2018. These files cannot be trusted to have meaningful date
    information in the filename, and so it must be mined from the 
    summary sheet (sheet 0) of the excel file (handled outside this
    function). These files can have header information anywhere between
    rows 5 and 13, so we have to use some looping and name checking
    to force the file to behave predictably. Maybe not the cleanest,
    but it works reliably and finds the right headers. 
    '''
    
    print('Parsing', filename)
    df = pd.DataFrame()
    
    # Process sheets one at a time because bad standardization    
    for sheet in range(1,4):
        skiprows = 5
        have_headers = False
        
        # Maybe not the best way to force sequential checks of information,
        # but these files are terrible and it's not worth more effort when
        # this works
        while not have_headers:
            first_row = pd.read_excel(DATA_DIR + filename, sheet_name=sheet, nrows=1, skiprows=skiprows)
            if 'Age Category' in first_row.columns[0]:
                skiprows += 1
            elif 'Service Type' in first_row.columns[0]:
                have_headers = True
            else:
                skiprows += 3
                
        xls = pd.read_excel(DATA_DIR + filename, header=[0,1], sheet_name=sheet, skiprows=skiprows)
        xls = flatten_hierarchical_columns(xls, sheet, month, year)
        df = join_to_accumulator(df, xls, sheet)
    
    # Standardize case of towns
    df['Town'] = df['Town'].apply(lambda s: s.title())
    return df
      

# If it's the first file we process, just use that as the base DF
df = pd.DataFrame()
is_first = True

for filename in os.listdir(DATA_DIR):
    if '2016' in filename or '2017' in filename:
        file_df = parse_pre_18_report(filename)
    else:
        first_row = pd.read_excel(DATA_DIR + filename, sheet_name=0, header=None, nrows=1, skiprows=1)
        
        # Once again, some files randomly add or subtract multiple rows
        # of information (such as Report IDs or Org IDs)--ignore these
        # and search for the reporting 'period'
        if not 'period' in str(first_row.loc[0,0]).lower():
            first_row = pd.read_excel(DATA_DIR + filename, sheet_name=0, header=None, nrows=1, skiprows=0)
            
        # Get the date from our forced find
        working_date = re.search('\d+\/\d+\/\d+', first_row.loc[0,0])[0]
        working_date = working_date.split("/")
        month = get_month(working_date[0].strip())
        year = working_date[-1].strip()
        
        file_df = parse_post_18_report(filename, month, year)
        
    # Accumulate information the right way
    if is_first:
        is_first = False
        df = file_df
    else:
        df = df.merge(file_df, on='Town')
        
# Two corrections to make:
# 1. replace all dashes with 0's (don't know why some reports do this)
# 2. delete all multi-index column clones of other columns (some tuples get
#    processed with more 'header' columns than they should and have all NaNs)
df.drop(columns=[c for c in df.columns if re.search('\.\d', c) != None ], inplace=True)
df.replace('-', 0, inplace=True)

df.to_csv(OUT_FILE, index=False)



