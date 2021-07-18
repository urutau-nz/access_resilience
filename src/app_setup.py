'''
Takes raw and process results and formats them for the access-resilience app
'''

from numpy.core.shape_base import block
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

    blocks = blocks.sort_values(by=block_id, axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')

    blocks[block_id] = blocks[block_id].astype(int).tolist()

    if block_id == 'geoid10':
        #opening total population stats for each block
        sql = """SELECT "H7X001", geoid10 FROM demograph"""
        demo_df = pd.read_sql(sql, db['con'])
        #orders by geoid and sets it as the index
        demo_df = demo_df.sort_values(by=block_id, axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')
        zero_pop = demo_df.loc[demo_df['H7X001'] == 0]
        zero_pop_id_int = zero_pop[block_id].astype(int).tolist()
        blocks = blocks[~blocks[block_id].isin(zero_pop_id_int)]
    else:
        #opening total population stats for each block
        sql = """SELECT "population", gid FROM census_18"""
        demo_df = pd.read_sql(sql, db['con'])
        demo_df = demo_df.rename(columns={'gid':block_id})
        #orders by geoid and sets it as the index
        demo_df = demo_df.sort_values(by=block_id, axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')
        zero_pop = demo_df.loc[demo_df['population'] == 0]
        zero_pop = zero_pop.dropna()
        zero_pop_id_int = zero_pop[block_id].astype(int).tolist()
        blocks = blocks[~blocks[block_id].isin(zero_pop_id_int)]

    blocks[block_id] = blocks[block_id].astype(int)
    blocks = blocks.rename(columns={block_id:'id_orig'})
    blocks = blocks.set_index('id_orig')

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
        city = 'christchurch'
        from_col = 'from_'
        hazard = int(input('What Hazard: (1)Tsunami, (2)Liquefaction, (3)Multi: '))
        if hazard == 1:
            hazard = 'tsunami'
        elif hazard == 2:
            hazard = 'liquefaction'
        elif hazard == 3:
            hazard = 'multi'
    elif state == 'wa':
        city = 'seattle'
        hazard = 'liquefaction'
    elif state =='tx':
        city = 'houston'
        hazard = 'hurricane'

    edges = gpd.read_file(r'data/{}/road_edges/edges.shp'.format(city))
    updates = pd.read_csv(r'data/{}_{}_update.csv'.format(state, hazard), names=['from_', "to", "speed"])
    from_ids = updates['from_'].tolist()
    to_ids = updates['to'].tolist()
    edges = edges.to_crs("EPSG:4326")
    edges = edges[['osmid', from_col, 'to', 'geometry']]
    edges = edges[edges[from_col].isin(from_ids) & edges['to'].isin(to_ids)]
    edges = edges.drop(columns=['osmid', from_col, 'to'])
    with open("plotly/{}_{}_road.geojson".format(city, hazard), "wt") as tf:
        tf.write(edges.to_json())

    # m_edges = edges.to_crs("+proj=eck4 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")
    # road_length = m_edges.geometry.length.sum()/1000
    # print('{} Damaged Road Length in a {}: {}km'.format(city, hazard, np.round(road_length, 1)))


    # lats = []
    # lons = []
    # names = []
    # for feature in edges.geometry:
    #     if isinstance(feature, shapely.geometry.linestring.LineString):
    #         linestrings = [feature]
    #     elif isinstance(feature, shapely.geometry.multilinestring.MultiLineString):
    #         linestrings = feature.geoms
    #     else:
    #         continue
    #     for linestring in linestrings:
    #         x, y = linestring.xy
    #         lats = np.append(lats, y)
    #         lons = np.append(lons, x)
    #         lats = np.append(lats, None)
    #         lons = np.append(lons, None)

    # np.save(r'plotly/{}_{}_lat_edges'.format(state, hazard), lats)
    # np.save(r'plotly/{}_{}_lon_edges'.format(state, hazard), lons)



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
