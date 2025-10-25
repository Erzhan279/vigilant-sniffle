from flask import Flask, request
import requests, os

app = Flask(__name__)

# 🔹 Telegram және Gemini API кілттері
TELEGRAM_TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"
GEMINI_API_KEY = "AIzaSyANUlbK97fpMfIe-RPmaR-Zlc93SaOBo_8"

# 🔹 Telegram-ға хабар жіберу функциясы
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# 🔹 Gemini AI-дан жауап алу функциясы
def ask_gemini(question):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"parts": [{"text": question}]}
            ]
        }
        response = requests.post(url, json=payload)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Қате: {e}"

# 🔹 Telegram webhook
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "no update"

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    # Gemini-ге сұрақ жібереміз
    answer = ask_gemini(text)
    send_message(chat_id, answer)
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "🤖 Gemini AI Telegram Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)