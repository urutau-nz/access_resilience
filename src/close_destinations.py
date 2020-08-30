'''this is intended to be run during each iteration so it returns a new set of ids'''
#open up dest df in gdf format (possibly pass this to function so we only have to open it once)
#then return a list of dest ids to ignore in next simulation, change nearest distance function to include this.
from config import *


def dests_to_drop(exposure_df, db, context):
    '''picks out dest ids that are affected by hazard'''
    closed_ids = []
    #set hypothetical damage level for each building
    exposure_df['damage'] = np.random.random_sample(exposure_df.shape[0])
    #if dmaage level is over these thresholds then it has to close
    exposure_level = ['low', 'med', 'high']
    damage_threshold = [0.95, 0.5, 0.05]
    for i in range(0, 3):
        to_shut = exposure_df.loc[(exposure_df['exposure'] == exposure_level[i]) & (exposure_df['damage'] > damage_threshold[i])]
        closed_ids.extend(to_shut['dest_id'].tolist())

    return closed_ids



'''
    low medium high
p = 0.05 0.5  0.95
just choose a value from np.random and then if its smaller than threshold close the dest?
'''
