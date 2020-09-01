import subprocess
from config import *

mode_dict = {'driving':'car','walking':'foot','cycling':'bicycle'}

def main(state, mode=mode_dict[0]):
    ''' run the shell script that
    - removes the existing docker
    - downloads the osrm files
    - establishes the osrm routing docker
    '''
    context = cfg_init(state)[1]

    state_name = context['state']
    port = context['port']
    transport_mode = mode_dict[mode]
    directory = '/homedirs/man112/osm_data'

    subprocess.check_call(['/bin/bash', 'init_osrm.sh', state_name, port, transport_mode, directory, state])


if __name__ == "__main__":
    state = input('State: ')
    main(state)
