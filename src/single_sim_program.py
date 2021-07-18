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
service = 'medical_clinic'
hazard_type = 'hurricane'

# pull in osm network, destinations, origins, roads
# overlay hazard
# modify osm network
# query to new list of services
# save roads and services to sql
# save blocks with distance to sql


def main_function(state):
    '''main'''
    #initialise config
    db, context = cfg_init(state)
    # reset osrm network
    sim = False
    init_osrm.main(sim, state, context)
    #print('Beginning Baseline Query')
    #intilise hazard, df to save and find dests exposed at each fragility level
    exposure_df = initialise_hazard.open_hazard(hazard_type, db, context)
    # get gpd df of roads with inundation depths and damage bands
    exposed_roads = drop_roads.open_hazard(hazard_type, db, context)
    nearest_matrix = pd.DataFrame(columns=['id_orig', 'distance', 'dest_type', 'sim_num'])
    #df_roads = pd.DataFrame(columns=['from_osmid', 'to_osmid', 'edge_speed', 'sim_num'])
    df_roads = gpd.read_file(r'/homedirs/man112/monte_christchurch/data/{}/road_edges/edges.shp'.format(context['city']))
    df_roads['sim_num'] = 0
    df_roads['num_closed'] = 0
    df_roads = df_roads.drop(columns=['geometry'])
    if context['city'] == 'christchurch':
        df_roads.rename(columns={'from_':'from'}, inplace=True)
    #df_dests = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations WHERE dest_type IN ('medical_clinic', 'primary_school', 'supermarket')", db['con'], geom_col='geom')
    df_dests = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations", db['con'], geom_col='geom')
    gdf_dests = df_dests
    gdf_dests['closed'] = False
    df_dests = df_dests.drop(columns=['geom'])
    df_dests = df_dests.set_index('id')
    df_dests['num_closed'] = 0
    #open demographic data
    #demo = demographic_data(baseline_nearest, db, context)
    #number of iterations for the simulation
    nsim = 1
    df_dests['sims_run'] = nsim
    for i in tqdm(range(nsim)):
        sim_num = i
        #close destinations
        dest_ids = dests_to_drop(exposure_df, hazard_type, db, context)
        #df_dests.loc[dest_ids,'num_closed'] += 1
        #drop roads
        exposed_roads, roads_effected = drop_roads.close_rd(exposed_roads, state, hazard_type, db, context, sim_num)
        #append list of broken roads
        #df_roads['num_closed'].iloc[list(roads_effected.index)] += 1
        #df_roads['sim_num'] += 1
        #requery
        distance_matrix = query_points(dest_ids, db, context)
        #find new nearest_service matrix
        nearest_service = find_nearest_service(distance_matrix, dest_ids, db, context)
        #save sim number
        nearest_service['sim_num'] = i
        #saving data
        nearest_matrix = pd.concat([nearest_matrix, nearest_service], ignore_index=True)
        nearest_matrix = nearest_matrix[nearest_matrix['dest_type']=='{}'.format(service)]
        sql = "SELECT * FROM block"
        orig_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
        if state == 'ch':
            orig_df['id_orig'] = orig_df['sa12018_v1']
        else:
            orig_df['id_orig'] = orig_df['geoid10']
        temp_blocks = pd.merge(orig_df, nearest_matrix, on='id_orig', how='outer')
        temp_blocks['distance'] = temp_blocks['distance'].fillna(-1)
        temp_blocks.to_postgis('temp_blocks', db['engine'], if_exists='replace', dtype={'geometry': Geometry('POLYGON')})
        # save roads
        roads_effected.to_postgis('temp_roads', db['engine'], if_exists='replace', dtype={'geometry': Geometry('LINESTRING')})
        roads_effected = roads_effected.to_crs(3395)
        length = roads_effected.length.sum()
        print(length)
        # save dests
        gdf_dests = gdf_dests.set_index('id')
        gdf_dests['closed'].iloc[dest_ids] = True
        gdf_dests = gdf_dests[gdf_dests['dest_type']=='{}'.format(service)]
        gdf_dests.to_postgis('temp_dests', db['engine'], if_exists='replace', dtype={'geometry': Geometry('POINT')})
        
    #code.interact(local=locals())
    #save matrix to sql for analysis later
    # save_matrix = True
    # if save_matrix == True:
    #     # nearest_matrix
    #     write_to_postgres(nearest_matrix, db, 'nearest_distance_{}'.format(hazard_type), indices=False)
    #     # services
    #     write_to_postgres(df_dests, db, 'closed_services_{}'.format(hazard_type), indices=False)
    #     # roads
    #     write_to_postgres(df_roads, db, 'closed_roads_{}'.format(hazard_type), indices=False)
    #     print('Saved nearest distance matrix to SQL')
    # else:
    #     plotting(baseline_nearest, nearest_matrix, demo, db, context, hazard_type, nsim)
    #     #having a gander at some results
    #     #update something horribly wrong is going on here
    #     ede_matrix = pd.DataFrame()
    #     for j in nearest_matrix.sim_num.unique():
    #         subset = nearest_matrix.loc[nearest_matrix['sim_num'] == j]
    #         ede_df = kp_ede_main(demo, subset, context)
    #         ede_df['sim_num'] = j
    #         ede_matrix = pd.concat([ede_matrix, ede_df], ignore_index=True)

    #     sup = ede_matrix.loc[(ede_matrix['population_group'] == 'total') & (ede_matrix['dest_type'] == 'medical_clinic')]
    #     mean = sup.ede.mean()
    #     print('mean medical_centers = {}\n'.format(mean))
    #     tenth = sup.ede.quantile(0.1)
    #     print('10th percentile = {}\n'.format(tenth))
    #     ninety = sup.ede.quantile(0.9)
    #     print('90th percentile = {}\n'.format(ninety))



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

    write_to_postgres(baseline_nearest, db, 'baseline_nearest', indices=False)


main_function(state)

#calculate ede's
#ede_df = kp_ede_main(demo, nearest_service, context)
#ede_df.to_csv('results/ede_after.csv')

#plotting(nearest_service, demo, db, context)
#
