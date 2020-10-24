'''
Takes raw and process results and formats them for the access-resilience app
'''

from config import *

state = 'wa' #('ch', 'tx', 'wa')
db, context = cfg_init(state)

def main():
    format_blocks()


####################################################################################################################################################################################
''' SHP to GEOJSON '''
####################################################################################################################################################################################
def format_blocks():
    ''' Convert meshblock shapefile to geojson '''
    blocks = gpd.read_sql('SELECT * FROM block', db['con'])

    blocks.to_file("plotly/{}_block.geojson".format(state), driver='GeoJSON')









####################################################################################################################################################################################
''' Destinations to CSV '''
####################################################################################################################################################################################















####################################################################################################################################################################################
''' ECDF CSV '''
####################################################################################################################################################################################











####################################################################################################################################################################################
''' Nearest_Dist to CSV '''
####################################################################################################################################################################################














if __name__ == '__main__':
    main()
