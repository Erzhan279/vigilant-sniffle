import os
import json
import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    try:
        print("🚀 Firebase инициализациясы басталды...")
        creds_json = os.environ.get("FIREBASE_CREDENTIALS")

        if not creds_json:
            print("🚫 ENV айнымалысы FIREBASE_CREDENTIALS табылмады.")
            return None, None

        # 🔍 ENV ішіндегіні тексеру
        print("📦 ENV FIREBASE_CREDENTIALS табылды, ұзындығы:", len(creds_json))

        # \\n-ды \n-ға ауыстыру (Render үшін маңызды)
        creds_json_fixed = creds_json.replace('\\n', '\n')

        try:
            creds = json.loads(creds_json_fixed)
        except json.JSONDecodeError as je:
            print("❌ JSONDecodeError:", je)
            return None, None

        cred = credentials.Certificate(creds)

        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
        })

        print("✅ Firebase іске қосылды!")

        info_ref = db.reference("channel_info")
        memory_ref = db.reference("channel_posts")

        # 🔍 Байланысты тексеру
        test_val = info_ref.get()
        print("📊 Firebase test read:", test_val)

        return info_ref, memory_ref

    except Exception as e:
        print("🚫 Firebase қатесі:", e)
        return None, None
