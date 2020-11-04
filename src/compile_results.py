from config import *
from get_demo import *
from nearest_service import *
from query import *

state = 'ch' #('ch', 'wa', 'tx')
hazard = 'multi'  #('liquefaction', 'tsunami', 'hurricane', 'multi')
print('Compiling results for {} under a {} hazard scenario'.format(state, hazard))

def main():
    '''Pulls raw data from SQL, refines and saves as a CSV'''
    db, context = cfg_init(state)
    #open up required tables
    nearest_matrix = pd.read_sql('SELECT * FROM nearest_distance_{}'.format(hazard), db['con'])
    baseline_nearest = pd.read_sql('SELECT * FROM baseline_nearest', db['con'])
    demo = demographic_data(baseline_nearest, db, context)
    #income data was added for Christchurch at a late stage and hasn't been put into general format.
    #Too run this file without income data just take out all income bits at the end of refine_nearest_distance
    income = pd.read_csv('/homedirs/dak55/monte_christchurch/data/christchurch/demographic/ch_income.csv')
    refined_df = refine_nearest_distance(nearest_matrix, baseline_nearest, demo, income, db, context)
    #remove blocks with 0 population
    refined_df = refined_df.loc[refined_df['total_pop'] > 0]
    refined_df.reset_index(inplace=True, drop=True)
    refined_df.to_csv(r'results/results_{}_{}.csv'.format(state, hazard))






def refine_nearest_distance(nearest_matrix, baseline_nearest, demo, income, db, context):
    '''refines the nearest distance matrix so it has a consistent format between all cities.
    allows for plotting'''
    #intialise new df
    refined_df = pd.DataFrame(columns=[
    'id_orig', 'base_supermarket', 'base_medical_clinic', 'base_primary_school', 'mean_supermarket',
    'mean_medical_clinic', 'mean_primary_school', '95_supermarket', '95_medical_clinic', '95_primary_school',
    '5_supermarket', '5_medical_clinic', '5_primary_school'
    ])
    #replace NaN
    nearest_matrix.fillna('isolated', inplace=True)
    #determine percentage of time that block is isolated from services
    id_orig = nearest_matrix.id_orig.unique()
    for i in tqdm(range(len(id_orig))):
        #get subset of nearest matrix that includes id
        id = id_orig[i]
        df_subset = nearest_matrix.loc[nearest_matrix['id_orig'] == id]
        #create tempoary dictionary to append to the df
        dict = {'id_orig': id}
        #determine level of isolated from each service type
        for service in context['services']:
            #subset df of orig ids to include only a particular service
            df_service = df_subset.loc[df_subset['dest_type'] == service]
            #find proportion of simulations that service is isolated
            df_iso = df_service.loc[df_service['distance'] == 'isolated']
            chance_iso = len(df_iso)/len(df_service)
            #determine if service is cut off
            if chance_iso >= 0.9:
                isolated = 'True'
            else:
                isolated = 'False'
                #find rows that have access
                df_access = df_service.loc[df_service['distance'] != 'isolated']
                #add data to dict
                dict['mean_{}'.format(service)] = df_access.distance.mean()
                dict['95_{}'.format(service)] = df_access.distance.quantile(0.95)
                dict['5_{}'.format(service)] = df_access.distance.quantile(0.05)
            #add to tempoary dictionary to store results
            dict['isolated_{}'.format(service)] = isolated
            baseline = baseline_nearest.loc[(baseline_nearest['id_orig'] == id) & (baseline_nearest['dest_type'] == service)].distance
            dict['base_{}'.format(service)] = baseline.iloc[0]

        #append to df, note that there are faster ways to do this https://stackoverflow.com/questions/10715965/add-one-row-to-pandas-dataframe
        refined_df = refined_df.append(dict, ignore_index=True)

    #add demo data to the df
    #to get consist values with the refined_df
    demo.id_orig = demo.id_orig.astype(int)
    demo.id_orig = demo.id_orig.astype(str)
    #ensures values are sorted correctly
    demo.sort_values(by=['id_orig'], inplace=True, ignore_index=True)
    refined_df.sort_values(by=['id_orig'], inplace=True, ignore_index=True)
    #add to df
    refined_df['total_pop'] = demo['total']
    refined_df['white'] = demo['white']
    refined_df['indigenous'] = demo['indigenous']
    refined_df['asian'] = demo['asian']
    refined_df['polynesian'] = demo['polynesian']
    refined_df['latino'] = demo['latino']
    refined_df['african_american'] = demo['african_american']
    #add income data
    income = income.loc[income['Area_Code'].isin(refined_df['id_orig'].astype(str))]
    income.sort_values(by=['Area_Code'], inplace=True)
    income.reset_index(inplace=True, drop=True)
    refined_df['0_5000'] = income['Census_2018_Grouped_personal_income_1_.5.000.or.less_CURP_adult']
    refined_df['5000_10000'] = income['Census_2018_Grouped_personal_income_2_.5.001..10.000_CURP_adult']
    refined_df['10001_20000'] = income['Census_2018_Grouped_personal_income_3_.10.001..20.000_CURP_adult']
    refined_df['20001_30000'] = income['Census_2018_Grouped_personal_income_4_.20.001..30.000_CURP_adult']
    refined_df['30001_50000'] = income['Census_2018_Grouped_personal_income_5_.30.001..50.000_CURP_adult']
    refined_df['50001_70000'] = income['Census_2018_Grouped_personal_income_6_.50.001..70.000_CURP_adult']
    refined_df['70001_inf'] = income['Census_2018_Grouped_personal_income_7_.70.001.or.more_CURP_adult']
    return refined_df



if __name__ == '__main__':
    main()
