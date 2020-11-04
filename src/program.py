'''runs simulation to find return a large table called nearest_matrix, which is a collection of nearest_distance tables collated with a sim number'''
from config import *
from query import *
from calculate_ede import *
from nearest_service import *
from get_demo import *
from plot_cdf import *
import initialise_hazard
from close_destinations import *
import drop_roads
import init_osrm

def main_function(state):
    '''main'''
    #initialise config
    db, context = cfg_init(state)
    # reset osrm network
    sim = False
    init_osrm.main(sim, state, context)
    print('Beginning Baseline Query')
    #get baseline origxdest df and nearest service
    dest_ids = []
    baseline_distance = query_points(dest_ids, db, context)
    baseline_nearest = find_nearest_service(baseline_distance, dest_ids, db, context)
    #intilise hazard, df to save and find dests exposed at each fragility level
    hazard_type = 'hurricane'#'multi'#'liquefaction'#'liquefaction'
    exposure_df = initialise_hazard.open_hazard(hazard_type, db, context)
    # get gpd df of roads with inundation depths and damage bands
    exposed_roads = drop_roads.open_hazard(hazard_type, db, context)
    nearest_matrix = pd.DataFrame(columns=['id_orig', 'distance', 'dest_type', 'sim_num'])
    #open demographic data
    demo = demographic_data(baseline_nearest, db, context)
    #number of iterations for the simulation
    nsim = 1000
    for i in tqdm(range(nsim)):
        #close destinations and roads according to 2 damage state fragility curves
        dest_ids = dests_to_drop(exposure_df, hazard_type, db, context)
        exposed_roads = drop_roads.close_rd(exposed_roads, state, hazard_type, db, context)
        #requery access in city with new road network and destinations
        distance_matrix = query_points(dest_ids, db, context)
        #find new nearest_service matrix by filtering through distance matrix
        nearest_service = find_nearest_service(distance_matrix, dest_ids, db, context)
        #save sim number
        nearest_service['sim_num'] = i
        #saving  simulation to nearest_matrix
        nearest_matrix = pd.concat([nearest_matrix, nearest_service], ignore_index=True)
    #save matrix to sql
    write_to_postgres(nearest_matrix, db, 'nearest_distance_{}'.format(hazard_type), indices=False)
    print('Saved nearest distance matrix to SQL')

def query_baseline(state):
    '''saves a copy of the baseline_nearest to sql, needed for compile_results.py'''
    #initialise config
    db, context = cfg_init(state)
    # reset osrm network
    sim = False
    init_osrm.main(sim, state, context)
    print('Beginning Baseline Query')
    #open baseline origxdest df and nearest service #definately would be faster to save and open these, should make an initilise function?
    dest_ids = []
    baseline_distance = query_points(dest_ids, db, context)
    baseline_nearest = find_nearest_service(baseline_distance, dest_ids, db, context)
    write_to_postgres(baseline_nearest, db, 'baseline_nearest', indices=False)

#if __name__ == "__main__":
state = 'tx'#'wa'#'ch'
#query_baseline(state)
main_function(state)
