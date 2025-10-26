from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔐 Токендер мен параметрлер
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"  # ✅ Сенің жұмыс істейтін Gemini кілтің
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# =========================================================
# 📤 Telegram-ға хабар жіберу
def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)

# =========================================================
# 🤖 Gemini API арқылы жауап алу
def ask_gemini(prompt):
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(
        GEMINI_URL,
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        },
        json=data
    )
    if r.status_code == 200:
        try:
            js = r.json()
            return js["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "⚠️ Gemini жауап құрылымын талдай алмады."
    else:
        return f"⚠️ Gemini қатесі: {r.text}"

# =========================================================
# 🎬 Каналдағы соңғы 200 постты алу
def get_channel_posts(limit=200):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url).json()
        posts = []
        if "result" in response:
            for update in response["result"]:
                msg = update.get("channel_post")
                if msg and str(msg["chat"]["id"]) == CHANNEL_ID:
                    text = msg.get("text", "")
                    if text:
                        posts.append(text)
        posts = posts[-limit:]
        print(f"✅ Каналдан {len(posts)} пост алынды.")
        return posts
    except Exception as e:
        print("❌ Қате (канал посттарын алу):", e)
        return []

# Канал посттарын бот іске қосылғанда бір рет аламыз
CHANNEL_POSTS = get_channel_posts()

# =========================================================
# 🌐 Telegram Webhook
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
            ["🆕 Жаңадан шыққан кино", "🔥 ТІРКЕЛУ 🔥"]
        ]
        welcome = (
            "🎬 <b>Qazaqsha Films</b> әлеміне қош келдің!\n\n"
            "Мұнда ең жаңа және сапалы қазақша кинолар🔥\n\n"
            "Төменнен таңда ⤵️"
        )
        send_message(chat_id, welcome, buttons)
        return "ok"

    # Тіркелу батырмасы
    if "ТІРКЕЛУ" in text:
        send_message(chat_id, '📺 <b>Біздің арнаға қосыл:</b>\n👉 <a href="https://t.me/+3gQIXD-xl1Q0YzY6">Qazaqsha Films</a>')
        return "ok"

    # Жаңадан шыққан кино
    if "Жаңадан шыққан" in text:
        latest = "\n\n".join(CHANNEL_POSTS[-5:]) if CHANNEL_POSTS else "Әзірге жаңа кино жоқ 😅"
        send_message(chat_id, f"🆕 <b>Соңғы кинолар:</b>\n\n{latest}")
        return "ok"

    # Кино іздеу
    if "Кино іздеу" in text:
        send_message(chat_id, "🔍 Қай киноды іздейсің? Атын жаз 👇")
        return "ok"

    # Ұсыныс
    if "қандай кино ұсынасын" in text.lower():
        send_message(chat_id, "🎭 Қай жанр ұнайды? (мысалы: драма, комедия, экшн т.б.)")
        return "ok"

    # Кино атауы жазылған кезде
    found_movies = [m for m in CHANNEL_POSTS if text.lower() in m.lower()]
    if found_movies:
        movie_list = "\n\n".join([f"🎬 <b>{m}</b>" for m in found_movies[:5]])
        send_message(chat_id, f"🔎 Табылған кинолар:\n\n{movie_list}")
        return "ok"
    else:
        gemini_reply = ask_gemini(f"'{text}' фильмі қазақша каналдарда бар ма немесе соған ұқсас қандай фильм бар?")
        send_message(chat_id, f"🎞 {gemini_reply}")
        return "ok"

# =========================================================
@app.route("/")
def home():
    return "🎬 Qazaqsha Films бот жұмыс істеп тұр ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)