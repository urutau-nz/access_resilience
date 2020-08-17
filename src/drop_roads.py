'''
Clip osm edges with hazards
get from and to IDs
Save to a csv
'''

from config import *

#import edges
edges = gpd.read_file(r'data/edges.shp')

#import hazard
hazard = gpd.read_file(r'data/esl_aep1_slr150_Project.shp')

#clip roads to hazards
roads_effected = gpd.clip(edges, hazard)

# make list of from and to OSM IDs
df = pd.DataFrame()
df['from_osmid'] = roads_effected['from_']
df['to_osmid'] = roads_effected['to']

# reverse way
df_inv = pd.DataFrame()
df_inv['from_osmid'] = roads_effected['to']
df_inv['to_osmid'] = roads_effected['from_']

df = df.append(df_inv)
df = df.astype(int)

# set edge speeds
df['edge_speed'] = 0
df['edge_rate'] = 0
#df['junk'] = 'junk'

df.to_csv(r'/homedirs/man112/osm_data/updates/updates.csv', header=False, index=False)



#####
lat = []
long = []
orig = lst[0]
dest = lst[-1]
for i in np.arange(0,len(lst)):
    lat.append(lst[i][1])
    long.append(lst[i][0])


plot_path(lat, long, orig, dest)

def plot_path(lat, long, origin_point, destination_point):
    """
    Given a list of latitudes and longitudes, origin
    and destination point, plots a path on a map

    Parameters
    ----------
    lat, long: list of latitudes and longitudes
    origin_point, destination_point: co-ordinates of origin
    and destination
    Returns
    -------
    Nothing. Only shows the map.
    """
    # adding the lines joining the nodes
    fig = go.Figure(go.Scattermapbox(
        name = "Path",
        mode = "lines",
        lon = long,
        lat = lat,
        marker = {'size': 10},
        line = dict(width = 4.5, color = 'blue')))
    # adding source marker
    fig.add_trace(go.Scattermapbox(
        name = "Source",
        mode = "markers",
        lon = [origin_point[0]],
        lat = [origin_point[1]],
        marker = {'size': 12, 'color':"red"}))
    # adding destination marker
    fig.add_trace(go.Scattermapbox(
        name = "Destination",
        mode = "markers",
        lon = [destination_point[0]],
        lat = [destination_point[1]],
        marker = {'size': 12, 'color':'green'}))
    # getting center for plots:
    lat_center = np.mean(lat)
    long_center = np.mean(long)
    # defining the layout using mapbox_style
    fig.update_layout(mapbox_style="stamen-terrain",
        mapbox_center_lat = 30, mapbox_center_lon=-80)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      mapbox = {
                          'center': {'lat': lat_center,
                          'lon': long_center},
                          'zoom': 12})
    fig.write_image("data/fig2.png")
