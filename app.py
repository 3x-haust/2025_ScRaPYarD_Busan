from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import re
import random

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

def is_english(text: str) -> bool:
    """
    텍스트가 영어인지 한국어인지 확인 (알파벳 비율로 추정).
    """
    letters = re.findall(r"[a-zA-Z]", text)
    return len(letters) > (len(text) / 2)

def generate_excuse(situation: str) -> str:
    """
    상황에 맞춰 한국어 또는 영어로 황당한 변명을 생성.
    """
    user_lang_is_english = is_english(situation)

    # 랜덤 테마
    themes_kr = ["외계인", "시간 여행", "초능력", "마법", "로봇"]
    themes_en = ["aliens", "time travel", "superpowers", "magic", "robots"]
    random_theme = random.choice(themes_en if user_lang_is_english else themes_kr)

    # 랜덤 황당한 문구
    absurd_phrases_kr = [
        "갑자기 중력이 반대로 돼서 떠다녔어요.",
        "제 그림자가 저를 대신해버렸어요.",
        "구름이 제 다리를 먹어버렸어요.",
        "제 몸이 갑자기 투명해졌어요.",
        "제 방이 우주로 날아갔어요.",
        "시간이 멈춰서 움직일 수 없었어요.",
        "제 손이 갑자기 빛을 내기 시작했어요.",
        "제 목소리가 갑자기 사라졌어요.",
        "제 집이 갑자기 바다로 변했어요.",
        "제 다리가 갑자기 나무로 변했어요.",
        "제 눈이 갑자기 미래를 볼 수 있게 됐어요.",
        "제 귀가 갑자기 동물 소리를 들을 수 있게 됐어요.",
        "제 코가 갑자기 냄새를 볼 수 있게 됐어요.",
        "제 입이 갑자기 말을 거꾸로 하기 시작했어요.",
        "제 머리가 갑자기 하늘로 날아갔어요.",
        "제 발이 갑자기 땅에 붙어버렸어요.",
        "제 손가락이 갑자기 10개로 늘어났어요.",
        "제 팔이 갑자기 길어져서 천장에 닿았어요.",
        "제 다리가 갑자기 짧아져서 걷지 못했어요.",
        "제 몸이 갑자기 물로 변했어요.",
        "제 머리가 갑자기 돌로 변했어요.",
        "제 눈이 갑자기 레이저를 쏘기 시작했어요.",
        "제 귀가 갑자기 음악을 연주하기 시작했어요.",
        "제 코가 갑자기 꽃을 피우기 시작했어요.",
        "제 입이 갑자기 불을 뿜기 시작했어요.",
        "제 손이 갑자기 얼음으로 변했어요.",
        "제 발이 갑자기 불로 변했어요.",
        "제 몸이 갑자기 전기로 변했어요.",
        "제 머리가 갑자기 컴퓨터로 변했어요.",
        "제 다리가 갑자기 로켓으로 변했어요."
    ]
    absurd_phrases_en = [
        "Gravity suddenly reversed and I floated away.",
        "My shadow took over for me.",
        "A cloud ate my legs.",
        "I suddenly became invisible.",
        "My room flew into space.",
        "Time stopped and I couldn't move.",
        "My hands started glowing.",
        "My voice suddenly disappeared.",
        "My house turned into an ocean.",
        "My legs turned into wood.",
        "My eyes could suddenly see the future.",
        "My ears could suddenly hear animal thoughts.",
        "My nose could suddenly see smells.",
        "My mouth started speaking backwards.",
        "My head flew into the sky.",
        "My feet got stuck to the ground.",
        "My fingers suddenly multiplied to ten.",
        "My arms grew so long they touched the ceiling.",
        "My legs shortened and I couldn't walk.",
        "My body turned into water.",
        "My head turned into stone.",
        "My eyes started shooting lasers.",
        "My ears started playing music.",
        "My nose started blooming flowers.",
        "My mouth started breathing fire.",
        "My hands turned into ice.",
        "My feet turned into fire.",
        "My body turned into electricity.",
        "My head turned into a computer.",
        "My legs turned into rockets."
    ]

    # 프롬프트 생성
    if user_lang_is_english:
        prompt = f"""
We have a user who wrote their situation in English. 
Please respond in English with the most absurd and unrealistic excuse possible, involving {random_theme}. 
Use your wildest imagination to make it completely nonsensical and useless. Keep it short.

Situation: {situation}
"""
    else:
        prompt = f"""
사용자가 한국어로 상황을 입력했습니다.
'{random_theme}'을(를) 주제로 한 가장 엉뚱하고 현실과 동떨어진 변명을 만들어주세요. 상상력을 최대한 발휘하여 말도 안 되고 쓸모없는 변명을 생성해 주세요. 너무 길면 안됩니다.

상황: {situation}
"""

    # Gemini API 호출
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={API_KEY}",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates and len(candidates) > 0:
            excuse = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if excuse:
                random_phrase = random.choice(absurd_phrases_en if user_lang_is_english else absurd_phrases_kr)
                return f"{excuse.strip()} And {random_phrase}" if user_lang_is_english else f"{excuse.strip()} 그리고 {random_phrase}"
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