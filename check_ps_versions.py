import requests
from bs4 import BeautifulSoup

# URL of the Arxiv page for High Energy Physics - Lattice articles in January 2020
url = 'https://arxiv.org/list/hep-lat/2020-01'

# Send a GET request to the URL
response = requests.get(url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find all the articles listed on the page
articles = soup.find_all('dt')

# Initialize a counter for articles with a 'ps' version
ps_count = 0

# Iterate through each article
for article in articles:
    # Check if a 'ps' version is available
    if article.find('a', string='ps'):
        ps_count += 1

# Print the total number of articles with a 'ps' version
print(f'Total number of articles with a ps version: {ps_count}')