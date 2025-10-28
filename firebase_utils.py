import firebase_admin
from firebase_admin import credentials, db
import json, os

def initialize_firebase():
    try:
        print("🔄 Firebase байланысын орнату...")
        if not os.path.exists("serviceAccountKey.json"):
            print("❌ serviceAccountKey.json табылмады!")
            return None, None

        # JSON тексеру
        with open("serviceAccountKey.json", "r") as f:
            data = json.load(f)

        cred = credentials.Certificate(data)

        # Firebase Realtime Database URL
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
        })

        info_ref = db.reference("info")
        memory_ref = db.reference("memory")

        print("✅ Firebase байланысы сәтті орнатылды!")
        return info_ref, memory_ref

    except Exception as e:
        print("🚫 Firebase қатесі:", e)
        return None, None
