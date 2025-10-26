from flask import Flask, request
import requests, json, os, threading, time
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# === 🔐 Telegram және Gemini ===
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
CHANNEL_LINK = "https://t.me/+3gQIXD-xl1Q0YzY6"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

ADMIN_ID = 1815036801  # Тек админ үшін /files командасы

# === 🔥 Firebase баптау ===
cred_json = json.loads(os.environ["FIREBASE_CREDENTIALS"])
cred = credentials.Certificate(cred_json)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
})

# === 🧠 Firebase есте сақтау функциялары ===
def save_to_firebase(path, data):
    try:
        db.reference(path).set(data)
        print(f"✅ Firebase сақталды: {path}")
    except Exception as e:
        print(f"❌ Firebase қатесі: {e}")

def load_from_firebase(path):
    try:
        data = db.reference(path).get()
        return data if data else []
    except Exception as e:
        print(f"❌ Firebase оқу қатесі: {e}")
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
        save_to_firebase("channel_memory", posts)
        print(f"✅ {len(posts)} пост Firebase-ке сақталды.")
        return posts
    except Exception as e:
        print("❌ Қате (канал посттарын алу):", e)
        return []

# === 📖 Арна туралы ақпарат сақтау ===
def save_channel_info():
    info = {
        "name": "Qazaqsha Films 🎬",
        "description": "Қазақша дубляждалған ең жаңа фильмдер мен сериалдар. 🔥",
        "link": CHANNEL_LINK,
        "id": CHANNEL_ID,
        "language": "kk",
        "topic": "Фильмдер мен қазақша кино әлемі"
    }
    save_to_firebase("channel_info", info)
    print("✅ Арна туралы ақпарат Firebase-ке сақталды.")

# === 🔁 3 сағат сайын жаңарту ===
def update_channel_data():
    while True:
        print("♻️ Канал деректерін жаңарту...")
        get_channel_posts()
        save_channel_info()
        time.sleep(3 * 60 * 60)

# === 🤖 Gemini API ===
def ask_gemini(prompt):
    info = load_from_firebase("channel_info")
    posts = load_from_firebase("channel_memory")

    data = {
        "contents": [{
            "parts": [{
                "text": f"Сен Qazaqsha Films Telegram арнасының көмекшісісің. "
                        f"Тек сол арна туралы жауап бер. Арнада қазақша фильмдер бар. "
                        f"Міне сипаттамасы: {info}. "
                        f"Міне соңғы посттар: {posts}. "
                        f"Пайдаланушы сұрағы: {prompt}"
            }]
        }]
    }

    r = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY},
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

# === 📤 Telegram хабар жіберу ===
def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)

# === 🌐 Webhook ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "no update"

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    # 🔹 Тек админге арналған
    if text.lower() == "/files":
        if chat_id != ADMIN_ID:
            send_message(chat_id, "⚠️ Бұл команда тек админге арналған.")
            return "ok"

        info = load_from_firebase("channel_info")
        posts = load_from_firebase("channel_memory")
        msg_text = (
            "📂 <b>Firebase деректері:</b>\n\n"
            f"📘 Арна: {info.get('name', '—')}\n"
            f"📄 Сақталған пост саны: {len(posts)}"
        )
        send_message(chat_id, msg_text)
        return "ok"

    # /start
    if text.lower() == "/start":
        buttons = [
            ["🔍 Кино іздеу", "🧠 Маған қандай кино ұсынасын"],
            ["🆕 Жаңадан шыққан кино", "🔥 ТІРКЕЛУ 🔥"]
        ]
        send_message(chat_id, "🎬 Qazaqsha Films әлеміне қош келдің!", buttons)
        return "ok"

    # ТІРКЕЛУ
    if "ТІРКЕЛУ" in text:
        send_message(chat_id, f'📺 Біздің арна: <a href="{CHANNEL_LINK}">Qazaqsha Films</a>')
        return "ok"

    # Соңғы кинолар
    if "Жаңадан шыққан" in text:
        posts = load_from_firebase("channel_memory")
        latest = "\n\n".join(posts[-5:]) if posts else "Әзірге жаңа кино жоқ 😅"
        send_message(chat_id, f"🆕 <b>Соңғы кинолар:</b>\n\n{latest}")
        return "ok"

    # Кино іздеу
    posts = load_from_firebase("channel_memory")
    found = [m for m in posts if text.lower() in m.lower()]

    if found:
        send_message(chat_id, "🔎 Табылған кинолар:\n\n" + "\n\n".join(found[:5]))
    else:
        send_message(chat_id, f"🎞 {ask_gemini(text)}")
    return "ok"

@app.route("/")
def home():
    return "🎬 Qazaqsha Films бот Firebase-пен жұмыс істеп тұр ✅"

if __name__ == "__main__":
    save_channel_info()
    get_channel_posts()
    threading.Thread(target=update_channel_data, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)