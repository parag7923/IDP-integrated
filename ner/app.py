from flask import Blueprint, render_template, request, jsonify, send_file, current_app
import spacy
import pandas as pd
import os
import pdfplumber
import easyocr
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
import logging

ner = Blueprint('ner', __name__, template_folder='templates', static_folder='static')

nlp = spacy.load('en_core_web_trf')
reader = easyocr.Reader(['en'])

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
                else:
                    text += extract_text_from_scanned_pdf(pdf_path, pdf.pages.index(page)) + "\n"
    except Exception as e:
        logging.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return None
    return text


def extract_text_from_scanned_pdf(pdf_path, page_number):
    try:
        pdf_document = fitz.open(pdf_path)
        page = pdf_document.load_page(page_number)
        image = page.get_pixmap()
        image_path = f"{pdf_path}_page_{page_number}.png"
        image.save(image_path)
        result = reader.readtext(image_path, detail=0)
        os.remove(image_path)  # Remove temporary image
        pdf_document.close()
        return ' '.join(result)
    except Exception as e:
        logging.error(f"Error extracting text from scanned PDF page {page_number} of {pdf_path}: {e}")
        return ""


def extract_text_from_image(image_path):
    try:
        result = reader.readtext(image_path, detail=0)
        return ' '.join(result)
    except Exception as e:
        logging.error(f"Error extracting text from image {image_path}: {e}")
        return ""


def perform_ner(file_path):
    text = ""
    try:
        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
            if text is None:
                return {"error": "Error during PDF text extraction."}
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            text = extract_text_from_image(file_path)
        else:
            return {"error": "Unsupported file format."}

        if not text.strip():
            return {"message": "No text extracted."}

        doc = nlp(text)
        unique_entities = list(set((ent.text.strip(), ent.label_) for ent in doc.ents if ent.text.strip()))
        return unique_entities
    except Exception as e:
        logging.error(f"Error during NER processing for {file_path}: {e}")
        return {"error": f"Error during NER processing: {str(e)}"}


@ner.route('/')
def index():
    return render_template('ner/index.html')


@ner.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(file_path)
        entities = perform_ner(file_path)
    except Exception as e:
        logging.error(f"Error saving or processing file {filename}: {e}")
        return jsonify({'error': f"Error saving or processing file: {str(e)}"}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)  # Clean up uploaded file after processing

    return jsonify(entities)


@ner.route('/download_excel', methods=['POST'])
def download_excel():
    data = request.get_json()
    entities = data.get('entities', [])

    df = pd.DataFrame(entities, columns=['Entity', 'Label'])
    excel_path = os.path.join(UPLOAD_FOLDER, 'entities.xlsx')
    try:
        df.to_excel(excel_path, index=False)
        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Error creating or sending Excel file: {e}")
        return jsonify({'error': f"Error creating or sending Excel file: {str(e)}"}), 500
    finally:
        if os.path.exists(excel_path):
            os.remove(excel_path)