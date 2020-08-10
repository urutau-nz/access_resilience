'''runs program'''
from config import *
from query import *
from calculate_ede import *
from nearest_service import *

def main(state):
    '''main'''
    db, context = cfg_init(state)
    origxdest = query_points(db, context)
    nearest_service = find_nearest_service(origxdest)
