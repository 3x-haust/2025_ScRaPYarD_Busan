from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
API_KEY = "AIzaSyDaeq4-vLjj5iGhbsCwZEZFKtqOHXY0lSQ" 

def generate_excuse(situation: str) -> str:
    """
    주어진 상황에 대해 상상력이 넘치고 엉뚱하며, 웃음을 자아내는 변명을
    Google Gemini API를 통해 생성합니다.
    """
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
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={API_KEY}", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        candidates = data.get("candidates")
        if candidates and isinstance(candidates, list) and len(candidates) > 0:
            excuse = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
            if excuse:
                return excuse.strip()
        
        return "변명을 생성할 수 없습니다. 응답 데이터: " + json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return f"API 호출 중 오류가 발생했습니다: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    excuse = None
    if request.method == "POST":
        situation = request.form.get("situation", "")
        excuse = generate_excuse(situation)
    return render_template("index.html", excuse=excuse)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443, debug=True)
