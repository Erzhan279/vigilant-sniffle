from flask import Flask, request
import requests, os, json

app = Flask(__name__)

BOT_TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"
GEMINI_API_KEY = "AIzaSyANUlbK97fpMfIe-RPmaR-Zlc93SaOBo_8"
# MODEL варианттары: "gemini-pro", "gemini-1.5-flash-latest", "gemini-flash-latest"
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print("Telegram send error:", e)

def ask_gemini(prompt):
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(GEMINI_URL, json=payload, timeout=15)
    except Exception as e:
        print("Request to Gemini failed:", e)
        return None, f"Request error: {e}"

    # лог: статус пен толық жауап мәтіні
    print("Gemini status:", resp.status_code)
    text_resp = None
    try:
        text_resp = resp.text
        print("Gemini raw response:", text_resp)
    except Exception as e:
        print("Can't read resp.text:", e)

    # егер JSON болса — парсиміз
    try:
        data = resp.json()
    except Exception as e:
        print("JSON parse error:", e)
        return None, f"Non-JSON response from Gemini (status {resp.status_code})."

    # 1) стандартты жол: candidates -> content -> parts -> text
    try:
        cand = data.get("candidates")
        if cand and isinstance(cand, list) and len(cand) > 0:
            parts = cand[0].get("content", {}).get("parts", [])
            if parts and isinstance(parts, list) and len(parts) > 0:
                return parts[0].get("text", ""), None
    except Exception as e:
        print("Error extracting candidates:", e)

    # 2) басқа мүмкін нысандар: 'output' немесе 'result' немесе 'generated_text'
    # (құрғақ-парақша тексерістері)
    # try a few common fields
    for key in ("output", "result", "generated_text", "text", "message"):
        try:
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                return v, None
            if isinstance(v, dict):
                # егер dict болса, іздеп көрейік ішінен text тәрізді өрістер
                for subk in ("text", "generated_text", "content"):
                    if subk in v and isinstance(v[subk], str) and v[subk].strip():
                        return v[subk], None
        except Exception:
            pass

    # 3) егер жауапта error өрісі бар болса, оны қайтар
    if "error" in data:
        return None, f"Gemini error: {json.dumps(data['error'], ensure_ascii=False)}"

    # 4) болмаса — бүкіл JSON-ды қысқаша қайтарып көр (debug)
    return None, f"Unexpected Gemini response structure: {json.dumps(data, ensure_ascii=False)[:1500]}"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=True)
    print("Update from Telegram:", update)
    if not update or "message" not in update:
        return "no update", 200

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    # қысқа жауап беру кезінде Gemini-ге сұрау жіберу
    reply, error = ask_gemini(text)

    if error:
        # логқа шығару
        print("Gemini error / debug:", error)
        send_message(chat_id, f"Қате Gemini жауап: {error}")
    else:
        send_message(chat_id, reply)

    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running and Gemini debug enabled", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)