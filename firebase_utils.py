import firebase_admin
from firebase_admin import credentials, db
import json
import os

def initialize_firebase():
    try:
        # 🔍 Render немесе жергілікті жолды тексеру
        secret_path = "/etc/secrets/firebase_secret.json"
        local_path = "firebase_secret.json"

        # 🗂 Secret файл бар-жоғын анықтау
        if os.path.exists(secret_path):
            path = secret_path
        elif os.path.exists(local_path):
            path = local_path
        else:
            print("🚫 Firebase secret файлы табылмады!")
            return None, None

        # 📖 JSON оқу
        with open(path, "r", encoding="utf-8") as f:
            firebase_config = json.load(f)

        # 🔑 Firebase инициализация
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://kinobot-fe2ac-default-rtdb.firebaseio.com/"
        })

        print("✅ Firebase сәтті қосылды!")

        info_ref = db.reference("info")
        memory_ref = db.reference("memory")

        return info_ref, memory_ref

    except Exception as e:
        print("🚫 Firebase қатесі:", e)
        print("🚫 Firebase деректер базасы байланыспады! Бэкап режимі іске қосылды.")
        return None, None
