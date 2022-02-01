'''
Takes road outage and service outage data and returns one scenario for the xth percentile
'''
from config import *
from query import *
from nearest_service import *
from get_demo import *
import init_osrm
import inequalipy as ineq


state = 'ch'
hazard_type = 'liquefaction'
optimise_service = 'supermarket'
optimise_demographic = 'total_pop'
file_path = r'results/recovery/opt_recovery_{}_{}_old.csv'.format(optimise_service, optimise_demographic)


# db, context = cfg_init(state)


def recover():
    db, context = cfg_init(state)
    # simulate random hazard event, get list of roads and services that are inoperable
    road_options, df_services = get_damages(state, hazard_type, optimise_service)
    # merge roads with hierachy
    road_options = get_road_hierachy(road_options)
    # init results df
    results = init_results()
    # update results for baseline query @ t=-1, also imports dmeographic data as demo
    results, demo = bau_query(results, db, context)
    # update results for query at point of hazard (t=0)
    results, proximity_ids = hazard_query(results, demo, road_options, df_services, db, context)
    # init df of options to restore
    df_options = init_options(df_services, road_options, proximity_ids)
    # greedy optimise
    results = init_greedy(df_options, results, demo, road_options, db, context)
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

def bau_query(results, db, context):
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

def hazard_query(results, demo, df_roads, df_services, db, context):
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
    # run query for supermarket supply to 172.45050,-43.56613 or 172.66500,-43.34904
    supply_distances = query_supply_points(dest_ids, db, context, optimise_service=None)
    # take unique ids that can get to both state highways in less than 60km
    proximity_ids = []
    for i in list(supply_distances['id_orig'].unique()):
        if (True in list(supply_distances[supply_distances['id_orig']==i].distance.isnull())) or (supply_distances[supply_distances['id_orig']==i].distance.sum() > 60000):
            continue
        else:
            proximity_ids.append(i)
    # refine for nearest
    baseline_nearest = find_nearest_service(distance_matrix, dest_ids, db, context)
    baseline_nearest = combine_demo_dist(baseline_nearest, demo, False)
    time = 0
    temp_results = make_temp_results(time, baseline_nearest, None, None)
    temp_df = pd.Series(temp_results, index = results.columns)
    results = results.append(temp_df, ignore_index=True)
    return(results,  proximity_ids)

def init_options(df_services, road_options, proximity_ids):
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
    df_options = df_options.reset_index(drop=True)
    df_options['proximity'] = 0
    # col for 'Collector', 'Local Road', 'Major Arterial', 'Minor Arterial' road lengths
    collector, local, major, minor, private, cell_ids = [], [], [], [], [], []
    for cell_id in road_options['cell_id'].unique():
        cell_ids.append(cell_id)
        collector.append(road_options[(road_options['cell_id']==cell_id) & (road_options['hierarchy']=='Collector')]['length'].sum())
        local.append(road_options[(road_options['cell_id']==cell_id) & (road_options['hierarchy']=='Local Road')]['length'].sum())
        major.append(road_options[(road_options['cell_id']==cell_id) & (road_options['hierarchy']=='Major Arterial')]['length'].sum())
        minor.append(road_options[(road_options['cell_id']==cell_id) & (road_options['hierarchy']=='Minor Arterial')]['length'].sum())
        private.append(road_options[(road_options['cell_id']==cell_id) & (road_options['hierarchy']=='Private')]['length'].sum())
    collector += [0]*(len(df_options)-len(collector))
    local += [0]*(len(df_options)-len(local))
    major += [0]*(len(df_options)-len(major))
    minor += [0]*(len(df_options)-len(minor))
    private += [0]*(len(df_options)-len(private))
    df_options['local'] = local
    df_options['collector'] = collector
    df_options['major'] = major
    df_options['minor'] = minor
    df_options['private'] = private
    proximity = []
    for i in df_options.index:
        if (df_options['type'].iloc[i] == 'service') and (df_options['option_id'].iloc[i] in proximity_ids):
            proximity.append(1)
        else:
            proximity.append(0)
    # update proximity
    df_options['proximity'] = proximity
    return(df_options)

def init_greedy(df_options, results, demo, road_options, db, context):
    '''
    Loops through all possible options within a timestep & executes the best option before removing that option from future use
    '''
    print('BEGINNING GREEDY OPTIMIZATION')
    # start greedy optim
    iterations = np.arange(0,len(df_options))
    for i in tqdm(iterations): # total number of iterations
        # set timestep, starts at 1
        time = i + 1
        # loop through all options of a timestep
        for j in tqdm(np.arange(0, len(df_options))): # check each option within a timestep, chose best. j is the index of each option
            print('ESTIMATED TOTAL TIME: {} HOURS'.format(np.sum(iterations)*9/60**2))
            # check if option is road or service related
            if df_options.iloc[j]['type'] == 'road':
                # make tempory df of roads to close (closes all except those within cell j)
                temp_roads = road_options[road_options['cell_id'] != df_options.iloc[j]['option_id']]
                # updates OSRM server for closed roads
                close_rd(temp_roads, db, context)
                # sets destionations to close - should be all those within df_options
                dest_ids = list(df_options[df_options['type']=='service']['option_id'])

            elif df_options.iloc[j]['type'] == 'service':
                # get the id of the dest to open
                dest_id = df_options.iloc[j]['option_id']
                # get list of ids to close (all in df_options except dest_id)
                dest_ids = [x for x in list(df_options[df_options['type']=='service']['option_id']) if x != dest_id]
                # get roads to close based on grid ids left in df_options
                temp_roads = road_options[road_options['cell_id'].isin(list(df_options[df_options['type']=='road']['option_id']))]
                # updates OSRM server with closed roads
                close_rd(temp_roads, db, context)

            # test option by evaluating access and isolation change    
            distance_matrix = query_points(dest_ids, db, context, optimise_service)
            # get nearest
            baseline_nearest = find_nearest_service(distance_matrix, dest_ids, db, context)
            # combine with demographic data
            baseline_nearest = combine_demo_dist(baseline_nearest, demo, False)
            # update temp results for option metrics
            temp_results = make_temp_results(time, baseline_nearest, None, None)
            # turn into df
            temp_df = pd.Series(temp_results, index = results.columns)
            # update option id with changed isolation metrics
            df_options.loc[j, 'delta_iso'] = list(results[results['time']==(time-1)]['iso_{}_{}'.format(optimise_service, optimise_demographic)])[0] - temp_df['iso_{}_{}'.format(optimise_service, optimise_demographic)]
            # update option id with changed EDE metrics
            df_options.loc[j, 'delta_ede'] = list(results[results['time']==(time-1)]['ede_{}_{}'.format(optimise_service, optimise_demographic)])[0] - temp_df['ede_{}_{}'.format(optimise_service, optimise_demographic)]

        # reset osrm server
        init_osrm.main(False, state, context)
        # assess whether there is one or multiple best options
        if len(list(df_options[df_options['delta_iso'] == df_options['delta_iso'].max()]['option_id'])) == 1:
            # get the option ID for the best option
            best_id = list(df_options[df_options['delta_iso'] == df_options['delta_iso'].max()]['option_id'])[0]
            # get which type of restoration it is, road or service
            best_type = list(df_options[df_options['delta_iso'] == df_options['delta_iso'].max()]['type'])[0]

        elif len(list(df_options[df_options['delta_iso'] == df_options['delta_iso'].max()]['option_id'])) > 1:
            # format so can assess which has best change in EDE and ISO
            temp_best_df = df_options[df_options['delta_iso'] == df_options['delta_iso'].max()]
            # get the option ID for the best option
            best_id = list(temp_best_df[temp_best_df['delta_ede'] == temp_best_df['delta_ede'].max()]['option_id'])[0]
            # get which type of restoration it is, road or service
            best_type = list(temp_best_df[temp_best_df['delta_ede'] == temp_best_df['delta_ede'].max()]['type'])[0]

        # execute the best option & remove that option from appearing in future
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
        # get access stats from greedy choice
        distance_matrix = query_points(dest_ids, db, context, optimise_service)
        # refines to nearest
        baseline_nearest = find_nearest_service(distance_matrix, dest_ids, db, context)
        # combine with demographic data
        baseline_nearest = combine_demo_dist(baseline_nearest, demo, False)
        # gets temp results
        temp_results = make_temp_results(time, baseline_nearest, best_type, best_id)
        # updates results
        temp_df = pd.Series(temp_results, index = results.columns)
        # updates results
        results = results.append(temp_df, ignore_index=True)
        # removes used option from df_options
        df_options = df_options.drop(list(df_options[(df_options['type']==best_type) & (df_options['option_id']==best_id)].index))
        df_options['delta_iso'] = 0
        df_options['delta_ede'] = 0
        df_options = df_options.reset_index(drop=True)
        road_options = temp_roads

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


### OLD CODE
# def make_temp_results(time, baseline_nearest, restore_type, restore_id):
#     if time == -1:
#         iso = 0
        # temp_results = [time, 
        # ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['total_pop'])),
        # iso,
        # ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['white'])),
        # iso,
        # ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['indigenous'])),
        # iso,
        # ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['asian'])),
        # iso,
        # ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['polynesian'])),
        # iso, restore_type, restore_id]
#     else:
#         temp_results = [time, 
#         ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['total_pop'])),
#         baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['total_pop'].sum(),
#         ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['white'])),
#         baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['white'].sum(),
#         ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['indigenous'])),
#         baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['indigenous'].sum(),
#         ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['asian'])),
#         baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['asian'].sum(),
#         ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['polynesian'])),
#         baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['polynesian'].sum(), restore_type, restore_id]
#     return(temp_results)


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

    df.to_csv(r'data/osm/updates/update.csv', header=False, index=False)
    sim = True
    init_osrm.main(sim, state, context)

    # re query
    return()

def get_road_hierachy(road_options):
    # import
    rh = gpd.read_file(r'/home/mitchell/CivilSystems/projects/access_resilience/chch_roads.shp')
    # drop no service
    rh = rh[rh['ServiceSta']=='In Service']
    # buffer
    rh = rh.to_crs(2193)
    rh['geometry'] = rh.geometry.buffer(20)
    rh = rh[['geometry', 'Hierarchy']]
    rh = rh.to_crs(4326)
    # merge
    road_options = gpd.sjoin(road_options, rh, how="left", op='intersects')
    # replace nan with 'Private'
    road_options['hierarchy'] = road_options['Hierarchy'].fillna('Private')
    # rename Central City Local Distributor and Central City Main Distributor with Local Road
    road_options['hierarchy'].replace({"Central City Local Distributor": "Local Road", "Central City Main Distributor": "Local Road", "Pedestrian":"Private"}, inplace=True)
    return(road_options)

def get_damages(state, hazard_type, optimise_service):
    # get road options from greedy optimised run
    road_options = gpd.read_file(r'results/recovery/road_options.shp')
    # get services used in greedy optimise run
    df_dests = gpd.read_file(r'results/recovery/service_options.shp')
    df_dests = df_dests.drop(columns=['geometry'])
    df_dests = df_dests.set_index('id')
    return(road_options, df_dests)

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