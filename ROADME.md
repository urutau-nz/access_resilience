# How to drop roads in OSRM

1. Using OSMNX in python, enter the following to get a shapefile of nodes and road edges:
```
import osmnx as ox
#Get OSM network from a grid of co-ords
G = ox.graph_from_bbox(north, south, east, west, network_type='drive', simplify=False) # N/S/E/W = N/S/E/W most point
# Houston (30.2566308, 29.4393792, -94.8779992, -96.0635489)
# Seattle (47.7574682, 47.4564817, -122.1985686, -122.4868201)
# Save file
ox.save_graph_shapefile(G, file_path)
```
2. Create a csv file of edges to change the traffic speed on. This will be done by overlaying a hazard to the new edge shapefile and creating a list of all the 'from' and 'to' OSM IDs asscociated with each edge. Your update.csv will look something like this:
```
from_osmid, to_osmid, new_speed(km/h)
to_osmid, from_osmid, new_speed(km/h)
```
Make sure you reverse each id pair you enter so that the speed is changed in both directions on the road

3. Set up the docker (Using NZ example and port 6015), on the server the update.csv file is within osm_data/upates/.
```
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/new-zealand-latest.osm.pbf
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-partition /data/new-zealand-latest.osrm
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-customize /data/new-zealand-latest.osrm --segment-speed-file /data/updates/update.csv
docker run --name nz_test -t -i -p 6015:5000 -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-routed --algorithm mld /data/new-zealand-latest.osrm
```
4. Query the new OSRM network
