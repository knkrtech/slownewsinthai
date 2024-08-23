import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
from celery_worker import translate_text
from google.cloud import texttospeech
import os

# Define the audio directory path
AUDIO_DIR = '/workspaces/slownewsinthai/audio_files'

# Ensure the directory exists
os.makedirs(AUDIO_DIR, exist_ok=True)

def fetch_daily_articles():
    feed = feedparser.parse("https://www.bangkokpost.com/rss/data/topstories.xml")
    bangkok_tz = ZoneInfo("Asia/Bangkok")
    today = datetime.now(bangkok_tz).date()
    
    daily_articles = []
    for entry in feed.entries:
        pub_date = datetime(*entry.published_parsed[:6]).replace(tzinfo=ZoneInfo("UTC")).astimezone(bangkok_tz).date()
        if pub_date == today:
            daily_articles.append({
                'title': entry.title,
                'content': entry.description,
                'link': entry.link,
                'pub_date': pub_date
            })
    
    return daily_articles

def compile_daily_post():
    articles = fetch_daily_articles()
    compiled_post = f"Daily News Summary for {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    for article in articles:
        compiled_post += f"Title: {article['title']}\n"
        compiled_post += f"Original: {article['content']}\n"
        compiled_post += f"Translation: {translate_text(article['content'])}\n"
        compiled_post += f"Link: {article['link']}\n\n"
    
    return compiled_post

def text_to_speech(text, output_file):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="th-TH", 
        name="th-TH-Standard-A"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open(output_file, "wb") as out:
        out.write(response.audio_content)

def run_daily_automation():
    daily_post = compile_daily_post()
    audio_filename = f"daily_summary_{datetime.now().strftime('%Y-%m-%d')}.mp3"
    audio_file_path = os.path.join(AUDIO_DIR, audio_filename)
    text_to_speech(daily_post, audio_file_path)
    return daily_post, audio_file_path, daily_post