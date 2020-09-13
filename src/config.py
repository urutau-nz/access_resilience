'''
Imports functions and variables that are common throughout the project
'''

# functions - data analysis
import numpy as np
import pandas as pd
import itertools
import osmnx as ox
import networkx as nx
import plotly.graph_objects as go
# functions - geospatial
import geopandas as gpd
import rasterio as rio
# functions - data management
import pickle as pk
import psycopg2
from sqlalchemy.engine import create_engine
# functions - coding
import code
import os
from datetime import datetime, timedelta
import time
from tqdm import tqdm
#plotting
from scipy.integrate import simps
import plotly
#disable false positive warning, specifically: A value is trying to be set on a copy of a slice from a DataFrame.
pd.options.mode.chained_assignment = None  # default='warn'

def cfg_init(state):
    # SQL connection
    db = dict()
    db['passw'] = open('pass.txt', 'r').read().strip('\n')
    db['host'] = '132.181.102.2'
    db['port'] = '5001'
    # city information
    context = dict()
    # CHRISTCHURCH
    if state == 'ch':
        db['name'] = 'monte_christchurch'
        context['state'] = 'new-zealand'
        context['city_code'] = 'chc'
        context['city'] = 'christchurch'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6010'
        context['services'] = ['medical_clinic', 'primary_school', 'supermarket']
    # SEATTLE
    elif state == 'wa':
        db['name'] = 'access_wa'
        context['city_code'] = 'sea'
        context['city'] = 'seattle'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6004'
        context['services'] = ['supermarket', 'school', 'hospital', 'library']
    # HOUSTON
    elif state == 'tx':
        db['name'] = 'access_tx'
        context['city_code'] = 'hou'
        context['city'] = 'Houston'
        context['osrm_url'] = 'http://localhost:6006'
        context['services'] = ['supermarket']
    # elif state == 'sim_ch':
    #     db['name'] = 'monte_christchurch'
    #     context['state'] = 'new-zealand'
    #     context['city_code'] = 'chc'
    #     context['city'] = 'christchurch'
    #     # url to the osrm routing machine
    #     context['osrm_url'] = 'http://localhost:6010'
    #     context['services'] = ['medical_clinic', 'primary_school', 'supermarket']
    # connect to database
    db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
    db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
    db['con'] = psycopg2.connect(db['address'])
    return(db, context)
