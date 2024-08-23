import os
import feedparser
from datetime import datetime
from zoneinfo import ZoneInfo
from celery_worker import translate_text
from google.cloud import texttospeech
from pydub import AudioSegment
import io

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
    compiled_post = f"บทสรุปข่า��ประจำวันที่ {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    for article in articles:
        compiled_post += f"หัวข้อ: {article['title']}\n"
        compiled_post += f"เนื้อหา: {translate_text(article['content'])}\n"
        compiled_post += f"ลิงก์: {article['link']}\n\n"
    
    return compiled_post

def text_to_speech(text, output_file):
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code="th-TH", 
        name="th-TH-Standard-A"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Split the text into smaller chunks (approximately 3000 bytes each)
    def split_text(text, chunk_size=3000):
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        for word in words:
            if current_size + len(word.encode('utf-8')) > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(word)
            current_size += len(word.encode('utf-8')) + 1  # +1 for space
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        return chunks

    text_chunks = split_text(text)
    
    combined_audio = AudioSegment.empty()
    for chunk in text_chunks:
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
            print(f"Chunk content: {chunk[:100]}...")  # Print first 100 characters of the chunk

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