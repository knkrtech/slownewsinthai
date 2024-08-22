from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

app = Flask(__name__)
CORS(app)

# Load a pre-trained model and tokenizer
model_name = "t5-base"
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

@app.route("/translate", methods=["POST"])
def translate():
    text = request.get_json()["text"]
    translation = translate_text(text)
    return jsonify({"translation": translation})

if __name__ == "__main__":
    app.run(debug=True)