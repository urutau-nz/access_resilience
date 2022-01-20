'''
Adding various types of destinations. Note that filenames etc will have to be changed. More suited to running on a line by line basis
This is mostly just a mess of me trying to get the crs to line up when appending a new shp of dests to the existing destinations table
'''

from config import *
from geoalchemy2 import Geometry, WKTElement





'''
Anderson 09/09/2021
uploading csv dests into sql
'''
def append_csv_dests(state):
    '''opens and appends new dest'''
    #initialize db connection
    db, context = cfg_init(state)
    filename = '/homedirs/man112/monte_christchurch/data/christchurch/christchurch_destinations.csv'
    df = pd.read_csv(filename, encoding = "ISO-8859-1")
    #convert to gdf and format to send to sql
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))
    gdf.drop(['lat', 'lon'], axis=1, inplace=True)
    gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4326))
    gdf.crs = "EPSG:4326"
    gdf.drop('geometry', 1, inplace=True)
    gdf['id'] = np.arange(0,len(gdf))
    gdf.to_sql('destinations', db['engine'], index=False, dtype={'geom': Geometry(geometry_type='POINT', srid= 4326)})


append_csv_dests('ch')











# #for downtown:
# def add_downtown(state):
#     '''adds a point for downtown, lat and lon must be specified'''
#     df = pd.DataFrame(columns=['id', 'dest_type', 'name', 'Latitude', 'Longitude'])
#     df['id'] = list(range(len(df)))
#     df.loc[0] = ['downtown', 'downtown', lat, long]
#     #then do same with gpd as below



# def append_csv_dests(state):
#     '''opens and appends new dest'''
#     #initialize db connection
#     db, context = cfg_init(state)
# filename = '/homedirs/dak55/monte_christchurch/data/seattle/demograph/demo_sea.csv'
# df = pd.read_csv(filename, encoding = "ISO-8859-1")

#         #extraact and format data so it is the same form as destinations
#     df = df[['Org Name', 'Latitude', 'Longitude']]
#     df['dest_type'] = 'secondary_school'
#     df = df.rename(columns={'Org Name':'name'})
#     df.sort_values(inplace=True, by=['name'])
#     df.reset_index(inplace=True, drop=True)
#     df['id'] = list(range(len(df)))
#     cols = ['id', 'dest_type', 'name', 'Latitude', 'Longitude']
#     df = df[cols]

#     #convert to gdf and format to send to sql
#     gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
#     gdf.drop(['Latitude', 'Longitude'], axis=1, inplace=True)
# gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4269))
# gdf.crs = "EPSG:4269"
# gdf.drop('geometry', 1, inplace=True)
#     gdf.to_sql('destinations', db['engine'], if_exists='append', index=False, dtype={'geom': Geometry(geometry_type='POINT', srid= 4269)})

# def append_shp_dest(state):
#     '''opens shp file and appends dests to a table in sql server'''
# gdf = gpd.GeoDataFrame()
# dests = ['library']
# names = ['library_chc.shp']

# files = '/homedirs/dak55/monte_christchurch/data/seattle/destinations/primary_schools.shp'
# df_type = gpd.read_file('{}'.format(files))
# df_type.sort_values(inplace=True, by=['COMMON_NAM'])
# df_type['id'] = list(range(len(df_type)))
# df_type['dest_type'] = 'primary_school'
# df_type = df_type[['id', 'dest_type', 'NAME', 'geometry']]
# df_type = df_type.rename(columns={'NAME':'name'})

# files = '/homedirs/dak55/monte_christchurch/data/seattle/destinations/supermarket.shp'
# df_type = gpd.read_file('{}'.format(files))
# df_type.sort_values(inplace=True, by=['Name'])
# df_type['id'] = list(range(len(df_type)))
# df_type['dest_type'] = 'supermarket'
# df_type = df_type[['id', 'dest_type', 'Name', 'geometry']]
# df_type = df_type.rename(columns={'Name':'name'})
# gdf = gdf.append(df_type)



# gdf.reset_index(drop=True, inplace=True)
# gdf['id'] = list(range(len(gdf)))
# # prepare for sql
# gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4269))
# gdf = gdf.to_crs('EPSG:4269')
# gdf.drop('geometry', axis=1, inplace=True)
#     # export to sql
# gdf.to_sql('dests_part3', db['engine'], if_exists='replace', dtype={'geom': Geometry('POINT', srid= 4269)})

# def formatting old destinations table():
#     'retrieving old destinations table and appending to it, formatting it and resending it to sql'
# gdf_old = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations", db['con'], geom_col='geom')
# gdf_old = gdf_old.loc[gdf_old['dest_type'] != 'library']
# #neccessary to re add gdf to sql after pulling it down
# gdf_old['geom1'] = gdf_old['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
# gdf_old.crs = "EPSG:4269"
# gdf_old.drop(['geom'], axis=1, inplace=True)
# gdf_old = gdf_old.rename(columns={'geom1':'geom'})



# db = dict()
# db['passw'] = open('pass.txt', 'r').read().strip('\n')
# db['host'] = '132.181.102.2'
# db['port'] = '5001'
# # city information
# context = dict()
# db['name'] = 'access_wa'
# context['city_code'] = 'sea'
# context['city'] = 'seattle'
# # url to the osrm routing machine
# context['osrm_url'] = 'http://localhost:6004'
# context['services'] = ['supermarket', 'school', 'hospital', 'library']
# db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
# db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
# db['con'] = psycopg2.connect(db['address'])

# orig = gpd.GeoDataFrame.from_postgis("SELECT * FROM block", db['con'], geom_col='geom')
# dest = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations", db['con'], geom_col='geom')

# # prepare for sql
# orig['geom1'] = orig['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
# orig = orig.to_crs('EPSG:4269')
# orig.drop('geom1', axis=1, inplace=True)

# dest['geom1'] = dest['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
# dest = dest.to_crs('EPSG:4269')
# dest.drop('geom1', axis=1, inplace=True)

# db = dict()
# db['passw'] = open('pass.txt', 'r').read().strip('\n')
# db['host'] = '132.181.102.2'
# db['port'] = '5001'
# # city information
# context = dict()
# db['name'] = 'seadf'
# context['city_code'] = 'sea'
# context['city'] = 'seattle'
# # url to the osrm routing machine
# context['osrm_url'] = 'http://localhost:6004'
# context['services'] = ['supermarket', 'school', 'hospital', 'library']
# db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
# db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
# db['con'] = psycopg2.connect(db['address'])

# orig.to_sql('block1', db['engine'])
# dest.to_sql('dest1', db['engine'], dtype={'geom': Geometry('POINT', srid= 4269)})
