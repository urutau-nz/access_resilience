from config import *

def main():
    state = 'ch'
    db, context = cfg_init(state)
    origxdest = pd.read_sql("SELECT * FROM baseline_distance", db['con'])
    nearest = find_nearest_service(origxdest, db, context)

def find_nearest_service(distances, closed_ids, db, context):
    '''takes a distance matrix and returns a matrix of 1 origin per service
    paired with the nearest service to that origin'''
    con = db['con']

    dest_df = pd.read_sql("SELECT * FROM destinations", db['con'])
    #remove destinations that are closed
    dest_df = dest_df.loc[~dest_df['id'].isin(closed_ids)]
    services = context['services']
    # init the dataframe
    df = pd.DataFrame(columns = ['id_orig','distance','dest_type'])

    #converts distance column from string to float
    distances.distance = pd.to_numeric(distances.distance)
    # block ids
    id_orig = np.unique(distances.id_orig)
    # loop services
    for i in tqdm(range(len(services))):
        service = services[i]
        dest_ids = dest_df.loc[dest_df['dest_type'] == service]
        df_min = nearest_distance(distances, dest_ids)

        df_min['dest_type'] = service
        # append
        df = df.append(df_min, ignore_index=True)
    #sorts by id_orig
    df.sort_values(by=['id_orig', 'dest_type'], inplace=True)
    # add df to sql, if it exists it will be replaced
    return df

def nearest_distance(distances, ids_open):
    '''
    Calculates the nearest distance matrix for a particular service in a particular time_step
    '''

    dists_sub = distances.loc[distances['id_dest'].isin(ids_open['id'])]
    # get the minimum distance
    df_min = dists_sub.groupby('id_orig')['distance'].min()
    # prepare df to append: This makes distance the name of the column not the series
    df_min = df_min.to_frame('distance')
    #reset the index so it goes from 0 to n instead of repeating 0 to blocks * services every time_step
    df_min.reset_index(inplace=True)
    return df_min
