import feedparser
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from gtts import gTTS
import os

# Load a pre-trained model and tokenizer
model_name = "t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

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
    # Preprocess the input text
    inputs = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=512,
        return_attention_mask=True,
        return_tensors="pt"
    )

    # Generate the translation
    outputs = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        num_beams=4,
        max_length=512,
        early_stopping=True
    )

    # Postprocess the output
    translation = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return translation

def generate_audio_files(news_data):
    # Generate audio files for each news article
    for article in news_data:
        translated_title = translate_text(article['title'])
        translated_content = translate_text(article['content'])
        audio_file = gTTS(text=translated_title + translated_content, lang='th')
        audio_file.save(translated_title + '.mp3')

def run_automation():
    news_data = fetch_news_data()
    generate_audio_files(news_data)

if __name__ == "__main__":
    run_automation()