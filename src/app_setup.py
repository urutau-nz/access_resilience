'''
Takes raw and process results and formats them for the access-resilience app
'''

from config import *

state = input("Enter State (ch, wa, tx): ") #('ch', 'tx', 'wa')
db, context = cfg_init(state)

def main():
    job = input('Would you like to: (1)Format Blocks, (2)Format Edges, (3)Format Destinations, (4)All: ' )
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
    blocks = gpd.read_postgis('SELECT * FROM block', db['con'])

    blocks = blocks.to_crs("EPSG:4326")

    blocks.to_file("plotly/{}_block.geojson".format(state), driver='GeoJSON')

####################################################################################################################################################################################
''' EDGES to GEOJSON '''
####################################################################################################################################################################################
def format_edges():
    ''' Convert edges shapefile to geojson '''
    edges = gpd.read_file(r'data/{}/road_edges/edges.shp'.format(context['city']))

    edges = edges.to_crs("EPSG:4326")

    edges.to_file("plotly/{}_edges.geojson".format(state), driver='GeoJSON')


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
