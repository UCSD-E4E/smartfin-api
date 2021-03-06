"""smartfin_ride_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views


urlpatterns = [
    # GET: api endpoints and descriptions
    path('', views.rideOverview, name='ride-overview'),
    # GET: list of fields in Ride Model
    path('fields', views.rideFields, name='ride-fields'), 
    # GET: all ride data in db
    path('rides', views.rideList, name='ride-list'), 
    # GET: all ride data in db of specified fields
    path('rides/fields=<str:fields>', views.rideFieldList, name='ride-field-list'), 
    # GET/POST/DELETE: ride specified by id
    path('rides/rideId=<str:rideId>', views.rideGet, name='ride-get-single'),  
    # GET: rides specified by location
    path('rides/location=<str:location>', views.rideGetLocation, name='ride-get-location'), 
    # GET: rides between start and end date
    path('rides/startDate=<str:startDate>,endDate=<str:endDate>', views.rideGetDate, name='ride-get-date'), 
    # GET: rides for webapp
    path('rides/maps/<str:startLat>,<str:endLat>,<str:startLon>,<str:endLon>,<str:startDate>,<str:endDate>', views.rideGetFilter, name="ride-get-filter"),

    # GET: field(s) of ride(s) specified by id
    path('rides/rideId=<str:rideId>/fields=<str:fields>', views.fieldGet, name='field-get'),
     # GET: fields(s) of ride(s) filtered by location
    path('rides/location=<str:location>/fields=<str:fields>', views.fieldGetLocation, name='field-get-location'),
    # GET: field(s) of ride(s) between start and end date
    path('rides/startDate=<str:startDate>,endDate=<str:endDate>/fields=<str:fields>', views.fieldGetDate, name='field-get-date'), 

    # PUT: update heights in db with new method
    path('update-heights', views.updateHeights, name='update-heights'), 
    # GET: dataframes of specified ride
    path('rides/rideId=<str:rideId>/dataframes/type=<str:datatype>', views.get_dataframe, name='get-dataframe'),

    # GET: list of CDIP buoys
    path('buoys', views.buoyList, name='buoy-list'), 
    path('buoys/fields', views.buoyFields, name="buoy-fields"),
    path('buoys/dataframes/station=<str:stn>,start=<str:startDate>,end=<str:endDate>', views.buoyAccs, name="buoy-accs"),
]
