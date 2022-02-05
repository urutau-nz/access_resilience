import seaborn as sns
import matplotlib.pyplot as plt
import os 
import pandas as pd
import numpy as np

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


axes[0].plot(time, iso_random, label='Randomised recovery', color='darkgrey')
axes[0].plot(time, iso_between, label='Informed recovery', color='olive')
axes[0].plot(time, iso_data, label='Data-driven recovery', color='royalblue')
axes[0].invert_yaxis()
#axes[0].set_ylabel('# Isolated Residents')
axes[0].grid(axis='x')



axes[1].plot(time, ede_random, label='Randomised recovery', color='darkgrey')
axes[1].plot(time, ede_between, label='Informed recovery', color='olive')
axes[1].plot(time, ede_data,label='Data-driven recovery', color='royalblue')
axes[1].invert_yaxis()
#axes[1].set_ylabel('EDE Distance to nearest supermarket')
axes[1].grid(axis='x')

# axes = plt.gca()
# axes.yaxis.grid()

#plt.legend()
#plt.xlabel('# Restoration Actions Taken')
plt.savefig(r'/home/mitchell/projects/access_resilience/results/new_recovery_curve', dpi=1000)
