from recordlinkage import Index, Compare
import pandas as pd
from builtins import isinstance
import sys

'''
To reference more information about deduplication with recordlinkage,
consult the docs and a working example at:
https://recordlinkage.readthedocs.io/en/latest/notebooks/data_deduplication.html
'''

SCORE_THRESHOLD = 5
OUT_FILE = 'deduped_ece_child_ids.csv'


def identify_duplicates(df, threshold, show_ranks_distribution=True):
    '''
    Identifies duplicates in a given data frame that consists of
    child records with a variety of fields. For the identification
    procedure to succeed, the df MUST contain the following fields,
    named as such:
      - id
      - birthdate
      - sasid
      - uniqueId
      - firstName
      - middleName
      - lastName
    Additionally, the df will be typecast to strings before finding
    duplicates, so it's advisable to pass in just a dataframe with
    these given columns. 
    '''
    print('-------Casting Data Frame-------')
    # Empty strings are 'compared as' equal under exact blocking
    # This lets us check for sasids when they're there but not
    # care if they aren't
    df.fillna('', inplace=True)
    df.loc[:, df.columns != 'id'] = df.drop('id', axis=1).apply(lambda x: x.astype(str).str.title())

    print('-------Indexing Candidate Matches-------')
    indexer = Index()
    # Blocking on sasids gives too many candidates because na's and
    # '' are treated as matching pairs--this gives 92 million candidates...
    # Also, many children are missing sasids, but there's only a single
    # record that doesn't have a birthdate, making it the best initial
    # candidate selector
    indexer.sortedneighbourhood('birthdate', window=3)
    candidates = indexer.index(df)
    print(str(len(candidates)) + ' candidate pairs identified')

    print('-------Building similarity scores-------')
    comparator = Compare()
    # We'll make an allowance for the equivalent of transposing one digit
    # in each of these IDs, since they're still human entered
    comparator.string('sasid', 'sasid', threshold=0.95, label='sasid')
    comparator.string('uniqueId', 'uniqueId', threshold=0.95, label='uniqueId')

    # These are threshold scores based on probability of being the
    # same string, just misspelled
    # Thresholds are based on a combination of guidance from the example
    # and some experimentation around quality of matches
    comparator.string('firstName', 'firstName', threshold=0.85, label='firstName')
    comparator.string('middleName', 'middleName', threshold=0.85, label='middleName')
    comparator.string('lastName', 'lastName', threshold=0.85, label='lastName')
    comparator.string('birthdate', 'birthdate', threshold=0.85, label='birthdate')
    features = comparator.compute(candidates, df)

    if show_ranks_distribution:
        # With six features and two exact matches, all candidates will score
        # between 2 and 6; each name field and birthdate that matches is +1.
        # We just need to decide the cutoff level. 6's are guaranteed matches.
        # In 200+ 5's, I saw MAYBE one false positive, so those are good too.
        # 4's get tricky and look 50/50 on whether one of the names are 
        # significantly different.
        print("")
        print('Distribution of ranks:')
        print(features.sum(axis=1).value_counts().sort_index(ascending=False))
        print("")
        
    print('-------Thresholding Matches-------')
    # Decided on keeping only records that have at least 5 score points.
    # These are the highest quality matches and don't prune out any records
    # that aren't true duplicates.
    matches = features[features.sum(axis=1) >= threshold]
    print(str(len(matches)) + ' duplicates identified')
    print("")
                 
    # Start by building a dictionary pointing duplicates to the original
    dupes = {}
    for idx in matches.index:
        dupes[df.iloc[idx[1]]['id']] = df.iloc[idx[0]]['id']
    
    # Now assign each child their own unique ID for DB joining purposes
    ece_ids = list(df['id'].values)
    new_ids = {}
    i = 1
    # Start with a first pass to make sure all "original" records are given
    # an id, since duplicates are in no particular referential order
    for id in ece_ids:
        if not id in dupes:
            new_ids[id] = i
            i += 1
        else:
            new_ids[id] = dupes[id]
    # Now replace everything that points to another record with the
    # reference record's ID number
    for key in new_ids:
        if isinstance(new_ids[key], str):
            new_ids[key] = new_ids[new_ids[key]]
    new_ids = [new_ids[id] for id in ece_ids]
    
    # Write the output to a new CSV
    out = pd.DataFrame()
    out['ece_ids'] = ece_ids
    out['new_ids'] = new_ids
    out.to_csv(OUT_FILE, index=False)
        

if __name__ == '__main__':
    fpath = sys.argv[-1]
    df = pd.read_csv(fpath)
    identify_duplicates(df, SCORE_THRESHOLD, show_ranks_distribution=False)


