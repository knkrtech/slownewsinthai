import os
import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
from celery_worker import translate_text
from google.cloud import texttospeech
from pydub import AudioSegment
import io
import re

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
    compiled_post = f"บทสรุปข่าวประจำวันที่ {datetime.now(ZoneInfo('Asia/Bangkok')).strftime('%Y-%m-%d')}\n\n"
    
    for article in articles:
        thai_title = translate_text(article['title'])
        thai_content = translate_text(article['content'])
        english_title = article['title']
        english_content = article['content']
        
        compiled_post += f"• {thai_title}\n"
        compiled_post += f"  (English: {english_title})\n"
        
        thai_sentences = re.split(r'(?<=[.!?])\s+', thai_content)
        english_sentences = re.split(r'(?<=[.!?])\s+', english_content)
        
        for thai_sentence, english_sentence in zip(thai_sentences[:3], english_sentences[:3]):
            compiled_post += f"  - {thai_sentence.strip()}\n"
            compiled_post += f"    (English: {english_sentence.strip()})\n"
        compiled_post += "\n"
    
    return compiled_post

def text_to_speech(text, output_file):
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code="th-TH",
        name="th-TH-Neural2-C"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.8
    )

    # Remove English subtitles (content in parentheses)
    thai_only_text = re.sub(r'\(English:.*?\)\n?', '', text)

    # Split text into sentences and then into smaller chunks
    sentences = re.split(r'(?<=[.!?])\s+', thai_only_text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < 2000:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())

    combined_audio = AudioSegment.empty()
    for chunk in chunks:
        synthesis_input = texttospeech.SynthesisInput(text=chunk)
        try:
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            chunk_audio = AudioSegment.from_mp3(io.BytesIO(response.audio_content))
            combined_audio += chunk_audio
        except Exception as e:
            print(f"Error processing chunk: {e}")
            print(f"Chunk size: {len(chunk.encode('utf-8'))} bytes")
            print(f"Chunk content: {chunk[:100]}...")

    combined_audio.export(output_file, format="mp3")
    print(f"Audio content written to file {output_file}")

def run_daily_automation():
    try:
        print("Starting daily automation...")
        daily_post = compile_daily_post()
        print(f"Daily post compiled: {daily_post[:100]}...")  # Print first 100 chars
        audio_filename = f"daily_summary_{datetime.now().strftime('%Y-%m-%d')}.mp3"
        audio_file_path = os.path.join(AUDIO_DIR, audio_filename)
        print(f"Generating audio file: {audio_file_path}")
        text_to_speech(daily_post, audio_file_path)
        print("Audio file generated successfully")
        return daily_post, audio_file_path, daily_post
    except Exception as e:
        print(f"Error in run_daily_automation: {str(e)}")
        raise