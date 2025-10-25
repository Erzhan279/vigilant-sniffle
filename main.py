from flask import Flask, request
import requests, os, json

app = Flask(__name__)

TELEGRAM_TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"
GEMINI_API_KEY = "AIzaSyANUlbK97fpMfIe-RPmaR-Zlc93SaOBo_8"

@app.route("/")
def home():
    return "🤖 Bot is running with Gemini v1beta1!"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "no message"

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    try:
        # ✅ v1beta1 нұсқасын қолданамыз (жұмыс істейтін нұсқа)
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"parts": [{"text": text}]}
            ]
        }

        response = requests.post(gemini_url, headers=headers, json=payload)
        data = response.json()

        if "candidates" in data:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            reply = f"⚠️ Gemini error: {data}"
    except Exception as e:
        reply = f"Қате: {e}"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={
        "chat_id": chat_id,
        "text": reply
    })
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)