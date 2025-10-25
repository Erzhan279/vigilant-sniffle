from flask import Flask, request
import requests, os

app = Flask(__name__)

BOT_TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"
GEMINI_MODEL = "gemini-2.0-flash"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "no message"

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    if not text:
        return "no text"

    gemini_url = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": text}]}]}

    try:
        response = requests.post(gemini_url, json=payload)
        if response.status_code != 200:
            reply = f"Gemini қатесі: {response.status_code} - {response.text}"
        else:
            data = response.json()
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        reply = f"Қате: {e}"

    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": chat_id,
        "text": reply
    })
    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)