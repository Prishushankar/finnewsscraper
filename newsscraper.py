import pandas as pd
import requests
from bs4 import BeautifulSoup
from GoogleNews import GoogleNews
import time
import random

def get_article_image(url):
    """
    Visits a cleaned article URL and scrapes the main image,
    prioritizing the 'og:image' meta tag.
    """
    try:
        # Step 1: Clean the URL by removing Google's tracking parameters
        clean_url = url.split('&ved=')[0]

        # Step 2: Use more realistic browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        
        response = requests.get(clean_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        og_image = soup.find('meta', property='og:image')

        if og_image and og_image.get('content'):
            return og_image['content']

    except requests.exceptions.RequestException as e:
        print(f"  -> Could not fetch URL {clean_url}: {e}")
    except Exception as e:
        print(f"  -> An error occurred while processing {clean_url}: {e}")

    return None

# --- Main Script ---
print("Initializing Google News client for India...")
googlenews = GoogleNews(lang='en', region='IN')

topics = [
    "Indian Stock Market (NSE & BSE)",
    "Indian Economy News",
    "Startup India Funding",
]

all_news_results = []
print("Searching for the latest Indian financial news...")

for topic in topics:
    googlenews.search(topic)
    for item in googlenews.result():
        item['topic'] = topic
        all_news_results.append(item)
    googlenews.clear()

print(f"\nFound {len(all_news_results)} total articles.")
print("Fetching main image for each article... (This will be slower to appear more human)")

for i, item in enumerate(all_news_results):
    print(f"Processing article {i+1}/{len(all_news_results)}: {item['title'][:50]}...")
    item['img'] = get_article_image(item['link'])
    
    # Step 3: Add a random delay to be respectful to the servers
    sleep_time = random.uniform(1, 3)
    time.sleep(sleep_time)

# --- Display the Final Results ---
if all_news_results:
    df = pd.DataFrame(all_news_results)
    print("\n--- JSON Output with Working Image Links ---")
    print(df.to_json(orient='records', indent=4))
else:
    print("Could not find any news articles at this time.")