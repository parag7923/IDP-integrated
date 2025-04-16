from flask import Blueprint, render_template, request, jsonify
import os
import shutil
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import pdf2image
import easyocr
from werkzeug.utils import secure_filename

summary_bp = Blueprint('summary', __name__, template_folder='templates', static_folder='static')

# Setup upload folder specific to summary module
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'summary')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load models
checkpoint = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
base_model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint, device_map="auto", torch_dtype=torch.float32)
reader = easyocr.Reader(['en'])

# Helper functions
def extract_text_from_image(image_path):
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

def extract_text_from_pdf_images(pdf_path):
    images = pdf2image.convert_from_path(pdf_path)
    extracted_text = ""
    for i, image in enumerate(images):
        temp_image_path = os.path.join(UPLOAD_FOLDER, f"temp_page_{i}.jpg")
        image.save(temp_image_path, "JPEG")
        extracted_text += extract_text_from_image(temp_image_path) + "\n"
        os.remove(temp_image_path)
    return extracted_text

def extract_text_from_file(file_path):
    if file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        texts = text_splitter.split_documents(pages)
        extracted_text = "\n".join([text.page_content for text in texts])
        if not extracted_text.strip():
            extracted_text = extract_text_from_pdf_images(file_path)
    elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        extracted_text = extract_text_from_image(file_path)
    else:
        raise ValueError("Unsupported file format.")
    return extracted_text

def generate_summary(text, max_length, min_length):
    summarization_pipeline = pipeline('summarization', model=base_model, tokenizer=tokenizer, max_length=max_length, min_length=min_length)
    result = summarization_pipeline(text)
    return result[0]['summary_text']

# Routes
@summary_bp.route('/')
def index():
    return render_template('summary/index.html')

@summary_bp.route('/uploads', methods=['POST'], endpoint='upload')
def summarize():
    try:
        # Clean old uploads (optional, for fresh start each time)
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Check file
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Summary type
        summary_type = request.form.get('summary-length')
        if not summary_type:
            return jsonify({"error": "Missing summary length"}), 400
        max_length, min_length = (150, 60) if summary_type == "short" else (500, 200)

        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Extract & summarize
        extracted_text = extract_text_from_file(filepath)
        if not extracted_text.strip():
            return jsonify({"error": "No readable text found in the document."})
        summary = generate_summary(extracted_text, max_length, min_length)

        # Clean up uploaded file(s)
        shutil.rmtree(UPLOAD_FOLDER)

        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
