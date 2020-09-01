'''this is intended to be run during each iteration so it returns a new set of ids'''
#open up dest df in gdf format (possibly pass this to function so we only have to open it once)
#then return a list of dest ids to ignore in next simulation, change nearest distance function to include this.
from config import *


def dests_to_drop(exposure_df, hazard_type, db, context):
    '''picks out dest ids that are affected by hazard'''
    closed_ids = []
    #set hypothetical damage level for each building
    damage_level = np.random.uniform(size=len(exposure_df))
    exposure_df['damage'] = damage_level
    #if dmaage level is over these thresholds then it has to close
    exposure_level = ['low', 'med', 'high']
    #this is the expected percentage of services to remain open in each respective zone
    #it will be different for different hazards?
    if hazard_type == 'tsunami':
        damage_threshold = [0.8, 0.45, 0.05]
    elif hazard_type == 'liquefaction':
        damage_threshold = [0.95, 0.75, 0.4]
    for i in range(0, 3):
        to_shut = exposure_df.loc[(exposure_df['exposure'] == exposure_level[i]) & (exposure_df['damage'] > damage_threshold[i])]
        closed_ids.extend(to_shut['dest_id'].tolist())

    return closed_ids
