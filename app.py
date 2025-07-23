# --- Part 0: Imports (with new additions) ---
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from GoogleNews import GoogleNews
import pandas as pd
import random
import time

app = FastAPI()

# --- Part 1: Self-Pinging Logic ---
def ping_self():
    """
    Sends a GET request to the root URL of the app to keep it alive.
    """
    try:
        # Render provides the `RENDER_EXTERNAL_URL` environment variable
        app_url = os.environ.get("RENDER_EXTERNAL_URL")
        if app_url:
            print(f"Pinging {app_url} to keep alive...")
            requests.get(app_url, timeout=10)
            print("Ping successful.")
        else:
            # This is a fallback for local testing or other environments
            print("RENDER_EXTERNAL_URL not set. Cannot ping self.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to ping self: {e}")

@app.on_event("startup")
def startup_event():
    """
    Initializes the scheduler and adds the ping job when the app starts.
    """
    scheduler = BackgroundScheduler()
    # Ping every 14 minutes, safely inside Render's 15-minute timeout
    scheduler.add_job(ping_self, 'interval', minutes=14)
    scheduler.start()
    print("Scheduler started. App will be pinged every 14 minutes.")
# --- End of Self-Pinging Logic ---


# --- CORS Configuration ---
origins = [
    "*",  # Allows all origins. For production, restrict this to your frontend domain.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

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
@app.get("/")
def read_root():
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
        raise HTTPException(status_code=500, detail=str(e))
