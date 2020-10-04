from config import *

def demographic_data(df, db, context):
    '''returns the demographic data with blocks that are common with input df (so df can be nearest_service or distance matrix)
    Removes any rows from input df that do not have census data (these are usually in the ocean)'''
    #retrieve census data and format so as to have standard column names between the two countries
    if context['country'] == 'nz':
        #open census data for all of nz
        census_data = pd.read_sql("SELECT * FROM census_18", db['con'])
        #select only rows that are common with our meshblocks
        relevant_demo = census_data.loc[census_data['gid'].isin(df['id_orig'])]
        #format results
        relevant_demo.sort_values(by=['gid'], inplace=True)
        relevant_demo.reset_index(inplace=True, drop=True)

        sorted_demo = relevant_demo.drop(['gid', 'median_age', 'male_pop', 'female_pop'], axis=1)
        #replace values that are'confidential'
        sorted_demo = sorted_demo.replace(['C'], 0).apply(lambda x: np.int64(x))
        #standardize column names. Note latino pop is more relevant for USA, melaa in NZ census includes middle eastarn and african as well as latino
        sorted_demo = sorted_demo.rename({'population':'total', 'pop_euro':'white', 'pop_maori':'indigenous', 'pop_asian':'asian', 'pop_pacific':'polynesian', 'pop_melaa':'latino'}, axis=1)
        demo = sorted_demo[['total', 'white', 'indigenous', 'asian', 'polynesian', 'latino']]
        demo.insert(loc=0, column='id_orig', value=relevant_demo['gid'])
        demo['african_american'] = None #not relevant for NZ data
    elif context['country'] == 'usa':
        #open US state census data
        if context['city'] == 'houston': #temp fix while I send this to sql 
            census_data = pd.read_csv(filename, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLOCKA':str, 'H7X001':int, 'H7X002':int, 'H7X003':int, 'H7X004':int, 'H7X005':int, 'H7X006':int, 'H7Y003':int})
            census_data['geoid10'] = census_data['STATEA'] + census_data['COUNTYA'] + census_data['TRACTA'] + census_data['BLOCKA']
        else:
            census_data = pd.read_sql("SELECT * FROM demograph", db['con'])
        #select only rows that are common with our meshblocks
        relevant_demo = census_data.loc[census_data['geoid10'].isin(df['id_orig'])]
        #format results
        relevant_demo.sort_values(by=['geoid10'], inplace=True)
        relevant_demo.reset_index(inplace=True, drop=True)
        #standardize column names
        relevant_demo = relevant_demo.rename({'H7X001':'total', 'H7X002':'white', 'H7X003':'african_american', 'H7X004':'indigenous', 'H7X005':'asian', 'H7X006':'polynesian', 'H7Y003':'latino'}, axis=1)
        demo = relevant_demo[['total', 'white', 'indigenous', 'asian', 'polynesian', 'latino', 'african_american']]
        demo.insert(loc=0, column='id_orig', value=relevant_demo['geoid10'])
    return demo


#removes any rows in nearest_service (called df here) that dont have census data. More useful to just copy and paste this and then take out the block(s)
#if len(relevant_demo) < len(df):
#    to_drop = []
#    for value in df['id_orig']:
#       if len(relevant_demo.loc[relevant_demo['gid'] == value]) == 0:
#           to_drop.append(value)
#    df = df.loc[~df['id_orig'].isin(to_drop)]

#need to remove 7029868 orig_id
