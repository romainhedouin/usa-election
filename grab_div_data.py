from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import json

# Base URL for the site
base_url = "https://www.nbcnews.com"

with open('states_to_exclude.json', 'r') as file:
    exclusions_json = json.load(file)

# Load the list of links from the file
with open('nbc_states.json', 'r') as file:
    states = [line.strip() for line in json.load(file)]

def is_excluded(state):
    return exclusions_json[state]


# Initialize Selenium WebDriver (assuming Chrome; make sure the chromedriver is in your PATH)
driver = webdriver.Chrome()

# Iterate over each link
for state in states:
    if is_excluded(state) is True:
        continue
    # Open the link
    driver.get(base_url + "/politics/2024-elections/" + state + "-president-results")
    
    
    try:
        # Try to locate the button; if it doesn't exist, skip clicking
        try:
            button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "president-results-table-toggle"))
            )
            # If button is found, click it using JavaScript
            driver.execute_script("arguments[0].click();", button)
            time.sleep(1)  # Adjust if necessary to allow data loading
        except Exception:
            print(f"No button found to click for {state}. Continuing...")
        
        # Retrieve the state name from the page title
        title_element = driver.find_element(By.CSS_SELECTOR, 'h1.page-title.state-county-title')
        state_name = title_element.text.split(' President Results')[0]
        
        # Create directory for the state if it doesn't exist
        state_dir = f'states/{state_name}'
        os.makedirs(state_dir, exist_ok=True)
        
        # Find all county rows and save their HTML content
        county_rows = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="county-row"]')
        with open(f'{state_dir}/raw_div.txt', 'w') as outfile:
            for row in county_rows:
                outfile.write(row.get_attribute('outerHTML') + '\n\n')
                
        print(f"Data saved for {state_name}")
    
    except Exception as e:
        print(f"An error occurred for {state}: {e}")

# Close the driver
driver.quit()
