from config import *

def remove_zero(db, context):
    '''removes each block that has noone living in them to improve query efficiency.
     usually these are water, this process is formatted for US census blocks'''
     #creates df of geoid10 indexes
sql = "SELECT * FROM block"
orig_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
#sorts and indexes by geoid10 of the blocks
orig_df = orig_df.sort_values(by='geoid10', axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')


#opening total population stats for each block
sql = """SELECT "H7X001", geoid10 FROM demograph"""
demo_df = pd.read_sql(sql, db['con'])
#orders by geoid and sets it as the index
demo_df = demo_df.sort_values(by='geoid10', axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')
zero_pop = demo_df.loc[demo_df['H7X001'] == 0]
zero_pop_id_flt = zero_pop['geoid10'].tolist()
#convert to ints
zero_pop_id_int = [int(i) for i in zero_pop_id_flt]
#convert to str
zero_pop_id_str = [str(i) for i in zero_pop_id_int]
orig_df = orig_df[~orig_df['geoid10'].isin(zero_pop_id_str)]


orig_df.reset_index(inplace=True, drop=True)
orig_df['geom1'] = orig_df['geom'].apply(lambda x: WKTElement(x.wkt, srid=4269))
orig_df.crs = "EPSG:4269"
orig_df.drop('geom', 1, inplace=True)
orig_df.rename(columns={'geom1':'geom'}, inplace=True)

orig_df.to_sql('block_zero5', db['engine'], if_exists='append', index=False, dtype={'geom': Geometry(geometry_type='MULTIPOLYGON', srid= 4269)})
