import requests
import json
from json import loads
import pandas as pd
from datetime import datetime
import time
import math
import random
import requests_cache
import lxml.html as lx
import re
from selenium import webdriver

#Load station data through legacy BART API
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

#Load crime data through SF and OAK openData portal
def loadCrime(city, coordinates, radius, startYear, limit, offset, user, password):
    lat, long = coordinates
    #Convert radius to meters
    meters = 1609.34 * radius
    #SF parameters
    if city == "SF":
        params = {
            "$select":"incident_datetime, incident_category, point",
            "$limit":limit,
            "$offset":offset,
            "$where":f"incident_datetime >= '{startYear}-01-01T00:00:00.000' and within_circle(point, {lat}, {long}, {meters})",
            "$order":"incident_datetime"
            
        }
        url = 'https://data.sfgov.org/resource/wg3w-h783.json'
    #Oak parameters
    elif city == "OAK":
        params = {
            "$select":"datetime, description, location",
            "$limit":limit,
            "$offset":offset,
            "$where":f"datetime >= '{startYear}-01-01T00:00:00.000' and within_circle(location, {lat}, {long}, {meters})",
            "$order":"datetime"
        }
        url = 'https://data.oaklandca.gov/resource/ppgh-7dqv.json'

    #Request
    response = requests.get(url, auth = (user, password), params = params)
    time.sleep(random.uniform(2,5))
    if response.status_code == 200:
        return response.json()
    else:
        print("Authentication failed:", response.status_code)
        return None

#Helper function to get all subpages for a BART yelp page
def GetPages(url):
    links_to_visit = [url]  # Initialize with the parent URL
    processed_links = set()  # Track links that have already been processed
    unique_start_urls = {}  # Track URLs with unique `start` values

    while links_to_visit:
        link = links_to_visit.pop()  # Lifo

        if link in processed_links:  # Skip if already processed
            continue
        processed_links.add(link)  # Mark as processed

        try:
            response = requests.get(link, timeout=10)
            if response.status_code != 200:
                time.sleep(random.uniform(2, 10))
                response = requests.get(link)
                if response.status_code != 200:
                    time.sleep(random.uniform(10, 20))
                    response = requests.get(link)
            
            html_tree = lx.fromstring(response.text)
            
            # Extract pagination links
            new_links = html_tree.xpath("//a[contains(@class, 'pagination-link-component')]/@href")

            # Deduplicate links based on `start` parameter
            for new_link in new_links:
                start_value = new_link.split("start=")[1].split("&")[0] if "start=" in new_link else "0"
                if start_value not in unique_start_urls:  # Check if `start` value is unique
                    unique_start_urls[start_value] = new_link
                    links_to_visit.append(new_link)  # Add unique link to visit next
        except Exception as e:
            continue

        time.sleep(random.uniform(1, 3))  # Pause between requests
    return list(unique_start_urls.values())  # Return all unique URLs based on `start` values

def GetReviews(url, initialize = True):
    if initialize:
        toVisit = GetPages(url)
        return toVisit
    reviewlist = []  # List to store reviews

    # Request the page
    response = requests.get(url)
    if response.status_code != 200:
        time.sleep(random.uniform(2, 10))
        response = requests.get(url)
        if response.status_code != 200:
            time.sleep(random.uniform(10, 20))
            response = requests.get(url)
            if response.status_code != 200:
                return reviewlist  # Return an empty list if the request fails

    # Parse the page content
    html_tree = lx.fromstring(response.text)
    
    # Extract reviews using XPath
    reviews = html_tree.xpath("//div[@id='reviews']//ul/li//p/span/text()")
    reviewlist.extend(reviews)
    
    # Random delay to avoid detection
    time.sleep(random.uniform(2, 5))

    return reviewlist


    