'''
Inputs:
    a = distribution of data, type=list
    weight (optional) = list of len(a)
    kappa (optional) = int < 0
    beta (optional, default = -0.5)
    if the distribution is of an undesirable (e.g., exposure)
        beta = int < 0
    if it is a desirable property (e.g., income)
        beta = int > 0
    epsilon (optional, default = 0.5) = int > 0
Output:
    Kolm-Pollak EDE & Index (kappa)
'''

import numpy as np
from scipy.integrate import simps
from config import *
from get_demo import *

def main(state, hazard):
    '''return the ede for each pop group and service'''
    #open up required tables
    db, context = cfg_init(state)
    baseline_nearest = pd.read_sql("SELECT * FROM baseline_nearest", db['con'])
    demo = demographic_data(baseline_nearest, db, context)
    services = context['services']
    demo.rename(columns={'total':'total_pop'}, inplace=True)
    pop_groups = demo.columns[1:]
    if context['country'] == 'nz': #removes african american population type for nz
        pop_groups = pop_groups[:-1]
    #openup result csv (obtained from runnning compile_results.py)
    refined_nearest = pd.read_csv('/homedirs/dak55/monte_christchurch/results/results_{}_{}.csv'.format(state, hazard))
    #set up df to fill with ede results
    results_df = pd.DataFrame(columns=['sim_ede', 'base_ede', 'sim_mean', 'base_mean', 'dest_type', 'population_group', 'state', 'hazard'])
    #find ede and mean for simulations & baseline cases
    for pop_group in pop_groups:
        sim_ede = []
        sim_average = []
        base_ede = []
        base_average = []
        for service in services:
            #pick out blocks that are not isolated for this particular service
            subset = refined_nearest.loc[refined_nearest['isolated_{}'.format(service)] == False]
            #sim edes
            demo_group = subset['{}'.format(pop_group)]
            distances = subset['mean_{}'.format(service)]
            sim_ede.append(kolm_pollak_ede(a=distances, beta=-0.5, weights=demo_group))
            sim_average.append(np.average(distances, weights=demo_group))
            #base edes
            distances = baseline_nearest.loc[baseline_nearest['dest_type'] == service].distance
            demo_group = demo[pop_group]
            base_ede.append(kolm_pollak_ede(a=distances, beta=-0.5, weights=demo_group))
            base_average.append(np.average(distances, weights=demo_group))
        #fill results into dict and then append to df
        dict = {'sim_ede':sim_ede, 'base_ede':base_ede, 'sim_mean':sim_average, 'base_mean':base_average, 'dest_type':services, 'population_group':pop_group, 'state':state, 'hazard':hazard}
        df = pd.DataFrame(dict)
        results_df = results_df.append(df, ignore_index=True)

    results_df.sort_values(inplace=True, by=['population_group', 'dest_type'])
    results_df.reset_index(inplace=True, drop=True)
    return results_df

def income_main(state, hazard):
    '''return the ede for each income group and service'''
    #open up required tables
    db, context = cfg_init(state)
    baseline_nearest = pd.read_sql("SELECT * FROM baseline_nearest", db['con'])
    baseline_nearest['id_orig'] = baseline_nearest['id_orig'].astype(int)
    services = context['services']
    #openup result csv (obtained from runnning compile_results.py)
    refined_nearest = pd.read_csv('/homedirs/dak55/monte_christchurch/results/results_{}_{}_income.csv'.format(state, hazard))
    #select only the income columns
    income_groups = refined_nearest.columns[-7:]
    baseline_nearest = baseline_nearest[baseline_nearest['id_orig'].isin(refined_nearest.id_orig)]
    #set up df to fill with ede results
    results_df = pd.DataFrame(columns=['sim_ede', 'base_ede', 'sim_mean', 'base_mean', 'dest_type', 'income_group', 'state', 'hazard'])
    #find ede and mean for simulations
    for income_group in income_groups:
        sim_ede = []
        sim_average = []
        base_ede = []
        base_average = []
        for service in services:
            #pick out services that are not isolated
            subset = refined_nearest.loc[refined_nearest['isolated_{}'.format(service)] == False]
            #sim edes
            income_weight = subset['{}'.format(income_group)]
            distances = subset['mean_{}'.format(service)]
            sim_ede.append(kolm_pollak_ede(a=distances, beta=-0.5, weights=income_weight))
            sim_average.append(np.average(distances, weights=income_weight))
            #base edes
            distances = baseline_nearest.loc[baseline_nearest['dest_type'] == service].distance
            income_weight = refined_nearest[income_group]
            base_ede.append(kolm_pollak_ede(a=distances, beta=-0.5, weights=income_weight))
            base_average.append(np.average(distances, weights=income_weight))
        #fill dict with results then append to csv
        dict = {'sim_ede':sim_ede, 'base_ede':base_ede, 'sim_mean':sim_average, 'base_mean':base_average, 'dest_type':services, 'income_group':income_group, 'state':state, 'hazard':hazard}
        df = pd.DataFrame(dict)
        results_df = results_df.append(df, ignore_index=True)

    results_df.reset_index(inplace=True, drop=True)
    return results_df

def kolm_pollak_ede(a, beta = None, kappa = None, weights = None):
    '''returns the Kolm-Pollak EDE'''
    a = np.asanyarray(a)
    if kappa is None:
        if beta is None:
            raise TypeError("you must provide either a beta or kappa aversion parameter")
        kappa = calc_kappa(a, beta, weights)
    if weights is None:
        ede_sum = np.exp(a*-kappa).sum()
        N = len(a)
    else:
        ede_sum = np.multiply(np.exp(a*-kappa), weights).sum()
        N = sum(weights) # for a weighted average
    ede = (-1 / kappa) * np.log(ede_sum / N)
    return(ede)

def kolm_pollak_index(a, beta = None, kappa = None, weights = None):
    '''returns the Kolm-Pollak Inequality Index'''
    if weights is None:
        x_mean = np.mean(a)
    else:
        x_mean = np.average(a, weights = weights)
    a = a - x_mean
    inequality_index = kolm_pollak_ede(a, beta = beta, kappa = kappa, weights = weights)
    return(inequality_index)

def calc_kappa(a, beta, weights = None):
    '''calculates kappa by minimising the sum of squares'''
    if weights is None:
        x_sum = sum(a)
        x_sq_sum = (np.array(a)**2).sum()
    else:
        x_sum = np.multiply(a, weights).sum()
        x_sq_sum = np.multiply(a**2, weights).sum()
    kappa = beta * (x_sum / x_sq_sum)
    return(kappa)


df = income_main('ch', 'multi_10')
df = df.append(income_main('ch', 'liquefaction'), ignore_index=True)
df = df.append(income_main('ch', 'tsunami'), ignore_index=True)

#check results and then send to csv
code.interact(local=locals())
df.to_csv('results/income_ede_results.csv')
