from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from django.db.models import Q
from rest_framework import serializers

from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import RideSerializer, HeightSerializer, TempSerializer, BuoySerializer

from .modules.smartfin_ride_module import RideModule
from .modules.cdip_web_scrape import CDIPScraper
from .modules.formatter import DataFormatter
from .models import RideData, Buoy, DataframeCSV
import json
import random
import sys
from zipfile import ZipFile
from wsgiref.util import FileWrapper
from io import BytesIO
import pandas as pd
import os




# TODO: combine get many with the location and date views


# Create your views here.
@api_view(['GET'])
def rideOverview(request):
    # list of url patterns in this api
    api_urls = {
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
        'Get list of active CDIP buoys': 'buoys',
    }

    return Response(api_urls)



# get list of all rideIds
@api_view(['GET'])
def rideList(request):
    rideModule = RideModule()
    axds_ride_list = rideModule.fetch_session_ids()
    axds_ride_list = list(axds_ride_list.keys())
    axds_ride_list = [id.split(':', 1)[1] for id in axds_ride_list]
    print(len(axds_ride_list))
    print(type(axds_ride_list))
    ride_list = list(RideData.objects.all().values_list('rideId', flat=True))
    print(type(ride_list))
    print(len(ride_list))
    id_list = ride_list + axds_ride_list
    print(len(id_list))
    return JsonResponse({'ids': id_list})


# get list of a field of all rides
@api_view(['GET'])
def rideFieldList(request, fields):

    formatter = DataFormatter()
    attributes = formatter.parseAttributes(fields)
    rd = RideData.objects.all().values_list(*attributes)

    # format data to send back
    data = {'data': [dict(zip(attributes, values)) for values in rd]}
    return JsonResponse(data)



@api_view(['GET'])
def rideFields(request):
    data = {
        'id of smartfin session': 'rideId',
        'location (city, county, state) of session': 'loc1, loc2, loc3',
        'start time of session': 'startTime',
        'end time of session': 'endTime',
        'significant wave height calculated by smartfin': 'heightSmartfin',
        'significant wave height reported by nearest CDIP buoy': 'heightCDIP',
        'calibrated ocean temperature read by smartfin': 'tempSmartfin',
        'ocean temperature reported by nearest CDIP buoy': 'tempCDIP',
        'nearest CDIP buoy to smartfin session': 'buoyCDIP',
        'latitude of smartfin session': 'latitude',
        'longitude of smartfin session': 'longitude',
    }
    return JsonResponse(data)




@api_view(['GET', 'DELETE', 'POST'])
# create new ride or return it if it is already in the database 
def rideGet(request, rideId):

    print(request.method)

    if request.method == 'GET':
        return getRide(rideId)
    elif request.method == 'DELETE':
        return deleteRide(rideId)
    elif request.method == 'POST':
        return getRide(rideId)
    else:
        return JsonResponse({'Error': 'url not found'})



def getRide(rideId):

    # if ride already exists in the database, return it
    try: 
        data = RideData.objects.get(rideId=rideId)
        print('found ride in database, returning data...')

    # if ride doesn't exist, then create a new model and fill its data
    except:
        rideModule = RideModule()

        # get all CDIP buoys from db
        buoys = Buoy.objects.values()
        if len(buoys) == 0:
            buoys = rideModule.get_CDIP_stations()
            for buoy in buoys:
                buoyModel = Buoy(**buoy)
                buoyModel.save()
    
        # fetch data from the ride_module
        data, df_path = rideModule.get_ride_data(rideId, buoys)
        print(data)

        if data == {}:
            return JsonResponse({"Error": f"no such ride '{rideId}' exists"})

        # save ride data into RideData model
        rideModel = RideData(**data)
        rideModel.save()

        dfModel = DataframeCSV(ride=rideModel, filePath=df_path, datatype='motion')
        dfModel.save()

        print(f'uploaded {sys.getsizeof(data)} bytes of ride data to database...')

    # return ride data that was sent to model
    serializer = RideSerializer(data, many=False)
    return Response(serializer.data)



def deleteRide(rideId):
    try:
        rideToDelete = RideData.objects.get(rideId=rideId)

        # delete motion dataframe
        if os.path.exists(f'ride/motion_dfs/{rideId}_mdf.csv'):
            os.remove(f'ride/motion_dfs/{rideId}_mdf.csv')
        else:
            print("The file does not exist")

        # delete ocean dataframe
        if os.path.exists(f'ride/ocean_dfs/{rideId}_odf.csv'):
            os.remove(f'ride/ocean_dfs/{rideId}_odf.csv')
        else:
            print("The file does not exist")
        rideToDelete.delete()

    except:
        return JsonResponse({"Error": "ride not found"})
    
    return JsonResponse({"success": f"ride '{rideId}' successfully deleted"})



@api_view(['GET'])
def rideGetLocation(request, location):
    # return all ride ids if all locations are specified
    if (location == 'all'):
        rideSet = RideData.objects.all()
    # only return ids in the specified location
    else:
        if ':' in location:
            loc1, loc3 = location.split(':')
        else:
            loc1 = location
            loc3 = location
        # here | is being used as set union not bitwise OR
        rideSet = RideData.objects.filter(Q(loc1=loc1) | Q(loc2=loc1) | Q(loc3=loc1) | Q(loc1=loc3) | Q(loc2=loc3) | Q(loc3=loc3))

    print(rideSet)

    if len(rideSet) <= 0:
        return JsonResponse({ "Error": "no rides found in this location" })

    serializer = RideSerializer(rideSet, many=True)
    return Response(serializer.data)



@api_view(['GET'])
def rideGetDate(request, startDate, endDate):
    
    if startDate == 'all':
        rideSet = RideData.objects.all()
    try:     
        startDate = int(startDate)
        endDate = int(endDate)
        if startDate > endDate:
            return JsonResponse({"Error": "end date must be greater than start date"})
    except:
        return JsonResponse({'Error': 'dates must be formatted in unix time'})

    # get all rides that occur after the startDate
    rideSet = RideData.objects.filter(Q(startTime__gte=startDate) & Q(endTime__lte=endDate))
    if len(rideSet) <= 0:
        return JsonResponse({ "Error": f"No rides found between {startDate} and {endDate}" })

    serializer = RideSerializer(rideSet, many=True)
    return Response(serializer.data)





@api_view(['GET'])
def rideGetFilter(request, stratLat, endLat, startLon, endLon, startDate='all', endDate='all'):

    rideSetLocation = RideData.objects.filter(Q(latitude__gte=startLat) & Q(latitude__lte=endLat) & Q(longitude__gte=startLon) & Q(longitude__lte=endLon))

    rideSetDate = rideGetDate(request, startDate, endDate)
    rideSet = rideSetLocation & rideSetDate
    
    if len(rideSet) <= 0:
        return JsonResponse({ 'Error': f'No rides found within these parameters' })

    serializer = RideSerializer(rideSet, many=True)
    return Response(serializer.data)






# get single field from ride
@api_view(['GET']) 
def fieldGet(request, rideId, fields):

    formatter = DataFormatter()
    attributes = formatter.parseAttributes(fields)
 
    data = {}
    try:
        field = RideData.objects.get(rideId=rideId)
    except:
        return JsonResponse({"Error": f"No such ride {rideId} found in database, create a new ride if the ride should exist with the ride-get query"})

    for attribute in attributes:
        data[attribute] = getattr(field, attribute)


    return JsonResponse(data)




@api_view(['GET'])
def fieldGetLocation(request, fields, location):

    formatter = DataFormatter()
    attributes = formatter.parseAttributes(fields)

    # return all ride ids if all locations are specified
    if (location == 'all'):
        fieldSet = RideData.objects.all()
        fieldSet = fieldSet.values_list(*attributes)
    # only return ids in the specified location
    else:
        if ':' in location:
            loc1, loc3 = location.split(':')
        else:
            loc1 = location
            loc3 = location
        # here | is being used as set union not bitwise OR
        fieldSet = RideData.objects.filter(Q(loc1=loc1) | Q(loc2=loc1) | Q(loc3=loc1) | Q(loc1=loc3) | Q(loc2=loc3) | Q(loc3=loc3))
        fieldSet = fieldSet.values_list(*attributes)

    if len(fieldSet) <= 0:
        return JsonResponse({ "Error": "no rides found in this location" })
    
    data = {'data': [dict(zip(attributes, values)) for values in fieldSet]}
    return JsonResponse(data)


@api_view(['GET'])
def fieldGetDate(request, startDate, endDate, fields):

    formatter = DataFormatter()
    attributes = formatter.parseAttributes(fields)

    # parse dates
    try:     
        startDate = int(startDate)
        endDate = int(endDate)
       
        if startDate > endDate:
            return JsonResponse({"Error": "end date must be greater than start date"})
  
    except:
        return JsonResponse({'error': 'dates must be formatted in unix time'})

    # get all rides that occur after the startDate and before end date
    fieldSet = RideData.objects.filter(Q(startTime__gte=startDate) & Q(endTime__lte=endDate))
    fieldSet = fieldSet.values_list(*attributes)

    if len(fieldSet) <= 0:
        return JsonResponse({ "Error": f"No rides found between {startDate} and {endDate}" })

    data = {'data': [dict(zip(attributes, values)) for values in fieldSet]}
    return JsonResponse(data)



@api_view(['PUT'])
# used to update smartfin calculated heights when new analysis method is used
def updateHeights(request):

    # get all ids currently in database
    ids = RideData.objects.values_list('rideId', flat=True)
    rm = RideModule()

    # for each ride currently in database...
    for id in ids:
        dfPath = DataframeCSV.objects.get(ride__rideId=id, datatype='motion')
        fi = open(dfPath, 'rb')
        mdf = pd.read_csv(BytesIO(fi))
        # calculate the new ride height from updated height analysis algorithm
        heightUpdated, heightList, heightSampleRate = rm.get_ride_height(mdf)

        # update the old height in the database
        ride = RideData.objects.get(rideId=id)
        ride.heightSmartfin = heightUpdated  # change field
        ride.save() # this will update only

    return JsonResponse({'success': 'rides updated '})



@api_view(['GET'])
def get_dataframe(request, rideId, datatype):

    try:
        dfPath = DataframeCSV.objects.get(ride__rideId=rideId, datatype=datatype)
    except:
        return JsonResponse({"Error": f"No such ride {rideId} found in database, create a new ride if the ride should exist with the ride-get query"})
    dfPath = getattr(dfPath, 'filePath')
    print(dfPath)
    fi = open(dfPath, 'rb')
    return FileResponse(fi)


@api_view(['GET'])
def get_data_list(request, rideId, dtype):
    print(rideId)
    try:
        dfPath = DataframeCSV.objects.get(ride__rideId=rideId, datatype='motion')
    except:
        return JsonResponse({"Error": f"No such ride {rideId} found in database, create a new ride if the ride should exist with the ride-get query"})
    dfPath = getattr(dfPath, 'filePath')
    print(dfPath)
    fi = open(dfPath, 'rb')
    df = pd.read_csv(fi)

    rm = RideModule()
    data_list = []
    if (dtype == 'temp' or dtype == 'temperature'):
        data_list = rm.get_temp_list(df)
    elif (dtype == 'acc' or dtype == 'acceleration'):
        data_list = rm.get_acc_list(df)

    print('returning datalist')
    print(data_list)
    data = { dtype: list(data_list) }
    return JsonResponse(data)
        



@api_view(['GET'])
def buoyList(request):
    
    # return list of buoys
    data = Buoy.objects.all().values_list('buoyNum', flat=True)
    print(data)
    return Response(data)



@api_view(['GET'])
def buoyFields(request):

    data = list(Buoy.objects.all())
    print(data)
    bs = BuoySerializer(data, many=True)
    print('returning buoy data')
    return Response(bs.data)




# @api_view(['GET'])
# def buoyAccs(request, stn, startDate, endDate):
#     cws = CDIPScraper()
#     print(stn)
#     print(startDate)
#     print(endDate)
#     df = cws.get_acc_df(stn, startDate, endDate)

#     df = pd.to_csv(df)
#     return FileResponse(df)
