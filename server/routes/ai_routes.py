from flask import Blueprint, render_template, request
from ai_ollama import run_ai_assistant

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai_assistant', methods=['GET', 'POST'])
def ai_assistant():
    response = ""
    if request.method == 'POST':
        question = request.form.get('question', '')
        try:
            response = run_ai_assistant(question)
        except Exception as e:
            response = f"שגיאה: {str(e)}"
    return render_template('ai_assistant.html', response=response)
