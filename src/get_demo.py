from config import *

def demographic_data(df, db, context):
    '''returns the demographic data with blocks that are common with input df (so df can be nearest_service or distance matrix)
    Removes any rows from input df that do not have census data (these are usually in the ocean)'''
    #open census data for all of nz
    census_data = pd.read_sql("SELECT * FROM census_18", db['con'])
    #select only rows that are common with our meshblocks
    relevant_demo = census_data.loc[census_data['gid'].isin(df['id_orig'])]
    #needed to avoid slicing error on next line
    sorted_demo = relevant_demo
    #format census data
    sorted_demo["gid"] = sorted_demo['gid'].apply(lambda x: np.int64(x))
    sorted_demo["gid"] = sorted_demo['gid'].apply(lambda x: np.str(x))
    sorted_demo.sort_values(by=['gid'], inplace=True)
    sorted_demo.reset_index(inplace=True, drop=True)

    df.sort_values(['id_orig', 'dest_type'], inplace=True)
    return sorted_demo


#removes any rows in nearest_service (called df here) that dont have census data. More useful to just copy and paste this and then take out the block(s)
#if len(sorted_demo) < len(df):
#    to_drop = []
#    for value in df['id_orig']:
#       if len(sorted_demo.loc[sorted_demo['gid'] == value]) == 0:
#           to_drop.append(value)
#    df = df.loc[~df['id_orig'].isin(to_drop)]

#need to remove 7029868 orig_id
