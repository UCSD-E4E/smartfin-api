import requests
import json 
import pandas as pd
from datetime import datetime

PLATFORM_API = 'https://stage.platforms.axds.co'

class SmartfinScraper:

    def __init__(self):
        print("web scraper initialized")

    
    def get_ride_data (self, ride_id):
                
        search_tag = f'packrat_source_id:{ride_id}'
        response = requests.get(f'{PLATFORM_API}/tags/search/{search_tag}', params={'verbosity' : 2})
        session = response.json()['tags'][search_tag]


        url = ''
        for k, c in session.items():
            file = session[k]['files']
            for fname, fc in file.items():
                if fname.endswith('csv'):
                    url = fc['url'] 

        

        if (url != ''):             

            # data cleaning
            df = pd.read_csv(url, index_col=None, header=0)
            df = df.sort_values('time', axis=0)
            df = df.drop(['text', 'epoch', 'type_name', 'fin_id', 'session_id', 'batt_v'], axis=1)
            df = df[df['az'].notna()]
            df = df.set_index('time')
            df['timestamp'] = [datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f").timestamp() for date in df.index]

            return df

        else:
            print('ride not found')
            df = pd.DataFrame() # empty DF just so something is returned
            return df
    
    def fetch_session_ids (self):
        search_tag = f'packrat_source_id:Sfin*'
        response = requests.get(f'{PLATFORM_API}/tags/search/{search_tag}', params={ 'verbosity': 1 })

        return response.json()['tags']