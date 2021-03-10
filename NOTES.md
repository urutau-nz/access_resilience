
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


# Setting up the query

1. Get latest OSM data. Type the following into the linux server. This will save the OSM.pbf file into your current directory

```
wget http://download.geofabrik.de/ #find specific location on link
```

2. Set up the docker container. Type the following into linux:
```
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/florida-latest.osm.pbf
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-partition /data/florida-latest.osrm
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-customize /data/florida-latest.osrm
docker run --name osrm-fl -t -i -p 6012:5000 -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-routed --algorithm mld /data/florida-latest.osrm
```


3. Download County Shapefile

4. Download the city boundary shapefile from the city website

5. Overlap (TOOL:intersect) boundary and county shapefiles (After they've been projected on 4269, TOOL: Project) and save the overlap as block as a shapefile (TOOL: Feature to shapefile)

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




300 mm is the average depth at which a passenger vehicles starts to float, and therefore widely recognised as the ultimate thresholds for a safety drive for most of the common cars. https://www.sciencedirect.com/science/article/pii/S1361920916308367
600 mm Maximum wading depth for special vehicles.

