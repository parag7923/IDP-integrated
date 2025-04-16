# NER-web

## start--
python -m venv venv 

source venv/bin/activate

## for plagiarism module
pip install flask flask_socketio easyocr  pymupdf werkzeug

## for translation--
pip install googletrans==4.0.0rc1 pypdf PyPDF2 pdfplumber  pdf2image langchain langchain_community langchain_google_genai

pip install --upgrade googletrans

## for summary--
pip install sentence-transformers accelerate>=0.26.0 

## for ner--
pip install spacy openpyxl pandas

python -m spacy download en_core_web_trf

#for chatbot--
pip install langchain_google_genai faiss-cpu

## run --
python main.py

## General Info-

pip install flask flask_socketio easyocr pymupdf pandas googletrans==4.0.0rc1 numpy werkzeug pdf2image sentence-transformers faiss-cpu accelerate>=0.26.0 spacy langchain langchain_community langchain_google_genai pdfplumber langsmith pypdf PyPDF2 pdfplumber openpyxl uuid 

pip uninstall torch torchvision 
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements.txt
pip install --upgrade googletrans

python -m spacy download en_core_web_trf


python app.py


List all installed packages:

pip freeze > installed_packages.txt
This will save a list of all your installed packages to a file named installed_packages.txt.

Uninstall packages (USE WITH CAUTION):
You can then try to uninstall them using pip uninstall -r installed_packages.txt.

pip uninstall -y -r installed_packages.txt
The -y flag automatically confirms the uninstallation of each package.




Okay, let's go through the entire process of setting up your project with a virtual environment to manage the dependencies for your different modules (summary, chatbot, translation, NER, and plagiarism).

Step 1: Navigate to Your Project Directory

Open your terminal or command prompt and navigate to the root directory of your project (the one containing main.py and the plagiarism_app, summary, chatbot, etc., directories).   

Step 2: Create a Virtual Environment

At the root of your project directory, run the command to create a virtual environment. A common name for the virtual environment directory is venv or .venv.

Bash
python -m venv venv 

Run the activation script like this:
Bash
source venv/bin/activate
