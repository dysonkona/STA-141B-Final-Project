import requests
import json
from json import loads
import pandas as pd
from datetime import datetime
import time
import math
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import functools
import re

#Convert data frames to dictionaries (for faster lookup)
def dfToDict(df, key, values, groupby = None):
    #When no groupby
    if groupby == None:
        Dict = {key: group[values].iloc[0].tolist()
                for key, group in df.groupby(key)}
        return Dict
    else:
        #When specific group to organize dict by
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

#Rename a dataframe
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

#Split columns based on 'col', with new 'names', also accounts for a nested structure
def splitColumnsJSON(data, col, names, nestedSplit, split = False):
    '''
    Meta arguments - data, column to split, nested, nestedSplit, new names
    '''
    #iterates through list of dictionaries
    for record in data:
        if col in record:
            if split:
                if isinstance(record[col], dict):
                    for name, info in zip(names, record[col][nestedSplit]):
                        record[name] = info
                    del record[col]
                elif isinstance(record[col], str):
                    for name, info in zip(names, record[col].split(nestedSplit)):
                        record[name] = info
                    del record[col]
    return data

#Classifies crimes as violent or nonviolent
def isViolent(data, col, city):
    #Stoplist
    violentStopList = ['murder', 'voluntary manslaughter', 'mayhem', 'rape', 'sodomy', 'oral',
                 'lewd', 'lascivious', 'robbery', 'arson', 'penetration', 'attempted murder',
                 'kidnapping', 'assault', 'sexual', 'abuse', 'carjacking', 'extortion', 'threats',
                 'violence', 'battery']
    #Ensuring correct things are downloaded
    try:
        nltk.data.find('corpora/wordnet.zip')
    except LookupError:
        nltk.download('wordnet')
    try:
        nltk.data.find('tokenizers/punkt-tab')
    except LookupError:
        nltk.download('punkt_tab')
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
    #Creates lemmatizer using functools to cache results for performance improvements
    wnl = nltk.WordNetLemmatizer()
    lemmatize = functools.lru_cache(maxsize = 300)(wnl.lemmatize)
    #Iterate through list of dictionaries
    for record in data:
        info = record[col]
        info = info.replace("-", " ")
        #Tokenize and tag data
        tokens = nltk.word_tokenize(info)
        tags = nltk.pos_tag(tokens)
        noun = [word for word, tag in tags if tag in ('NN', 'NNS', 'NNP', 'NNPS')]
        if noun:
            wordList = noun
        else:
            wordList = tokens
        #Get list of crimes
        crime = [lemmatize(word.lower()) for word in wordList]
        #Create new columns
        record["isViolent"] = ((True in [word in violentStopList for word in crime]))
        #Simplify Oakland crime description
        if city == "OAK":
            record[col] = " ".join(crime)
    return data

# Classifies crimes as drug related or non drug related
def isDrug(data, col, city):
    drugStopList = ['drug', 'narcotic', 'narcotics', 'drugs', 'intoxication']
    wnl = nltk.WordNetLemmatizer()
    lemmatize = functools.lru_cache(maxsize = 300)(wnl.lemmatize)
    for record in data:
        info = record[col]
        info = info.replace("-", " ")
        tokens = nltk.word_tokenize(info)
        tags = nltk.pos_tag(tokens)
        noun = [word for word, tag in tags if tag in ('NN', 'NNS', 'NNP', 'NNPS')]
        if noun:
            wordList = noun
        else:
            wordList = tokens

        crime = [lemmatize(word.lower()) for word in wordList]
        record["isDrug"] = ((True in [word in drugStopList for word in crime]))
    return data

# classifies crimes as occuring at day or nighttime
def dayOrNight(data, col):
    form = '%H:%M:%S.%f'
    for record in data:
        info = record[col]
        #Split datetime
        times = info.split("T")[1]
        times = datetime.strptime(times, form).time()
        #Classify
        if (times >= datetime(1, 1, 1, 21, 0).time() and times <= datetime(1, 1, 1, 0, 0).time()) or (times > datetime(1, 1, 1, 0, 0).time() and times <= datetime(1, 1, 1, 3, 0).time()):
            record["night"] = True
        else:
            record["night"] = False
    return data

#Calculate distance from crime and station
def radius(data, city, station, dict):
    #Haversine helper function to calculate distance from spherical coordinates
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
    #Calculate distances
    for record in data:
        stationC = dict[city][station]
        try:
            crimeC = [record['latitude'], record['longitude']]
        except:
            record['distance'] = None
            return data
        record['distance'] = haversine(stationC, crimeC)
    return data
    
# organize reviews
def reviewStationDict(data, cityName, stationName):
    data = {'city': cityName, 'station': stationName, 'reviews': data}
    return data

# get sentiment score for a review, helper function
def average_compound_score(reviews, sid):
    """calculates the average compound sentiment score for a list of reviews."""
    compound_scores = []
    for sentence in reviews:
        ss = sid.polarity_scores(sentence)
        compound_scores.append(ss['compound'])
    return sum(compound_scores) / len(compound_scores) if compound_scores else 0

# Calculate sentiment for every station
def getCompoundSentiment(data, col):
    sid = SentimentIntensityAnalyzer()
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon')
    data['overallSentiment'] = average_compound_score(data[col], sid)
    del data[col]
    return data