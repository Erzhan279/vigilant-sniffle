from flask import Flask, request
import requests
import os

app = Flask(__name__)

# === 🔐 Токендер ===
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"   # ← мұнда өзіңнің жұмыс істеп тұрған Gemini API Key қой

# === 🔗 Telegram API URL ===
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# === 🧠 Gemini API (2.0-flash) ===
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# =========================================================
# Telegram-ға жауап жіберу
def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)

# Gemini-ден жауап алу
def ask_gemini(prompt):
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    r = requests.post(
        GEMINI_URL,
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        },
        json=data
    )
    if r.status_code == 200:
        js = r.json()
        try:
            return js["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "Қате: Gemini жауап құрылымын түсінбедім 😅"
    else:
        return f"Gemini қатесі: {r.text}"

# =========================================================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "no update"
    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    # /start
    if text.lower() == "/start":
        buttons = [
            ["🔍 Кино іздеу", "🧠 Маған қандай кино ұсынасын"],
            ["🆕 Жаңадан шыққан кино", "📺 Каналға тіркелу"]
        ]
        welcome = (
            "🎬 <b>Qazaqsha Films</b> әлеміне қош келдің!\n\n"
            "Мұнда ең жаңа және сапалы қазақша кинолар🔥\n"
            "Төменнен таңда ⤵️"
        )
        send_message(chat_id, welcome, buttons)
        return "ok"

    # Каналға тіркелу
    if "Каналға тіркелу" in text:
        send_message(chat_id, "📺 Каналымызға жазыл:\n👉 https://t.me/+3gQIXD-xl1Q0YzY6")
        return "ok"

    # Жаңадан шыққан кино
    if "Жаңадан шыққан" in text:
        send_message(chat_id, "🎬 Соңғы жүктемелер:")
        return "ok"

    # Кино іздеу
    if "Кино іздеу" in text:
        send_message(chat_id, "🔍 Қай киноды іздейсің? Атын жаз 👇")
        return "ok"

    # Ұсыныс
    if "қандай кино ұсынасын" in text.lower():
        send_message(chat_id, "🧠 Қай жанр ұнайды? (драма, комедия, экшн т.б.)")
        return "ok"

    # Басқа кез келген мәтін → Gemini және іздеу
    gemini_reply = ask_gemini(f"'{text}' деген киноны іздеп жатырмын. "
                              f"Қазақша фильмдер каналымда сол фильм бар ма және ұқсас атаулар қандай?")
    send_message(chat_id, f"🎞 {gemini_reply}")
    return "ok"

# =========================================================
@app.route("/")
def home():
    return "Qazaqsha Films bot is running! ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)