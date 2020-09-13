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

    state_name = state
    port = context['osrm_url'][-4:]
    transport_mode = 'car' #mode_dict[mode]
    directory = '/homedirs/man112/osm_data'

    if sim == True:
        subprocess.Popen(['/bin/bash', 'init_osrm_sim.sh', state_name, port, transport_mode, directory, state])
    elif sim == False:
        subprocess.Popen(['/bin/bash', 'init_osrm.sh', state_name, port, transport_mode, directory, state])



# if __name__ == "__main__":
#     state = input('State: ')
#     main(state)
