from flask import Flask, request
import requests, os, json, threading, time
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# === 🔐 Негізгі параметрлер ===
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
CHANNEL_LINK = "https://t.me/+3gQIXD-xl1Q0YzY6"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"

# === Firebase орнату ===
cred = credentials.Certificate("firebase_credentials.json")  # ← сенің Firebase service account JSON файлың
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
})

# === Telegram және Gemini URL ===
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# === 🧠 Боттың ішкі памяты ===
memory = []

# ============================================================
# 📂 Firebase функциялары
def save_to_firebase(path, data):
    ref = db.reference(path)
    ref.set(data)

def load_from_firebase(path):
    ref = db.reference(path)
    return ref.get() or {}

# ============================================================
# 🎬 Канал посттарын алу
def get_channel_posts(limit=50):
    print("🔄 Каналдан посттар алынып жатыр...")
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
        save_to_firebase("channel_posts", posts)
        print(f"✅ {len(posts)} пост Firebase-ке сақталды.")
        return posts
    except Exception as e:
        print(f"❌ Қате (канал посттарын алу): {e}")
        return []

# ============================================================
# 🧾 Канал туралы ақпарат
def save_channel_info():
    info = {
        "name": "🎬 Qazaqsha Films",
        "description": "Қазақша дубляждалған фильмдер мен сериалдардың орталығы! 🔥",
        "link": CHANNEL_LINK,
        "topic": "Қазақша кино әлемі 🇰🇿",
        "language": "kk"
    }
    save_to_firebase("channel_info", info)
    print("✅ Арна туралы ақпарат Firebase-ке сақталды.")

# ============================================================
# ♻️ Автожаңарту (3 сағат сайын)
def update_channel_data():
    while True:
        get_channel_posts()
        save_channel_info()
        time.sleep(3 * 60 * 60)

# ============================================================
# 🧠 Gemini жауап
def ask_gemini(prompt):
    channel_info = load_from_firebase("channel_info")
    channel_posts = load_from_firebase("channel_posts")

    context = f"""
    Сен Qazaqsha Films Telegram арнасының ресми көмекшісісің 🎬
    Арна сипаттамасы: {json.dumps(channel_info, ensure_ascii=False)}
    Соңғы фильмдер тізімі: {channel_posts}
    Пайдаланушы сұрағы: {prompt}
    Тек осы арна жайлы жауап бер, сыртқы тақырыпқа кетпе.
    """

    data = {"contents": [{"parts": [{"text": context}]}]}
    r = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": GEMINI_API_KEY},
        json=data
    )

    if r.status_code == 200:
        try:
            answer = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            memory.append({"q": prompt, "a": answer})  # ⏺ Есте сақтау
            if len(memory) > 10:  # Тек соңғы 10 әңгімені ұстайды
                memory.pop(0)
            save_to_firebase("bot_memory", memory)
            return answer
        except Exception:
            return "⚠️ Gemini жауап құрылымын талдай алмады."
    else:
        return f"⚠️ Gemini қатесі: {r.text}"

# ============================================================
# 📤 Telegram хабар жіберу
def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"keyboard": buttons, "resize_keyboard": True}
    requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)

# ============================================================
# 🌐 Webhook (бот логикасы)
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "no update"

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text.lower() == "/start":
        buttons = [
            ["🔍 Кино іздеу", "🧠 Кино ұсынысы"],
            ["🆕 Соңғы кинолар", "🔥 Тіркелу"]
        ]
        welcome = (
            "🎬 <b>Qazaqsha Films</b> әлеміне қош келдің!\n\n"
            "Мұнда ең жаңа қазақша фильмдер мен сериалдар🔥\n\n"
            "Қайта оралған кино әлемі — тек бізде!\n\n"
            "Төменнен таңда ⤵️"
        )
        send_message(chat_id, welcome, buttons)
        return "ok"

    if "Тіркелу" in text:
        send_message(chat_id, f'📺 <b>Біздің арна:</b>\n👉 <a href="{CHANNEL_LINK}">Qazaqsha Films</a>')
        return "ok"

    if "Соңғы кинолар" in text:
        posts = load_from_firebase("channel_posts")
        if posts:
            latest = "\n\n".join(posts[-5:])
            send_message(chat_id, f"🆕 <b>Соңғы жүктемелер:</b>\n\n{latest}")
        else:
            send_message(chat_id, "😅 Арнада әзірге жаңа кино табылмады.")
        return "ok"

    if "Кино іздеу" in text:
        send_message(chat_id, "🔎 Қай киноны іздейсің? Атын жаз 👇")
        return "ok"

    if "Кино ұсынысы" in text:
        send_message(chat_id, "🎭 Қай жанр ұнайды? (комедия, драма, экшн т.б.)")
        return "ok"

    # 🎬 Кино іздеу логикасы
    posts = load_from_firebase("channel_posts")
    found = [m for m in posts if text.lower() in m.lower()]
    if found:
        send_message(chat_id, "🔎 Табылған кинолар:\n\n" + "\n\n".join(found[:5]))
    else:
        send_message(chat_id, f"🎞 {ask_gemini(text)}")

    return "ok"

# ============================================================
@app.route("/")
def home():
    return "🎬 Qazaqsha Films бот Firebase-пен жұмыс істеп тұр ✅"

# ============================================================
if __name__ == "__main__":
    save_channel_info()
    get_channel_posts()
    threading.Thread(target=update_channel_data, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)