from datetime import timedelta
from datetime import date
from scraper_functions import *

### Function to clean excel files based off of Equity ####
def equity_cleaner(input_path, output_path):
    # Function to convert currency to float
    def currency_to_float(currency_str):
        try:
            return float(currency_str.replace("$", "").replace(",", ""))
        except:
            return None  # Return None if conversion fails
        
    # read the input data
    input_df = pd.read_excel(input_path)

    # Convert currency columns to float for calculations
    input_df['Final Judgment Amount:'] = input_df['Final Judgment Amount:'].apply(currency_to_float)
    input_df['Assessed Value:'] = input_df['Assessed Value:'].apply(currency_to_float)

    # Calculate 'Equity' column as Assessed Value - Final Judgment Amount
    input_df['Equity'] = input_df['Assessed Value:'] - input_df['Final Judgment Amount:']

    # Save the DataFrame to a new Excel file
    input_df.to_excel(output_path, index=False)
    
    return output_path 

### Function to generate a list of weekdays ###
def generate_weekdays(start_date, days=21):
    weekdays = []
    current_date = start_date
    while len(weekdays) < days:
        if current_date.weekday() < 5: # Monday is 0 and Sunday is 6
            weekdays.append(current_date)
        current_date += timedelta(days=1)
    return weekdays

def visit_auction_pages_extended(driver, url, weekdays, url_to_county):
    ALL_DATA = []
    
    for target_date in weekdays_to_scrape:
        # Use driver to navigate to the website
        driver.get(url)
        print(driver.title)

        # Click on Auction Calander
        wait = WebDriverWait(driver, 10)
        auction_calander_element = driver.find_element(By.ID, "splashMenuBottom")
        auction_calander_element.click()
        time.sleep(5)

        navigate_to_target_month(driver, target_date)
        time.sleep(10)

        auction_date(driver, target_date)
        time.sleep(10)

        # Wait for the content to load
        driver.implicitly_wait(5)
        time.sleep(20)
        page_source = driver.page_source

        stats = extract_auction_data(page_source)
        details = extract_auction_details(page_source)
        # check the 'details' to decide whether to call the other method
        if all(not bool(d) for d in details):
            details = extract_data(page_source) 

        data = []
        for i in range(len(stats)):
            merged_dict = {**stats[i], **details[i]}  # Merge dictionaries at index i
            data.append(merged_dict)

        df = pd.DataFrame(data)

        # Add the 'Counties' column
        county_name = "Unknown"
        for county_url in url_to_county:
            if url in county_url.values():
                county_name = list(county_url.keys())[0]
                break
        
        df["Counties"] = county_name
        
        if df.empty:
            print("Empty DataFrame, no content found")
        else:
            print("Raw Data:")
            print(df.head())
        ALL_DATA.append(df)
    
    # Combine all dataframes
    final_df = pd.concat(ALL_DATA, ignore_index=True)
    return final_df

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

def store_all_data(driver, urls_to_visit, weekdays, url_to_county):
    # Initialize an empty Dataframe with the same columns as your data
    all_data = pd.DataFrame(columns=['Auction Sold', 'Amount', 'Sold To', 'Auction Type:', 'Case #:',
        'Final Judgment Amount:', 'Parcel ID:', 'Property Address:', '',
        'Assessed Value:', 'Plaintiff Max Bid:', 'Auction Status'])
    print(f"Type of all_data: {type(all_data)}")  # Debugging line
    # Iterate through the list of URLs and scrape data
    for url in urls_to_visit:
        df = visit_auction_pages_extended(driver, url, weekdays_to_scrape, url_to_county)
        print(f"Type of df: {type(df)}")
        all_data = pd.concat([all_data, df], ignore_index=True)
    
    return all_data

### Main Code ###
# define webdriver and options                
options = Options()
driver = webdriver.Chrome(options=options)

# Define a list of URLs to visit
all_urls = ['https://hillsborough.realforeclose.com/index.cfm']#, 'https://hillsborough.realtaxdeed.com/index.cfm?resetcfcobjs=1', 
#            'https://pinellas.realforeclose.com/index.cfm?resetcfcobjs=1', 'https://pinellas.realtaxdeed.com/index.cfm?resetcfcobjs=1']
url_to_county = [{'hillsborough': 'https://hillsborough.realforeclose.com/index.cfm'},
                 {'hillsborough': 'https://hillsborough.realtaxdeed.com/index.cfm?resetcfcobjs=1'},
                 {'pinellas': 'https://pinellas.realforeclose.com/index.cfm?resetcfcobjs=1'},
                 {'pinellas': 'https://pinellas.realtaxdeed.com/index.cfm?resetcfcobjs=1'},
]
# use the current date as the target date
#start_date = datetime.now()
start_date = date(2023, 11, 27)
weekdays_to_scrape = generate_weekdays(start_date)


#data = visit_auction_pages_extended(driver, url, weekdays_to_scrape)
data = store_all_data(driver, all_urls, weekdays_to_scrape, url_to_county)

driver.quit()

# Specify the base path and extension for the Excel file
base_path = r"C:\Users\jacks\OneDrive\Desktop\Auction Automations\WORKING_Web_Scraper\data"
extension = "xlsx"

# Get the current date and time, and format as string
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create a unique filename by appending the date and time
unique_filename = f"raw_data_{current_datetime}"
file_path = f"{base_path}\\{unique_filename}.{extension}"
data.to_excel(file_path, index=False)


cleaned_filename = f"cleaned_surplus_{current_datetime}"
cleaned_file_path = f"{base_path}\\{cleaned_filename}.{extension}"
output_path = clean_excel_file(file_path, cleaned_file_path)

equity_filename = f"equity_{current_datetime}"
# Combine the base path and extension to create the full file path
equity_file_path = f"{base_path}\\{equity_filename}.{extension}"
# Clean the raw excel file
output_path_2 = equity_cleaner(file_path, equity_file_path)
# Save the combined DataFrame to the specified file path

print(f"Data saved to {file_path}")
## Send email of the data ##
subject = "Weekly Equity Report"
message = "Here is the equity data for specified counties in florida. This data is for the next three weeks."
attachment_paths = [file_path, cleaned_file_path, equity_file_path]
