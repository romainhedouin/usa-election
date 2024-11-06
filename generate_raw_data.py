from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys
import time
import json
from bs4 import BeautifulSoup

# Base URL for the site
base_url = "https://www.nbcnews.com"

with open('states_to_exclude.json', 'r') as file:
    exclusions_json = json.load(file)

def process_state(folder_path, state_name):
    file_path = os.path.join(folder_path, 'raw_div.txt')
    
    # Check if the raw_div.txt file exists
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        for line in content.split('\n'):
            if line.strip() == '':
                continue
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(line, 'html.parser')

            try:
                # Find the county name using the specified span class
                county_row = soup.find('div', {'data-testid': 'county-row'})
                county_name_element = county_row.find('span', class_='dib dn-m')  # Get the county name from the right span
                county_name = county_name_element.text.strip() if county_name_element else 'Unknown County'
                if ' EV ' in county_name:
                    # ugly workaround for Maine and Nebraska but... gimme a break
                    continue
                total_expected = int(soup.find('div', {'id': 'total-estimated'}).text.strip().replace(',', ''))
                county_total_votes = int(soup.find('span', {'data-testid': 'state-results-table-area-votes'}).text.split()[0].replace(',', ''))
                county_percent_in = float(soup.find('span', {'class': 'percent-in'}).text.split('%')[0])
                county_percent_in = 100.0 if county_percent_in in (95.0, 0) else county_percent_in
            except Exception as e:
                print(f'Error processing {county_name}, {state_name}. Exception: {e}')
                continue
            
            # Find the candidates and their votes
            candidates = county_row.find('div', {'class': 'county-table'}).find_all('tr', {'class': 'row'})
            votes_dict = {}
            for candidate in candidates:
                # Extract candidate name
                candidate_name = candidate.find('span', class_='cand-cell-name').find('span', {'data-testid': 'text--m'}).text.strip()
                
                # Extract number of votes
                votes = int(candidate.find('td', {'data-type': 'votes'}).text.strip().replace(',', ''))

                votes_dict[candidate_name] = {'real': votes, 'predicted': int(votes*(100/county_percent_in))}
            
            with open('raw_data.csv', 'a') as output_file:
#                output_file.write(f"{state_name};{county_name};{county_total_votes};{county_percent_in};{votes_dict['Kamala Harris']['real']};{votes_dict['Donald Trump']['real']}\n")
                output_file.write(f"{state_name};{county_name};{total_expected};{county_total_votes};{county_percent_in};{votes_dict['Kamala Harris']['real']};{votes_dict['Donald Trump']['real']};{votes_dict['Kamala Harris']['predicted']};{votes_dict['Donald Trump']['predicted']}\n")
    else:
        print(f'{file_path} does not exist.')

def process_all():
    with open('raw_data.csv', 'w') as output_file:
        output_file.write('State;County;Total Expected;Total Votes;Percent In;Harris Real;Trump Real;Harris Predicted;Trump Predicted\n')
#        output_file.write('State;County;Total Votes;Percent In;Harris Real;Trump Real\n')

    # Define the directory containing the folders
    directory = './states/'

    # Get a sorted list of all folders in the directory
    folders = sorted(os.listdir(directory))

    # Iterate through each folder
    for folder in folders:
        folder_path = os.path.join(directory, folder)
        
        # Check if it's a directory
        if os.path.isdir(folder_path):
            state_name = folder.replace('_', ' ')

            process_state(folder_path, state_name)

def grab_data():
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
            total_counted = int(driver.find_element(By.ID, 'president-results-summary-grid').find_element(By.ID, 'president-results-summary-container').find_element(By.CLASS_NAME, 'rs-total-votes').text.replace(',', ''))
            estimated_remaining = int(driver.find_element(By.CLASS_NAME, 'percent-in').text.split('remaining ')[1].split(')')[0].replace(',', ''))
            total_expected = f'<div id="total-estimated">{total_counted+estimated_remaining}</div>'

            # Create directory for the state if it doesn't exist
            state_dir = f'states/{state_name}'
            os.makedirs(state_dir, exist_ok=True)
            
            # Find all county rows and save their HTML content
            county_rows = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="county-row"]')
            with open(f'{state_dir}/raw_div.txt', 'w') as outfile:
                for row in county_rows:
                    outfile.write(total_expected + row.get_attribute('outerHTML') + '\n\n')
                    
            print(f"Data saved for {state_name}")
        
        except Exception as e:
            print(f"An error occurred for {state}: {e}")

    # Close the driver
    driver.quit()


if __name__ == '__main__':
    if '--no-grab' not in sys.argv:
        grab_data()
    process_all()