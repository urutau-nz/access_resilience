'''
Init the database
Query origins to dests in OSRM
'''
# user defined variables
par = True
par_frac = 0.9
transport_mode = 'driving'

import utils
from config import *
logger = logging.getLogger(__name__)
import math
import os.path
import osgeo.ogr
import io
import shapely
from geoalchemy2 import Geometry, WKTElement
import requests
from sqlalchemy.types import Float, Integer
if par == True:
    import multiprocessing as mp
    from joblib import Parallel, delayed
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry

def main(state):
    '''
    set up the db tables I need for the querying
    '''
    db, context = cfg_init(state)

    # query the distances
    query_points(db, context)

    # close the connection
    db['con'].close()
    logger.info('Database connection closed')

def query_points(db, context):
    '''
    query OSRM for distances between origins and destinations
    '''
    # connect to db
    cursor = db['con'].cursor()

    # get list of all origin ids
    sql = "SELECT * FROM block"
    orig_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')

    orig_df['x'] = orig_df.geom.centroid.x
    orig_df['y'] = orig_df.geom.centroid.y
    # drop duplicates
    orig_df.drop('geom',axis=1,inplace=True)
    orig_df.drop_duplicates(inplace=True)
    # set index
    orig_df = orig_df.set_index('sa12018_v1')

    # get list of destination ids
    sql = "SELECT * FROM destinations"
    dest_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')

    dest_df = dest_df.set_index('id')
    dest_df['lon'] = dest_df.geom.centroid.x
    dest_df['lat'] = dest_df.geom.centroid.y

    # list of origxdest pairs
    origxdest = pd.DataFrame(list(itertools.product(orig_df.index, dest_df.index)), columns = ['id_orig','id_dest'])
    origxdest['distance'] = None
    # df of durations, distances, ids, and co-ordinates

    origxdest = execute_table_query(origxdest, orig_df, dest_df, context)

    # add df to sql
    logger.info('Writing data to SQL')
    write_to_postgres(origxdest, db, 'baseline_distance')
    # origxdest.to_sql('distance_duration', con=db['engine'], if_exists='replace', index=False, dtype={"distance":Float(), "duration":Float(), 'id_dest':Integer()}, method='multi')
    logger.info('Distances written successfully to SQL')
    logger.info('Updating indices on SQL')
    # update indices
    queries = [
                'CREATE INDEX "dest_idx" ON baseline_distance ("id_dest");',
                'CREATE INDEX "orig_idx" ON baseline_distance ("id_orig");'
                ]
    for q in queries:
        cursor.execute(q)

    # commit to db
    db['con'].commit()
    logger.info('Query Complete')

def write_to_postgres(df, db, table_name):
    ''' quickly write to a postgres database
        from https://stackoverflow.com/a/47984180/5890574'''

    df.head(0).to_sql(table_name, db['engine'], if_exists='replace',index=False) #truncates the table

    conn = db['engine'].raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    cur.copy_from(output, table_name, null="") # null values become ''
    conn.commit()


def execute_table_query(origxdest, orig_df, dest_df, context):
    # Use the table service so as to reduce the amount of requests sent
    # https://github.com/Project-OSRM/osrm-backend/blob/master/docs/http.md#table-service

    batch_limit = 10000

    dest_n = len(dest_df)
    orig_n = len(orig_df)
    orig_per_batch = int(batch_limit/dest_n)
    batch_n = math.ceil(orig_n/orig_per_batch)

    #create query string
    base_string = context['osrm_url'] + "/table/v1/{}/".format(transport_mode)

    # make a string of all the destination coordinates
    dest_string = ""
    dest_df.reset_index(inplace=True, drop=True)
    for j in range(dest_n):
        #now add each dest in the string
        dest_string += str(dest_df['lon'][j]) + "," + str(dest_df['lat'][j]) + ";"
    #remove last semi colon
    dest_string = dest_string[:-1]

    # options string
    options_string_base = '?annotations=distance' #'?annotations=duration,distance'

    # loop through the sets of
    orig_sets = [(i, min(i+orig_per_batch, orig_n)) for i in range(0,orig_n,orig_per_batch)]

    # create a list of queries
    query_list = []
    for i in orig_sets:
        # make a string of all the origin coordinates
        orig_string = ""
        orig_ids = range(i[0],i[1])
        for j in orig_ids:
            #now add each dest in the string
            orig_string += str(orig_df.x[j]) + "," + str(orig_df.y[j]) + ";"
        # make a string of the number of the sources
        source_str = '&sources=' + str(list(range(len(orig_ids))))[1:-1].replace(' ','').replace(',',';')
        # make the string for the destinations
        dest_idx_str = '&destinations=' + str(list(range(len(orig_ids), len(orig_ids)+len(dest_df))))[1:-1].replace(' ','').replace(',',';')
        # combine and create the query string
        options_string = options_string_base + source_str + dest_idx_str
        query_string = base_string + orig_string + dest_string + options_string
        # append to list of queries
        query_list.append(query_string)
    # # Table Query OSRM in parallel

    if par == True:
        #define cpu usage
        num_workers = np.int(mp.cpu_count() * par_frac)
        #gets list of tuples which contain 1list of distances and 1list
        results = Parallel(n_jobs=num_workers)(delayed(req)(query_string) for query_string in tqdm(query_list))
    # get the results in the right format
    #dists = [l for orig in results for l in orig[0]] was giving errors so i rewrote
    dists = [result for query in results for result in query]
    origxdest['distance'] = dists
    return(origxdest)

def req(query_string):
    response = requests.get(query_string).json()
    temp_dist = [item for sublist in response['distances'] for item in sublist]
    return temp_dist


if __name__ == "__main__":
    state = 'ch'#input('State: ')
    logger.info('query.py code invoked')
    main(state)
