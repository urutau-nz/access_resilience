
# Useful lines
```
# Linux server
ssh man112@132.181.102.8

# Filezilla connection
sftp://132.181.102.8

# SQL
psql -h 132.181.102.2 -p 5001 -U postgres -W

# SQL monte chch
psql monte_christchurch -h 132.181.102.2 -p 5001 -U postgres -W
```


# How to drop roads in OSRM

1. Using OSMNX in python, enter the following to get a shapefile of nodes and road edges:
```
import osmnx as ox
#Get OSM network from a grid of co-ords
G = ox.graph_from_bbox(north, south, east, west, network_type='drive', simplify=False) # N/S/E/W = N/S/E/W most point
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


# Setting up the query

Download routing data from: http://download.geofabrik.de/north-america.html, as osm.pbf by typing in osm_data folder on server, wget 'download link'


Set up Docker

docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/florida-latest.osm.pbf
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-partition /data/florida-latest.osrm
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-customize /data/florida-latest.osrm
docker run --name osrm-fl -t -i -p 6012:5000 -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-routed --algorithm mld /data/florida-latest.osrm


Download County Shapefile from https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2010&layergroup=Blocks

Download the city boundary shapefile from the city website

Overlap (TOOL:intersect) boundary and county shapefiles (After they've been projected on 4269, TOOL: Project) and save the overlap as block as a shapefile (TOOL: Feature to shapefile)

Make database in SQL and ready it for gis
  CREATE DATABASE name;
  CREATE EXTENSION postgis;

Upload block to SQL
shp2pgsql -I -s 4269 /homedirs/man112/monte_christchurch/data/chc_bound/chch_mb.shp block | psql -U postgres -d monte_christchurch -h 132.181.102.2 -p 5001

Get Destination data from overpass turbo (https://overpass-turbo.eu/), download as KML

                *way
                  [shop=supermarket]
                  ({{bbox}});
                (._;>;);
                out;

                node
                  [shop=supermarket]
                  ({{bbox}});
                (._;>;);
                out;

                rel
                  [shop=supermarket]
                  ({{bbox}});
                (._;>;);
                out;*

Import the kml into ARCHGIS and use TOOL:feature to point for points and polygons to get the centroid
Then merge any new layers and export as a SHP with the Z axis disabled

Add sql data to config.py
    *elif state == 'ca':
        db['name'] = 'access_ca'
        context['city_code'] = 'san'
        context['city'] = 'San_Francisco'
        context['osrm_url'] = 'http://localhost:6013'
        context['services'] = ['supermarket', 'hospital']*

Run query to create_dest_table

Run query to create distance

db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
db['con'] = psycopg2.connect(db['address'])
