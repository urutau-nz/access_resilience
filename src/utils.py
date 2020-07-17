'''
General functions that support the project
- import_csv for csv -> postgres db
-
'''
# user defined variables
state = 'wa'
from config import *
db, context = cfg_init(state)

import yagmail


def send_email(body):
    # send an email

    receiver = "man112@uclive.ac.nz"
    # filename = "document.pdf"

    yag = yagmail.SMTP('toms.scrapers',open('pass_email.txt', 'r').read().strip('\n'))
    yag.send(
        to=receiver,
        subject="Your code notification",
        contents=body,
        # attachments=filename,
    )


def import_csv(db):
    '''
    import a csv into the postgres db
    '''
    elif state == 'wa':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '033'
    elif state == 'tx':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '201'
    #
    table_name = 'demograph'
    # add csv to nc.demograph
    df = pd.read_csv(file_name, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLOCKA':str, 'H7X001':int, 'H7X002':int, 'H7X003':int, 'H7X004':int, 'H7X005':int, 'H7Y003':int})
    df = df[df.COUNTYA==county]
    df['geoid10'] = df['STATEA'] + df['COUNTYA'] + df['TRACTA'] + df['BLOCKA']

    df_filt = pd.DataFrame()
    df_filt['geoid10'] = df['geoid10']
    df_filt['H7X001'] = df['H7X001']
    df_filt['H7X002'] = df['H7X002']
    df_filt['H7X003'] = df['H7X003']
    df_filt['H7X004'] = df['H7X004']
    df_filt['H7X005'] = df['H7X005']
    df_filt['H7Y003'] = df['H7Y003']
    df_filt.to_sql(table_name, db['engine'])
    # add the table indices

    cursor = db['con'].cursor()
    queries = ['CREATE INDEX "geoid10" ON demograph ("geoid10");']
    for q in queries:
        cursor.execute(q)
    # commit
    db['con'].commit()


#if __name__ == '__main__':
    #import_csv(db)
