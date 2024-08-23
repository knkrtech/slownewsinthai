from celery import Celery
import time
from google.cloud import translate_v3 as translate
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Create Celery app
celery = Celery('tasks', broker='redis://localhost:6379/0')

# Configure Celery
celery.conf.update(
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = translate.TranslationServiceClient()
project_id = "total-pier-425200-f4"  # Replace if different
location = "global"
parent = f"projects/{project_id}/locations/{location}"

@celery.task
def translate_text(text):
    try:
        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [text],
                "mime_type": "text/plain",
                "source_language_code": "en-US",
                "target_language_code": "th",
            }
        )
        return response.translations[0].translated_text
    except Exception as e:
        print(f"Error translating text: {str(e)}")
        return text

@celery.task
def process_article(article):
    title = article['title']
    content = article['content']

    translated_title = translate_text(title)
    translated_content = translate_text(content)

    return {
        'original_title': title,
        'original_content': content,
        'translated_title': translated_title,
        'translated_content': translated_content,
        'link': article['link']
    }