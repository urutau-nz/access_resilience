## Dropping Roads

### Two Methods
1. Traffic Updates
2. Create new .pbf file


#### Traffic Updates
While OSRM backend has said they are not looking to include the function to 'close' roads,
they have advocated the use of 'traffic updates' where we set the new traffic speed of a way to 0.
Notes on the matter can be found below:
1. Traffic update documentation: https://github.com/Project-OSRM/osrm-backend/wiki/Traffic
2. Traffic updates for road closures: https://github.com/Project-OSRM/osrm-backend/issues/1313

###### My progress
So far I have been able to create new OSRM servers using the '--contract' function and a csv of from_osmid, to_osmid, edge_speed, and edge_rate.
With the csv being generated both manually for a single street segment (way), and also from clipping a SLR hazard extent.
This way of creating a new routing server makes it such that the 'business as usual' server is always faster than the other.
However, the hazard edited server does not take a logical route to the destination.
This has been shown by using the plot_routes.py script which takes an input of Coordinates (generated from the curl request when annotations of 'overview=full&geometries=geojson' are added) and returns a png file within the server showing the route taken.

All servers have been set up for car.lua and all curl requests have been made for driving.

Using osmnx I have created a shapefile for christchurch that clearly outlines the available routes. This file named 'edges.shp' is mandatory for this process of finding the specific osm ids for each 'way'.

An example of the docker set up can be seen below:

```
docker kill osmnx # stop any running dockers in the name of X
docker rm osmnx # remove any dockers with name X

docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/new-zealand-latest.osm.pbf
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-partition /data/new-zealand-latest.osrm

# note the osrm-contract and the update.csv file
docker run -t -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-customize /data/new-zealand-latest.osm.pbf --segment-speed-file /data/updates/update_road.csv

# note the docker name of 'osmnx' and port of 6012
docker run --name nz_test -t -i -p 6016:5000 -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-routed --algorithm mld /data/new-zealand-latest.osrm
```

I'd like to try not using the mld algorithm and see if that changes things.
Notes on this are at the end of the first github link.
.
Then the route I have been testing is as follows:

1. Start point: 172.698460,-43.404104
2. End point: 172.691915,-43.429373

Base case (no hazards): curl "http://localhost:6001/route/v1/driving/172.698460,-43.404104;172.691915,-43.429373?overview=full&geometries=geojson"

New case: curl "http://localhost:6016/route/v1/driving/172.698460,-43.404104;172.691915,-43.429373?overview=full&geometries=geojson"








#### Create new .pbf file
Inverse clip and figure out how to save a shapefile as a .pbf
