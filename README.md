# Smartfin Ride API

This api is built on top of the Django REST framework and can be used to fetch IMU and Ocean data captured by the Smartfin surfboard tool, analyzed and processed by UCSD's Engineers for Exploration Smartfin Research Team.


## Requirements
* python 3.8
* pythoon virtual environment (recommended) [(set up)](https://docs.python-guide.org/dev/virtualenvs/)
* Django (3.1) [(set up)](https://docs.djangoproject.com/en/3.1/intro/install/)
* Django REST Framework [(set up)](https://www.django-rest-framework.org/)


## Installation (recommended to do this in a virtual environment)
    pip install django
    pip install djangorestframework
    pip install -r requirements.txt
    
## Run
use the runserver commmand from manage.py to host the api on your local machine 
    
    python manage.py runserver


## Structure 
### API info endpoints
| Endpoint          | HTTP Method | Result                                             |
|-------------------|-------------|----------------------------------------------------|
| ride            | GET         | Get list of api endpoints and functionaltiy        |
| ride/rides   | GET         | Get list of ids of all rides currently in database |
| ride/fields | GET         | Get list of ride's fields                          |
| ride/updateDb | GET | When hit, this endpoint triggers the api to search for new sessions in the smartfin axds website, and create a new entry if new sessions exist in the axds api and not in this one |

### Get ride data 
| Endpoint                                                        | HTTP Method | Result                                                                                                                                      |
|-----------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| ride/rides/fields={str:fields} | GET | Get the specified fields of all sessions in db |
| ride/rides/rideId={str:rideId}                                     | GET/POST/DELETE    | Get, post, or delete session data by id                                                                          |
| ride/rides/rideId={str:rideId}/fields={str:fields}                       | GET         | Get specified fields of a ride data entry. Specify multiple fields by separating them with a "," i.e. "heightSmartfin,startDate"            |
| ride/rides/location={str:location}                          | GET         | Get list of ride datas filtered by location. Location can be the name of the city or county the session took place                          |
| ride/rides/location={str:location}/fields={str:fields}            | GET         | Get list of ride data fields filtered by location. Specify multiple fields with "," separation                                              |
| ride/rides/startDate={int:startDate}/endDate={int:endDate}             | GET         | Get list of ride datas that occured between the start and end date specified. Dates are formatted in unix time                              |
| ride/rides/startDate={int:startDate}/endDate={int:endDate}/fields={str:fields} | GET         | Get list of ride datas that occured between the start and end date specified. Specify multiple fields with "," separation. Unix time dates. |
| ride/rides/maps/{str:startLat},{str:endLat},{str:startLon},{str:endLon},{str:startDate},{str:endDate} | GET | Get all sessions that fall inside of a specified latitude/longitude box in between start date and end date. This endpoint is set up as the direct endpoint for the smartfin maps app, however it can still be requested like any of the other endpoints |
| ride/rides/rideId={str:rideId}/dataframes/type={str:datatype} | GET         | get a CSV file of a smartfin session's data. Datatype can be either 'motion' (IMU sensor data) or 'ocean' (ocean sensor data) |
| ride/rides/rideId={str:rideId}/datalist/type={str:dtype} | GET | gets acceleration or temperature readings from db based on whether dtype="accs" or dtype="temp". Acceleration readings are m/s^2 and temp readings are in degrees C. Readings are all 1 sample per second. |



### other functionality
| Endpoint                                   | HTTP Method | Result                                                                                                                        |
|--------------------------------------------|-------------|-------------------------------------------------------------------------------------------------------------------------------|
| ride/buoys                                 | GET         | get list of all currently deployed CDIP buoys                                                                                 |
| ride/bouys/fields | GET | get a list of the specified fields from all bouys in db |


# Usage Examples
### get info about api endpoints:

```python
import requests
response = requests.get('https://lit-sands-95859.herokuapp.com/ride')
data = response.json()
```

#### data: 
    {
     'List api endpoints': '/',
     'List ride fields': '/fields',
     'Get all rides in db': '/rides',
     'Get field of all rides in db': '/rides/fields=<str:fields>',
     'Get single ride': '/rides/rideId=<str:rideId>',
     'Filter rides by location': '/rides/location=<str:location>',
     'Filter rides by date': '/rides/startDate=<str:startDate>,endDate=<str:endDate>',
     'Get single ride attribute': 'rides/rideId=<str:rideId>/fields=<str:fields>',
     'Get attributes of rides filtered by location': 'rides/location=<str:location>/fields=<str:fields>',
     'Get attributes of rides filtered by date': 'rides/startDate=<str:startDate>,endDate=<str:endDate>/fields=<str:fields>',
     'Update heights of all rides in database': 'update-heights',
     'Get list of active CDIP buoys': 'buoys'
     }

### fetching all rides in san diego
```python
import requests
response = requests.get('https://lit-sands-95859.herokuapp.com/ride/rides/location={location}')
data = response.json()
```


### parsing motion and ocean CSV string into a pandas dataframe through BytesIO:
```python
from io import BytesIO
import pandas as pd

csv_str = BytesIO(data['motionData'])
dataframe = pd.read_csv(csv_str)
```
