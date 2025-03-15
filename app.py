from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
API_KEY = "AIzaSyDaeq4-vLjj5iGhbsCwZEZFKtqOHXY0lSQ"

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('ChatMessage', backref='session', lazy=True)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(10))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id
        }

def generate_excuse(situation: str) -> str:
    prompt = f"""
다음 상황에 대해 상상력이 넘치고 엉뚱하며, 웃음을 자아내는 재치있는 변명을 만들어줘.
변명이 너무 길어서는 안돼.

예시)
Q: 학교에 지각했을 때, 선생님께 뭐라고 해야 해?
A: 코끼리가 집 문을 막고 있어서, 밀고 나오느라 늦었어요.

상황: {situation}
"""
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={API_KEY}", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates")
        if candidates and isinstance(candidates, list) and len(candidates) > 0:
            excuse = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
            if excuse:
                return excuse.strip()
        return "변명을 생성할 수 없습니다."
    except Exception as e:
        return f"API 호출 중 오류가 발생했습니다: {e}"

@app.route('/')
def index():
    session_id = request.args.get('session_id', None)
    messages = []
    if session_id:
        messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
    sessions = ChatSession.query.order_by(ChatSession.created_at.desc()).all()
    return render_template('index.html', messages=messages, sessions=sessions, current_session_id=session_id)

@app.route('/new_chat', methods=['GET'])
def new_chat():
    new_session = ChatSession()
    db.session.add(new_session)
    db.session.commit()
    return redirect(url_for('index', session_id=new_session.id))

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    situation = data.get('situation', '')
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    user_msg = ChatMessage(sender='user', message=situation, session_id=session_id)
    db.session.add(user_msg)
    db.session.commit()

    excuse = generate_excuse(situation)

    bot_msg = ChatMessage(sender='bot', message=excuse, session_id=session_id)
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({"excuse": excuse})

@app.route('/history', methods=['GET'])
def history():
    messages = ChatMessage.query.order_by(ChatMessage.timestamp).all()
    return jsonify([msg.to_dict() for msg in messages])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8443, debug=True)
