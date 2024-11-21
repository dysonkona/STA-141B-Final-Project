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

def Pagination(query, fetch_function, maxRecords, user, password):
    """Fetch all pages of data for a given query."""
    limit = query[4]  # Assuming 'limit' is the 5th element in the query
    offset = query[5]  # Assuming 'offset' is the 6th element in the query
    all_data = []
    while True:
        query[4] = limit
        query[5] = offset
        page_data = fetch_function(*query, user, password)
        if not page_data:  # Stop if no more data
            break
        all_data.extend(page_data)

        if maxRecords is not None and len(all_data) >= maxRecords:
            return all_data[:maxRecords]

        offset += limit
    return all_data

def parallelProcess(workers, function, params, task = 'load', 
                    nested = True, maxRecords = None, subprocess = None, metadata = None, *args):
    def fetchQuery(query):
        if nested:
            return Pagination(query, function, maxRecords, *args)  
        return function(query, *args)
    
    def processAll(args):
        """Process all paginated data for a station."""
        query, meta = args
        data = fetchQuery(query)  # Fetch all pages or data
        if subprocess:
            return subProcess(data, subprocess, [meta])
        return data
    
    startTime = time.time()
    with ThreadPoolExecutor(max_workers = workers) as executor:
        pairedArgs = zip(params, metadata)
        
        results = list(executor.map(processAll, pairedArgs))

        # if subprocess:
        #     results = list(executor.map(
        #         lambda result_meta: subProcess(result_meta[0], subprocess, [result_meta[1]]), 
        #         zip(rawResults, metadata)))
        # else:
        #     results = rawResults
        endTime = time.time()
        print("Time taken to process (seconds):", str(endTime-startTime))
        if task == 'load':
            flattened = [value for sublist in results for value in sublist]
            return pd.DataFrame(flattened)
        if task == 'other':
            return results


