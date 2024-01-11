# import modules
#import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time
from time import sleep 
import pandas as pd
import requests
from datetime import datetime, timedelta


def calculate_custom_dates():
    # Get the current date
    today = datetime.now()

    # Calculate the number of days until the upcoming Sunday
    days_since_sunday = today.weekday() + 1

    # Calculate the start date
    start_date = today - timedelta(days=days_since_sunday)
    print(f"Start Date: {start_date}")
    # Calculate the end date (following Saturday, which is 6 days after the start date)
    end_date = start_date + timedelta(days=6)
    print(f"End Date: {end_date}")

    return start_date, end_date
    
"""
# Function to calculate the dates of start and end date
def calculate_custom_dates(target_date):
    # Convert the target date to a datetime object
    target_date =datetime.strptime(target_date, "%Y-%m-%d")

    # Calculate the number of days until next Sunday (0 for Sunday, 1 for Monday, etc.)
    days_until_sunday = (5 - target_date.weekday()) % 7

    # Calculate the "On or After" date (next Sunday)
    on_or_after_date = target_date - timedelta(days=days_until_sunday)

    # Calculate the "On or Before" date (following Saturday)
    on_or_before_date = target_date

    print("On or After Date:", on_or_after_date.strftime("%Y-%m-%d"))  # Format as desired
    print("On or Before Date:", on_or_before_date.strftime("%Y-%m-%d")) 
    return on_or_after_date, on_or_before_date
"""
def party_information_test(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="ssCaseDetailSectionTitle" and contains(text(), "Party Information")]')))
    
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    party_info_table = soup.find('table', {'style': 'table-layout: fixed'})
    all_data = []

    for row in party_info_table.find_all('tr'):
        for cell in row.find_all(['th', 'td']):
            cell_text = cell.get_text(separator=" ", strip=True).replace('\n', ' ')
            all_data.append(cell_text)
    
    print(all_data)
    return all_data

# Function to extract party information
def extract_party_information(driver):
    # Wait for the Party Information table to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="ssCaseDetailSectionTitle" and contains(text(), "Party Information")]')))
    # Extract HTML content
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    defendants = []
    plaintiffs = []

    # Initialize a list to store extracted data
    party_info_table = soup.find('table', {'style': 'table-layout: fixed'})
    # Find all rows in the Party Information table
    for row in party_info_table.find_all('tr'):
        #print(party_info_table.find_all('tr'))
        cells = row.find_all('th')
        if len(cells) >= 2:
            party_type = cells[0].text.strip().upper()
            print(f"Party Type: {party_type}")

            if party_type == "ATTORNEYS":
                continue

            party_name = cells[1].text.strip()
            print(f"Party Name: {party_name}")

            next_row = row.find_next_sibling('tr')
            if next_row:
                address_cell = next_row.find('td', valign='top')
                if address_cell:
                    # If found, get the address text
                    temp_address = " ".join(address_cell.stripped_strings)
                    print(f"Party Address: {temp_address}")
                else:
                    # Otherwise, set it to an empty string or None
                    temp_address = ""
            if party_type == "DEFENDANT":
                defendants.append({'Name': party_name, 'Address':temp_address})
            elif party_type == "PLAINTIFF":
                plaintiffs.append({'Name': party_name})
            
    return defendants, plaintiffs

def get_all_case_search(driver, url):
    # open the url
    driver.get(url)

    # Wait for the All Case Records Search element to be lcoated
    wait = WebDriverWait(driver, 10)
    all_cases_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "ssSearchHyperlink")))
    # Click on the element 
    all_cases_button.click()

    time.sleep(5)
    
    # Find the 'Date Filed' input and click on the input
    date_filed = wait.until(EC.element_to_be_clickable((By.ID, 'DateFiled')))
    date_filed.click()

    # Calculate the custom dates
    #target_date = "2023-11-05"
    #target_date = datetime.now() #change to pull the current day (will only run on Saturdays)
    #on_or_after, on_or_before = calculate_custom_dates(target_date)
    on_or_after, on_or_before = calculate_custom_dates()


    # Find the 'Date Filed On or After' input and input the date
    date_filed_on_after = wait.until(EC.element_to_be_clickable((By.ID, 'DateFiledOnAfter')))
    date_filed_on_after.send_keys(on_or_after.strftime("%m/%d/%Y"))
    time.sleep(5)
    # Find the 'Date Filed On or Before' input and input the date
    date_filed_on_before = wait.until(EC.element_to_be_clickable((By.ID, 'DateFiledOnBefore')))
    date_filed_on_before.send_keys(on_or_before.strftime("%m/%d/%Y"))
    time.sleep(5)
    # Select the element to be located
    wait = WebDriverWait(driver, 10)
    select_element = wait.until(EC.presence_of_element_located((By.ID, 'selCaseTypeGroups')))

    # Create a Select object
    select = Select(select_element)

    # Select the option by its value
    option_value = "1624,1393,1385,1380,1352,1361,1375,1335,1339,1342,1362,1563,1449,2597,3824,23119,23120,23925,23926,23927,23928,23929,23930,23931,23932,23933,23934,23935,23936,24789"
    select.select_by_value(option_value)    
    time.sleep(5)

    # Find the submit button
    sumbit_button = wait.until(EC.element_to_be_clickable((By.ID, 'SearchSubmit')))
    sumbit_button.click()
    time.sleep(5)

    response = requests.get(url)
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table element
    table = soup.find("table")
    # Find all the case number links by locating 'a' elements with a 'href' attribute
    case_number_links = driver.find_elements(By.XPATH, '//a[contains(@href, "CaseID=")]')
    """
    # Create an empty list to store part information DataFrames
    all_party_info_dfs = []
    """
    # Create empty lists to store party information
    all_defendants_info = []
    all_plaintiffs_info = []

    # Generate a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file_name = f"party_info_{timestamp}.xlsx"
    excel_file_path = os.path.join(os.getcwd(), excel_file_name)

    writer = pd.ExcelWriter(excel_file_path, engine='xlsxwriter')

    # Iterate through each case number link and perform tasks
    for i in range(len(case_number_links)):
        # Re-locate the case number links on each iteration to avoid staleness
        case_number_links = driver.find_elements(By.XPATH, '//a[contains(@href, "CaseID=")]')
        
        # Click on the case number link
        case_number_links[i].click()
        time.sleep(5)
        """
        # Call the function to scrape party information on the current page
        raw_table_data = party_information_test(driver)
        """
        # Call the function to scrape party information on the current page
        defendants, plaintiffs = extract_party_information(driver)

 
        defendants_df = pd.DataFrame(defendants)
        plaintiffs_df = pd.DataFrame(plaintiffs)
        
        ####
        fake_list = [defendants_df, plaintiffs_df]
        print(f"Here is a fake data: {fake_list}")

        # Generate a sheet name dynamically based on the iteration index
        sheet_name = f"Page_{i+1}"

        # Write DataFrames to their corresponding sheets in the same Excel file
        if not defendants_df.empty:
            defendants_df.to_excel(writer, sheet_name=f"{sheet_name}_Defendants", index=False)

        if not plaintiffs_df.empty:
            plaintiffs_df.to_excel(writer, sheet_name=f"{sheet_name}_Plaintiffs", index=False)
       
        time.sleep(15)
        driver.execute_script("window.history.go(-1)")

    # Save and close the Excel file
    writer.close()
    print(f"Party Data saved to {excel_file_path}")


    # Make sure to close the webdriver
    driver.quit()
    print("Success, Review for Inconsitencies in Data")
    print(f"Final Party Data: {defendants_df, plaintiffs_df}")
    return defendants_df, plaintiffs_df


##### Main Code #####
options = Options()
#options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

# Specify a url for Pinnellas County
url = "https://ccmspa.pinellascounty.org/PublicAccess/default.aspx"
print(get_all_case_search(driver, url))
time.sleep(5)