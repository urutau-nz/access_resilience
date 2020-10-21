'''opens and formats hazard shapefile'''
from config import *

def open_hazard(hazard_type, db, context):
    '''opens and formats hazard'''
    sql = "SELECT * FROM destinations"
    dest_gdf = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
    exposure_df = pd.DataFrame(columns={'dest_id', 'exposure'})
    #shapefile format is different for each city, need to make a common format
    if hazard_type == 'liquefaction':
        if context['city'] == 'christchurch':
            filename = '/homedirs/dak55/monte_christchurch/data/{}/hazard/liquefaction_vulnerability.shp'.format(context['city'])
            hazard = gpd.read_file(filename)
            #exclude unnecessary columns
            hazard = hazard[['Liq_Cat', 'geometry']]
            #catagorize all exposure as no, low, medium or high
            hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Possible', 'Medium Liquefaction Vulnerability'], 'med')
            hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Unlikely', 'Low Liquefaction Vulnerability'], 'low')
            hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['High Liquefaction Vulnerability'], 'high')
            #change name of column to generalise
            hazard.rename(columns={'Liq_Cat':'exposure_catagory'}, inplace=True)

        elif context['city'] == 'seattle':
            filename = '/homedirs/dak55/monte_christchurch/data/{}/hazard/liquefaction_susceptibility_2.shp'.format(context['city'])
            hazard = gpd.read_file(filename)
            #exclude unnecessary columns
            hazard = hazard[['LIQUEFAC_1', 'geometry']]
            #catagorize all exposure as no, low, medium or high
            hazard['LIQUEFAC_1'] = hazard['LIQUEFAC_1'].replace(['low to moderate', 'moderate to high'], 'med')
            hazard['LIQUEFAC_1'] = hazard['LIQUEFAC_1'].replace(['very low to low'], 'low')
            hazard['LIQUEFAC_1'] = hazard['LIQUEFAC_1'].replace(['very low', 'N/A (peat)', 'N/A (water)', 'N/A (bedrock)'], 'none')
            #change name of column to generalise

            hazard.rename(columns={'LIQUEFAC_1':'exposure_catagory'}, inplace=True)
        #set up possible states
        exposure_level = ['low', 'med', 'high']
        #determine which exposure level each destination is in
        for i in range(0, 3):
            exposure = hazard.loc[hazard['exposure_catagory'] == '{}'.format(exposure_level[i])]
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

    elif hazard_type == 'hurricane':
        hur = rio.open('/homedirs/man112/monte_christchurch/data/houston/hazard/harvey_inundation/harris_dgft_tif.tif',mode='r+')
        #code.interact(local=locals())
        #get x,y point values of all dests
        dest_coords = [(x,y) for x, y in zip(dest_gdf.geom.x, dest_gdf.geom.y)]
        #find corresponding inundation depth for each dest
        dest_gdf['inundation_depth'] = [x[0] for x in hur.sample(dest_coords)]
        #set unaffected dests to 0 m depth
        dest_gdf['inundation_depth'] = dest_gdf['inundation_depth'].replace([3.4028234663852886e+38], 0)
        #change from ft to m
        dest_gdf['inundation_depth'] = dest_gdf['inundation_depth'] * 0.3048
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

    elif hazard_type == 'multi': #only available for chch at this stage
        #get tsunami data
        tsu = rio.open('/homedirs/dak55/monte_christchurch/data/christchurch/hazard/tsunami/tsunami.tif')
        #get x,y point values of all dests
        dest_coords = [(x,y) for x, y in zip(dest_gdf.geom.x, dest_gdf.geom.y)]
        #find corresponding inundation depth for each dest
        dest_gdf_tsu = dest_gdf.copy()
        dest_gdf_tsu['inundation_depth'] = [x[0] for x in tsu.sample(dest_coords)]
        #low, medium, high catagories for discrete fragility curve
        bands = [(0, 0.5), (0.5, 2), (2, 1000)]
        exposure_level = ['low', 'med', 'high']
        exposure_tsu = pd.DataFrame(columns={'dest_id', 'tsu_exp'})
        for i in range(0, 3):
            #subset dests that are exposed at particular level
            exposed_dests = dest_gdf.loc[(dest_gdf_tsu['inundation_depth'] > bands[i][0]) & (dest_gdf_tsu['inundation_depth'] <= bands[i][1])]
            ids = exposed_dests['id']
            #formats for append
            temp_df = pd.DataFrame()
            temp_df['dest_id'] = ids
            temp_df['tsu_exp'] = exposure_level[i]
            #append to df
            exposure_tsu = pd.concat([exposure_tsu, temp_df], ignore_index=False)

        #get liquefaction data
        filename = '/homedirs/dak55/monte_christchurch/data/{}/hazard/liquefaction_vulnerability.shp'.format(context['city'])
        hazard = gpd.read_file(filename)
        #exclude unnecessary columns
        hazard = hazard[['Liq_Cat', 'geometry']]
        #catagorize all exposure as no, low, medium or high
        hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Possible', 'Medium Liquefaction Vulnerability'], 'med')
        hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['Liquefaction Damage is Unlikely', 'Low Liquefaction Vulnerability'], 'low')
        hazard['Liq_Cat'] = hazard['Liq_Cat'].replace(['High Liquefaction Vulnerability'], 'high')
        #change name of column to generalise
        hazard.rename(columns={'Liq_Cat':'exposure_catagory'}, inplace=True)
        exposure_liq = pd.DataFrame(columns={'dest_id', 'liq_exp'})
        for i in range(0, 3):
            exposure = hazard.loc[hazard['exposure_catagory'] == '{}'.format(exposure_level[i])]
            exposed_dests = gpd.clip(dest_gdf, exposure)
            ids = exposed_dests['id']
            #formats for append
            temp_df = pd.DataFrame()
            temp_df['dest_id'] = ids
            temp_df['liq_exp'] = exposure_level[i]
            #append to df
            exposure_liq = pd.concat([exposure_liq, temp_df], ignore_index=False)
        #merge exposure levels into both df
        dest_gdf = pd.merge(dest_gdf, exposure_tsu, left_on='id', right_on='dest_id', how='left').drop('dest_id', axis=1)
        dest_gdf = pd.merge(dest_gdf, exposure_liq, left_on='id', right_on='dest_id', how='left').drop('dest_id', axis=1)
        dest_gdf.fillna(value='none', inplace=True)
        #increase exposure level of dests that are exposed to both hazards. e.g low+low=med, low+med=med, med+med=high, high+med=veryhigh, high+high=veryhigh
        el = ['none', 'low', 'med', 'high', 'very_high']
        exposure_level = ['low', 'med', 'high', 'very_high']
        conditions = []
        conditions.append(((dest_gdf['tsu_exp'] == el[1]) & (dest_gdf['liq_exp'] == el[0])) | ((dest_gdf['tsu_exp'] == el[0]) & (dest_gdf['liq_exp'] == el[1])))
        conditions.append(((dest_gdf['tsu_exp'] == el[2]) & (dest_gdf['liq_exp'] == el[0])) | ((dest_gdf['tsu_exp'] == el[0]) & (dest_gdf['liq_exp'] == el[2])) | ((dest_gdf['tsu_exp'] == el[2]) & (dest_gdf['liq_exp'] == el[1])) | ((dest_gdf['tsu_exp'] == el[1]) & (dest_gdf['liq_exp'] == el[2])) | ((dest_gdf['tsu_exp'] == el[1]) & (dest_gdf['liq_exp'] == el[1])))
        conditions.append(((dest_gdf['tsu_exp'] == el[3]) & (dest_gdf['liq_exp'] == el[0])) | ((dest_gdf['tsu_exp'] == el[0]) & (dest_gdf['liq_exp'] == el[3])) | ((dest_gdf['tsu_exp'] == el[3]) & (dest_gdf['liq_exp'] == el[1])) | ((dest_gdf['tsu_exp'] == el[1]) & (dest_gdf['liq_exp'] == el[3])) | ((dest_gdf['tsu_exp'] == el[2]) & (dest_gdf['liq_exp'] == el[2])))
        conditions.append(((dest_gdf['tsu_exp'] == el[3]) & (dest_gdf['liq_exp'] == el[3])) | ((dest_gdf['tsu_exp'] == el[0]) & (dest_gdf['liq_exp'] == el[4])) | ((dest_gdf['tsu_exp'] == el[3]) & (dest_gdf['liq_exp'] == el[2])) | ((dest_gdf['tsu_exp'] == el[2]) & (dest_gdf['liq_exp'] == el[3])))
        dest_gdf.rename(columns={'id':'dest_id'}, inplace=True)
        dest_gdf['exposure'] = np.select(conditions, exposure_level)
        exposure_df = dest_gdf.loc[dest_gdf['exposure'] != '0']
        exposure_df = exposure_df[['dest_id', 'exposure']]

    #f|mat exposure_df
    exposure_df.reset_index(inplace=True, drop=True)
    return exposure_df
