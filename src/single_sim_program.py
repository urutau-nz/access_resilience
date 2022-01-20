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


state = 'tx'
hazards = ['hurricane']



def main_function(state):
    '''main'''
    #initialise config
    db, context = cfg_init(state)
    # reset osrm network
    sim = False
    init_osrm.main(sim, state, context)
    # get baseline distances (nearest)
    print('Beginning Baseline Query')
    baseline_distances = query_baseline(state)
    baseline_distances['hazard'] = 'base'
    # init sim
    for hazard_type in hazards:
        #intilise hazard for dests, returns df of dests with damage band
        exposure_df = initialise_hazard.open_hazard(hazard_type, db, context)
        # returns gdf of roads under different damage bands
        exposed_roads = drop_roads.open_hazard(hazard_type, db, context)
        # init dist matrix
        nearest_matrix = pd.DataFrame(columns=['id_orig', 'distance', 'dest_type'])
        # read in full road network
        df_roads = gpd.read_file(r'/homedirs/man112/monte_christchurch/data/{}/road_edges/edges.shp'.format(context['city']))
        df_roads['closed'] = False
        df_roads = df_roads.drop(columns=['geometry'])
        # rename chch col due to bug
        if context['city'] == 'christchurch':
            df_roads.rename(columns={'from_':'from'}, inplace=True)
        # read in dests
        df_dests = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations", db['con'], geom_col='geom')
        gdf_dests = df_dests
        gdf_dests['closed'] = False
        df_dests = df_dests.drop(columns=['geom'])
        df_dests = df_dests.set_index('id')
        df_dests['closed'] = False
        #close destinations
        dest_ids = dests_to_drop(exposure_df, hazard_type, db, context)
        #drop roads and modify network, return roads_effected as closed roads
        exposed_roads, roads_effected = drop_roads.close_rd(exposed_roads, state, hazard_type, db, context, sim_num=0)
        # save roads effected to file
        roads_effected.to_postgis('temp_roads_{}'.format(hazard_type), db['engine'], if_exists='replace', dtype={'geometry': Geometry('LINESTRING')})
        roads_effected = roads_effected.to_crs(3395)
        length = roads_effected.length.sum()
        # save dests
        gdf_dests = gdf_dests.set_index('id')
        gdf_dests['closed'].iloc[dest_ids] = True
        gdf_dests.to_postgis('temp_dests_{}'.format(hazard_type), db['engine'], if_exists='replace', dtype={'geometry': Geometry('POINT')})
        #requery
        distance_matrix = query_points(dest_ids, db, context)
        #find new nearest_service matrix
        nearest_service = find_nearest_service(distance_matrix, dest_ids, db, context)
        nearest_service['hazard'] = hazard_type
        # append to baseline dists
        baseline_distances = baseline_distances.append(nearest_service)
        # print road length
        print('Roads closed for {} under {}: {}m'.format(context['city'], hazard_type, length))
    #saving data
    baseline_distances.to_sql('temp_distances', db['engine'], if_exists='replace')
        



def query_baseline(state):
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
    #write_to_postgres(baseline_nearest, db, 'baseline_nearest', indices=False)
    return(baseline_nearest)


main_function(state)
