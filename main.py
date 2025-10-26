from flask import Flask, request
import requests, json, os, threading, time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

app = Flask(__name__)

# === 🔐 Токендер мен параметрлер ===
BOT_TOKEN = "6947421569:AAGCqkNTN6AhlgZLHW6Q_B0ild7TMnf03so"
CHANNEL_ID = "-1002948354799"
CHANNEL_LINK = "https://t.me/+3gQIXD-xl1Q0YzY6"
GEMINI_API_KEY = "AIzaSyAbCKTuPXUoCZ26l0bEQc0qXAIJa5d7Zlk"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DRIVE_FOLDER_ID = "14iPNSmNbq5r_7w8PqFHN-FSwFx838PKz"

SCOPES = ['https://www.googleapis.com/auth/drive.file']
MEMORY_FILE = "channel_memory.json"
INFO_FILE = "channel_info.json"

# === 📂 Google Drive байланысы ===
def get_drive_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("client_secret_873098965972-hs2fkrmj3qigtdmge4rv8otimhmhb0v4.apps.googleusercontent.com.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

# === 🔼 Файлды Drive-қа жүктеу ===
def upload_to_drive(filename):
    try:
        service = get_drive_service()
        file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaFileUpload(filename, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✅ {filename} Google Drive-қа жүктелді.")
    except Exception as e:
        print("❌ Drive жүктеу қатесі:", e)

# === 🔽 Drive-тен файлды жүктеу ===
def download_from_drive(filename):
    try:
        service = get_drive_service()
        results = service.files().list(q=f"name='{filename}' and '{DRIVE_FOLDER_ID}' in parents",
                                       spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        if not items:
            return False
        file_id = items[0]['id']
        request_drive = service.files().get_media(fileId=file_id)
        fh = io.FileIO(filename, 'wb')
        downloader = MediaIoBaseDownload(fh, request_drive)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        print(f"✅ {filename} Google Drive-тен жүктелді.")
        return True
    except Exception as e:
        print("❌ Drive жүктеу қатесі:", e)
        return False

# === 📦 JSON сақтау/жүктеу ===
def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    upload_to_drive(filename)

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    if download_from_drive(filename):
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
    save_json(INFO_FILE, info)

# === 🔁 3 сағат сайын жаңарту ===
def update_channel_data():
    while True:
        get_channel_posts()
        save_channel_info()
        time.sleep(3 * 60 * 60)

# === 🤖 Gemini API ===
def ask_gemini(prompt):
    data = {
        "contents": [{"parts": [{"text": f"Сен Qazaqsha Films Telegram арнасының көмекшісісің. "
                                     f"Арна сипаттамасы: {load_json(INFO_FILE)}. "
                                     f"Соңғы 50 пост: {load_json(MEMORY_FILE)}. "
                                     f"Пайдаланушы сұрағы: {prompt}"}]}]
    }
    r = requests.post(GEMINI_URL, headers={
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }, json=data)
    if r.status_code == 200:
        try:
            js = r.json()
            return js["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "⚠️ Gemini жауап құрылымын талдай алмады."
    else:
        return f"⚠️ Gemini қатесі: {r.text}"

# === 📤 Telegram хабарлама жіберу ===
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

    if text.lower() == "/start":
        buttons = [
            ["🔍 Кино іздеу", "🧠 Маған қандай кино ұсынасын"],
            ["🆕 Жаңадан шыққан кино", "🔥 ТІРКЕЛУ 🔥"]
        ]
        welcome = "🎬 <b>Qazaqsha Films</b> әлеміне қош келдің!\n\nТөменнен таңда ⤵️"
        send_message(chat_id, welcome, buttons)
        return "ok"

    if "ТІРКЕЛУ" in text:
        send_message(chat_id, f'📺 <b>Арна:</b>\n👉 <a href="{CHANNEL_LINK}">Qazaqsha Films</a>')
        return "ok"

    if "Жаңадан шыққан" in text:
        posts = load_json(MEMORY_FILE)
        latest = "\n\n".join(posts[-5:]) if posts else "Посттар табылмады 😅"
        send_message(chat_id, f"🆕 <b>Соңғы кинолар:</b>\n\n{latest}")
        return "ok"

    if "Кино іздеу" in text:
        send_message(chat_id, "🔍 Қай киноны іздейсің? Атын жаз 👇")
        return "ok"

    posts = load_json(MEMORY_FILE)
    found = [m for m in posts if text.lower() in m.lower()]
    if found:
        send_message(chat_id, "🔎 Табылған кинолар:\n\n" + "\n".join([f"🎬 <b>{m}</b>" for m in found[:5]]))
    else:
        send_message(chat_id, "🎞 " + ask_gemini(text))
    return "ok"

@app.route("/")
def home():
    return "🎬 Qazaqsha Films бот жұмыс істеп тұр ✅"

if __name__ == "__main__":
    download_from_drive(MEMORY_FILE)
    download_from_drive(INFO_FILE)
    threading.Thread(target=update_channel_data, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)