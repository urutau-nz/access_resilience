'''runs program'''
from config import *
from query import *
from calculate_ede import *
from nearest_service import *
from get_demo import *

def main_function(state):
    '''main'''
    db, context = cfg_init(state)
    logger.info('querying dests')
    origxdest = query_points(db, context)
    logger.info('finding nearest services')
    nearest_service = find_nearest_service(origxdest, db, context)
    logger.info('retrieving relevant census data')
    demo, nearest_service = demographic_data(nearest_service, db, context)

    logger.info('calculating ede\'s')
    #need to make into its own function
    results_df = pd.DataFrame(columns=['ede', 'mean', 'dest_type', 'population_group'])
    services = context['services']
    pop_groups = demo.columns
    pop_groups = pop_groups[1:]
    code.interact(local=locals())
    for pop_group in pop_groups:
        ede = []
        average = []
        for service in services:
            service_subset = nearest_service.loc[nearest_service['dest_type'] == service]
            distances = service_subset['distance']
            ede.append(kolm_pollak_ede(a=distances, beta=-0.5, weights=demo[pop_group]))
            average.append(distances.mean())
        dict = {'ede':ede, 'mean':average, 'dest_type':services, 'population_group':pop_group}
        df = pd.DataFrame(dict)
        results_df = results_df.append(df, ignore_index=True)
    results_df.sort_values(inplace=True, by=[''])
    code.interact(local=locals())

#if __name__ == "__main__":
state = 'ch'#input('State: ')
main_function(state)
