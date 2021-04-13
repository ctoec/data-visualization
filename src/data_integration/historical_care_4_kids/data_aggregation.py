import pandas as pd
import os
import re

'''
A note on turning lists of lists into dataframes: there is almost
certainly a pandas native way of transforming the data we get from
the individual enrollment report sheets into the structure we want.
That way *should* use the functions pivot, stack, unstack, and melt.
However, because we these files have inconsistent multi-index and
multi-level column formatting, none of these functions works as 
expected. Columns where the 0-level part is associated only with
a single 1-level part get massacred because they're not actually 
multi-index but they get treated as such. And, while it's possible
to correct that (theoretically...), because this is a) a one-off
script, and b) dealing with individual files which are only 170 
lines long, there's no need to over-optimize because the efficiency
gain is minimal. So, lists of lists is what's happening.
'''

# Where all the historical reports are, named exactly as they
# were downloaded
DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/enrollment_reports/"


# These are the columns we'll keep in our database-like CSV
SCHEMA_COLS = ['year', 'month', 'town', 'age', 'regulation', 'setting', 'enrollments']


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
    

def get_age_group(sheet):
    '''
    Turns a given sheet number into the associated age group, since sheets
    always present age groups in the same order.
    '''
    age_group = ''
    if sheet == 1:
        age_group = 'Infant/Toddler'
    elif sheet == 2:
        age_group = 'Preschool'
    elif sheet == 3:
        age_group = 'School Aged'
    return age_group


def correct_towns(town):
    '''
    Correct a few naming artifacts in town conventions that change
    sporadically throughout the data.
    '''
    if 'Terryville' in town:
        return 'Plymouth'
    if 'Pomfret' in town:
        return 'Pomfret'
    if 'Windham' in town:
        return 'Windham'
    return town
    
    
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
    rows = []
    
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

        # Some columns get read-in as duplicates because of the multi-
        # level index and are entirely NaN--they all end with ".X"        
        xls.drop(columns=[c for c in xls.columns if re.search('\.\d', c[1]) != None ], inplace=True)
        
        ag = get_age_group(sheet)
        for _, row in xls.iterrows():
            
            # Standardize the case for the town and ONLY count
            # actual towns (we can do totals on our own)
            town = row[('Service Settings', 'Municipality')].title()
            if 'Total' not in town:
                town = correct_towns(town)
                for c in xls.columns:
                    if c[1] != 'Municipality':
                        reg = c[0]
                        setting = c[1].replace('\n', ' ')
                        
                        # Enrollment totals are actually unique values
                        # because they don't count double-entered kids
                        # They don't have a regulation though
                        if 'Total' in setting:
                            setting = 'Total'
                            reg = 'Total'
                        enrollments = row[c]
                        rows.append([year, month, town, ag, reg, setting, enrollments])
           
    df = pd.DataFrame(rows, columns=SCHEMA_COLS)
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
    rows = []

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
        
        # Same thing with duplicated multi-indexes as above
        xls.drop(columns=[c for c in xls.columns if re.search('\.\d', c[1]) != None ], inplace=True)
        
        ag = get_age_group(sheet)
        for _, row in xls.iterrows():
            
            # Some of the columns have dashes instead of numbers, which
            # prevents any kind of stable type reading when opening the sheet
            # Just use try/catch to ignore casing for dashes, we'll handle
            # these later
            try:
                town = row[('Service Type', 'Town (Child Residence)')].title()
                
                # As above, we'll do our own totals; also, footnotes aren't towns
                if 'Total' not in town and 'Note:' not in town:
                    town = correct_towns(town)
                    for c in xls.columns:
                        if 'Town' not in c[1]:
                            reg = c[0]
                            setting = c[1].replace('\n', ' ')
                            if 'Total' in setting:
                                setting = 'Total'
                                reg = 'Total'
                            
                            # Clear away asterisk notes that reference footnotes
                            # Numerically, these shouldn't drastically affect our
                            # results because a) the magnitude is either < 5, or b)
                            # it's > 5 but no one knows which way
                            enrollments = str(row[c]).replace('*', '').strip()
                            if enrollments == '':
                                enrollments = 0
                            rows.append([year, month, town, ag, reg, setting, enrollments])

            except:
                pass

    df = pd.DataFrame(rows, columns=SCHEMA_COLS)
    return df      


def get_historical_c4k(final_filename):
    
    # If it's the first file we process, just use that as the base DF
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
            df = df.append(file_df)
            
    # Correct any dashes or nan values
    df.replace('-', 0, inplace=True)
    df.fillna(0, inplace=True)
    
    df.to_csv(final_filename, index=False)



