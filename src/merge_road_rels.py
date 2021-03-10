'''
Searches through a list of road segments and joins them together if matching IDs
'''

import pandas as pd
import numpy as np
from tqdm import tqdm
import geopandas as gpd

def main():
    df = import_data()
    froms = list(df['from_osmid'].unique())
    tos = list(df['to_osmid'].unique())
    froms.extend(tos)
    osmids = list(np.unique(froms))
    i = 1
    for osmid in tqdm(osmids):
        indexs = []
        if len(df[(df['from_osmid']==osmid)]) != 0:
            indexs.extend(list(df[(df['from_osmid']==osmid)].index))
        if len(df[(df['to_osmid']==osmid)]) != 0:
            indexs.extend(list(df[(df['to_osmid']==osmid)].index)) #get list of indexs where this osmid occurs
        # add i to option column (if option columns != Nan, use that i value to match other osmids)
        for j in indexs:
            if df['option'].loc[j] == 0:
                df['option'].loc[j] = int(i)
            elif df['option'].loc[j] != 0:
                option_num = df['option'].loc[j]
                df['option'].loc[j] = option_num
        i += 1

    city = 'christchurch'
    edges = gpd.read_file(r'/homedirs/man112/monte_christchurch/data/{}/road_edges/edges.shp'.format(city))
    edges.rename(columns={'from_':'from'}, inplace=True)
    edges= edges.drop(columns = ['name', 'highway', 'oneway','access','lanes', 'service', 'maxspeed', 'junction', 'ref', 'bridge', 'width', 'tunnel', 'u', 'v', 'key'])
    edges['option'] = 0
    for i in tqdm(range(len(df))):
        tid = df['from_osmid'].iloc[i]
        fid = df['to_osmid'].iloc[i]
        option = df['option'].iloc[i]
        edges.loc[list(edges.loc[(edges['from'].isin([tid, fid])) & (edges['to'].isin([tid, fid]))].index), 'option'] = option
    new_edges = edges.drop(list(edges.loc[edges['option']==0].index))


def import_data():
    df = pd.read_csv(r'/homedirs/man112/osm_data/updates/update.csv', names=['from_osmid', 'to_osmid', 'edge_speed', 'num_sim', 'option'])
    df = df.drop(np.arange(0,len(df)/2)) # drops half as are inversed, must add back in later
    df['option'] = 0
    return(df)



if __name__ == "__main__":
    main()