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


def sfCrimeLoad(database):
    raise NotImplementedError

def oakCrimeLoad(database):
    url = 'https://data.oaklandca.gov/resource/ppgh-7dqv.json'
    secretKey = '1ef8dner8br348ez190z3z188a6pm1yluwh2wcj4xjjnlvupe'
    key = '523e7ewewudxb1frvbmdftwdt'
    raise NotImplementedError

    