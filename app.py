from flask import Flask, request, jsonify, render_template, url_for
from flask_caching import Cache
import time
import logging
import os
import glob
import feedparser
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='.')
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Try to import Celery, but don't fail if it's not available
try:
    from celery import group
    from celery_worker import process_article
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery is not available. Running in non-distributed mode.")

# Set Google Application Credentials
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    print(f"Using Google credentials from: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
else:
    print("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/articles')
@cache.cached(timeout=300)
def get_articles():
    articles = fetch_rss_feed()
    return jsonify([{'title': article.title, 'summary': article.summary, 'content': article.content, 'link': article.link} for article in articles[:10]])

@app.route('/process', methods=['POST'])
def process():
    try:
        selected_indices = request.json['articles']
        articles = fetch_rss_feed()
        selected_articles = [{'title': articles[int(i)].title, 'summary': articles[int(i)].summary, 'content': articles[int(i)].content, 'link': articles[int(i)].link} for i in selected_indices]

        logger.info(f"Processing {len(selected_articles)} articles")

        processed_articles = []
        for article in selected_articles:
            try:
                processed = process_article(article)
                logger.info(f"Processed article: {processed}")
                processed_articles.append(processed)
            except Exception as e:
                logger.error(f"Error processing article '{article['title']}': {str(e)}")

        if not processed_articles:
            raise Exception("No articles were successfully processed")

        return jsonify(processed_articles)
    except Exception as e:
        logger.error(f"Error processing articles: {str(e)}")
        return jsonify({"error": "An error occurred while processing articles"}), 500

def fetch_rss_feed():
    try:
        feed = feedparser.parse("https://www.bangkokpost.com/rss/data/topstories.xml")
        articles = []
        for entry in feed.entries[:10]:  # Limit to 10 articles
            try:
                full_content = fetch_full_article_content(entry.link)
                articles.append({
                    'title': entry.title,
                    'summary': entry.summary,
                    'content': full_content,
                    'link': entry.link
                })
            except Exception as e:
                logger.error(f"Error fetching full content for {entry.link}: {str(e)}")
        return articles
    except Exception as e:
        logger.error(f"Error fetching RSS feed: {str(e)}")
        return []

def fetch_full_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_body = soup.find('div', class_='articl-content')  # Adjust this selector based on the website's structure
    if article_body:
        paragraphs = article_body.find_all('p')
        content = ' '.join([p.text for p in paragraphs])
        return content[:1000]  # Limit to first 1000 characters (adjust as needed)
    return ""

if __name__ == "__main__":
    app.run(debug=True)