'''runs program'''
from config import *
from query import *
from calculate_ede import *
from nearest_service import *
from get_demo import *
from plot_cdf import *
from initialise_hazard import *
from drop_destinations import *

def main_function(state):
    '''main'''
    #initialise config
    db, context = cfg_init(state)
    #query origins and destinations
    #origxdest = query_points(db, context)
    origxdest = pd.read_sql('SELECT * FROM baseline_distance', db['con'])
    #find nearest_service
    dest_ids = []
    nearest_service = find_nearest_service(origxdest, dest_ids, db, context)
    #retrieve demographic data, also refines nearest service to match number of rows as SA1's, due to one being in the sea.
    demo, nearest_service = demographic_data(nearest_service, db, context)
    #to calcualte edes
    #ede_df = kp_ede(demo, nearest_service, context)
    #ede_df.to_csv('results/ede_before.csv')

    #plotting(nearest_service, demo, db, context)
    exposure_df = open_hazard(hazard_type, db, context)

    dest_ids = dests_to_drop(exposure_df, db, context) #needs rework
    nearest_service = find_nearest_service(origxdest, dest_ids, db, context)
    demo, nearest_service = demographic_data(nearest_service, db, context)
    #ede_df = kp_ede(demo, nearest_service, context)
    #ede_df.to_csv('results/ede_after.csv')
    plotting(nearest_service, demo, db, context)
    #will need a new origxdest when roads are altered, for now this will suffice

    #code.interact(local=locals())

#if __name__ == "__main__":
state = 'ch'#input('State: ')
main_function(state)
