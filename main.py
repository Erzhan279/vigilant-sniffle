from flask import Flask, request
import requests, os, json, traceback

app = Flask(__name__)

BOT_TOKEN = "8009566735:AAGV-oF1oHq6dpmJh3gmvqC92xXZVVzrIVg"
GEMINI_API_KEY = "AIzaSyANUlbK97fpMfIe-RPmaR-Zlc93SaOBo_8"
# Try v1beta1 model endpoint — adjust if ListModels shows different name
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta1/models/gemini-1.5-flash:generateContent"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception as e:
        print("Telegram send error:", e)

def ask_gemini(prompt):
    payload = {"contents":[{"parts":[{"text": prompt}]}]}
    try:
        resp = requests.post(GEMINI_URL + f"?key={GEMINI_API_KEY}", json=payload, timeout=20)
    except Exception as e:
        print("Network/request error to Gemini:", e)
        return None, f"Network error: {e}"

    print("Gemini status_code:", resp.status_code)
    print("Gemini raw response (first 2000 chars):")
    try:
        text = resp.text
        print(text[:2000])
    except Exception as e:
        print("Couldn't read resp.text:", e)
        text = ""

    # Try to parse JSON safely
    try:
        data = resp.json()
    except Exception as e:
        print("JSON parse error:", e)
        # return text for debug if non-json
        return None, f"Non-JSON response from Gemini (status {resp.status_code}): {text[:1500]}"

    # If JSON, try to extract usual fields
    if isinstance(data, dict):
        if "candidates" in data:
            try:
                parts = data["candidates"][0]["content"]["parts"]
                return parts[0].get("text",""), None
            except Exception as e:
                print("Error extracting candidates:", e)
        # fallback common fields
        for k in ("output", "result", "generated_text", "text"):
            if k in data:
                v = data[k]
                if isinstance(v, str) and v.strip():
                    return v, None
                if isinstance(v, dict):
                    for sub in ("text","content","generated_text"):
                        if sub in v and isinstance(v[sub], str):
                            return v[sub], None

    return None, f"Unexpected JSON from Gemini: {json.dumps(data)[:1500]}"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running and debug enabled"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = request.get_json(force=True, silent=True)
        print("Update:", update)
        if not update or "message" not in update:
            return "no message", 200

        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text","")
        if not text:
            send_message(chat_id, "Қолдау: тек мәтіндік хабарламаларды қабылдаймын.")
            return "ok", 200

        reply, err = ask_gemini(text)
        if err:
            print("Gemini error (to user):", err)
            send_message(chat_id, f"Gemini қатесі: {err}")
        else:
            send_message(chat_id, reply)
    except Exception:
        tb = traceback.format_exc()
        print("Webhook handler exception:", tb)
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)