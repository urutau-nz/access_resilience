'''
Imports functions and variables that are common throughout the project
'''

# functions - data analysis
import numpy as np
import pandas as pd
import itertools
# functions - geospatial
import geopandas as gpd
from geoalchemy2 import Geometry, WKTElement
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
import plotly.graph_objects as go
from statsmodels.distributions.empirical_distribution import ECDF
import matplotlib.pyplot as plt
#taken straight from query.py

# logging
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

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
        context['city_code'] = 'chc'
        context['city'] = 'christchurch'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6001'
        context['services'] = ['downtown', 'fire_station', 'hospital', 'library', 'medical_clinic', 'petrol_station', 'pharmacy', 'police_station', 'primary_school', 'secondary_school', 'supermarket']
    elif state == 'wa':
        db['name'] = 'access_wa'
        context['city_code'] = 'sea'
        context['city'] = 'seattle'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6004'
        context['services'] = ['supermarket', 'school', 'hospital', 'library']
    elif state == 'tx':
        db['name'] = 'access_tx'
        context['city_code'] = 'hou'
        context['city'] = 'Houston'
        context['osrm_url'] = 'http://localhost:6006'
        context['services'] = ['supermarket']

    # connect to database
    db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
    db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
    db['con'] = psycopg2.connect(db['address'])
    return(db, context)
