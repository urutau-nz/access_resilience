'''runs program'''
from config import *
from query import *
from calculate_ede import *
from nearest_service import *

def main(state):
    '''main'''
    db, context = cfg_init(state)
    origxdest = query_points(db, context)
    nearest_service = find_nearest_service(origxdest, db, context)
    demo = demographic_data(nearest_service, db, context)
    code.interact(local=locals())


if __name__ == "__main__":
    state = input('State: ')
    main(state)
