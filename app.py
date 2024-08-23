from flask import Flask, request, jsonify, render_template_string
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from gtts import gTTS
import os

try:
    import nltk
except ImportError:
    print("Installing nltk...")
    import subprocess
    subprocess.check_call(["pip", "install", "nltk"])
    import nltk

nltk.download('punkt')

app = Flask(__name__)

# Load a pre-trained model and tokenizer
model_name = "facebook/nllb-200-distilled-600M-en-th"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Define a function to translate text
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

# Define a route for the root URL
@app.route('/')
def index():
    return render_template_string('''
        <html>
            <body>
                <h1>Welcome to my translation app!</h1>
                <form action="/translate" method="post">
                    <input type="text" name="text" placeholder="Enter text to translate">
                    <input type="submit" value="Translate">
                </form>
            </body>
        </html>
    ''')

# Define a route for the /translate endpoint
@app.route('/translate', methods=['POST'])
def translate():
    # Get the text to be translated from the request body
    text = request.form['text']

    # Translate the text
    translation = translate_text(text)

    # Return the translation as a JSON response
    return jsonify({'translation': translation})

if __name__ == "__main__":
    app.run(debug=True)