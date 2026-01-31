"""
Bookinator Flask App - LLM Version
"""

from flask import Flask, render_template, jsonify, request, session
from llm_engine import BookinatorLLM
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Store engines per session (in production, use Redis or similar)
engines = {}

def get_engine():
    """Get or create an engine for the current session."""
    session_id = session.get('session_id')
    if not session_id:
        session_id = secrets.token_hex(8)
        session['session_id'] = session_id
    
    if session_id not in engines:
        engines[session_id] = BookinatorLLM()
    
    return engines[session_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    """Start a new game."""
    engine = get_engine()
    result = engine.start_game()
    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle a chat message."""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    engine = get_engine()
    result = engine.chat(user_message)
    return jsonify(result)

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the conversation."""
    engine = get_engine()
    engine.reset()
    return jsonify({'status': 'ok'})

@app.route('/api/health', methods=['GET'])
def health():
    """Check if Ollama is running."""
    import requests as req
    try:
        resp = req.get('http://127.0.0.1:11434/api/tags', timeout=2)
        models = resp.json().get('models', [])
        return jsonify({
            'ollama': True,
            'models': [m['name'] for m in models]
        })
    except:
        return jsonify({'ollama': False, 'models': []})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
