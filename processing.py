from concurrent.futures import ThreadPoolExecutor
import util
import loading
import time
import pandas as pd
import functools

def subProcess(data, operations, metadata):
    for operation, args in zip(operations, metadata):
        if args is not None:
            if type(args) == list:
                data = operation(data, *args)
            else:
                data = operation(data, args)
        else:
            data = operation(data)
    return data

def validateFill(data, city):
    """
    Ensure that all required columns are present in a list of dictionaries.
    If a column is missing, add it with a default value (None).

    Args:
        data (list of dict): Input data as a list of dictionaries.
        required_columns (list): A list of required column names.

    Returns:
        list of dict: The validated data with missing columns added.
    """
    if city == "SF":
        required_columns = ['incident_datetime',
                            'incident_category', 'point']
    if city == 'OAK':
        required_columns = ['datetime', 'description', 'location']
    filtered_data = []
    for record in data:
        missing_columns = [col for col in required_columns if col not in record]
        if missing_columns:
            #print(f"Skipping record missing columns: {missing_columns}")
            continue
        else:
            filtered_data.append(record)
    return filtered_data

def Pagination(task, query, fetch_function, maxRecords = None, user = None, password = None):
    """Fetch all pages of data for a given query."""
    all_data = []
    tp = []
    if task == 'crime':
        limit = query[4]  # Assuming 'limit' is the 5th element in the query
        offset = query[5]  # Assuming 'offset' is the 6th element in the query
        while True:
            s = time.time()
            query[4] = limit
            query[5] = offset
            page_data = fetch_function(*query, user, password)
            if not page_data:  # Stop if no more data
                break
            page_data = validateFill(page_data, query[0])
            all_data.extend(page_data)
            e = time.time()
            if maxRecords is not None and len(all_data) >= maxRecords:
                tp.append((e-s, len(page_data)))
                #print("time for batch:", str(tp))
                return all_data[:maxRecords], tp
            tp.append((e-s, len(page_data)))
            offset += limit
            #print("time for batch:", str(tp))
    elif task == 'review':
        all_data = []
        tp = []
        if query[1] == True:
            s= time.time()
            visitList = fetch_function(*query)
            print("done with visit list!")
            query[1] = False
            e = time.time()
            tp.append((e-s, len(visitList)))
        while visitList: #or toVisit
            print('review page done')
            s = time.time()
            query[0] = visitList[0]
            page_data = fetch_function(*query)
            all_data.extend(page_data)
            del visitList[0]
            e = time.time()
            tp.append((e-s, len(page_data)))
    return all_data, tp


def parallelProcess(workers, function, params, task, 
                    nested = True, maxRecords = None, subprocess = None, metadata = None, *args):
    throughput = []
    def fetchQuery(query):
        if nested:
            if task == 'crime':
                data, through = Pagination(task, query, function, maxRecords, *args)
            if task == 'review':
                data, through = Pagination(task, query, function)
        else:
            s = time.time()
            data = function(query, *args)
            e = time.time()
            through = e-s
        throughput.append(through)
        return data
    
    def processAll(args):
        """Process all paginated data for a station."""
        
        query, meta = args
        data = fetchQuery(query)  # Fetch all pages or data
        if subprocess:
            return subProcess(data, subprocess, meta)
        return data
    
    startTime = time.time()
    with ThreadPoolExecutor(max_workers = workers) as executor:
        if metadata == None:
            metadata = [None] * len(params)
            pairedArgs = zip(params, metadata)
            results = list(executor.map(processAll, pairedArgs))
        else:
            pairedArgs = zip(params, metadata)
            results = list(executor.map(processAll, pairedArgs))

        # if subprocess:
        #     results = list(executor.map(
        #         lambda result_meta: subProcess(result_meta[0], subprocess, [result_meta[1]]), 
        #         zip(rawResults, metadata)))
        # else:
        #     results = rawResults
        endTime = time.time()
        final = endTime - startTime
        print("Time taken to process (seconds):", str(final))
        if task == 'crime':
            flattened = [value for sublist in results for value in sublist]
            return pd.DataFrame(flattened), throughput, final
        if task == 'review':
            return pd.DataFrame(results), throughput, final
        # if task == 'other':
        #     return results, throughput, final

def multiParallelProcess(workers, functions):
    results = []
    def internal(func, params):
        return func(*params)
    with ThreadPoolExecutor(max_workers = workers) as executor:
        futures = [
            executor.submit(internal, function[0], function[1]) for function in functions
        ]
        for future in futures:
            results.append(future.result())
    return results
        
