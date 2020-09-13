'''
Clip osm edges with hazards
get from and to IDs
Save to a csv
'''

from config import *
import init_osrm

def close_rd(state, hazard_type, db, context):
    #import edges
    edges = gpd.read_file(r'data/road_edges/edges.shp')

    #import hazard
    hazard = open_hazard(hazard_type, db, context)

    #clip roads to hazards
    roads_effected = gpd.clip(edges, hazard)

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


def open_hazard(hazard_type, db, context):
    '''opens and formats hazard'''

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

    return(hazard)
