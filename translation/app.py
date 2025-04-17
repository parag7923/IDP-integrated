import os
from flask import Blueprint, request, jsonify, render_template
import easyocr
from googletrans import Translator
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdf2image
from werkzeug.utils import secure_filename
import shutil
import asyncio

# ------------------ Blueprint Setup ------------------
translation_bp = Blueprint('translation_bp', __name__,
                            static_folder='static',
                            template_folder='templates')

# ------------------ Upload Folder ------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'translation')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ Supported Languages ------------------
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'mr': 'Marathi',
    'hi': 'Hindi'
}

# ------------------ Utility Functions ------------------
def save_uploaded_file(uploaded_file):
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    filename = secure_filename(uploaded_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    uploaded_file.save(file_path)
    return file_path

def extract_text_from_image(image_path, lang_code='en'):
    try:
        reader = easyocr.Reader([lang_code])
        result = reader.readtext(image_path, detail=0)
        return " ".join(result)
    except Exception as e:
        return f"Error extracting text from image: {e}"

def extract_text_from_pdf_images(pdf_path, lang_code='en'):
    try:
        reader = easyocr.Reader([lang_code])
        images = pdf2image.convert_from_path(pdf_path)
        extracted_text = ""
        for i, image in enumerate(images):
            temp_image_path = os.path.join(UPLOAD_FOLDER, f"temp_page_{i}.jpg")
            image.save(temp_image_path, "JPEG")
            extracted_text += extract_text_from_image(temp_image_path, lang_code) + "\n"
            os.remove(temp_image_path)
        return extracted_text
    except Exception as e:
        return f"Error extracting text from PDF images: {e}"

async def translate_text_async(text, src_lang, dest_lang):
    translator = Translator()
    try:
        translation = await translator.translate(text, src=src_lang, dest=dest_lang)
        translated_text = translation.text
        return translated_text
    except Exception as e:
        return f"Error during translation: {e}"

def translate_text(text, src_lang, dest_lang):
    return asyncio.run(translate_text_async(text, src_lang, dest_lang))

def extract_text_from_document(file_path, lang_code='en'):
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_path, lang_code)
    elif file_path.lower().endswith('.pdf'):
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
            texts = text_splitter.split_documents(pages)
            full_text = "\n".join([text.page_content for text in texts])
            if not full_text.strip():
                full_text = extract_text_from_pdf_images(file_path, lang_code)
            return full_text
        except Exception as e:
            return f"Error extracting text from PDF: {e}"
    else:
        return None

# ------------------ Routes ------------------
@translation_bp.route('/')
def index():
    return render_template('translation/index.html', languages=SUPPORTED_LANGUAGES)

@translation_bp.route('/translate', methods=['POST'])
async def translate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    source_language = request.form.get('source_language')
    target_language = request.form.get('target_language')

    if not source_language or source_language not in SUPPORTED_LANGUAGES:
        return jsonify({'error': 'Please select the document language'}), 400
    if not target_language or target_language not in SUPPORTED_LANGUAGES:
        return jsonify({'error': 'Please select the target language'}), 400

    try:
        file_path = save_uploaded_file(file)
        extracted_text = extract_text_from_document(file_path, source_language)

        if extracted_text is None:
            shutil.rmtree(UPLOAD_FOLDER)
            return jsonify({'error': 'Unsupported file format for text extraction.'}), 400
        elif "Error extracting text" in extracted_text:
            shutil.rmtree(UPLOAD_FOLDER)
            return jsonify({'error': extracted_text}), 500
        elif not extracted_text.strip():
            shutil.rmtree(UPLOAD_FOLDER)
            return jsonify({'translatedText': ''}), 200

        translated_text = await translate_text_async(extracted_text, source_language, target_language)
        shutil.rmtree(UPLOAD_FOLDER)
        return jsonify({'translatedText': translated_text}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
