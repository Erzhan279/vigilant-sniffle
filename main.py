from flask import Flask, request
import requests, os

app = Flask(__name__)

TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update:
        return "no update"

    if "message" not in update:
        return "no message"

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    reply = f"Сәлем! Сен жаздың: {text}"
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
        "chat_id": chat_id,
        "text": reply
    })
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)