from concurrent.futures import ThreadPoolExecutor
import util
import loading
import time
import pandas as pd

def parallelProcess(workers, function, params, input, output = pd.DataFrame, *args):
    def fetchQuery(query):
        return function(*query, *args)

    startTime = time.time()
    with ThreadPoolExecutor(max_workers = workers) as executor:
        results = list(executor.map(fetchQuery, params))
        endTime = time.time()
        print("Time taken to process (seconds): " + endTime-startTime)
        return results