'''code to format a csv of USA census data and send to server'''

from config import *
state = 'wa'
db, context = cfg_init(state)
filename = '/homedirs/dak55/monte_christchurch/data/houston/demograph/demo_hou.csv'
census_data = pd.read_csv(filename, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLOCKA':str, 'H7X001':int, 'H7X002':int, 'H7X003':int, 'H7X004':int, 'H7X005':int, 'H7X006':int, 'H7Y003':int})
census_data['geoid10'] = census_data['STATEA'] + census_data['COUNTYA'] + census_data['TRACTA'] + census_data['BLOCKA']
census_data.to_sql('demograph_finally', db['engine'], if_exists='replace', index=False)
