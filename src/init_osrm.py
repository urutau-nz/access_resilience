import subprocess
from config import *

mode_dict = {'driving':'car','walking':'foot','cycling':'bicycle'}

def main(sim, state, context):
    ''' run the shell script that
    - removes the existing docker
    - downloads the osrm files
    - establishes the osrm routing docker
    '''
    context = cfg_init(state)[1]

    state_name = context['state']
    continent = context['continent']
    port = context['osrm_url'][-4:]
    transport_mode = 'car' #mode_dict[mode]
    directory = '/home/mitchell/projects/access_resilience/data/osm'

    if sim == True:
        subprocess.call(['/bin/bash', 'src/init_osrm_sim.sh', state_name, port, transport_mode, directory, state, continent])
    elif sim == False:
        subprocess.call(['/bin/bash', 'src/init_osrm.sh', state_name, port, transport_mode, directory, state, continent])



# if __name__ == "__main__":
#     state = input('State: ')
#     main(state)
