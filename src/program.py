'''runs program'''
from config import *
from query import *
from calculate_ede import *
from nearest_service import *
from get_demo import *
from plot_cdf import *
from initialise_hazard import *
from close_destinations import *

def main_function(state):
    '''main'''
    #initialise config
    db, context = cfg_init(state)
    #query origins and destinations
    #origxdest = query_points(db, context)
    #open baseline origxdest df
    distance_matrix = pd.read_sql('SELECT * FROM baseline_distance', db['con'])
    #intilise hazard, find dests exposed at each level
    hazard_type = 'tsunami'
    exposure_df = open_hazard(hazard_type, db, context)
    nsim = 100
    for i in tqdm(range(nsim)):
        #close destinations
        dest_ids = dests_to_drop(exposure_df, hazard_type, db, context)
        #drop roads(?)

        #requery
        distance_matrix = query_points(dest_ids, db, context)
        #find new nearest_service matrix
        nearest_service = find_nearest_service(distance_matrix, dest_ids, db, context)
        #how to save the data?
    code.interact(local=locals())


#if __name__ == "__main__":
state = 'ch'#input('State: ')
main_function(state)

#calculate ede's
#ede_df = kp_ede(demo, nearest_service, context)
#ede_df.to_csv('results/ede_after.csv')

#plotting(nearest_service, demo, db, context)
