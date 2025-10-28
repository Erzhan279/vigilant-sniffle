# firebase_utils.py
import os, json, firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    """Firebase-ті ENV немесе local файл арқылы қосу"""
    try:
        cred = None

        # 🔍 Алдымен local файл бар ма тексереміз
        if os.path.exists("serviceAccountKey.json"):
            print("📄 Local serviceAccountKey.json табылды.")
            cred = credentials.Certificate("serviceAccountKey.json")

        # 🔐 Егер local жоқ болса — ENV ішінен аламыз
        else:
            env_data = os.environ.get("FIREBASE_CREDENTIALS")
            if not env_data:
                raise FileNotFoundError("❌ FIREBASE_CREDENTIALS табылмады! Render ENV ішіне қосу керек.")
            
            # Render кейде \n орнына \\n береді, оны дұрыстаймыз
            config = json.loads(env_data.replace('\\n', '\n'))
            cred = credentials.Certificate(config)
            print("🔐 ENV арқылы Firebase key жүктелді.")

        # 🔥 Firebase қосу
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
            })
            print("🔥 Firebase іске қосылды!")

        # 📦 Сілтемелер
        info_ref = db.reference("/channel_info")
        memory_ref = db.reference("/channel_memory")

        # Тест — байланыс бар ма?
        info_ref.get()
        print("✅ Firebase байланысы жұмыс істейді!")

        return info_ref, memory_ref

    except Exception as e:
        print("🚫 Firebase қатесі:", e)
        return None, None
