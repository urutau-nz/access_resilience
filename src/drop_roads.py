'''
Clip osm edges with hazards
get from and to IDs
Save to a csv
'''

from config import *

#import edges
edges = gpd.read_file(r'data/road_edges/edges.shp')

#import hazard
#hazard = gpd.read_file(r'data/esl_aep1_slr150_Project.shp')

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
