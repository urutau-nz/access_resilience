'''runs program'''
from config import *
from query import *
from calculate_ede import *
from nearest_service import *
from get_demo import *
from plot_cdf import *


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
    ede_df = kp_ede(demo, nearest_service, context)
    #ede_df.to_csv('results/baseline_ede.csv')
    logger.info('plot boi')
    plotting(nearest_service, demo, db, context)
    #code.interact(local=locals())

#if __name__ == "__main__":
state = 'ch'#input('State: ')
main_function(state)
