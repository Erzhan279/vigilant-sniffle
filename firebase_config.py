import os
import json
import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    try:
        print("🚀 Firebase инициализациясы басталды...")

        # Егер Firebase бұрын іске қосылған болса, қайта инициализация жасамаймыз
        if firebase_admin._apps:
            print("⚠️ Firebase бұрыннан іске қосылған, қайта инициализация жасалмайды.")
            app = firebase_admin.get_app()
            info_ref = db.reference("channel_info")
            memory_ref = db.reference("channel_memory")
            return info_ref, memory_ref

        # 🔐 ENV ішіндегі JSON алу
        creds_json = os.environ.get("FIREBASE_CREDENTIALS")
        if not creds_json:
            print("🚫 ENV айнымалысы FIREBASE_CREDENTIALS табылмады.")
            return None, None

        # ✅ JSON ішіндегі \n форматтарын қалпына келтіру
        creds = json.loads(creds_json.replace("\\n", "\n"))

        # 🔥 Firebase қосу
        cred = credentials.Certificate(creds)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
        })

        print("✅ Firebase іске қосылды және дерекқорға қосылды!")

        info_ref = db.reference("channel_info")
        memory_ref = db.reference("channel_memory")

        # Тест үшін жазып көреміз
        test_path = db.reference("test_connection")
        test_path.set({"status": "ok"})
        print("📡 Firebase тест жазу сәтті өтті!")

        return info_ref, memory_ref

    except Exception as e:
        print("🚫 Firebase қатесі:", e)
        return None, None
