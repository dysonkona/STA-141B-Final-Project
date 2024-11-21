from concurrent.futures import ThreadPoolExecutor
import util
import loading
import time
import pandas as pd
import functools

def subProcess(data, operations, metadata):
    for operation, args in zip(operations, metadata):
        if args is not None:
            data = operation(data, args)
        else:
            data = operation(data)
    return data

def Pagination():
    raise NotImplementedError

def parallelProcess(workers, function, params, task = 'load', 
                    nested = True, subprocess = None, metadata = None, *args):
    def fetchQuery(query):
        if nested:
            return function(*query, *args)  
        return function(query, *args)
    startTime = time.time()
    with ThreadPoolExecutor(max_workers = workers) as executor:
        rawResults = list(executor.map(fetchQuery, params))

        if subprocess:
            results = list(executor.map(
                lambda result: subProcess(result, subprocess, metadata), 
                rawResults))
        else:
            results = rawResults
        endTime = time.time()
        print("Time taken to process (seconds):", str(endTime-startTime))
        if task == 'load':
            flattened = [value for sublist in results for value in sublist]
            return pd.DataFrame(flattened)
        if task == 'other':
            return results


