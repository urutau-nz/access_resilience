from config import *

def remove_zero(db, context):
    '''removes each block that has noone living in them to improve query efficiency.
     usually these are water, this process is formatted for US census blocks'''
     #creates df of geoid10 indexes
    sql = "SELECT * FROM block"
    orig_df = pd.read_sql(sql, db['con'])
    #sorts and indexes by geoid10 of the blocks
    orig_df = orig_df.sort_values(by='geoid10', axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')
    orig_df = orig_df.set_index('geoid10')

    #opening total population stats for each block
    sql = """SELECT "H7X001", geoid10 FROM demograph"""
    demo_df = pd.read_sql(sql, db['con'])
    #orders by geoid and sets it as the index
    demo_df = demo_df.sort_values(by='geoid10', axis=0, ascending=True, inplace=False, kind='quicksort', na_position='last')
    demo_df = demo_df.set_index('geoid10')

    orig_df['population'] = demo_df.H7X001
    #so we can retrieve rows based on geoid10 later
    orig_df.reset_index(inplace=True)
