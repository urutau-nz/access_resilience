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
db, context = cfg_init(state)

def main():
    recovery_info = pd.read_csv(r'/homedirs/man112/monte_christchurch/results/recovery/recovery_supermarket_total_pop.csv')
    services_out = gpd.read_file(r'/homedirs/man112/monte_christchurch/results/recovery/service_options.shp')
    roads_out = gpd.read_file(r'/homedirs/man112/monte_christchurch/results/recovery/road_options.shp')
    # set up results
    orig = gpd.GeoDataFrame.from_postgis("SELECT * FROM block", db['con'], geom_col='geom')
    # Baseline Query
    t = -1
    df = bau_query(t)
    # t = 0 query
    t = 0
    # set dests
    dest_ids = services_out['id'].tolist()
    # get roads to close based on grid ids left in df_options
    temp_roads = roads_out
    # updates OSRM server with closed roads
    close_rd(temp_roads, db, context)
    # test option by evaluating access and isolation change    
    distance_matrix = query_points(dest_ids, db, context, optimise_service)
    # get nearest
    baseline_nearest = find_nearest_service(distance_matrix, dest_ids, db, context)
    # add to dst    
    df['distance_{}'.format(t)] = baseline_nearest['distance']
    for t in tqdm(np.arange(1,recovery_info['time'].max()+1)):
        # reset osrm server
        init_osrm.main(False, state, context)
        time_id = int(t+1)
        restore_type = recovery_info['restore_type'].iloc[time_id]
        restore_id = recovery_info['restore_id'].iloc[time_id]
        if restore_type == 'road':
            roads_out = roads_out[roads_out['cell_id'] != restore_id]
        elif restore_type == 'service':
            services_out = services_out[services_out['id'] != restore_id]
            dest_ids = services_out['id'].tolist()
        # updates OSRM server with closed roads
        close_rd(roads_out, db, context)
        # test option by evaluating access and isolation change    
        distance_matrix = query_points(dest_ids, db, context, optimise_service)
        # get nearest
        baseline_nearest = find_nearest_service(distance_matrix, dest_ids, db, context)
        # add to dst    
        df['distance_{}'.format(t)] = baseline_nearest['distance']
    df['geom'] = orig['geom']
    gdf = gpd.GeoDataFrame(df, geometry='geom')
    gdf.to_file(r'/homedirs/man112/monte_christchurch/results/recovery/recovery_distances.shp')




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

def bau_query(t):
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
    baseline_nearest.rename(columns={'distance':'distance_{}'.format(t)}, inplace=True)
    return(baseline_nearest)


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

main()