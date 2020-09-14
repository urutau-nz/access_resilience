'''
Clip osm edges with hazards
get from and to IDs
Save to a csv
'''

from config import *
import init_osrm

def close_rd(exposed_roads, state, hazard_type, db, context):
    #set hypothetical damage level for each building
    damage_level = np.random.uniform(size=len(exposed_roads))
    exposed_roads['damage'] = damage_level
    exposure_level = ['low', 'med', 'high']

    if hazard_type == 'tsunami':
        damage_threshold = [0.8, 0.45, 0.05]
    elif hazard_type == 'liquefaction':
        damage_threshold = [0.95, 0.75, 0.4]

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

    # make list of from and to OSM IDs
    df = pd.DataFrame()
    df['from_osmid'] = roads_effected['from_']
    df['to_osmid'] = roads_effected['to']

    # reverse way
    df_inv = pd.DataFrame()
    df_inv['from_osmid'] = roads_effected['to']
    df_inv['to_osmid'] = roads_effected['from_']

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

def open_hazard(hazard_type, db, context):
    '''opens and formats hazard'''
    #import edges
    edges = gpd.read_file(r'data/road_edges/edges.shp')

    if hazard_type == 'liquefaction':
        filename = '/homedirs/dak55/monte_christchurch/data/christchurch/hazard/liquefaction_vulnerability.shp'
        hazard = gpd.read_file(filename)
        #exclude unnecessary columns
        hazard = hazard[['Liq_Cat', 'geometry']]
        #catagorize all exposure as no, low, medium or high
        hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Possible'], 'Medium Liquefaction Vulnerability')
        hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Unlikely'], 'Low Liquefaction Vulnerability')


    elif hazard_type == 'tsunami':
        #open raster file
        hazard = rio.open('/homedirs/dak55/monte_christchurch/data/christchurch/hazard/tsunami.tif')
        #get x,y point values of all dests
        road_coords = [(x,y) for x, y in zip(edges.centroid.x, edges.centroid.y)]
        #find corresponding inundation depth for each dest
        edges['inundation_depth'] = [x[0] for x in tsu.sample(road_coords)]
        #low, medium, high catagories for discrete fragility curve
        bands = [(0, 0.5), (0.5, 2), (2, 1000)]
        exposure_level = ['low', 'med', 'high']
        conditions = [(edges['inundation_depth'] <= bands[0][1]), (edges['inundation_depth'] > bands[1][0]) & (edges['inundation_depth'] <= bands[1][1]), (edges['inundation_depth'] > bands[2][0])]
        edges['exposure'] = np.select(conditions, exposure_level)

    return(edges)
