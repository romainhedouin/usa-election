import requests
from bs4 import BeautifulSoup
import re
import json

# Base URL for the site
base_url = "https://www.nbcnews.com"
main_url = base_url + "/politics/2024-elections/president-results"

# Pattern to match links with "/president-results" in the URL
pattern = re.compile(r"/politics/2024-elections/.+-president-results")

# List to store unique matching links while preserving order
matching_links = []

# Function to retrieve and parse links from a page
def get_links_from_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the h2 element with the specific text
        start_collecting = False
        for element in soup.find_all(True):
            # Start collecting after finding the target h2
            if element.name == "h2" and "All Presidential races" in element.get_text():
                start_collecting = True
                continue
            
            # Collect matching links only after "All Presidential races" h2 is found
            if start_collecting and element.name == "a" and element.has_attr("href"):
                href = element["href"]
                if pattern.match(href) and href not in matching_links:
                    matching_links.append(href.split('/')[3].split('-president-results')[0])  # Add only if it’s not already in the list

    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")

# Start with the base URL
get_links_from_page(main_url)


with open('nbc_states.json', 'w') as file:
    file.write(json.dumps(matching_links, indent=4))

print("Links saved to nbc_states.json")