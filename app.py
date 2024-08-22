from flask import Flask, jsonify, send_file
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# Thai news API or RSS feed URL
NEWS_API_URL = "https://example.com/thai-news-api"

# TTS service API key
TTS_API_KEY = "YOUR_TTS_API_KEY"

@app.route("/news", methods=["GET"])
def get_news():
    # Fetch news from API or RSS feed
    news_data = requests.get(NEWS_API_URL).json()
    
    # Process news data (e.g., extract titles, summaries, etc.)
    processed_news = []
    for article in news_data:
        title = article["title"]
        summary = article["summary"]
        processed_news.append({"title": title, "summary": summary})
    
    return jsonify(processed_news)

@app.route("/audio/<string:news_id>", methods=["GET"])
def get_audio(news_id):
    # Fetch news article by ID
    news_article = requests.get(f"{NEWS_API_URL}/{news_id}").json()
    
    # Convert text to speech using TTS service
    tts_response = requests.post(
        f"https://texttospeech.googleapis.com/v1/text:synthesize",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": news_article["text"], "voice": "th-TH-Wavenet-A"}),
        auth=("Bearer", TTS_API_KEY)
    )
    
    # Return audio file
    return send_file(tts_response.content, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True)