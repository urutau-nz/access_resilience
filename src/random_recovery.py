'''
Takes road outage and service outage data and returns one scenario for the xth percentile
'''
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
import shapely
import inequalipy as ineq


state = 'ch'
hazard_type = 'liquefaction'
optimise_service = 'supermarket'
optimise_demographic = 'total_pop'
file_path = r'results/recovery/new_random_recovery_{}_{}.csv'.format(optimise_service, optimise_demographic)

start_from_mid = True

db, context = cfg_init(state)


def recover():
    if start_from_mid == False:
        # simulate random hazard event, get list of roads and services that are inoperable
        road_options, df_services = get_damages(state, hazard_type, optimise_service)
        # init results df
        results = init_results()
        # update results for baseline query @ t=-1, also imports dmeographic data as demo
        results, demo = bau_query(results)
        # update results for query at point of hazard (t=0)
        results = hazard_query(results, demo, road_options, df_services)
        # init df of options to restore
        df_options = init_options(df_services, road_options)
        # greedy optimise
        results = init_random(df_options, results, demo, road_options)
    else:
        temp_results = init_results()
        temp_results, demo = bau_query(temp_results)
        road_options = gpd.read_file('results/recovery/rand_road_options.shp')
        df_options = pd.read_csv('results/recovery/rand_df_options.csv')
        results = pd.read_csv('results/recovery/rand_results.csv')
        results = results.drop(columns=['Unnamed: 0'])
        results = init_random(df_options, results, demo, road_options)
    # save results
    results.to_csv(file_path)

def init_results():
    '''
    Make DF for results
    '''
    results = pd.DataFrame(columns=[
        'time','ede_{}_total_pop'.format(optimise_service), 'iso_{}_total_pop'.format(optimise_service), 'ede_{}_white'.format(optimise_service), 'iso_{}_white'.format(optimise_service), 'ede_{}_indigenous'.format(optimise_service), 'iso_{}_indigenous'.format(optimise_service), 
        'ede_{}_asian'.format(optimise_service), 'iso_{}_asian'.format(optimise_service), 'ede_{}_polynesian'.format(optimise_service), 'iso_{}_polynesian'.format(optimise_service), 'restore_type', 'restore_id'])
    return(results)

def bau_query(results):
    '''
    Run query for business as usual (BAU / no hazard imposed)
    Return updated results df at t=-1, returns demographic dataframe too
    '''
    print('QUERYING ACCESS AT BUSINESS AS USUAL')
    #baseline query
    sim = False
    init_osrm.main(sim, state, context)
    print('Beginning Baseline Query')
    dest_ids = []
    #gets all network distances
    baseline_distance = query_points(dest_ids, db, context, optimise_service)
    # refines for just nearest distance to each service type
    baseline_nearest = find_nearest_service(baseline_distance, dest_ids, db, context)
    baseline_nearest = baseline_nearest.reset_index()
    # imports demographic data
    demo = demographic_data(baseline_nearest, db, context)
    demo.sort_values(by=['id_orig'], inplace=True, ignore_index=True)
    baseline_nearest = combine_demo_dist(baseline_nearest, demo, True)
    # populate results df
    temp_results = make_temp_results(-1, baseline_nearest, None, None)
    temp_df = pd.Series(temp_results, index = results.columns)
    results = results.append(temp_df, ignore_index=True)
    return(results, demo)

def hazard_query(results, demo, df_roads, df_services):
    '''
    Run query at the point of the hazard
    Return updated results df at t=0
    '''
    print('QUERYING DISTANCE AT POINT OF HAZARD')
    # take damaged roads and update osrm server
    close_rd(df_roads, db, context)
    # get list of destination IDs which are to be closed
    dest_ids = list(df_services.index)
    # run query with only operable roads and services
    distance_matrix = query_points(dest_ids, db, context, optimise_service)
    # refine for nearest
    baseline_nearest = find_nearest_service(distance_matrix, dest_ids, db, context)
    baseline_nearest = combine_demo_dist(baseline_nearest, demo, False)
    time = 0
    temp_results = make_temp_results(time, baseline_nearest, None, None)
    temp_df = pd.Series(temp_results, index = results.columns)
    results = results.append(temp_df, ignore_index=True)
    return(results)

def init_options(df_services, road_options):
    '''
    Return df of options to restore
    '''
    service_options = list(df_services.index)
    df_service_temp = pd.DataFrame()
    df_service_temp['option_id'] = service_options
    df_service_temp['type'] = 'service'
    df_options = pd.DataFrame()
    df_options['option_id'] = list(road_options['cell_id'].unique())
    df_options['type'] = 'road'
    df_options = df_options.append(df_service_temp)
    df_options['delta_iso'] = 0
    df_options['delta_ede'] = 0
    df_options = df_options.reset_index(drop=True)
    return(df_options)

def init_random(df_options, results, demo, road_options):
    '''
    Loops through all possible options within a timestep & executes the best option before removing that option from future use
    '''
    print('BEGINNING RANDOM RESTORATION')
    # start random recovery
    
    iterations = np.arange(0,len(df_options))
    for i in tqdm(iterations): # total number of iterations
        # set timestep, starts at 1
        time = i + 1
        # reset osrm server
        print('resetting osrm')
        init_osrm.main(False, state, context)
        # pick random option
        best_index = np.random.randint(0,len(df_options))
        best_id = df_options['option_id'].iloc[best_index]
        best_type = df_options['type'].iloc[best_index]
        # execute the best option & remove that option from appearing in future
        print('determining best type')
        if best_type == 'service':
            # get the option ID
            #df_option_id = list(df_options[(df_options['type']=='service') & (df_options['option_id']==best_id)].index)[0] ## TRY USE BEST ID
            # get list of ids to close (all in df_options except dest_id)
            dest_ids = [x for x in list(df_options[df_options['type']=='service']['option_id']) if x != best_id]
            # get roads to close based on grid ids left in df_options
            temp_roads = road_options[road_options['cell_id'].isin(list(df_options[df_options['type']=='road']['option_id']))]
            # updates OSRM server with closed roads
            close_rd(temp_roads, db, context)
        elif best_type == 'road':
            # get the option ID
            #df_option_id = list(df_options[(df_options['type']=='road') & (df_options['option_id']==best_id)].index)[0] ## TRY USE BEST ID
            # make tempory df of roads to close (closes all except those within cell 'df_option_id')
            temp_roads = road_options[road_options['cell_id'] != best_id]
            # updates OSRM server for closed roads
            close_rd(temp_roads, db, context)
            # sets destionations to close - should be all those within df_options
            dest_ids = list(df_options[df_options['type']=='service']['option_id'])
        print('querying post option distances')
        # get access stats from greedy choice
        distance_matrix = query_points(dest_ids, db, context, optimise_service)
        # refines to nearest
        print('nearest')
        baseline_nearest = find_nearest_service(distance_matrix, dest_ids, db, context)
        # combine with demographic data
        print('combine demo')
        baseline_nearest = combine_demo_dist(baseline_nearest, demo, False)
        # gets temp results
        print('EDEs')
        temp_results = make_temp_results(time, baseline_nearest, best_type, best_id)
        # updates results
        temp_df = pd.Series(temp_results, index = results.columns)
        # updates results
        results = results.append(temp_df, ignore_index=True)
        # removes used option from df_options
        print('resetting df options')
        df_options = df_options.drop(list(df_options[(df_options['type']==best_type) & (df_options['option_id']==best_id)].index))
        df_options = df_options.reset_index(drop=True)
        road_options = temp_roads
        if len(df_options) == 100:
            x=1
            #SAVE RESULTS AND DF_OPTIONS, RUN AGAIN, ROAD_OPTIONS
            road_options.to_file('results/recovery/rand_road_options.shp')
            df_options.to_csv('results/recovery/rand_df_options.csv')
            results.to_csv('results/recovery/rand_results.csv')
    # returns results
    return(results)

def make_temp_results(time, baseline_nearest, restore_type, restore_id):
    if time == -1:
        epsilon_i = -0.5 #-0.5692 #-0.5
        iso = 0
        temp_results = [time, 
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['total_pop'])),
        iso,
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['white'])),
        iso,
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['indigenous'])),
        iso,
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['asian'])),
        iso,
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['polynesian'])),
        iso, restore_type, restore_id]
    else:
        if time > 10:
            epsilon_i = -0.5#-0.5692 #-0.5
        else:
            epsilon_i = -0.5#-0.7552 #-0.5
        temp_results = [time, 
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['total_pop'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][baseline_nearest['distance'].isnull()]['total_pop'].sum(),
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['white'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][baseline_nearest['distance'].isnull()]['white'].sum(),
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['indigenous'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][baseline_nearest['distance'].isnull()]['indigenous'].sum(),
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['asian'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][baseline_nearest['distance'].isnull()]['asian'].sum(),
        ineq.kolmpollak.ede(a=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()).astype(float), epsilon=epsilon_i, kappa=None, weights=np.array(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['polynesian'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][baseline_nearest['distance'].isnull()]['polynesian'].sum(), restore_type, restore_id]
    return(temp_results)

def close_rd(df_roads, db, context):
    state = 'ch'
    # make list of from and to OSM IDs
    df = pd.DataFrame()
    df['from_osmid'] = df_roads['from']
    df['to_osmid'] = df_roads['to']

    # reverse way
    df_inv = pd.DataFrame()
    df_inv['from_osmid'] = df_roads['to']
    df_inv['to_osmid'] = df_roads['from']

    df = df.append(df_inv)
    df = df.astype(int)

    # set edge speeds
    df['edge_speed'] = 0

    df.to_csv(r'/home/mitchell/projects/access_resilience/data/osm/updates/update.csv', header=False, index=False)
    # init_osrm.py/.sh
    sim = True
    init_osrm.main(sim, state, context)

    # re query
    return()

def get_damages(state, hazard_type, optimise_service):
    # get road options from greedy optimised run
    roads_options = gpd.read_file(r'results/recovery/road_options.shp')
    # get services used in greedy optimise run
    df_dests = gpd.read_file(r'results/recovery/service_options.shp')
    df_dests = df_dests.drop(columns=['geometry'])
    df_dests = df_dests.set_index('id')
    return(roads_options, df_dests)

def combine_demo_dist(baseline_nearest, demo, drop_na):
    '''
    Combines two dfs
    '''
    #combines demographic and distance, has to times by three for the three services (FOR CHC CASE ONLY) ### CHANGE THIS CODE TO SOMETHING MORE ROBUST
    # sort for optimised service
    baseline_nearest = baseline_nearest[baseline_nearest['dest_type']==optimise_service]
    if drop_na == True:
        # drop nan distances
        baseline_nearest = baseline_nearest.dropna()
    # format column type to merge on
    baseline_nearest['id_orig'] = baseline_nearest['id_orig'].astype(str)
    # merge with demo data
    baseline_nearest = pd.merge(baseline_nearest, demo, on=["id_orig"])
    # change col name
    baseline_nearest['total_pop'] = baseline_nearest['total']
    baseline_nearest = baseline_nearest.drop(columns=['latino', 'african_american'])
    return(baseline_nearest)

if __name__ == "__main__":
    recover()