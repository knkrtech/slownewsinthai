from celery import Celery
import time

celery = Celery('tasks', broker='redis://localhost:6379/0')

celery.conf.update(
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery.task
def process_article(article):
    # Import functions from app.py
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