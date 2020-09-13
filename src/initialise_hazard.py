'''opens and formats hazard shapefile'''
from config import *

def open_hazard(hazard_type, db, context):
    '''opens and formats hazard'''
    sql = "SELECT * FROM destinations"
    dest_gdf = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
    exposure_df = pd.DataFrame(columns={'dest_id', 'exposure'})

    if hazard_type == 'liquefaction':
        filename = '/homedirs/dak55/monte_christchurch/data/christchurch/hazard/liquefaction_vulnerability.shp'
        hazard = gpd.read_file(filename)
        #exclude unnecessary columns
        hazard = hazard[['Liq_Cat', 'geometry']]
        #catagorize all exposure as no, low, medium or high
        hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Possible'], 'Medium Liquefaction Vulnerability')
        hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Unlikely'], 'Low Liquefaction Vulnerability')
        #set up possible states
        string_name = ['Low Liquefaction Vulnerability', 'Medium Liquefaction Vulnerability', 'High Liquefaction Vulnerability']
        exposure_level = ['low', 'med', 'high']
        for i in range(0, 3):
            exposure = hazard.loc[hazard['Liq_Cat'] == '{}'.format(string_name[i])]
            exposed_dests = gpd.clip(dest_gdf, exposure)
            ids = exposed_dests['id']
            #formats for append
            temp_df = pd.DataFrame()
            temp_df['dest_id'] = ids
            temp_df['exposure'] = exposure_level[i]
            #append to df
            exposure_df = pd.concat([exposure_df, temp_df], ignore_index=False)

    elif hazard_type == 'tsunami':
        #open raster file
        tsu = rio.open('/homedirs/dak55/monte_christchurch/data/christchurch/hazard/tsunami/tsunami.tif')
        #get x,y point values of all dests
        dest_coords = [(x,y) for x, y in zip(dest_gdf.geom.x, dest_gdf.geom.y)]
        #find corresponding inundation depth for each dest
        dest_gdf['inundation_depth'] = [x[0] for x in tsu.sample(dest_coords)]
        #low, medium, high catagories for discrete fragility curve
        bands = [(0, 0.5), (0.5, 2), (2, 1000)]
        exposure_level = ['low', 'med', 'high']
        for i in range(0, 3):
            #subset dests that are exposed at particular level
            exposed_dests = dest_gdf.loc[(dest_gdf['inundation_depth'] > bands[i][0]) & (dest_gdf['inundation_depth'] <= bands[i][1])]
            ids = exposed_dests['id']
            #formats for append
            temp_df = pd.DataFrame()
            temp_df['dest_id'] = ids
            temp_df['exposure'] = exposure_level[i]
            #append to df
            exposure_df = pd.concat([exposure_df, temp_df], ignore_index=False)

    #format exposure_df
    exposure_df.reset_index(inplace=True, drop=True)
    return exposure_df
