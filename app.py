from flask import Flask, request, jsonify, render_template, url_for
from flask_caching import Cache
import time
import logging
import os
import glob

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize variables
tokenizer = None
model = None

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    
    # Load pre-trained models
    model_name = "facebook/nllb-200-distilled-600M-en-th"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
except ImportError:
    logger.warning("Failed to import from transformers. Translation feature will not work.")

try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
except ImportError:
    logger.warning("Failed to import nltk. Some features may not work.")

try:
    from gtts import gTTS
except ImportError:
    logger.warning("Failed to import gTTS. Text-to-speech feature may not work.")

try:
    import feedparser
except ImportError:
    logger.warning("Failed to import feedparser. RSS feed fetching may not work.")

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except ImportError:
    logger.warning("Failed to import spacy. Some NLP features may not work.")

try:
    from celery_worker import process_article
    USE_CELERY = True
except ImportError:
    USE_CELERY = False
    logger.warning("Failed to import process_article from celery_worker. Falling back to synchronous processing.")
    
    def process_article(article):
        # Fallback function if Celery is not set up
        from app import translate_text, paraphrase_text, text_to_speech
        
        title = article['title']
        content = article['summary']

        translated_title = translate_text(title)
        translated_content = translate_text(content)

        paraphrased_title = paraphrase_text(translated_title)
        paraphrased_content = paraphrase_text(translated_content)

        audio_filename = f"audio_{article['id']}_{int(time.time())}.mp3"
        text_to_speech(paraphrased_content, audio_filename)

        return {
            'original_title': title,
            'original_content': content,
            'translated_title': translated_title,
            'translated_content': translated_content,
            'paraphrased_title': paraphrased_title,
            'paraphrased_content': paraphrased_content,
            'audio_file': audio_filename
        }

app = Flask(__name__, static_folder='static', template_folder='.')

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def translate_text(text):
    if tokenizer is None or model is None:
        logger.warning("Translation model not loaded. Returning original text.")
        return text
    
    try:
        inputs = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=512,
            return_attention_mask=True,
            return_tensors="pt"
        )

        outputs = model.generate(
            inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            num_beams=4,
            max_length=512,
            early_stopping=True
        )

        translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translation
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        return text

def paraphrase_text(text):
    if nlp is None:
        logger.warning("spaCy model not loaded. Returning original text.")
        return text
    
    doc = nlp(text)
    return " ".join([token.text for token in doc if not token.is_stop])

def text_to_speech(text, filename):
    try:
        audio_path = os.path.join(app.static_folder, 'audio', filename)
        tts = gTTS(text=text, lang='th')
        tts.save(audio_path)
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")

def cleanup_old_audio_files():
    audio_files = glob.glob(os.path.join(app.static_folder, 'audio', '*.mp3'))
    for file in audio_files:
        os.remove(file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/articles')
@cache.cached(timeout=300)
def get_articles():
    articles = fetch_rss_feed()
    return jsonify([{'title': article.title} for article in articles[:10]])

@app.route('/process', methods=['POST'])
def process():
    try:
        selected_indices = request.json['articles']
        articles = fetch_rss_feed()
        selected_articles = [articles[int(i)] for i in selected_indices]

        if USE_CELERY:
            from celery import group
            tasks = group(process_article.s({'id': i, **article}) for i, article in enumerate(selected_articles))
            result = tasks.apply_async()
            processed_articles = result.get(timeout=300)
        else:
            processed_articles = [process_article({'id': i, **article}) for i, article in enumerate(selected_articles)]

        # Add the audio file URL
        for article in processed_articles:
            article['audio_file'] = url_for('static', filename=f'audio/{article["audio_file"]}')

        return jsonify(processed_articles)
    except Exception as e:
        logger.error(f"Error processing articles: {str(e)}")
        return jsonify({"error": "An error occurred while processing articles"}), 500

def fetch_rss_feed():
    try:
        feed = feedparser.parse("https://www.bangkokpost.com/rss/data/topstories.xml")
        return feed.entries
    except Exception as e:
        logger.error(f"Error fetching RSS feed: {str(e)}")
        return []

if __name__ == "__main__":
    app.run(debug=True)