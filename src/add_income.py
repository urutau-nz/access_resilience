'''takes result file and adds income data before saving as csv'''
from config import *
income = pd.read_csv('/homedirs/dak55/monte_christchurch/data/christchurch/demographic/ch_income.csv')
income.drop(columns={'Area_Description', 'Area_code_and_description'}, inplace=True)

state = 'ch'
hazards = ['liquefaction', 'tsunami', 'multi_10']

for hazard in hazards:
    refined_df = pd.read_csv('/homedirs/dak55/monte_christchurch/results/results_{}_{}.csv'.format(state, hazard))
    income = income.loc[income['Area_Code'].isin(refined_df['id_orig'].astype(str))]
    income = income.replace(['C'], 0).apply(lambda x: np.int64(x))
    income.sort_values(by=['Area_Code'], inplace=True)
    income.reset_index(inplace=True, drop=True)
    refined_df['0_5000'] = income['Census_2018_Grouped_personal_income_1_.5.000.or.less_CURP_adult']
    refined_df['5000_10000'] = income['Census_2018_Grouped_personal_income_2_.5.001..10.000_CURP_adult']
    refined_df['10001_20000'] = income['Census_2018_Grouped_personal_income_3_.10.001..20.000_CURP_adult']
    refined_df['20001_30000'] = income['Census_2018_Grouped_personal_income_4_.20.001..30.000_CURP_adult']
    refined_df['30001_50000'] = income['Census_2018_Grouped_personal_income_5_.30.001..50.000_CURP_adult']
    refined_df['50001_70000'] = income['Census_2018_Grouped_personal_income_6_.50.001..70.000_CURP_adult']
    refined_df['70001_inf'] = income['Census_2018_Grouped_personal_income_7_.70.001.or.more_CURP_adult']
    refined_df.to_csv('results_{}_{}_income.csv'.format(state, hazard))
