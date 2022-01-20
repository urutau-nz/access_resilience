# Monte Christchurch
## ENCN493 Research Project: TLO-01
###### Dai Kiddle, Mitchell Anderson, Tom Logan (Supervisor)

*A framework to evaluate access distributions of cities to essential
services/destinations with imposed natural hazards.*

Using Monte Carlo Simulation, this approach allows urban planners to evaluate access resilience within a community.
This enables the identification of (1) potentially vulnerable communities or demographic groups, and
(2) critical amenity nodes or transport links. This will also aid (1) vulnerability assessments, (2) pre and post hazard investment prioritisation

<<<<<<< HEAD
###### Data Inputs:

(1) Block Level Demographic Data
=======
Simulation determines which roads and destinations are exposed in initiialise_hazard.py and drop_raods.py
it then closes destinations and certain routes based on a two damage state fragility curve process
outlined in the close_destinations.py and drop_roads.py files.
program.py will run this simulation and save results to sql

Running compile_results.py will then format the big nearest_matrix to be ready for plotting
>>>>>>> 6dcfc583694a33c172dcd1a12325a23854258b71

(2) OSM Transport Network

(3) Amenity Network

(4) Hazard Data (Inundation/flooding: Raster, Liquefaction: Shapefile)

###### Method:

(1) Quantify access performance and equity in a business as usual case

(2) Simulate a hazard event. Based on some fragilities, 'close' road segments and services

(3) Re-model the transport and service network

(4) Quantify the new level of access

(5) Repeat (3) & (4) n times for Monte Carlo

(6) Quantify uncertainty and mean of post hazard access

(7) Visualize (ECDF & Maps)
