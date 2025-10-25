from flask import Flask, request
import requests

app = Flask(__name__)

# 🔑 Сенің кілттерің
TELEGRAM_TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"
GEMINI_API_KEY = "AIzaSyANUlbK97fpMfIe-RPmaR-Zlc93SaOBo_8"

# Telegram API URL
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Gemini API URL
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

@app.route("/")
def home():
    return "🤖 Gemini Telegram bot is working successfully!"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]

        # Gemini API сұрау
        payload = {
            "contents": [
                {"parts": [{"text": user_text}]}
            ]
        }

        gemini_response = requests.post(GEMINI_URL, json=payload)
        gemini_data = gemini_response.json()

        try:
            ai_reply = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            ai_reply = "😅 Кешір, мен жауап таба алмадым."

        # Telegram-ға жауап жазу
        requests.post(TELEGRAM_URL, json={"chat_id": chat_id, "text": ai_reply})

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443)
