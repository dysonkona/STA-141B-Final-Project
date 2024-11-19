import requests
import json
from json import loads
import pandas as pd
from datetime import datetime
import time
import math


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


def inStationRadius(stations, crime, radius):
    '''
    Takes dictionary for stations, Take crime (one row from database)
    Checks distance between crime and station using Haversine formula, returns
    '''
    rtrnDct = {}
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
            rtrnDct[station] = dist
        
    return rtrnDct
    