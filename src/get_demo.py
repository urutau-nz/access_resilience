from config import *

def demographic_data(df, db, context):
    '''returns the demographic data with blocks that are common with input df (so df can be nearest_service or distance matrix)'''
    #retrieve census data and format so as to have standard column names between the two countries
    if context['country'] == 'nz':
        #open census data for all of nz
        census_data = pd.read_sql("SELECT * FROM census_18", db['con'])
        census_data = census_data.dropna(subset=['gid'])
        census_data['gid'] = census_data['gid'].astype(int)
        census_data['gid'] = census_data['gid'].astype(str)

        #select only rows that are common with our meshblocks
        relevant_demo = census_data.loc[census_data['gid'].astype(str).isin(df['id_orig'])]
        #format results
        relevant_demo.sort_values(by=['gid'], inplace=True)
        relevant_demo.reset_index(inplace=True, drop=True)

        sorted_demo = relevant_demo.drop(['gid', 'median_age', 'male_pop', 'female_pop'], axis=1)
        #replace values that are'confidential'
        sorted_demo = sorted_demo.replace(['C'], 0).apply(lambda x: np.int64(x))
        #standardize column names. Note latino pop is more relevant for USA, melaa in NZ census includes middle eastarn and african as well as latino. Further note that because latino is not a race it was not included in our eventaul analysis
        sorted_demo = sorted_demo.rename({'population':'total', 'pop_euro':'white', 'pop_maori':'indigenous', 'pop_asian':'asian', 'pop_pacific':'polynesian', 'pop_melaa':'latino'}, axis=1)
        demo = sorted_demo[['total', 'white', 'indigenous', 'asian', 'polynesian', 'latino']]
        demo.insert(loc=0, column='id_orig', value=relevant_demo['gid'])
        demo['african_american'] = None #not relevant for NZ data
    elif context['country'] == 'usa':
        #open US state census data
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
