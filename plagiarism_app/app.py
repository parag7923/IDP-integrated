from flask import render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
import zipfile
import fitz
import difflib
import shutil
import easyocr
from . import plagiarism_bp

socketio = SocketIO()

# Function to extract ZIP and count PDF files
# Function to extract ZIP and count PDF files
def extract_zip(file_path, extract_to):
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return len([f for f in os.listdir(extract_to) if f.endswith('.pdf')])


# Function to extract text from PDFs
def extract_text_from_pdf(pdf_path, reader, file_index, total_files):
    text = ""
    print(f"Processing file {file_index}/{total_files}: {os.path.basename(pdf_path)}")
    emit('processing_file', {'filename': os.path.basename(pdf_path)}, namespace='/plagiarism')
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            image = page.get_pixmap()
            image.save('plagiarism_app/temp_page.png')
            result = reader.readtext('plagiarism_app/temp_page.png', detail=0)
            text += ' '.join(result) + '\n'
        doc.close()
        os.remove('plagiarism_app/temp_page.png')
        print(f"Successfully processed: {os.path.basename(pdf_path)}")
        emit('file_processed', {'filename': os.path.basename(pdf_path)}, namespace='/plagiarism')
    except Exception as e:
        error_message = f"Error processing {os.path.basename(pdf_path)}: {e}"
        print(error_message)
        emit('processing_error', {'filename': os.path.basename(pdf_path), 'error': error_message}, namespace='/plagiarism')
        return f"Error: {e}"
    return text

# Function to detect plagiarism and group similar files
def detect_plagiarism(texts, file_names):
    plagiarism_groups = []
    visited = [False] * len(texts)
    all_processed_files = set(file_names)  # Keep track of all file names
    plagiarized_files = set()

    for i in range(len(texts)):
        if visited[i]:
            continue

        group = [file_names[i]]
        visited[i] = True
        for j in range(i + 1, len(texts)):
            if not visited[j]:
                similarity = difflib.SequenceMatcher(None, texts[i], texts[j]).ratio()
                if similarity > 0.7:
                    group.append(file_names[j])
                    visited[j] = True

        if len(group) > 1:
            plagiarism_groups.append(group)
            plagiarized_files.update(group)

    original_files = list(all_processed_files - plagiarized_files)

    print("\n[PYTHON] Plagiarism Detection Results:")
    if plagiarism_groups:
        print("[PYTHON] Plagiarized Groups:", plagiarism_groups)
    else:
        print("[PYTHON] No significant plagiarism detected.")
    print("[PYTHON] Original Files:", original_files)
    return plagiarism_groups, original_files

@plagiarism_bp.route('/')
def index():
    return render_template('index.html')

@plagiarism_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"})

    if file and file.filename.endswith('.zip'):
        extract_to = os.path.join('plagiarism_app', 'uploads')
        # Clean up previous uploads
        if os.path.exists(extract_to):
            try:
                shutil.rmtree(extract_to)
                os.makedirs(extract_to, exist_ok=True)
            except OSError as e:
                print(f"Error deleting previous uploads: {e}")
                return jsonify({"error": f"Could not clean up previous uploads: {e}"})
        else:
            os.makedirs(extract_to, exist_ok=True)

        file_path = os.path.join(extract_to, 'uploaded.zip')
        file.save(file_path)
        num_files = extract_zip(file_path, extract_to)  # Pass extract_to to extract_zip
        return jsonify({"success": True, "num_files": num_files})

    return jsonify({"error": "Invalid file type"})

# SocketIO handler to process files and send progress
@socketio.on('process_files', namespace='/plagiarism')
def process_files(data):
    extract_to = 'plagiarism_app/uploads'
    pdf_files = [f for f in os.listdir(extract_to) if f.endswith('.pdf')]
    reader = easyocr.Reader(['en'])

    texts = []
    file_names = []

    # Start processing files
    total_files = len(pdf_files)
    print(f"\nStarting processing of {total_files} files...")
    emit('processing_started', {'total_files': total_files}, namespace='/plagiarism')

    for i, pdf in enumerate(pdf_files):
        text = extract_text_from_pdf(os.path.join(extract_to, pdf), reader, i + 1, total_files)
        texts.append(text)
        file_names.append(pdf)

        # Send real-time progress update
        progress = (i + 1) / total_files * 100
        emit('progress_update', {'progress': progress, 'current_file': pdf, 'total_files': total_files}, namespace='/plagiarism')

    plagiarism_groups, no_plagiarism_files = detect_plagiarism(texts, file_names)

    # Clean up the directory
    shutil.rmtree(extract_to)
    print("Processing complete. Cleaning up temporary files.")
    emit('processing_finished', {'message': 'Processing complete.'}, namespace='/plagiarism')

    # Send the results and no plagiarism files
    emit('processing_complete', {'plagiarism_groups': plagiarism_groups, 'no_plagiarism_files': no_plagiarism_files}, namespace='/plagiarism')

# Function to initialize SocketIO with the app (will be called in main.py)
def init_socketio(app):
    socketio.init_app(app)
    return socketio

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(plagiarism_bp)
    socketio.init_app(app)
    socketio.run(app, debug=True)