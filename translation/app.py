import os
from flask import Blueprint, request, jsonify, render_template
import easyocr
from googletrans import Translator
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdf2image
from werkzeug.utils import secure_filename
import shutil
import asyncio  # Import asyncio

# ------------------ Blueprint Setup ------------------
translation_bp = Blueprint('translation_bp', __name__,
                                        static_folder='static',
                                        template_folder='templates')

# ------------------ Upload Folder ------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'translation')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ Utility Functions ------------------
def save_uploaded_file(uploaded_file):
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    filename = secure_filename(uploaded_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    uploaded_file.save(file_path)
    return file_path

def extract_text_from_image(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

def extract_text_from_pdf_images(pdf_path):
    reader = easyocr.Reader(['en'])
    images = pdf2image.convert_from_path(pdf_path)
    extracted_text = ""
    for i, image in enumerate(images):
        temp_image_path = os.path.join(UPLOAD_FOLDER, f"temp_page_{i}.jpg")
        image.save(temp_image_path, "JPEG")
        extracted_text += extract_text_from_image(temp_image_path) + "\n"
        os.remove(temp_image_path)
    return extracted_text

async def translate_to_hindi_async(file_path):
    translator = Translator()

    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        input_text = extract_text_from_image(file_path)
    elif file_path.lower().endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        texts = text_splitter.split_documents(pages)
        input_text = "\n".join([text.page_content for text in texts])

        if not input_text.strip():
            input_text = extract_text_from_pdf_images(file_path)
    else:
        return "Unsupported file format"

    try:
        translation = await translator.translate(input_text, src='en', dest='hi')
        translated_text = translation.text
    except Exception as e:
        translated_text = f"Error occurred during translation: {e}"

    return translated_text

def translate_to_hindi(file_path):
    return asyncio.run(translate_to_hindi_async(file_path))

# ------------------ Routes ------------------
@translation_bp.route('/')
def index():
    return render_template('translation/index.html')

@translation_bp.route('/translate', methods=['POST'])
def translate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        file_path = save_uploaded_file(file)
        translated_text = translate_to_hindi(file_path)
        shutil.rmtree(UPLOAD_FOLDER)  # Clean up after use
        return jsonify({'translatedText': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500