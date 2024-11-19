import requests
import json
from json import loads
import pandas as pd
from datetime import datetime
import time
import math


def stationLoad(cities):
    url = "https://api.bart.gov/api/stn.aspx"  
    key = "Z2XJ-5YDK-9AKT-DWEI"
    response = requests.get(url, params={
    "key": key,  # outcoded personal legacy key
    "cmd": "stns",
    "json": "y"
    
    })  
    time.sleep(2) #maybe use for loop if make mulitple requestst

    if response.status_code == 200:
        data = response.json()  # Parse JSON response
    else:
        print("Error:", response.status_code)
    
    data = data["root"]["stations"]["station"] #long list of nested dicts, get down
    sfstations = [] #initialize empty list of sf stations
    for station in data:
    # Check if the city is "San Francisco"
        if station.get("city") in cities:
            sfstations.append(station)

    df = pd.DataFrame(sfstations)[['city', 'name', 'gtfs_latitude', 'gtfs_longitude']].sort_values("city").reset_index()
    df.drop('index', axis = 1, inplace = True)
    df['gtfs_latitude'] = df['gtfs_latitude'].astype(float)
    df['gtfs_longitude'] = df['gtfs_longitude'].astype(float)

    return df

def dfToDict(df, key, values, groupby = None):
    if groupby == None:
        Dict = {key: group[values].iloc[0].tolist()
                for key, group in df.groupby(key)}
        return Dict
    else:
        Dict = {
            group:{
                key: group[values].iloc[0].tolist()
                for key, group in colGroup.groupby(key)
                }
                for group, colGroup in df.groupby(groupby)
            }
        return Dict


def sfCrimeLoad(database):
    raise NotImplementedError

def oakCrimeLoad(database):
    raise NotImplementedError

def inStationRadius(stations, crime, radius):
    '''
    Takes dictionary for stations, Take crime (one row from database)
    Checks distance between crime and station using Haversine formula, returns
    '''
    rtrnLst = []
    def haversine(stationCoords, crimeCoords):
        # Coordinates in decimal degrees (e.g. 2.89078, 12.79797)
        lon1, lat1 = stationCoords
        lon2, lat2 = crimeCoords

        R = 3958.8  # radius of Earth in miles
        phi_1 = math.radians(lat1)
        phi_2 = math.radians(lat2)

        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        sqrtNum = 1 - math.cos(delta_phi) + math.cos(phi_1) * math.cos(phi_2) * (1 - math.cos(delta_lambda))
        distance = 2 * R * math.asin(math.sqrt(sqrtNum/2))

        return distance
    city = stations[crime['city']]
    for station in city:
        dist = haversine(city[station], crime.loc[['gtfs_latitude', 'gtfs_longitude']].tolist())
        if dist <= radius:
            rtrnLst.append((station, True, dist))
        
    return rtrnLst



def haversine(stationCoords, crimeCoords):
        # Coordinates in decimal degrees (e.g. 2.89078, 12.79797)
        lon1, lat1 = stationCoords
        lon2, lat2 = crimeCoords

        R = 3958.8  # radius of Earth in miles
        phi_1 = math.radians(lat1)
        phi_2 = math.radians(lat2)

        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        sqrtNum = 1 - math.cos(delta_phi) + math.cos(phi_1) * math.cos(phi_2) * (1 - math.cos(delta_lambda))
        distance2 = 2 * R * math.asin(math.sqrt(sqrtNum/2))

        return distance2
    

dist2 = haversine([37.803768, -122.271450], [37.808350, -122.268602])

print(dist2)
    