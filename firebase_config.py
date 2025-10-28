import os
import json
import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    try:
        cred_json = os.environ.get("FIREBASE_CREDENTIALS")
        if not cred_json:
            print("🚫 FIREBASE_CREDENTIALS табылмады.")
            return None, None

        # 🔧 Escape-ті дұрыстаймыз
        cred_json = cred_json.replace("\\n", "\n")

        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)

        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
        })

        info_ref = db.reference("info")
        memory_ref = db.reference("memory")

        print("🔥 Firebase іске қосылды!")
        return info_ref, memory_ref

    except Exception as e:
        print(f"🚫 Firebase қатесі: {e}")
        return None, None
