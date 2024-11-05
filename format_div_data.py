import os
from bs4 import BeautifulSoup

with open('raw_data.csv', 'w') as output_file:
    output_file.write('State;County;Total Votes;Percent In;Harris Real;Trump Real;Harris Predicted;Trump Predicted\n')
#    output_file.write('State;County;Total Votes;Percent In;Harris Real;Trump Real\n')

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
                county_total_votes = int(soup.find('span', {'data-testid': 'state-results-table-area-votes'}).text.split()[0])
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
                votes = int(candidate.find('td', {'data-type': 'votes'}).text.strip())

                votes_dict[candidate_name] = {'real': votes, 'predicted': int(votes*(100/county_percent_in))}
            
            with open('raw_data.csv', 'a') as output_file:
                output_file.write(f"{state_name};{county_name};{county_total_votes};{county_percent_in};{votes_dict['Kamala Harris']['real']};{votes_dict['Donald Trump']['real']}\n")
#                output_file.write(f"{state_name};{county_name};{county_total_votes};{county_percent_in};{votes_dict['Kamala Harris']['real']};{votes_dict['Donald Trump']['real']};{votes_dict['Kamala Harris']['predicted']};{votes_dict['Donald Trump']['predicted']}\n")
    else:
        print(f'{file_path} does not exist.')

def process_all():
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


if __name__ == '__main__':
    process_all()