'''runs program'''
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
    #open baseline origxdest df and nearest service #definately would be faster to save and open these, should make an initilise function?
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
        #close destinations
        dest_ids = dests_to_drop(exposure_df, hazard_type, db, context)
        #drop roads
        exposed_roads = drop_roads.close_rd(exposed_roads, state, hazard_type, db, context)
        #requery
        distance_matrix = query_points(dest_ids, db, context)
        #find new nearest_service matrix
        nearest_service = find_nearest_service(distance_matrix, dest_ids, db, context)
        #save sim number
        nearest_service['sim_num'] = i
        #saving data
        nearest_matrix = pd.concat([nearest_matrix, nearest_service], ignore_index=True)
    #code.interact(local=locals())
    #save matrix to sql for analysis later
    save_matrix = True
    if save_matrix == True:
        write_to_postgres(nearest_matrix, db, 'nearest_distance_{}'.format(hazard_type), indices=False)
        print('Saved nearest distance matrix to SQL')
    else:
        plotting(baseline_nearest, nearest_matrix, demo, db, context, hazard_type, nsim)
        #having a gander at some results
        #update something horribly wrong is going on here
        ede_matrix = pd.DataFrame()
        for j in nearest_matrix.sim_num.unique():
            subset = nearest_matrix.loc[nearest_matrix['sim_num'] == j]
            ede_df = kp_ede_main(demo, subset, context)
            ede_df['sim_num'] = j
            ede_matrix = pd.concat([ede_matrix, ede_df], ignore_index=True)

        sup = ede_matrix.loc[(ede_matrix['population_group'] == 'total') & (ede_matrix['dest_type'] == 'medical_clinic')]
        mean = sup.ede.mean()
        print('mean medical_centers = {}\n'.format(mean))
        tenth = sup.ede.quantile(0.1)
        print('10th percentile = {}\n'.format(tenth))
        ninety = sup.ede.quantile(0.9)
        print('90th percentile = {}\n'.format(ninety))



def doot(state):
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
state = 'tx'#input('State: ')
#doot(state)
main_function(state)

#calculate ede's
#ede_df = kp_ede_main(demo, nearest_service, context)
#ede_df.to_csv('results/ede_after.csv')

#plotting(nearest_service, demo, db, context)
#
