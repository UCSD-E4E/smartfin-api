import netCDF4
import numpy as np
import requests
import datetime
from bs4 import BeautifulSoup
import pandas as pd



class CDIPScraper:

    def __init__(self):
        print('cdip scraper intialized')

        
        
    def CDIP_web_scrape(self, start_time, end_time, latitude, longitude, buoys):
                
        # get nearest station
        station = self.get_nearest_station(latitude, longitude, buoys)
        
        data_url = f'http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/archive/{station}p1/{station}p1_historic.nc'
        print(f'retriving CDIP wave heights from: {data_url}')
        
        # netCDF data object fetched from CDIP API
        nc = netCDF4.Dataset(data_url)
        
        # GET WAVE DATA
        # UNIX based time from 1991-yeardate in 30 minute increments
        waveTime = nc.variables['waveTime'][:]

        # wave heights
        Hs = nc.variables['waveHs'][:]
        
        # find the 30 minute chunks that correspond with smartfin ride timeframe
        unixstart = start_time
        nearest_date = self.find_nearest(waveTime, unixstart)  # Find the closest unix timestamp
        wave_start_index = np.where(waveTime==nearest_date)[0][0]  # Grab the index number of found date

        unixend = end_time
        future_date = self.find_nearest(waveTime, unixend)  # Find the closest unix timestamp
        wave_end_index = np.where(waveTime==future_date)[0][0]  # Grab the index number of found date 

        if (wave_start_index - wave_end_index == 0): wave_end_index += 1


        # CHECK START AND END INDICES AND WHY THEY ARE THE SAME FOR TEMPS BUT NOT HEIGHTS

        # account for index offsets
#         wave_start_index -= 14
#         wave_end_index -= 14
        
        print(f'calculating significant wave height between {start_time} - {end_time}')
        
        # all wave height averages per 30 minute increments over each month
        ride_hs = Hs[wave_start_index:wave_end_index]
        ride_hs = ride_hs.data
       
        # GET XYZ ACCELERATIONS
        #print('getting acceleration data#')
        
        #  df_CDIP = self.get_acc_df(station, unixstart, unixend)
    
        # GET TEMPERATURE DATA
        # UNIX based time from 1991-yeardate in 30 minute increments
        sstTime = nc.variables['sstTime'][:]
        # ocean temp
        Ts = nc.variables['sstSeaSurfaceTemperature'][:]
        
        # find the 30 minute chunks that correspond with smartfin ride timeframe
        unixstart = start_time
        
        
        print('unixstart', unixstart)
        nearest_date = self.find_nearest(sstTime, unixstart)  # Find the closest unix timestamp
        print('nearestdate', nearest_date )
        temp_start_index = np.where(sstTime==nearest_date)[0][0]  # Grab the index number of found date

        unixend = end_time
        print('unixend', unixend)

        future_date = self.find_nearest(sstTime, unixend)  # Find the closest unix timestamp
        print('futuredate', future_date)
        temp_end_index = np.where(sstTime==future_date)[0][0]  # Grab the index number of found date 

        if (temp_start_index == temp_end_index): temp_end_index += 1
        
#         temp_start_index -= 14
#         temp_end_index -= 14
                
        print("temperature indices", temp_start_index, temp_end_index)
            
        # get ocean surface temperature during ride
        ride_ts = Ts[temp_start_index:temp_end_index]
        # print('startindex', temp_start_index)
        # print('endex,',temp_end_index)
        # print('ridets', Ts)
        ride_ts = ride_ts.data
   
        # CALCULATE MEANS of each month dataset in box_data
        mean_h = ride_hs.mean()
        mean_t = ride_ts.mean()
        
        print(f'mean wave height: {mean_h}')
        print(f'mean ocean temp: {mean_t}')
        
        return mean_h, list(ride_hs), mean_t, list(ride_ts), station


    def get_acc_df(self, stn, unixstart, unixend):

        qc_level = 2 # Filter data with qc flags above this number 
        findingDeployment = True
        deploy = 1
        unixstart = int(unixstart)
        unixend = int(unixend)

        while(findingDeployment):
        
            print('deploy number', deploy)
            try: 
                deployStr = ''
                if (deploy < 10):
                    deployStr = '0' + str(deploy)
                else:
                    deployStr = str(deploy)

                data_url = 'http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/archive/' + stn + 'p1/' + stn + 'p1_d' + deployStr + '.nc'
                
                print('fetching CDIP data from', data_url)
                nc = netCDF4.Dataset(data_url)
                # Find UNIX timestamps for human-formatted start/end dates
                print('fetching acceleration data')
                
                ncTime = nc.variables['waveTime'][:]
                filterdelay = nc.variables['xyzFilterDelay']
                starttime = nc.variables['xyzStartTime'][:] # Variable that gives start time for buoy data collection
                samplerate = nc.variables['xyzSampleRate'][:] # Variable that gives rate (frequency, Hz) of sampling

                # Specify variables to automatically grab station name and number
                station_name = nc.variables['metaStationName'][:]
                station_title = station_name.tobytes().decode().split('\x00',1)[0]

                print('calculating sample times')
                print('vars', starttime, len(ncTime), type(samplerate.count()))
                
                # Create specialized array using UNIX Start and End times minus Filter Delay, and Sampling Period (1/samplerate) 
                # to calculate sub-second time values that correspond to Z-Displacement sampling values
                sample_time = np.arange((starttime - filterdelay[0]),(ncTime[-1]), (1/(samplerate)))
                print(sample_time[0])
                print(unixend)
                if (sample_time[-1] < unixstart): 
                    deploy = deploy + 1
                    print('finding next deployment\n')
                    ncTime = 0
                    filtedelay = 0
                    starttime = 0
                    smaplerate = 0
                    station_name = 0
                    station_title = 0
                    continue

                print('calculating start and end indices')
                print(len(sample_time))
                print(unixstart)
                print(unixend)
                # print(sample_time.searchsorted)
                # Find corresponding start/end date index numbers in 'sample_time' array    
                startindex = sample_time.searchsorted(unixstart) 
                endindex = sample_time.searchsorted(unixend)

                print('start index', startindex)
                print('end index', endindex)

                if (startindex - endindex == 0): 
                    deploy = deploy + 1
                    print('checking next deployment:', deploy)
                    continue
                
                xdisp = nc.variables['xyzXDisplacement'] # Make a numpy array of three directional displacement variables (x, y, z)
                ydisp = nc.variables['xyzYDisplacement']
                zdisp = nc.variables['xyzZDisplacement']
                qcflag = nc.variables['xyzFlagPrimary']
                
                # if start index and end index are different we found a valid ride
                findingDeployment = False

            except Exception as e:
                print('No valid CDIP acceleration data found from this session')
                return pd.DataFrame()
                    
            # Turn off auto masking
            nc.set_auto_mask(False)
        print('filtering quality control data')

        # Limit data to date/times
        x = xdisp[startindex:endindex]
        y = ydisp[startindex:endindex]
        z = zdisp[startindex:endindex]
        qc = qcflag[startindex:endindex]

        # Filter out by quality control level
        x = np.ma.masked_where(qc>qc_level,x)
        y = np.ma.masked_where(qc>qc_level,y)
        z = np.ma.masked_where(qc>qc_level,z)

        # get the time where each sample was taken
        sample_time_cut = sample_time[startindex:endindex]
        sample_time_cut *= 1000
        sample_t_cut_ms = sample_time_cut.astype('datetime64[ms]').astype(datetime.datetime)

        df_CDIP = pd.DataFrame({ 'time': sample_t_cut_ms, 'ax': x, 'ay': y, 'az': z })
        df_CDIP = df_CDIP.set_index('time')
        return df_CDIP
                



    def get_CDIP_stations(self):
        
        # get all active buoys with archived data
        stns = self.get_active_buoys()
        buoys = []
        count = 0

         # iterate through 0-450 (station numbers are from 28-433 with gaps in between)
        for i in stns:
            
            count += 1

            # format i into a 3 digit string
            i = str(i)
            if len(i) == 1:
                i = '00' + i
            elif len(i) == 2:
                i = '0' + i

            # see if there is a station with the current iteration number
            try:
                data_url = 'http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/archive/' + i + 'p1/' + i+ 'p1_historic.nc'
                nc = netCDF4.Dataset(data_url)

                # get latitude and longitude of current station
                nc_latitude = nc.variables['metaStationLatitude'][:]
                nc_longitude = nc.variables['metaStationLongitude'][:]
                nc_latitude = float(nc_latitude.data)
                nc_longitude = float(nc_longitude.data)

                buoys.append({'buoyNum': i, 'latitude': nc_latitude, 'longitude': nc_longitude})

            except OSError as err:
                continue

        return buoys
   
    
    def get_nearest_station(self, latitude, longitude, buoys):
        # intialize the lowest distance to be some rediculously big number
        lowest_distance = 1000000000
        stn = -1
        count = 0

        for buoy in buoys:

            b_latitude = buoy['latitude']
            b_longitude = buoy['longitude']

            curr_distance = abs(b_latitude - latitude) + abs(b_longitude - longitude)
            if curr_distance < lowest_distance:
                lowest_distance = curr_distance
                stn = buoy['buoyNum']
            count += 1


        if stn == -1:
            print('no station found error')
            
        return stn
                


    def get_active_buoys(self):
        # CDIP active buoys URL
        url="http://cdip.ucsd.edu/m/deployment/station_view/?mode=active"

        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text

        # Parse the html content
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find("table")
        table_data = table.tbody.find_all("tr")  # contains 2 rows
        stns = []
        for node in table_data:
            try:
                stn = node.findAll('td', text=True)[0]
                stns.append(stn.text.strip(' '))
            except:
                continue

        return stns
        
   # Find nearest value in ncTime array to inputted UNIX Timestamp
    def find_nearest(self, array, value):
        idx = (np.abs(array-value)).argmin()
        return array[idx]
    
    
