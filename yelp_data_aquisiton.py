import requests
import requests_cache
import lxml.html as lx
import re
from selenium import webdriver
import time
import random
import nltk

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

def GetReviews(url):
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