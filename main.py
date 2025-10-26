from flask import Flask, request
import requests
import json
import os
import threading
import time

app = Flask(__name__)

# === 🔐 Токендер мен параметрлер ===
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
CHANNEL_LINK = "https://t.me/+3gQIXD-xl1Q0YzY6"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

MEMORY_FILE = "channel_memory.json"
INFO_FILE = "channel_info.json"

# === 🧠 Есте сақтау функциялары ===
def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# === 📡 Канал посттарын алу ===
def get_channel_posts(limit=50):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
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
        save_json(MEMORY_FILE, posts)
        print(f"✅ {len(posts)} пост сақталды ({MEMORY_FILE})")
        return posts
    except Exception as e:
        print("❌ Қате (канал посттарын алу):", e)
        return []

# === 📖 Арна туралы ақпарат сақтау ===
def save_channel_info():
    info = {
        "name": "Qazaqsha Films 🎬",
        "description": "Қазақша дубляждалған ең жаңа фильмдер мен сериалдар. 🔥\nКүн сайын жаңа кино!",
        "link": CHANNEL_LINK,
        "id": CHANNEL_ID,
        "language": "kk",
        "topic": "Фильмдер мен қазақша кино әлемі"
    }
    save_json(INFO_FILE, info)
    print("✅ Арна туралы ақпарат сақталды (channel_info.json)")

# === 🔁 3 сағат сайын жаңарту функциясы ===
def update_channel_data():
    while True:
        print("♻️ Канал деректерін жаңарту...")
        get_channel_posts()
        save_channel_info()
        time.sleep(3 * 60 * 60)  # 3 сағат сайын

# === 🤖 Gemini API жауап ===
def ask_gemini(prompt):
    data = {
        "contents": [{"parts": [{"text": f"Сен Qazaqsha Films Telegram арнасының көмекшісісің. "
                                     f"Тек сол арна жайлы жауап бер. Арнада қазақша фильмдер бар. "
                                     f"Міне оның сипаттамасы: {load_json(INFO_FILE)}. "
                                     f"Міне соңғы 50 пост: {load_json(MEMORY_FILE)}. "
                                     f"Пайдаланушы сұрағы: {prompt}"}]}]
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
        try:
            js = r.json()
            return js["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "⚠️ Gemini жауап құрылымын талдай алмады."
    else:
        return f"⚠️ Gemini қатесі: {r.text}"

# === 📤 Telegram-ға хабар жіберу ===
def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)

# === 🌐 Telegram Webhook ===
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

    # 🔥 ТІРКЕЛУ
    if "ТІРКЕЛУ" in text:
        send_message(chat_id, f'📺 <b>Біздің арна:</b>\n👉 <a href="{CHANNEL_LINK}">Qazaqsha Films</a>')
        return "ok"

    # 🆕 Соңғы кинолар
    if "Жаңадан шыққан" in text:
        posts = load_json(MEMORY_FILE)
        latest = "\n\n".join(posts[-5:]) if posts else "Әзірге жаңа кино жоқ 😅"
        send_message(chat_id, f"🆕 <b>Соңғы кинолар:</b>\n\n{latest}")
        return "ok"

    # 🔍 Кино іздеу
    if "Кино іздеу" in text:
        send_message(chat_id, "🔍 Қай киноды іздейсің? Атын жаз 👇")
        return "ok"

    # 🧠 Ұсыныс
    if "қандай кино ұсынасын" in text.lower():
        send_message(chat_id, "🎭 Қай жанр ұнайды? (драма, комедия, экшн т.б.)")
        return "ok"

    # 🎬 Іздеу
    posts = load_json(MEMORY_FILE)
    found = [m for m in posts if text.lower() in m.lower()]
    if found:
        movie_list = "\n\n".join([f"🎬 <b>{m}</b>" for m in found[:5]])
        send_message(chat_id, f"🔎 Табылған кинолар:\n\n{movie_list}")
    else:
        gemini_reply = ask_gemini(text)
        send_message(chat_id, f"🎞 {gemini_reply}")

    return "ok"

# === 🏠 Басты бет ===
@app.route("/")
def home():
    return "🎬 Qazaqsha Films бот жұмыс істеп тұр ✅"

# === 🚀 Серверді іске қосу ===
if __name__ == "__main__":
    save_channel_info()
    get_channel_posts()
    threading.Thread(target=update_channel_data, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)