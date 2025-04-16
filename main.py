from flask import Flask, render_template
from plagiarism_app import plagiarism_bp, app as plagiarism_app_module

from summary.app import summary_bp
from ner.app import ner
from chatbot.app import chatbot_bp
from translation.app import translation_bp

app = Flask(__name__)
app.register_blueprint(plagiarism_bp, url_prefix='/plagiarism')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
app.register_blueprint(ner, url_prefix='/ner')
app.register_blueprint(summary_bp, url_prefix='/summary')
app.register_blueprint(translation_bp, url_prefix='/translation')

socketio = plagiarism_app_module.socketio
socketio.init_app(app)

@app.route('/')
def main_index():
    return render_template('main/index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)