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
optimise_service = 'supermarket'
db, context = cfg_init(state)


def main():
    #CHCH QUERY 1,2,3
    # get blocks
    orig = gpd.GeoDataFrame.from_postgis("SELECT * FROM block_06", db['con'], geom_col='geom')
    # get destinations
    dest_df = gpd.read_file(r'data/dests/chch_dests.csv')
    dest_df['id'] = np.arange(0,len(dest_df))
    # Loop though events
    t=-1
    df = bau_query(t)
    df['time'] = t
    #df.to_csv('./data/chch_distances.csv'.format(state))
    t = 0
    # set dests
    dest_ids = dest_df[dest_df['open']=='FALSE']['id'].tolist()
    dest_ids = dest_ids.append([40,41,42])
    # get roads to close based on grid ids left in df_options
    temp_roads = pd.read_csv(r'data/dests/chch_blockedRoads.csv')
    # updates OSRM server with closed roads
    close_rd(temp_roads, db, context)
    # test option by evaluating access and isolation change    
    distance_matrix = query_points(dest_ids, db, context, optimise_service)
    # get nearest
    baseline_nearest = distance_matrix.loc[distance_matrix.groupby('id_orig')['distance'].idxmin()]
    baseline_nearest['time'] = t
    t=1
    distances = df.append(baseline_nearest)
    dest_ids = dest_df[dest_df['open']=='FALSE']['id'].tolist()
    distance_matrix = query_points(dest_ids, db, context, optimise_service)
    # get nearest
    baseline_nearest = distance_matrix.loc[distance_matrix.groupby('id_orig')['distance'].idxmin()]
    baseline_nearest['time'] = t
    distances = distances.append(baseline_nearest)

    # add to csv
    gdf = gpd.read_file(r'data/dests/chch_meshblocks.shp')#'chch_meshblocks.shp')
    # cut down for shapefile
    mb = gdf[['SA12018_V1', 'geometry']]
    # save to file
    mb['SA12018_V1'] = mb['SA12018_V1'].astype(int)
    mb = mb.set_index('SA12018_V1')
    mb = mb.to_crs("EPSG:4326")
    # blocks.to_file("plotly/{}_block.geojson".format(state), index=True, driver='GeoJSON')
    #with open("edge_block.geojson", "wt") as tf:
        #tf.write(mb.to_json())
    # make meshblock data csv
    df = pd.DataFrame()
    # set id
    df['SA12018_V1'] = list(gdf['SA12018_V1'])*6*3
    df = df.sort_values(by='SA12018_V1')
    df = df.reset_index(drop=True)
    # set race column
    df['demographic'] = ['all', 'euro', 'maori', 'pacific', 'asian', 'meela']*len(gdf)*3
    df = df.sort_values(by='demographic')
    # add population counts
    df['population'] = list(gdf['C06_CURPop'])*3 + list(gdf['C06_Ethn_3'])*3 + list(gdf['C06_Ethnic'])*3 + list(gdf['C06_Ethn_1'])*3 + list(gdf['C06_Ethn_4'])*3 + list(gdf['C06_Ethn_2'])*3
    # add timesteps
    df['timestep'] = list(np.arange(-1,2)*6*len(mb)
    # add distances
    df['distance'] = None
    df['id_dest'] = None
    df = df.reset_index(drop=True)
    #distance = distance.reset_index(drop=True)
    # get the nearest
    distance_near = distances.loc[distances.groupby(['id_orig','time'])['distance'].idxmin()]
    # merge with demographic
    df_merged = pd.merge(distance_near, df, how='right',on=['id_orig', 'SA12018_V1'])

    df_merged.to_csv('./data/chc_distances_choro.csv')
    print('saved')


# # get the nearest
# distance_near = distances.loc[distances.groupby(['id_orig','time'])['distance'].idxmin()]
# # merge with demographic
# df_merged = pd.merge(distance_near, df, how='left',left_on='id_orig', right_on='SA12018_V1')

# df_merged.to_csv('./data/chc_distances_choro.csv')


    




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
    dest_ids = [40,41,42]
    #gets all network distances
    baseline_distance = query_points(dest_ids, db, context, optimise_service)
    #baseline_distance.to_csv('./data/edge_distances_dests.csv'.format(state))
    # refines for just nearest distance to each service type
    baseline_nearest = baseline_distance.loc[baseline_distance.groupby('id_orig')['distance'].idxmin()]
    # baseline_nearest = find_nearest_service(baseline_distance, dest_ids, db, context)
    # baseline_nearest = baseline_nearest.reset_index()
    # # imports demographic data
    # demo = demographic_data(baseline_nearest, db, context)
    # demo.sort_values(by=['id_orig'], inplace=True, ignore_index=True)
    # baseline_nearest = combine_demo_dist(baseline_nearest, demo, True)
    # baseline_nearest.rename(columns={'distance':'distance_{}'.format(t)}, inplace=True)
    return(baseline_nearest)


def close_rd(df_roads, db, context):
    state = 'ch'
    # make list of from and to OSM IDs
    df = pd.DataFrame()
    df['from_osmid'] = df_roads['from_osmid']
    df['to_osmid'] = df_roads['to_osmid']

    # reverse way
    df_inv = pd.DataFrame()
    df_inv['from_osmid'] = df_roads['to_osmid']
    df_inv['to_osmid'] = df_roads['from_osmid']

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