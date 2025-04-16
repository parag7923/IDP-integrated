import os
import shutil
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

# Define Blueprint
chatbot_bp = Blueprint('chatbot', __name__, template_folder='templates', static_folder='static', static_url_path='/chatbot/static')

# Use dedicated folder for chatbot uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'chatbot')
ALLOWED_EXTENSIONS = {'pdf'}

# Helper to check allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Process the uploaded PDF
def process_pdf(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = FAISS.from_documents(pages, embeddings)
    return db

# Gemini LLM setup
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key="AIzaSyBpZUY9sQrxkPFc64bVlkaO8D-K0s84KlY"
)

# Routes
@chatbot_bp.route('/')
def index():
    return render_template('chatbot/index.html')

@chatbot_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})
    
    if file and allowed_file(file.filename):
        # ✅ Clean and recreate upload folder
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # ✅ Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # ✅ Process and delete after use
        db = process_pdf(file_path)
        current_app.config['chatbot_db'] = db
        shutil.rmtree(UPLOAD_FOLDER)  # ✅ Delete uploaded file(s) after processing

        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Invalid file format"})

@chatbot_bp.route('/get_answer', methods=['GET'])
def get_answer():
    query = request.args.get('query')
    db = current_app.config.get('chatbot_db')

    if db is not None and query:
        docs = db.similarity_search(query)
        relevant_search = "\n".join([x.page_content for x in docs])
        gemini_prompt = (
            "Use the following pieces of context to answer the question. "
            "If you don't know the answer, just say you don't know."
        )
        input_prompt = f"{gemini_prompt}\nContext: {relevant_search}\nUser Question: {query}"
        result = llm.invoke(input_prompt)
        return jsonify({"answer": result.content})
    
    return jsonify({"answer": "No answer available. Please upload a PDF first."})
