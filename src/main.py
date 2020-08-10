'''runs program'''
from config import *
from query import *
from calculate_ede import *

def main(state):
    '''main'''
    db, context = cfg_init(state)
    origxdest = query_points(db, context)
    
