from config import *

def find_nearest_service():
    '''takes a distance matrix and returns a matrix of 1 origin per service
    paired with the nearest service to that origin'''
    db, context = cfg_init(state)
    con = db['con']
    cursor = con.cursor()

    dest_df = pd.read_sql("SELECT * FROM destinations", db['con'])
    services = dest_df.dest_type.unique()
    # init the dataframe
    df = pd.DataFrame(columns = ['id_orig','distance','service'])

    # get the distance matrix
    distances = pd.read_sql('SELECT * FROM baseline_distance', db['con'])
    #making the id_dest column the index
    distances = distances.set_index('id_dest')
    #converts distance column from string to float
    distances.distance = pd.to_numeric(distances.distance)
    # block ids
    id_orig = np.unique(distances.id_orig)
    # loop services
    for i in tqdm(range(len(services))):
        service = services[i]
        dest_ids = dest_df.loc[dest_df['dest_type'] == service]
        df_min = nearest_distance(distances, dest_ids)

        df_min['service'] = service
        # append
        df = df.append(df_min, ignore_index=True)
    #sorts by id_orig
    df.sort_values(by=['id_orig', 'service'], inplace=True)
    # add df to sql, if it exists it will be replaced
    code.interact(local=locals())
    df.to_sql('nearest_dist', con=db['engine'], if_exists='replace', index=False)
    # add index
    cursor.execute('CREATE INDEX on nearest_dist (time_stamp);')
    # commit
    con.commit()
    con.close()

def nearest_distance(distances, ids_open):
    '''
    Calculates the nearest distance matrix for a particular service in a particular time_step
    '''
    # subset the distance matrix on dest_id
    dists_sub = distances.loc[ids_open]
    # get the minimum distance
    df_min = dists_sub.groupby('id_orig')['distance'].min()
    # prepare df to append: This makes distance the name of the column not the series
    df_min = df_min.to_frame('distance')
    #reset the index so it goes from 0 to n instead of repeating 0 to blocks * services every time_step
    df_min.reset_index(inplace=True)
    return df_min


find_nearest_service()
