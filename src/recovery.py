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
grids = 900 #must be a square number
optimise_service = 'supermarket'
optimise_demographic = 'total_pop'
file_path = r'/homedirs/man112/monte_christchurch/results/recovery/recovery_{}_{}.csv'.format(optimise_service, optimise_demographic)


db, context = cfg_init(state)


def recover():
    # simulate random hazard event, get list of roads and services that are inoperable
    df_roads, df_services = random_sim(state, hazard_type, optimise_service)
    # make grid and assign cell ids to each road segemnt, return df of roads with grid IDs assigned
    road_options = make_grid(df_roads, df_services)
    # init results df
    results = init_results()
    # update results for baseline query @ t=-1, also imports dmeographic data as demo
    results, demo = bau_query(results)
    # update results for query at point of hazard (t=0)
    results = hazard_query(results, demo, df_roads, df_services)
    # init df of options to restore
    df_options = init_options(df_services, road_options)
    # greedy optimise
    results = init_greedy(df_options, results, demo, road_options)
    # save results
    results.to_csv(file_path)
        

def make_grid(df_roads, df_services):
    '''
    Make a set of grids based on boundary of the origin blocks file
    return geodataframe
    '''
    print('MAKING GRID OF {}'.format(context['city'].upper()))
    # import origins for making the grid
    orig_df = gpd.GeoDataFrame.from_postgis("SELECT * FROM block", db['con'], geom_col='geom')
    # Save origins as .shp
    #orig_df.to_file(r'/homedirs/man112/monte_christchurch/results/recovery/origins.shp')
    # get boundary for grids
    xmin,ymin,xmax,ymax = orig_df.total_bounds
    # get number of grids on one side-length
    n_cells= np.sqrt(grids)
    # determine cell size
    cell_size = (xmax-xmin)/n_cells
    # set projection
    crs = "EPSG:4326"
    #init list for cell geom
    grid_cells = []
    # loop through x and y for making grid geom
    for x0 in np.arange(xmin, xmax+cell_size, cell_size ):
        for y0 in np.arange(ymin, ymax+cell_size, cell_size):
            x1 = x0-cell_size
            y1 = y0+cell_size
            grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))
    # turn cells into a geodataframe
    cells = gpd.GeoDataFrame(grid_cells, columns=['geometry'], crs=crs)
    # add a cell id to each cell
    cells['cell_id'] = np.arange(1,len(cells)+1)
    # save cells as a .shp
    cells.to_file(r'/homedirs/man112/monte_christchurch/results/recovery/grid_{}.shp'.format(grids))
    # import roads
    edges = gpd.read_file(r'/homedirs/man112/monte_christchurch/data/{}/road_edges/edges.shp'.format(context['city']))
    if context['city'] == 'christchurch':
        edges.rename(columns={'from_':'from'}, inplace=True)
    # only overlay roads identified as non-operable
    df_roads = edges.iloc[df_roads.index]
    # merge cells and un-usable roads to assign each road segment with a grid ID number
    road_options = gpd.overlay(df_roads, cells, how='union')
    # save roads as shp
    road_options.to_file(r'/homedirs/man112/monte_christchurch/results/recovery/road_options.shp')
    # save destinations as a shp
    df_dests = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations WHERE dest_type='{}'".format(optimise_service), db['con'], geom_col='geom')
    df_dests.to_file(r'/homedirs/man112/monte_christchurch/results/recovery/all_services.shp')
    closed_services = df_dests[df_dests['id'].isin(list(df_services.index))]
    closed_services.to_file(r'/homedirs/man112/monte_christchurch/results/recovery/service_options.shp')
    #return road segments with cell IDs on them
    return(road_options)

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

def init_greedy(df_options, results, demo, road_options):
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
        iso = 0
        temp_results = [time, 
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['total_pop'])),
        iso,
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['white'])),
        iso,
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['indigenous'])),
        iso,
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['asian'])),
        iso,
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance']), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['polynesian'])),
        iso, restore_type, restore_id]
    else:
        temp_results = [time, 
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['total_pop'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['total_pop'].sum(),
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['white'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['white'].sum(),
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['indigenous'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['indigenous'].sum(),
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['asian'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['asian'].sum(),
        ineq.kolmpollak.ede(a=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)]['distance'].dropna()), epsilon=-0.5, kappa=None, weights=list(baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)].dropna()['polynesian'])),
        baseline_nearest[baseline_nearest['dest_type']=='{}'.format(optimise_service)][np.isnan(baseline_nearest['distance'])]['polynesian'].sum(), restore_type, restore_id]
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

    df.to_csv(r'/homedirs/man112/osm_data/updates/update.csv', header=False, index=False)
    # init_osrm.py/.sh
    sim = True
    init_osrm.main(sim, state, context)

    # re query
    return()

def random_sim(state, hazard_type, optimise_service):
    '''main'''
    #initialise config
    print('SIUMLATING RANDOM {} EVENT'.format(hazard_type.upper()))
    db, context = cfg_init(state)
    exposure_df = initialise_hazard.open_hazard(hazard_type, db, context)
    # get gpd df of roads with inundation depths and damage bands
    exposed_roads = drop_roads.open_hazard(hazard_type, db, context)
    df_roads = gpd.read_file(r'/homedirs/man112/monte_christchurch/data/{}/road_edges/edges.shp'.format(context['city']))
    df_roads = df_roads.drop(columns=['geometry'])
    if context['city'] == 'christchurch':
        df_roads.rename(columns={'from_':'from'}, inplace=True)
    df_dests = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations", db['con'], geom_col='geom')
    df_dests = df_dests.drop(columns=['geom'])
    df_dests = df_dests.set_index('id')
    #close destinations
    dest_ids = dests_to_drop(exposure_df, hazard_type, db, context)

    df_dests = df_dests.iloc[dest_ids]
    df_dests = df_dests[df_dests['dest_type']==optimise_service]

    #drop roads
    damage_level = np.random.uniform(size=len(exposed_roads))
    exposed_roads['damage'] = damage_level
    exposure_level = ['low', 'med', 'high']

    if hazard_type in ['tsunami', 'hurricane']:
        damage_threshold = [0.9, 0.6, 0.2]
    elif hazard_type == 'liquefaction':
        damage_threshold = [0.95, 0.7, 0.25]
    elif hazard_type == 'multi':
        damage_threshold = [0.85, 0.55, 0.15, 0.05]

    conditions = [
    (exposed_roads['exposure'] == exposure_level[0]) & (exposed_roads['damage'] >= damage_threshold[0]),
    (exposed_roads['exposure'] == exposure_level[1]) & (exposed_roads['damage'] >= damage_threshold[1]),
    (exposed_roads['exposure'] == exposure_level[2]) & (exposed_roads['damage'] >= damage_threshold[2]),
    (exposed_roads['exposure'] == exposure_level[0]) & (exposed_roads['damage'] <= damage_threshold[0]),
    (exposed_roads['exposure'] == exposure_level[1]) & (exposed_roads['damage'] <= damage_threshold[1]),
    (exposed_roads['exposure'] == exposure_level[2]) & (exposed_roads['damage'] <= damage_threshold[2])]

    values = ['True','True','True','False','False','False']
    exposed_roads['closed'] = np.select(conditions, values)

    roads_effected = exposed_roads[(exposed_roads['closed'] == 'True')]
    roads_effected = roads_effected.drop(columns=['geometry'])

    return(roads_effected, df_dests)

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
    baseline_nearest['id_orig'] = baseline_nearest['id_orig'].astype(float)
    # merge with demo data
    baseline_nearest = pd.merge(baseline_nearest, demo, on=["id_orig"])
    # change col name
    baseline_nearest['total_pop'] = baseline_nearest['total']
    baseline_nearest = baseline_nearest.drop(columns=['latino', 'african_american'])
    return(baseline_nearest)

if __name__ == "__main__":
    recover()