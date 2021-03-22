import censusdata as cd
from numpy import nan

SINGLE_FIELD_FILE = "single_field_lookups.txt"
COMBINATION_FIELD_FILE = "combination_field_lookups.txt"
STATE_CODE = '09'
CENSUS_FIELD_LIMIT = 50
CENSUS_NAME_FIELD = 'NAME'
OUT_FILE = "town_demographic_data_all_fields.csv"



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
                
                # Determine whether we're parsing any single field vars
                sfs = parts[3].strip()
                if sfs == "":
                    sfs = []
                    sfns = []
                else:
                    sfs = [int(x.strip()) for x in sfs.split(",")]
                    sfns = [x.strip() for x in parts[4].strip().split(",")]
                
                # Same thing for aggregation based variables 
                cfs = parts[5].strip()
                groups = []
                names = []
                if cfs != "":
                    for cluster in cfs.split('+'):
                        cleaned_cluster = [int(x.strip()) for x in cluster.strip().split(',')]
                        groups.append(tuple(cleaned_cluster))
                    names = [x.strip() for x in parts[6].strip().split(',')]
                    
                # Skip the row if the lengths don't match up
                if len(sfs) == len(sfns) and len(groups) == len(names):
                    root_names.append(parts[0].strip())
                    tables.append(parts[1].strip())
                    max_nums.append(int(parts[2].strip()))
                    solo_fields.append(sfs)
                    solo_names.append(sfns)
                    combination_fields.append(groups)
                    combination_names.append(names)
                else:
                    print("Error parsing line: " + line.strip())
                    print(groups)
                    print(names)
                    print("Number of fields and number of names do not match")
                    
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
                str_rep = str(i).zfill(3)
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
            str_rep = str(solo_fields[t][i]).zfill(3)
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
                str_rep = str(field).zfill(3)
                str_rep = tables[t] + "_" + str_rep + "E" 
                affected_fields.append(str_rep)
                total += dat[str_rep]
            dat[root_names[t] + ' - ' + combination_names[t][i]] = total
            dat.drop(columns=affected_fields, inplace=True)
        
    return dat


def filter_concepts(search_term):
    """
    Uses census data package to more effectively search for a certain term, for use in terminal/notebooks
    :param search_term:
    :return: list of all metrics that have the search term in the concept
    """
    init_list = cd.search('acs5', 2019, 'concept', search_term)
    concept_set = set([x[1] for x in init_list])
    for x in concept_set:
        print(x)
    return init_list


def get_code_from_concept(concept_name, init_list):
    """
    Gets precise code information from concept name, should be used in conjunction with filter concepts
    :param concept_name: Precise concept name that will be exact matched
    :param init_list: list from filter_concepts of all potential concept fields
    :return: Tuple of code, concept and metric name
    """

    for x in init_list:
        if x[1] == concept_name:
            return x


def create_census_variable_file(filename, single_field_mapping_file, combination_field_mapping_file):
    """
    Writes a csv with fields specified in `combination_field_lookups.txt` and `single_field_lookups.txt`
    :param filename: name of resulting file
    :param single_field_mapping_file: File containing single fields to add to file
    :param combination_field_mapping_file: File containing multiple categories
    :return: None
    """
    # Let's pull some data
    geo = cd.censusgeo([('state', STATE_CODE), ('county', '*'), ('county subdivision', '*')])
    single_field_mapping = parse_single_field_file(single_field_mapping_file)
    df_single = handle_single_fields(geo, single_field_mapping)
    root_names, tables, max_nums, solo_fields, solo_names, combination_fields, combination_names = parse_combination_field_file(combination_field_mapping_file)
    df_combination = download_combination_fields(geo, tables, max_nums, solo_fields, combination_fields)
    df_combination = handle_combination_fields(df_combination, tables, solo_fields, solo_names, combination_fields, root_names, combination_names)
    df = df_single.join(df_combination)
    df[df < 0] = nan
    null_cols = df.isnull().all()
    df = df.drop(null_cols[null_cols].index.values, axis=1)

    # Get rid of the kruft in each town's name that the censusgeo object comes with
    # Makes for much cleaner df writing
    # Also dump subcounties that aren't actual towns (census has a few that are
    # 'unorganized/unspecified')
    df['town'] = [str(x) for x in df.index]
    df = df.loc[df['town'].apply(lambda x: True if 'town' in x else False), :]
    df['town'] = df['town'].apply(lambda x: x.split(',')[0].strip())
    df['town'] = df['town'].apply(lambda x: x.replace(' town', ''))
    df.to_csv(filename, index=False)



