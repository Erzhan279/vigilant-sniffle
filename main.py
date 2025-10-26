from flask import Flask, request
import requests, json, os, threading, time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

# === 🔐 Токендер мен параметрлер ===
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
CHANNEL_LINK = "https://t.me/+3gQIXD-xl1Q0YzY6"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"

# === Google Drive параметрлері ===
GOOGLE_CREDENTIALS_FILE = "google_client_secret.json"  # ✅ қысқартылған атау
FOLDER_ID = "14iPNSmNbq5r_7w8PqFHN-FSwFx838PKz"

# === Telegram және Gemini ===
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

MEMORY_FILE = "channel_memory.json"
INFO_FILE = "channel_info.json"
ADMIN_ID = 1815036801  # 👈 Тек осы ID /files командасын пайдалана алады


# === 🧩 Google Drive Service ===
def get_drive_service():
    creds = Credentials.from_authorized_user_file(
        GOOGLE_CREDENTIALS_FILE, ["https://www.googleapis.com/auth/drive.file"]
    )
    return build("drive", "v3", credentials=creds)


def find_file_on_drive(filename):
    service = get_drive_service()
    results = service.files().list(
        q=f"name='{filename}' and '{FOLDER_ID}' in parents and trashed=false",
        spaces="drive",
        fields="files(id, name, modifiedTime)"
    ).execute()
    files = results.get("files", [])
    return files[0] if files else None


def upload_or_replace_drive_file(filename):
    try:
        service = get_drive_service()
        file_info = find_file_on_drive(filename)
        media = MediaFileUpload(filename, mimetype="application/json")
        if file_info:
            service.files().update(fileId=file_info["id"], media_body=media).execute()
            print(f"♻️ Drive файлы жаңартылды: {filename}")
        else:
            file_metadata = {"name": filename, "parents": [FOLDER_ID]}
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            print(f"✅ Drive-қа жаңа файл жүктелді: {filename}")
    except Exception as e:
        print(f"❌ Drive қатесі: {e}")


# === 🧠 JSON сақтау ===
def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    upload_or_replace_drive_file(filename)


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
        print(f"✅ {len(posts)} пост сақталды және Drive-қа жіберілді.")
        return posts
    except Exception as e:
        print("❌ Қате (канал посттарын алу):", e)
        return []


# === 📖 Арна туралы ақпарат ===
def save_channel_info():
    info = {
        "name": "Qazaqsha Films 🎬",
        "description": "Қазақша дубляждалған ең жаңа фильмдер мен сериалдар. 🔥",
        "link": CHANNEL_LINK,
        "id": CHANNEL_ID,
        "language": "kk",
        "topic": "Фильмдер мен қазақша кино әлемі"
    }
    save_json(INFO_FILE, info)
    print("✅ Арна туралы ақпарат сақталды және Drive-қа көшірілді.")


# === 🔁 3 сағат сайын жаңарту ===
def update_channel_data():
    while True:
        print("♻️ Канал деректерін жаңарту...")
        get_channel_posts()
        save_channel_info()
        time.sleep(3 * 60 * 60)


# === Gemini API ===
def ask_gemini(prompt):
    data = {
        "contents": [{"parts": [{"text": f"Сен Qazaqsha Films Telegram арнасының көмекшісісің. "
                                     f"Тек сол арна жайлы жауап бер. Арнада қазақша фильмдер бар. "
                                     f"Міне соңғы 50 пост: {load_json(MEMORY_FILE)}. "
                                     f"Пайдаланушы сұрағы: {prompt}"}]}]
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


# === Telegram хабарламалары ===
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

    if text.lower() == "/files":
        if chat_id != ADMIN_ID:
            send_message(chat_id, "⚠️ Бұл команда тек админге арналған.")
            return "ok"
        service = get_drive_service()
        results = service.files().list(
            q=f"'{FOLDER_ID}' in parents and trashed=false",
            fields="files(name, modifiedTime, webViewLink)"
        ).execute()
        files = results.get("files", [])
        if not files:
            send_message(chat_id, "📂 Drive-та файл табылмады 😅")
        else:
            msg_text = "📂 <b>Google Drive-тағы файлдар:</b>\n\n"
            for f in files:
                msg_text += f"🔸 <a href='{f['webViewLink']}'>{f['name']}</a>\n🕓 {f['modifiedTime']}\n\n"
            send_message(chat_id, msg_text)
        return "ok"

    if text.lower() == "/start":
        buttons = [
            ["🔍 Кино іздеу", "🧠 Маған қандай кино ұсынасын"],
            ["🆕 Жаңадан шыққан кино", "🔥 ТІРКЕЛУ 🔥"]
        ]
        send_message(chat_id, "🎬 Qazaqsha Films әлеміне қош келдің!", buttons)
        return "ok"

    if "ТІРКЕЛУ" in text:
        send_message(chat_id, f'📺 <b>Біздің арна:</b>\n👉 <a href="{CHANNEL_LINK}">Qazaqsha Films</a>')
        return "ok"

    if "Жаңадан шыққан" in text:
        posts = load_json(MEMORY_FILE)
        latest = "\n\n".join(posts[-5:]) if posts else "Әзірге жаңа кино жоқ 😅"
        send_message(chat_id, f"🆕 <b>Соңғы кинолар:</b>\n\n{latest}")
        return "ok"

    posts = load_json(MEMORY_FILE)
    found = [m for m in posts if text.lower() in m.lower()]
    if found:
        send_message(chat_id, "🔎 Табылған кинолар:\n\n" + "\n\n".join(found[:5]))
    else:
        send_message(chat_id, f"🎞 {ask_gemini(text)}")
    return "ok"


@app.route("/")
def home():
    return "🎬 Qazaqsha Films бот Google Drive-пен жұмыс істеп тұр ✅"


if __name__ == "__main__":
    save_channel_info()
    get_channel_posts()
    threading.Thread(target=update_channel_data, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)