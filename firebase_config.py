# firebase_config.py
import os
import json
import firebase_admin
from firebase_admin import credentials, db

INFO_REF = None
MEMORY_REF = None

def init_firebase():
    global INFO_REF, MEMORY_REF

    try:
        # ENV-тен кілтті алу
        firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
        if not firebase_json:
            print("❌ FIREBASE_CREDENTIALS табылмады.")
            return False

        firebase_config = json.loads(firebase_json)
        cred = credentials.Certificate(firebase_config)

        # Firebase қосу
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
            })
            print("🔥 Firebase іске қосылды!")
        else:
            print("⚠️ Firebase бұрыннан іске қосылған.")

        INFO_REF = db.reference("channel_info")
        MEMORY_REF = db.reference("channel_memory")

        print("✅ Firebase байланысы дайын!")
        return True

    except Exception as e:
        print("❌ Firebase қате:", e)
        return False
