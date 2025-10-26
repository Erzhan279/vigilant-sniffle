from flask import Flask, request
import requests, json, os, threading, time
import firebase_admin
from firebase_admin import credentials, db

# === 🚀 Flask қосымшасы ===
app = Flask(__name__)

# === 🔐 Бот параметрлері ===
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
CHANNEL_LINK = "https://t.me/+3gQIXD-xl1Q0YzY6"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"
ADMIN_ID = 1815036801  # Сенің Telegram ID-ің

# === 🔥 Firebase баптауы ===
import os
import json
import firebase_admin
from firebase_admin import credentials, db

# 🔐 FIREBASE_CREDENTIALS мәнін Render Environment Variables ішіне салып қою керек
firebase_config = json.loads(os.environ["FIREBASE_CREDENTIALS"])

cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
})

# === 📦 Firebase сілтемелер ===
INFO_REF = db.reference("channel_info")
MEMORY_REF = db.reference("channel_memory")

# === 🌍 API сілтемелер ===
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


# === 📤 Telegram хабар жіберу ===
def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)


# === 📡 Канал посттарын алу және Firebase-ке сақтау ===
def get_channel_posts(limit=50):
    print("📡 Канал посттарын жүктеу басталды...")
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
    if posts:
        MEMORY_REF.set(posts)
        print(f"✅ {len(posts)} пост Firebase-ке сақталды.")
    else:
        print("⚠️ Пост табылған жоқ.")
    return posts


# === 📖 Арна туралы ақпарат Firebase-ке сақтау ===
def save_channel_info():
    info = {
        "name": "Qazaqsha Films 🎬",
        "description": "Қазақша дубляждалған ең жаңа фильмдер мен сериалдар. 🔥",
        "link": CHANNEL_LINK,
        "id": CHANNEL_ID,
        "language": "kk",
        "topic": "Фильмдер мен қазақша кино әлемі"
    }
    INFO_REF.set(info)
    print("✅ Арна туралы ақпарат Firebase-ке сақталды.")


# === 🔁 Әр 3 сағат сайын тексеріп тұру ===
def auto_refresh():
    while True:
        posts = MEMORY_REF.get()
        if not posts:
            print("♻️ Firebase бос, посттарды қайта жүктеймін...")
            get_channel_posts()
            save_channel_info()
        else:
            print("✅ Посттар бар, қайта жүктеу қажет емес.")
        time.sleep(3 * 60 * 60)


# === 🤖 Gemini Firebase арқылы жауап беру ===
def ask_gemini(prompt):
    posts = MEMORY_REF.get() or []
    info = INFO_REF.get() or {}

    context = (
        f"Сен Qazaqsha Films Telegram арнасының көмекшісісің. "
        f"Арна сипаттамасы: {info.get('description', '')}. "
        f"Міне соңғы 50 пост:\n\n" + "\n".join(posts[-50:]) +
        f"\n\nПайдаланушы сұрағы: {prompt}"
    )

    data = {"contents": [{"parts": [{"text": context}]}]}
    r = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY},
        json=data
    )

    try:
        js = r.json()
        return js["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "⚠️ Gemini Firebase деректеріне сүйене алмады."


# === 🌐 Telegram Webhook ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "no update"

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    # 🔒 Админге арналған командалар
    if chat_id == ADMIN_ID:
        if text.lower() == "/files":
            info = INFO_REF.get()
            posts = MEMORY_REF.get()
            send_message(chat_id,
                         f"📊 Арна: {info.get('name')}\n"
                         f"🗂 Пост саны: {len(posts) if posts else 0}\n"
                         f"🌐 Firebase синхрондалған ✅")
            return "ok"

        if text.lower() == "/gostart":
            posts = MEMORY_REF.get()
            if posts:
                send_message(chat_id, "♻️ Соңғы посттар бұрыннан бар, қайта жүктелмейді.")
            else:
                get_channel_posts()
                save_channel_info()
                send_message(chat_id, "✅ Соңғы 50 пост Firebase-ке жүктелді!")
            return "ok"

    # 🏠 Старт
    if text.lower() == "/start":
        buttons = [
            ["🔍 Кино іздеу", "🧠 Кино ұсынысы"],
            ["🆕 Жаңа кинолар", "🔥 ТІРКЕЛУ 🔥"]
        ]
        send_message(chat_id,
                     "🎬 <b>Qazaqsha Films</b> әлеміне қош келдің!\n\n"
                     "Мұнда ең жаңа және сапалы қазақша дубляждалған фильмдер! 🍿", buttons)
        return "ok"

    # 🔥 ТІРКЕЛУ батырмасы
    if "ТІРКЕЛУ" in text:
        send_message(chat_id, f'📺 Біздің арна: <a href="{CHANNEL_LINK}">Qazaqsha Films</a>')
        return "ok"

    # 🆕 Соңғы кинолар
    if "Жаңа кинолар" in text:
        posts = MEMORY_REF.get()
        latest = "\n\n".join(posts[-5:]) if posts else "Әзірге жаңа кино жоқ 😅"
        send_message(chat_id, f"🆕 <b>Соңғы кинолар:</b>\n\n{latest}")
        return "ok"

    # 🔍 Іздеу
    if "Кино іздеу" in text:
        send_message(chat_id, "🔍 Қай киноды іздеп жатырсың? Атын жаз 👇")
        return "ok"

    # 🎭 Ұсыныс
    if "Ұсыныс" in text:
        send_message(chat_id, "🎭 Қай жанр ұнайды? (драма, комедия, экшн, қорқынышты т.б.)")
        return "ok"

    # 🔎 Іздеу нәтижесі
    posts = MEMORY_REF.get() or []
    found = [m for m in posts if text.lower() in m.lower()]
    if found:
        send_message(chat_id, "🎞 Табылған кинолар:\n\n" + "\n\n".join(found[:5]))
    else:
        send_message(chat_id, ask_gemini(text))

    return "ok"


@app.route("/")
def home():
    return "🎬 Qazaqsha Films бот Firebase және Gemini-пен толық жұмыс істеп тұр ✅"


# === 🚀 Іске қосу ===
if __name__ == "__main__":
    threading.Thread(target=auto_refresh, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)