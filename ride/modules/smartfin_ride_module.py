import requests

from .double_integral_bandpass import double_integral_bandpass_filter
from .smartfin_web_scrape import SmartfinScraper
from .cdip_web_scrape import CDIPScraper
from datetime import datetime



"""
Smartfin Web Scrape API is an interface that allows smartfin users to get data of their smartfin ride. This module interacts with both the smartfin website and CDIP THREDDS API to get smartfin and CDIP data. 
"""
class RideModule:
    
    def __init__(self): 
        print('ride initialized')

    
    def fetch_session_ids(self):
        sWebScrape = SmartfinScraper()
        return sWebScrape.fetch_session_ids()

        
    # MAIN RIDE FUNCTION
    def get_ride_data(self, ride_id, buoys):
        """
        adds a ride dataframe to this dictionary 
        
        """

        sWebScrape = SmartfinScraper()
        df = sWebScrape.get_ride_data(ride_id)

        if len(df) == 0:
            print('ERROR: Ride has no valid data, returning...')
            return {}
       
        latitude = df['latitude'].mean() 
        longitude = df['longitude'].mean()

        # get timeframe
        start_time, end_time = self.get_timeframe(df)
        print(f'calculated start_time: {start_time}')
        print(f'calculated end_time: {end_time}')
        
        cWebScrape = CDIPScraper()
        mean_CDIP, means_CDIP, temp_CDIP, temps_CDIP, nearest_CDIP, df_CDIP = cWebScrape.CDIP_web_scrape(start_time, end_time, latitude, longitude, buoys)
        print(f'retrieved nearest CDIP buoy: {nearest_CDIP}')
        print(f'retrieved CDIP mean height for ride: {mean_CDIP}')
        print(f'retrieved CDIP mean temp for ride: {temp_CDIP}')


        height_smartfin, height_list, height_sample_rate = self.calculate_ride_height(df)
        temp_smartfin, temp_list, temp_sample_rate = self.calculate_ride_temp(df)


        print('finding cities near', latitude, longitude)
        loc1, loc2, loc3 = self.get_nearest_city(latitude, longitude)
        
        print('uploading ride data to database...')

        # compress dataframes and save path
        df_path = f"ride/data_csvs/{ride_id}.csv"
        df.to_csv(df_path)
        df_CDIP_path = f"ride/data_csvs/{ride_id}_CDIP.csv"
        df_CDIP.to_csv(df_CDIP_path)

        # format data into dict for ride model
        data = {
            'rideId': ride_id, 
            'loc1': loc1,
            'loc2': loc2,
            'loc3': loc3,
            'startTime': int(start_time),
            'endTime': int(end_time),
            'heightSmartfin': height_smartfin,
            'tempSmartfin': temp_smartfin,
            'buoyCDIP': nearest_CDIP, 
            'heightCDIP': mean_CDIP, 
            'tempCDIP': temp_CDIP, 
            'latitude': latitude,
            'longitude': longitude,
        }
    
        return data, df_path, df_CDIP_path
     
    

    # HELPER FUNCTIONS    
    # these two functions are temporary and will be edited when we refine them
    def calculate_ride_height(self, df): 
        
        filt = double_integral_bandpass_filter()
        height_smartfin, height_list, height_sample_rate = filt.calculate_ride_height(df)

        print(f'calculated smartfin significant wave height: {height_smartfin}')
        print(f'height reading sample rate: {height_sample_rate}')
        return height_smartfin, height_list, height_sample_rate 


    def calculate_ride_temp(self, df):
        temps = df['temperature']
        temp = temps.mean()
        temps = list(temps)
        print(f'calculated smartfin ride temp: {temp}')
        tempSampleRate = (int(df.iloc[1]['timestamp']) - int(df.iloc[0]['timestamp']))
        print(f'temperature reading sample rate: {tempSampleRate}')

        return temp, temps, tempSampleRate


    def get_nearest_city(self, latitude, longitude):
        key = "AIzaSyCV3zZ2YhNOsf9DN8CvSiH1NBJC3XdMYs4"
        url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&sensor=true&key={key}'
        response = requests.get(url).json()
        # print('google maps response', response)

        if (response['status'] == "INVALID_REQUEST"):
            return 'N/A', 'N/A', 'N/A'

        loc1 = (response['results'][0]['address_components'][2]['long_name'])
        loc2 = (response['results'][0]['address_components'][3]['long_name'])
        loc3 = (response['results'][0]['address_components'][4]['long_name'])
        
        return loc1, loc2, loc3

    
    def get_timeframe(self, df):
        
        # get the times of the first and last reading
        start_time = df.iloc[0]['timestamp']
        end_time = df.iloc[-1]['timestamp']
        return start_time, end_time

    def get_CDIP_stations(self):
        cws = CDIPScraper()
        return cws.get_CDIP_stations()
    

        