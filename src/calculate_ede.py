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

def kp_ede(demo, nearest_service, context):
    '''calculates an ede for each pop group for the given nearest_distance matrix'''
    results_df = pd.DataFrame(columns=['ede', 'mean', 'dest_type', 'population_group'])
    services = context['services']
    #removes gid and median_age columns, we are only interested in population groups
    pop_groups = demo.columns
    pop_groups = pop_groups[1:]
    pop_groups = pop_groups[np.arange(len(pop_groups))!=3]
    for pop_group in pop_groups:
        ede = []
        average = []
        for service in services:
            service_subset = nearest_service.loc[nearest_service['dest_type'] == service]
            distances = service_subset['distance']
            demo_group = demo[pop_group].replace(['C'], 0).apply(lambda x: np.int64(x))
            ede.append(kolm_pollak_ede(a=distances, beta=-0.5, weights=demo_group))
            average.append(distances.mean())
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
