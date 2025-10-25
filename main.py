from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔐 Телеграм бот токенің осында жаз
TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"

# 🔹 Басты webhook маршруты
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    if not update or "message" not in update:
        return "no update"

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # Жауап жазу
    reply_text = f"Сәлем! 👋 Сен жаздың: {text}"

    # Telegram API арқылы жауап қайтару
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
        "chat_id": chat_id,
        "text": reply_text
    })

    return "ok"

# 🔹 Тест үшін басты бет
@app.route("/")
def home():
    return "✅ Telegram Bot is running on Render!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render PORT орнатады
    app.run(host="0.0.0.0", port=port)