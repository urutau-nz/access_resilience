from config import *

def demographic_data(df, db, context):
    '''returns the demographic data with blocks that are common with input df'''
    census_data = pd.read_sql("SELECT * FROM census_18", db['con'])

    relevant_demo = census_data.loc[census_data['gid'].isin(df['id_orig'])]
    relevant_demo["gid"] = relevant_demo['gid'].apply(lambda x: np.int64(x))
    relevant_demo.sort_values(by=['gid'], inplace=True)
    relevant_demo.reset_index(inplace=True, drop=True)
    return relevant_demo


#doing this to find missing block, turns out its in the sea so we will just ignore it:
#for value in df_o['id_orig']:
#    if len(relevant_demo.loc[relevant_demo['gid'] == value]) == 0:
#        a = value
#        print(value)

#df_o.loc[df_o['id_orig'] == a]
