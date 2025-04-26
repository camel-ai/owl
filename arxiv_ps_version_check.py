import feedparser

# Define the base URL for the Arxiv API
base_url = "http://export.arxiv.org/api/query?"

# Define the search query for High Energy Physics - Lattice articles from January 2020
search_query = "search_query=cat:hep-lat+AND+submittedDate:[202001010000+TO+202001312359]"

# Define the full URL with the search query
query_url = f"{base_url}{search_query}&start=0&max_results=100"

# Parse the feed
feed = feedparser.parse(query_url)

# Initialize a counter for articles with ps versions
ps_version_count = 0

# Iterate over each entry in the feed
for entry in feed.entries:
    # Check if the entry has a link to a ps version
    if any(link.type == 'application/postscript' for link in entry.links):
        ps_version_count += 1

# Print the number of articles with ps versions
print(f"Number of articles with ps versions: {ps_version_count}")