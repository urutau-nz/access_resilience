'''this is intended to be run during each iteration so it returns a new set of ids'''

from config import *


def dests_to_drop(exposure_df, hazard_type, db, context):
    '''picks out dest ids that are affected by hazard'''
    closed_ids = []
    #set hypothetical damage level for each building
    damage_level = np.random.uniform(size=len(exposure_df))
    exposure_df['damage'] = damage_level
    #if dmaage level is over these thresholds then it has to close
    exposure_level = ['low', 'med', 'high']
    #this is the expected percentage of services to remain open at each exposure level, according to 2 damage state fragility curves
    if hazard_type in ['tsunami', 'hurricane']:
        damage_threshold = [0.6, 0.2, 0.025]
    elif hazard_type == 'liquefaction':
        damage_threshold = [0.90, 0.67, 0.195]
    #the others were taken from sources (see our report for references), this was just a rough combination
    elif hazard_type == 'multi':
        damage_threshold = [0.55, 0.15, 0.01, 0]
        exposure_level = ['low', 'med', 'high', 'very high']
    for i in range(len(damage_threshold)):
        to_shut = exposure_df.loc[(exposure_df['exposure'] == exposure_level[i]) & (exposure_df['damage'] > damage_threshold[i])]
        closed_ids.extend(to_shut['dest_id'].tolist())
    return closed_ids
