'''
Plot figures for the paper
'''

#from turtle import color
import seaborn as sns
import yaml
from yaml import Loader, Dumper
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import matplotlib.pyplot as plt
import os 
import pandas as pd
import numpy as np
import psycopg2
from io import StringIO
from pylab import rcParams
rcParams['figure.figsize'] = 12.917, 6.458
rcParams['pdf.fonttype'] = 42
rcParams['axes.linewidth'] = 3
params = {"ytick.color" : "w",
          "xtick.color" : "w",
          "axes.labelcolor" : "w",
          "axes.edgecolor" : "w",
          "font.size": 18}
rcParams.update(params)
lwidth = 2.25

def main():
    #cdf()
    #bar()
    recovery()

def cdf():
    ## TO DO
    # legend
    # import data
    scenarios = [('ch','multi', 'supermarket', 'polynesian', 'monte_christchurch'), ('wa','liquefaction', 'primary_school', 'african_american', 'seadf'), ('tx','hurricane', 'medical_clinic', 'latino', 'housim')]
    for scenario in scenarios:
        df = pd.read_csv('results/ede_results.csv')
        df_plot = df[(df['state']==scenario[0])&(df['hazard']==scenario[1])&(df['dest_type']==scenario[2])&(df['population_group'].isin(['total_pop', scenario[3]]))]
        ede_0_0 = float(df_plot[df_plot['population_group']=='total_pop']['base_ede'])
        ede_0_1 = float(df_plot[df_plot['population_group']=='total_pop']['sim_ede'])
        ede_1_0 = float(df_plot[df_plot['population_group']==scenario[3]]['base_ede'])
        ede_1_1 = float(df_plot[df_plot['population_group']==scenario[3]]['sim_ede'])
        # import distances
        df = pd.read_csv('results/results_{}_{}.csv'.format(scenario[0], scenario[1]))
        df_plot = df[['base_{}'.format(scenario[2]),'mean_{}'.format(scenario[2]), '95_{}'.format(scenario[2]), '5_{}'.format(scenario[2]), 'total_pop', scenario[3]]]
        df_plot['base_{}'.format(scenario[2])] = df_plot['base_{}'.format(scenario[2])]/1000
        df_plot['mean_{}'.format(scenario[2])] = df_plot['mean_{}'.format(scenario[2])]/1000
        df_plot['95_{}'.format(scenario[2])] = df_plot['95_{}'.format(scenario[2])]/1000
        df_plot['5_{}'.format(scenario[2])] = df_plot['5_{}'.format(scenario[2])]/1000
        dx = 0.05
        x  = np.arange(0, 10,dx)#df_plot[plot].max(), dx)
        y_0_0, y_0_1, y_0_5, y_0_95 = [], [], [], []
        y_1_0, y_1_1, y_1_5, y_1_95 = [], [], [], []
        e_0_0, e_0_1 = [], []
        e_1_0, e_1_1 = [], []
        for i in x:
            # base
            y_0_0.append(df_plot[df_plot['base_{}'.format(scenario[2])]<=i]['total_pop'].sum()/df_plot['total_pop'].sum()*100)
            y_1_0.append(df_plot[df_plot['base_{}'.format(scenario[2])]<=i][scenario[3]].sum()/df_plot[scenario[3]].sum()*100)
            e_0_0.append(ede_0_0/1000)
            e_1_0.append(ede_1_0/1000)
            # mean
            y_0_1.append(df_plot[df_plot['mean_{}'.format(scenario[2])]<=i]['total_pop'].sum()/df_plot['total_pop'].sum()*100)
            y_1_1.append(df_plot[df_plot['mean_{}'.format(scenario[2])]<=i][scenario[3]].sum()/df_plot[scenario[3]].sum()*100)
            e_0_1.append(ede_0_1/1000)
            e_1_1.append(ede_1_1/1000)
            # 95
            y_0_95.append(df_plot[df_plot['95_{}'.format(scenario[2])]<=i]['total_pop'].sum()/df_plot['total_pop'].sum()*100)
            y_1_95.append(df_plot[df_plot['95_{}'.format(scenario[2])]<=i][scenario[3]].sum()/df_plot[scenario[3]].sum()*100)
            # 5
            y_0_5.append(df_plot[df_plot['5_{}'.format(scenario[2])]<=i]['total_pop'].sum()/df_plot['total_pop'].sum()*100)
            y_1_5.append(df_plot[df_plot['5_{}'.format(scenario[2])]<=i][scenario[3]].sum()/df_plot[scenario[3]].sum()*100)
        # plot
        fig = plt.figure() # Create matplotlib figure

        # base
        plt.plot(x,y_0_0, color='#197BB0', linewidth=lwidth)
        plt.plot(x,y_1_0, color='#B7F6FF', linewidth=lwidth)
        plt.plot(e_0_0,np.arange(-10,110,120/len(y_0_0)), color='#197BB0', linewidth=lwidth)
        plt.plot(e_1_0,np.arange(-10,110,120/len(y_0_0)), color='#B7F6FF', linewidth=lwidth)
        # sim
        plt.plot(x,y_0_1, linestyle='dashed', color='#197BB0', linewidth=lwidth)
        plt.plot(x,y_1_1, linestyle='dashed', color='#B7F6FF', linewidth=lwidth)
        plt.plot(e_0_1,np.arange(-10,110,120/len(y_0_0)), linestyle='dashed', color='#197BB0', linewidth=lwidth)
        plt.plot(e_1_1,np.arange(-10,110,120/len(y_0_0)), linestyle='dashed', color='#B7F6FF', linewidth=lwidth)
        # 90th percentile
        plt.plot(x,y_0_5, color='#197BB0', alpha=0.2, linewidth=lwidth)
        plt.plot(x,y_0_95, color='#197BB0', alpha=0.2, linewidth=lwidth)
        plt.plot(x,y_1_5, color='#B7F6FF', alpha=0.2, linewidth=lwidth)
        plt.plot(x,y_1_95, color='#B7F6FF', alpha=0.2, linewidth=lwidth)
        plt.fill_between(x, y_1_5, y_1_95, alpha=0.05, color='#B7F6FF')
        plt.fill_between(x, y_0_5, y_0_95, alpha=0.05, color='#197BB0')

        # plt.set_ylabel('% Residents')
        if scenario[0] == 'wa':
            plt.xlim(0,4)
        else:
            plt.xlim(0,10)
        plt.ylim(0,100)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        if scenario[0] == 'ch':
            plt.xlabel('Distance to nearest operating {}'.format(scenario[2].capitalize()))
        else:
            plt.xlabel('Distance to nearest operating {}'.format(scenario[2].split('_')[0].capitalize() + ' ' + scenario[2].split('_')[1].capitalize()))
        plt.ylabel('% Population')

        plt.savefig(r'/home/mitchell/projects/access_resilience/results/cdf_{}.pdf'.format(scenario[0]), dpi=1000, transparent=True)
        plt.clf()





def bar():
    # import data
    scenarios = [('ch','multi', 'supermarket'), ('wa','liquefaction', 'primary_school'), ('tx','hurricane', 'medical_clinic')]
    df = pd.read_csv('results/plot_results.csv')
    for scenario in scenarios:
        df_plot = df[(df['state']==scenario[0])&(df['hazard']==scenario[1])&(df['dest_type']==scenario[2])]
        df_plot = df_plot[['population_group','number_isolated', 'percent_isolated']]
        groups = list(df_plot['population_group'])
        new_groups = []
        for i in np.arange(len(groups)):
            if groups[i] == 'total_pop':
                new_groups.append('0 All')
            elif groups[i] == 'african_american':
                new_groups.append('1 African American')
            elif groups[i] == 'american_indian_or_alaska':
                new_groups.append('2 American Indian or Inuit')
            elif groups[i] == 'asian':
                new_groups.append('3 Asian')
            elif groups[i] == 'latino':
                new_groups.append('4 Latino')
            elif groups[i] == 'native_hawaiian_or_pi':
                new_groups.append('5 Native Hawaiian or Pacific Islander')
            elif groups[i] == 'white':
                new_groups.append('6 White')
            elif groups[i] == 'maori':
                new_groups.append('1 Māori')
            elif groups[i] == 'melaa':
                new_groups.append('4 Middle Eastern / Latin American / African')
            elif groups[i] == 'polynesian':
                new_groups.append('5 Polynesian')
        df_plot['population_group'] = new_groups
        df_plot = df_plot.sort_values(by=['population_group'])
        df_plot.set_index('population_group', inplace=True)

        fig = plt.figure() # Create matplotlib figure

        ax = fig.add_subplot(111) # Create matplotlib axes
        ax2 = ax.twinx() # Create another axes that shares the same x-axis as ax.
        ax.grid(axis='y')
        width = 0.2

        df_plot.number_isolated.plot(kind='bar', color='#197BB0', ax=ax, width=width, position=1)
        df_plot.percent_isolated.plot(kind='bar', color='#B7F6FF', ax=ax2, width=width, position=0)

        ax.set_ylabel('Isolated Residents')
        ax2.set_ylabel('% Sub-group Isolated')
        ax.spines['top'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        # ax2.grid(axis='y')

        plt.savefig(r'/home/mitchell/projects/access_resilience/results/bar_{}.pdf'.format(scenario[0]), dpi=1000, transparent=True)
        plt.clf()


def recovery():
    os.chdir("results/recovery")
    data = pd.read_csv('new_opt_recovery_supermarket_total_pop.csv')
    random = pd.read_csv('new_random_recovery_supermarket_total_pop.csv')
    inbetweener = pd.read_csv('new_road_h_recovery_supermarket_total_pop.csv')

    data = data[['time', 'iso_supermarket_total_pop', 'ede_supermarket_total_pop']]
    random = random[['time', 'iso_supermarket_total_pop', 'ede_supermarket_total_pop']] 
    inbetweener = inbetweener[['time', 'iso_supermarket_total_pop', 'ede_supermarket_total_pop']] 

    time = list(data['time'])
    time = list(np.arange(-20,-1)) + time
    iso_data, iso_random, ede_data, ede_random = data['iso_supermarket_total_pop'] ,random['iso_supermarket_total_pop'], data['ede_supermarket_total_pop'] ,random['ede_supermarket_total_pop']
    iso_between, ede_between = inbetweener['iso_supermarket_total_pop'] ,inbetweener['ede_supermarket_total_pop']

    iso_data = [list(iso_data)[0]]*len(np.arange(-20,-1)) + list(iso_data)
    iso_random = [list(iso_random)[0]]*len(np.arange(-20,-1)) + list(iso_random)
    ede_data = [list(ede_data)[0]]*len(np.arange(-20,-1)) + list(ede_data)
    ede_random = [list(ede_random)[0]]*len(np.arange(-20,-1)) + list(ede_random)
    iso_between = [list(iso_between)[0]]*len(np.arange(-20,-1)) + list(iso_between)
    ede_between = [list(ede_between)[0]]*len(np.arange(-20,-1)) + list(ede_between)

    # figure out why distance is off

    fig, axes = plt.subplots(2, 1, sharex=True)
    fig.subplots_adjust(hspace=.35)


    ax[0].plot(time, iso_random, label='Randomised recovery', color='#646464', linewidth=lwidth)
    axes[0].plot(time, iso_between, label='Informed recovery', color='#54E848', linewidth=lwidth)
    axes[0].plot(time, iso_data, label='Data-driven recovery', color='#197BB0', linewidth=lwidth)
    axes[0].invert_yaxis()
    #axes[0].set_ylabel('# Isolated Residents')
    axes[0].grid(axis='x')



    axes[1].plot(time, ede_random, label='Randomised recovery', color='#646464', linewidth=lwidth)
    axes[1].plot(time, ede_between, label='Informed recovery', color='#54E848', linewidth=lwidth)
    axes[1].plot(time, ede_data,label='Data-driven recovery', color='#197BB0', linewidth=lwidth)
    axes[1].invert_yaxis()
    #axes[1].set_ylabel('EDE Distance to nearest supermarket')
    axes[1].grid(axis='x')

    # axes = plt.gca()
    # axes.yaxis.grid()
    axes[0].spines['right'].set_visible(False)
    axes[0].spines['top'].set_visible(False)
    axes[1].spines['right'].set_visible(False)
    axes[1].spines['top'].set_visible(False)

    #plt.legend()
    #plt.xlabel('# Restoration Actions Taken')
    plt.savefig(r'/home/mitchell/projects/access_resilience/results/new_recovery_curve.pdf', dpi=1000, transparent=True)



main()