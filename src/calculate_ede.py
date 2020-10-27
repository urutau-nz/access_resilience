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
    if context['country'] == 'nz': #removes african american column for NZ, which is currently 0
        pop_groups = pop_groups[:-1]
    #refine nearest_matrix to remove rows without access
    refined_nearest = pd.read_csv('/homedirs/dak55/monte_christchurch/results/results_{}_{}.csv'.format(state, hazard))
    #set up results df
    results_df = pd.DataFrame(columns=['sim_ede', 'base_ede', 'sim_mean', 'base_mean', 'dest_type', 'population_group', 'state', 'hazard'])
    #find ede and mean for simulations
    for pop_group in pop_groups:
        sim_ede = []
        sim_average = []
        base_ede = []
        base_average = []
        for service in services:
            #pick out services that are open
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
        dict = {'sim_ede':sim_ede, 'base_ede':base_ede, 'sim_mean':sim_average, 'base_mean':base_average, 'dest_type':services, 'population_group':pop_group, 'state':state, 'hazard':hazard}
        df = pd.DataFrame(dict)
        results_df = results_df.append(df, ignore_index=True)

    results_df.sort_values(inplace=True, by=['population_group', 'dest_type'])
    results_df.reset_index(inplace=True, drop=True)
    return results_df


def kp_ede_main(demo, nearest_service, context):
    '''calculates an ede for each pop group for the given nearest_distance matrix'''
    results_df = pd.DataFrame(columns=['ede', 'mean', 'dest_type', 'population_group'])
    services = context['services']
    #removes gid and median_age columns, we are only interested in population groups
    pop_groups = demo.columns
    index = [0]
    if context['country'] == 'nz': #removes african american column for NZ, which is currently 0
        index.append(-1)
    pop_groups = np.delete(pop_groups, index)

    #remove rows with 0 population from each df
    zero_pop = demo.loc[demo['total'] == 0]
    zero_pop_id_flt = zero_pop['id_orig'].tolist()
    #convert to ints
    zero_pop_id_int = [int(i) for i in zero_pop_id_flt]
    #convert to str
    zero_pop_id_str = [str(i) for i in zero_pop_id_int]
    nearest_service = nearest_service[~nearest_service['id_orig'].isin(zero_pop_id_str)]
    demo = demo[~demo['id_orig'].isin(zero_pop_id_flt)]

    for pop_group in pop_groups:
        ede = []
        average = []
        for service in services:
            service_subset = nearest_service.loc[nearest_service['dest_type'] == service]
            distances = service_subset['distance']
            if 'C' in demo[pop_group]:
                demo_group = demo[pop_group].replace(['C'], 0).apply(lambda x: np.int64(x))
            else:
                demo_group = demo[pop_group]
            ede.append(kolm_pollak_ede(a=distances, beta=-0.5, weights=demo_group))
            average.append(np.average(distances, weights=demo_group))
        dict = {'ede':ede, 'mean':average, 'dest_type':services, 'population_group':pop_group}
        df = pd.DataFrame(dict)
        results_df = results_df.append(df, ignore_index=True)
    results_df.sort_values(inplace=True, by=['dest_type', 'population_group'])
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


df = main('ch', 'multi')
df = df.append(main('ch', 'liquefaction'), ignore_index=True)
df = df.append(main('ch', 'tsunami'), ignore_index=True)
df = df.append(main('tx', 'hurricane'), ignore_index=True)
df = df.append(main('wa', 'liquefaction'), ignore_index=True)
code.interact(local=locals())
df.to_csv('results/ede_results.csv')
