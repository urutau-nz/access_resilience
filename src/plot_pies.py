'''
Takes final results csv as input and returns pie charts of isolated demogrphics
'''

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    states = ['ch', 'wa', 'tx']
    for state in states:
        if state == 'ch':
            hazards = ['tsunami', 'liquefaction', 'multi']
        elif state == 'wa':
            hazards = ['liquefaction']
        elif state == 'tx':
            hazards = ['hurricane']
        for hazard in hazards:
            df = pd.read_csv(r'results/results_{}_{}.csv'.format(state, hazard))
            
