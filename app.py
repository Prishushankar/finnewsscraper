from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse # <--- IMPORT THIS
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
from GoogleNews import GoogleNews
import time
import random

app = FastAPI()

# --- Cache Setup ---
news_cache = None
cache_timestamp = None
CACHE_DURATION = timedelta(minutes=30) 

# --- Helper Function to Scrape Images ---
def get_article_image(url):
    try:
        clean_url = url.split('&ved=')[0]
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
    except requests.exceptions.RequestException:
        pass
    except Exception:
        pass
    return None

# --- Root endpoint that now redirects ---

# --- Health Check Endpoint ---
@app.get("/health")
def health_check():
    return {"status": "ok"}
@app.get("/")
def read_root():
    # This will automatically redirect anyone visiting the root URL
    # to the /api/indian-news endpoint.
    return RedirectResponse(url="/api/indian-news")

# --- API Endpoint with Caching Logic ---
@app.get('/api/indian-news')
def get_indian_news():
    global news_cache, cache_timestamp

    if news_cache and (datetime.now() - cache_timestamp < CACHE_DURATION):
        print("Serving news from cache.")
        return news_cache

    print("Cache is empty or expired. Scraping new data...")
    try:
        googlenews = GoogleNews(lang='en', region='IN')
        topics = [
            "Indian Stock Market (NSE & BSE)",
            "Indian Economy News",
            "Startup India Funding",
        ]
        all_news_results = []

        for topic in topics:
            googlenews.search(topic)
            for item in googlenews.result():
                item['topic'] = topic
                all_news_results.append(item)
            googlenews.clear()

        for item in all_news_results:
            item['img'] = get_article_image(item['link'])
            time.sleep(random.uniform(0.5, 1.5))
            
        news_cache = all_news_results
        cache_timestamp = datetime.now()
        
        print("Scraping complete. Cache has been updated.")
        return all_news_results

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))