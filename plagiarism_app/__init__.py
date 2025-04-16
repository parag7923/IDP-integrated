from flask import Blueprint

plagiarism_bp = Blueprint('plagiarism', __name__,
                            template_folder='templates/plagiarism',
                            static_folder='static')

# Import app AFTER plagiarism_bp is defined
from . import app