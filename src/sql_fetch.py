from config import *

state = input("State: ")
db, context = cfg_init(state)

geom = input("Use geometry [True, False]: ")
table_name = input("Table name: ")

if geom == "True":
    df = gpd.GeoDataFrame.from_postgis("SELECT * FROM {}".format(table_name), db['con'], geom_col='geom')
else:
    df = pd.read_sql('SELECT * FROM {}'.format(table_name), db['con'])

print("Successfully read in {}".format(table_name))

save_or_edit = input("Would you like to save the dataframe or edit it in Python? [save, edit]: ")

if save_or_edit == 'save':
    file_path = input("Filepath to save to: ")
    if geom == "True":
        df.to_file(r'{}/{}.shp'.format(file_path, table_name))
    else:
        df.to_csv(r'{}/{}.csv'.format(file_path, table_name))
elif save_or_edit == 'edit':
    code.interact(local=locals())


