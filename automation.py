import feedparser
from googletrans import Translator
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from gTTS import gTTS
import os

def fetch_news_data():
    # Fetch news data from Bangkok Post's RSS feed
    feed = feedparser.parse('https://www.bangkokpost.com/rss/data/topstories.xml')
    news_data = []
    for entry in feed.entries:
        news_data.append({
            'title': entry.title,
            'content': entry.description
        })
    return news_data

def translate_text(text):
    # Translate text from English to Thai using Google Translate
    translator = Translator()
    translated_text = translator.translate(text, dest='th')
    return translated_text.text

def paraphrase_text(text):
    # Paraphrase text using NLTK
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
    paraphrased_text =''.join(filtered_tokens)
    return paraphrased_text

def generate_audio_files(news_data):
    # Generate audio files for each news article
    for article in news_data:
        translated_title = translate_text(article['title'])
        paraphrased_title = paraphrase_text(translated_title)
        translated_content = translate_text(article['content'])
        paraphrased_content = paraphrase_text(translated_content)
        audio_file = gTTS(text=paraphrased_title +'' + paraphrased_content, lang='th')
        audio_file.save(paraphrased_title + '.mp3')

def run_automation():
    news_data = fetch_news_data()
    generate_audio_files(news_data)

if __name__ == "__main__":
    run_automation()