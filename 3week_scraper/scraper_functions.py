#### Web Scraper Algorithm ####
'''
The client essentially wants a web-scraper that will gather relevant information from this site.
https://hillsborough.realforeclose.com/

The scraper should be able to go through EACH county within Florida. Next the program should sort through
auctions every single day, the site allows a convenient look into auctions sorted by date.
Go To:
'Auction Calendar' -> Select The Appropriate Calendar Date (Most Recent/Daily) ->  View All Auctions
There are Auction Categories: 1. Running Auctions 2. Auctions Waiting 3. Auctions Closed or Canceled
'''
# import modules
#import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time
from time import sleep 
import pandas as pd
from urllib.parse import urlparse
from emailer import send_email

# Function to construct the calendar url based on the start/target date
def construct_calendar_url(base_url, target_date):
    # Format the date in 'YYYY-MM-DD' format
    formatted_date = target_date.strftime('%Y-%m-%d')
    # Construct the URL
    constructed_url = f"{base_url}?zaction=user&zmethod=calendar&selCalDate=%7Bts%20%27{formatted_date}%2000%3A00%3A00%27%7D"
    return constructed_url

def navigate_to_target_month(driver, target_date):
    # Extract the base URL from the current URL
    current_url = driver.current_url
    parsed_url = urlparse(current_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    print(f"Found and Created BaseURL: {base_url}")
    
    # Find the target date
    target_day = target_date.day
    target_month = target_date.strftime("%B")
    target_year = target_date.year
    
    try:
        # Get the current month and year displayed on the calendar
        current_month_year_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CALDATE"))
        )
        current_month_year = current_month_year_element.text
        current_month, current_year = current_month_year.split(" ")
    
        if f"{target_month} {target_year}" != f"{current_month} {current_year}":
            # Navigate to the target month using constructed URL
            constructed_url = construct_calendar_url(base_url, target_date)
            driver.get(constructed_url)
        
        # Check if the target day is greater than the last day of the current month
        all_day_elements =  WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "CALNUM"))
        )
        last_day_in_current_month = int(all_day_elements[-1].text)
            
        if last_day_in_current_month is not None and target_day >= last_day_in_current_month:
            # If the target day is the last day in the current month, click "Next Month"
            next_month_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='CALNAV'][@tabindex='0']/a[contains(@aria-label, 'Next Month')]"))
            )
            next_month_button.click()
    except Exception as e:
        print("Failed Navigating to the target month: {e}")
    
def navigate_to_auction_calendar(driver, url, target_date):
    # Wait for the auction calendar to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'calendar'))
    )
    
    # Find all date buttons in the calendar
    date_buttons = driver.find_elements_by_class_name('day')


# Function to grab the date and click on correct auction_date tab
def auction_date(driver, target_date):
    wait = WebDriverWait(driver, 10)
    # format the target date to match the format in the aria-label attribute
    formatted_target_date = target_date.strftime("%B-%d-%Y")
    # Construct the XPath to find the date element by its aria-label attribute
    date_element_xpath = f'//div[@aria-label="{formatted_target_date}"]'
    try:
        # Find the date element
        date_element = wait.until(EC.element_to_be_clickable((By.XPATH, date_element_xpath)))

        # Click on the date element
        date_element.click()
    except:
        print(f"Date element for {formatted_target_date} not found.")

# Function to extract auction info from each auction
def extract_auction_data(html_content):
    auction_data_list = []

    soup = BeautifulSoup(html_content, "html.parser")
    auction_stats_divs = soup.find_all('div', class_='AUCTION_STATS')

    for auction_stats_div in auction_stats_divs:
        auction_data = {}

        auction_type_div = auction_stats_div.find('div', class_='ASTAT_MSGA ASTAT_LBL')
        if auction_type_div:
            key = auction_type_div.get_text(strip=True)
            value_div = auction_type_div.find_next('div', class_='ASTAT_MSGB Astat_DATA')
            if value_div:
                auction_data[key] = value_div.get_text(strip=True)

        amount_div = auction_stats_div.find('div', class_='ASTAT_MSGC ASTAT_LBL')
        if amount_div:
            key = amount_div.get_text(strip=True)
            value_div = amount_div.find_next('div', class_='ASTAT_MSGD Astat_DATA')
            if value_div:
                auction_data[key] = value_div.get_text(strip=True)

        sold_to_label_div = auction_stats_div.find('div', class_='ASTAT_MSG_SOLDTO_Label ASTAT_LBL')
        if sold_to_label_div:
            key = sold_to_label_div.get_text(strip=True)
            sold_to_value_div = sold_to_label_div.find_next('div', class_='ASTAT_MSG_SOLDTO_MSG Astat_DATA')
            if sold_to_value_div:
                auction_data[key] = sold_to_value_div.get_text(strip=True)

        auction_data_list.append(auction_data)

    return auction_data_list

def extract_auction_details(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    card_tiles = soup.find_all('div', class_='AUCTION_DETAILS')
    if not card_tiles:
        print("No elements with class 'AUCTION_DETAILS' found.")
        return []
    
    auction_data = []

    for card_tile in card_tiles:
        auction_info = {}

        # Extract auction details
        ad_details = card_tile.find_all('div', {'class':"AD_LBL"})
        ad_values = card_tile.find_all('div', {'class':"AD_DTA"})


        if len(ad_details) != len(ad_values):
            print("Mismatch between the number of details and values.")
            continue

        for label, value in zip(ad_details, ad_values):
            label_text = label.get_text(strip=True)
            value_text = value.get_text(strip=True)
            
            auction_info[label_text] = value_text

        auction_data.append(auction_info)

    return auction_data 
    
def extract_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    card_tiles = soup.find_all('div', class_='AUCTION_DETAILS')

    auction_data = []

    for card_tile in card_tiles:
        auction_info = {}

        # Extract auction details
        table = card_tile.find('table', class_='ad_tab')
        rows = table.find_all('tr')

        for row in rows:
            th = row.find('th', class_='AD_LBL')
            td = row.find('td', class_='AD_DTA')
            
            # Even if th or td is None, we put an empty string
            label = th.get_text(strip=True) if th else ""
            value = td.get_text(strip=True) if td else ""
            
            # If we have a label but no value, the value will be an empty string
            if label:
                auction_info[label] = value
                

        auction_data.append(auction_info)

    return auction_data

### Generate unique excel filenames ###
def generate_unique_filename(base_path, extension):
    timestamp = int(time.time())
    counter = 1
    while True:
        # Construct the filename with a timestamp and counter
        filename = f"{base_path}_{timestamp}_{counter}.{extension}"
        # Check if the file with the generated name already exists
        if not os.path.isfile(filename):
            return filename
        counter += 1

### Get rid of unnecessary excel rows ###
# Helper function to convert currency string to float
def currency_to_float(currency_str):
    if pd.isna(currency_str):
        return None
    return float(currency_str.replace("$", "").replace(",", "").strip())

def clean_excel_file(input_path, output_path):
    # Load the Excel file into a DataFrame
    input_df = pd.read_excel(input_path)
    
    # Step 1: Filter rows
    # Remove rows where 'Sold To' is not "3rd Party Bidder" or is blank/empty
    filtered_df = input_df[input_df['Sold To'] == '3rd Party Bidder'].copy()

    # Step 2: Calculate 'Surplus' column
    # Convert currency columns to float for calculations
    filtered_df['Amount'] = filtered_df['Amount'].apply(currency_to_float)
    filtered_df['Final Judgment Amount:'] = filtered_df['Final Judgment Amount:'].apply(currency_to_float)
    
    # Calculate Surplus as Amount - Final Judgment Amount
    filtered_df['Surplus'] = filtered_df['Amount'] - filtered_df['Final Judgment Amount:']

    # Step 3: Sort the DataFrame by 'Surplus' in descending order
    sorted_df = filtered_df.sort_values(by='Surplus', ascending=False)
    
    # Step 4: Save the cleaned DataFrame to a new Excel file
    sorted_df.to_excel(output_path, index=False)

    return output_path

# function to get county names from a dictionary of urls
def get_county_name(url, url_to_county):
    for county, url_list in url_to_county.items():
        if url in url_list:
            return county
    return "Unknown County"

def visit_auction_pages(driver, url, target_date, url_to_county):

    # Use driver to navigate to the website
    driver.get(url)
    print(driver.title)

    # Click on Auction Calander
    wait = WebDriverWait(driver, 10)
    auction_calander_element = driver.find_element(By.ID, "splashMenuBottom")   
    auction_calander_element.click()
    sleep(5)

    # Use the current date as the target date for the auction
    #navigate_to_auction_calendar(driver,url,target_date)
    navigate_to_target_month(driver, target_date)
    sleep(10)

    # Use the current date as the target date for the auction
    auction_date(driver, target_date)
    sleep(10)

    # Wait for content to load 
    driver.implicitly_wait(5)
    sleep(20)
    page_source = driver.page_source

    # extract auction data for the day
    stats = extract_auction_data(page_source)

    details = extract_auction_details(page_source)
    # check the 'details' to decide whether to call the other method
    if all(not bool(d) for d in details):
        details = extract_data(page_source) 

    data = []
    for i in range(len(stats)):
        merged_dict = {**stats[i], **details[i]}  # Merge dictionaries at index i
        data.append(merged_dict)

    # Create a dataframe from the auction data 
    df = pd.DataFrame(data)

    # Add the 'Counties' column
    county_name = "Unknown"
    for county_url in url_to_county:
        if url in county_url.values():
            county_name = list(county_url.keys())[0]
            break
    
    df["Counties"] = county_name

    # Check if the DataFrame is empty
    if df.empty:
        print("Empty DataFrame, no content found")
    else:
        print("Raw Data:")
        print(df.head())

    return df
