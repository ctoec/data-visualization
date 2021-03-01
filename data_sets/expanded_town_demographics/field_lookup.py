import censusdata as cd
import pandas as pd
from numpy import nan

TOWN_FILE = "town_data.csv"
SINGLE_FIELD_FILE = "single_field_lookups.txt"
COMBINATIONN_FIELD_FILE = "combination_field_lookups.txt"
STATE_CODE = '09'
OUT_FILE = "town_demographic_data.csv"

'''
Performs string padding on a given number so that the right number 
of '0's are prepended to make census geo lookup work. 
'''
def pad_int(x):
    str_rep = "0"
    if x < 10:
        str_rep += "0"
    str_rep += str(x)
    return str_rep


'''
Reads a given file to parse variable fields which involve no calculation
and are direct lookups of variables in a particular census table.
'''
def parse_single_field_file(filename):
    mapping = {}
    with open(filename, 'r') as fp:
        for line in fp:
            if line.strip() != "" and line[0] != '#':
                parts = line.strip().split(":")
                mapping[parts[1].strip()] = parts[0].strip()
    return mapping


'''
Reads a given file to parse variable fields which are calculated by 
combining various fields in a particular census table to enable more
sophisticated calculations. The format to parse such a table is given
in the file. The function will extract individual fields as well as 
perform any specified aggregations and keep only those variables
specifically desired.
'''
def parse_combination_field_file(filename):
    root_names = []
    tables = []
    max_nums = []
    solo_fields = []
    solo_names = []
    combination_fields = []
    combination_names = []
    
    with open(filename, 'r') as fp:
        for line in fp:
            # Ignore lines providing the example
            if line.strip() != "" and line[0] != '#':
                parts = line.strip().split(";")
                root_names.append(parts[0].strip())
                tables.append(parts[1].strip())
                max_nums.append(int(parts[2].strip()))
                
                # Determine whether we're parsing any single field vars
                sfs = parts[3].strip()
                if sfs == "":
                    solo_fields.append([])
                    solo_names.append([])
                else:
                    sfs = [int(x.strip()) for x in sfs.split(",")]
                    solo_fields.append(sfs)
                    sfns = [x.strip() for x in parts[4].strip().split(",")]
                    solo_names.append(sfns)
                
                # Same thing for aggregation based variables 
                cfs = parts[5].strip()
                if cfs == "":
                    combination_fields.append([])
                    combination_names.append([])
                else:
                    groups = []
                    for cluster in cfs.split('+'):
                        cleaned_cluster = [int(x.strip()) for x in cluster.strip().split(',')]
                        groups.append(tuple(cleaned_cluster))
                    combination_fields.append(groups)
                    names = [x.strip() for x in parts[6].strip().split(',')]
                    combination_names.append(names)
                    
    return root_names, tables, max_nums, solo_fields, solo_names, combination_fields, combination_names
                

'''
For a given censusgeo object, look up any direct/single fields that we
can pull straight from a table. Put these into a dataframe indexed by
the censusgeo object.
'''
def handle_single_fields(geo, mapping):
    fields = list(mapping.keys())
    dat = cd.download('acs5', 2019, geo, fields)
    dat.rename(columns=mapping, inplace=True)
    return dat


'''
Block download all of the tables and variable fields that will later be
parsed by the combination aggregator. Specifically only retrieve those
fields that impact the final dataset.
@param geo: an already retrieved censusgeo object
@param tables: list of uniquely identified table values, such as B10129_001E
  and B20002_004E
@param max_field_nums: list of ints, where int i is the largest unique ID the
  function will potentially retrieve for table[i] (used in a range)
@param solo_fields: see handle_combination_fields below
@param combination_fields: see handle_combination_fields below  
'''
def download_combination_fields(geo, tables, max_field_nums, solo_fields, combination_fields):
    field_list = []
    for t in range(len(tables)):
        for i in range(1, max_field_nums[t]+1):
            # Only fetch the fields that are going to be used
            need_field = False
            if i in solo_fields[t]:
                need_field = True
            if not need_field:
                for cf in combination_fields[t]:
                    if i in cf:
                        need_field = True
            if need_field:
                str_rep = pad_int(i)
                field_list.append(tables[t] + "_" + str_rep + "E")
    
    # Block download to minimize API calls
    dat = cd.download('acs5', 2019, geo, field_list)
    return dat
    

'''
Perform variable renaming and aggregation of multiple field into desired
calculated columns. Requires combination table data to already be 
downloaded.
@param dat: the data frame created from the single field result that we'll
  add results to
@param tables: list of strings of root table names (i.e. B13001, not B13001_001E)
@param solo_fields: list of list of strings, where list i holds the fields for
  table i; list i will have the unique ID numbers that will be concated to the
  root table code to correctly identify variables prior to renaming
@param solo_names: list of list of strings, where list i holds the names
  that should bijectively replace the codes in solo_fields[i]
@param combination_fields: list of list of tuples, where list i contains tuples 
  t_1, ..., 1_n of integers j_1, ..., j_m. Each tuple of integers represents a
  collection of fields that will be aggregated into a single column in the df.
@param root_names: list of str, where name i will be prepended to all calculated
  variables in solo_fields[i] and combination_fields[i] to make the table clear
@param combination_names: list of list of str, where list i holds the names that
  will replace field codes in combination_fields[i] (as with solo names/fields)
'''
def handle_combination_fields(dat, tables, solo_fields, solo_names, combination_fields, root_names, combination_names):
    for t in range(len(tables)):
        solo_strings = []
        for i in range(len(solo_fields[t])):
            
            # Accumulate all table identifiers of fields we indexed on their ownn
            str_rep = pad_int(solo_fields[t][i])
            str_rep = tables[t] + "_" + str_rep + "E"
            solo_strings.append(str_rep)
        
        # Bulk rename all these solo fields
        col_map = {}
        for i in range(len(solo_strings)):
            col_map[solo_strings[i]] = root_names[t] + ' - ' + solo_names[t][i]
        dat.rename(columns=col_map, inplace=True)
        
        # Create single columns for each aggregation / combination field,
        # and drop the individual constituent columns
        for i in range(len(combination_fields[t])):
            total = 0
            affected_fields = []
            for field in combination_fields[t][i]:
                str_rep = pad_int(field)
                str_rep = tables[t] + "_" + str_rep + "E" 
                affected_fields.append(str_rep)
                total += dat[str_rep]
            dat[root_names[t] + ' - ' + combination_names[t][i]] = total
            dat.drop(columns=affected_fields, inplace=True)
        
    return dat


'''
Simple util to drop all collected columns for which every value
is null or nan.
'''
def drop_null_cols(df):
    cols_to_drop = []
    for c in df.columns:
        if df[c].isnull().all():
            cols_to_drop.append(c)
    df = df.drop(columns=cols_to_drop)
    return df
    

# Let's pull some data
geo = cd.censusgeo([('state', STATE_CODE), ('county', '*'), ('county subdivision', '*')])
single_field_mapping = parse_single_field_file(SINGLE_FIELD_FILE)
df_single = handle_single_fields(geo, single_field_mapping)
root_names, tables, max_nums, solo_fields, solo_names, combination_fields, combination_names = parse_combination_field_file(COMBINATIONN_FIELD_FILE)
df_combination = download_combination_fields(geo, tables, max_nums, solo_fields, combination_fields)
df_combination = handle_combination_fields(df_combination, tables, solo_fields, solo_names, combination_fields, root_names, combination_names)
df = pd.concat([df_single, df_combination], axis=1)
df[df < 0] = nan
df = drop_null_cols(df)
  
# Get rid of the kruft in each town's name that the censusgeo object comes with
# Makes for much cleaner df writing
df['town'] = [str(x) for x in df.index]
df = df.loc[df['town'].apply(lambda x: True if 'town' in x else False), :]
df['town'] = df['town'].apply(lambda x: x.split(',')[0].strip())
df['town'] = df['town'].apply(lambda x: x.replace(' town', ''))
df.to_csv(OUT_FILE, index=False)




