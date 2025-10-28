import os
import json
import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    try:
        # 🔐 Firebase credentials ENV ішінен оқу
        creds_json = os.environ.get("FIREBASE_CREDENTIALS")

        if not creds_json:
            print("🚫 ENV-де FIREBASE_CREDENTIALS табылмады.")
            return None, None

        # JSON ішіндегі escape символдарын дұрыстау
        creds = json.loads(creds_json.replace('\\n', '\n'))

        # 🔥 Firebase инициализация
        cred = credentials.Certificate(creds)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
        })

        print("✅ Firebase іске қосылды!")
        info_ref = db.reference("channel_info")
        memory_ref = db.reference("channel_posts")
        return info_ref, memory_ref

    except Exception as e:
        print("🚫 Firebase қатесі:", e)
        return None, None
