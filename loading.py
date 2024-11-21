import requests
import json
from json import loads
import pandas as pd
from datetime import datetime
import time
import math
import random


def stationLoad(cities):
    url = "https://api.bart.gov/api/stn.aspx"  
    key = "Z2XJ-5YDK-9AKT-DWEI"
    response = requests.get(url, params={
    "key": key,  # outcoded personal legacy key
    "cmd": "stns",
    "json": "y"
    
    })  
    time.sleep(random.uniform(2,5)) #maybe use for loop if make mulitple requestst

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

def loadCrime(city, user, password, coordinates, radius, startYear, limit, offset):
    lat, long = coordinates
    meters = 1609.34 * radius
    if city == "SF":
        params = {
            "$select":"incident_datetime, incident_category, latitude, longitude, point",
            "$limit":limit,
            "$offset":offset,
            "$where":f"incident_datetime >= '{startYear}-01-01T00:00:00.000' and within_circle(point, {lat}, {long}, {meters})",
            "$order":"incident_datetime"
            
        }
        url = 'https://data.sfgov.org/resource/wg3w-h783.json'

    elif city == "OAK":
        params = {
            "$select":"crimetype, datetime, location",
            "$limit":limit,
            "$offset":offset,
            "$where":f"datetime >= '{startYear}-01-01T00:00:00.000' and within_circle(location, {lat}, {long}, {meters})",
            "$order":"datetime"
        }
        url = 'https://data.oaklandca.gov/resource/ppgh-7dqv.json'

    response = requests.get(url, auth = (user, password), params = params)
    time.sleep(random.uniform(2,5))
    if response.status_code == 200:
        return response.json()
    else:
        print("Authentication failed:", response.status_code)
        return None
    