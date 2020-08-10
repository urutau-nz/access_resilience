'''
Adding various types of destinations. Note that filenames etc will have to be changed. More suited to running on a line by line basis
'''

from config import *
from geoalchemy2 import Geometry, WKTElement

#for downtown:
def add_downtown(state):
    '''adds a point for downtown, lat and lon must be specified'''
    df = pd.DataFrame(columns=['id', 'dest_type', 'name', 'Latitude', 'Longitude'])
    df['id'] = list(range(len(df)))
    df.loc[0] = ['downtown', 'downtown', lat, long]
    #then do same with gpd as below



def append_csv_dests(state):
    '''opens and appends new dest'''
    #initialize db connection
    db, context = cfg_init(state)
    filename = '/homedirs/dak55/resilience_equity/data/census/secondary_school_chc.csv'
    df = pd.read_csv(filename, encoding = "ISO-8859-1", skiprows=15)

        #extraact and format data so it is the same form as destinations
    df = df[['Org Name', 'Latitude', 'Longitude']]
    df['dest_type'] = 'secondary_school'
    df = df.rename(columns={'Org Name':'name'})
    df.sort_values(inplace=True, by=['name'])
    df.reset_index(inplace=True, drop=True)
    df['id'] = list(range(len(df)))
    cols = ['id', 'dest_type', 'name', 'Latitude', 'Longitude']
    df = df[cols]

    #convert to gdf and format to send to sql
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
    gdf.drop(['Latitude', 'Longitude'], axis=1, inplace=True)
gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4269))
gdf.crs = "EPSG:4269"
gdf.drop('geometry', 1, inplace=True)
    gdf.to_sql('destinations', db['engine'], if_exists='append', index=False, dtype={'geom': Geometry(geometry_type='POINT', srid= 4269)})

def append_shp_dest(state):
    '''opens shp file and appends dests to a table in sql server'''
    gdf = gpd.GeoDataFrame()
    dests = ['medical_clinic']
    names = ['medical_cent.shp']
    for i in range(0, len(dests)):
        files = '/homedirs/dak55/resilience_equity/data/census/{}'.format(names[i])
        df_type = gpd.read_file('{}'.format(files))
        df_type['dest_type'] = dests[i]
        df_type.sort_values(inplace=True, by=['Name'])
        df_type['id'] = list(range(len(df_type)))
        df_type = df_type[['id', 'dest_type', 'Name', 'geometry']]
        df_type = df_type.rename(columns={'Name':'name'})
        gdf = gdf.append(df_type)



    gdf.reset_index(drop=True, inplace=True)
    gdf['id'] = list(range(len(gdf)))
    # prepare for sql
    gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4269))
    gdf = gdf.to_crs('EPSG:4269')
    gdf.drop('geometry', axis=1, inplace=True)
    # export to sql
    gdf.to_sql('block_bois', db['engine'], if_exists='replace', dtype={'geom': Geometry('POINT', srid= 4269)})

def formatting old destinations table():
    'retrieving old destinations table and appending to it, formatting it and resending it to sql'
    gdf_old = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations", db['con'], geom_col='geom')
    gdf_old = gdf_old.loc[gdf_old['dest_type'] != 'medical_clinic']
    gdf_old = gdf_old.loc[gdf_old['dest_type'] != 'pharmacy']

    gdf_pha = gpd.GeoDataFrame.from_postgis("SELECT * FROM pharmacy2", db['con'], geom_col='geom')
    gdf_med = gpd.GeoDataFrame.from_postgis("SELECT * FROM medical_clinic", db['con'], geom_col='geom')

    #neccessary to re add gdf to sql after pulling it down
    gdf_old['geom1'] = gdf_old['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
    gdf_old.crs = "EPSG:4269"
    gdf_old.drop(['geom'], axis=1, inplace=True)
    gdf_old = gdf_old.rename(columns={'geom1':'geom'})

    gdf_pha['geom1'] = gdf_pha['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
    gdf_pha.crs = "EPSG:4269"
    gdf_pha.drop(['geom'], axis=1, inplace=True)
    gdf_pha = gdf_pha.rename(columns={'geom1':'geom'})

    gdf_med['geom1'] = gdf_med['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
    gdf_med.crs = "EPSG:4269"
    gdf_med.drop(['geom'], axis=1, inplace=True)
    gdf_med = gdf_med.rename(columns={'geom1':'geom'})

    #gdf_old formatting
    gdf_old = gdf_old.append(gdf_pha)
    gdf_old = gdf_old.append(gdf_med)
    gdf_old.drop_duplicates(inplace=True)
    gdf_old.sort_values(by=['dest_type', 'name'], inplace=True)
    gdf_old.reset_index(inplace=True, drop=True)
    gdf_old['id'] = list(range(len(gdf_old)))
    gdf_old = gdf_old[['id', 'dest_type', 'name', 'geom']]

    gdf_old.to_sql('dest_final', db['engine'], if_exists='replace', dtype={'geom': Geometry('POINT', srid= 4269)})

        #random
    gdf_old = gpd.GeoDataFrame.from_postgis("SELECT * FROM destinations", db['con'], geom_col='geom')
    gdf_old['geom'] = gdf_old['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
    gdf_old.crs = "EPSG:4269"
    gdf_old.to_sql('jun1k', db['engine'], if_exists='append', dtype={'geom': Geometry('POINT', srid= 4269)})

    gdf1.sort_values(by=['dest_type', 'name'], inplace=True)
    gdf1.reset_index(inplace=True, drop=True)
    gdf1['id'] = list(range(len(gdf1)))
