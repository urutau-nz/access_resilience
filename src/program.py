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
    #open baseline origxdest df
    dest_ids = []
    distance_matrix = pd.read_sql('SELECT * FROM baseline_distance', db['con'])
    #intilise hazard, df to save and find dests exposed at each fragility level
    hazard_type = 'tsunami'
    exposure_df = open_hazard(hazard_type, db, context)
    nearest_matrix = pd.DataFrame(columns=['id_orig', 'distance', 'dest_type', 'sim_num'])
    nsim = 1
    for i in tqdm(range(nsim)):
        #close destinations
        dest_ids = dests_to_drop(exposure_df, hazard_type, db, context)
        #drop roads(?)

        #requery
        distance_matrix = query_points(dest_ids, db, context)
        #find new nearest_service matrix
        nearest_service = find_nearest_service(distance_matrix, dest_ids, db, context)
        #save sim number
        nearest_service['sim_num'] = i
        #saving data
        nearest_matrix = pd.concat([nearest_matrix, nearest_service], ignore_index=True)

    #having a gander at some results
    demo = demographic_data(nearest_service, db, context) #doesn't matter which nearest service. its just used to find the blocks
    ede_matrix = pd.DataFrame()
    for j in nearest_matrix.sim_num.unique():
        subset = nearest_matrix.loc[nearest_matrix['sim_num'] == j]
        ede_df = kp_ede_main(demo, subset, context)
        ede_df['sim_num'] = j
        ede_matrix = pd.concat([ede_matrix, ede_df], ignore_index=True)

    sup = ede_matrix.loc[(ede_matrix['population_group'] == 'population') & (ede_matrix['dest_type'] == 'medical_clinic')]
    mean = sup.ede.mean()
    print('mean medical_centers = {}\n'.format(mean))
    tenth = sup.ede.quantile(0.1)
    print('10th percentile = {}\n'.format(tenth))
    ninety = sup.ede.quantile(0.9)
    print('90th percentile = {}\n'.format(ninety))




#if __name__ == "__main__":
state = 'ch'#input('State: ')
main_function(state)

#calculate ede's
#ede_df = kp_ede_main(demo, nearest_service, context)
#ede_df.to_csv('results/ede_after.csv')

#plotting(nearest_service, demo, db, context)
