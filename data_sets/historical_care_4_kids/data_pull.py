from bs4 import BeautifulSoup
import requests
import os

BASE_URL = "https://www.ctcare4kids.com/care-4-kids-program/reports/"
DATA_DIR = "enrollment_reports/"

'''
Determines whether the given url string for a resource is an excel 
file that we should download. We care about enrollment reports during
the period 2016-2020. Some notes:
- All of 2018 is completely missing; the six files listed are actually
  copies of the same-named files in 2019 (every one of them...) 
- the numbering scheme of the 2020 reports is off, and some of them
  are labeled as though they are from 2021; also, none of the month
  numbers match the actual months (i.e. January is labeled 4, as is Feb,
  March is 5, etc.).
This means we can't explicitly bound our files by 2020 because we
care about getting some of the files tagged as 2021.
'''
def is_a_report_file(href):
    # All reports contain either 'files' or 'uploads' in their url string
    if 'files' in href or 'uploads' in href:
        # Only want excel versions of files, not PDFs
        if href[-5:] == '.xlsx':
            # We care about the last 5 years of data (2016-2020), disregard
            # earlier years
            if '2015' not in href:
                # Ignore counts by town files
                if 'Counts-by-Town' not in href:
                    return True
    return False

# Get the page and soupify it for easy link finding
page = requests.get(BASE_URL)
soup = BeautifulSoup(page.text, features="lxml")

# Make a directory to put data into, if it doesn't already exist
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)
    
# If the data directory alreasy has files, nothing to do
existing_files = os.listdir(DATA_DIR)
if len(existing_files) == 48:
    print("Data already present--nothing to download")
else:
    for link in soup.find_all('a'):
        href = link.get('href')
        if is_a_report_file(href):
              
            # Use the last part of the string as the name
            filename = href.split('/')[-1].strip()
            resp = requests.get(href)
            with open(DATA_DIR + filename, 'wb') as output:
                output.write(resp.content)
            print(filename)
        
        