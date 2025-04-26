import requests
from bs4 import BeautifulSoup

# URL of the NeurIPS 2022 Conference page on OpenReview.net
url = 'https://openreview.net/group?id=NeurIPS.cc/2022/Conference'

# Send a GET request to the URL
response = requests.get(url)

# Parse the content of the page with BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find all papers on the page
papers = soup.find_all('li', class_='note')

yuri_papers = []

# Iterate through each paper to find authors named Yuri and check recommendation status
for paper in papers:
    title = paper.find('h4', class_='title').text.strip()
    authors = paper.find('p', class_='authors').text.strip()
    recommendation = paper.find('span', class_='recommendation').text.strip()
    
    # Check if 'Yuri' is in the list of authors and if the recommendation is 'certain'
    if 'Yuri' in authors and 'certain' in recommendation:
        yuri_papers.append((title, authors, recommendation))

# Print the results
print(f"Papers by Yuri with 'certain' recommendation: {len(yuri_papers)}")
for paper in yuri_papers:
    print(f"Title: {paper[0]}, Authors: {paper[1]}, Recommendation: {paper[2]}")