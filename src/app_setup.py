'''
Takes raw and process results and formats them for the access-resilience app
'''

from config import *
import shapely

state = input("Enter State (ch, wa, tx): ") #('ch', 'tx', 'wa')
db, context = cfg_init(state)

def main():
    job = int(input('Would you like to: (1)Format Blocks, (2)Format Edges, (3)Format Destinations, (4)All: '))
    if job == 1:
        format_blocks()
    elif job == 2:
        format_edges()
    elif job == 3:
        format_dests()
    elif job == 4:
        format_blocks()
        format_edges()
        format_dests()

####################################################################################################################################################################################
''' BLOCKS to GEOJSON '''
####################################################################################################################################################################################
def format_blocks():
    ''' Convert meshblock shapefile to geojson '''

    if state == 'ch':
        block_id = 'sa12018_v1'
    else:
        block_id = 'geoid10'

    #creates df of geoid10 indexes
    sql = "SELECT geom, {} FROM block".format(block_id)
    blocks = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')

    blocks[block_id] = blocks[block_id].astype(int)
    blocks = blocks.set_index(block_id)

    blocks = blocks.to_crs("EPSG:4326")

    # blocks.to_file("plotly/{}_block.geojson".format(state), index=True, driver='GeoJSON')
    with open("plotly/{}_block.geojson".format(state), "wt") as tf:
        tf.write(blocks.to_json())

####################################################################################################################################################################################
''' EDGES to GEOJSON '''
####################################################################################################################################################################################
def format_edges():
    ''' Convert edges shapefile to geojson '''
    city = context['city']
    from_col = 'from'
    if state == 'ch':
        from_col = 'from_'
        hazard = int(input('What Hazard: (1)Tsunami, (2)Liquefaction, (3)Multi: '))
        if hazard == 1:
            hazard = 'tsunami'
        elif hazard == 2:
            hazard = 'liquefaction'
        elif hazard == 3:
            hazard = 'multi'
    elif state == 'wa':
        hazard = 'liquefaction'
    elif state =='tx':
        hazard = 'hurricane'

    edges = gpd.read_file(r'data/{}/road_edges/edges.shp'.format(city))
    updates = pd.read_csv(r'data/{}_{}_update.csv'.format(state, hazard), names=["from_", "to", "speed"])
    from_ids = updates['from_'].tolist()
    to_ids = updates['to'].tolist()
    edges = edges.to_crs("EPSG:4326")
    edges = edges[['osmid', from_col, 'to', 'geometry']]
    edges = edges[edges[from_col].isin(from_ids) & edges['to'].isin(to_ids)]


    lats = []
    lons = []
    names = []
    for feature in edges.geometry:
        if isinstance(feature, shapely.geometry.linestring.LineString):
            linestrings = [feature]
        elif isinstance(feature, shapely.geometry.multilinestring.MultiLineString):
            linestrings = feature.geoms
        else:
            continue
        for linestring in linestrings:
            x, y = linestring.xy
            lats = np.append(lats, y)
            lons = np.append(lons, x)
            lats = np.append(lats, None)
            lons = np.append(lons, None)

    np.save(r'plotly/{}_{}_lat_edges'.format(state, hazard), lats)
    np.save(r'plotly/{}_{}_lon_edges'.format(state, hazard), lons)



####################################################################################################################################################################################
''' Destinations to CSV '''
####################################################################################################################################################################################
def format_dests():
    ''' Saves dest lat and lons in a CSV '''
    dests = gpd.read_postgis('SELECT * FROM destinations', db['con'])
    dests['lon'] = dests.geom.centroid.x
    dests['lat'] = dests.geom.centroid.y
    dests = dests.drop(columns=['geom', 'id'])
    dests.to_csv(r'plotly/{}_destinations.csv'.format(state))













####################################################################################################################################################################################
''' ECDF CSV '''
####################################################################################################################################################################################











####################################################################################################################################################################################
''' Nearest_Dist to CSV '''
####################################################################################################################################################################################














if __name__ == '__main__':
    main()
