'''
Takes raw and process results and formats them for the access-resilience app
'''

from config import *

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
    city = context['city'])
    edges = gpd.read_file(r'data/{}/road_edges/edges.shp'.format(city))

    edges = edges.to_crs("EPSG:4326")

    edges = edges[['osmid', 'geometry']]

    count = 0
    for id in edges['osmid']:
        if ('[' in id) == True:
            edges['osmid'].iloc[count] = id.split()[0][1:-1]
        count += 1

    edges['osmid'] = edges['osmid'].astype(int)
    edges = edges.set_index('osmid')

    #edges.to_file("plotly/{}_edges.geojson".format(state), driver='GeoJSON')
    with open("plotly/{}_edges.geojson".format(state), "wt") as tf:
        tf.write(edges.to_json())


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
