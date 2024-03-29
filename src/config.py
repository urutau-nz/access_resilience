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
from geoalchemy2 import Geometry, WKTElement
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
    db['host'] = 'encivmu-tml62'
    db['port'] = '5002'
    # city information
    context = dict()
    # CHRISTCHURCH
    if state == 'ch':
        db['name'] = 'monte_christchurch'
        context['state'] = 'new-zealand'
        context['city_code'] = 'chc'
        context['city'] = 'christchurch'
        context['country'] = 'nz'
        context['continent'] = 'australia-oceania'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6002'
        context['services'] = ['medical_clinic', 'primary_school', 'supermarket']
    # SEATTLE
    elif state == 'wa':
        db['name'] = 'seadf'
        context['city_code'] = 'sea'
        context['city'] = 'seattle'
        context['country'] = 'usa'
        context['state'] = 'washington'
        context['continent'] = 'north-america/us'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6004'
        context['services'] = ['medical_clinic', 'primary_school', 'supermarket']
    # HOUSTON
    elif state == 'tx':
        db['name'] = 'housim'
        context['city_code'] = 'hou'
        context['city'] = 'houston'
        context['osrm_url'] = 'http://localhost:6007'
        context['services'] = ['medical_clinic', 'primary_school', 'supermarket']
        context['country'] = 'usa'
        context['state'] = 'texas'
        context['continent'] = 'north-america/us'
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
