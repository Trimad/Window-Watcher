from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO

import argparse
import torch
import re
import time
import gradio as gr
from moondream import detect_device, LATEST_REVISION
from threading import Thread
from transformers import TextIteratorStreamer, AutoTokenizer, AutoModelForCausalLM

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--cpu", action="store_true")
args = parser.parse_args()

if args.cpu:
    device = torch.device("cpu")
    dtype = torch.float32
else:
    device, dtype = detect_device()
    if device != torch.device("cpu"):
        print("Using device:", device)
        print("If you run into issues, pass the `--cpu` flag to this script.")
        print()
        
# Initialize the model
model_id = "vikhyatk/moondream2"
tokenizer = AutoTokenizer.from_pretrained(model_id, revision=LATEST_REVISION)
moondream = AutoModelForCausalLM.from_pretrained(
    model_id, trust_remote_code=True, revision=LATEST_REVISION
).to(device=device, dtype=dtype)
moondream.eval()

@app.route('/itt', methods=['POST'])
def get_answer():
    if 'image' not in request.files or 'prompt' not in request.form:
        return jsonify({"error": "Missing image file or prompt"}), 400

    image_file = request.files['image']
    prompt = request.form['prompt']

    image = Image.open(BytesIO(image_file.read()))

    # Ensure image size is optimal for the model
    # image = image.resize((optimal_width, optimal_height))

    image_embeds = moondream.encode_image(image)

    answer = moondream.answer_question(image_embeds, prompt, tokenizer)
    
    return jsonify({"text": answer})

@app.route('/test', methods=['GET'])
def test():
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # You can use the prompt for something if needed, for now just returning OK
    return jsonify({"message": "OK"}), 200

if __name__ == "__main__":
    # Disable debug for production
    app.run(debug=False, host='0.0.0.0')
