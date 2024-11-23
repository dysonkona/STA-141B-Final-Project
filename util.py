import requests
import json
from json import loads
import pandas as pd
from datetime import datetime
import time
import math
import nltk
import functools


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

def toDF(input, inputType = list):
    raise NotImplementedError

#DATA FRAME OPERATIONS

def Rename(df, columnNames):
    df=df.rename(columns = columnNames)
    return df

#These two are for internal use to take advantage of parallel processing, take json as input
def addColumnsJSON(data, newCols):
    #Assumes dictionary for newCols
    for record in data:
        for key, value in newCols.items():
            record[key] = value
    return data

def splitColumnsJSON(data, col, names, nestedSplit, split = False):
    '''
    Meta arguments - data, column to split, nested, nestedSplit, new names
    '''
    for record in data:
        if col in record:
            if split:
                if isinstance(record[col], dict):
                    for name, info in zip(names, record[col][nestedSplit]):
                        record[name] = info
                    del record[col]
    return data

def isViolent(data, col):
    violentStopList = ['murder', 'voluntary manslaughter', 'mayhem', 'rape', 'sodomy', 'oral',
                 'lewd', 'lascivious', 'robbery', 'arson', 'penetration', 'attempted murder',
                 'kidnapping', 'assault', 'sexual', 'abuse', 'carjacking', 'extortion', 'threats']
    try:
        nltk.data.find('corpora/wordnet.zip')
    except LookupError:
        nltk.download('wordnet')
    try:
        nltk.data.find('corpora/omw-1.4.zip')
    except LookupError:
        nltk.download('omw-1.4')
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('averaged_perceptron_tagger')

    wnl = nltk.WordNetLemmatizer()
    lemmatize = functools.lru_cache(maxsize = 300)(wnl.lemmatize)
    for record in data:
        info = record[col]
        tokens = nltk.word_tokenize(info)
        tags = nltk.pos_tag(tokens)
        noun = [word for word, tag in tags if tag in ('NN', 'NNS', 'NNP', 'NNPS')]
        if noun:
            word = noun[-1]
        else:
            word = tokens[-1]

        crime = lemmatize(word.lower())
        record["isViolent"] = (crime in violentStopList)
    return data





#Deprecated
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
    